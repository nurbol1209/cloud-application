# Лабораторная работа № 17. Обеспечение целостности и проверка данных

## Цель

Обеспечить целостность данных на трёх уровнях: ограничения PostgreSQL,
бизнес-логика сервисного слоя и валидация Pydantic.

## Что изменено

- ORM: `ServiceType.name` — `NOT NULL` + `UNIQUE` +
  `CHECK (TRIM(name) <> '')`; `Service.name`, `type_id`, `status` — `NOT NULL`;
- `CHECK` для `status` (только `running`, `maintenance`, `stopped`);
- миграция `0004` — ограничения `NOT NULL`, `UNIQUE`, `CHECK`;
- миграция `0005` — `ck_service_types_name_not_empty` (дополнительное задание);
- `ServiceCreate` — `min_length`/`max_length`, нормализация пробелов,
  `Literal` для `status`;
- `ServiceEndpointUpdate` — учебная модель для `endpoint_url`
  (8…255 символов, удаление пробелов) — самостоятельное задание.

## Уровни проверки

| Уровень | Что проверяет | Пример |
| --- | --- | --- |
| Pydantic | структура и значения | `status = unknown` → 422 |
| Сервисный слой | бизнес-правила | неизвестный `type` → 400 |
| PostgreSQL | целостность при обходе API | `NOT NULL`, `UNIQUE`, `CHECK`, `FK` |

## Проверки API

```bash
curl -i -X POST http://127.0.0.1:8000/services \
  -H "Content-Type: application/json" \
  -d '{"name":"   Test Service   ","type":"   application   ","status":"running"}'
```

Значения сохраняются без пробелов: `Test Service`, `application`.

| Ошибочные данные | Где обнаружено | Результат |
| --- | --- | --- |
| `status = unknown` | Pydantic | 422 |
| пустое `name` | Pydantic | 422 |
| слишком длинное `name` | Pydantic | 422 |
| неизвестный `type` | сервисный слой | 400 |
| `status = unknown` через SQL | PostgreSQL CHECK | ошибка |
| `name = NULL` через SQL | PostgreSQL NOT NULL | ошибка |
| `type_id = 999` через SQL | PostgreSQL FK | ошибка |
| повторный тип `application` | PostgreSQL UNIQUE | ошибка |

## Миграции

```bash
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

Для локального SQLite:

```bash
python scripts/init_db.py
```

## Вывод

Ограничения БД защищают данные даже при обходе FastAPI, а Pydantic и
сервисный слой дают клиенту понятные ошибки до выполнения SQL.
