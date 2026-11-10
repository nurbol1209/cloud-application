# Лабораторная работа № 20. Ролевая модель доступа

## Цель

Реализовать хранение ролей и разрешений, связь роль ↔ разрешение,
назначение роли пользователю и получение эффективного набора
разрешений.

> На этом этапе роль только **хранится**, но не проверяется при
> обработке запросов. Программная авторизация — ЛР №21.

## Модель

```
User N ────── 1 Role M ────── N Permission
                    │
                    └── role_permissions (role_id, permission_id)
```

## Матрица доступа

| Разрешение | viewer | operator | administrator | content_manager |
| --- | :-: | :-: | :-: | :-: |
| `services.read` | ✓ | ✓ | ✓ | ✓ |
| `services.write` |  | ✓ | ✓ |  |
| `objects.read` | ✓ | ✓ | ✓ | ✓ |
| `objects.write` |  | ✓ | ✓ | ✓ |
| `users.manage` |  |  | ✓ |  |
| `roles.manage` |  |  | ✓ |  |

`content_manager` — дополнительное задание: добавляется как данные
через `ROLE_MODEL`, миграция не требуется.

## Что изменено

- `app/data/models.py` — `role_permissions`, `Permission`, `Role`,
  `User.role_id` / `User.role`;
- миграция `0008_add_role_access_model`;
- `app/services/access.py` — `PERMISSIONS`, `ROLE_MODEL`,
  `initialize_access_model`, `assign_default_roles`, `get_roles`,
  `get_role_by_name`, `assign_role`, `get_user_access`;
- `app/schemas/access.py`;
- `app/routers/access.py`;
- `app/services/auth.py` — новый пользователь получает `viewer`;
- `scripts/init_access.py` — идемпотентная инициализация.

## Инициализация

```bash
python scripts/init_db.py
python scripts/init_access.py
# Access model initialized
```

Скрипт можно запускать повторно: дубли ролей и разрешений не
создаются. Существующие пользователи без роли получают `viewer`.

## Маршруты

| Метод | Адрес | Назначение |
| --- | --- | --- |
| GET | `/access/roles` | роли и их разрешения |
| GET | `/access/users/{user_id}` | роль и разрешения пользователя |
| PUT | `/access/users/{user_id}/role` | назначить роль |

## Проверка

```bash
curl http://127.0.0.1:8000/access/roles

curl -X PUT http://127.0.0.1:8000/access/users/1/role \
  -H "Content-Type: application/json" \
  -d '{"role_name":"operator"}'

curl http://127.0.0.1:8000/access/users/1
```

Ожидаемые результаты:

| Сценарий | Результат |
| --- | --- |
| `GET /access/roles` | viewer (2), operator (4), administrator (6), content_manager (3) |
| роль `operator` | 4 разрешения |
| роль `administrator` | все 6 разрешений |
| роль `superuser` | `404 Role not found` |
| новый пользователь | автоматически `viewer` |
| вход после смены роли | работает, сеансы не затрагиваются |

## Самостоятельное задание

| Пользователь | Роль | Количество разрешений | Вход выполнен |
| --- | --- | --- | --- |
| `student01` | viewer | 2 | да |
| `student02` | operator | 4 | да |
| `student03` | administrator | 6 | да |

Эксперимент: пользователь `viewer` не имеет `services.write`, но
`POST /services` всё ещё выполняется — маршрут пока не проверяет
разрешение. Это ожидаемо до ЛР №21.

## Вывод

Модель данных готова к авторизации: приложение знает пользователя,
его роль и её разрешения. Остаётся подключить проверку разрешений
к обработке HTTP-запросов.
