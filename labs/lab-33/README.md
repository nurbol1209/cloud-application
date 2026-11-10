# Лабораторная работа № 32. Отладка программного компонента

## Цель

Освоить практический цикл отладки Cloud Application на примере
`notification_client.py`: воспроизвести контролируемый дефект
off-by-one, локализовать его по журналам ЛР №31, выполнить пошаговую
отладку с точками останова, анализом переменных, Watch и Call Stack,
определить первопричину, внести минимальное исправление и подтвердить
отсутствие регрессии.

## Проверка Docker

```bash
docker version
# bash: docker: command not found
```

Docker Engine в учебной среде отсутствует. Сборка
`cloud-application:0.5`, `docker compose up` и проверка контейнеров
не выполнялись. Конфигурация Compose проверена статически
(`PASS`, [docs/compose_checks.txt](docs/compose_checks.txt)), а
исправление проверено на двух локальных процессах Uvicorn с SQLite.

## Окружение

| Параметр | Значение |
| --- | --- |
| Python | 3.13.14, `.venv` проекта |
| БД | SQLite (`DB_BACKEND=sqlite`) |
| Основное приложение | `http://127.0.0.1:8000` |
| Notification Service | `http://127.0.0.1:9000` |
| Диагностический endpoint | `http://127.0.0.1:9999` (закрыт) |

В Git Bash переменная `NO_PROXY` содержит `[::1]`, что httpx 0.28.1
разбирает как некорректный порт. Локальные процессы и сценарии
запускались через `env -u NO_PROXY`. Код приложения не изменялся:
в контейнерах переменная не наследуется.

## Ожидаемое поведение `send_notification()`

При `NOTIFICATION_MAX_ATTEMPTS=3` и полностью недоступном сервисе:

```
attempt = 1 -> ошибка соединения -> backoff
attempt = 2 -> ошибка соединения -> backoff
attempt = 3 -> ошибка соединения -> NotificationServiceUnavailable
```

События журнала: три `notification_request_attempt`, два
`notification_request_retry` и одно `notification_service_unavailable`
с `"attempt": 3`. В приложении задержки равны 0.5 и 1.0 с, в
диагностическом сценарии — 0.1 и 0.2 с.

## Учебный дефект

В [app/integrations/notification_client.py](app/integrations/notification_client.py)
правильный цикл заменён на вариант без `+ 1`:

```python
# правильный вариант
for attempt in range(1, max_attempts + 1):

# учебный дефект
for attempt in range(1, max_attempts):
```

Другие участки функции не изменялись. `range(1, 3)` создаёт `1, 2`,
поэтому третья попытка не выполняется, а исключение возникает на
резервном `raise` после цикла. Это логическая ошибка границы
(off-by-one error).

## Воспроизводимый сценарий

[scripts/debug_notification_client.py](scripts/debug_notification_client.py)
не требует входа, Swagger, PostgreSQL и не изменяет данные. Он
настраивает недоступный адрес и вызывает реальную функцию
`send_notification()`:

```python
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault(
    "NOTIFICATION_SERVICE_URL",
    "http://127.0.0.1:9999",
)
os.environ.setdefault("NOTIFICATION_TIMEOUT_SECONDS", "0.5")
os.environ.setdefault("NOTIFICATION_MAX_ATTEMPTS", "3")
os.environ.setdefault("NOTIFICATION_RETRY_DELAY_SECONDS", "0.1")
os.environ.setdefault("LOG_LEVEL", "DEBUG")

from app.config import settings
from app.integrations.notification_client import (
    NotificationServiceUnavailable,
    send_notification,
)
from app.logging_config import configure_logging

configure_logging(settings.log_level)


async def main():
    print("Configured max attempts:", settings.notification_max_attempts)

    try:
        await send_notification(
            recipient="debug@cloud.local",
            message="LR32 debug",
        )
    except NotificationServiceUnavailable:
        print("EXPECTED_RESULT: service unavailable")


if __name__ == "__main__":
    asyncio.run(main())
```

