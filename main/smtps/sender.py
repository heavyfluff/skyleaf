import dns.resolver
from loguru import logger


@logger.catch
def MERGE_RSP(rsp):
    result = []

    for row_rsp in rsp:
        key = False
        for row_result in result:
            domain_result = row_result['to_addresses'][0]['to_address'][row_result['to_addresses'][0]['to_address'].find("@") + 1:]
            domain_rsp = row_rsp['to_addresses'][0]['to_address'][row_rsp['to_addresses'][0]['to_address'].find("@") + 1:]
            if domain_result == domain_rsp:
                row_result['to_addresses'].append(row_rsp['to_addresses'][0])
                key = True
        if not key:
            result.append(row_rsp)

    return result


@logger.catch
def RETURN_RESPONSE_CODE(data):
    tmp = data.split(" ")
    return int(tmp[0])


@logger.catch
def UNIQ_BLOCK_MX(to_address):
    result = []
    to_domain = to_address[to_address.find("@") + 1:]
    resolver = dns.resolver.Resolver()
    resolver.timeout = 2
    resolver.lifetime = 2
    try:
        answers = resolver.query(to_domain, 'mx')
        for rdata in answers:
            dnsmx = rdata.to_text()
            temp = dnsmx.split()
            tempint = int(temp[0])
            result.append((tempint, temp[1]))
    except Exception as e:
        logger.error(str(e))
        pass

    return sorted(result, key=lambda tup: tup[0])


@logger.catch
def ADD_TAG_IN_SUBJECT(byte_data, tag):
    result = b''
    find_point = "Subject:"
    str_data = byte_data.decode()

    point_attachment = str_data.find("Content-Disposition: attachment;")
    point_subject = -1
    if point_attachment != -1:
        point_subject = str_data.find(find_point, 0, point_attachment)
    else:
        point_subject = str_data.find(find_point)

    if point_subject != -1:
        start = str_data[:point_subject + len(find_point)]
        end = str_data[point_subject + len(find_point):]
        str_data = "{}{}{}".format(start, tag, end)
        result = str_data.encode()
    else:
        result = byte_data

    return result
