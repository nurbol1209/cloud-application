# Cloud Application — лабораторные работы 1–34

Учебный сквозной проект по дисциплине «Управление работами и
разработка программного обеспечения облачных систем».
Один и тот же сервис развивается от простого FastAPI-приложения до
контейнеризованной системы с PostgreSQL, аутентификацией, ролями,
журналированием, статическим контролем качества и профилированием.

Каждая папка `labs/lab-NN` — самостоятельный снимок проекта на момент
соответствующей лабораторной работы. Последняя версия — `labs/lab-34`.

## Требования

- Python 3.13+
- Docker (для лабораторных 26–34; конфигурация проверяется и без него)
- Visual Studio Code с расширениями Python и Ruff
- Git

## Быстрый старт в VS Code

1. Откройте папку `cloud-application` в VS Code
   (`File → Open Folder`).
2. Создайте виртуальное окружение в корне и установите зависимости:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r labs\lab-34\requirements.txt
   python -m pip install -r labs\lab-34\requirements-dev.txt
   ```

3. Выберите интерпретатор `.venv` (`Ctrl+Shift+P` →
   `Python: Select Interpreter`).
4. Подготовьте локальные секреты и SQLite-базу в нужной лабораторной:

   ```powershell
   cd labs\lab-34
   python scripts\init_secrets.py
   python scripts\init_db.py
   python scripts\init_access.py
   ```

5. Запустите приложение: `F5` → **Cloud Application (выбранная ЛР)**.
   Для межсервисного сценария дополнительно запустите
   **Notification Service (выбранная ЛР)**.
6. Откройте `http://127.0.0.1:8000/docs`.

Готовые задачи VS Code: `Ctrl+Shift+P` → `Tasks: Run Task` →
`Quality gate`, `Compile all`, `Prepare local DB`,
`Profile service report`.

## Проверка качества

```powershell
cd labs\lab-34
.\scripts\check_quality.ps1
```

Ожидается `QUALITY CHECK PASSED`. В Linux/macOS:

```bash
bash scripts/check_quality.sh
```

В лабораторной 34 дополнительно:

```powershell
python scripts\profile_service_report.py
python -m cProfile -o profile_before.prof scripts\profile_service_report.py
python scripts\benchmark_scaling.py
```

## Лабораторные работы

| № | Тема | Отчёт |
| --- | --- | --- |
| 1 | Подготовка среды разработки облачного приложения | [lab-01](labs/lab-01/README.md) |
| 2 | Создание первого серверного приложения | [lab-02](labs/lab-02/README.md) |
| 3 | Исследование сетевых параметров приложения | [lab-03](labs/lab-03/README.md) |
| 4 | Формирование HTTP-запросов | [lab-04](labs/lab-04/README.md) |
| 5 | Разработка REST API | [lab-05](labs/lab-05/README.md) |
| 6 | Документирование программного API | [lab-06](labs/lab-06/README.md) |
| 7 | Модульная организация программного проекта | [lab-07](labs/lab-07/README.md) |
| 8 | Постановка задач программного проекта | [lab-08](labs/lab-08/README.md) |
| 9 | Создание и ведение Git-репозитория | [lab-09](labs/lab-09/README.md) |
| 10 | Работа с ветвями Git | [lab-10](labs/lab-10/README.md) |
| 11 | Организация коллективной разработки | [lab-11](labs/lab-11/README.md) |
| 12 | Конфигурирование облачного приложения | [lab-12](labs/lab-12/README.md) |
| 13 | Проектирование базы данных | [lab-13](labs/lab-13/README.md) |
| 14 | Выполнение операций SQL | [lab-14](labs/lab-14/README.md) |
| 15 | Подключение серверного приложения к СУБД | [lab-15](labs/lab-15/README.md) |
| 16 | Работа с миграциями базы данных | [lab-16](labs/lab-16/README.md) |
| 17 | Обеспечение целостности и проверка данных | [lab-17](labs/lab-17/README.md) |
| 18 | Реализация хранения файлов и объектов | [lab-18](labs/lab-18/README.md) |
| 19 | Реализация регистрации и аутентификации | [lab-19](labs/lab-19/README.md) |
| 20 | Реализация ролевой модели доступа | [lab-20](labs/lab-20/README.md) |
| 21 | Реализация программной авторизации | [lab-21](labs/lab-21/README.md) |
| 22 | Безопасное хранение паролей | [lab-22](labs/lab-22/README.md) |
| 23 | Защищённое сетевое взаимодействие | [lab-23](labs/lab-23/README.md) |
| 24 | Управление секретами приложения | [lab-24](labs/lab-24/README.md) |
| 25 | Управление зависимостями программного проекта | [lab-25](labs/lab-25/README.md) |
| 26 | Создание контейнерного образа приложения | [lab-26](labs/lab-26/README.md) |
| 27 | Запуск приложения в контейнере | [lab-27](labs/lab-27/README.md) |
| 28 | Контейнеризация приложения и СУБД | [lab-28](labs/lab-28/README.md) |
| 29 | Реализация взаимодействия программных сервисов | [lab-29](labs/lab-29/README.md) |
| 30 | Обработка ошибок сетевого взаимодействия | [lab-30](labs/lab-30/README.md) |
| 31 | Реализация журналирования приложения | [lab-31](labs/lab-31/README.md) |
| 32 | Отладка программного компонента | [lab-32](labs/lab-32/README.md) |
| 33 | Статический анализ и стандартизация кода | [lab-33](labs/lab-33/README.md) |
| 34 | Анализ и оптимизация программного компонента | [lab-34](labs/lab-34/README.md) |

## Структура проекта (lab-34)

```text
app/
  main.py                     FastAPI-приложение
  config.py                   настройки через pydantic-settings
  data/                       SQLAlchemy-модели и подключение
  routers/                    HTTP-маршруты
  services/                   бизнес-логика, reporting.py
  security/                   пароли, авторизация
  integrations/               клиент Notification Service
  notification_service/       второй сервис
  middleware/                 request_id и журналирование
migrations/                   Alembic
scripts/                      инициализация, проверки, benchmark
docs/                         свидетельства выполнения
compose.yaml                  PostgreSQL + app + migrate + notification
Dockerfile                    образ cloud-application:0.7
pyproject.toml                конфигурация Ruff
```

## Публикация на GitHub

Репозиторий ещё не привязан к удалённому. Один раз выполните:

```bash
git remote add origin https://github.com/<USER>/<REPO>.git
git branch -M main
git push -u origin main
```

Дальше достаточно `git push`. В репозиторий не попадают `.env`,
`secrets/*` (кроме README), `certs/*.pem`, базы `*.db`, профили
`*.prof`, кэши и `.venv` — это задано в `.gitignore`.

## Безопасность

- Реальные секреты хранятся только в `secrets/` и не коммитятся.
- В отчётах и журналах нет паролей, хешей, токенов и строк подключения.
- Для локальных примеров используются только учебные пароли.
- При утечке секрета его необходимо сменить (`scripts/init_secrets.py`).
