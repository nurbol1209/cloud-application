# Лабораторная работа № 27. Запуск приложения в контейнере

## Цель

Запустить образ `cloud-application:0.1`, передать runtime-конфигурацию
и секреты, опубликовать порт, исследовать состояние, файловую систему
и жизненный цикл контейнера.

## Проверка Docker

```bash
docker version
# bash: docker: command not found
wsl.exe -l -v
# Подсистема Windows для Linux не установлена
```

Docker Engine в текущей среде отсутствует, поэтому контейнер не
создавался и команды `docker run`, `docker ps`, `docker exec`,
`docker logs` не выполнялись. Ниже приведены полные команды
лабораторной работы и ожидаемые результаты; фактические значения
фиксируются на машине с Docker Desktop без изменения команд.

## Схема запуска

```
Браузер / curl
     |
     | http://127.0.0.1:8080
     v
Windows host: порт 8080
     |
     | docker publish 127.0.0.1:8080 -> 8000
     v
Контейнер cloud-application-container
     |
     | Uvicorn 0.0.0.0:8000
     v
Cloud Application (/app)
     |
     +-- /app/secrets  (bind mount, read-only)
     +-- /app/app, /app/migrations, run.py  (из образа)
```

Внутри контейнера приложение слушает `0.0.0.0:8000`, наружу
опубликован только локальный порт `127.0.0.1:8080`.

## Образ и контейнер

- Образ `cloud-application:0.1` — неизменяемый шаблон из ЛР №26.
- Контейнер `cloud-application-container` — запущенный экземпляр.
- Из одного образа можно создать несколько контейнеров с разными
  именами, портами и переменными среды.

`EXPOSE 8000` в Dockerfile только документирует порт. Публикация
выполняется параметром `-p` при создании контейнера.

## Runtime-конфигурация

`.env` и `secrets/` не входят в образ. При запуске:

- обычные параметры передаются через `--env-file .env`;
- `APP_HOST`, `APP_PORT`, `HTTPS_ENABLED` переопределяются `-e`;
- каталог `secrets/` монтируется в `/app/secrets` только для чтения;
- образ не пересобирается.

`APP_HOST=0.0.0.0` обязателен: `127.0.0.1` внутри контейнера — это
loopback самого контейнера, и опубликованный порт не получит трафик.

`HTTPS_ENABLED=false` для этой работы: исследуется жизненный цикл
контейнера, а не TLS. Механизм HTTPS из ЛР №23 сохраняется и может
быть включён отдельной конфигурацией.

## Запуск

PowerShell:

```powershell
$projectPath = (Get-Location).Path

docker run -d `
  --name cloud-application-container `
  -p 127.0.0.1:8080:8000 `
  --env-file .env `
  -e APP_HOST=0.0.0.0 `
  -e APP_PORT=8000 `
  -e HTTPS_ENABLED=false `
  --mount "type=bind,source=$projectPath\secrets,target=/app/secrets,readonly" `
  cloud-application:0.1
```

Git Bash:

```bash
docker run -d \
  --name cloud-application-container \
  -p 127.0.0.1:8080:8000 \
  --env-file .env \
  -e APP_HOST=0.0.0.0 \
  -e APP_PORT=8000 \
  -e HTTPS_ENABLED=false \
  --mount "type=bind,source=$(pwd)/secrets,target=/app/secrets,readonly" \
  cloud-application:0.1
```

| Параметр | Назначение |
| --- | --- |
| `-d` | фоновый режим |
| `--name` | имя контейнера |
| `-p 127.0.0.1:8080:8000` | host `127.0.0.1:8080` → контейнер `8000` |
| `--env-file .env` | обычная конфигурация |
| `-e APP_HOST=0.0.0.0` | слушать все интерфейсы контейнера |
| `-e APP_PORT=8000` | порт Uvicorn внутри контейнера |
| `-e HTTPS_ENABLED=false` | HTTP для данной работы |
| `--mount ... readonly` | секреты только на чтение |

Каталог `secrets/` должен существовать локально и содержать
`lab_db_password` и `auth_secret` (создаются
`python scripts/init_secrets.py`). Их содержимое не выводится.

## Проверка работы

```bash
docker ps
# cloud-application-container  ...  Up ...  127.0.0.1:8080->8000/tcp

docker port cloud-application-container
# 8000/tcp -> 127.0.0.1:8080

curl http://127.0.0.1:8080/status
# {"status":"ok","service":"Cloud Application",...}

curl -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/docs
# 200
```

`/docs` открывается из контейнера: на хосте процесс `python run.py`
не запущен, приложение работает внутри Docker.

На этом этапе PostgreSQL не контейнеризирован, поэтому endpoints,
которые обращаются к БД, могут завершаться ошибкой. Это ожидаемо;
исправляется в ЛР №28, а не созданием БД внутри ЛР №27.

## Журналы

```bash
docker logs cloud-application-container
docker logs --tail 20 cloud-application-container
docker logs -f cloud-application-container
```

В журнале видны запуск Uvicorn и строки HTTP-запросов. `Ctrl+C`
завершает только просмотр, контейнер продолжает работать.

## Диагностика внутри контейнера

