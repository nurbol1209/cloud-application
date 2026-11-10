# Лабораторная работа № 7. Модульная организация программного проекта

## Цель

Разделить приложение на модули: маршруты, схемы данных, бизнес-логику и
хранилище.

## Структура

```
app/
├── config.py
├── main.py
├── data/
│   └── services.py        # временное хранилище
├── schemas/
│   └── services.py        # Pydantic-модели
├── services/
│   └── services.py        # бизнес-логика
└── routers/
    ├── services.py        # /services
    └── system.py          # /, /status, /about, /course, /service-count
```

`app/models.py` удалён: модель перенесена в `app/schemas/services.py`.

## Что реализовано

- `APIRouter(prefix="/services", tags=["Services"])`;
- подключаемые маршрутизаторы `services_router` и `system_router`;
- сервисный слой (`get_all_services`, `get_service_by_id`, `create_service`,
  `update_service`, `delete_service`, `count_services`);
- маршрут `GET /service-count` (самостоятельное задание).

## Запуск

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

## Проверка

```bash
curl http://127.0.0.1:8000/services
curl http://127.0.0.1:8000/service-count
```

## Вывод

Разделение ответственности упрощает развитие проекта: изменение хранилища или
бизнес-правил не требует правки маршрутов, а маршруты можно подключать и
тестировать независимо.
