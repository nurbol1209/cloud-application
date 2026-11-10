# Лабораторная работа № 23. Защищённое сетевое взаимодействие (HTTPS)

## Цель

Настроить HTTPS для Cloud Application, защитить передачу паролей и
Bearer-токенов и убедиться, что аутентификация и авторизация работают
поверх TLS.

## Уровни защиты

| Что защищается | Механизм |
| --- | --- |
| Пароль в базе | Argon2-хеш (ЛР №22) |
| Пароль и токен в сети | HTTPS / TLS (эта работа) |
| Пользователь | Аутентификация + `AuthSession` |
| Действия пользователя | Role + Permission (ЛР №20–21) |

`HTTPS = HTTP + TLS`; REST-маршруты при этом не меняются.

## Сертификат

Файлы создаются локально и исключены из Git (`certs/*.pem`).

### mkcert

```powershell
mkcert -install
mkcert -cert-file certs/localhost.pem -key-file certs/localhost-key.pem localhost 127.0.0.1 ::1
```

### OpenSSL (если mkcert недоступен)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/localhost-key.pem \
  -out certs/localhost.pem \
  -subj "//CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:0:0:0:0:0:0:0:1"
```

Самоподписанный сертификат проверяется так:

```bash
curl.exe -v --cacert certs/localhost.pem https://localhost:8443/status
```

## Конфигурация

`.env` / `.env.example`:

```
HTTPS_ENABLED=true
HTTPS_PORT=8443
SSL_CERTFILE=certs/localhost.pem
SSL_KEYFILE=certs/localhost-key.pem
```

`app/config.py`:

```python
https_enabled: bool = False
https_port: int = 8443
ssl_certfile: str | None = None
ssl_keyfile: str | None = None
```

`run.py` при `HTTPS_ENABLED=true` передаёт Uvicorn `ssl_certfile` и
`ssl_keyfile`, а также использует порт 8443. При `false` приложение
запускается по HTTP на порту 8000.

## Запуск и проверка

```bash
python scripts/init_db.py
python scripts/init_access.py
python run.py
```

- `https://localhost:8443/docs` — Swagger через HTTPS;
- `https://127.0.0.1:8443/docs` — имя из SAN сертификата;
- `https://<hostname>:8443` — ошибка, если имя не добавлено в сертификат;
- `http://localhost:8443` — TLS-порт не отвечает на обычный HTTP;
- отсутствие `localhost.pem` → `RuntimeError: Certificate not found`.

Дополнительное задание: `GET /connection` возвращает
`{"scheme": "https", "host": "localhost", "secure": true}`.

## Сравнение HTTP и HTTPS

| Характеристика | HTTP | HTTPS |
| --- | --- | --- |
| Схема URL | `http://` | `https://` |
| Учебный порт | 8000 | 8443 |
| Сертификат | нет | да |
| Закрытый ключ | нет | да |
| TLS | нет | да |
| REST-маршруты | не меняются | не меняются |

## Проверка доступа через HTTPS

```bash
curl.exe -s --cacert certs/localhost.pem \
  -X POST https://localhost:8443/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"tls_user","password":"CloudTLS123"}'
```

| Проверка | Результат |
| --- | --- |
| `https://localhost:8443/docs` | открывается |
| `https://127.0.0.1:8443/docs` | открывается |
| `curl.exe -v --cacert ...` | TLS + `200 OK` |
| вход через HTTPS | `200`, токен |
| `GET /auth/me` с токеном | данные пользователя |
| viewer `GET /services` | `200` |
| viewer `POST /services` | `403` |
| неверный токен | `401` |
| имя узла вне сертификата | ошибка TLS |
| без сертификата | сервер не запускается |

## Самостоятельное задание

| Проверка | Результат |
| --- | --- |
| HTTPS включён | да |
| Swagger по HTTPS | да |
| Вход существующего пользователя | да |
| Bearer-токен работает | да |
| Ролевая авторизация работает | да |
| Неверный токен → 401 | да |
| Запрещённая операция → 403 | да |
| `localhost` и `127.0.0.1` в сертификате | да |
| Запуск без сертификата | ошибка |

## Вывод

TLS защищает канал, но не отменяет хеширование паролей, проверку сеанса
и проверку разрешений: каждый уровень решает свою задачу.
