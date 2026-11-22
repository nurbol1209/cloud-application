# Лабораторная работа № 36. Развертывание серверного приложения

**Дисциплина:** Управление работами и разработка программного обеспечения облачных систем  
**Результат обучения:** РО 3.2. Эксплуатировать облачные системы  
**Тема:** deployment Cloud Application в Linux без контейнеризации: отдельный пользователь, venv, внешняя конфигурация и секреты, systemd, smoke-test и rollback.

## Цель работы

Развернуть ранее разработанное приложение Cloud Application в Linux-среде без Docker: подготовить системного пользователя и каталоги, получить зафиксированную версию из Git, создать изолированное Python-окружение, вынести конфигурацию и секреты за пределы репозитория, оформить приложение как службу systemd, включить автозапуск, выполнить smoke-проверку и отработать безопасный rollback конфигурации.

## 1. Паспорт целевой среды

| Параметр | Принятое значение | Фактически |
|---|---|---|
| ОС | Ubuntu Server 24.04 LTS или совместимая | Ubuntu 24.04.5 LTS |
| Менеджер служб | systemd | systemd 255, PID 1 = `systemd` |
| Пользователь приложения | cloudapp | `uid=995(cloudapp)`, shell `/usr/sbin/nologin` |
| Каталог приложения | /opt/cloud-application/app | создан, владелец `cloudapp:cloudapp` |
| Python-окружение | /opt/cloud-application/venv | Python 3.12.3 |
| Конфигурация | /etc/cloud-application/cloud-application.env | `root:cloudapp`, `0640` |
| Секреты | /etc/cloud-application/secrets | `root:cloudapp`, каталог `0750`, файлы `0640` |
| systemd unit | cloud-application.service | создан, `enabled`, `active` |
| Адрес приложения | 127.0.0.1 | `127.0.0.1:8000` |
| Порт | 8000 | 8000 |
| Журнал | systemd journal | `journalctl -u cloud-application.service` |
| Способ проверки | GET /status | HTTP 200 |
| Внешний сетевой доступ | не настраивается | только loopback |

Учебная среда выполнена как привилегированный контейнер Ubuntu 24.04.5 LTS с настоящим systemd (Docker Desktop, Linux containers), поскольку отдельная VirtualBox VM отсутствовала. Все эксплуатационные механизмы — useradd, venv, EnvironmentFile, systemd unit, journal, ss, curl — работают без эмуляции.

### Схема deployment

```mermaid
flowchart LR
    G[Git commit 665e168] --> A[/opt/cloud-application/app]
    A --> V[/opt/cloud-application/venv]
    C[/etc/cloud-application/cloud-application.env] --> S[systemd]
    K[/etc/cloud-application/secrets] --> L[symlink app/secrets]
    L --> A
    V --> S
    S --> P[Cloud Application]
    P --> H[127.0.0.1:8000]
    H --> ST[/status]
```

## 2. Подготовка сервера и версии приложения

```text
$ cat /etc/os-release
PRETTY_NAME="Ubuntu 24.04.5 LTS"
...
$ ps -p 1 -o comm=
systemd
```

Установлены пакеты `git`, `python3`, `python3-venv`, `python3-pip`, `curl`, `iproute2`, `sudo`.

```text
$ python3 --version
Python 3.12.3
$ git --version
git version 2.43.0
$ which curl ss
/usr/bin/curl
/usr/bin/ss
```

### Пользователь и каталоги

```text
$ useradd --system --user-group --home-dir /opt/cloud-application \
    --shell /usr/sbin/nologin cloudapp
$ id cloudapp
uid=995(cloudapp) gid=995(cloudapp) groups=995(cloudapp)
$ getent passwd cloudapp
cloudapp:x:995:995::/opt/cloud-application:/usr/sbin/nologin
```

```text
$ ls -ld /opt/cloud-application /etc/cloud-application
drwxr-xr-x 2 cloudapp cloudapp 4096 ... /opt/cloud-application
drwxr-x--- 2 root     cloudapp 4096 ... /etc/cloud-application
```

Shell `nologin` запрещает интерактивный вход: учётная запись нужна только для выполнения процесса приложения.

### Получение версии из Git

