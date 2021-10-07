from datetime import datetime

from system.other import TARANTOOL_CONN, ADD_SCORE_FROM_CONFIG

from loguru import logger


def M_FILTER_LIST_ACTION(key, row_address, row_filter_list, j_config, result):
    row_address['verdict']['FILTER_LIST'] = {'id': row_filter_list[0],
                                             'value': row_filter_list[2],
                                             'action': row_filter_list[3]}

    if row_filter_list[3] == "deny":
        if "FILTER_LIST_BLACK" in j_config['methods']:
            row_address['verdict']['FILTER_LIST']['score'] = ADD_SCORE_FROM_CONFIG(j_config, "FILTER_LIST_BLACK")

    elif row_filter_list[3] == "permit":
        if "FILTER_LIST_WHITE" in j_config['methods']:
            row_address['verdict']['FILTER_LIST']['score'] = ADD_SCORE_FROM_CONFIG(j_config, "FILTER_LIST_WHITE")


def FILTER_LIST(md, j_config):
    result = {'row': []}
    start_time = datetime.now()
    space_filter_list, tarantool_space_status = TARANTOOL_CONN('filter_list')
    if not tarantool_space_status:
        raise ErrorConnectionTarantool('Tarantool error!')

    from_domain = md.smtpd_body_headers['from'][:md.smtpd_body_headers['from'].find("@") + 1]

    for row_domain in md.smtps_rcp:
        data_filter_list = space_filter_list.select([row_domain['organisation_id']], index=1)

        for row_address in row_domain['to_addresses']:
            to_domain = row_address['to_address'][:row_address['to_address'].find("@") + 1]

            # individual ###
            key = False
            for row_filter_list in data_filter_list:
                if row_filter_list[2] == "{}:{}".format(md.smtpd_body_headers['from'], row_address['to_address']):
                    M_FILTER_LIST_ACTION(key, row_address, row_filter_list, j_config, result)
                    break
                elif row_filter_list[2] == "{}:{}".format("any", row_address['to_address']):
                    M_FILTER_LIST_ACTION(key, row_address, row_filter_list, j_config, result)
                    key = True
                    break
                elif row_filter_list[2] == "{}:{}".format(md.smtpd_body_headers['from'], "any"):
                    M_FILTER_LIST_ACTION(key, row_address, row_filter_list, j_config, result)
                    break
            if key:
                continue

            # domains / individual ###
            key = False
            for row_filter_list in data_filter_list:
                if row_filter_list[2] == "{}:{}".format(from_domain, row_address['to_address']):
                    M_FILTER_LIST_ACTION(key, row_address, row_filter_list, j_config, result)
                    break
                elif row_filter_list[2] == "{}:{}".format(md.smtpd_body_headers['from'], to_domain):
                    M_FILTER_LIST_ACTION(key, row_address, row_filter_list, j_config, result)
                    break
            if key:
                continue

            # domains ###
            key = False
            for row_filter_list in data_filter_list:
                if row_filter_list[2] == "{}:{}".format(from_domain, to_domain):
                    M_FILTER_LIST_ACTION(key, row_address, row_filter_list, j_config, result)
                    break
                elif row_filter_list[2] == "{}:{}".format("any", to_domain):
                    M_FILTER_LIST_ACTION(key, row_address, row_filter_list, j_config, result)
                    break
                elif row_filter_list[2] == "{}:{}".format(from_domain, "any"):
                    M_FILTER_LIST_ACTION(key, row_address, row_filter_list, j_config, result)
                    break
            if key:
                continue

            # from_ip ###
            key = False
            for row_filter_list in data_filter_list:
                if row_filter_list[2] == "{}:{}".format(md.smtpd_ip, to_domain):
                    M_FILTER_LIST_ACTION(key, row_address, row_filter_list, j_config, result)
                    break
                elif row_filter_list[2] == "{}:{}".format(md.smtpd_ip, row_address['to_address']):
                    M_FILTER_LIST_ACTION(key, row_address, row_filter_list, j_config, result)
                    break
                elif row_filter_list[2] == "{}:{}".format(md.smtpd_ip, "any"):
                    M_FILTER_LIST_ACTION(key, row_address, row_filter_list, j_config, result)
                    break
            if key:
                continue

    result['processing_time'] = md.count_time(start_time)
    md.smtpa_verdict['FILTER_LIST'] = result
