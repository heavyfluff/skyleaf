import os
import smtplib
import sys
  
 
def send_email():

  from_addr = "test1@test.ru"
  
  f = open('./node/main/6.eml','rb')
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
  #server = smtplib.SMTP(host="mx07.bi.zone",port=25)
  server = smtplib.SMTP(host="127.0.0.1",port=10025)
  #server = smtplib.SMTP(host="185.163.157.40",port=25)
  #server.starttls()
  server.helo(name="test.ru")
  server.set_debuglevel(1)
  server.sendmail(from_addr, emails, BODY)
  server.quit()
 
 
if __name__ == "__main__":
  emails = ["p.pavlov@bi.zone", "qwer@bi.zone","pasha_ne@yahoo.com"]
  #emails = ["p.pavlov@pavlov.ru", "test1@test.ru", "test2@test.ru","bubu@pavlov.ru","neg@neg.ru"]
  send_email()