```bash
docker exec cloud-application-container whoami          # appuser
docker exec cloud-application-container pwd             # /app
docker exec cloud-application-container ls -la
docker exec cloud-application-container python --version
docker exec cloud-application-container sh -c 'echo $APP_HOST'      # 0.0.0.0
docker exec cloud-application-container sh -c 'echo $APP_PORT'      # 8000
docker exec cloud-application-container sh -c 'echo $HTTPS_ENABLED' # false

docker exec cloud-application-container \
  sh -c 'test -f /app/secrets/auth_secret && echo AUTH_SECRET_EXISTS'
docker exec cloud-application-container \
  sh -c 'test -f /app/secrets/lab_db_password && echo DB_SECRET_EXISTS'
```

Секреты проверяются только по факту наличия. Команды
`cat /app/secrets/...` не выполняются.

Режим монтирования:

```bash
docker inspect cloud-application-container --format '{{json .Mounts}}'
```

В разделе `Mounts` для `/app/secrets` должны быть
`"RW": false` и `"ReadOnly": true`.

## Жизненный цикл

```
docker run
   |
   v
 running --docker stop--> exited --docker start--> running
   |                        |
   | docker restart         | docker rm
   +------------------------+--> удалён
                                  (образ сохраняется)
```

| Команда | Результат |
| --- | --- |
| `docker stop cloud-application-container` | процесс остановлен, `docker ps` пуст |
| `docker ps -a` | контейнер со статусом `Exited` |
| `curl http://127.0.0.1:8080/status` | соединение отклонено |
| `docker start cloud-application-container` | параметры сохраняются, приложение снова доступно |
| `docker restart cloud-application-container` | остановка и запуск, в журнале новый старт |
| `docker inspect ... --format '{{.State.Status}}'` | `running` или `exited` |
| `docker rm cloud-application-container` | контейнер удалён |
| `docker image ls cloud-application` | образ `cloud-application:0.1` на месте |

`docker start` не требует повторно указывать порт, переменные среды и
mounts: они сохранены в конфигурации контейнера. Удаление контейнера
не удаляет образ.

## Второй экземпляр

```bash
docker run -d \
  --name cloud-application-second \
  -p 127.0.0.1:8081:8000 \
  --env-file .env \
  -e APP_HOST=0.0.0.0 \
  -e APP_PORT=8000 \
  -e HTTPS_ENABLED=false \
  --mount "type=bind,source=$(pwd)/secrets,target=/app/secrets,readonly" \
  cloud-application:0.1
```

Оба контейнера слушают внутри `8000`, но публикуются на разных портах
хоста: `8080` и `8081`. Один и тот же host port нельзя занять дважды:
попытка `-p 127.0.0.1:8080:8000` для третьего контейнера завершится
ошибкой `port is already allocated`.

| Проверка | Основной контейнер | Второй контейнер |
| --- | --- | --- |
| Имя | `cloud-application-container` | `cloud-application-second` |
| Образ | `cloud-application:0.1` | `cloud-application:0.1` |
| Внутренний порт | `8000` | `8000` |
| Host port | `8080` | `8081` |
| `/status` доступен | ожидается `200` | ожидается `200` |
| `/docs` доступен | ожидается `200` | ожидается `200` |
| Пользователь `appuser` | ожидается | ожидается |
| Секреты подключены | ожидается | ожидается |
| Состояние `running` | ожидается | ожидается |

Фактическое выполнение не проводилось: Docker Engine отсутствует.

## Эксперимент без секретов

```bash
docker run -d \
  --name cloud-no-secrets \
  -p 127.0.0.1:8081:8000 \
  --env-file .env \
  -e APP_HOST=0.0.0.0 \
  -e APP_PORT=8000 \
  -e HTTPS_ENABLED=false \
  cloud-application:0.1

docker ps -a
docker logs cloud-no-secrets
```

Ожидается быстрый переход в `Exited`: после ЛР №24 `lab_db_password`
и `auth_secret` обязательны, слабых значений по умолчанию нет,
поэтому `Settings()` завершается ошибкой `Field required`. Это
правильное поведение. Контейнер удаляется:

```bash
docker rm cloud-no-secrets
```

Образ при этом не меняется: отличались только runtime-параметры.

## Итог проверки

| Проверка | Результат |
| --- | --- |
| Образ `cloud-application:0.1` существует | не проверено: нет Docker |
| Контейнер создан и запущен | не выполнено |
| Порт `127.0.0.1:8080:8000` опубликован | задан в команде |
| `APP_HOST=0.0.0.0` | задан в команде |
| Секреты подключены read-only | задано в команде |
| `/status`, `/docs` | ожидается `200`, не проверено |
| `docker logs`, `docker exec` | не выполнялось |
| `whoami` = `appuser`, `pwd` = `/app` | следует из Dockerfile |
| stop / start / restart / rm | не выполнялось |
| Образ сохраняется после `rm` | следует из модели Docker |
| Два контейнера на 8080 и 8081 | команды подготовлены |
| Отказ без секретов | ожидается `Field required` |

## Git

Лабораторная работа не изменяет исходный код приложения: исследуется
runtime Docker. В репозиторий добавляется только отчёт:

```bash
git add README.md
git commit -m "Document Cloud Application container runtime"
```

Секреты, `.env`, журналы и Container ID в Git не добавляются.

## Вывод

Подготовлены команды запуска Cloud Application в контейнере: образ
`cloud-application:0.1`, публикация `127.0.0.1:8080:8000`, runtime-конфигурация,
read-only монтирование секретов и управление жизненным циклом.
Архитектура «образ — контейнер — runtime-конфигурация» разделена:
изменение порта, среды или секретов не требует пересборки образа.
Фактический запуск требует Docker Desktop, отсутствующего в текущей
среде; ожидаемые результаты и проверки приведены полностью.
