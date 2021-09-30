import json
import os
from datetime import timedelta, datetime
from time import sleep
from loguru import logger

from system.other import TARANTOOL_CONN, PIKA_CONNECTION, PIKA_PUBLISH, GET_CONF_FROM_MEM


@logger.catch            
def QUEUE_MANAGER(addres_in_mem):
    
    """ Function to check, delete and return emails from the queue """
    
    while True:
        
        j_config = GET_CONF_FROM_MEM(addres_in_mem)

        meta = {}
        MetaForDelete = {}
        
        now = datetime.now()
        now_timestamp = int(now.timestamp())
        
        tarantool_queue_message, tarantool_space_status = TARANTOOL_CONN('queue_message')
        if not tarantool_space_status:
            raise ErrorConnectionTarantool('Tarantool error queue_message!')
        delta_now = now_timestamp - 3600*j_config['ttl']['queue']
        
        ### DELETE OLD MESSAGE ###
        res = tarantool_queue_message.call('space_cleaner', (delta_now, 4, 'queue_message'))
        
        for row_res in res[0]:
            file_name = "/queue/{}.eml".format(str(row_res))
            try:
                os.remove(file_name)
                logger.info("Delete {}".format(file_name))
            except Exception as e:
                logger.error(str(e))
                logger.error("Can't delete {}".format(file_name))
        
                
        """ CHECK PUSH QUEUE """
        
        space_file_binary, tarantool_space_status = TARANTOOL_CONN("file_binary")
        if not tarantool_space_status:
            raise ErrorConnectionTarantool('Tarantool error!')
        res = tarantool_queue_message.call('queue_push', (now_timestamp, 5, 'queue_message'))
        for row_res in res[0]:
            message_log = json.loads(row_res[1])
            file_name_eml = "/queue/{}.eml".format(row_res[0])
            try:
                f = open(file_name_eml, 'rb')
                byte_file = f.read()
                f.close()
            except Exception as e:
                logger.error(str(e))
                logger.error("Can't open {}".format(file_name_eml))
                tarantool_queue_message.delete(row_res[0])
                continue
            
            tr_return = space_file_binary.insert((
                None,
                now_timestamp,
                "from_queue",
                byte_file
            ))
            content_id = tr_return[0][0]
            message_log['content_id'] = content_id
            message_log['smtps_rcp'][0]['to_addresses'][0]['status'] = "from_queue"
            message_log['address_configuration'] = addres_in_mem
            
            pika_connection = PIKA_CONNECTION("tasks")
            if pika_connection[0] is False:
                logger.error("Error connection pika!")
                continue
            if PIKA_PUBLISH(pika_connection[2],json.dumps(message_log),"tasks"):
                logger.info("publish message in rebbitmq from queue manager module")
            else:
                space_file_binary.delete(content_id)
                continue
            
            os.remove(file_name_eml)
            pika_connection[2].close()
            tarantool_queue_message.delete(row_res[0])
        
        sleep(60)
        
