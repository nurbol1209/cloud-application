# Файлы секретов для Compose-стека

Каталог содержит только runtime-секреты и не попадает в Git
(`.gitignore`: `secrets/*`, кроме этого README).

Создать учебные секреты:

```bash
python -c "import secrets,sys; sys.stdout.write(secrets.token_urlsafe(32))" > secrets/auth_secret
python -c "import secrets,sys; sys.stdout.write(secrets.token_urlsafe(24))" > secrets/lab_db_password
```

`lab_db_password` используется одновременно как пароль PostgreSQL и как
секрет приложения, поэтому значения должны совпадать. Содержимое файлов
не выводится в журналы и отчёты.