`setdefault` позволяет переопределить параметры окружением, например
`NOTIFICATION_MAX_ATTEMPTS=1` для самостоятельного задания.

## Git-ветвь

```bash
git switch main
git pull origin main
git status
git switch -c feature/debug-notification-client
```

Дефект вносится и исправляется в этой ветви; основная ветвь не должна
содержать дефектный код.

## Первый запуск без debugger

```bash
env -u NO_PROXY .venv/Scripts/python.exe \
  scripts/debug_notification_client.py
```

Фактический журнал:

```
Configured max attempts: 3
DEBUG   notification_request_attempt attempt=1
WARNING notification_request_retry   attempt=1 error_type=ConnectTimeout
DEBUG   notification_request_attempt attempt=2
WARNING notification_request_retry   attempt=2 error_type=ConnectTimeout
EXPECTED_RESULT: service unavailable
```

Наблюдение:

- ожидалось три попытки, фактически две;
- `max_attempts = 3` прочитано правильно;
- событие `notification_service_unavailable` отсутствует;
- цикл завершается раньше ожидаемого.

Гипотеза: причина связана с верхней границей цикла, управляющего
номером попытки. Полный протокол —
[docs/debug_session.txt](docs/debug_session.txt).

## Конфигурация Python Debugger в VS Code

`.vscode/launch.json` (каталог исключён из Git):

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "LR32 Debug notification client",
      "type": "debugpy",
      "request": "launch",
      "program": "${workspaceFolder}/scripts/debug_notification_client.py",
      "console": "integratedTerminal",
      "justMyCode": true
    }
  ]
}
```

Запуск: Run and Debug → `LR32 Debug notification client` → F5.
`justMyCode: true` не даёт проваливаться внутрь сторонних библиотек.

В учебной среде нет графического интерфейса VS Code, поэтому
скриншоты панелей не приводятся. Эквивалентные действия выполнены в
стандартном `pdb`: точки останова, `p` (аналог Watch и Debug Console),
`n` (Step Over), `s` (Step Into), `r` (Step Out), `where`
(Call Stack), `c` (Continue). Значения переменных и стек вызовов
совпадают с тем, что показывает VS Code.

## Breakpoint и Variables

Точка останова установлена после вычисления `max_attempts` и после
формирования `url`. Значения в Variables:

```
max_attempts = 3
url = 'http://127.0.0.1:9999/notifications'
```

Конфигурация прочитана правильно, адрес сервиса корректен. Значит,
причина не в настройках и не в URL.

## Watch

| Выражение | Результат | Вывод |
| --- | --- | --- |
| `max_attempts` | `3` | конфигурация верна |
| `list(range(1, max_attempts))` | `[1, 2]` | третья попытка не входит в цикл |
| `list(range(1, max_attempts + 1))` | `[1, 2, 3]` | правильная граница |
| `settings.notification_retry_delay_seconds` | `0.1` | учебная задержка |
| `... * (2 ** (attempt - 1))` при `attempt=1` | `0.1` | первый backoff |
| то же при `attempt=2` | `0.2` | второй backoff |

## Пошаговое выполнение

`F10` / `n` — переход к следующей строке без входа в вызываемую
функцию. После входа в цикл `attempt` последовательно равен `1`, затем
`2`; после второй итерации цикл завершается и `3` не появляется.

`F11` / `s` на строке `response = await client.post(...)` один раз
показывает вход в httpx. Для этой работы внутренний код HTTPX не
исследуется: `Shift+F11` / `r` возвращает в `send_notification()`.

## Второй breakpoint и Call Stack

Точка останова на `if attempt == max_attempts:`:

| Итерация | `attempt` | `max_attempts` | Условие |
| --- | --- | --- | --- |
| 1 | 1 | 3 | `False` |
| 2 | 2 | 3 | `False` |

Третьей итерации нет, поэтому ветвь `attempt == 3` недостижима.

Call Stack при остановке:

```
main()
  -> await send_notification(...)
     -> if attempt == max_attempts:
