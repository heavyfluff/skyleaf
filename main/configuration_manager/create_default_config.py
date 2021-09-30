#!/usr/bin/python
# -*- coding: UTF-8 -*
import json



# Скрипт создания дефолтного конфигурационного файла для запуска фильтрации #



config = {}

config['system'] = {}
config['system']['description'] = ""
config['system']['max_active_cheldren'] = 4
config['system']['max_active_workers'] = 4
config['system']['data_size_default'] = 33554432

config['node'] = {}
config['node']['description'] = ""
config['node']['type'] = "incomming"
config['node']['bind_address'] = "172.16.20.11"
config['node']['bind_port'] = 10025
config['node']['hostname'] = "SKYLEAF"



config['version'] = 1

config['greylite'] = {}
config['greylite']['description'] = "count_treshold - Число попыток проверки грейлистинга; time_between_trys - Время в секундах, после которого будет защитана попытка грейлистинга;"
config['greylite']['count_treshold'] = 3
config['greylite']['time_between_trys'] = 60

config['sender_module'] = {}
config['sender_module']['description'] = "header_mail_from - Добавление в заголовок MAIL FROM имени;"
config['sender_module']['header_mail_from'] = "skyleaf@bi.zone"

config['ttl'] = {}
config['ttl']['description'] = "Модуль очистки старых сообщений, значения указаны а часах;"
config['ttl']['quarantined'] = 24
config['ttl']['delivered'] = 1
config['ttl']['rejected'] = 1
config['ttl']['queue'] = 1

config['domains'] = {}

config['domains']['pavlov.ru'] = {}
config['domains']['pavlov.ru']['domain'] = "pavlov.ru"
config['domains']['pavlov.ru']['dst_port'] = 1025
config['domains']['pavlov.ru']['dst_ip'] = "172.16.20.14"
config['domains']['pavlov.ru']['date'] = 1
config['domains']['pavlov.ru']['description'] = "description"
config['domains']['pavlov.ru']['organisation_id'] = 3
config['domains']['pavlov.ru']['from_ip_pool'] = {'PSEG01':[]}

config['domains']['test.ru'] = {}
config['domains']['test.ru']['domain'] = "test.ru"
config['domains']['test.ru']['dst_port'] = 1026
config['domains']['test.ru']['dst_ip'] = "172.16.20.14"
config['domains']['test.ru']['date'] = 1
config['domains']['test.ru']['description'] = "description"
config['domains']['test.ru']['organisation_id'] = 2
config['domains']['test.ru']['from_ip_pool'] = {'PSEG01':[]}

config['organisations'] = {}

config['organisations']['first_organisation'] = {}
config['organisations']['first_organisation']['id'] = 2
config['organisations']['first_organisation']['name'] = "first_organisation"
config['organisations']['first_organisation']['description'] = "desc_first_organisation"

config['organisations']['second_organisation'] = {}
config['organisations']['second_organisation']['id'] = 3
config['organisations']['second_organisation']['name'] = "second_organisation"
config['organisations']['second_organisation']['description'] = "desc_second_organisation"

'''
with open("configuration.json", "w") as f:
    json.dump(config, f)
'''

with open('configuration.json', 'w') as f:
    f.write(json.dumps(config, indent=4))


