# Лабораторная работа № 29. Реализация взаимодействия программных сервисов

## Цель

Реализовать межсервисное взаимодействие по HTTP в сквозном проекте
Cloud Application: создать отдельный Notification Service, определить
API-контракт, вызвать сервис из основного приложения с помощью
`httpx.AsyncClient` и подключить новый компонент к Docker Compose.

## Проверка Docker

```bash
docker version
# bash: docker: command not found
```

Docker Engine в текущей среде отсутствует, поэтому `docker build`,
`docker compose up` и проверки `docker compose exec` не выполнялись.
Статическая проверка конфигурации:

```bash
python scripts/check_compose_config.py
# PASS: compose.yaml соответствует требованиям лабораторной работы
```

Результат сохранён в `docs/compose_checks.txt`: проверены сервисы
`app`, `db`, `migrate`, `notification`, образ `cloud-application:0.2`,
порядок запуска, адресация по имени `notification` и отсутствие
опубликованного порта `9000`.

Функциональность проверена локально: Notification Service запущен
Uvicorn на `127.0.0.1:9000`, основное приложение — на
`127.0.0.1:8000` в режиме `DB_BACKEND=sqlite`. Все результаты ниже
получены реальными HTTP-запросами между двумя процессами.

## Архитектура взаимодействия

```
Оператор / Swagger UI
        |
        | Authorization: Bearer <token>
        | POST /integration/notifications
        v
+----------------------+     HTTP POST /notifications      +-----------------------+
|  app                 |  http://notification:9000         |  notification         |
|  Cloud Application   | --------------------------------->|  Notification Service |
|  (FastAPI)           | <--------------------------------- |  (FastAPI)            |
|                      |  201 Created, JSON accepted       |  список в памяти      |
|  httpx.AsyncClient   |                                   |  GET /status          |
+----------+-----------+                                   +-----------------------+
           |
           | PostgreSQL (cloud-network)
           v
          db (postgres:18)
```

| Компонент | Роль |
| --- | --- |
| браузер / curl | клиент основного REST API |
| `app` | HTTP-сервер для пользователя и HTTP-клиент для `notification` |
| `notification` | самостоятельный программный сервис уведомлений |
| `db` | существующий инфраструктурный сервис хранения данных |

Пользователь не обращается к Notification Service напрямую: сервис
доступен только внутри сети `cloud-network`.

## API-контракт

Запрос:

```
POST /notifications
Content-Type: application/json

{
  "recipient": "operator@cloud.local",
  "message": "Cloud Application is running"
}
```

Успешный ответ:

```
201 Created

{
  "id": 1,
  "recipient": "operator@cloud.local",
  "message": "Cloud Application is running",
  "status": "accepted"
}
```

Контракт фиксирует адрес, метод, структуру запроса и ответа, код
успешного выполнения и допустимое значение `status`.

## Notification Service

Файл [app/notification_service/main.py](app/notification_service/main.py):

```python
app = FastAPI(title="Notification Service", version="1.0.0")


class NotificationCreate(BaseModel):
    recipient: str = Field(..., min_length=3, max_length=100)
    message: str = Field(..., min_length=1, max_length=500)


class NotificationResponse(BaseModel):
    id: int
    recipient: str
    message: str
    status: Literal["accepted"]


notifications: list[dict] = []
```

| Endpoint | Назначение |
| --- | --- |
| `GET /status` | диагностика: сервис запущен |
| `POST /notifications` | принять уведомление, код `201` |
| `GET /notifications` | список принятых уведомлений |
| `GET /notifications/{id}` | одно уведомление (доп. задание) |

Сервис не отправляет реальные письма: его задача — доказать сетевое
обращение, передачу JSON, выполнение удалённой операции и получение
результата. Список уведомлений хранится в памяти процесса и исчезает
после перезапуска.

## Конфигурация адреса

В [app/config.py](app/config.py) добавлено:

```python
notification_service_url: str = "http://127.0.0.1:9000"
```

В `.env.example`:

```
NOTIFICATION_SERVICE_URL=http://127.0.0.1:9000
```

URL не является секретом, но вынесен в конфигурацию: одна и та же
версия кода работает локально и в Compose. В Compose значение
переопределяется на `http://notification:9000`.

## HTTP-клиент

Файл [app/integrations/notification_client.py](app/integrations/notification_client.py):

