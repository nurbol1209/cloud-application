# Лабораторная работа № 33. Статический анализ и стандартизация кода

## Цель

Подключить Ruff как единый инструмент линтинга и форматирования,
настроить правила проекта в `pyproject.toml`, исследовать нарушения
F401, F841, E711, I001 и F821, выполнить безопасные автоматические и
ручные исправления, стандартизировать оформление `app/` и `scripts/`
и сформировать воспроизводимый quality gate перед коммитом.

## Проверка Docker

```bash
docker version
# bash: docker: command not found
```

Docker Engine недоступен, поэтому сборка `cloud-application:0.6`,
`docker compose up` и контейнерная smoke-проверка не выполнялись.
Конфигурация Compose проверена статически
([docs/compose_checks.txt](docs/compose_checks.txt)), приложение
проверено локально на Uvicorn с SQLite.

## Linter и formatter

| Инструмент | Вопрос | Команда |
| --- | --- | --- |
| linter | какие нарушения правил есть в коде? | `ruff check` |
| formatter | как привести оформление к единому виду? | `ruff format` |

Linter анализирует структуру и находит потенциальные проблемы;
formatter переписывает оформление, не меняя логику. В работе
используются обе функции Ruff.

```
исходный код
   -> ruff check (диагностика)
   -> безопасные / ручные исправления
   -> ruff format (оформление)
   -> повторная проверка
   -> quality gate
   -> Git
```

## Инструмент разработки

```bash
python -m pip install ruff mypy
ruff --version
# ruff 0.17.4
mypy --version
# mypy 2.4.1
```

Ruff и mypy не нужны FastAPI-приложению в контейнере, поэтому они не
добавлены в `requirements-direct.txt` и runtime `requirements.txt`.

[requirements-dev.txt](requirements-dev.txt):

```
mypy==2.4.1
ruff==0.17.4
```

## Конфигурация

[pyproject.toml](pyproject.toml):

```toml
[tool.ruff]
line-length = 88
extend-exclude = [
    ".venv",
    "migrations/versions",
    "storage",
]

[tool.ruff.lint]
select = [
    "E4",
    "E7",
    "E9",
    "F",
    "I",
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
```

`migrations/versions` исключён как автоматически созданный Alembic-код.
`secrets/` и `storage/` не являются исходным кодом и также не
анализируются. Набор `E4`, `E7`, `E9` покрывает выбранные группы
pycodestyle, `F` — Pyflakes, `I` — порядок импортов.

Проверка применённых настроек:

```bash
ruff check app/config.py --show-settings
# Settings path: ...\lab-33\pyproject.toml
# linter.line_length = 88
# file_resolver.extend_exclude = .venv, migrations/versions, storage
# linter.rules.enabled = I001, E401, ... F401 ...
```

## Воспроизводимый пример

[scripts/static_analysis_sample.py](scripts/static_analysis_sample.py)
до исправлений:

```python
import sys, os
from pathlib import Path

def build_message( name ):
    unused_value = 10
    if name == None:
        return "Unknown"
    return "Service: " + name

print(build_message("notification"))
```

Первый запуск `ruff check`:

```
E401 [*] Multiple imports on one line          строка 1
I001 [*] Import block is un-sorted             строка 1
F401 [*] `sys` imported but unused             строка 1
F401 [*] `os` imported but unused              строка 1
F401 [*] `pathlib.Path` imported but unused    строка 2
F841 [ ] Local variable `unused_value` ...     строка 5
E711 [ ] Comparison to `None` should be ...    строка 6

Found 7 errors.
```

Сообщение читается как `файл:строка:столбец: код правило`. Код
обозначает правило, текст объясняет нарушение.

## Правила

| Правило | Что обнаруживает | Влияние на выполнение | Исправление |
| --- | --- | --- | --- |
| F401 | неиспользуемый импорт | обычно нет; возможен побочный эффект импорта | удалить импорт (авто) |
| F841 | неиспользуемая локальная переменная | присваивание может иметь побочный эффект | удалить после проверки (вручную) |
| E711 | сравнение с `None` через `==` | может дать неверный результат для перегруженного `__eq__` | `is None` (вручную) |
| I001 | несортированный блок импортов | не влияет, только читаемость и diff | organize imports (авто) |
| F821 | неопределённое имя | `NameError` при выполнении | определить имя или исправить ссылку |

