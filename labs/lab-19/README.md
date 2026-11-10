# Лабораторная работа № 19. Регистрация и аутентификация

## Цель

Реализовать регистрацию пользователя, проверку учётных данных,
создание сеанса с уникальным токеном, проверку и завершение сеанса.

## Понятия

| Процесс | Что делает |
| --- | --- |
| Регистрация | создаёт новую учётную запись `User` |
| Аутентификация | проверяет `username` + `password` |
| Авторизация | определяет права (ЛР №20–21, здесь отсутствует) |

> Пароль в этой работе хранится в открытом виде — это учебное
> ограничение. Безопасное хеширование выполняется в ЛР №22.

## Структура данных

```
users
  id, username (UNIQUE), password, created_at

auth_sessions
  id, token (UNIQUE), user_id -> users.id, created_at

User 1 ────── N AuthSession
```

Модели: `app/data/models.py`, миграция `0007_add_users_and_auth_sessions`.

## Схемы

`app/schemas/auth.py`:

- `UserRegister` — `username` 3…50 (trim + lower), `password` 6…100;
- `LoginRequest` — `username`, `password`;
- `UserResponse` — без поля `password`;
- `LoginResponse` — `access_token`, `token_type = "session"`;
- `SessionResponse` — `authenticated`, `user_id`, `username`.

## Сервисы

`app/services/auth.py`:

- `get_user_by_username`;
- `register_user` — `None`, если имя уже занято;
- `authenticate_user` — создаёт `AuthSession` с `uuid4().hex`;
- `get_auth_session`;
- `logout_user` — удаляет сеанс;
- `logout_all_sessions` — дополнительное задание.

## Маршруты

| Метод | Адрес | Результат |
| --- | --- | --- |
| POST | `/auth/register` | `201` / `409` |
| POST | `/auth/login` | `200` + токен / `401` |
| GET | `/auth/session/{token}` | `200` / `401` |
| DELETE | `/auth/session/{token}` | `200` / `401` |
| DELETE | `/auth/user/{user_id}/sessions` | закрывает все сеансы (доп.) |

## Проверка

```bash
python scripts/init_db.py
python run.py
```

```bash
curl -i -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"student01","password":"cloud12345"}'

curl -i -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"student01","password":"cloud12345"}'
```

Ожидаемые сценарии:

| Сценарий | Код |
| --- | --- |
| новая регистрация | `201` |
| повторный `username` | `409` |
| имя с пробелами | сохраняется в нижнем регистре без пробелов |
| верные учётные данные | `200`, уникальный токен |
| неверный пароль | `401` |
| неизвестный пользователь | `401` (то же сообщение) |
| неверный токен | `401` |
| выход | `200`, запись `auth_sessions` удалена |

Сеанс хранится в БД, поэтому токен остаётся действительным после
перезапуска приложения.

## Самостоятельное задание

| Пользователь | Регистрация | Вход | Токен создан | Сеанс проверен |
| --- | --- | --- | --- | --- |
| `student01` | да | да | да | да |
| `student02` | да | да | да | да |
| `student03` | да | да | да | да |

Токены трёх пользователей различаются. Один пользователь может иметь
несколько сеансов; удаление одного токена не затрагивает остальные.

## Вывод

Аутентификация устанавливает, *кто* выполняет запрос. Сами ресурсы
`/services` и `/objects` пока открыты: наличие сеанса ещё не означает
права доступа — это задача ролевой модели и программной авторизации.
