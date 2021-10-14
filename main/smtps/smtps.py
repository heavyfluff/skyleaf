import json
import aiosmtpd.psmtplib
from datetime import datetime
import socket
from random import randint
from loguru import logger

from system.other import TARANTOOL_CONN, GET_CONF_FROM_MEM
from smtps.sender import UNIQ_BLOCK_MX, MERGE_RSP, ADD_TAG_IN_SUBJECT
from system.system_const import CONST_RESPONSE_CODES_FOR_QUEUE


@logger.catch
def GET_SOURCE_IP(row_smtps_rcp, node_name):
    result = ""
    if "from_ip_pool" not in row_smtps_rcp:
        return result
    if node_name in row_smtps_rcp['from_ip_pool']:
        len_list = len(row_smtps_rcp['from_ip_pool'][node_name])
        if len_list > 0:
            result = row_smtps_rcp['from_ip_pool'][randint(0, len_list)]

    return result


@logger.catch
def CHECK_CONN_SERVER(to_address_dict):
    if to_address_dict['status'] == "from_queue":
        return True
    if to_address_dict['status'] == "new":
        return True
    return False


@logger.catch
def CHECK_CONN_SERVER_ALL(domain):
    for row_address in domain['to_addresses']:
        if CHECK_CONN_SERVER(row_address):
            return True
    return False


@logger.catch
def SERVER_LOG_ADD_ROW(response_code, response, now, row_to_address):
    if response_code in CONST_RESPONSE_CODES_FOR_QUEUE:
        row_to_address['status'] = "queue"
        row_to_address['queue_count'] += 1
        row_to_address['log'].append({'date': now.strftime("%Y-%m-%d %H:%M:%S"),
                                      'response': response,
                                      'response_code': response_code})
    elif response_code == 250:
        row_to_address['status'] = "delivered"
        row_to_address['log'].append({'date': now.strftime("%Y-%m-%d %H:%M:%S"),
                                      'response': response,
                                      'response_code': response_code})
    else:
        row_to_address['status'] = "rejected"
        row_to_address['log'].append({'date': now.strftime("%Y-%m-%d %H:%M:%S"),
                                      'response': response,
                                      'response_code': response_code})


@logger.catch
def MAIL_SENDER(md):

    space_file_binary, tarantool_space_status = TARANTOOL_CONN("file_binary")
    if not tarantool_space_status:
        raise ErrorConnectionTarantool('Tarantool error!')
    db_tarantool = space_file_binary.select(md.content_id)
    if db_tarantool.rowcount == 0:
        logger.error("Error sender. File binary not fount in tarantool!")
        return

    byte_data = str.encode(db_tarantool[0][3])
    now = datetime.now()

    j_config = GET_CONF_FROM_MEM(md.address_configuration)
    ###################################
    #                     incomming   #
    ###################################

    if j_config['node']['type'] == "incomming":

        for row_smtps_rcp in md.smtps_rcp:
            if CHECK_CONN_SERVER_ALL(row_smtps_rcp) is False:
                continue

            bind_ip = GET_SOURCE_IP(row_smtps_rcp, j_config['node']['hostname'])
            bind_port = 0

            try:
                server = aiosmtpd.psmtplib.SMTP(host=row_smtps_rcp['dst_ip'],
                                                port=row_smtps_rcp['dst_port'],
                                                timeout=2,
                                                source_address=(bind_ip, bind_port))
                server.helo("helo_cesp@bi.zone")
                # server.set_debuglevel(1)
                if md.smtpd_starttls_status:
                    try:
                        server.starttls()
                    except aiosmtpd.psmtplib.SMTPNotSupportedError:
                        logger.error("SMTP SENDER: Remote host {} not supported starttls. I turn off the starttls for him.".format(row_smtps_rcp['dst_ip']))
                        pass
                for row_address in row_smtps_rcp['to_addresses']:
                    if CHECK_CONN_SERVER(row_address):
                        if row_address['is_tagged']:
                            result_sendmain = server.sendmail(j_config['sender_module']['header_mail_from'],
                                                              row_address['to_address'],
                                                              ADD_TAG_IN_SUBJECT(byte_data, row_smtps_rcp['thresholds']['tag']))
                        else:
                            result_sendmain = server.sendmail(j_config['sender_module']['header_mail_from'], row_address['to_address'], byte_data)
                        SERVER_LOG_ADD_ROW(result_sendmain[0], result_sendmain[1].decode(), now, row_address)

            except ConnectionRefusedError:
                for row_address in row_smtps_rcp['to_addresses']:
                    SERVER_LOG_ADD_ROW(10000, "Connection refused", now, row_address)

            except socket.timeout:
                for row_address in row_smtps_rcp['to_addresses']:
                    SERVER_LOG_ADD_ROW(10001, "Timeout error", now, row_address)

            except Exception:
                for row_address in row_smtps_rcp['to_addresses']:
                    SERVER_LOG_ADD_ROW(10001, "Exception", now, row_address)

    else:
        ###################################
        #                     outgoing    #
        ###################################

        md.smtps_rcp = MERGE_RSP(md.smtps_rcp)
        for row_smtps_rcp in md.smtps_rcp:
            row_smtps_rcp['mxs'] = UNIQ_BLOCK_MX(row_smtps_rcp['to_addresses'][0]['to_address'])

            bind_ip = GET_SOURCE_IP(row_smtps_rcp, j_config['node']['hostname'])
            bind_port = 0

            for row_mx in row_smtps_rcp['mxs']:
                try:
                    server = aiosmtpd.psmtplib.SMTP(host=row_mx[1],
                                                    port=25,
                                                    timeout=2,
                                                    source_address=(bind_ip, bind_port))
                    server.helo("helo_cesp@bi.zone")
                    result_sendmain = (0, "")
                    for row_address in row_smtps_rcp['to_addresses']:
                        if row_address['is_tagged']:
                            result_sendmain = server.sendmail(md.smtpd_mail_from,
                                                              row_address['to_address'],
                                                              ADD_TAG_IN_SUBJECT(byte_data, row_smtps_rcp['thresholds']['tag']))
                        else:
                            result_sendmain = server.sendmail(md.smtpd_mail_from, row_address['to_address'], byte_data)
                        SERVER_LOG_ADD_ROW(result_sendmain[0], result_sendmain[1].decode(), now, row_address)
                    break

                except ConnectionRefusedError:
                    for row_address in row_smtps_rcp['to_addresses']:
                        SERVER_LOG_ADD_ROW(10000, "Connection refused", now, row_address)

                except socket.timeout:
                    for row_address in row_smtps_rcp['to_addresses']:
                        SERVER_LOG_ADD_ROW(10001, "Timeout error", now, row_address)

                except Exception:
                    for row_address in row_smtps_rcp['to_addresses']:
                        SERVER_LOG_ADD_ROW(10001, "Exception", now, row_address)

    md.add_in_db()
    print(json.dumps(md.__dict__, indent=4))

    del byte_data
    return
