# Локальные TLS-сертификаты

Файлы `*.pem` в этом каталоге исключены из Git: закрытый ключ нельзя
публиковать, а сертификат создаётся на каждой рабочей станции заново.

## Вариант 1. mkcert (рекомендуется в учебной среде)

```powershell
mkcert -install
mkcert -cert-file certs/localhost.pem -key-file certs/localhost-key.pem localhost 127.0.0.1 ::1
```

Сертификат будет доверенным для локальной системы, и `curl` сможет
проверить его без дополнительных параметров.

## Вариант 2. OpenSSL (если mkcert недоступен)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/localhost-key.pem \
  -out certs/localhost.pem \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:::1"
```

Такой сертификат самоподписанный. Браузер покажет предупреждение,
пока сертификат не добавлен в доверенное хранилище. Для проверки
через curl используйте сам сертификат как CA:

```bash
curl.exe -v --cacert certs/localhost.pem https://localhost:8443/status
```

## Файлы

| Файл | Назначение | В Git |
| --- | --- | --- |
| `localhost.pem` | серверный сертификат | нет |
| `localhost-key.pem` | закрытый ключ | нет |
| `README.md` | инструкция | да |
