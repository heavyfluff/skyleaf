from datetime import timedelta, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import email.utils
from email.utils import formatdate

myid = email.utils.make_msgid()
now = datetime.now()
str_time_now = str(now.strftime("%Y-%m-%d %H:%M:%S"))

list_filename = ["./node/main/att.exe"]
message_d={}
message_d['mail_body'] = "http://shariksfoto.ru  114.237.155.243"
message_d['mail_filename'] = "legitimate2.doc"


msg = MIMEMultipart()
msg['From'] = "cesp@bi.zone"
msg['To'] = "p.pavlov@pavlov.ru"
msg['Subject'] = "🙆ПРИВЕТ!!! go_to_devcesp_in_legitimate: "+str_time_now
#msg['Subject'] = "ПРИВЕТ"
msg.add_header("Message-ID", myid)
msg.add_header("In-Reply-To", myid)
msg.add_header("References", myid)
msg['Date'] = formatdate(localtime=True)
#msg.attach(MIMEText(message_d['mail_body'], 'html'))
msg.attach(MIMEText(message_d['mail_body'], "plain", "utf-8"))


for row in list_filename:
	attachment = open(row, "rb")
	p = MIMEBase('application', 'octet-stream')
	p.set_payload((attachment).read())
	encoders.encode_base64(p)
	p.add_header('Content-Disposition', "attachment; filename= %s" % row)
	msg.attach(p)

	
s = smtplib.SMTP(host="127.0.0.1",port=10025)
s.set_debuglevel(1)
try:
	text = msg.as_string()
	s.helo("helo_cesp@bi.zone")
	s.sendmail(msg['From'], msg['To'], text)
	s.quit()
	print("Send email to "+msg['To']+" comlete.")
except:
	print("Send email to "+msg['To']+" error.")
	raise
