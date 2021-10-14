import dns.resolver
from datetime import datetime
import socket
from smtp_an.general_const import file_extention_balck_list, emoji_list, risky_country, stop_words_list
from system.other import ADD_SCORE_FROM_CONFIG
import string

from loguru import logger


@logger.catch
def BAYES_FROMAT_STRING(data: str) -> list:
    text = data.translate(str.maketrans('', '', string.punctuation))
    text = text.translate(text.maketrans('\r\n', '  '))
    text = text.lower()

    wl = text.split()
    result = []
    for row in wl:
        if len(row) > 2:
            result.append(row)
    return result


@logger.catch
def COUNTING_SCORE(md):
    # COUNTING TOTAL SCORE ###
    summ = 0
    for row in md.smtpa_verdict.keys():
        if "score" in md.smtpa_verdict[row]:
            summ += md.smtpa_verdict[row]['score']
    md.smtpa_hits = summ

    # COUNTING INDIVIDUAL SCORE ###
    for row_rcp in md.smtps_rcp:
        for row_address in row_rcp['to_addresses']:
            row_address['hits'] = md.smtpa_hits
            for row_method in row_address['verdict'].keys():
                if "score" in row_address['verdict'][row_method]:
                    row_address['hits'] += row_address['verdict'][row_method]['score']

    # CHECK THRESHOLDS ###
            if row_address['hits'] >= row_rcp['thresholds']['spam']:
                row_address['status'] = "quarantined"
            elif row_address['hits'] < row_rcp['thresholds']['spam'] and row_address['hits'] >= row_rcp['thresholds']['not_spam']:
                row_address['is_tagged'] = True
            elif row_address['hits'] < row_rcp['thresholds']['not_spam']:
                pass


@logger.catch
def GLOBAL_PROCESSING_TIME(md):
    start_time = datetime.now()
    end = int(start_time.timestamp())
    md.global_processing_time = end - md.date_timestamp


@logger.catch
def DNS_QUERY(row, type):
    result = []

    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 2
        resolver.lifetime = 2
        result = resolver.query(row, type)
    except dns.resolver.NXDOMAIN:
        pass
    except dns.name.EmptyLabel:
        pass
    except dns.resolver.NoAnswer:
        pass
    except dns.exception.Timeout:
        pass
    except Exception as e:
        logger.error(str(e))
        pass

    return result


@logger.catch
def VALIDATION_PRIVATE_IP(ip: str):
    if ip.find("10.") != 0 and ip.find("100.64.") != 0 and ip.find("172.16.") != 0 and ip.find("192.168.") != 0 and ip.find("172.17.") != 0:
        return True
    else:
        return False


@logger.catch
def ROTATE_IP(ip: str):
    try:
        tmp = ip.split(".")
        return "{}.{}.{}.{}".format(tmp[3], tmp[2], tmp[1], tmp[0])
    except Exception as e:
        logger.error(str(e))


@logger.catch
def MISSING_MID(md, j_config):
    start_time = datetime.now()
    result = {'status': False, 'score': 0}
    if md.smtpd_body_headers['message_id'] == "":
        result['status'] = True
        result['score'] = ADD_SCORE_FROM_CONFIG(j_config, "MISSING_MID")
    result['processing_time'] = md.count_time(start_time)
    md.smtpa_verdict['MISSING_MID'] = result


@logger.catch
def STOP_WORDS(md, j_config):
    start_time = datetime.now()
    result = {'status': False, 'score': 0}
    text = md.smtpd_body_headers['text_plain'].lower()
    for row in stop_words_list:
        if text.find(row) != -1:
            result['status'] = True
            result['score'] = ADD_SCORE_FROM_CONFIG(j_config, "STOP_WORDS")
            break
    result['processing_time'] = md.count_time(start_time)
    md.smtpa_verdict['STOP_WORDS'] = result


@logger.catch
def MISSING_TO(md, j_config):
    start_time = datetime.now()
    result = {'status': False, 'score': 0}
    if len(md.smtpd_body_headers['to']) == 0:
        result['status'] = True
        result['score'] = ADD_SCORE_FROM_CONFIG(j_config, "MISSING_TO")
    result['processing_time'] = md.count_time(start_time)
    md.smtpa_verdict['MISSING_TO'] = result


@logger.catch
def SUBJ_ALL_CAPS(md, j_config):
    start_time = datetime.now()
    result = {'status': False, 'score': 0}
    if md.smtpd_body_headers['Subject'].isupper():
        result['status'] = True
        result['score'] = ADD_SCORE_FROM_CONFIG(j_config, "SUBJ_ALL_CAPS")
    result['processing_time'] = md.count_time(start_time)
    md.smtpa_verdict['SUBJ_ALL_CAPS'] = result


@logger.catch
def MISSING_SUBJECT(md, j_config):
    start_time = datetime.now()
    result = {'status': False, 'score': 0}
    if md.smtpd_body_headers['Subject'] == "":
        result['status'] = True
        result['score'] = ADD_SCORE_FROM_CONFIG(j_config, "MISSING_SUBJECT")
    result['processing_time'] = md.count_time(start_time)
    md.smtpa_verdict['MISSING_SUBJECT'] = result


