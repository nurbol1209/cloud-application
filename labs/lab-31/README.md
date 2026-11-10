# Лабораторная работа № 31. Реализация журналирования приложения

## Цель

Реализовать централизованное структурированное журналирование Cloud
Application: уровни, JSON-формат, `request_id`, фиксацию HTTP-запросов,
аутентификации, авторизации, межсервисных вызовов и сетевых ошибок
без раскрытия паролей, токенов и секретов.

## Проверка Docker

```bash
docker version
# bash: docker: command not found
```

Docker Engine отсутствует, поэтому сборка `cloud-application:0.4` и
`docker compose logs` не выполнялись. Конфигурация проверена
статически (`PASS`, `docs/compose_checks.txt`), а журналирование
проверено на двух локальных процессах Uvicorn. Фрагменты реальных
записей сохранены в `docs/logging_examples.txt`.

## Контур журналирования

```
Cloud Application ── JSON ──► stdout ──► docker compose logs app
        │
        │ X-Request-ID
        v
Notification Service ── JSON ──► stdout ──► docker compose logs notification
```

Оба сервиса используют один `JsonFormatter` и один middleware.
Прикладные записи идут в стандартный поток контейнера; собственный
файл журнала внутри контейнера не создаётся.

| Уровень | Назначение | Пример |
| --- | --- | --- |
| `DEBUG` | подробная диагностика | `permission_granted`, `notification_request_attempt` |
| `INFO` | штатное событие | вход выполнен, запрос завершён, уведомление создано |
| `WARNING` | необычная ситуация, работа продолжается | неверный пароль, retry, отказ permission |
| `ERROR` | операция не выполнена | timeout, недоступность сервиса, ошибочный HTTP-ответ |
| `CRITICAL` | продолжение работы невозможно | критический системный отказ |

По умолчанию используется `INFO`; `DEBUG` включается параметром
`LOG_LEVEL`.

## Что нельзя журналировать

`password`, `password_hash`, `Authorization: Bearer ...`,
`access_token`, `AUTH_SECRET`, `LAB_DB_PASSWORD`, `database_url`,
закрытый TLS-ключ, а также тело запроса целиком. Middleware не
записывает заголовки, query string и body.

## Конфигурация

В [app/config.py](app/config.py):

```python
log_level: str = "INFO"
```

В `.env.example`:

```
LOG_LEVEL=INFO
```

## Контекст запроса

[app/request_context.py](app/request_context.py):

```python
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar(
    "request_id",
    default="-",
)


def get_request_id() -> str:
    return request_id_var.get()
```

`ContextVar` хранит идентификатор в контексте текущего HTTP-запроса,
поэтому значение доступно middleware, сервисам и HTTP-клиенту без
передачи параметра через все функции.

## Централизованная конфигурация logging

[app/logging_config.py](app/logging_config.py):

```python
EXTRA_FIELDS = (
    "service", "event", "method", "path", "status_code",
    "duration_ms", "user_id", "username", "permission",
    "target_service", "attempt", "error_type",
    "notification_id",
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
        }
        for field in EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str) -> None:
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"json": {"()": JsonFormatter}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {"level": level.upper(), "handlers": ["console"]},
    })
```

## HTTP middleware

[app/middleware/request_logging.py](app/middleware/request_logging.py)
берёт `X-Request-ID` из запроса или создаёт `uuid4().hex`, сохраняет
его в `ContextVar`, измеряет длительность и пишет
`http_request_completed`, а заголовок `X-Request-ID` возвращает
клиенту. При необработанном исключении пишется
`http_request_failed` с трассировкой. В `finally` контекст
сбрасывается.

```python
request_id = request.headers.get("X-Request-ID") or uuid4().hex
token = request_id_var.set(request_id)
started = time.perf_counter()
try:
    response = await call_next(request)
    ...
    response.headers["X-Request-ID"] = request_id
    return response
finally:
    request_id_var.reset(token)
```

Middleware подключён в [app/main.py](app/main.py) для
`cloud-application` и в
[app/notification_service/main.py](app/notification_service/main.py)
для `notification-service`.

## Notification Service и собственный Settings

Notification Service не получает секреты БД и аутентификации, поэтому
не может использовать полный `app.config.Settings` (там обязательны
`lab_db_password` и `auth_secret`). Для него создан минимальный
[app/notification_service/config.py](app/notification_service/config.py)
с единственным параметром `log_level`. Формат журнала, middleware и
`LOG_LEVEL` остаются общими для обоих сервисов.

## Передача request_id в Notification Service

В [app/integrations/notification_client.py](app/integrations/notification_client.py):

