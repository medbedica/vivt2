import psycopg
from pyVim.connect import Disconnect, SmartConnect
from pyVmomi import vim


def sync_vmware(conn: psycopg.Connection, hosts: list, username: str, password: str):
    print("Синхронизация vmware")
    servers = []
    for h in hosts:
        servers.append(
            (
                SmartConnect(
                    host=h, user=username, pwd=password, disableSslCertValidation=True
                ),
                h,
            )
        )

    # Массивы с выходной информацией
    vms = list()
    datastores = list()

    for instance in servers:
        srv = instance[0]
        try:
            source = instance[1].split(".")[0]

            content = srv.content

            # Список датасторов
            container_datastore = content.viewManager.CreateContainerView(
                content.rootFolder, [vim.Datastore], True
            )
            # Список гипервизоров
            container_host = content.viewManager.CreateContainerView(
                content.rootFolder, [vim.HostSystem], True
            )

            # Проходимся по всем гипервизорам
            for host in container_host.view:
                # Проходимся по всем виртуальным машинам на данном хосте
                for vm in host.vm:
                    # Если поле config отсутствует -
                    # виртуальная машина в процессе создания / удаления,
                    # нам такая не нужна, так как не получится достать информацию
                    if vm.config is None:
                        continue
                    vms.append(
                        {
                            "memory_size_MB": vm.config.hardware.memoryMB,
                            "vm": vm._GetMoId(),
                            "name": vm.name,
                            "power_state": vm.runtime.powerState,
                            "cpu_count": vm.config.hardware.numCPU,
                            "ip": vm.guest.ipAddress,
                            "datastore": vm.datastore[0]._GetMoId(),
                            "source": source,
                            "hostname": vm.guest.hostName,
                            "host": host.name,
                        }
                    )

            for datastore in container_datastore.view:
                datastores.append(
                    {
                        "datastore": datastore._GetMoId(),
                        "name": datastore.info.name,
                        "type": datastore.summary.type,
                        "free_space": datastore.summary.freeSpace,
                        "capacity": datastore.summary.capacity,
                        "source": source,
                        "uncommitted": datastore.summary.uncommitted,
                    }
                )
        finally:
            Disconnect(srv)

    with conn.cursor() as cur:
        cur.execute(
            """\
            CREATE TABLE IF NOT EXISTS vcenter_datastore (
                datastore   TEXT,
                name        TEXT NOT NULL,
                type        TEXT NOT NULL,
                free_space  BIGINT NOT NULL,
                capacity    BIGINT NOT NULL,
                source      TEXT NOT NULL,
                uncommitted BIGINT,
                PRIMARY KEY (datastore, source)
            )
        """
        )
        # Очищаем таблицу
        cur.execute("TRUNCATE TABLE vcenter_datastore CASCADE")

        cur.execute(
            """\
            CREATE TABLE IF NOT EXISTS vcenter_vm (
                id              SERIAL
                memory_size_MB  INTEGER NOT NULL,
                vm              TEXT,
                name            TEXT NOT NULL,
                power_state     TEXT NOT NULL,
                cpu_count       INTEGER NOT NULL,
                ip              INET,
                datastore       TEXT,
                source          TEXT NOT NULL,
                hostname        TEXT,
                host            TEXT NOT NULL,
                zabbix_hostid   INTEGER,
                zabbix_method   INTEGER,
                PRIMARY KEY     (vm, source),
                FOREIGN KEY     (datastore, source) REFERENCES vcenter_datastore (datastore, source) ON DELETE CASCADE
            )
                """
        )
        cur.execute("TRUNCATE TABLE vcenter_vm CASCADE")

        cur.executemany(
            """\
            INSERT INTO vcenter_datastore (
                datastore, name, type, free_space,
                capacity, source, uncommitted
            ) VALUES (
                %(datastore)s, %(name)s, %(type)s, %(free_space)s,
                %(capacity)s, %(source)s, %(uncommitted)s
            )
                """,
            datastores,
        )

        cur.executemany(
            """\
            INSERT INTO vcenter_vm (
                memory_size_MB, vm, name, power_state,
                cpu_count, ip, datastore, source,
                hostname, host
            ) VALUES (
                %(memory_size_MB)s, %(vm)s, %(name)s, %(power_state)s,
                %(cpu_count)s, %(ip)s, %(datastore)s, %(source)s,
                %(hostname)s, %(host)s
            )
                """,
            vms,
        )
