#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
This is an bayes module.

It seems that it has to have THIS docstring with a summary line, a blank line
and sume more text like here. Wow.
"""

from loguru import logger
from system.other import TARANTOOL_CONN
import sys
import mailparser
from datetime import datetime

from smtp_an.general_func import BAYES_FROMAT_STRING


def startLearn() -> str:
    start_time = datetime.now()
    tmp_date = int(start_time.timestamp())
    result = ""
    if len(sys.argv) != 3:
        logger.error("Error. Input spam/ham [file name]")
        result = "Error. Input spam/ham [file name]"
        return result

    if sys.argv[1] != "spam" and sys.argv[1] != "ham":
        result = "Error. Input spam/ham [file name]"
        return result

    file_byte_data = b""
    try:
        f = open(sys.argv[2], "rb")
        file_byte_data
        f.close()
    except Exception:
        logger.error("Error. Can't open file {}".format(sys.argv[2]))
        result = "Error. Can't open file {}".format(sys.argv[2])
        return result

    mail = mailparser.mailparser.parse_from_bytes(file_byte_data)
    words = BAYES_FROMAT_STRING(mail.text_plain[0])

    space_bayes, tarantool_space_status = TARANTOOL_CONN("bayes")
    if tarantool_space_status is False:
        logger.error("Erorr connection tarntool.")
        result = "Erorr connection tarntool."
        return result

    for row_word in words:
        tr_result = space_bayes.select(row_word)
        if tr_result.rowcount > 0:
            if sys.argv[1] != "spam":
                tr_result = space_bayes.update(row_word, [('+', 1, 1), ('=', 3, tmp_date)])
            elif sys.argv[1] != "ham":
                tr_result = space_bayes.update(row_word, [('+', 2, 1), ('=', 3, tmp_date)])
        else:
            if sys.argv[1] != "spam":
                tr_result = space_bayes.insert((row_word, 1, 0, tmp_date, tmp_date))
            elif sys.argv[1] != "ham":
                tr_result = space_bayes.insert((row_word, 0, 1, tmp_date, tmp_date))
        logger.info(str(tr_result[0]))
    result = "Learn comlited."
    return result


if __name__ == "__main__":
    print(startLearn())