```python
headers = {"X-Request-ID": get_request_id()}
...
response = await client.post(url, json=payload, headers=headers)
```

Authorization основного пользователя в Notification Service не
передаётся: контракт этого не требует.

```
Входящий X-Request-ID
        |
        v
app middleware -> ContextVar -> notification_client
        |                            |
        |                            v
        |                     X-Request-ID
        |                            |
        v                            v
  app logs                  notification middleware
                                     |
                                     v
                              notification logs
```

Журнал клиента:

| Событие | Уровень | Поля |
| --- | --- | --- |
| `notification_request_started` | INFO | target_service |
| `notification_request_attempt` | DEBUG | attempt |
| `notification_request_completed` | INFO | status_code, duration_ms, attempt |
| `notification_request_retry` | WARNING | attempt, error_type |
| `notification_service_unavailable` | ERROR | attempt, error_type |
| `notification_service_timeout` | ERROR | error_type |
| `notification_service_bad_response` | ERROR | status_code, error_type |
| `request_id_mismatch` | WARNING | target_service (доп. задание) |

## Аутентификация и авторизация

[app/services/auth.py](app/services/auth.py): неудачный вход —
`authentication_failed` уровня WARNING с `username`; успешный —
`authentication_succeeded` уровня INFO с `user_id` и `username`.
Пароль, хеш и токен не записываются.

[app/security/authorization.py](app/security/authorization.py):
отказ — `permission_denied` уровня WARNING с `user_id`, `username`,
`permission`; успешная проверка — `permission_granted` уровня DEBUG.

Notification Service после создания записи пишет
`notification_created` уровня INFO с `notification_id` и
`status_code`; `recipient` и `message` не журналируются.

## Compose и образ

| Изменение | Значение |
| --- | --- |
| образ `app`, `migrate`, `notification` | `cloud-application:0.4` |
| `app.environment` | `LOG_LEVEL: INFO` |
| `notification.environment` | `LOG_LEVEL: INFO` |
| метка `Dockerfile` | `version="0.4"` |

```bash
docker build -t cloud-application:0.4 .
docker compose config
docker compose down
docker compose up -d
docker compose logs app | Select-String '"event"'
docker compose logs notification | Select-String '"event"'
```

## Проверка request_id

Собственный идентификатор:

```bash
curl.exe -i -H "X-Request-ID: lab31-demo-001" \
  http://127.0.0.1:8080/status
# x-request-id: lab31-demo-001
```

Автоматическая генерация: запрос без заголовка вернул
`x-request-id: 3d6d76fe26814ea1a7c1cdff85a6a008`, и эта запись есть
в журнале.

Один межсервисный запрос с `lab31-notify-001`:

```
app:
  notification_request_started
  notification_request_completed  status_code=201 duration_ms=998.55
  http_request_completed          path=/integration/notifications 201

notification:
  notification_created            notification_id=1 status_code=201
  http_request_completed          path=/notifications 201
```

Все записи содержат `request_id: lab31-notify-001`. Полные строки —
в `docs/logging_examples.txt`.

## Проверка уровней

| Событие | Ожидаемый уровень | request_id | Полезные поля | Конфиденциальных данных нет |
| --- | --- | --- | --- | --- |
| успешный HTTP-запрос | INFO | есть | method, path, status_code, duration_ms | да |
| неуспешный вход | WARNING | есть | username | да |
| отказ permission | WARNING | есть | user_id, username, permission | да |
| retry Notification Service | WARNING | есть | attempt, error_type | да |
| timeout Notification Service | ERROR | есть | error_type, target_service | да |

`LOG_LEVEL=DEBUG`: появились `permission_granted` и
`notification_request_attempt`. После возврата `LOG_LEVEL=INFO`
DEBUG-записи отсутствуют (проверено: 0 совпадений), а INFO
(`notification_request_started`, `notification_request_completed`,
`http_request_completed`), WARNING и ERROR продолжают писаться.

## Сетевые ошибки в журнале

503 (notification остановлен):

```
WARNING notification_request_retry attempt=1 error_type=ConnectTimeout
WARNING notification_request_retry attempt=2 error_type=ConnectTimeout
ERROR   notification_service_unavailable attempt=3 error_type=ConnectTimeout
```

504 (сервис принимает соединение, но не отвечает):

```
ERROR notification_service_timeout error_type=ReadTimeout
```

## Исследование request_id

Запросы `lab31-001`, `lab31-002`, `lab31-003` дали по одной записи
`http_request_completed` с соответствующим идентификатором. Запрос
`lab31-cross-service` найден одновременно в журналах `app` и
`notification`. `request_id` связывает записи точнее, чем время:
несколько событий могут иметь близкие или одинаковые метки времени,
а идентификатор уникален для операции и передаётся между сервисами.

