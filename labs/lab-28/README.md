# Лабораторная работа № 28. Контейнеризация приложения и СУБД

## Цель

Объединить Cloud Application и PostgreSQL в многокомпонентную систему
Docker Compose: настроить сеть, имя сервиса БД, секреты, volume,
healthcheck, автоматические миграции и проверить сохранение данных
между пересозданиями контейнеров.

## Проверка Docker

```bash
docker version
# bash: docker: command not found
wsl.exe -l -v
# Подсистема Windows для Linux не установлена
```

Docker Engine в текущей среде отсутствует, поэтому `docker compose up`
не выполнялся. Конфигурация проверена без Docker:

```bash
python scripts/check_compose_config.py
# PASS: compose.yaml соответствует требованиям лабораторной работы
```

Результат сохранён в `docs/compose_checks.txt`: проверены сервисы,
образ PostgreSQL, healthcheck, сеть, volume, secrets, порядок запуска,
отсутствие пароля в compose и наличие init SQL. Фактические результаты
`docker compose up`, `psql` и API-проверок фиксируются на машине
с Docker Desktop по приведённым ниже командам.

## Архитектура

```
Браузер / curl
     |
     | http://127.0.0.1:8080
     v
+------------------------- Compose project -------------------------+
|                                                                   |
|  app (cloud-application:0.1)                                      |
|    APP_HOST=0.0.0.0, DB_HOST=db                                   |
|         |                                                         |
|         | cloud-network                                           |
|         v                                                         |
|  db (postgres:18)  <--- postgres_data (named volume)              |
|    без публикации 5432 на хост                                    |
|                                                                   |
|  migrate (cloud-application:0.1)                                  |
|    alembic upgrade head + initialize_access_model()               |
|    один раз, до запуска app                                       |
+-------------------------------------------------------------------+
```

| Сервис | Роль | Образ |
| --- | --- | --- |
| `app` | FastAPI/Uvicorn, публикует `127.0.0.1:8080:8000` | `cloud-application:0.1` |
| `db` | PostgreSQL, доступен только по `db:5432` | `postgres:18` |
| `migrate` | миграции и инициализация ролей, завершается | `cloud-application:0.1` |

`migrate` — не новый компонент, а другой режим запуска того же образа:
вместо Uvicorn выполняется `alembic upgrade head` и инициализация
модели доступа.

## Почему `DB_HOST=db`

Внутри контейнера `localhost` — это сам контейнер приложения.
PostgreSQL работает в другом контейнере, поэтому используется имя
Compose-сервиса `db`. Docker DNS разрешает его во внутренний IP.
IP может измениться при пересоздании контейнера, имя остаётся тем же,
поэтому статический адрес в конфигурацию не записывается.

## Базовая схема

История Alembic начинается с baseline-ревизии `0001`, которая только
фиксирует состояние БД ЛР №14 и ничего не создаёт. Поэтому пустому
PostgreSQL сначала нужна исходная схема:
`docker/postgres/01_base_schema.sql` создаёт `service_types`, `services`
и три стартовые записи. Файл монтируется в
`/docker-entrypoint-initdb.d` и выполняется только при инициализации
пустого каталога данных. Затем `migrate` применяет всю историю
(`0002`–`0009`) и создаёт роли и permissions.

## compose.yaml

```yaml
services:
  db:
    image: postgres:18
    environment:
      POSTGRES_DB: cloud_application
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD_FILE: /run/secrets/lab_db_password
    secrets:
      - lab_db_password
    volumes:
      - postgres_data:/var/lib/postgresql
      - ./docker/postgres:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test:
        [
          "CMD-SHELL",
          "pg_isready -U postgres -d cloud_application"
        ]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 10s
    networks:
      - cloud-network

  migrate:
    image: cloud-application:0.1
    env_file:
      - .env
    environment:
      DB_BACKEND: postgresql
      DB_HOST: db
      DB_PORT: 5432
      DB_NAME: cloud_application
      DB_USER: postgres
      HTTPS_ENABLED: "false"
    secrets:
      - source: lab_db_password
        target: /app/secrets/lab_db_password
      - source: auth_secret
        target: /app/secrets/auth_secret
    depends_on:
      db:
        condition: service_healthy
    command:
      - sh
      - -c
      - >
        alembic upgrade head &&
        python -c "from app.data.database import SessionLocal;
        from app.services.access import initialize_access_model, assign_default_roles;
        db = SessionLocal();
        initialize_access_model(db);
        assign_default_roles(db);
        db.close()"
    networks:
      - cloud-network

  app:
    image: cloud-application:0.1
    env_file:
      - .env
    environment:
      APP_HOST: 0.0.0.0
      APP_PORT: 8000
      HTTPS_ENABLED: "false"
      DB_BACKEND: postgresql
      DB_HOST: db
      DB_PORT: 5432
      DB_NAME: cloud_application
      DB_USER: postgres
    ports:
      - "127.0.0.1:8080:8000"
    secrets:
      - source: lab_db_password
        target: /app/secrets/lab_db_password
      - source: auth_secret
        target: /app/secrets/auth_secret
    depends_on:
      migrate:
        condition: service_completed_successfully
    networks:
      - cloud-network

volumes:
  postgres_data:

networks:
  cloud-network:
    driver: bridge

secrets:
  lab_db_password:
    file: ./secrets/lab_db_password
  auth_secret:
    file: ./secrets/auth_secret
```

`DB_BACKEND=postgresql` добавлен к заданию: в проекте сохранён
локальный SQLite-режим (`DB_BACKEND=sqlite` в `.env`), и без явного
переопределения приложение в контейнере продолжило бы использовать
SQLite вместо PostgreSQL. В среде без локального SQLite-режима это
поле можно не задавать.

