import json
import os
from datetime import timedelta, datetime
from time import sleep
from loguru import logger

from system.other import GET_CONF_FROM_MEM


@logger.catch
def ANALYSIS_FILE_NAME(type,j_config):

    """ Function for deleting old messages from the disk """

    result = {}
    now = datetime.now()
    now_timestamp = int(now.timestamp())
    
    if type == "delivered":
        ttl = 3600*j_config['ttl']['delivered']
    elif type == "quarantine":
        ttl = 3600*j_config['ttl']['quarantined']
    elif type == "rejected":
        ttl = 3600*j_config['ttl']['rejected']
    else:
        return
    
    for root, dirs, files in os.walk("/{}/".format(type)):
        for filename in files:
            if filename.find(".log") != -1:
                file_name_meta = filename[:filename.find(".log")]
                list_meta = file_name_meta.split("_")
                
                if len(list_meta) == 3:
                    try:
                        if int(list_meta[2])+ttl < now_timestamp:
                            result[file_name_meta] = list_meta
                    except:
                        pass
    
    for row in list(result):
        file_name_eml = "/{}/{}.eml".format(type,row)
        file_name_log = "/{}/{}.log".format(type,row)
        try:
            os.remove(file_name_log)
            logger.info("Delete {}".format(file_name_log))
        except Exception as e:
            logger.error(str(e))
            logger.error("Can't delete {}".format(file_name_log))
        
        try:
            os.remove(file_name_eml)
            logger.info("Delete {}".format(file_name_eml))
        except Exception as e:
            logger.error(str(e))
            logger.error("Can't delete {}".format(file_name_eml))
    

@logger.catch
def CLEANER_MANAGER(addres_in_mem):

    while True:
        sleep(60)
        
        j_config = GET_CONF_FROM_MEM(addres_in_mem)
        ANALYSIS_FILE_NAME("delivered",j_config)
        ANALYSIS_FILE_NAME("quarantine",j_config)
        ANALYSIS_FILE_NAME("rejected",j_config)
