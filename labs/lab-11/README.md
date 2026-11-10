# Лабораторная работа № 11. Организация коллективной разработки

## Цель

Освоить удалённый репозиторий, рабочую ветвь, Pull Request, получение
изменений и разрешение конфликтов на примере задачи TASK-02.

## Что изменено

- в `app/services/services.py` добавлена функция
  `get_services_by_status(status)`;
- `GET /services` принимает необязательный параметр `status`;
- параметр описан в OpenAPI (`Query(..., description=...)`);
- TASK-02, TASK-03 и TASK-05 отмечены как `DONE`;
- добавлен документ [docs/team-workflow.md](docs/team-workflow.md).

## Проверка фильтрации

```bash
curl http://127.0.0.1:8000/services
curl "http://127.0.0.1:8000/services?status=running"
curl "http://127.0.0.1:8000/services?status=maintenance"
curl -i "http://127.0.0.1:8000/services?status=unknown"
```

Первые два запроса возвращают полный список и отфильтрованный список.
Недопустимое значение отклоняется с кодом `422`, так как параметр описан типом
`ServiceStatus`.

## Git-процесс

```bash
git switch -c feature/service-status-filter
git add app PROJECT_TASKS.md
git commit -m "TASK-02 Add service status filtering"
git push -u origin feature/service-status-filter
```

Далее создаётся Pull Request, выполняется проверка и слияние в `main`.
Подробный порядок, включая разрешение конфликта в README, приведён в
`docs/team-workflow.md`.

## Вывод

Фильтрация реализована в сервисном слое, а маршрут только выбирает нужную
функцию. Такое разделение упрощает проверку и повторное использование логики.