@logger.catch
def FAKE_REPLAY(md, j_config):
    start_time = datetime.now()
    result = {'status': False, 'score': 0}
    low = md.smtpd_body_headers['Subject'].lower()
    if low.find("re:") == 0 and "In-Reply-To" not in md.smtpd_body_headers:
        result['status'] = True
        result['score'] = ADD_SCORE_FROM_CONFIG(j_config, "FAKE_REPLAY")
    result['processing_time'] = md.count_time(start_time)
    md.smtpa_verdict['FAKE_REPLAY'] = result


@logger.catch
def MISSING_DATE(md, j_config):
    start_time = datetime.now()
    result = {'status': False, 'score': 0}
    if "Date" in md.smtpd_body_headers:
        result['status'] = True
        result['score'] = ADD_SCORE_FROM_CONFIG(j_config, "MISSING_DATE")
    result['processing_time'] = md.count_time(start_time)
    md.smtpa_verdict['MISSING_DATE'] = result


@logger.catch
def FILE_EXTENTION_BLACK(md, j_config):
    start_time = datetime.now()
    result = {'status': False, 'data': [], 'score': 0}
    for row_file in md.smtpd_body['files']:
        if row_file[row_file.rfind(".") + 1:] in file_extention_balck_list:
            result['data'].append(row_file)
    if len(result['data']) > 0:
        result['status'] = True
        result['score'] = ADD_SCORE_FROM_CONFIG(j_config, "FILE_EXTENTION_BLACK")
    result['processing_time'] = md.count_time(start_time)
    md.smtpa_verdict['FILE_EXTENTION_BLACK'] = result


@logger.catch
def EMOJII_IN_SUBJECT(md, j_config):
    start_time = datetime.now()
    result = {'status': False, 'score': 0}
    for row_emoji in emoji_list:
        if md.smtpd_body_headers['Subject'].find(row_emoji) != -1:
            result['status'] = True
            result['score'] = ADD_SCORE_FROM_CONFIG(j_config, "EMOJII_IN_SUBJECT")
    result['processing_time'] = md.count_time(start_time)
    md.smtpa_verdict['EMOJII_IN_SUBJECT'] = result


@logger.catch
def FORGED_RECIPIENTS(md, j_config):
    start_time = datetime.now()
    result = {'status': False, 'score': 0}
    for row_domain in md.smtps_rcp:
        for row_rcpt in row_domain['to_addresses']:
            if row_rcpt['to_address'] not in md.smtpd_body_headers['to']:
                result['score'] = ADD_SCORE_FROM_CONFIG(j_config, "FORGED_RECIPIENTS")
                result['status'] = True
    result['processing_time'] = md.count_time(start_time)
    md.smtpa_verdict['FORGED_RECIPIENTS'] = result


@logger.catch
def RISKY_COUNTRY(md, j_config):
    start_time = datetime.now()
    result = {'status': False,
              'score': 0,
              'data': []}

    for row_rd in risky_country:
        if md.smtpd_mail_from.endswith(row_rd):
            result['data'].append("{}:{}".format(md.smtpd_mail_from, row_rd))
        if md.smtpd_body_headers['from'].endswith(row_rd):
            result['data'].append("{}:{}".format(md.smtpd_body_headers['from'], row_rd))
    if len(result['data']) > 0:
        result['score'] = ADD_SCORE_FROM_CONFIG(j_config, "RISKY_COUNTRY")

    result['processing_time'] = md.count_time(start_time)
    md.smtpa_verdict['RISKY_COUNTRY'] = result


@logger.catch
def MX_SENDER_CHECK_CHILD(domain: str):
    if domain != "":
        r = DNS_QUERY(domain, 'mx')
        preference = 1000
        mx = ""
        for row_r in r:
            tmpStr = str(row_r)
            tmpList = tmpStr.split(" ")
            if int(tmpList[0]) < preference:
                preference = int(tmpList[0])
                mx = tmpList[1]
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.settimeout(1)
            s.connect((mx, 25))
            s.close()
            return False, ""
        except Exception:
            return True, domain
    else:
        return False, ""


@logger.catch
def MX_SENDER_CHECK(md, j_config):
    start_time = datetime.now()
    result = {'status': False, 'data': [], 'score': 0}

    domain = md.smtpd_mail_from[md.smtpd_mail_from.find("@") + 1:]
    status, row = MX_SENDER_CHECK_CHILD(domain)
    if status:
        result['data'].append(domain)

    domain = md.smtpd_body_headers['from'][md.smtpd_body_headers['from'].find("@") + 1:]
    status, row = MX_SENDER_CHECK_CHILD(domain)
    if status:
        result['data'].append(domain)

    if len(result['data']) == 0:
        result['status'] = True
        result['score'] = ADD_SCORE_FROM_CONFIG(j_config, "MX_SENDER_CHECK")

    result['processing_time'] = md.count_time(start_time)
    md.smtpa_verdict['MX_SENDER_CHECK'] = result


@logger.catch
def FROM_NOT_MAIL_FROM(md, j_config):
    start_time = datetime.now()
    result = {'status': False, 'score': 0}

    from_domain = md.smtpd_body_headers['from'][md.smtpd_body_headers['from'].find("@") + 1:]
    mail_from_domain = md.smtpd_mail_from[md.smtpd_mail_from.find("@") + 1:]
    if from_domain != mail_from_domain:
        result['status'] = True
        result['score'] = ADD_SCORE_FROM_CONFIG(j_config, "FROM_NOT_MAIL_FROM")
    result['processing_time'] = md.count_time(start_time)
    md.smtpa_verdict['FROM_NOT_MAIL_FROM'] = result
