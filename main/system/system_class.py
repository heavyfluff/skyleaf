import json
from multiprocessing import Process
from datetime import datetime

from system.using_database import ADD_IN_DATABASE_ROW_EMAIL


class MainData:
    def add_in_db(self) -> dict:
        p = Process(target=ADD_IN_DATABASE_ROW_EMAIL, args=(json.dumps(self.__dict__),))
        p.start()

    def count_time(self, start_time):
        end_time = datetime.now() - start_time
        return round(end_time.total_seconds(), 4)

    def __init__(self, **entries):
        if len(entries.keys()) != 0:
            self.__dict__.update(entries)
        else:
            self.cid = ""
            self.address_configuration = ""
            self.date_timestamp = 0
            self.date_string = ""
            self.smtpd_ip = ""
            self.smtpd_port = 0
            self.smtpd_gfl = []
            self.smtpd_starttls_status = False
            self.smtpd_starttls_cipher = ""
            self.smtpd_hostname = ""
            self.smtpd_extended_smtp = True
            self.smtpd_proxy_data = None

            self.smtpd_mail_from = ""
            self.smtpd_mail_options = []
            self.smtpd_smtp_utf8 = False
            self.smtpd_body_headers = {'from': "", 'Subject': ""}
            self.smtpd_body = {'files': [],
                               'urls': [],
                               'ips': [],
                               'emails': []}
            self.smtpd_dkim_verify = False

            self.smtpd_verdict = {}
            self.smtpa_verdict = {}
            self.smtpa_hits = 0

            self.content_id = 0
            self.next_action = "level_one"
            self.status = "created"

            self.smtps_rcp = []
            self.smtps_db_id = 0

            self.global_processing_time = 0
