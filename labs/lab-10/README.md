# Лабораторная работа № 10. Работа с ветвями Git

## Цель

Освоить создание ветви, внесение изменения, коммит, слияние с `main` и
удаление ветви на примере задачи TASK-01.

## Что изменено

- поле `status` в `app/schemas/services.py` ограничено типом
  `Literal["running", "maintenance", "stopped"]`;
- TASK-01 в `PROJECT_TASKS.md` переведена в статус `DONE`;
- в README добавлен раздел «Состояния сервисов» (самостоятельное задание,
  ветвь `docs/status-description`).

## Состояния сервисов

- `running` — сервис работает;
- `maintenance` — сервис на обслуживании;
- `stopped` — сервис остановлен.

Недопустимое значение, например `unknown`, отклоняется с кодом
`422 Unprocessable Entity`.

## Порядок работы с ветвями

```bash
git switch main
git switch -c feature/status-validation
# изменение app/schemas/services.py
git add app/schemas/services.py PROJECT_TASKS.md
git commit -m "TASK-01 Restrict service status values"
git switch main
git merge --no-ff feature/status-validation
git branch -d feature/status-validation
```

Самостоятельное задание:

```bash
git switch -c docs/status-description
# раздел «Состояния сервисов» в README.md
git add README.md
git commit -m "Document service status values"
git switch main
git merge --no-ff docs/status-description
git branch -d docs/status-description
```

## Проверка

```bash
curl -i -X POST http://127.0.0.1:8000/services \
  -H "Content-Type: application/json" \
  -d '{"name":"Invalid","type":"application","status":"unknown"}'
```

Ожидается `422`; корректное значение `running` — `201`.

## Вывод

Ветвь изолирует изменение до проверки. После слияния история сохраняет
отдельный коммит задачи, а удаление ветви не удаляет её коммиты из `main`.
