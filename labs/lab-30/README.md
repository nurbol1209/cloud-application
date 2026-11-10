# Лабораторная работа № 30. Обработка ошибок сетевого взаимодействия

## Цель

Повысить устойчивость межсервисного взаимодействия Cloud Application:
добавить явные тайм-ауты, собственные исключения интеграционного слоя,
ограниченные повторные попытки только для ошибок установления
соединения и контролируемые ответы `502`, `503`, `504`.

## Проверка Docker

```bash
docker version
# bash: docker: command not found
```

Docker Engine в текущей среде отсутствует, поэтому `docker build`,
`docker compose stop/pause/unpause` не выполнялись. Статическая
проверка Compose:

```bash
python scripts/check_compose_config.py
# PASS: compose.yaml соответствует требованиям лабораторной работы
```

Результат сохранён в `docs/compose_checks.txt`. Все сценарии отказов
проверены локально на двух реальных HTTP-процессах; протокол
находится в `docs/error_scenarios.txt`.

## Типы ошибок межсервисного вызова

| Ситуация | Пример | Поведение Cloud Application |
| --- | --- | --- |
| Успех | `201 Created` | вернуть результат клиенту |
| Ошибка соединения | сервис остановлен | ограниченный retry → `503` |
| Timeout | сервис не отвечает вовремя | `504` |
| Ошибочный HTTP-ответ | `4xx` / `5xx` | `502` |

Сетевое исключение не выходит из интеграционного модуля наружу:
клиент получает понятный ответ основного API.

## Схема обработки запроса

```
Пользователь
    |
    | POST /integration/notifications
    v
Cloud Application
    |-- require_permission("services.write") --> 401 / 403
    |
    v
notification_client.send_notification()
    |
    | attempt 1..N, httpx.Timeout(2.0)
    v
Notification Service
    |
    +-- 201 ----------------------> 201 клиенту
    +-- ConnectError/ConnectTimeout -> пауза -> retry -> 503
    +-- TimeoutException ----------> 504 (без retry)
    +-- HTTP 4xx/5xx --------------> 502 (без retry)
```

## Конфигурация

В [app/config.py](app/config.py) добавлены:

```python
notification_service_url: str = "http://127.0.0.1:9000"
notification_timeout_seconds: float = 2.0
notification_max_attempts: int = 3
notification_retry_delay_seconds: float = 0.5
```

В `.env.example`:

```
NOTIFICATION_SERVICE_URL=http://127.0.0.1:9000
NOTIFICATION_TIMEOUT_SECONDS=2.0
NOTIFICATION_MAX_ATTEMPTS=3
NOTIFICATION_RETRY_DELAY_SECONDS=0.5
```

Параметры не являются секретами: это обычная конфигурация поведения
клиента. В Compose для `app` значения продублированы явно.

## Собственные исключения интеграции

```python
class NotificationServiceError(Exception):
    pass


class NotificationServiceUnavailable(NotificationServiceError):
    pass


class NotificationServiceTimeout(NotificationServiceError):
    pass


class NotificationServiceBadResponse(NotificationServiceError):
    def __init__(self, status_code: int):
        self.status_code = status_code
        super().__init__(
            f"Notification service returned HTTP {status_code}"
        )
```

Router не зависит от классов исключений httpx: он различает только
три состояния интеграции — недоступность, тайм-аут и ошибочный
ответ.

## Полный notification_client.py

[app/integrations/notification_client.py](app/integrations/notification_client.py):

```python
import asyncio

import httpx

from app.config import settings


class NotificationServiceError(Exception):
    pass


class NotificationServiceUnavailable(NotificationServiceError):
    pass


class NotificationServiceTimeout(NotificationServiceError):
    pass


class NotificationServiceBadResponse(NotificationServiceError):
    def __init__(self, status_code: int):
        self.status_code = status_code
        super().__init__(
            f"Notification service returned HTTP {status_code}"
        )


async def send_notification(recipient: str, message: str) -> dict:
    url = f"{settings.notification_service_url}/notifications"
    payload = {"recipient": recipient, "message": message}

    timeout = httpx.Timeout(settings.notification_timeout_seconds)
    max_attempts = settings.notification_max_attempts

    for attempt in range(1, max_attempts + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            if attempt == max_attempts:
                raise NotificationServiceUnavailable() from exc

            delay = (
                settings.notification_retry_delay_seconds
                * (2 ** (attempt - 1))
            )
            await asyncio.sleep(delay)
        except httpx.TimeoutException as exc:
            raise NotificationServiceTimeout() from exc
        except httpx.HTTPStatusError as exc:
            raise NotificationServiceBadResponse(
                exc.response.status_code
            ) from exc
        except httpx.RequestError as exc:
            raise NotificationServiceUnavailable() from exc

    raise NotificationServiceUnavailable()
```

