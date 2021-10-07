import tarantool
import os
import json
import pika
from multiprocessing import shared_memory
from loguru import logger
import base64


@logger.catch
def ADD_SCORE_FROM_CONFIG(j_config, METHOD):
    result = 0
    if "methods" in j_config:
        if METHOD in j_config['methods']:
            result = j_config['methods'][METHOD]
    return result


@logger.catch
def F_MAIL_ADDRESS_SLICER(email):
    return email[:email.find("@")], email[email.find("@") + 1:]


@logger.catch
def GET_CONF_FROM_MEM(address_in_mem):
    result = {}
    try:
        shm = shared_memory.SharedMemory(name=address_in_mem)
    except Exception as e:
        logger.error(str(e))
        logger.error("GET_CONFIGURATION_MODULE: Error - {}".format(str(e)))

    bytes = shm.buf.tobytes()
    str_conf = bytes.decode()
    point = str_conf.rfind("}") + 1
    str_conf = str_conf[:point]

    try:
        result = json.loads(str_conf)
    except Exception as e:
        logger.error(str(e))

    shm.close()

    return result


@logger.catch
def TARANTOOL_CONN(space):
    status = False
    link_space = None
    try:
        connection = tarantool.connect("127.0.0.1",
                                       3301,
                                       user=os.environ['TARANTOOL_USER'],
                                       password=os.environ['TARANTOOL_PASSWORD'])
        link_space = connection.space(space)
        status = True
    except Exception as e:
        logger.error(str(e))
        logger.error("ERROR connection tarantool {}".format(str(e)))
    return link_space, status


@logger.catch
def ENCODED_BASE(data: str):
    b = data.encode("UTF-8")
    e = base64.b16encode(b)
    return e.decode("UTF-8")


@logger.catch
def PIKA_PUBLISH(channel, str_data, queue_name):
    try:
        channel.basic_publish(exchange='', routing_key=queue_name, body=str_data)
    except Exception as e:
        logger.error(str(e))
        return False
    return True


@logger.catch
def PIKA_CONNECTION(queue_name):
    status = False
    connection = None
    channel = None
    try:
        PIKACREDENTIALS = pika.PlainCredentials(os.environ['RABBITMQ_USER'], os.environ['RABBITMQ_PASSWORD'])
        PIKAPARAMETERS = pika.ConnectionParameters("127.0.0.1", 5672, '/', PIKACREDENTIALS)
    except Exception as e:
        logger.error(str(e))

    i = 0
    while i < 10:
        try:
            connection = pika.BlockingConnection(PIKAPARAMETERS)
            channel = connection.channel()
            channel.queue_declare(queue=queue_name, durable=True)
            channel.basic_qos(prefetch_count=1)
            status = True
        except pika.exceptions.AMQPConnectionError:
            return status, connection, channel

        i += 1

    return status, connection, channel
