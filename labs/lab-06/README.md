# Лабораторная работа № 6. Документирование программного API

## Цель

Оформить OpenAPI-документацию FastAPI: описание приложения, группы тегов,
summary и description маршрутов, описание параметров и схем данных.

## Что реализовано

- `FastAPI(title=..., version=..., description=..., openapi_tags=...)`;
- группы `System` и `Services` в Swagger UI;
- `summary` и `description` для каждого маршрута;
- `Path(..., description=..., gt=0)` для идентификатора сервиса;
- описания полей `ServiceCreate` через `Field(..., description=..., examples=...)`;
- описание ответов `404` и `422` через `responses`.

## Документация

После запуска доступны:

- Swagger UI — <http://127.0.0.1:8000/docs>;
- ReDoc — <http://127.0.0.1:8000/redoc>;
- OpenAPI JSON — <http://127.0.0.1:8000/openapi.json>.

В Swagger UI отображаются две группы: `System` и `Services`. Для каждого метода
показаны описание, параметры, примеры тела запроса и возможные ответы.

## Запуск

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```
