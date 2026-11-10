# Лабораторная работа № 25. Управление зависимостями программного проекта

## Цель

Организовать управление зависимостями Cloud Application: проанализировать
виртуальное окружение, отделить прямые зависимости от транзитивных,
зафиксировать проверенные версии, проверить совместимость и
воспроизводимость установки в чистом окружении, подготовив проект
к контейнеризации.

## Среда выполнения

| Параметр | Значение |
| --- | --- |
| Python | 3.13.14 |
| pip (рабочее `.venv`) | 26.3 |
| pip (чистое `.venv-check`) | 26.1.2 |
| Режим БД | `DB_BACKEND=sqlite` (локально), PostgreSQL — целевой |

Версия Python входит в среду выполнения: один и тот же набор библиотек
может иметь разные требования к разным версиям интерпретатора.

## Прямые зависимости

| Пакет | Используется для | Версия | Requires |
| --- | --- | --- | --- |
| fastapi | REST API | 0.162.2 | annotated-doc, opentelemetry-api, pydantic, starlette, typing-extensions, typing-inspection |
| uvicorn | запуск ASGI-приложения | 0.54.0 | click, h11 (+ extra `standard`) |
| sqlalchemy | ORM и работа с БД | 2.1.8 | typing-extensions |
| alembic | миграции | 1.20.1 | Mako, SQLAlchemy, typing-extensions |
| psycopg2-binary | подключение PostgreSQL | 2.9.13 | — |
| pydantic-settings | конфигурация | 2.16.2 | pydantic, python-dotenv, typing-extensions, typing-inspection |
| python-multipart | загрузка файлов | 0.0.33 | — |
| pwdlib | хеширование паролей | 0.3.1 | — (extra `argon2` → argon2-cffi) |

`pip list --not-required` показывает пакеты, не являющиеся зависимостями
других установленных пакетов. В окружении это не только прямые
зависимости, но и инструменты проверки (`pytest`, `httpx`), поэтому
результат команды сверяется с фактическим кодом проекта.

## Файлы фиксации

| Файл | Назначение | Записей |
| --- | --- | --- |
| `requirements-direct.txt` | прямые зависимости проекта | 8 |
| `requirements.txt` | зафиксированное окружение (`pip freeze`) | 40 |

`requirements.txt` длиннее, потому что содержит транзитивные пакеты:
`starlette`, `pydantic`, `Mako`, `argon2-cffi` и другие. `pytest` и
`httpx` попали в снимок как инструменты локальной проверки.

Ключевые библиотеки присутствуют в `requirements.txt`:
`fastapi`, `SQLAlchemy`, `alembic`, `psycopg2-binary`, `pydantic`,
`pwdlib`, `python-multipart`, `uvicorn`.

## Доступные обновления

`python -m pip list --outdated`:

| Пакет | Установленная версия | Доступная версия | Обновлялся в ЛР |
| --- | --- | --- | --- |
| annotated-doc | 0.0.5 | 0.0.6 | нет |
| fastapi | 0.162.2 | 0.162.4 | нет |

Массовое обновление не выполнялось: новая версия не означает
необходимость немедленной установки. Обновление требует понимания
причины, проверки совместимости, повторного тестирования и
актуализации `requirements.txt`.

## Проверка совместимости

```bash
python -m pip check
# No broken requirements found.
```

## Воспроизводимость в чистом окружении

Рабочее `.venv` не удалялось. Создано отдельное проверочное окружение:

