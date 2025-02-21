import logging
import os
from pyzabbix import ZabbixAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.sql import text, select, update

from cmdb_sync.logging_config import log_errors
from cmdb_sync.models import InfraVms2

logger = logging.getLogger(__name__)


@log_errors(logger)
def sync_zbx_datastore() -> bool:
    try:
        cmdb_url = os.environ["CMDB_DB_CONN"]
        zabbix_url = os.environ["ZABBIX_API_URL"]
        zabbix_token = os.environ["ZABBIX_API_TOKEN"]
    except KeyError as key:
        logger.error("Не задана переменная окружения: %s", key)
        return True

    zapi = ZabbixAPI(zabbix_url)
    zapi.login(api_token=zabbix_token)

    engine = create_engine(cmdb_url,
                           connect_args={"prepare_threshold": None})

    with Session(engine) as s:
        datastores = s.execute(text("""
            select
            vvm.hostname,
            vvm.host,
            vd.datastore,
            vd."name",
            vd.vmcluster
            from public.vcenter_vm vvm
            left join public.vcenter_datastore vd on vd.datastore = vvm.datastore_id
            where vvm.power_state = 'poweredOn'
            and vvm.hostname notnull
        """)).fetchall()
        fields = ['hostname', 'host', 'datastore', 'name', 'vmcluster']
        datastores = [dict(zip(fields, r)) for r in datastores]
        [r.update({'hostname': r['hostname'].split('.')[0]}) for r in datastores]

    os_types={
        'Windows': 26,
        'Linux': 2,
    }

    all_hosts = zapi.host.get(
            groupids=[os_types['Windows'], os_types['Linux']],
            selectTags='extend',
            output=['hostids', 'name', 'host']
    )

    for host in all_hosts:
        tags = host['tags']
        [t.pop('automatic') for t in tags if 'automatic' in t]
        datastore = None
        vmhost = None
        vmcluster = None

        try:
            datastore = [r['name'] for r in datastores if r['hostname'].split('.')[0].lower().strip() == host['name'].lower()][0]
        except IndexError:
            pass
        try:
            vmhost = [r['host'] for r in datastores if r['hostname'].lower().split('.')[0].strip() == host['name'].lower()][0]
        except IndexError:
            pass
        try:
            vmcluster = [r['vmcluster'] for r in datastores if r['hostname'].split('.')[0].lower().strip() == host['name'].lower()][0]
        except IndexError:
            pass

        update_tags = False
        if datastore:
            if 'vmdatastore' not in [t['tag'] for t in tags]:
                tags.append({'tag': 'vmdatastore', 'value': datastore})
                update_tags = True
            if len([t for t in tags if t['tag'] == 'vmdatastore']) > 1:
                [tags.remove(t) for t in tags if t['tag'] == 'vmdatastore' and t['value'] != datastore]
                update_tags = True
            elif datastore != [t['value'] for t in tags if t['tag'] == 'vmdatastore'][0]:
                [tags.remove(t) for t in tags if t['tag'] == 'vmdatastore' and t['value'] != datastore]
                tags.append({'tag': 'vmdatastore', 'value': datastore})
                update_tags =  True

        if vmhost:
            if 'vmhost' not in [t['tag'] for t in tags]:
                tags.append({'tag': 'vmhost', 'value': vmhost})
                update_tags = True
            if len([t for t in tags if t['tag'] == 'vmhost']) > 1:
                [tags.remove(t) for t in tags if t['tag'] == 'vmhost' and t['value'] != vmhost]
                update_tags = True
            elif vmhost != [t['value'] for t in tags if t['tag'] == 'vmhost'][0]:
                [tags.remove(t) for t in tags if t['tag'] == 'vmhost' and t['value'] != vmhost]
                tags.append({'tag': 'vmhost', 'value': vmhost})
                update_tags =  True

        if vmcluster:
            if 'vmcluster' not in [t['tag'] for t in tags]:
                tags.append({'tag': 'vmcluster', 'value': vmcluster})
                update_tags = True
            if len([t for t in tags if t['tag'] == 'vmcluster']) > 1:
                [tags.remove(t) for t in tags if t['tag'] == 'vmcluster' and t['value'] != vmcluster]
                update_tags = True
            elif vmcluster != [t['value'] for t in tags if t['tag'] == 'vmcluster'][0]:
                update_tags =  True

        if update_tags:
            zapi.host.update(hostid=host['hostid'], tags=tags)

    return True
