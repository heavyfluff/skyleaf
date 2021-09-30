import dns.resolver
import json, os
from datetime import timedelta, datetime
from urllib.parse import urlparse
from aiosmtpd.spf import check2

from smtp_an.general_func import VALIDATION_PRIVATE_IP, ROTATE_IP, DNS_QUERY

from loguru import logger


@logger.catch
def SPAMHAUS_DBL_CHECK(code: str):
    result = ""
    if code == "127.0.1.2":
        result = "spam"
    elif code == "127.0.1.4":
        result = "phish"
    elif code == "127.0.1.5":
        result = "malware"
    elif code == "127.0.1.6":
        result = "botnet"
    elif code == "127.0.1.102":
        result = "abused legit spam"
    elif code == "127.0.1.103":
        result = "abused spammed redirector domain"
    elif code == "127.0.1.104":
        result = "abused legit phish"
    elif code == "127.0.1.105":
        result = "abused legit malware"
    elif code == "127.0.1.106":
        result = "abused legit botnet C&C"
    
    return result
    
@logger.catch
def SPAMHAUS_CHECK(md):
    start_time = datetime.now()
    result = {'SBL':[],'XBL':[],'PBL':[],'DBL':[]}
    
    for row_ip in md.smtpd_body['ips']:
        if VALIDATION_PRIVATE_IP(row_ip):
            r = DNS_QUERY("{}.zen.spamhaus.org".format(ROTATE_IP(row_ip)), 'a')
            for row_r in r:
                if str(row_r) == "127.0.0.2" or str(row_r) == "127.0.0.3" or str(row_r) == "127.0.0.9":
                    result['SBL'].append(row_ip)
                elif str(row_r) == "127.0.0.4":
                    result['XBL'].append(row_ip)
                elif str(row_r) == "127.0.0.10" or str(row_r) == "127.0.0.11":
                    result['PBL'].append(row_ip)
                
    for row_url in md.smtpd_body['urls']:
        row_urls_parse = urlparse(row_url)
        if row_urls_parse.netloc == "":
            continue
        r = DNS_QUERY("{}.dbl.spamhaus.org".format(row_urls_parse.netloc), 'a')
        for row_r in r:
            resDBL = SPAMHAUS_DBL_CHECK(str(row_r))
            if resDBL != "":
                result['DBL'].append("{}:{}".format(row_urls_parse.netloc,resDBL))

    for row_email in md.smtpd_body['emails']:
        domain = row_email[row_email.find("@")+1:]
        if domain == "":
            continue
        r = DNS_QUERY("{}.dbl.spamhaus.org".format(domain), 'a')
        for row_r in r:
            resDBL = SPAMHAUS_DBL_CHECK(str(row_r))
            if resDBL != "":
                result['DBL'].append("{}:{}".format(domain,resDBL))
    
    result['processing_time'] = md.count_time(start_time)
    md.smtpa_verdict['SPAMHAUS_CHECK'] = result

@logger.catch
def R_SPF_FAIL(md):
    start_time = datetime.now()
    result = {'value': ""}
    spf_result = check2(i=md.smtpd_ip,s=md.smtpd_body_headers['from'],h="",timeout=3)
    result['value'] = spf_result[0]
    
    result['processing_time'] = md.count_time(start_time)
    md.smtpa_verdict['R_SPF_FAIL'] = result
    
@logger.catch    
def DNSBL_SORBS_NET(md):
    start_time = datetime.now()
    result = {'status': False}
    for row_ip in md.smtpd_body['ips']:
        if VALIDATION_PRIVATE_IP(row_ip):
            r = DNS_QUERY("{}.dnsbl.sorbs.net".format(ROTATE_IP(row_ip)), 'a')
            for row_r in r:
                if str(row_r) == "127.0.0.6":
                    result['status'] = True
    
    result['processing_time'] = md.count_time(start_time)
    md.smtpa_verdict['DNSBL_SORBS_NET'] = result

@logger.catch    
def DNSBL_MAILSPIKE_NET(md):
    start_time = datetime.now()
    result = {'status': False}
    for row_ip in md.smtpd_body['ips']:
        if VALIDATION_PRIVATE_IP(row_ip):
            r = DNS_QUERY("{}.bl.mailspike.net".format(ROTATE_IP(row_ip)), 'a')
            for row_r in r:
                if str(row_r) == "127.0.0.10" or str(row_r) == "127.0.0.11" or str(row_r) == "127.0.0.12":
                    result['status'] = True
    
    result['processing_time'] = md.count_time(start_time)
    md.smtpa_verdict['DNSBL_MAILSPIKE_NET'] = result

@logger.catch    
def DNSBL_SURBL(md):
    start_time = datetime.now()
    result = {'status': False, 'list': []}
    for row_url in md.smtpd_body['urls']:
        row_urls_parse = urlparse(row_url)
        if row_urls_parse.netloc == "":
            continue
        r = DNS_QUERY("{}.multi.surbl.org".format(row_urls_parse.netloc), 'a')
        for row_r in r:
            if str(row_r) == "127.0.0.64":
                result['status'] = True
                result['list'].append(row_urls_parse.netloc)
    
    result['processing_time'] = md.count_time(start_time)
    md.smtpa_verdict['DNSBL_SURBL'] = result
    
