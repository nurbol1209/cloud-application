# Cloud Application

Учебное серверное приложение на FastAPI, разрабатываемое в лабораторных
работах по дисциплине «Управление работами и разработка программного
обеспечения облачных систем».

## Возможности

- REST API для управления облачными сервисами;
- получение списка и отдельного сервиса;
- создание, изменение и удаление сервиса;
- служебные маршруты состояния приложения;
- автоматическая OpenAPI-документация.

## Запуск

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS:       source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

## Основные адреса

| Адрес | Назначение |
| --- | --- |
| <http://127.0.0.1:8000/> | сведения о приложении |
| <http://127.0.0.1:8000/status> | состояние приложения |
| <http://127.0.0.1:8000/services> | REST API сервисов |
| <http://127.0.0.1:8000/docs> | Swagger UI |
| <http://127.0.0.1:8000/redoc> | ReDoc |

## Структура проекта

```
app/
├── config.py
├── main.py
├── data/services.py
├── schemas/services.py
├── services/services.py
└── routers/
    ├── services.py
    └── system.py
```

`PROJECT_TASKS.md` содержит требования и план задач проекта.

## Git

Порядок работы с репозиторием описан в [docs/git.md](docs/git.md).
