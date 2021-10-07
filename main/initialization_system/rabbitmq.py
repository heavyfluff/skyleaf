import os
from loguru import logger

from initialization_system.generate_credential import GET_USER, GET_PASSWORD


def START_RABBITMQ():

    # os.environ['RABBITMQ_USER'] = GET_USER(8)
    # os.environ['RABBITMQ_PASSWORD'] = GET_PASSWORD(8)
    # logger.info("Generate password for rabbitmq.")
    os.environ['RABBITMQ_USER'] = "guest"
    os.environ['RABBITMQ_PASSWORD'] = "guest"
    os.system('/etc/init.d/rabbitmq-server start')
    # os.system('service rabbitmq-server start')

    # os.system('rabbitmqctl delete_user guest')

    # os.system("rabbitmqctl add_user " + os.environ['RABBITMQ_USER'] + " " + os.environ['RABBITMQ_PASSWORD'])
    # os.system("rabbitmqctl set_user_tags " + os.environ['RABBITMQ_USER'] + " administrator")
    # os.system('rabbitmqctl set_permissions -p / ' + os.environ['RABBITMQ_USER'] + ' ".*" ".*" ".*"')
    return True
