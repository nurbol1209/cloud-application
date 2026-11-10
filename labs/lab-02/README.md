# Лабораторная работа № 2. Создание первого серверного приложения

## Цель

Создать первое серверное приложение Cloud Application, вынести название и
версию в отдельный модуль конфигурации и добавить служебные маршруты.

## Что реализовано

- `app/config.py` с константами `APP_NAME` и `APP_VERSION`;
- `FastAPI(title=..., version=...)` — данные отображаются в Swagger UI;
- маршруты:
  - `GET /` — приложение, версия, статус;
  - `GET /status` — состояние и имя сервиса;
  - `GET /about` — тип, язык, фреймворк;
  - `GET /course` — дисциплина, номер ЛР, проект (самостоятельное задание).

## Запуск

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Swagger UI: <http://127.0.0.1:8000/docs>, ReDoc: <http://127.0.0.1:8000/redoc>.

```bash
curl http://127.0.0.1:8000/status
curl http://127.0.0.1:8000/about
curl http://127.0.0.1:8000/course
```
