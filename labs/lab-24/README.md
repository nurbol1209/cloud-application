# Лабораторная работа № 24. Управление секретами приложения

## Цель

Отделить конфиденциальные параметры от исходного кода и обычной
конфигурации, загружать их через `pydantic-settings`, маскировать при
выводе и исключить из Git.

## Классификация параметров

| Параметр | Секрет | Где хранится |
| --- | :-: | --- |
| `APP_NAME`, `APP_PORT`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` | нет | `.env` |
| `LAB_DB_PASSWORD` | да | `secrets/lab_db_password` |
| `AUTH_SECRET` | да | `secrets/auth_secret` |
| `SSL_CERTFILE`, `SSL_KEYFILE` | нет (это пути) | `.env` |
| содержимое `localhost-key.pem` | да | `certs/`, вне Git |

## Структура

```
secrets/
├── README.md          (в Git)
├── lab_db_password    (вне Git)
└── auth_secret        (вне Git)
```

```bash
python scripts/init_secrets.py
# lab_db_password: generated
# auth_secret: generated
```

В файлах хранится только значение, без `KEY=`.

## Настройки

```python
lab_db_password: SecretStr
auth_secret: SecretStr

model_config = SettingsConfigDict(
    env_file=".env",
    secrets_dir="secrets",
    extra="ignore",
    ...
)

@property
def database_url(self) -> str:
    ...
```

Пароль БД больше не входит в `DATABASE_URL` в `.env`: URL собирается
внутри приложения из `DB_USER`, `LAB_DB_PASSWORD`, `DB_HOST`,
`DB_PORT`, `DB_NAME`. Значение секрета доступно только через
`get_secret_value()` в месте подключения.

Для локального режима без PostgreSQL используется
`DB_BACKEND=sqlite`; для целевого — `DB_BACKEND=postgresql`.

## Маскирование

```bash
python scripts/check_secret_config.py
# LAB_DB_PASSWORD: CONFIGURED
# AUTH_SECRET: CONFIGURED
# AUTH_SECRET: LENGTH OK
# TLS_PRIVATE_KEY: MISSING
```

`print(settings.lab_db_password)` выводит `**********`.
`settings.database_url` никогда не выводится в логи и REST-ответы.

## Отказ при отсутствии секрета

Если переименовать `secrets/auth_secret`, импорт настроек завершается
ошибкой `Field required`: приложение не запускается с неполной
конфигурацией безопасности. Слабые значения по умолчанию для секретов
не задаются.

## Git

```bash
git check-ignore -v secrets/lab_db_password
git ls-files .env
git ls-files secrets
git log --all -- .env
```

Секреты и `.env` не отслеживаются. Если секрет когда-либо попал
в репозиторий, его нужно заменить, а не просто удалить файл.

## Проверка после изменения конфигурации

```bash
python scripts/init_db.py
python scripts/init_access.py
python run.py
```

| Проверка | Результат |
| --- | --- |
| регистрация / вход | работает, хеш не возвращается |
| `GET /auth/me` | данные пользователя |
| viewer `GET /services` | `200` |
| viewer `POST /services` | `403` |
| неверный токен | `401` |
| HTTPS (при наличии сертификатов) | работает без изменений |

## Ротация AUTH_SECRET

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Новое значение записывается в `secrets/auth_secret`, приложение
перезапускается. Исходный код не меняется; существующие `AuthSession`
не затрагиваются, так как `AUTH_SECRET` не используется для их подписи.

## Аудит (самостоятельное задание)

| Объект | Содержит секрет | Должен быть в Git | Результат |
| --- | :-: | :-: | --- |
| `app/config.py` | нет | да | только `SecretStr`-поля |
| `.env` | возможно | нет | игнорируется |
| `.env.example` | нет | да | безопасный шаблон |
| `secrets/lab_db_password` | да | нет | игнорируется |
| `secrets/auth_secret` | да | нет | игнорируется |
| `certs/localhost.pem` | нет | нет | игнорируется |
| `certs/localhost-key.pem` | да | нет | игнорируется |
| `requirements.txt` | нет | да | проверено |

## Вывод

Секреты отделены от кода и обычной конфигурации, маскируются при
выводе и загружаются из внешнего источника. Управление секретами
дополняет, но не заменяет TLS, хеширование паролей и авторизацию.
