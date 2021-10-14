#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
This is an bayes module.

It seems that it has to have THIS docstring with a summary line, a blank line
and sume more text like here. Wow.
"""
from datetime import datetime
from loguru import logger

from smtp_an.general_func import BAYES_FROMAT_STRING
from system.other import ADD_SCORE_FROM_CONFIG
from system.other import TARANTOOL_CONN


@logger.catch
def BAYES(md, j_config: dict):
    start_time = datetime.now()
    result = {'status': False, 'score': 0}

    words = BAYES_FROMAT_STRING(md.smtpd_body_headers['text_plain'])
    space_bayes, tarantool_space_status = TARANTOOL_CONN("bayes")
    if tarantool_space_status is False:
        result['error'] = "Erorr connection tarntool."
        logger.error("Erorr connection tarntool.")
    else:
        spam_reputation_list = []
        ham_reputation_list = []
        for row_word in words:
            tr_result = space_bayes.select(row_word)
            if tr_result.rowcount > 0:
                spam_reputation_list.append(tr_result[0][1] / (tr_result[0][1] + tr_result[0][2]))
                ham_reputation_list.append(tr_result[0][2] / (tr_result[0][1] + tr_result[0][2]))
            else:
                spam_reputation_list.append(0)
                ham_reputation_list.append(0)

        i = 0
        coef_spam = 0
        coef_ham = 0
        while i < len(words):
            coef_spam += spam_reputation_list[i]
            coef_ham += ham_reputation_list[i]
            i += 1

        result['spam'] = coef_spam / len(words)
        result['ham'] = coef_ham / len(words)
        if result['spam'] == result['ham']:
            result['score'] = 0
        elif result['spam'] > result['ham']:
            result['score'] = int(result['spam'] * ADD_SCORE_FROM_CONFIG(j_config, "BAYES_MAX"))
        elif result['spam'] < result['ham']:
            result['score'] = int(result['ham'] * ADD_SCORE_FROM_CONFIG(j_config, "BAYES_MIN"))

    result['processing_time'] = md.count_time(start_time)
    md.smtpa_verdict['BAYES'] = result