```python
async def send_notification(recipient: str, message: str) -> dict:
    url = f"{settings.notification_service_url}/notifications"
    payload = {"recipient": recipient, "message": message}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        return response.json()


async def get_notification(notification_id: int) -> dict:
    url = (
        f"{settings.notification_service_url}"
        f"/notifications/{notification_id}"
    )

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

`await client.post(...)` не блокирует event loop: пока ожидается ответ
другого сервиса, приложение обслуживает другие запросы. Каталог
`app/integrations` отделяет детали HTTP-вызова от бизнес-логики
router.

## Схемы и маршрут интеграции

[app/schemas/integration.py](app/schemas/integration.py) содержит
`NotificationSendRequest` и `NotificationSendResponse` с теми же
ограничениями полей, что и контракт.

[app/routers/integration.py](app/routers/integration.py):

```python
router = APIRouter(prefix="/integration", tags=["Integration"])


@router.post(
    "/notifications",
    response_model=NotificationSendResponse,
    summary="Передать уведомление внутреннему сервису",
)
async def forward_notification(
    notification: NotificationSendRequest,
    current_user: User = Depends(
        require_permission("services.write")
    ),
):
    result = await send_notification(
        recipient=notification.recipient,
        message=notification.message,
    )
    return result
```

Новых ролей и разрешений не добавлялось: используется существующее
`services.write`. Поэтому `viewer` получает `403`, а `operator` и
`administrator` — успешный ответ.

Router подключён в [app/main.py](app/main.py) и появляется в Swagger
группой `Integration`.

## Зависимости

```bash
python -m pip install httpx
# httpx 0.28.1 уже присутствовал в окружении как инструмент проверок
python -m pip check
# No broken requirements found.
python -m pip freeze
# совпадает с requirements.txt
```

В `requirements-direct.txt` добавлена строка `httpx`: теперь это
осознанная прямая зависимость, а не только пакет для тестов.

## Изменения compose.yaml

| Что изменилось | Значение |
| --- | --- |
| образ `app` и `migrate` | `cloud-application:0.2` |
| новый сервис | `notification` на том же образе |
| команда `notification` | `uvicorn app.notification_service.main:app --host 0.0.0.0 --port 9000` |
| `app.environment` | `NOTIFICATION_SERVICE_URL: http://notification:9000` |
| `app.depends_on` | `migrate: service_completed_successfully`, `notification: service_started` |
| порт `9000` | не публикуется на хост |

Сервис `notification` подключён только к `cloud-network`. Docker
Compose разрешает имя `notification` во внутренний IP, поэтому
адрес не зависит от пересоздания контейнера. В `Dockerfile` метка
образа обновлена до `0.2`.

## Локальная проверка

Подготовка (локальный режим SQLite):

```bash
python scripts/init_secrets.py
python scripts/init_db.py
python scripts/init_access.py
python -m uvicorn app.notification_service.main:app --host 127.0.0.1 --port 9000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Диагностика сервиса:

```bash
curl http://127.0.0.1:9000/status
{"service":"notification","status":"running"}
```

Прямой POST в сервис:

```bash
curl -X POST http://127.0.0.1:9000/notifications \
  -H "Content-Type: application/json" \
  -d '{"recipient":"compose@cloud.local","message":"Direct service call"}'
