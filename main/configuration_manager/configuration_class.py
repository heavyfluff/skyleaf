from pydantic import BaseModel
from typing import (List,
                    Dict)
import json


class ConfigSystem(BaseModel):
    description: str
    max_active_cheldren: int
    max_active_workers: int
    data_size_default: int


class ConfigNode(BaseModel):
    description: str
    type: str
    bind_address: str
    bind_port: int
    hostname: str


class ConfigGreylite(BaseModel):
    description: str
    count_treshold: int
    time_between_trys: int


class ConfigSenderModule(BaseModel):
    description: str
    header_mail_from: str


class ConfigTTL(BaseModel):
    description: str
    quarantined: int
    delivered: int
    rejected: int
    queue: int


class ConfigMethods(BaseModel):
    FILTER_LIST_BLACK: int = 0
    FILTER_LIST_WHITE: int = 0
    MISSING_SUBJECT: int = 0
    RISKY_COUNTRY: int = 0
    MISSING_TO: int = 0
    MISSING_DATE: int = 0
    MISSING_MID: int = 0
    MISSING_SUBJECT: int = 0
    SUBJ_ALL_CAPS: int = 0
    FAKE_REPLAY: int = 0
    FILE_EXTENTION_BLACK: int = 0
    EMOJII_IN_SUBJECT: int = 0
    FORGED_RECIPIENTS: int = 0
    RISKY_COUNTRY: int = 0
    FROM_NOT_MAIL_FROM: int = 0
    SPAMHAUS_SBL: int = 0
    SPAMHAUS_XBL: int = 0
    SPAMHAUS_PBL: int = 0
    SPAMHAUS_DBL: int = 0
    MX_SENDER_CHECK: int = 0
    R_SPF_FAIL: int = 0
    DNSBL_SORBS_NET: int = 0
    DNSBL_MAILSPIKE_NET: int = 0
    DNSBL_SURBL: int = 0
    STOP_WORDS: int = 0
    BAYES_MAX: int = 0
    BAYES_MIN: int = 0


class ConfigOrganisationTemplate(BaseModel):
    id: int
    name: str
    description: str


class ConfigThresholds(BaseModel):
    not_spam: int
    spam: int
    tag: str


class ConfigDomainTemplate(BaseModel):
    domain: str
    dst_port: int
    dst_ip: str
    date: int
    description: str
    thresholds: ConfigThresholds
    organisation_id: int
    from_ip_pool: Dict[str, list[str]]


class MainConfig(BaseModel):
    system: ConfigSystem
    node: ConfigNode
    version: int
    greylite: ConfigGreylite
    sender_module: ConfigSenderModule
    ttl: ConfigTTL
    methods: ConfigMethods
    organisations: Dict[str, ConfigOrganisationTemplate]
    domains: Dict[str, ConfigDomainTemplate]