`get_notification()` из лабораторной работы №29 сохранён и использует
тот же явный timeout.

## Политика повторных попыток

Повтор выполняется только при `ConnectError` и `ConnectTimeout` —
ошибках установления соединения, когда запрос до сервиса не дошёл.

| После неудачной попытки | Задержка |
| --- | --- |
| 1 | 0,5 с |
| 2 | 1,0 с |
| 3 | новая попытка не выполняется |

```
попытка 1 --ConnectError--> 0,5 с
попытка 2 --ConnectError--> 1,0 с
попытка 3 --ConnectError--> NotificationServiceUnavailable
попытка N --ReadTimeout----> NotificationServiceTimeout (без retry)
попытка N --HTTP 4xx/5xx---> NotificationServiceBadResponse (без retry)
```

`POST /notifications` изменяет состояние удалённого сервиса. Если
сервер уже создал уведомление, а ответ потерялся или задержался,
повтор создаст дубликат. Поэтому `ReadTimeout` и ошибочные
HTTP-статусы автоматически не повторяются: для безопасного повтора
после обработки запроса нужна идемпотентность.

## Router интеграции

[app/routers/integration.py](app/routers/integration.py):

```python
@router.post(
    "/notifications",
    response_model=NotificationSendResponse,
    status_code=201,
    summary="Передать уведомление внутреннему сервису",
)
async def forward_notification(
    notification: NotificationSendRequest,
    current_user: User = Depends(
        require_permission("services.write")
    ),
):
    try:
        result = await send_notification(
            recipient=notification.recipient,
            message=notification.message,
        )
        return result
    except NotificationServiceTimeout as exc:
        raise HTTPException(
            status_code=504,
            detail="Notification service response timeout",
        ) from exc
    except NotificationServiceUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail="Notification service is unavailable",
        ) from exc
    except NotificationServiceBadResponse as exc:
        raise HTTPException(
            status_code=502,
            detail="Notification service returned an invalid response",
        ) from exc
```

Маршрут теперь явно возвращает `201 Created`, как требует успешный
сценарий лабораторной работы №30. Авторизация не изменилась:
используется существующее разрешение `services.write`.

| Код | Ситуация |
| --- | --- |
| `201` | Notification Service принял уведомление |
| `502 Bad Gateway` | сервис ответил ошибочным HTTP-статусом |
| `503 Service Unavailable` | соединение установить не удалось |
| `504 Gateway Timeout` | сервис не ответил за допустимое время |

## Диагностический endpoint

В [app/notification_service/main.py](app/notification_service/main.py)
добавлен учебный маршрут:

```python
@app.get(
    "/test/error/{status_code}",
    summary="Сформировать тестовую ошибку",
)
def test_error(status_code: int):
    raise HTTPException(
        status_code=status_code,
        detail="Test service error",
    )
```

## Сборка и Compose

| Изменение | Значение |
| --- | --- |
| образ | `cloud-application:0.3` |
| `app`, `migrate`, `notification` | используют `cloud-application:0.3` |
| `app.environment` | добавлены `NOTIFICATION_TIMEOUT_SECONDS`, `NOTIFICATION_MAX_ATTEMPTS`, `NOTIFICATION_RETRY_DELAY_SECONDS` |
| метка `Dockerfile` | `org.opencontainers.image.version="0.3"` |

```bash
docker build -t cloud-application:0.3 .
docker image ls cloud-application
docker compose config
docker compose down
docker compose up -d
```

В текущей среде эти команды не выполнялись из-за отсутствия Docker.
Конфигурация проверена статически: `PASS`.

## Нормальный сценарий

```bash
curl -X POST http://127.0.0.1:8000/integration/notifications \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"recipient":"stable@cloud.local",
       "message":"Network error handling enabled"}'
```

```
HTTP 201

{"id":1,"recipient":"stable@cloud.local",
 "message":"Network error handling enabled","status":"accepted"}
```

Обработка ошибок не изменила успешное поведение.

## Недоступный Notification Service

Локальный аналог `docker compose stop notification` — остановка
процесса Uvicorn:

```bash
POST /integration/notifications
```

```
HTTP 503, время ответа около 10,4 с

{"detail":"Notification service is unavailable"}
```

На Windows подключение к закрытому порту завершается не мгновенным
отказом, а `ConnectTimeout` (около 2,7 с на попытку). Три попытки и
задержки 0,5 с + 1,0 с дают наблюдавшееся время. Класс события —
`ConnectError`/`ConnectTimeout`, retry выполнялся.

