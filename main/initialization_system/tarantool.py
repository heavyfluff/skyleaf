import os
from loguru import logger

from initialization_system.generate_credential import GET_PASSWORD


@logger.catch
def START_TARANTOOL():
    os.environ['TARANTOOL_USER'] = "admin"
    os.environ['TARANTOOL_PASSWORD'] = GET_PASSWORD(10)
    logger.info("Generate password for tarantool.")

    try:
        config_file = []
        with open("/etc/tarantool/instances.enabled/start_config.lua", 'r') as f:
            for line in f:
                if line.find("box.schema.user.passwd('admin'") == -1:
                    config_file.append(line)
                else:
                    config_file.append("box.schema.user.passwd('admin', '{}')\n".format(os.environ['TARANTOOL_PASSWORD']))

        with open("/etc/tarantool/instances.enabled/start_config.lua", 'w') as f:
            for line in config_file:
                f.write(line)
    except Exception as e:
        logger.error(str(e))
        return False

    os.system('tarantoolctl start start_config')
    # os.system('tarantool /etc/tarantool/instances.enabled/start_config.lua')
    return True
