# Лабораторная работа № 22. Безопасное хранение паролей

## Цель

Заменить хранение паролей в открытом виде на Argon2-хеши, сохранив
работоспособность аутентификации, сеансов, ролей и авторизации.

## Хранение пароля

```
До:    password       = cloud12345
После: password_hash  = $argon2id$v=19$...
```

Хеширование необратимо и использует случайную соль, поэтому одинаковые
пароли разных пользователей дают разные хеши. При входе пароль
проверяется через `verify_password`, а не сравнением строк.

## Структура

```
app/security/
├── __init__.py
├── authorization.py   (перенесено из app/security.py в ЛР №21)
└── passwords.py       (новое)
```

`app/security/passwords.py`:

```python
password_manager = PasswordHash.recommended()

def hash_password(password: str) -> str: ...
def verify_password(plain_password: str, password_hash: str) -> bool: ...
```

Библиотека: `pwdlib[argon2]`.

## Изменения

- `User.password` → `User.password_hash`;
- миграция `0009_rename_password_to_password_hash` —
  `op.alter_column(..., new_column_name=...)`, данные сохраняются;
- `register_user` сохраняет только хеш;
- `authenticate_user` проверяет `verify_password`;
- `scripts/hash_existing_passwords.py` — преобразование старых значений,
  повторный запуск безопасен (`Passwords converted: 0`);
- `scripts/check_password_storage.py` — выводит `HASHED` / `LEGACY`
  без пароля и хеша;
- схема API не изменилась: клиент по-прежнему передаёт `password`.

## Порядок выполнения

```bash
python scripts/init_db.py
python -m alembic upgrade head
python scripts/hash_existing_passwords.py
python run.py
```

Проверка:

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"secure01","password":"cloud12345"}'

curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"secure01","password":"cloud12345"}'
```

| Сценарий | Результат |
| --- | --- |
| регистрация | `201`, в ответе нет `password` и `password_hash` |
| `password_hash` в БД | начинается с `$argon2id$` |
| одинаковый пароль двух пользователей | хеши различаются |
| верный пароль | `200` + токен |
| неверный пароль | `401 Invalid username or password` |
| старый учебный пользователь | вход работает после конвертации |
| viewer / operator / administrator | доступ по-прежнему 200 / 403 по матрице |
| после `DELETE /auth/session/{token}` | `401` |

## Самостоятельное задание

| Проверка | security_test01 | security_test02 |
| --- | :-: | :-: |
| Регистрация выполнена | да | да |
| Исходного пароля нет в БД | да | да |
| Хеш создан | да | да |
| Хеши отличаются | да | да |
| Правильный пароль принимается | да | да |
| Неправильный пароль отклоняется | да | да |
| Токен создаётся | да | да |
| Авторизация продолжает работать | да | да |

## Вывод

Пароль хранится только в виде Argon2-хеша; API и схема запросов
не изменились. Хеширование защищает базу при утечке, но не заменяет
HTTPS — защита канала рассматривается в ЛР №23.
