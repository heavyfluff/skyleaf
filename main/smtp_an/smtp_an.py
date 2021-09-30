import pika,os,json

from system.other import PIKA_CONNECTION, PIKA_PUBLISH, TARANTOOL_CONN, GET_CONF_FROM_MEM
from smtps.smtps import MAIL_SENDER
from system.system_class import MainData
from smtp_an.filter_list import FILTER_LIST
from smtp_an.body_analysis import M_BODY_PARSING, M_CHECKDMARC
from smtp_an.dnsbl_check import *
from smtp_an.general_func import *

from loguru import logger


def ANALYSIS_LEVEL_ONE(md):
    space_file_binary, tarantool_space_status = TARANTOOL_CONN("file_binary")
    if not tarantool_space_status:
        raise ErrorConnectionTarantool('Tarantool error!')
    tr_result = space_file_binary.select(md.content_id)
    
    M_BODY_PARSING(tr_result[0][3],md)
    result_checkdmarc = M_CHECKDMARC(md)
    
    ###
    ###
    ###
    
def ANALYSIS_LEVEL_TWO(md):
    j_config = GET_CONF_FROM_MEM(md.address_configuration)
    FILTER_LIST(md,j_config)
    
    MISSING_TO(md)
    MISSING_DATE(md)
    MISSING_MID(md)
    MISSING_SUBJECT(md,j_config)
    SUBJ_ALL_CAPS(md)
    FAKE_REPLAY(md)
    FILE_EXTENTION_BLACK(md)
    EMOJII_IN_SUBJECT(md)
    FORGED_RECIPIENTS(md)
    RISKY_COUNTRY(md,j_config)
    FROM_NOT_MAIL_FROM(md)
    
    ###
    ###
    ###
    
    
def ANALYSIS_LEVEL_THREE(md):
    j_config = GET_CONF_FROM_MEM(md.address_configuration)
    SPAMHAUS_CHECK(md)
    MX_SENDER_CHECK(md)
    R_SPF_FAIL(md)
    DNSBL_SORBS_NET(md)
    DNSBL_MAILSPIKE_NET(md)
    DNSBL_SURBL(md)
    ###
    ###
    ###
    GLOBAL_PROCESSING_TIME(md)
    COUNTING_SCORE(md)
    
    
    
def CALLBACK(ch, method, properties, body):
    data = json.loads(body.decode("utf-8"))
    md = MainData(**data)
    
    if md.next_action == "level_one":
        ANALYSIS_LEVEL_ONE(md)
        md.next_action = "level_two"
        if PIKA_PUBLISH(ch,json.dumps(md.__dict__),"tasks"):
            ch.basic_ack(delivery_tag = method.delivery_tag)
            return
        else:
            print("Error publish pika!")
            
    elif md.next_action == "level_two":
        ANALYSIS_LEVEL_TWO(md)
        md.next_action = "level_three"
        if PIKA_PUBLISH(ch,json.dumps(md.__dict__),"tasks"):
            ch.basic_ack(delivery_tag = method.delivery_tag)
            return
        else:
            print("Error publish pika!")
    
    elif md.next_action == "level_three":
        ANALYSIS_LEVEL_THREE(md)
        md.next_action = "send_mail"
        if PIKA_PUBLISH(ch,json.dumps(md.__dict__),"tasks"):
            ch.basic_ack(delivery_tag = method.delivery_tag)
            return
        else:
            print("Error publish pika!")
    
    elif md.next_action == "send_mail":
        MAIL_SENDER(md)
        ch.basic_ack(delivery_tag = method.delivery_tag)
        return
    
    elif md.next_action == "pull_in_db":
        ch.basic_ack(delivery_tag = method.delivery_tag)
        return
    else:
        ch.basic_ack(delivery_tag = method.delivery_tag)
        return
        
    
    
def SMTP_AN(addres_in_mem):

    pika_connection = PIKA_CONNECTION("tasks")
    if pika_connection[0] is False:
        print("Error connection pika!")
        return
    pika_connection[2].basic_consume("tasks", CALLBACK)
    pika_connection[2].start_consuming()
    