## Тайм-аут ответа

Docker-аналог — `docker compose pause notification`. В локальной среде
использован TCP-сервер, который принимает соединение и не отвечает:
сетевой путь существует, приложение не обрабатывает запрос.

```
HTTP 504, время ответа около 3,0 с

{"detail":"Notification service response timeout"}
```

Класс события — `httpx.ReadTimeout` (подкласс `TimeoutException`),
повтор не выполнялся. Значение `NOTIFICATION_TIMEOUT_SECONDS=2.0`
ограничило ожидание.

## Ошибочный HTTP-ответ

```bash
python -c "import httpx; r=httpx.get(
'http://127.0.0.1:9000/test/error/503');
print(r.status_code); r.raise_for_status()"
# 503
# httpx.HTTPStatusError
```

```bash
# /test/error/400
# 400
# httpx.HTTPStatusError
```

Преобразование в `502` проверено заглушечным HTTP-сервером, который
отвечает на POST кодом `500` (приложение запущено с
`NOTIFICATION_SERVICE_URL=http://127.0.0.1:9100`):

```
HTTP 502

{"detail":"Notification service returned an invalid response"}
```

Внутренний ответ зависимого сервиса пользователю не передаётся:
Notification Service — деталь реализации Cloud Application.

## Самостоятельная работа

| Сценарий | Состояние notification | Класс события | Retry | Код Cloud Application | Результат |
| --- | --- | --- | --- | --- | --- |
| A | работает | успешный ответ | нет | `201` | `status=accepted` |
| B | остановлен | `ConnectError`/`ConnectTimeout` | да, 3 попытки | `503` | «Notification service is unavailable» |
| C | принимает соединение, не отвечает | `ReadTimeout` (`TimeoutException`) | нет | `504` | «Notification service response timeout» |
| D | снова работает | успешный ответ | нет | `201` | `status=accepted` |

После каждого отказа сервис восстанавливался, и следующий запрос
снова завершался успешно. Список уведомлений после перезапуска пуст:
данные хранятся в памяти процесса.

## Изменение timeout

При `NOTIFICATION_TIMEOUT_SECONDS=1.0` и неотвечающем сервисе:

```
HTTP 504, время ответа около 2,2 с
```

При значении `2.0` время составляло около `3,0 с`. Параметр влияет
именно на ожидание ответа; повтор при `ReadTimeout` не выполняется,
поэтому длительность примерно равна значению timeout плюс накладные
расходы. После эксперимента восстановлено `2.0`.

## Изменение числа попыток

При `NOTIFICATION_MAX_ATTEMPTS=2` и
`NOTIFICATION_RETRY_DELAY_SECONDS=0.25` недоступный сервис дал:

```
HTTP 503, время ответа около 6,4 с
```

При `3` попытках и задержке `0.5` время составляло около `10,4 с`.
После эксперимента восстановлены значения `3` и `0.5`.

## Анализ безопасности retry

- `ConnectError` — разумный кандидат для повтора: соединение не было
  установлено, поэтому запрос почти наверняка не дошёл до сервиса и
  не изменил его состояние.
- `ReadTimeout` для POST автоматически повторять опасно: сервер мог
  принять запрос, создать уведомление и не успеть вернуть ответ.
- Если первый запрос был обработан, а ответ потерян, повтор создаст
  второе уведомление — дубликат операции.
- Для безопасных повторов операция должна быть идемпотентной:
  например, клиент передаёт уникальный `request_id`, а сервис хранит
  соответствие `request_id → notification` и возвращает ранее
  созданный результат.
- Количество retry ограничивают, чтобы отказ не занимал выполнение
  пользовательской операции неограниченно долго и не создавал
  лавину запросов.
- Задержка увеличивается (exponential backoff), чтобы дать сервису
  время восстановиться и не перегружать его частыми повторами.
- Автоматический retry может усилить перегрузку зависимого сервиса:
  каждый клиент умножает число обращений во время сбоя.

## Ответы на контрольные вопросы

1. Удалённый вызов зависит от сети, состояния и загрузки другого
   процесса; локальный вызов функции выполняется в том же процессе
   и не имеет сетевых отказов.
2. Timeout — предельное время ожидания сетевой операции.
3. Без ограничения вызывающий сервис может ждать недоступный
   компонент неопределённо долго и исчерпать ресурсы.
4. HTTP-клиент различает connect, read, write и pool timeout;
   `httpx.Timeout` задаёт их значения.
5. `TimeoutException` — общее исключение httpx для превышения
   времени ожидания; конкретные виды — `ConnectTimeout`,
   `ReadTimeout`, `WriteTimeout`, `PoolTimeout`.
