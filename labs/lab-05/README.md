# Лабораторная работа № 5. Разработка REST API

## Цель

Реализовать REST API для ресурса `services`: получение списка и одного
ресурса, создание, изменение и удаление, а также обработку отсутствующего
ресурса.

## Что реализовано

- `app/models.py` — Pydantic-модель `ServiceCreate` (`name`, `type`, `status`);
- временное хранилище в памяти (`services`);
- маршруты:

| Метод | URL | Операция | Код |
| --- | --- | --- | --- |
| GET | `/services` | список сервисов | 200 |
| GET | `/services/{id}` | один сервис | 200 / 404 |
| POST | `/services` | создание | 201 / 422 |
| PUT | `/services/{id}` | изменение | 200 / 404 |
| DELETE | `/services/{id}` | удаление | 200 / 404 |

`new_id` вычисляется через `max(..., default=0) + 1`, поэтому создание
продолжает работать и после удаления всех сервисов (дополнительное задание).

## Запуск и проверка

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Запросы находятся в `requests.http` (VS Code REST Client) или выполняются через
Swagger UI <http://127.0.0.1:8000/docs>.

```bash
curl -i http://127.0.0.1:8000/services
curl -i http://127.0.0.1:8000/services/100
curl -i -X POST http://127.0.0.1:8000/services \
  -H "Content-Type: application/json" \
  -d '{"name":"Monitoring Service","type":"monitoring","status":"running"}'
```

## Самостоятельное задание

Создан сервис `Notification Service`:

```bash
curl -i -X POST http://127.0.0.1:8000/services \
  -H "Content-Type: application/json" \
  -d '{"name":"Notification Service","type":"notification","status":"running"}'
```

Далее выполнены: получение списка, получение по `id`, изменение состояния на
`maintenance` через `PUT`, проверка изменения, удаление и повторное получение
(ответ `404 Service not found`).

## Вывод

Данные хранятся только в памяти процесса: после перезапуска изменения теряются.
Это ограничение будет устранено при подключении PostgreSQL (ЛР № 15).
