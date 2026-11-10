# Лабораторная работа № 12. Конфигурирование облачного приложения

## Цель

Вынести параметры среды выполнения из кода в конфигурацию на основе
`pydantic-settings`, добавить запуск через `run.py` и файл `.env.example`.

## Что изменено

- `app/config.py` — класс `Settings` (`app_name`, `app_version`,
  `app_description`, `app_env`, `app_host`, `app_port`, `debug`,
  `api_prefix`);
- `app/main.py` и `app/routers/system.py` используют `settings`;
- `run.py` запускает Uvicorn с хостом, портом и режимом перезагрузки из
  настроек;
- добавлены `.env.example` и локальный `.env` (в Git не попадает);
- `/status` возвращает окружение, признак отладки и `api_prefix`
  (самостоятельное задание).

## Файл .env.example

```dotenv
APP_NAME=Cloud Application
APP_VERSION=1.0
APP_ENV=development
APP_HOST=127.0.0.1
APP_PORT=8000
DEBUG=true
API_PREFIX=/api
```

`API_PREFIX` только отображается в `/status`; маршруты не перестраиваются —
так требует задание.

## Запуск

```bash
copy .env.example .env      # Windows
# cp .env.example .env      # Linux/macOS
pip install -r requirements.txt
python run.py
```

Проверка:

```bash
curl http://127.0.0.1:8000/status
```

```json
{
  "status": "ok",
  "service": "Cloud Application",
  "environment": "development",
  "debug": true,
  "api_prefix": "/api"
}
```

## Вывод

Параметры среды отделены от кода: изменение `.env` меняет поведение
приложения без правки Python-файлов, а `.env.example` документирует состав
настроек.
