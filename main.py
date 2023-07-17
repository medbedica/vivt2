#!/usr/bin/env python3
import sys
import os

import psycopg

from cmdb_sync.vmware import sync


def main() -> int:
    # Берём из переменной окружения строку для подключения, пример:
    # postgresql://my_user:my_password@hostname:5432/dbname
    conninfo = os.environ["POSTGRESQL_CONNINFO"]

    # Из переменной окружения VMWARE_HOSTS берём список vmware-хостов
    # Пример: VMWARE_HOSTS=sif-vcenter01.alkor.ru,sif-vcenter02.alkor.ru
    hosts = os.environ["VMWARE_HOSTS"].replace(" ", "").split(",")

    # Берём данные для авторизации
    username = os.environ["VMWARE_USERNAME"]
    password = os.environ["VMWARE_PASSWORD"]

    # В компании используется PGBouncer, поэтому ставим prepare_threshold=None
    # Ставим application_name для идентификации приложения на стороне postgresql
    conn = psycopg.connect(
        conninfo, application_name=os.path.basename(__file__), prepare_threshold=None
    )

    sync(conn, hosts, username, password)

    conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