Для воспроизводимости deployment-снимок приложения зафиксирован отдельным Git-коммитом и передан на сервер в виде bundle, после чего выполнен обычный `git clone`.

```text
$ git clone /tmp/cloud-application.bundle /opt/cloud-application/app
$ chown -R cloudapp:cloudapp /opt/cloud-application/app
$ sudo -u cloudapp git -C /opt/cloud-application/app status --short
(пусто — рабочее дерево чистое)
```

| Параметр | Значение |
|---|---|
| Полный commit hash | `665e168195fe9c7d0976f2dcd18920d8ee21cc7c` |
| Короткий hash | `665e168` |
| Сообщение коммита | `Cloud Application 0.7 deployment snapshot (LR36)` |
| Git status | чисто |

Структура содержит `app/`, `requirements.txt`, `run.py`, `alembic.ini`, `migrations/`, `Dockerfile`, `compose.yaml`.

## 3. Python-окружение, конфигурация и секреты

```text
$ sudo -u cloudapp python3 -m venv /opt/cloud-application/venv
$ /opt/cloud-application/venv/bin/python --version
Python 3.12.3
```

Установка зависимостей:

```text
Successfully installed ... fastapi-0.162.2 ... pydantic-2.14.3 ...
    pydantic-settings-2.16.2 ... SQLAlchemy-2.1.8 ... uvicorn-0.54.0 ...
$ sudo -u cloudapp /opt/cloud-application/venv/bin/python -m pip check
No broken requirements found.
$ ... python -c "import fastapi, uvicorn, sqlalchemy, httpx; print('IMPORTS_OK')"
IMPORTS_OK
```

### Эксплуатационный env-файл

`/etc/cloud-application/cloud-application.env` (секреты отсутствуют):

```ini
APP_NAME=CloudApplication
APP_VERSION=0.7
APP_ENV=production

APP_HOST=127.0.0.1
APP_PORT=8000
DEBUG=false

HTTPS_ENABLED=false

DB_BACKEND=sqlite
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=cloud_application
DB_USER=postgres

NOTIFICATION_SERVICE_URL=http://127.0.0.1:9000
NOTIFICATION_TIMEOUT_SECONDS=2.0
NOTIFICATION_MAX_ATTEMPTS=3
NOTIFICATION_RETRY_DELAY_SECONDS=0.5

LOG_LEVEL=INFO
```

`DB_BACKEND=sqlite` добавлен явно: в ЛР №36 PostgreSQL ещё не разворачивается, а smoke-проверка не должна зависеть от СУБД. Права:

```text
-rw-r----- 1 root cloudapp ... /etc/cloud-application/cloud-application.env
```

### Секреты

```text
$ ls -l /etc/cloud-application/secrets
-rw-r----- 1 root cloudapp ... auth_secret
-rw-r----- 1 root cloudapp ... lab_db_password
$ sudo -u cloudapp test -r .../auth_secret && echo AUTH_SECRET_READABLE
AUTH_SECRET_READABLE
$ sudo -u cloudapp test -r .../lab_db_password && echo DB_SECRET_READABLE
DB_SECRET_READABLE
```

Значения не выводились. Секреты созданы генератором `secrets.token_urlsafe`, находятся вне Git и вне `/opt`.

```text
$ ln -s /etc/cloud-application/secrets /opt/cloud-application/app/secrets
$ sudo -u cloudapp test -r /opt/cloud-application/app/secrets/auth_secret \
    && echo SECRET_VIA_SYMLINK_OK
SECRET_VIA_SYMLINK_OK
```

Символическая ссылка сохраняет работу существующего механизма `secrets_dir="secrets"` в pydantic-settings, не копируя секреты в проект.

## 4. systemd-служба Cloud Application

Unit: [`deploy/systemd/cloud-application.service`](deploy/systemd/cloud-application.service).