```bash
python -m venv .venv-check
.venv-check\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

`.venv-check/` добавлен в `.gitignore`.

| Шаг | Результат |
| --- | --- |
| `pip list` до установки | только `pip` |
| `pip show fastapi` до установки | `Package(s) not found: fastapi` |
| `pip install -r requirements.txt` | 40 пакетов установлено |
| `pip check` | `No broken requirements found.` |
| `pip freeze` и сравнение с `requirements.txt` | различий нет |

Снимки сохранены в `docs/`:

- `docs/packages_before.txt` — список пакетов рабочего окружения;
- `docs/pip_check_clean_env.txt` — результат `pip check` в `.venv-check`;
- `docs/requirements_check.txt` — `pip freeze` восстановленного окружения.

## Контрольный запуск

Проверки выполнялись интерпретатором `.venv-check`:

```bash
python -c "import fastapi; print('FastAPI OK')"
python -c "import sqlalchemy; print('SQLAlchemy OK')"
python -c "import alembic; print('Alembic OK')"
python -c "import pydantic_settings; print('Settings OK')"
python -c "import pwdlib; print('pwdlib OK')"
alembic current      # 0009 (head)
python run.py
```

Перед запуском локально созданы `.env` (из `.env.example`), секреты
(`scripts/init_secrets.py`) и схема БД (`scripts/init_db.py`,
`scripts/init_access.py`). Эти файлы не входят в виртуальное окружение
и в Git.

| Проверка | Результат |
| --- | --- |
| `GET /status` | `200`, `{"status": "ok", ...}` |
| `GET /docs` | `200`, Swagger UI загружается |
| `POST /auth/register` | `201` |
| `POST /auth/login` | `200`, выдан Bearer-токен |
| `GET /auth/me` | `200`, `{"id": 1, "username": "student1", "role": "viewer"}` |
| `GET /services` (viewer) | `200`, список сервисов |
| `GET /services` без токена | `401` |

То есть новое окружение содержит библиотеки для FastAPI, SQLAlchemy,
аутентификации, авторизации и работы с БД. HTTPS в этой проверке
отключён (`HTTPS_ENABLED=false`), так как сертификаты — локальный
артефакт и в Git не входят; порядок включения описан в README ЛР №23.

## Самостоятельное задание: pwdlib

| Характеристика | Значение |
| --- | --- |
| Пакет | `pwdlib` |
| Установленная версия | 0.3.1 |
| Назначение | хеширование и проверка паролей (Argon2) |
| Requires | прямых нет; extra `[argon2]` устанавливает `argon2-cffi` → `argon2-cffi-bindings` → `cffi` → `pycparser` |
| Где используется | `app/security/passwords.py` (`PasswordHash.recommended()`, `hash_password`, `verify_password`), `app/services/auth.py` |
| Последствие отсутствия | `ImportError` при старте приложения; регистрация и вход недоступны, существующие хеши не проверяются |

`Requires` у `pwdlib` пуст, но проект подключает extra `[argon2]`
в `requirements-direct.txt`. Это показывает, что прямые зависимости
могут требовать не только сам пакет, но и его extras.

## Эксперимент с отсутствующей зависимостью

Выполнялся только в `.venv-check`:

```bash
python -m pip uninstall python-multipart
python -m pip check
# No broken requirements found.

python -c "import app.main"
# RuntimeError: Form data requires "python-multipart" to be installed.
```

`pip check` не обнаружил проблемы: пакет не заявлен как обязательная
зависимость FastAPI, он нужен коду приложения. При этом приложение
вообще не запускается — маршрут загрузки файлов объявляет
`multipart/form-data`. После эксперимента окружение восстановлено:

```bash
python -m pip install -r requirements.txt
python -m pip check        # No broken requirements found.
python -m pip show python-multipart
# Name: python-multipart
# Version: 0.0.33
```

Вывод: корректность зависимостей пакетов (`pip check`) и полнота
зависимостей конкретного приложения — разные проверки. Вторая требует
контрольного запуска приложения.

## Дополнительное задание: pip lock

Установленный pip 26.3 поддерживает экспериментальную команду `lock`:

```bash
python -m pip lock -r requirements-direct.txt -o pylock.toml
```

Файл содержит секции `[[packages]]` с именами, версиями, URL колёс и
хэшами SHA-256. Lock-файл разрешает зависимости заново и потому
отличается от проверенного окружения: в нём `fastapi 0.162.4` и
`annotated-doc 0.0.6` (в рабочем окружении — 0.162.2 и 0.0.5).
`pylock.toml` не заменяет `requirements.txt` и зависит от версии
Python и платформы.

## Структура

```
lab-25/
├── requirements-direct.txt   прямые зависимости
├── requirements.txt          зафиксированное окружение (40 пакетов)
├── pylock.toml               экспериментальный lock (доп. задание)
├── .venv-check/              проверочное окружение (вне Git)
├── docs/
│   ├── dependencies.md
│   ├── packages_before.txt
│   ├── pip_check_clean_env.txt
│   └── requirements_check.txt
└── ...                       приложение Cloud Application
```

## Вывод

Зависимости разделены на прямые и транзитивные, проверенные версии
зафиксированы в `requirements.txt`, совместимость подтверждена
`pip check`, а установка из файла в чистом окружении воспроизводит
рабочий набор без различий. Приложение запускается и выполняет
основные операции в восстановленном окружении. Проект готов
к контейнеризации: зависимости больше не привязаны к конкретной
машине разработчика.
