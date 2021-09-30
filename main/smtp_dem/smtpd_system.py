import os
import json
import re
import email
from email.header import decode_header

def RCPT_VALID(email):
    if len(email) > 7:
        if re.match("(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email) != None:
            return True
        return False



def ADD_HEADER_IN_BODY(str_body,bind_address,hostname):
    result = "Received: {} ({})\r\n{}".format(hostname,bind_address,str_body)
    return result