## Аудит конфиденциальных данных

Поиск по журналам приложения:

| Шаблон | Совпадений |
| --- | --- |
| `Bearer` | 0 |
| учебный пароль пользователя | 0 |
| выданный access token | 0 |
| `postgresql+psycopg2` | 0 |
| `AUTH_SECRET`, `LAB_DB_PASSWORD` | 0 |

Тело запроса, заголовок `Authorization`, query string и конфигурация
целиком не журналируются.

## Ответы на контрольные вопросы

1. Журналирование — фиксация событий работы приложения в
   структурированном виде для анализа и диагностики.
2. `print()` не имеет уровней, формата, обработчиков и контекста;
   журнал можно фильтровать и обрабатывать автоматически.
3. `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
4. `DEBUG` — подробная диагностика, например успешная проверка
   permission и номер попытки.
5. `INFO` — штатные события: вход, завершение запроса, создание
   уведомления.
6. `WARNING` — необычная ситуация, после которой работа продолжается:
   неверный пароль, retry, отказ permission.
7. `ERROR` — операция не выполнена: timeout, недоступность сервиса,
   ошибочный HTTP-ответ.
8. `CRITICAL` — отказ, при котором приложение в целом не может
   продолжать работу.
9. `INFO` даёт достаточный обзор без большого объёма подробных
   записей.
10. `logging.getLogger(__name__)` создаёт logger с именем модуля,
    поэтому в записи видно источник события.
11. Handler направляет записи в конкретное место — здесь в stdout.
12. Formatter определяет формат записи — здесь JSON.
13. Структурированный журнал хранит поля отдельно, а не только
    текстовую строку.
14. JSON удобно обрабатывать и фильтровать инструментами, он
    однозначно представляет поля.
15. `timestamp`, `level`, `logger`, `message`, `request_id` и
    дополнительные поля события.
16. `request_id` связывает события одной операции, в том числе
    в разных сервисах.
17. Несколько событий могут иметь одинаковое или очень близкое
    время; timestamp не уникален.
18. `ContextVar` хранит значение в контексте выполнения запроса и
    доступен без явной передачи параметров.
19. Middleware основного приложения кладёт `request_id` в контекст,
    клиент передаёт его заголовком, middleware Notification Service
    читает заголовок и устанавливает своё значение контекста.
20. `X-Request-ID`.
21. Клиент видит идентификатор операции и может сообщить его при
    обращении в поддержку или для поиска в журнале.
22. Path не содержит query string, где могут быть чувствительные
    параметры; полный URL раскрывает лишние данные.
23. В теле могут быть пароли и персональные данные; журнал не должен
    становиться их хранилищем.
24. Bearer-токен даёт доступ к API; его попадание в журнал —
    компрометация учётных данных.
25. Пароль не должен попадать в журнал даже при ошибке: журнал
    хранится и копируется, а пароль может быть использован повторно.
26. Допустимо фиксировать `user_id`, `username`, время и результат.
27. `WARNING`.
28. `WARNING`.
29. Успешная проверка — штатная операция, но подробность нужна
    только при диагностике, поэтому DEBUG.
30. `notification_request_retry` уровня WARNING с `attempt` и
    `error_type`.
31. ERROR (`notification_service_unavailable`).
32. ERROR (`notification_service_timeout`).
33. Одинаковый `request_id` позволяет собрать события одной операции
    из журналов разных контейнеров.
34. `duration_ms` показывает длительность операции и помогает найти
    медленные запросы и влияние сетевых задержек.
35. В контейнере stdout собирается средством журналирования Docker и
    не требует файла внутри временной файловой системы.
36. `docker compose logs app`.
37. `docker compose logs notification`.
38. Появляются DEBUG-записи (например, попытки вызова и успешная
    проверка permission); остальные уровни продолжают писаться.
39. Нет, достаточно изменить `LOG_LEVEL` и перезапустить сервис.
40. Секреты в журнале — утечка; журнал может быть доступен шире, чем
    сама конфигурация.
41. Журналировать только необходимый диагностический минимум и не
    копировать пользовательские данные и секреты.

## Git

```bash
git switch -c feature/application-logging
git add app .env.example compose.yaml Dockerfile \
  scripts docs requests.http README.md
git commit -m "Add structured application logging"
```

## Вывод

Оба сервиса пишут структурированные JSON-записи в stdout и
разделяют `request_id`, что позволяет проследить одну операцию через
два контейнера. Уровни различают штатные события, предупреждения и
ошибки, а аудит подтверждает отсутствие паролей, токенов и секретов
в журналах.
