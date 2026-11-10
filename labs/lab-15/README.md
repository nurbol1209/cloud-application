# Лабораторная работа № 15. Подключение серверного приложения к СУБД

## Цель

Заменить временное хранилище в памяти на PostgreSQL через SQLAlchemy ORM,
сохранив контракт REST API.

## Что изменено

- `app/data/database.py` — `engine`, `SessionLocal`, `Base`, зависимость
  `get_db()`;
- `app/data/models.py` — ORM-модели `ServiceType` и `Service` со связью
  `relationship`;
- `app/services/services.py` — функции работают с `Session`;
- `app/routers/services.py` — зависимость `db: Session = Depends(get_db)`;
- `app/data/services.py` удалён (данные больше не хранятся в памяти);
- `DATABASE_URL` добавлен в конфигурацию;
- `scripts/init_db.py` — локальная инициализация схемы и начальных данных.

`Base.metadata.create_all()` в приложении не вызывается: схема создаётся
SQL-скриптами ЛР № 14 (PostgreSQL) или вспомогательным скриптом (SQLite).

## Запуск

### PostgreSQL (как в задании)

```sql
CREATE DATABASE cloud_application;
```

```bash
psql -U postgres -d cloud_application -f docs/sql/01_initial_schema.sql
psql -U postgres -d cloud_application -f docs/sql/02_initial_data.sql
```

`.env`:

```dotenv
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/cloud_application
```

### SQLite (локальный режим без PostgreSQL)

```bash
python scripts/init_db.py
```

По умолчанию используется `sqlite:///./cloud_application.db`.

### Запуск приложения

```bash
pip install -r requirements.txt
python run.py
```

## Проверка

```bash
curl http://127.0.0.1:8000/services
curl http://127.0.0.1:8000/services/1
curl -i -X POST http://127.0.0.1:8000/services \
  -H "Content-Type: application/json" \
  -d '{"name":"Backup Service","type":"application","status":"running"}'
curl -i -X POST http://127.0.0.1:8000/services \
  -H "Content-Type: application/json" \
  -d '{"name":"Unknown","type":"unknown_type","status":"running"}'
```

Последний запрос возвращает `400 Service type not found`: тип проверяется в
сервисном слое до вставки в БД.

## Вывод

REST API не изменился, но данные теперь сохраняются в СУБД и переживают
перезапуск приложения. Проверка существования типа выполняется отдельным
запросом, поэтому клиент получает понятную ошибку `400`.