```

Асинхронная среда добавляет служебные кадры `asyncio.run`,
`run_until_complete`, `_run_once` и `handle._run`; они показывают, что
выполнение пришло из `main()` через event loop.

## Схема локализации

```
max_attempts = 3
        |
        v
breakpoint после max_attempts
        |
        +-- Variables: max_attempts = 3, url = ...:9999
        |
        +-- Watch: range(1, 3)        -> [1, 2]
        |          range(1, 3 + 1)    -> [1, 2, 3]
        |
        v
цикл выполняет attempt 1, 2
        |
        v
if attempt == max_attempts -> всегда False
        |
        v
первопричина: верхняя граница range не включается
```

## Первопричина

В Python `range(start, stop)` не включает `stop`. Поэтому
`range(1, max_attempts)` при `max_attempts = 3` создаёт `1, 2`.
Третья попытка не выполняется, последняя ветвь недостижима, а
исключение возникает на резервном `raise` после цикла.

## Минимальное исправление

```python
for attempt in range(1, max_attempts + 1):
```

Другие части функции не изменялись. Одно изменение проверяет
причинно-следственную связь: если сценарий начинает работать
правильно, гипотеза подтверждается.

## Повторная отладка

```
Configured max attempts: 3
DEBUG   notification_request_attempt attempt=1
WARNING notification_request_retry   attempt=1 error_type=ConnectTimeout
DEBUG   notification_request_attempt attempt=2
WARNING notification_request_retry   attempt=2 error_type=ConnectTimeout
DEBUG   notification_request_attempt attempt=3
ERROR   notification_service_unavailable attempt=3 error_type=ConnectTimeout
EXPECTED_RESULT: service unavailable
```

На третьей итерации `attempt == max_attempts` даёт `True`, ветвь
достигается, итоговая ошибка журналируется с `"attempt": 3`.

## Сравнение до и после

| Параметр | До исправления | После исправления |
| --- | --- | --- |
| `max_attempts` | 3 | 3 |
| attempt 1 | да | да |
| attempt 2 | да | да |
| attempt 3 | нет | да |
| последняя ветвь `attempt == max_attempts` | недостижима | достигается |
| итоговая ошибка | после выхода из цикла | на последней попытке |
| поведение соответствует конфигурации | нет | да |

## Проверка backoff

При `NOTIFICATION_RETRY_DELAY_SECONDS=0.1` и `attempt=1` задержка
равна 0.1 с, при `attempt=2` — 0.2 с. После третьей попытки retry не
выполняется, поэтому третья задержка не рассчитывается и не
применяется. Формула `delay * (2 ** (attempt - 1))` соответствует
экспоненциальному backoff.

## Conditional breakpoint

Точка останова на `if attempt == max_attempts:` с условием
`attempt == 3`:

```
(Pdb) condition 1 attempt == 3
New condition set for breakpoint 1.
(Pdb) c
-> if attempt == max_attempts:
(Pdb) p attempt
3
(Pdb) p attempt == max_attempts
True
```

Остановка происходит только на третьей попытке. В дефектном варианте
условие не срабатывает ни разу, потому что `attempt` принимает только
значения 1 и 2.

## Debug Console

Во время остановки проверены выражения:

```
attempt
max_attempts
attempt == max_attempts
list(range(1, max_attempts + 1))
```

Значения не изменялись: задача — наблюдать состояние. В `pdb`
аналогом служит команда `p`.

## Встроенный `breakpoint()`

Временно добавленный вызов перед циклом:

```
$ python scripts/debug_notification_client.py
> .../notification_client.py(46)send_notification()
-> breakpoint()
(Pdb) p max_attempts
3
(Pdb) n
(Pdb) c
```

`p` выводит выражение, `n` переходит к следующей строке, `c`
продолжает выполнение. После эксперимента вызов удалён из рабочего
кода; итоговый файл содержит только цикл `range(1, max_attempts + 1)`.

## Самостоятельное задание: `max_attempts = 1`

Ошибочный вариант — `range(1, 1)` пуст, попыток нет:

```
$ NOTIFICATION_MAX_ATTEMPTS=1 python scripts/debug_notification_client.py
Configured max attempts: 1
EXPECTED_RESULT: service unavailable
```

Исправленный вариант — одна попытка:

```
Configured max attempts: 1
DEBUG notification_request_attempt attempt=1
ERROR notification_service_unavailable attempt=1 error_type=ConnectTimeout
EXPECTED_RESULT: service unavailable
```

При `max_attempts = 1` дефект проявляется максимально: не выполняется
ни одной попытки. `range(1, max_attempts + 1)` даёт `range(1, 2)` →
`[1]`, поэтому исправление корректно и для этого значения.

## Регрессия через HTTP

Notification Service и приложение запущены локально, БД SQLite.

Штатный сценарий (`X-Request-ID: lab32-final-201`):

```
app:
  DEBUG notification_request_attempt attempt=1
  INFO  notification_request_completed status_code=201 attempt=1
  INFO  http_request_completed path=/integration/notifications status_code=201

