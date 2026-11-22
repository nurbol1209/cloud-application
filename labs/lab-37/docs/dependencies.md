# Зависимости Cloud Application

## Среда выполнения

- Python: 3.13.14
- pip: 26.3 (рабочее окружение `.venv`)
- Проверочное окружение: `.venv-check`, Python 3.13.14, pip 26.1.2
- ОС: Windows (venv, PowerShell / Git Bash)

Один и тот же набор библиотек может предъявлять разные требования
к версии Python, поэтому версия интерпретатора фиксируется в отчёте
и учитывается при переносе проекта.

## Прямые зависимости

| Пакет | Назначение в проекте |
| --- | --- |
| FastAPI | REST API, маршрутизация, DI, OpenAPI/Swagger |
| Uvicorn | ASGI-сервер, запуск приложения, HTTPS |
| SQLAlchemy | ORM и доступ к БД |
| Alembic | миграции схемы БД |
| psycopg2-binary | драйвер PostgreSQL |
| pydantic-settings | конфигурация и секреты |
| python-multipart | приём `multipart/form-data`, загрузка файлов |
| pwdlib[argon2] | хеширование и проверка паролей (Argon2) |
| httpx | асинхронный HTTP-клиент для межсервисных запросов (ЛР №29) |

Список продублирован в `requirements-direct.txt` без версий: файл
отвечает на вопрос, какие библиотеки разработчик подключил осознанно.

## Транзитивные зависимости

Библиотеки, которые нужны прямым зависимостям и не импортируются
кодом проекта напрямую. Примеры из текущего окружения:

- `starlette`, `pydantic`, `pydantic_core`, `anyio`, `annotated-doc`,
  `typing_extensions`, `typing-inspection` — FastAPI;
- `click`, `h11`, `httptools`, `watchfiles`, `websockets`, `PyYAML` —
  Uvicorn (extra `standard`);
- `Mako`, `MarkupSafe` — Alembic;
- `argon2-cffi`, `argon2-cffi-bindings`, `cffi`, `pycparser` — pwdlib
  (extra `argon2`);
- `python-dotenv` — pydantic-settings.

Точный состав зависит от установленных версий и может меняться,
поэтому фиксируется файлом `requirements.txt`.

## Установка

```bash
python -m pip install -r requirements.txt
```

Для рабочего окружения разработчика прямой набор ставится так:

```bash
python -m pip install -r requirements-direct.txt
```

## Проверка

```bash
python -m pip check
python -m pip list
python -m pip show fastapi
```

## Обновление зависимостей

```bash
python -m pip list --outdated
```

`pip list --outdated` только показывает доступные версии. Массовое
обновление (`pip install --upgrade --upgrade-strategy eager ...`) для
всего окружения в проекте не выполняется.

## Правило изменения зависимостей

Новая внешняя библиотека добавляется только тогда, когда она
действительно необходима функциональности проекта. После изменения
набора пакетов необходимо:

1. проверить совместимость окружения (`python -m pip check`);
2. актуализировать `requirements.txt` (`python -m pip freeze`);
3. выполнить контрольный запуск приложения и проверить ключевые
   маршруты;
4. зафиксировать изменение в Git.

## Файлы фиксации окружения

| Файл | Назначение |
| --- | --- |
| `requirements-direct.txt` | прямые зависимости, выбранные разработчиком |
| `requirements.txt` | зафиксированное фактическое окружение (`pip freeze`) |
| `pylock.toml` | экспериментальный lock-файл `pip lock` (доп. задание) |

`pylock.toml` не заменяет `requirements.txt`: он разрешает зависимости
заново под конкретную версию Python и платформу и может содержать
более новые версии (`fastapi 0.162.4`, `annotated-doc 0.0.6`), чем
проверенное рабочее окружение.
