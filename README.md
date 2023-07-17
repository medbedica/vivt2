# Vmware
- Забираем из VMWare виртуальные машины и датасорсы
- Записываем в таблицы vcenter_datastore и vcenter_vm

# Переменные для работы скрипта
- `POSTGRESQL_CONNINFO` - строка для подключения, пример: postgresql://my_user:my_password@hostname:5432/dbname
- `VMWARE_HOSTS` - список vmware-кластеров : VMWARE_HOSTS=sif-vcenter01.alkor.ru,sif-vcenter02.alkor.ru
- `VMWARE_USERNAME` - логин для авторизации в api vmWare
- `VMWARE_PASSWORD` - пароль для авторизации в api vmWare

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
venv/bin/python3 main.py 
```
