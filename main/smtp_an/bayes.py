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

    tr_result = space_bayes.call('box.space.bayes:len', ())
    count_all_words = tr_result[0]

    summ_factor = 0
    for row_word in words:
        tr_result = space_bayes.select(row_word)
        if tr_result > 0:
            summ_factor += (tr_result[0][1] / (tr_result[0][1] + tr_result[0][2])) - 0.5
    result_factor = round((summ_factor / count_all_words), 2)
    score_max = ADD_SCORE_FROM_CONFIG(j_config, "BAYES_MAX")
    score_min = ADD_SCORE_FROM_CONFIG(j_config, "BAYES_MIN")
    score_ava = (score_max + score_min) / 2
    result['score'] = score_ava * result_factor
    result['processing_time'] = md.count_time(start_time)
    md.smtpa_verdict['BAYES'] = result
