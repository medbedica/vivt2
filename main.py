#!/usr/bin/env python3
import os
import sys

import psycopg
import psycopg.rows
from dotenv import load_dotenv
from pyzabbix.api import ZabbixAPI

from cmdb_sync.vmware import sync_vmware
from cmdb_sync.zabbix import sync_zabbix


def main() -> int:
    load_dotenv()

    # Берём из переменной окружения строку для подключения, пример:
    # postgresql://my_user:my_password@hostname:5432/dbname
    conninfo = os.environ["POSTGRESQL_CONNINFO"]

    # Из переменной окружения VMWARE_HOSTS берём список vmware-хостов
    # Пример: VMWARE_HOSTS=sif-vcenter01.alkor.ru,sif-vcenter02.alkor.ru
    hosts = os.environ["VMWARE_HOSTS"].replace(" ", "").split(",")

    # Берём данные для авторизации
    username = os.environ["VMWARE_USERNAME"]
    password = os.environ["VMWARE_PASSWORD"]

    zabbix_url = os.environ["ZABBIX_URL"]
    zabbix_username = os.environ["ZABBIX_USERNAME"]
    zabbix_password = os.environ["ZABBIX_PASSWORD"]
    zapi = ZabbixAPI(zabbix_url)
    zapi.login(zabbix_username, zabbix_password)

    # В компании используется PGBouncer, поэтому ставим prepare_threshold=None
    # Ставим application_name для идентификации приложения на стороне postgresql
    with psycopg.connect(
        conninfo,
        application_name=os.path.basename(__file__),
        row_factory=psycopg.rows.dict_row,
        prepare_threshold=None,
    ) as conn, zapi:
        sync_vmware(conn, hosts, username, password)
        sync_zabbix(conn, zapi)

    return 0


if __name__ == "__main__":
    sys.exit(main())
