"""This is configuration manager."""

from time import sleep
from multiprocessing import shared_memory
from loguru import logger


@logger.catch
def CONFIGURATION_MANAGER(address_in_mem: str, max_mem_for_conf: int):
    """Load and check configuration from disk function."""
    while True:
        byte_config = b""
        with open('/main/configuration_manager/configuration.json', 'rb') as f:
            byte_config = f.read()
            f.close()

        res = bytearray(max_mem_for_conf)
        i = 0
        while i < len(byte_config):
            res[i] = byte_config[i]
            i += 1

        try:
            shared = shared_memory.SharedMemory(name=address_in_mem)
            shared.buf[0:len(res)] = res
        except Exception as e:
            logger.error(str(e))
        shared.close()
        # logger.info("Update configuration {}".format(address_in_mem))

        sleep(120)