Документация правил получена командами `ruff rule F401`, `ruff rule
F841`, `ruff rule E711`, `ruff rule I001`, `ruff rule F821`.

## Статистика примера

```
3  F401  [*] unused-import
1  E401  [*] multiple-imports-on-one-line
1  E711  [ ] none-comparison
1  I001  [*] unsorted-imports
1  F841  [ ] unused-variable
```

## Безопасные исправления

```bash
ruff check scripts/static_analysis_sample.py --fix
# Found 6 errors (4 fixed, 2 remaining).
```

`git diff` после `--fix` показывает удаление всех трёх импортов:
`sys`, `os`, `pathlib.Path` не использовались, поэтому F401, E401 и
I001 исчезли одновременно. F841 и E711 в Ruff 0.17.4 помечены как
unsafe и автоматически не применялись.

Ручные исправления:

```python
-    unused_value = 10
-    if name == None:
+    if name is None:
```

`unused_value` не имеет побочных эффектов; замена `== None` на
`is None` корректна. После исправлений: `All checks passed`.

## Форматирование

```bash
ruff format --check scripts/static_analysis_sample.py
# unformatted: File would be reformatted

ruff format --diff scripts/static_analysis_sample.py
# - def build_message( name ):
# + def build_message(name):
# + пустая строка перед print(...)

ruff format scripts/static_analysis_sample.py
# 1 file reformatted

ruff format --check scripts/static_analysis_sample.py
# 1 file already formatted
```

`--check` не изменяет файл, `--diff` показывает будущие изменения,
`format` применяет их. Финальная проверка примера: lint и format
проходят, запуск выводит:

```
Service: notification
```

Поведение программы не изменилось.

## Анализ реального проекта

```bash
ruff check app scripts
# app/logging_config.py:4:8: F401 `sys` imported but unused

ruff check app scripts --statistics
# 1  F401  [*] unused-import
```

Классификация: неиспользуемый код — 1 (F401). Других категорий
выбранного набора не обнаружено. Причина: после перехода на
`ext://sys.stdout` модуль `sys` в `logging_config.py` не используется.

Безопасное исправление:

```bash
ruff check app scripts --fix
# Found 1 error (1 fixed, 0 remaining).
```

`git diff` подтвердил удаление только строки `import sys`:

```diff
-import sys
 from datetime import datetime, timezone
```

Повторная проверка: `All checks passed`.

## Стандартизация оформления

```bash
ruff format --check app scripts
# 19 files would be reformatted, 27 files already formatted

ruff format --diff app scripts
# полный diff сохранён в docs/format_diff.txt

ruff format app scripts
# 19 files reformatted, 27 files left unchanged

ruff format --check app scripts
# 46 files already formatted
```

Изменения только в оформлении: переносы длинных выражений, отступы,
пустые строки, скобки. Логика не менялась. `git diff --stat` показывает
24 изменённых файла, `+86 / -180` строк.

## Цикл стандартизации

```
ruff check
   -> классификация
   -> safe --fix
   -> git diff
   -> ручное исправление
   -> format --check
   -> format --diff
   -> format
   -> повторный quality gate
```

Сначала проверка и просмотр diff, затем применение formatter — это
безопаснее массового форматирования без предварительного анализа.

## Quality gate

[scripts/check_quality.ps1](scripts/check_quality.ps1):

```powershell
$python = "python"
$venvPython = Join-Path $PSScriptRoot "..\..\..\.venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $python = $venvPython
}

Write-Host "1. Ruff lint"
& $python -m ruff check app scripts
if ($LASTEXITCODE -ne 0) {
    Write-Error "Ruff lint failed"
    exit $LASTEXITCODE
}

Write-Host "2. Ruff format check"
& $python -m ruff format --check app scripts
if ($LASTEXITCODE -ne 0) {
    Write-Error "Ruff format check failed"
    exit $LASTEXITCODE
}

Write-Host "QUALITY CHECK PASSED"
```

