import psycopg
from pyzabbix import ZabbixAPI


def sync_zabbix(conn: psycopg.Connection, zapi: ZabbixAPI) -> None:
    print("Синхронизация Zabbix")

    with conn.cursor() as cur:
        vms = cur.execute(
            """\
        SELECT
            id,
            LOWER(name) name,
            host(ip) ip
        FROM
            vcenter_vm
        """
        ).fetchall()

    hosts = zapi.host.get(
        output=["hostid", "host", "name", "interfaces"], selectInterfaces=["ip", "main"]
    )

    update = []

    for vm in vms:
        matched_host = None
        method = None
        for host in hosts:
            if host["name"].lower() == vm["name"]:
                matched_host = host
                method = 0
                break
            if host["host"].lower() == vm["name"]:
                matched_host = host
                method = 1
                break

            for iface in host["interfaces"]:
                if iface["main"] == "1":
                    if iface["ip"] == vm["ip"]:
                        matched_host = host
                        method = 2
                        break
                    # Если уже нашли главный IP и он не подошёл, то нет смысла проверять остальные
                    else:
                        break
        if matched_host:
            hosts.remove(matched_host)
            update.append(
                {"id": vm["id"], "zabbix_hostid": int(matched_host["hostid"]), "zabbix_method": method}
            )

    with conn.cursor() as cur:
        cur.executemany(
            """\
        UPDATE
            vcenter_vm
        SET
            zabbix_hostid = %(zabbix_hostid)s,
            zabbix_method = %(zabbix_method)s
        WHERE
            id = %(id)s
        """,
            update,
        )
