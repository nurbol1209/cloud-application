# Лабораторная работа № 26. Создание контейнерного образа приложения

## Цель

Подготовить контекст сборки и Dockerfile для Cloud Application,
исключить из образа локальные и конфиденциальные данные, установить
зафиксированные в ЛР №25 зависимости и собрать образ
`cloud-application:0.1`.

## Проверка Docker

```bash
docker version
# bash: docker: command not found

wsl.exe -l -v
# Подсистема Windows для Linux не установлена
```

Docker Engine на текущем компьютере отсутствует, WSL не установлен,
поэтому команды `docker build`, `docker image inspect` и
`docker image history` в этой среде не выполнялись. Сборка образа
требует Docker Desktop; результаты выполнения команд приведены ниже
как ожидаемые, без подмены фактических данных.

Вместо выполнения Docker подготовлен статический контроль артефактов:

```bash
python scripts/check_docker_assets.py
# PASS: Dockerfile и .dockerignore согласованы, секреты вне контекста
```

Результат сохранён в `docs/docker_checks.txt`: разобран Dockerfile,
проверен порядок слоёв, перечислен build context (47 файлов, 69 KiB)
и подтверждено исключение секретов, сертификатов, виртуальных
окружений и локальных данных. Скрипт не заменяет `docker build`, но
проверяет те же контракты, которые нарушаются чаще всего.

## Образ и контейнер

- **Образ** — неизменяемый шаблон: базовый Python, зависимости, код,
  миграции, рабочая директория, пользователь, метаданные, `CMD`.
- **Контейнер** — запущенный экземпляр образа.

В ЛР №26 создаётся только образ. Запуск контейнера — ЛР №27,
подключение к PostgreSQL — ЛР №28.

## Структура образа

```
python:3.13-slim
        |
        +-- /app
             +-- app/              исходный код
             +-- migrations/       миграции Alembic
             +-- alembic.ini
             +-- run.py
             +-- storage/objects   каталог runtime-файлов
             +-- системные пакеты Python из requirements.txt
        |
        +-- пользователь appuser (UID без root)
        +-- EXPOSE 8000
        +-- CMD ["python", "run.py"]
```

`storage/objects` создаётся при сборке и принадлежит `appuser`:
приложение загружает файлы, но не должно писать в `/app` от root.

## Build context

Точка в `docker build -t cloud-application:0.1 .` означает, что
текущий каталог передаётся Docker как контекст сборки. Всё, что не
исключено, может стать доступно инструкциям `COPY`/`ADD`, поэтому
конфиденциальные файлы исключаются заранее, а не «на всякий случай»
не копируются.

`.dockerignore`:

```
.venv/
.venv-check/
__pycache__/
*.py[cod]
*.pyd
.pytest_cache/
.git/
.gitignore
.dockerignore
.env
.env.example
secrets/
certs/*.pem
storage/
docs/
*.db
*.log
.vscode/
pylock.toml
requirements-direct.txt
requests.http
README.md
PROJECT_TASKS.md
Dockerfile
```

| Исключение | Причина |
| --- | --- |
| `.venv/` | окружение Windows-разработчика, в Linux оно непригодно |
| `.venv-check/` | временное проверочное окружение ЛР №25 |
| `__pycache__/`, `*.py[cod]` | служебные файлы Python |
| `.git/`, `.gitignore` | история репозитория не нужна runtime |
| `.env`, `.env.example` | локальная конфигурация, возможные секреты |
| `secrets/` | конфиденциальные значения |
| `certs/*.pem` | TLS-сертификат и закрытый ключ |
| `storage/` | пользовательские runtime-файлы |
| `docs/` | учебная документация не нужна образу |
| `*.db`, `*.log` | локальная БД и журналы |
| `pylock.toml`, `requirements-direct.txt` | не используются при сборке |
| `requests.http`, `README.md`, `PROJECT_TASKS.md` | не runtime-компоненты |

Исключение на этапе контекста важнее осторожности `COPY`: образ может
быть сохранён, передан и опубликован, и секрет переедет вместе с ним.

## Dockerfile

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Зависимости копируются и устанавливаются отдельным слоем:
# изменения исходного кода не инвалидируют этот слой.
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/storage/objects \
    && chown -R appuser:appuser /app/storage

COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser migrations ./migrations
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser run.py ./

USER appuser

EXPOSE 8000

LABEL org.opencontainers.image.title="Cloud Application" \
      org.opencontainers.image.version="0.1" \
      org.opencontainers.image.description="Cloud Application REST API on FastAPI"

