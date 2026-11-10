# Лабораторная работа № 16. Работа с миграциями базы данных

## Цель

Принять существующую схему PostgreSQL под управление Alembic, сформировать
миграции добавления полей `description` и `endpoint_url`, выполнить
`upgrade`/`downgrade` без потери данных.

## Что добавлено

- `alembic.ini`, каталог `migrations/`;
- `migrations/env.py` связан с `Base.metadata` и `settings.database_url`;
- baseline-миграция `0001` (структура создана SQL-скриптами ЛР № 14);
- `0002` — `services.description` (`VARCHAR(255)`, NULL);
- `0003` — `services.endpoint_url` (`VARCHAR(255)`, NULL);
- модель `Service` дополнена полями `description` и `endpoint_url`;
- `scripts/init_db.py` для локального SQLite: создаёт baseline-схему,
  выполняет `stamp 0001`, затем `upgrade head`.

## Команды (PostgreSQL)

```bash
alembic current
alembic history
alembic stamp 0001
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

## Локальный режим (SQLite)

```bash
python scripts/init_db.py
alembic current
alembic history
```

Скрипт создаёт исходную схему, фиксирует baseline и применяет миграции — так
же, как это делается в PostgreSQL после выполнения SQL-скриптов ЛР № 14.

## Результат

```
columns: id, name, type_id, status, description, endpoint_url
alembic current: 0003 (head)
```

После `downgrade -1` поле `endpoint_url` исчезает, после повторного
`upgrade head` — появляется снова; существующие строки сохраняются.

## Вывод

Миграция описывает и прямое, и обратное изменение. Baseline фиксирует уже
существующую схему, поэтому данные не пересоздаются.
