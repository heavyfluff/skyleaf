#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
This is an bayes module.

It seems that it has to have THIS docstring with a summary line, a blank line
and sume more text like here. Wow.
"""
from datetime import datetime
from loguru import logger
import string

from system.other import ADD_SCORE_FROM_CONFIG
from system.other import TARANTOOL_CONN


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
def BAYES(md, j_config: dict):
    start_time = datetime.now()
    result = {'status': False, 'score': 0}

    words = BAYES_FROMAT_STRING(md.smtpd_body_headers['text_plain'])
    space_bayes, tarantool_space_status = TARANTOOL_CONN("bayes")
    if tarantool_space_status is False:
        result['error'] = "Erorr connection tarntool."
        logger.error("Erorr connection tarntool.")

    tr_result = space_bayes.call('box.space.bayes:len', ())
    alfa = 1
    count_all_words = tr_result[0]      # 14
    count_spam_words = 0                # 9
    count_ham_words = 0                 # 7
    count_words_in_text = len(words)
    spam_chis = 1
    spam_znam = 1
    ham_chis = 1
    ham_znam = 1

    for row_word in words:
        tr_result = space_bayes.select(row_word)
        if tr_result > 0:
            spam_chis = (alfa + tr_result[0][1]) * spam_chis
            ham_chis = (alfa + tr_result[0][2]) * ham_chis

    result['processing_time'] = md.count_time(start_time)
    md.smtpa_verdict['BAYES'] = result
