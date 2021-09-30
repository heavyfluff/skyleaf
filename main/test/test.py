import os
import smtplib
import sys
  
 
def send_email():

  from_addr = "cesp@bi.zone"
  #from_addr = ""
  
  f = open('./filtration_node/main/test/3.eml','rb')
  BODY = f.read()
  f.close
  '''
  BODY = "\r\n".join((
    "From: %s" % from_addr,
    "To: %s" % ', '.join(emails),
    "Subject: %s" % subject ,
    "",
    body_text
  ))
  '''
  server = smtplib.SMTP(host="127.0.0.1",port=10025)
  #server = smtplib.SMTP(host="185.163.157.40",port=25)
  #server.starttls()
  server.helo(name="test@pavlov.ru")
  server.set_debuglevel(1)
  server.sendmail(from_addr, emails, BODY)
  server.quit()
 
 
if __name__ == "__main__":
  emails = ["test1@test.ru","test2@test.ru","pavlov@pavlov.ru"]
  #emails = ["p.pavlov@pavlov.ru", "test1@test.ru", "test2@test.ru","bubu@pavlov.ru","neg@neg.ru"]
  send_email()
