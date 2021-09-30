import os
from time import sleep
import json
from datetime import timedelta, datetime
from loguru import logger

from system.other import TARANTOOL_CONN


@logger.catch
def F_SEPARATION_DATA(data) -> dict:

    """ Data separation function """

    result = []
    main_data = json.loads(data)
        
    for row_domain in main_data['smtps_rcp']:
        for row_address in row_domain['to_addresses']:
            tmp_data = json.loads(data)
            del tmp_data['smtps_rcp']
            
            tmp_domains = json.loads(json.dumps(row_domain))
            tmp_domains['to_addresses'] = [json.loads(json.dumps(row_address))]
            tmp_data['smtps_rcp'] = [tmp_domains]
            
            result.append(tmp_data)
    
    return result

@logger.catch
def F_INSERT_OR_UPDATE_MESSAGE_LOG(space,data):
    if data['status'] == "created":
        tr_return = space.insert((
            None,
            data['smtps_rcp'][0]['organisation_id'],
            data['smtpd_body_headers']['from'],
            data['smtps_rcp'][0]['to_addresses'][0]['to_address'],
            data['smtpd_ip'],
            data['smtpd_body_headers']['Subject'],
            data['smtps_rcp'][0]['to_addresses'][0]['status'],
            data['date_timestamp'],
            json.dumps(data)
        ))
    elif data['status'] == "from_queue":
        tr_return = space.update(data['smtps_db_id'], [('=',5,data['smtps_rcp'][0]['to_addresses'][0]['status']),('=',8,json.dumps(data))])
    elif data['status'] == "from_quarantine":
        tr_return = space.update(data['smtps_db_id'], [('=',5,data['smtps_rcp'][0]['to_addresses'][0]['status']),('=',8,json.dumps(data))])
    
    return tr_return

@logger.catch
def F_CHECK_QUEUE(data,space):
    if data['smtps_rcp'][0]['to_addresses'][0]['status'] == "queue":
        '''
        start_second = data['smtps_rcp'][0][0]['queue_count']*400
        if start_second > 86400:
            start_second = 86400
        '''
        now = datetime.now()
        
        start_second = 120
        tarantool_queue_message, tarantool_space_status = TARANTOOL_CONN('queue_message')
        if not tarantool_space_status:
            raise ErrorConnectionTarantool('Tarantool error queue_message!')
            
        tr_return = tarantool_queue_message.insert((
            None,
            data['smtps_rcp'][0]['organisation_id'],
            data['smtps_db_id'],
            int(data['date_timestamp']),
            int(now.timestamp()+start_second),
            json.dumps(data)
        ))
        
        file_name = "/queue/{}.eml".format(str(tr_return[0][0]))
        tr_return = space.select(data['content_id'])
        byte_file = open(file_name, 'wb')
        byte_file.write(str.encode(tr_return[0][3]))
        byte_file.close()
        

@logger.catch        
def F_CHECK_QUARANTINE_OR_DELIVERED(data,space):
    if data['smtps_rcp'][0]['to_addresses'][0]['status'] == "quarantined" or data['smtps_rcp'][0]['to_addresses'][0]['status'] == "delivered" or data['smtps_rcp'][0]['to_addresses'][0]['status'] == "rejected":
        now = datetime.now()
        
        path_file_name = "{}_{}_{}".format(data['date_string'],                                             ### Created date
                                            str(data['smtps_db_id']),                                     ### Message log ID in tarantool
                                            str(data['date_timestamp']))                                ### Created Date timestamp format   
                                        
        if data['smtps_rcp'][0]['to_addresses'][0]['status'] == "quarantined":
            file_name = "/quarantine/{}.eml".format(path_file_name)
            log_file_name = "/quarantine/{}.log".format(path_file_name)
        elif data['smtps_rcp'][0]['to_addresses'][0]['status'] == "delivered":
            file_name = "/delivered/{}.eml".format(path_file_name)
            log_file_name = "/delivered/{}.log".format(path_file_name)
        elif data['smtps_rcp'][0]['to_addresses'][0]['status'] == "rejected":
            file_name = "/rejected/{}.eml".format(path_file_name)
            log_file_name = "/rejected/{}.log".format(path_file_name)
        else:
            return
        
        
        tr_return = space.select(data['content_id'])
        byte_file = open(file_name, 'wb')
        byte_file.write(str.encode(tr_return[0][3]))
        byte_file.close()
        
        log_file = open(log_file_name, 'w')
        log_file.write(json.dumps(data))
        log_file.close()

@logger.catch        
def F_CHECK_BLOCKED(data,space):
    tr_return = space.insert((
        None,
        0,
        data['smtpd_mail_from'],
        "",
        data['smtpd_ip'],
        "",
        data['status'],
        data['date_timestamp'],
        json.dumps(data)
    ))

def ADD_IN_DATABASE_ROW_EMAIL(data: str):
    tarantool_message_log, tarantool_space_status = TARANTOOL_CONN('message_log')
    if not tarantool_space_status:
        raise ErrorConnectionTarantool('Tarantool error!')
    
    
    j_data = json.loads(data)
    if j_data['status'] == "blocked":
        F_CHECK_BLOCKED(j_data,tarantool_message_log)
    else:
        
        list_rows = F_SEPARATION_DATA(data)
        space_file_binary, tarantool_space_status = TARANTOOL_CONN('file_binary')
        if not tarantool_space_status:
            raise ErrorConnectionTarantool('Tarantool error!')
        
        for message_row in list_rows:

            tr_return = F_INSERT_OR_UPDATE_MESSAGE_LOG(tarantool_message_log,message_row)
            message_row['smtps_db_id'] = tr_return[0][0]
            F_CHECK_QUEUE(message_row,space_file_binary)
            F_CHECK_QUARANTINE_OR_DELIVERED(message_row,space_file_binary)
        
        db_tarantool = space_file_binary.delete(list_rows[0]['content_id'])