CMD ["python", "run.py"]
```

Версия базового образа соответствует проверенной в ЛР №25:
Python 3.13.14 → `python:3.13-slim`.

| Инструкция | Назначение |
| --- | --- |
| `FROM` | базовый образ с Python 3.13 и минимальной Linux-средой |
| `ENV` | без `.pyc`, небуферизованный вывод, без кэша pip |
| `WORKDIR /app` | рабочая директория и база относительных путей |
| `COPY requirements.txt` | сначала только файл зависимостей |
| `RUN pip install` | отдельный слой, переиспользуемый при правках кода |
| `RUN useradd` | непривилегированный пользователь `appuser` |
| `COPY --chown` | код, миграции, `alembic.ini`, `run.py` от `appuser` |
| `USER appuser` | процесс не работает от root |
| `EXPOSE 8000` | объявленный порт (не публикует его) |
| `LABEL` | метаданные OCI |
| `CMD` | команда будущего контейнера, при сборке не выполняется |

## Сборка

```bash
docker build -t cloud-application:0.1 .
```

Ожидаемые этапы: загрузка базового образа → чтение `.dockerignore` →
передача контекста → `WORKDIR` → копирование `requirements.txt` →
`pip install` → создание `appuser` → копирование кода → итоговый образ.

Сборка не выполнена в текущей среде из-за отсутствия Docker Engine.
На машине с Docker Desktop команды отчёта выполняются без изменений:

```bash
docker image ls cloud-application
docker image inspect cloud-application:0.1
docker image inspect cloud-application:0.1 --format '{{.Config.User}}'
docker image inspect cloud-application:0.1 --format '{{json .Config.Cmd}}'
docker image inspect cloud-application:0.1 --format '{{json .Config.ExposedPorts}}'
docker image history cloud-application:0.1
```

Ожидаемые значения метаданных:

| Характеристика | Ожидаемое значение |
| --- | --- |
| Имя образа | `cloud-application` |
| Тег | `0.1` |
| Image ID | вычисляется при сборке, в отчёт вносится фактический |
| Базовый образ | `python:3.13-slim` |
| Рабочий каталог | `/app` |
| Пользователь | `appuser` |
| Exposed port | `8000/tcp` |
| CMD | `["python", "run.py"]` |
| Размер | определяется сборкой, фиксируется по `docker image ls` |

`EXPOSE` не публикует порт: публикация выполняется при запуске
контейнера (`-p 8000:8000`) в ЛР №27.

## Кэш сборки

Порядок `COPY requirements.txt` → `RUN pip install` → `COPY app`
выбран намеренно. Слой зависимостей зависит только от
`requirements.txt`, поэтому правка `app/main.py` не запускает
повторную установку библиотек. Повторная сборка без изменений должна
показать `CACHED` для неизменившихся шагов и выполняться быстрее
первой.

## Самостоятельное задание

| Проверка | Результат |
| --- | --- |
| Docker Engine доступен | нет: `docker: command not found`, WSL не установлен |
| `.dockerignore` создан | да |
| `.env` исключён | да, проверено скриптом |
| `secrets/` исключён | да |
| `certs/*.pem` исключены | да |
| `.venv/` исключена | да |
| `.venv-check/` исключена | да |
| Dockerfile создан | да |
| Использован проверенный `requirements.txt` | да |
| Образ успешно собран | не выполнено: нет Docker Engine |
| Имя образа `cloud-application` | задано в команде сборки |
| Тег `0.1` | задан в команде сборки |
| Пользователь `appuser` | присутствует в Dockerfile |
| CMD задан | `["python", "run.py"]` |
| EXPOSE содержит порт | `8000` |
| `docker image history` выполнен | не выполнено: нет Docker Engine |
| Повторная сборка использует кэш | не проверено на практике; порядок слоёв это обеспечивает |

### Исследование размера

- Наиболее крупные слои — базовый `python:3.13-slim` и слой
  `pip install`; исходный код проекта занимает десятки килобайт.
- Установка зависимостей напрямую влияет на размер: колёса
  `pydantic_core`, `psycopg2-binary`, `argon2-cffi-bindings` содержат
  бинарные расширения.
- `--no-cache-dir` не сохраняет скачанные архивы pip внутри слоя,
  уменьшая образ.
- Локальная `.venv` не копируется: она собрана под Windows и несовместима
  с Linux; зависимости ставятся заново из `requirements.txt`.
- `slim` выбран потому, что полный образ содержит компиляторы и
  инструменты, ненужные для запуска приложения.

### Дополнительный тег

```bash
docker image tag cloud-application:0.1 cloud-application:lab26
docker image ls cloud-application
# cloud-application  0.1    <image-id>
# cloud-application  lab26  <image-id>   (одинаковый Image ID)
docker image rm cloud-application:lab26
```

### Проверка Dockerfile средствами Docker

```bash
docker build --check .
```

Команда относится к дополнительному заданию и выполняется только при
поддержке её установленной версией Docker.

## Конфигурация при запуске

Образ не содержит `.env` и `secrets/`. Настройки передаются при
запуске контейнера переменными окружения; `pydantic-settings` читает
их наравне с файлами:

```bash
docker run --rm -p 8000:8000 \
  -e DB_BACKEND=sqlite \
  -e LAB_DB_PASSWORD=cloud_application \
  -e AUTH_SECRET=<сгенерированное значение> \
  cloud-application:0.1
```

Реальные секреты не записываются в Dockerfile, `.dockerignore`,
README или Git. Для PostgreSQL в ЛР №28 параметры подключения
передаются аналогично.

## Файлы лабораторной работы

| Файл | Назначение |
| --- | --- |
| `Dockerfile` | рецепт сборки образа |
| `.dockerignore` | исключения build context |
| `scripts/check_docker_assets.py` | статическая проверка артефактов |
| `docs/docker_checks.txt` | результат проверки |

## Git

```bash
git add Dockerfile .dockerignore scripts/check_docker_assets.py docs
git commit -m "Add Cloud Application container image"
```

Сам образ в Git не добавляется: репозиторий хранит рецепт сборки,
а образ при необходимости собирается заново.

## Вывод

Dockerfile и `.dockerignore` подготовлены: образ строится на
`python:3.13-slim`, зависимости ставятся отдельным слоем из
проверенного `requirements.txt`, приложение работает от `appuser`,
порт `8000` объявлен, `CMD` записан в метаданные. Секреты, `.env`,
TLS-ключи, виртуальные окружения и локальные данные исключены из
контекста сборки. Фактическая сборка образа требует Docker Desktop,
которого нет в текущей среде; статическая проверка артефактов
пройдена, команды для сборки и исследования образа приведены.