Для Linux/macOS и CI добавлен эквивалент
[scripts/check_quality.sh](scripts/check_quality.sh). Скрипт только
проверяет проект и ничего не изменяет.

Результат:

```
1. Ruff lint
All checks passed!
2. Ruff format check
46 files already formatted
QUALITY CHECK PASSED
```

`git diff --check` завершился без ошибок пробельных символов.

## Функциональная проверка

```bash
python -m compileall -q app scripts
# exit 0
```

Локальный запуск с SQLite:

```
GET /status -> 200
GET /docs   -> 200
POST /integration/notifications -> 201
```

Журнал приложения для `X-Request-ID: lab33-smoke-201`:

```
INFO notification_request_started
INFO notification_request_completed status_code=201 attempt=1
INFO http_request_completed status_code=201
```

Ответ:

```json
{"id": 1, "recipient": "quality@cloud.local",
 "message": "LR33 smoke after ruff format", "status": "accepted"}
```

## Образ 0.6

| Изменение | Значение |
| --- | --- |
| образ `app`, `migrate`, `notification` | `cloud-application:0.6` |
| метка `Dockerfile` | `version="0.6"` |
| статическая проверка Compose | `PASS` |

```bash
docker build -t cloud-application:0.6 .
docker compose config
docker compose down
docker compose up -d
docker compose ps
```

Команды Docker не выполнялись: Docker Engine отсутствует. Проверка
`scripts/check_compose_config.py` подтверждает версию 0.6 и структуру
Compose.

## Самостоятельная работа

| Файл | Lint до | Format до | Lint после | Format после |
| --- | --- | --- | --- | --- |
| `app/main.py` | 0 | требуется | 0 | OK |
| `app/integrations/notification_client.py` | 0 | требуется | 0 | OK |
| `app/notification_service/main.py` | 0 | уже формат | 0 | OK |

Единственное lint-нарушение проекта было в `logging_config.py`.
Выбранные файлы нарушали только форматирование, кроме
`notification_service/main.py`, который уже соответствовал formatter.

## Анализ одного правила: F401

- Код: `F401 imported but unused`.
- Фрагмент: `import sys` в `app/logging_config.py`.
- Назначение: неиспользуемый импорт засоряет зависимости и может
  скрывать реально нужный импорт; импорт также способен иметь побочный
  эффект.
- Исправление: удаление импорта, автоматическое.
- Влияние на runtime: в данном случае отсутствует, `sys` не
  использовался.
- Тип исправления: автоматический безопасный `--fix`.

## Эксперимент F821

Временная строка `print(undefined_status)` добавлена в пример, файл не
запускался:

```
F821 Undefined name `undefined_status`
 --> scripts/static_analysis_sample.py:9:7
```

После удаления строки: `All checks passed`. Неопределённое имя
обнаружено статически, без выполнения программы.

## Почему не используется `--unsafe-fixes`

- Автоматическое исправление изменяет код; диагностика только
  сообщает о нарушении.
- `git diff` показывает, что именно changed, и позволяет заметить
  неожиданное изменение поведения.
- Безопасный fix не гарантирует корректность: после него всё равно
  нужна функциональная проверка.
- Массовые unsafe-изменения в учебном проекте затрудняют анализ
  причинно-следственных связей.
- Чистый lint не доказывает отсутствие логических ошибок: дефект
  `range(1, max_attempts)` из ЛР №32 синтаксически корректен.

## Дополнительное задание: mypy

```bash
mypy app/integrations/notification_client.py
# app/config.py:70: error: Missing named argument "lab_db_password" ...
# app/config.py:70: error: Missing named argument "auth_secret" ...
# Found 2 errors in 1 file
```

Сообщения относятся к обязательным секретам pydantic-settings. Полная
типизация проекта не выполнялась: это отдельная задача, требующая
изменения существующего кода.

