import sys, os, json

import random
import string



def GET_USER(length):
  letters = string.ascii_letters + string.digits
  return ''.join(random.choice(letters) for i in range(length))
  
def GET_PASSWORD(length):
  letters = string.ascii_letters + string.digits
  return ''.join(random.choice(letters) for i in range(length))
