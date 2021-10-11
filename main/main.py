import os
from multiprocessing import Process, shared_memory
from time import sleep
from loguru import logger

from initialization_system.rabbitmq import START_RABBITMQ
from initialization_system.tarantool import START_TARANTOOL
from configuration_manager.configuration_manager import CONFIGURATION_MANAGER
from system.other import GET_CONF_FROM_MEM
from system.cleaner_manager import CLEANER_MANAGER
from system.queue_manager import QUEUE_MANAGER
from smtp_dem.smtp_dem import SMTP_DEM
from smtp_an.smtp_an import SMTP_AN


MAX_MEM_FOR_CONF = 16384    # Max byte size for data configuration
log_name = "/var/log/skyleaf.log"
if "LOG_NAME" in os.environ:
    log_name = os.environ['LOG_NAME']

logger.add(log_name,
           format="{time} {level} {message}",
           level="DEBUG",
           rotation="10 MB",
           compression="zip")

if __name__ == "__main__":

    """ INITILIZATION """

    logger.info("Starting initilization.")

    """
    while True:
        print("!")
        sleep(40)
    """
    if not START_TARANTOOL():
        logger.error("Tarantool is not started.")
        exit(1)

    if not START_RABBITMQ():
        logger.error("Rabbitmq is not started.")
        exit(1)

    """ Getting configuration """

    j_config = {'version': 0}
    shm = shared_memory.SharedMemory(create=True, size=MAX_MEM_FOR_CONF)
    address_in_mem = shm.name
    logger.info("Starting configuration manager.")
    p_conf = Process(target=CONFIGURATION_MANAGER, args=[address_in_mem, MAX_MEM_FOR_CONF])
    p_conf.start()
    sleep(10)
    while True:
        j_config = GET_CONF_FROM_MEM(address_in_mem)
        if "version" in j_config:
            if j_config['version'] != 0:
                logger.info("Upload configuration successfully")
                break

        sleep(10)

    """ Start cleaner manager """
    logger.info("Starting cleaner manager.")
    cleaner_m = Process(target=CLEANER_MANAGER, args=[address_in_mem,])
    cleaner_m.start()

    """ Start queue manager """
    logger.info("Starting queue manager.")
    queue_m = Process(target=QUEUE_MANAGER, args=[address_in_mem,])
    queue_m.start()

    """ Start smtpd server """
    logger.info("Starting smtpd server.")
    smtpd_server = Process(target=SMTP_DEM, args=[address_in_mem,])
    smtpd_server.start()

    """ Start smtp senders """
    logger.info("Starting smtp senders.")
    proc_active_children = []
    for num in range(j_config['system']['max_active_workers']):
        sender = Process(target=SMTP_AN, args=[address_in_mem,])
        sender.start()
        proc_active_children.append(sender)

    """ MONITORIN """
    logger.info("Filtration node is ready!")
    while True:
        sleep(10)

        if p_conf.is_alive() is not True:
            logger.info("Starting configuration manager again.")
            p_conf = Process(target=CONFIGURATION_MANAGER, args=[address_in_mem,])
            p_conf.start()

        if cleaner_m.is_alive() is not True:
            logger.info("Starting cleaner manager again.")
            cleaner_m = Process(target=CLEANER_MANAGER, args=[address_in_mem,])
            cleaner_m.start()

        if queue_m.is_alive() is not True:
            logger.info("Starting queue manager again.")
            queue_m = Process(target=QUEUE_MANAGER, args=[address_in_mem,])
            queue_m.start()

        if smtpd_server.is_alive() is not True:
            logger.info("Starting smtpd server again.")
            smtpd_server = Process(target=SMTP_DEM, args=[address_in_mem,])
            smtpd_server.start()

        for i in range(len(proc_active_children)):
            if proc_active_children[i].is_alive() is not True:
                logger.info("Starting smtp senders again.")
                sender = Process(target=SMTP_AN, args=[address_in_mem,])
                sender.start()
                proc_active_children[i] = sender