notification:
  INFO notification_created notification_id=2 status_code=201

HTTP/1.1 201
{"id": 2, "recipient": "debug@cloud.local",
 "message": "LR32 final regression", "status": "accepted"}
```

Отказ (`notification` остановлен,
`X-Request-ID: lab32-regression-down`):

```
WARNING notification_request_retry attempt=1 error_type=ConnectTimeout
WARNING notification_request_retry attempt=2 error_type=ConnectTimeout
ERROR   notification_service_unavailable attempt=3 error_type=ConnectTimeout
HTTP/1.1 503
{"detail": "Notification service is unavailable"}
```

Восстановление (`notification` запущен снова,
`X-Request-ID: lab32-regression-restored`): `201`, одна успешная
попытка. Это подтверждает отсутствие регрессии: исправленный
компонент работает и при доступном, и при недоступном сервисе.

## Compose и образ 0.5

| Изменение | Значение |
| --- | --- |
| образ `app`, `migrate`, `notification` | `cloud-application:0.5` |
| метка `Dockerfile` | `version="0.5"` |
| `notification` | отдельный процесс, порт 9000 |

```bash
docker build -t cloud-application:0.5 .
docker compose config
docker compose down
docker compose up -d
docker compose ps
docker compose stop notification
docker compose start notification
```

Эти команды не выполнялись: Docker недоступен. Статическая проверка
`python scripts/check_compose_config.py` завершилась `PASS`; результат
сохранён в `docs/compose_checks.txt`. Локальный эквивалент проверки
успешного и неуспешного сценариев выполнен через Uvicorn и приведён
выше.

## Проверка итогового кода

```bash
grep -n "breakpoint()" app/integrations/notification_client.py
# совпадений нет