## Ответы на контрольные вопросы

1. Статический анализ — исследование исходного кода без выполнения
   программы.
2. Отладка требует запуска и наблюдения runtime-состояния; статический
   анализ работает с текстом и структурой кода.
3. Нет, `ruff check` не запускает приложение.
4. Linter — инструмент поиска нарушений правил и потенциальных
   проблем.
5. Formatter — инструмент приведения оформления к единому стандарту.
6. Linter сообщает о проблемах, formatter переписывает оформление.
7. PEP 8 — общий ориентир стиля Python-кода.
8. Проект может выбрать свою длину строки для единообразия и
   совместимости с инструментами.
9. `pyproject.toml` хранит конфигурацию инструментов проекта.
10. Ruff нужен только разработчику и не требуется приложению в
    контейнере.
11. `requirements-dev.txt` фиксирует инструменты разработки отдельно
    от runtime-зависимостей.
12. `ruff check` выполняет статический анализ и выводит нарушения.
13. F401 — импорт создан, но не используется.
14. F841 — локальная переменная присвоена, но не используется.
15. `ruff rule` показывает документацию правила по коду.
16. E711 — сравнение с `None` через `==` вместо `is`.
17. Группа I контролирует сортировку и оформление импортов.
18. F821 — использование неопределённого имени.
19. Да, Pyflakes обнаруживает такое имя без запуска.
20. Нет, Ruff не доказывает отсутствие логических ошибок.
21. Дефект границы `range` синтаксически корректен и не является
    нарушением выбранных правил.
22. `--statistics` показывает количество нарушений по кодам правил.
23. `--fix` применяет доступные автоматические исправления.
24. Unsafe-исправления могут изменить поведение, поэтому в основной
    работе не применяются.
25. Чтобы увидеть и проверить каждое изменение до коммита.
26. `ruff format --check` сообщает, требуется ли файлам форматирование,
    не изменяя их.
27. Нет, `--check` только проверяет.
28. `--diff` показывает предполагаемые изменения оформления.
29. `ruff format` применяет форматирование к файлам.
30. Formatter запускается после анализа, чтобы не смешивать
    семантические исправления с массовым изменением оформления.
31. Миграции генерируются Alembic; их массовое форматирование не
    требуется.
32. Quality gate — единая проверка, отвечающая, соответствует ли
    версия проекта принятым правилам.
33. Quality gate должен только проверять, а не неожиданно менять код.
34. `git diff --check` обнаруживает проблемы пробельных символов в
    изменениях.
35. Formatter и lint не проверяют работу приложения; smoke-проверка
    подтверждает сохранение поведения.
36. Регрессия — новый дефект в ранее работавшей функциональности.
37. Чистый lint не проверяет бизнес-логику, интеграции и runtime.
38. Type checker проверяет типы, formatter — оформление.
39. Журналы показывают runtime-симптом, debugger — состояние и стек,
    статический анализ — нарушения правил до запуска; вместе они
    дополняют друг друга.

## Git

```bash
git switch -c feature/static-code-quality
git add pyproject.toml requirements-dev.txt scripts app compose.yaml Dockerfile .gitignore
git diff --staged --stat
git diff --staged
git commit -m "Add static code quality checks"
git push -u origin feature/static-code-quality
```

`.venv/`, `.ruff_cache/`, `.mypy_cache/` исключены через `.gitignore`.

## Вывод

Ruff подключён как инструмент разработки и отделён от runtime-
зависимостей. Воспроизводимый пример показал правила F401, F841,
E711, I001; безопасный `--fix` устранил четыре нарушения, два
потребовали ручного решения. Реальный проект содержал один
неиспользуемый импорт, который удалён; formatter стандартизировал
24 файла без изменения логики. Quality gate проходит, `compileall`
успешен, приложение отвечает `200` на `/status`, `200` на `/docs` и
`201` на межсервисный запрос. Статический анализ дополняет, но не
заменяет отладку и функциональное тестирование.