6. `ConnectError` — не удалось установить TCP-соединение с сервисом.
7. `HTTPStatusError` — ответ получен, но `raise_for_status()`
   обнаружил код `4xx`/`5xx`.
8. `raise_for_status()` превращает ошибочный HTTP-статус
   в исключение, чтобы клиент не обрабатывал его как успех.
9. Retry — повторная попытка выполнить запрос после временной
   ошибки.
10. Бесконечный retry может навсегда занять обработку запроса и
    усилить перегрузку зависимого сервиса.
11. Exponential backoff — увеличение паузы между попытками
    (здесь `0.5 × 2^(attempt-1)`).
12. При базовом значении `0,5` используются `0,5 с` и `1,0 с`.
13. В основной реализации — три попытки
    (`NOTIFICATION_MAX_ATTEMPTS=3`).
14. `ConnectError` означает, что запрос не дошёл до сервиса, поэтому
    его повтор не создаёт дубликат.
15. `ReadTimeout` может возникнуть после того, как сервер уже
    обработал POST; повтор создаст дубликат.
16. POST изменяет состояние; безопасное чтение (GET) повторять
    проще, потому что оно не создаёт новых записей.
17. Дублирование операции — повторное выполнение уже выполненного
    изменения (второе уведомление).
18. Идемпотентность позволяет повторять запрос без создания
    повторного эффекта: сервис узнаёт операцию по ключу.
19. Собственные исключения отделяют технические классы httpx от
    логики приложения и дают router понятные состояния.
20. Router не должен зависеть от деталей библиотеки: при смене
    клиента или версии httpx меняется только интеграционный слой.
21. `503` возвращается, когда соединение с Notification Service
    установить не удалось после исчерпания попыток.
22. `504` возвращается, когда сервис не ответил за
    `NOTIFICATION_TIMEOUT_SECONDS`.
23. `502` используется, когда зависимый сервис вернул ошибочный
    HTTP-статус.
24. Внутренний ответ — деталь реализации; пользователь получает
    контролируемое сообщение уровня интеграции без раскрытия
    внутреннего API.
25. `stop` завершает процессы контейнера (соединение не
    устанавливается), `pause` замораживает их (соединение возможно,
    ответа нет).
26. Восстановить paused-контейнер: `docker compose unpause
    notification`.
27. После восстановления сервис снова принимает соединения и
    обрабатывает запросы; приложение не хранит состояние отказа.
28. Параметры хранятся в `app/config.py` (`Settings`) и
    переопределяются переменными окружения и Compose.
29. Нет, timeout, число попыток и задержка не являются секретами.
30. URL остаётся в конфигурации, чтобы один код работал локально,
    в Compose и в другой среде без изменения бизнес-логики.
31. Ограничение числа повторов защищает время ответа пользователю
    и зависимый сервис от лавины запросов.
32. Увеличивающаяся пауза даёт сервису время восстановиться и
    снижает нагрузку в момент сбоя.
33. Повторяющиеся запросы от многих клиентов умножают нагрузку на
    уже перегруженный сервис.
34. `/test/error/{status_code}` позволяет получить контролируемый
    ошибочный HTTP-ответ и исследовать `raise_for_status()` и
    преобразование в `502`.
35. Выполнить запрос к `/test/error/503` и вызвать
    `raise_for_status()`; будет получен `httpx.HTTPStatusError`.
36. Полноценное журналирование — тема лабораторной работы №31;
    в ЛР №30 намеренно не вводятся logger, уровни и файлы журналов.
37. Для безопасного повтора уже обработанного POST нужен ключ
    идемпотентности (`request_id`) и хранение результата операции
    на стороне сервиса.

## Примечание об окружении

В Git Bash переменная `NO_PROXY` содержит шаблон `[::1]`, который
`httpx 0.28.1` разбирает как URL с некорректным портом. Проверочные
процессы запускались с `env -u NO_PROXY`; в контейнерах Docker эта
переменная не задана. В код приложения обходных решений не
добавлялось.

## Git

```bash
git switch -c feature/network-error-handling
git add app .env.example compose.yaml Dockerfile \
  scripts docs requests.http README.md
git commit -m "Handle service communication errors"
```

## Вывод

Интеграционный слой преобразует сетевые сбои в три понятных
состояния, а router — в коды `502`, `503`, `504`. Явный timeout
ограничивает ожидание, retry с backoff применяется только к ошибкам
соединения, успешный сценарий и авторизация сохранены. Остаётся
задача наблюдаемости — она решается в лабораторной работе №31.