## Запуск

```bash
cp .env.example .env          # если файла ещё нет
python scripts/init_secrets.py

docker compose config
docker compose up -d
docker compose ps
docker compose ps -a
```

Ожидаемая последовательность: создание сети и volume → запуск `db` →
выполнение `01_base_schema.sql` → `healthy` → `migrate` применяет
Alembic и роли → `app` запускается после успешного завершения
`migrate`.

## Проверки

```bash
docker compose exec db pg_isready -U postgres -d cloud_application
docker compose exec db psql -U postgres -d cloud_application -c "\dt"
docker compose exec db psql -U postgres -d cloud_application \
  -c "SELECT * FROM alembic_version;"
docker compose exec db psql -U postgres -d cloud_application \
  -c "SELECT id, name, status FROM services ORDER BY id;"
docker compose exec db psql -U postgres -d cloud_application \
  -c "SELECT name FROM roles ORDER BY id;"

docker compose exec app python -c \
  "import socket; print(socket.gethostbyname('db'))"
docker compose exec app python -c \
  "from app.config import settings; print(settings.db_host)"
```

`settings.database_url` не выводится: строка содержит пароль.
Ожидаемые таблицы: `service_types`, `services`, `stored_objects`,
`users`, `auth_sessions`, `roles`, `permissions`, `role_permissions`,
`alembic_version`; роли `viewer`, `operator`, `administrator`
(+ `content_manager` как дополнительная).

API:

```bash
curl http://127.0.0.1:8080/status
curl -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/docs
```

```bash
curl -X POST http://127.0.0.1:8080/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"compose_user","password":"CloudCompose123"}'

curl -X POST http://127.0.0.1:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"compose_user","password":"CloudCompose123"}'

curl http://127.0.0.1:8080/auth/me -H "Authorization: Bearer <token>"
curl http://127.0.0.1:8080/services -H "Authorization: Bearer <token>"
```

Пользователь сохраняется в PostgreSQL:

```bash
docker compose exec db psql -U postgres -d cloud_application \
  -c "SELECT id, username FROM users ORDER BY id;"
```

Изоляция БД: у `db` нет `ports`, поэтому с хоста `127.0.0.1:5432`
не открывается. SQL выполняется через `docker compose exec db psql`.

## Постоянное хранение

```bash
docker compose exec db psql -U postgres -d cloud_application \
  -c "INSERT INTO services (name, type_id, status)
      SELECT 'Compose Test Service', id, 'running'
      FROM service_types WHERE name = 'application';"

docker compose down
docker volume ls          # postgres_data сохраняется
docker compose up -d
```

После повторного запуска `Compose Test Service` и `compose_user`
должны сохраниться. `01_base_schema.sql` повторно не выполняется:
каталог данных не пуст.

| Команда | Контейнеры | Сеть | Volume `postgres_data` | Данные |
| --- | --- | --- | --- | --- |
| `docker compose down` | удаляются | удаляется | сохраняется | сохраняются |
| `docker compose down -v` | удаляются | удаляется | удаляется | уничтожаются |

`docker compose down -v` не выполняется до завершения проверок:
удаление volume уничтожает учебную БД.

## Самостоятельная проверка

| Проверка | Результат |
| --- | --- |
| `compose.yaml` проходит `docker compose config` | YAML проверен `scripts/check_compose_config.py`; запуск Docker недоступен |
| Сервис `db` запущен | не выполнено: нет Docker Engine |
| PostgreSQL `healthy` | настроено, не проверено |
| `migrate` завершился успешно | настроено, не проверено |
| Сервис `app` запущен | не выполнено |
| `/status` доступен | не проверено |
| `/docs` доступен | не проверено |
| `DB_HOST=db` | подтверждено статически |
| PostgreSQL не опубликован на host port | подтверждено статически |
| Приложение разрешает имя `db` | настроено через `cloud-network` |
| Таблицы Alembic созданы | настроено через `migrate` |
| Роли и permissions созданы | настроено через `initialize_access_model` |
| Регистрация пользователя работает | не проверено |
| Пользователь сохраняется в PostgreSQL | не проверено |
| `postgres_data` существует | объявлен в compose |
| Данные сохраняются после `down` | следует из named volume |
| Повторный `up` восстанавливает данные | следует из named volume |

## Дополнительное задание: файловое хранилище

```yaml
volumes:
  postgres_data:
  app_storage:

services:
  app:
    volumes:
      - app_storage:/app/storage/objects
```

Dockerfile ЛР №26 уже создаёт каталог и назначает владельца:

```dockerfile
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/storage/objects \
    && chown -R appuser:appuser /app/storage
```

Поэтому `appuser` может писать в volume. Пересборка `cloud-application:0.2`
не требуется, пока Dockerfile не меняется; при изменении Dockerfile
образ собирается заново:

```bash
docker build -t cloud-application:0.2 .
```

## Git

```bash
git add compose.yaml docker/postgres/01_base_schema.sql \
        scripts/check_compose_config.py docs
git commit -m "Containerize application with PostgreSQL"
```

`.env`, `secrets/`, `certs/*.pem` и данные volume в Git не попадают:
volume существует внутри Docker, а не в каталоге проекта.

## Вывод

Создана конфигурация многокомпонентной системы: `app`, `db` и
`migrate` в одной сети, PostgreSQL доступен по имени `db` и не
опубликован на хост, пароль передаётся через Docker secret, данные
хранятся в `postgres_data`, миграции и роли применяются до запуска
приложения, а запуск упорядочен через `healthcheck` и
`service_completed_successfully`. Фактический запуск требует Docker
Desktop; статическая проверка конфигурации пройдена.