# 201 Created
{"id":2,"recipient":"compose@cloud.local","message":"Direct service call","status":"accepted"}
```

Вызов через Cloud Application (роль `administrator`):

```bash
curl -X POST http://127.0.0.1:8000/integration/notifications \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"recipient":"operator@cloud.local","message":"Notification from Cloud Application"}'
# 200 OK
{"id":1,"recipient":"operator@cloud.local","message":"Notification from Cloud Application","status":"accepted"}
```

Проверка авторизации:

| Сценарий | Результат |
| --- | --- |
| `administrator` | `200 OK`, JSON `accepted` |
| `viewer` | `403 Forbidden`, `Insufficient permissions: services.write` |
| без токена | `401 Unauthorized`, `Authentication required` |

## Журналы

Фрагмент журнала `app`:

```
INFO: 127.0.0.1:64723 - "POST /integration/notifications HTTP/1.1" 200 OK
INFO: 127.0.0.1:64725 - "POST /integration/notifications HTTP/1.1" 200 OK
INFO: 127.0.0.1:64730 - "POST /integration/notifications HTTP/1.1" 200 OK
```

Фрагмент журнала `notification`:

```
INFO: 127.0.0.1:64724 - "POST /notifications HTTP/1.1" 201 Created
INFO: 127.0.0.1:64729 - "POST /notifications HTTP/1.1" 201 Created
INFO: 127.0.0.1:64731 - "POST /notifications HTTP/1.1" 201 Created
```

Пара записей с близким временем показывает прохождение одной операции
через два программных сервиса: пользовательский вызов принимает
`app`, исходящий вызов принимает `notification`.

## Проверки

| Проверка | Результат |
| --- | --- |
| `pip check` | `No broken requirements found.` |
| `pip freeze` совпадает с `requirements.txt` | да |
| Notification Service запускается | да, `127.0.0.1:9000` |
| `GET /status` | `200`, `{"status":"running"}` |
| Прямой `POST /notifications` | `201`, `status=accepted` |
| Вызов через `POST /integration/notifications` | `200`, JSON от сервиса |
| `viewer` на интеграционном маршруте | `403` |
| Запрос без токена | `401` |
| `notification` не публикует порт на хост | подтверждено в compose |
| `docker build -t cloud-application:0.2 .` | не выполнен: Docker отсутствует |
| `docker compose up -d` | не выполнен: Docker отсутствует |

## Самостоятельная работа

Три уведомления отправлены через `POST /integration/notifications`
(роль `administrator`):

| № | Основной endpoint | Внутренний endpoint | Код | `id` | `status` | Найдено в Notification Service |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `/integration/notifications` | `/notifications` | `200` | 3 | `accepted` | да |
| 2 | `/integration/notifications` | `/notifications` | `200` | 4 | `accepted` | да |
| 3 | `/integration/notifications` | `/notifications` | `200` | 5 | `accepted` | да |

Идентификаторы начинаются с 3, потому что до самостоятельной работы
в сервисе уже были созданы два уведомления (через приложение и
напрямую). Это подтверждает, что `id` зависит от числа предыдущих
запросов и не является фиксированным.

Проверка списка изнутри сети аналога `docker compose exec app`:

```bash
curl http://127.0.0.1:9000/notifications
# [{"id":1,...},{"id":2,...},{"id":3,...},{"id":4,...},{"id":5,...}]
```

Все три сообщения присутствуют в списке сервиса уведомлений.

## Исследование сервисного имени

В Docker-среде:

```bash
docker compose exec app \
  python -c "import socket; print(socket.gethostbyname('notification'))"
docker compose up -d --force-recreate notification
docker compose exec app \
  python -c "import socket; print(socket.gethostbyname('notification'))"
```

IP контейнера может измениться после пересоздания, но приложение
продолжает обращаться по имени `notification`. Внутренний DNS Docker
Compose связывает имя сервиса с актуальным адресом, поэтому
статический IP в конфигурации не нужен.

## Эксперимент с остановленным сервисом

```bash
# остановить Notification Service
# затем один запрос через основной API
POST /integration/notifications
```

Фактический результат:

```
HTTP 500 Internal Server Error
httpx.ConnectError: All connection attempts failed
```

После повторного запуска сервиса запрос снова выполняется успешно.
Обработка ошибок, `try/except`, `retry`, `timeout`, `fallback`
и Circuit Breaker намеренно не добавлялись: это исходная проблема
для лабораторной работы №30.

После перезапуска список уведомлений пуст — данные хранились только
в памяти процесса. Первое новое уведомление снова получило `id = 1`.

## Дополнительное задание: уведомление по идентификатору

В Notification Service добавлен `GET /notifications/{notification_id}`,
в клиент — `get_notification(notification_id)`.

```bash
curl http://127.0.0.1:9000/notifications/1
# 200 {"id":1,"recipient":"extra@cloud.local","message":"Optional task","status":"accepted"}

curl http://127.0.0.1:9000/notifications/99
# 404 {"detail":"Notification not found"}
```

Вызов из основного приложения через клиент:

```python
import asyncio
from app.integrations.notification_client import get_notification

print(asyncio.run(get_notification(1)))
# {'id': 1, 'recipient': 'extra@cloud.local',
#  'message': 'Optional task', 'status': 'accepted'}
```

## Примечание об окружении

В Git Bash текущей машины переменная `NO_PROXY` содержит шаблон
`[::1]`, который `httpx 0.28.1` разбирает как URL с некорректным
портом (`Invalid port: ':1]'`). Поэтому проверочные процессы
запускались с `env -u NO_PROXY`. В контейнерах Docker эта переменная
не задана, и код работает без изменений; никакой обходной логики
в приложение не добавлялось.

## Git

```bash
git switch -c feature/notification-service
git add app compose.yaml requirements-direct.txt requirements.txt \
  Dockerfile .env.example scripts docs requests.http README.md
git commit -m "Add notification service and HTTP integration"
```

## Вывод

Создан самостоятельный программный сервис уведомлений и реализован
межсервисный HTTP-вызов из Cloud Application. API-контракт, адрес
сервиса в конфигурации, асинхронный клиент и авторизация маршрута
обеспечивают слабую связанность компонентов. Compose-конфигурация
описывает новый сервис в общей сети без публикации порта на хост.
Отказ зависимого сервиса приводит к `500` и будет обработан
в лабораторной работе №30.