```ini
[Unit]
Description=Cloud Application FastAPI Service
After=network.target

[Service]
Type=simple
User=cloudapp
Group=cloudapp
WorkingDirectory=/opt/cloud-application/app
EnvironmentFile=/etc/cloud-application/cloud-application.env
ExecStart=/opt/cloud-application/venv/bin/python /opt/cloud-application/app/run.py
Restart=on-failure
RestartSec=3
TimeoutStopSec=15
UMask=0027
NoNewPrivileges=true
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```text
$ systemd-analyze verify /etc/systemd/system/cloud-application.service
(критических ошибок нет)
$ systemctl daemon-reload
$ systemctl enable --now cloud-application.service
Created symlink /etc/systemd/system/multi-user.target.wants/cloud-application.service -> ...
$ systemctl is-enabled cloud-application.service
enabled
$ systemctl is-active cloud-application.service
active
```

| Свойство | Значение |
|---|---|
| `ActiveState` | `active` |
| `SubState` | `running` |
| `MainPID` | `2419` |
| `ExecMainStatus` | `0` |
| `Restart` | `on-failure` |
| `UnitFileState` | `enabled` |

```text
$ ps -fp 2419
UID          PID    PPID  C STIME TTY          TIME CMD
cloudapp    2419       1 16 12:52 ?        00:00:00 /opt/cloud-application/venv/bin/python /opt/cloud-application/app/run.py
```

Процесс работает от `cloudapp`, а не от root. Журнал запуска:

```text
... "message": "Cloud Application configured", "event": "application_configured"
... INFO:     Started server process [2419]
... INFO:     Application startup complete.
... INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

## 5. Smoke-test

```text
$ ss -ltnp | grep ':8000'
LISTEN 0 2048 127.0.0.1:8000 0.0.0.0:* users:(("python",pid=2419,fd=6))

$ curl -i http://127.0.0.1:8000/status
HTTP/1.1 200 OK
...
{"status":"ok","service":"CloudApplication","environment":"production","debug":false,"api_prefix":"/api"}

$ curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/docs
200
$ curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/openapi.json
200
```

| Проверка | Ожидаемый результат | Фактически |
|---|---|---|
| `is-enabled` | enabled | enabled |
| `is-active` | active | active |
| MainPID | ненулевой | 2419 |
| пользователь процесса | cloudapp | cloudapp |
| порт | 127.0.0.1:8000 | 127.0.0.1:8000 |
| `/status` | успешный ответ | HTTP 200 |
| `/docs` | HTTP 200 | 200 |
| journal | нет критической ошибки | ошибок запуска нет |

Приложение слушает только `127.0.0.1`, поэтому недоступно извне. Публикация в сеть — тема ЛР №39–40.

## 6. Контролируемая ошибка конфигурации и rollback

```text
$ cp .../cloud-application.env .../cloud-application.env.bak
$ sed -i 's/^APP_PORT=8000$/APP_PORT=not-a-number/' .../cloud-application.env
$ grep '^APP_PORT=' .../cloud-application.env
APP_PORT=not-a-number
$ systemctl restart cloud-application.service
$ systemctl status cloud-application.service --no-pager
     Active: activating (auto-restart) (Result: exit-code) ...
    Process: 2444 ... (code=exited, status=1/FAILURE)
```

Причина по журналу:

```text
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
app_port
  Input should be a valid integer, unable to parse string as an integer
  [type=int_parsing, input_value='not-a-number', input_type=str]
... systemd[1]: cloud-application.service: Failed with result 'exit-code'.
```

`Restart=on-failure` начал цикл перезапусков. Служба остановлена, конфигурация восстановлена из резервной копии:

```text
$ systemctl stop cloud-application.service
$ cp .../cloud-application.env.bak .../cloud-application.env
$ grep '^APP_PORT=' .../cloud-application.env
APP_PORT=8000
$ systemctl start cloud-application.service
$ systemctl is-active cloud-application.service
active
$ curl -i http://127.0.0.1:8000/status
HTTP/1.1 200 OK
{"status":"ok", ...}
```

После подтверждения резервная копия удалена. Rollback выполнен без изменения исходного кода и завершён повторной smoke-проверкой.

### Схема проверки и rollback

```mermaid
flowchart TD
    A[готовая версия] --> B[systemctl start]
    B --> C[status / journal]
    C --> D[/status]
    D --> E[deployment OK]
    C --> F[ошибка конфигурации]
    F --> G[service failed]
    G --> H[journal]
    H --> I[backup config]
    I --> J[restore]
    J --> K[start]
    K --> L[smoke-test]
```

