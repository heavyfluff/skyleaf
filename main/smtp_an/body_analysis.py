import json, os
import re
import mailparser
import email
from email.header import decode_header
import dkim
import checkdmarc
from loguru import logger


def M_CHECKDMARC(md):
    #############################################################
    # https://domainaware.github.io/checkdmarc/checkdmarc.html# #
    #############################################################
    result = {}
    try:
        res = checkdmarc.check_domains(md.smtpd_body_headers['from'][md.smtpd_body_headers['from'].find("@")+1:],
                                        parked=False,
                                        approved_nameservers=None,
                                        approved_mx_hostnames=None,
                                        skip_tls=True,
                                        include_dmarc_tag_descriptions=False,
                                        nameservers=None,
                                        timeout=2.0,
                                        wait=0.0)
        result = checkdmarc.results_to_json(res)
    except Exception as e:
        logger.error(str(e))
        pass
    return result


def M_BODY_PARSING(body: str, md):
    '''
    mail.attachments: list of all attachments
    mail.body
    mail.date: datetime object in UTC
    mail.defects: defect RFC not compliance
    mail.defects_categories: only defects categories
    mail.delivered_to
    mail.from_
    mail.get_server_ipaddress(trust="my_server_mail_trust")
    mail.headers
    mail.mail: tokenized mail in a object
    mail.message: email.message.Message object
    mail.message_as_string: message as string
    mail.message_id
    mail.received
    mail.subject
    mail.text_plain: only text plain mail parts in a list
    mail.text_html: only text html mail parts in a list
    mail.text_not_managed: all not managed text (check the warning logs to find content subtype)
    mail.to
    mail.to_domains
    mail.timezone: returns the timezone, offset from UTC
    mail.mail_partial: returns only the mains parts of emails
    '''
    
    ###DKIM CHECK###
    byte_data = str.encode(body)
    md.smtpd_dkim_verify = dkim.verify(byte_data)
    
    
    mail = mailparser.parse_from_string(body)
    #msg = email.message_from_string(body)
    
    dict_headers = dict(mail.headers)
    
    
    md.smtpd_body_headers['text_plain'] = mail.text_plain[0]
    
    md.smtpd_body_headers['to'] = []
    for row_to in mail.to:
        md.smtpd_body_headers['to'].append(row_to[1])
    
    if "Date" in dict_headers:
        md.smtpd_body_headers['Date'] = dict_headers['Date']
    if "In-Reply-To" in dict_headers:
        md.smtpd_body_headers['In-Reply-To'] = dict_headers['In-Reply-To']
    
    ### FROM
    if len(mail.from_) == 0:
        md.smtpd_body_headers['from'] = ""
    else:
        md.smtpd_body_headers['from'] = mail.from_[0][1]
        
    ### SUBJECT
    #subject = mail.subject
    md.smtpd_body_headers['Subject'] = mail.subject
    
    #md.smtpd_body_headers['Subject'] = subject.encode().decode("unicode-escape").encode().decode("unicode-escape")
    '''
    subject = ""
    dec = decode_header(msg['Subject'])
    if isinstance(dec[0][0], bytes):
        subject = dec[0][0].decode()
    else:
        subject = dec[0][0]
    md.smtpd_body_headers['Subject'] = subject
    '''
    
    md.smtpd_body_headers['message_id'] = mail.message_id
    for row in mail.attachments:
        md.smtpd_body['files'].append(row['filename'])
    
    ListTmp = re.findall(r'(https?://[^\s]+)', mail.body)
    for row in ListTmp:
        if row not in md.smtpd_body['urls']:
            md.smtpd_body['urls'].append(row)
            
    ListTmp = re.findall(r'[\w\.-]+@[\w\.-]+', mail.body)
    ListTmp.append(md.smtpd_body_headers['from'])
    ListTmp.append(md.smtpd_mail_from)
    for row in ListTmp:
        if row not in md.smtpd_body['emails']:
            md.smtpd_body['emails'].append(row)
            
    ListTmp = re.findall( r'[0-9]+(?:\.[0-9]+){3}', mail.body)
    ListTmp.append(md.smtpd_ip)
    for row in ListTmp:
        if row not in md.smtpd_body['ips']:
            if row.find("10.") != 0 and row.find("100.64.") != 0 and row.find("172.16.") != 0 and row.find("192.168.") != 0:
                md.smtpd_body['ips'].append(row)
    
    
    del mail
    #del msg
    
    
