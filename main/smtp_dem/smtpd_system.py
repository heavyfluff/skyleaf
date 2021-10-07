import re
from loguru import logger
from datetime import datetime
import ipaddress

from system.other import TARANTOOL_CONN


def RCPT_VALID(email):
    if len(email) > 7:
        if re.match("(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email) is not None:
            return True
        return False


def ADD_HEADER_IN_BODY(str_body, bind_address, hostname):
    result = "Received: {} ({})\r\n{}".format(hostname, bind_address, str_body)
    return result


def GET_SUBNET(ip_from: str):
    ip1 = ipaddress.ip_address(ip_from)
    ip_point = ip_from.split(".")
    i = 0
    while i <= 224:
        subnet = ipaddress.ip_network('{}.{}.{}.0/19'.format(ip_point[0],
                                                             ip_point[1],
                                                             str(i)))
        if ip1 in subnet:
            return str(subnet)
        i += 32
    return "NONE"


def GREYLITE_VALIDATION(ip_from, mail_from):
    tuple = "{}:{}".format(GET_SUBNET(ip_from), mail_from)

    result = True
    now = datetime.now()
    sp_greylite, tarantool_space_status = TARANTOOL_CONN('greylite')
    if tarantool_space_status:
        tr_result = sp_greylite.select(tuple)
        if tr_result.rowcount == 0:
            try:
                sp_greylite.insert((tuple, 1, int(now.timestamp())))
                logger.info("GREYLITE: Insert in tarantool greylite {}".format(tuple))
            except Exception as e:
                logger.error(str(e))
                logger.error("GREYLITE: Can't insert in tarantool greylite {}".format(tuple))
            result = False
            return result
        else:
            if tr_result[0][1] == 1:
                if tr_result[0][2] < (int(now.timestamp()) - 360):
                    try:
                        sp_greylite.update(tuple, [('+', 1, 1), ('=', 2, int(now.timestamp()))])
                        logger.info("GREYLITE: Update in tarantool greylite for {}".format(tuple))
                    except Exception as e:
                        logger.error(str(e))
                        logger.error("GREYLITE: Can't update in tarantool greylite for {}".format(tuple))
                    return result
                else:
                    result = False
                    return result
            else:
                try:
                    sp_greylite.update(tuple, [('+', 1, 1), ('=', 2, int(now.timestamp()))])
                    logger.info("GREYLITE: Update in tarantool greylite for {}".format(tuple))
                except Exception as e:
                    logger.error(str(e))
                    logger.error("GREYLITE: Can't update in tarantool greylite for {}".format(tuple))
                return result

    return result