grep -n "for attempt in range" app/integrations/notification_client.py
# for attempt in range(1, max_attempts + 1):
```

Временный дефект и отладочные остановки в рабочем коде отсутствуют.

## Ответы на контрольные вопросы

1. Отладка — процесс поиска, локализации и устранения причин
   неправильной работы программы.
2. Симптом — наблюдаемое проявление (две попытки вместо трёх);
   первопричина — дефект границы цикла, который это проявление
   вызывает.
3. Воспроизводимость позволяет повторять наблюдение, проверять
   гипотезы и подтверждать исправление.
4. Журналы показывают, где и при каких значениях проявляется
   проблема, и помогают сузить участок до конкретной функции.
5. Breakpoint — точка останова, в которой debugger приостанавливает
   выполнение.
6. Открыть Run and Debug, выбрать конфигурацию `launch.json` и нажать
   F5.
7. F5 запускает выбранную конфигурацию отладки.
8. Step Over выполняет строку целиком, не входя во внутренние
   вызовы.
9. Step Into входит внутрь вызываемой функции.
10. Step Out выполняет остаток текущей функции и возвращается в
    вызывающую.
11. Variables показывает локальные и доступные переменные в текущем
    кадре.
12. Watch вычисляет заданные выражения при каждой остановке.
13. Call Stack показывает цепочку вызовов, приведшую к текущей
    строке.
14. Debug Console позволяет выполнять выражения и команды в контексте
    остановки.
15. Логическая ошибка — программа синтаксически корректна, но
    реализует неверную логику.
16. Off-by-one error — ошибка на единицу в границе диапазона или
    индекса.
17. Нет, `stop` не включается.
18. `range(1, 3)` создаёт `1, 2`.
19. Верхняя граница 3 исключается, поэтому итерации только 1 и 2.
20. В цикл добавлено `+ 1`: `range(1, max_attempts + 1)`.
21. Чтобы последнее значение `max_attempts` вошло в диапазон.
22. Debugger показал `max_attempts = 3` и корректный `url`, исключив
    ошибку конфигурации.
23. `max_attempts`, оба варианта `range`, задержку retry и формулу
    backoff.
24. Потому что цикл не создаёт значение `attempt = 3`.
25. Чтобы проверить, что исправление устранило дефект и не изменило
    ожидаемое поведение.
26. Регрессия — новый дефект в ранее работавшей функциональности.
27. Исправленный компонент участвует в реальном межсервисном
    взаимодействии; успешный запрос подтверждает, что он не нарушен.
28. Чтобы остановиться только при конкретном состоянии, например
    `attempt == 3`.
29. Вычислять выражения, проверять переменные и вызывать функции в
    контексте остановки.
30. Встроенная функция останавливает выполнение и запускает debugger
    без отдельной конфигурации.
31. Иначе программа будет останавливаться при каждом запуске, в том
    числе в рабочей среде.
32. Debugger даёт состояние переменных и стек в реальном времени;
    `print()` требует заранее выбранных точек и изменений кода.
33. Минимальное изменение точнее подтверждает причину и снижает риск
    нового дефекта.
34. База данных не влияет на логику повторных попыток; сценарий
    изолирован от лишних компонентов.
35. Малое число переменных делает поведение воспроизводимым и
    однозначным.
36. Журналы показывают симптом и участок, debugger — конкретную
    строку и значения переменных.
37. Цель работы — логика повторов в своём коде, а не устройство HTTPX;
    внешний код только подтверждает сетевую ошибку.
38. `range(1, 1)` пуст, поэтому не выполняется ни одной попытки и
    сразу возникает итоговое исключение.

## Git

```bash
git switch -c feature/debug-notification-client
git add app/integrations/notification_client.py \
  scripts/debug_notification_client.py \
  compose.yaml docs/debug_session.txt \
  docs/compose_checks.txt README.md
git diff --staged
git commit -m "Fix notification retry off-by-one error"
git push -u origin feature/debug-notification-client
```

`.vscode/` не добавляется в Git. В коммит входят исправленный цикл,
диагностический сценарий и обновлённые материалы отчёта.

## Вывод

Дефект воспроизведён изолированным сценарием и локализован по
журналам. Debugger подтвердил, что конфигурация верна, а
`range(1, max_attempts)` создаёт только `[1, 2]`. Первопричина —
исключение верхней границы диапазона; минимальное исправление
`range(1, max_attempts + 1)` восстановило три попытки и достижимость
последней ветви. Повторная проверка подтвердила поведение при
`max_attempts = 1`, успешный запрос `201`, отказ `503` и
восстановление `201`, то есть отсутствие регрессии.
