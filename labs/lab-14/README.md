# Лабораторная работа № 14. Выполнение операций SQL

## Цель

Реализовать спроектированную схему средствами SQL и освоить основные операции
над данными.

## Файлы

| Файл | Назначение |
| --- | --- |
| `docs/sql/01_initial_schema.sql` | создание таблиц `service_types` и `services` |
| `docs/sql/02_initial_data.sql` | начальные типы и сервисы |
| `docs/sql/03_queries.sql` | SELECT, WHERE, ORDER BY, JOIN, INSERT, UPDATE, DELETE |

## Выполнение в PostgreSQL

```bash
psql -U postgres -d cloud_application -f docs/sql/01_initial_schema.sql
psql -U postgres -d cloud_application -f docs/sql/02_initial_data.sql
psql -U postgres -d cloud_application -f docs/sql/03_queries.sql
```

Либо те же команды выполняются в pgAdmin / DBeaver.

## Результат

После выполнения скриптов таблица `services` содержит:

| id | name | type_id | status |
| --- | --- | --- | --- |
| 1 | Web Service | 1 | running |
| 2 | Database Service | 2 | running |
| 3 | Monitoring Service | 3 | maintenance |

Попытка вставить сервис с `type_id = 999` завершается ошибкой внешнего ключа.

## Самостоятельное задание

В `03_queries.sql` приведён полный жизненный цикл сервиса `Backup Service`:
создание, выборка, изменение состояния, повторная выборка, удаление и проверка
отсутствия записи.

## Примечание

Скрипты рассчитаны на PostgreSQL (`SERIAL`). В ЛР № 15 приложение подключается
к этой базе через SQLAlchemy; для локального запуска без PostgreSQL в
последующих работах предусмотрен SQLite-режим.