## 7. Самостоятельная проверка

```text
PID до restart: 2452
PID после restart: 2461
$ systemctl is-active cloud-application.service
active
$ curl -s http://127.0.0.1:8000/status
{"status":"ok","service":"CloudApplication","environment":"production","debug":false,"api_prefix":"/api"}
```

После `restart` создан новый процесс с новым PID; приложение осталось работоспособным.

### Итоговый паспорт работающей среды

| Характеристика | Фактическое значение |
|---|---|
| hostname | `e54f726edf6d` |
| ОС | Ubuntu 24.04.5 LTS |
| Python | 3.12.3 (venv) |
| commit hash | `665e168195fe9c7d0976f2dcd18920d8ee21cc7c` |
| пользователь процесса | cloudapp |
| systemd unit | cloud-application.service |
| ActiveState | active |
| Unit enabled | enabled |
| MainPID | 2461 |
| bind address | 127.0.0.1 |
| port | 8000 |
| /status | 200 |
| /docs | 200 |
| место конфигурации | /etc/cloud-application/cloud-application.env |
| место секретов | /etc/cloud-application/secrets → app/secrets |
| место журналов | systemd journal |

## 8. Ответы на контрольные вопросы

1. **Что называется развертыванием серверного приложения?** Перенос зафиксированной версии приложения в целевую серверную среду, настройка окружения, конфигурации, секретов и способа запуска, а также проверка работоспособности.
2. **Чем deployment отличается от разработки?** Разработка создаёт код; deployment делает конкретную версию работоспособной на сервере и управляемой.
3. **Что называется целевой средой?** Сервер (ОС, ресурсы, сеть, пользователи, каталоги), на котором будет работать приложение.
4. **Для чего составляется паспорт целевой среды?** Чтобы заранее зафиксировать параметры развертывания и обеспечить воспроизводимость.
5. **Почему необходимо фиксировать commit hash?** Он однозначно определяет, какая версия кода развернута.
6. **Почему на сервер должна попадать определённая версия проекта?** Случайная рабочая папка невоспроизводима и может содержать незакоммиченные изменения.
7. **Почему приложение не запускается от root?** Чтобы ошибка или компрометация приложения не давала полных прав на сервер.
8. **Для чего создан пользователь cloudapp?** Для изоляции процесса приложения и владения его файлами.
9. **Почему его shell установлен в nologin?** Учётная запись нужна только для запуска службы, интерактивный вход запрещён.
10. **Для чего используется каталог /opt/cloud-application?** Для кода приложения и его виртуального окружения.
11. **Почему конфигурация помещена в /etc/cloud-application?** Это стандартное место для конфигурации; она отделена от кода и не попадает в Git.
12. **Для чего используется Python virtual environment?** Для изоляции зависимостей приложения от системного Python.
13. **Почему не следует устанавливать зависимости глобально?** Это может конфликтовать с системными пакетами и другими приложениями.
14. **Что проверяет pip check?** Согласованность установленных зависимостей и отсутствие конфликтов версий.
15. **Чем runtime-зависимости отличаются от dev-зависимостей?** Runtime нужны для работы приложения, dev — для разработки, тестов и линтеров.
16. **Почему секреты не должны храниться в Git?** История Git сохраняет значения навсегда; утечка секрета требует ротации.
17. **Почему каталог секретов размещён отдельно от исходного кода?** Чтобы код можно было свободно копировать и публиковать, не раскрывая секреты.
18. **Для чего используется символическая ссылка secrets?** Чтобы существующий механизм `secrets_dir="secrets"` работал, а файлы физически лежали в защищённом `/etc`.
19. **Как проверяется доступность секретов без вывода значения?** `test -r` от имени cloudapp и печать только признака `..._READABLE`.
20. **Для чего используется EnvironmentFile?** Для передачи systemd-службе обычных переменных окружения из внешнего файла.
21. **Что делает WorkingDirectory в systemd unit?** Задаёт рабочий каталог процесса.
22. **Что запускает ExecStart?** Команду запуска приложения — venv Python и `run.py`.
23. **Почему unit выполняется от cloudapp?** Чтобы процесс не имел прав root.
24. **Для чего используется Restart=on-failure?** Для автоматического перезапуска после аварийного завершения.
25. **Что делает RestartSec?** Задаёт паузу перед перезапуском.
26. **Для чего используется NoNewPrivileges=true?** Запрещает процессу и его потомкам повышать привилегии.
27. **Что делает enable --now?** Включает автозапуск и сразу запускает службу.
28. **Чем enabled отличается от active?** `enabled` — автозапуск при загрузке; `active` — работа сейчас.
29. **Как получить MainPID?** `systemctl show <unit> -p MainPID --value`.
30. **Как проверить пользователя процесса?** `ps -o user= -p <PID>` или `ps -fp <PID>`.
31. **Для чего используется journalctl -u?** Для чтения журнала конкретной службы.
32. **Что называется smoke-test?** Быстрая проверка ключевой функциональности после развертывания.
33. **Почему /status подходит для базовой smoke-проверки?** Он не зависит от БД и внешних сервисов и подтверждает, что приложение запущено.
34. **Почему Swagger UI проверяется отдельно?** Он подтверждает доступность документации и корректную маршрутизацию.
35. **Как проверить слушаемый TCP-порт?** `ss -ltnp | grep ':8000'`.
36. **Почему приложение привязано к 127.0.0.1?** На этом этапе проверяется deployment, а не публикация в сеть.
37. **Почему в ЛР №36 не используется 0.0.0.0?** Публикация и сетевые ограничения — тема ЛР №39–40.
38. **Почему не все REST API должны работать без PostgreSQL?** Зависимые от БД маршруты требуют развернутой СУБД, которой в ЛР №36 ещё нет.
39. **Когда будет развернута полная многокомпонентная система?** В ЛР №38.
40. **Что называется rollback?** Возврат к ранее проверенному состоянию конфигурации или артефакта.
41. **Почему перед экспериментом создаётся резервная копия конфигурации?** Чтобы быстро и точно восстановить рабочее состояние.
42. **Как журнал помогает определить причину неуспешного deployment?** Он содержит traceback, имя параметра и характер ошибки валидации.
43. **Нужно ли выполнять daemon-reload после изменения только EnvironmentFile?** Нет, `daemon-reload` нужен при изменении unit-файла; переменные перечитываются при рестарте службы.
44. **Почему после rollback необходимо повторить smoke-test?** Только успешный HTTP-ответ подтверждает восстановление работоспособности.
45. **Чем ЛР №36 отличается от ЛР №37?** Здесь приложение запускается напрямую через systemd и venv, а в ЛР №37 — в Docker-контейнере.
46. **Чем ЛР №36 отличается от ЛР №39?** Здесь приложение доступно только на loopback; в ЛР №39 настраивается сетевой доступ.
47. **Почему развернутую среду следует сохранить для следующих лабораторных работ?** Она служит базой для сравнения systemd- и контейнерной моделей. В нашем стенде среда воспроизводится скриптом; после снятия доказательств контейнер удалён, а ЛР №37 разворачивает приложение в Docker-модели на host.

## 9. Вывод

Cloud Application развернут в Linux без контейнеризации. Создан отдельный системный пользователь `cloudapp`, код получен из зафиксированного Git-коммита `665e168`, зависимости установлены в изолированный venv (Python 3.12.3, `pip check` без конфликтов). Эксплуатационная конфигурация вынесена в `/etc/cloud-application`, секреты размещены отдельно, не попали в Git и подключены через symlink. Создан unit `cloud-application.service`: служба включена в автозапуск, работает от непривилегированного пользователя, слушает только `127.0.0.1:8000`; `/status`, `/docs` и `/openapi.json` возвращают 200. Контролируемая ошибка `APP_PORT=not-a-number` диагностирована по journal (Pydantic ValidationError), конфигурация восстановлена, работоспособность подтверждена повторным smoke-test. Перезапуск изменил PID `2452 → 2461`.

## Воспроизведение

```bash
# из корня репозитория, при запущенном Docker Desktop
bash labs/lab-36/scripts/lr36/run_lab36.sh
# сохранить стенд после выполнения:
KEEP=1 bash labs/lab-36/scripts/lr36/run_lab36.sh
```

Полный журнал: [`docs/lr36_evidence.txt`](docs/lr36_evidence.txt).
