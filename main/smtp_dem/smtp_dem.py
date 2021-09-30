from aiosmtpd.controller import Controller
from aiosmtpd.smtp import Envelope
import os, json
import asyncore
from time import sleep
from datetime import timedelta, datetime
import ssl
from loguru import logger

from system.system_class import MainData
from system.other import TARANTOOL_CONN, PIKA_CONNECTION, PIKA_PUBLISH, F_MAIL_ADDRESS_SLICER, GET_CONF_FROM_MEM
                                                                
from smtp_dem.smtpd_system import ADD_HEADER_IN_BODY, RCPT_VALID



def send_byte_data_in_tarantool(space,time,content):

    """ Function for adding binary information to the Tarantool database """

    tr_return = space.insert((None,time,"description",content))
    return tr_return[0][0]

def return_struct_row_address(address):

    """ Data structure return function """

    return {'to_address':address,
            'log':[],
            'queue_count':0,
            'status':"new",
            'is_tagged': False,
            'hits':0,
            #'analysis_status':"starting",
            'verdict':{'FILTER_LIST':{}}}
    
class CustomHandler:

    async def handle_RCPT(self, server, session, envelope, maindata, address, rcpt_options ):
        try:
            valid = RCPT_VALID(address)
        except BaseException as e:
            logger.error(str(e))
        except Exception as e:
            logger.error(str(e))
            
        if not valid:
            return "501 5.5.4 invalid email address"
        
        slice_rcpt = F_MAIL_ADDRESS_SLICER(address)
        to_name = slice_rcpt[0]
        to_domain = slice_rcpt[1]
        
        slice_rcpt = F_MAIL_ADDRESS_SLICER(envelope.mail_from)
        from_name = slice_rcpt[0]
        from_domain = slice_rcpt[1]
        
        j_config = GET_CONF_FROM_MEM(maindata.address_configuration)
        
        if j_config['node']['type'] == "incomming":
            if to_domain in j_config['domains'].keys():
                for row_pseg in maindata.smtps_rcp:
                    if to_domain == row_pseg['domain']:
                        row_address = return_struct_row_address(address)
                        row_pseg['to_addresses'].append(row_address)
                        envelope.rcpt_tos.append(address)
                        return "250 OK address"
                row_pseg = j_config['domains'][to_domain]
                row_pseg['to_addresses'] = [return_struct_row_address(address)]
                maindata.smtps_rcp.append(row_pseg)
                        
            else:
                return "501 5.5.4 recipient rejected"

        else:
            if from_domain in j_config['domains'].keys():
                row_pseg = j_config['domains'][from_domain]
                if 'to_addresses' in row_pseg:
                    row_pseg['to_addresses'].append(return_struct_row_address(address))
                else:
                    row_pseg['to_addresses'] = [return_struct_row_address(address)]
                maindata.smtps_rcp.append(row_pseg)
            else:
                return "501 5.5.4 recipient rejected"
            
        
        envelope.rcpt_tos.append(address)
        return "250 OK address"
        
    
    async def handle_DATA(self, server, session, envelope, maindata):
        
        str_original_content = envelope.original_content.decode()
        j_config = GET_CONF_FROM_MEM(maindata.address_configuration)
        
        ### SEND BYNARY DATA IN TARANTOOL ###
        node_bind_address = j_config['node']['bind_address']
        node_hostname = j_config['node']['hostname']
        
        space_file_binary, tarantool_space_status = TARANTOOL_CONN("file_binary")
        if not tarantool_space_status:
            raise ErrorConnectionTarantool('Tarantool error!')
        maindata.content_id = send_byte_data_in_tarantool(space_file_binary,
                                                            maindata.date_timestamp,
                                                            ADD_HEADER_IN_BODY(str_original_content,node_bind_address,node_hostname))
        
        
        
        del str_original_content
        #del headers_mail
        
        ### SEND META DATA IN PIKA ###
        pika_connection = PIKA_CONNECTION("tasks")
        if pika_connection[0] is False:
            logger.info("Error connection pika!")
            return
        if PIKA_PUBLISH(pika_connection[2],json.dumps(maindata.__dict__),"tasks"):
            pass
        else:
            space_file_binary.delete(maindata.content_id)
        
        
        return '250 OK data'
    


@logger.catch
def SMTP_DEM(address_in_mem):
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain('/filtration_node/smtp_dem/starttls/cert.pem', '/filtration_node/smtp_dem/starttls/key.pem')
    
    j_config = GET_CONF_FROM_MEM(address_in_mem)
    
    handler = CustomHandler()
    controller = Controller(handler,
                            hostname=j_config['node']['bind_address'],
                            port=j_config['node']['bind_port'],
                            tls_context=context,
                            require_starttls=True,
                            address_in_mem = address_in_mem)
    
    controller.start()
    while True:
        sleep(30)
