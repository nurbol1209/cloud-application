# Лабораторная работа № 21. Программная авторизация

## Цель

Подключить ролевую модель к обработке HTTP-запросов: определять
пользователя по Bearer-токену и проверять разрешение перед выполнением
операции.

## Аутентификация и авторизация

```
Authorization: Bearer <token>
        ↓
   AuthSession → User          (аутентификация; нет токена → 401)
        ↓
   Role → permissions          (авторизация; нет права → 403)
        ↓
   endpoint разрешён / запрещён
```

- `401 Unauthorized` — токен отсутствует или недействителен;
- `403 Forbidden` — пользователь определён, но разрешения не хватает.

## Модуль безопасности

`app/security.py`:

- `bearer_scheme = HTTPBearer(auto_error=False)`;
- `get_current_user` — проверяет схему `Bearer`, находит `AuthSession`
  и возвращает related `User`;
- `require_permission(code)` — фабрика зависимостей, проверяет код
  разрешения текущей роли;
- `require_any_permission(*codes)` — дополнительное задание: достаточно
  любого из перечисленных разрешений.

Пользователь определяется только по токену. Переданный клиентом
`user_id` не используется для идентификации.

## Матрица защиты

| Операция | Разрешение |
| --- | --- |
| `GET /services`, `GET /services/{id}` | `services.read` |
| `POST/PUT/DELETE /services` | `services.write` |
| `GET /objects`, `/objects/{id}`, `/download` | `objects.read` |
| `POST/DELETE /objects` | `objects.write` |
| `GET /access/roles`, `PUT /access/users/{id}/role` | `roles.manage` |
| `GET /access/users/{id}` | `users.manage` |
| `GET /access/summary` | `users.manage` **или** `roles.manage` |
| `GET /auth/me` | только аутентификация |
| `POST /auth/register`, `POST /auth/login` | без токена |

## Проверка

```bash
python scripts/init_db.py
python scripts/init_access.py
python run.py
```

Подготовка пользователей (роли назначаются администратором либо
скриптом из ЛР №20):

| Пользователь | Роль | Токен |
| --- | --- | --- |
| `student01` | viewer | свой |
| `student02` | operator | свой |
| `student03` | administrator | свой |

Результаты:

| Операция | viewer | operator | administrator |
| --- | :-: | :-: | :-: |
| GET services | 200 | 200 | 200 |
| POST services | 403 | 201 | 201 |
| PUT services | 403 | 200 | 200 |
| DELETE services | 403 | 200 | 200 |
| GET objects | 200 | 200 | 200 |
| POST objects | 403 | 201 | 201 |
| DELETE objects | 403 | 200 | 200 |
| GET access/roles | 403 | 403 | 200 |
| GET access/users/{id} | 403 | 403 | 200 |
| PUT user role | 403 | 403 | 200 |

Дополнительно:

- запрос без токена или с неверным токеном → `401`;
- после `DELETE /auth/session/{token}` тот же токен → `401`;
- после смены роли `viewer → operator` прежний токен сразу получает
  `services.write`: роль читается из БД при каждом запросе.

## Самостоятельное задание

| Пользователь | Роль | Запрос | Permission | Результат |
| --- | --- | --- | --- | --- |
| student01 | viewer | `GET /services` | `services.read` | 200 |
| student01 | viewer | `POST /services` | `services.write` | 403 |
| student02 | operator | `POST /services` | `services.write` | 201 |
| student02 | operator | `GET /access/roles` | `roles.manage` | 403 |
| student03 | administrator | `GET /access/users/1` | `users.manage` | 200 |

`content_manager` может `GET /services`, `GET /objects`, `POST /objects`,
но не `POST /services` и не менять роли — без изменения кода endpoint.

## Вывод

Единый механизм `require_permission` централизует авторизацию:
endpoint требует permission, а роль определяет, есть ли оно.
Новые роли начинают работать без правок защищённых маршрутов.
