# Vmware
- Забираем из VMWare виртуальные машины и датасорсы
- Записываем в таблицы vcenter_datastore и vcenter_vm
- Получаем хосты из Zabbix
- Сопоставляем хост из vmware с хостом Zabbix по name, host, main ip

Расшифровка колонки `zabbix_method` в таблице `vcenter_vm`:

0 - найдено по видимому имени
1 - найдено по техническому имени
2 - найдено по главному ip

# Переменные для работы скрипта

Переменные можно внести в файл `.env`

- `POSTGRESQL_CONNINFO` - строка для подключения, пример: postgresql://my_user:my_password@hostname:5432/dbname
- `VMWARE_HOSTS` - список vmware-кластеров : VMWARE_HOSTS=sif-vcenter01.alkor.ru,sif-vcenter02.alkor.ru
- `VMWARE_USERNAME` - логин для авторизации в api vmWare
- `VMWARE_PASSWORD` - пароль для авторизации в api vmWare
- `ZABBIX_URL` - url Zabbix API
- `ZABBIX_USERNAME` - имя пользователя Zabbix
- `ZABBIX_PASSWORD` - пароль пользователя Zabbix

# Установка

1. Склонировать репозиторий:
```bash
git clone https://github.com/medbedica/vivt2.git && cd vivt2
```
2. Создать виртуальное окружение python
```bash
python3 -m venv venv
```
3. Устанавливаем python модули
```bash
venv/bin/pip3 install -r requirements.txt
```
4. Запускаем
```bash
export VMWARE_USERNAME=user
export VMWARE_PASSWORD=pswd
export POSTGRESQL_CONNINFO=postgresql://user:pswd@hostname:5432/cmdb
export VMWARE_HOSTS=sif-vcenter01.alkor.ru,sif-vcenter02.alkor.ru
export ZABBIX_URL=https://zabbix.example.com
export ZABBIX_USERNAME=admin
export ZABBIX_PASSWORD=adminpsw
venv/bin/python3 main.py 
```
