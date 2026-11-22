#!/usr/bin/env bash
# ЛР 39: сетевой доступ к Compose-приложению Cloud Application.
# Среда: Windows-host + Docker Desktop (Linux containers).
set -uo pipefail

LAB_DIR=$(cd "$(dirname "$0")/../.." && pwd -W 2>/dev/null || pwd)
REPO_ROOT=$(cd "$LAB_DIR/../.." && pwd -W 2>/dev/null || pwd)
EVIDENCE="$LAB_DIR/docs/lr39_evidence.txt"
PROJECT=cloudapp-lr39
IMAGE=cloud-application:0.7
PYTHON="$REPO_ROOT/.venv/Scripts/python.exe"
if [ ! -x "$PYTHON" ]; then
    PYTHON=python
fi

mkdir -p "$LAB_DIR/docs" "$LAB_DIR/secrets"
cd "$LAB_DIR" || exit 1
exec > >(tee "$EVIDENCE") 2>&1

dc() {
    MSYS_NO_PATHCONV=1 docker compose -p "$PROJECT" "$@"
}

dk() {
    MSYS_NO_PATHCONV=1 docker "$@"
}

run() {
    printf '\n$ %s\n' "$*"
    set +e
    "$@"
    local rc=$?
    set -e
    printf '[exit=%s]\n' "$rc"
    return 0
}

psrun() {
    printf '\n$ powershell: %s\n' "$1"
    set +e
    powershell -NoProfile -Command "$1"
    local rc=$?
    set -e
    printf '[exit=%s]\n' "$rc"
    return 0
}

section() {
    printf '\n\n========== %s ==========\n' "$*"
}

wait_http() {
    local url=$1 tries=${2:-60} code
    for _ in $(seq 1 "$tries"); do
        code=$(curl --noproxy '*' -s -o /dev/null -w '%{http_code}' "$url" 2>/dev/null || true)
        [ "$code" = "200" ] && return 0
        sleep 1
    done
    return 1
}

if ! docker info >/dev/null 2>&1; then
    echo "Docker daemon недоступен" >&2
    exit 1
fi

# --- Адрес сетевого интерфейса Windows (аналог Host-only IP) ---
if [ -z "${LAB_IP:-}" ]; then
    LAB_IP=$(powershell -NoProfile -Command \
        "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { \$_.IPAddress -like '192.168.*' } | Select-Object -First 1).IPAddress" \
        2>/dev/null | tr -d '\r')
fi
if [ -z "${LAB_IP:-}" ]; then
    LAB_IP=$(powershell -NoProfile -Command \
        "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { \$_.IPAddress -notmatch '^(127\.|169\.254\.|172\.(1[7-9]|2[0-9]|3[01])\.)' } | Select-Object -First 1).IPAddress" \
        2>/dev/null | tr -d '\r')
fi
if [ -z "${LAB_IP:-}" ]; then
    echo "Не удалось определить LAB_IP; задайте LAB_IP вручную" >&2
    exit 1
fi


section "1. Среда и сетевые интерфейсы"
run hostname
run dk version
psrun "Get-NetIPAddress -AddressFamily IPv4 | Where-Object { \$_.IPAddress -notlike '127.*' } | Select-Object InterfaceAlias,IPAddress,PrefixLength | Format-Table -AutoSize"
printf '\nLAB_IP (адрес сетевого интерфейса Windows): %s\n' "$LAB_IP"
run ipconfig
printf '\nХост и учебный сервис находятся в одной подсети; loopback 127.0.0.1 не используется как внешний адрес.\n'


section "2. Состояние Compose-системы до изменения bind"
run dk image inspect "$IMAGE" --format 'image={{.Id}}'
run dk stop cloud-application-lr37
run dc down -v --remove-orphans
run dk ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'

# Учебные секреты (содержимое не выводится). Существующие файлы
# сохраняются, чтобы пароль совпадал с уже инициализированным томом БД.
if [ ! -s secrets/auth_secret ]; then
    "$PYTHON" -c "import secrets,sys; sys.stdout.write(secrets.token_urlsafe(32))" > secrets/auth_secret
fi
if [ ! -s secrets/lab_db_password ]; then
    "$PYTHON" -c "import secrets,sys; sys.stdout.write(secrets.token_urlsafe(24))" > secrets/lab_db_password
fi
chmod 600 secrets/auth_secret secrets/lab_db_password 2>/dev/null || true
run wc -c secrets/auth_secret secrets/lab_db_password

# Исходная публикация — loopback.
printf 'APP_PUBLISH_IP=127.0.0.1\n' > .env
run cat .env
run dc config --quiet
run dc up -d
wait_http http://127.0.0.1:8080/status 90
run dc ps
run dc port app 8000
run dc port db 5432
run dc port notification 9000
psrun "Get-NetTCPConnection -State Listen -LocalPort 8080 -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort,OwningProcess | Format-Table -AutoSize"
run curl --noproxy '*' -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/status
run curl --noproxy '*' -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/docs


section "3. Исходная проверка TCP-доступа с клиентского адреса"
psrun "Test-NetConnection -ComputerName $LAB_IP -Port 8080 -InformationLevel Quiet"
run curl --noproxy '*' --max-time 5 -sS "http://$LAB_IP:8080/status"
printf '\nВывод: процесс и healthcheck работают локально, но loopback-публикация недоступна по сетевому адресу.\n'


section "4. Изменение публикации на сетевой интерфейс"
printf 'APP_PUBLISH_IP=%s\n' "$LAB_IP" > .env
run cat .env
run dc config --quiet
run dc up -d --force-recreate app
wait_http "http://$LAB_IP:8080/status" 90
run dc ps
run dc port app 8000
psrun "Get-NetTCPConnection -State Listen -LocalPort 8080 -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort,OwningProcess | Format-Table -AutoSize"
run curl --noproxy '*' --max-time 5 -s -o /dev/null -w 'local=127.0.0.1 status=%{http_code}\n' http://127.0.0.1:8080/status
run curl --noproxy '*' --max-time 5 -i "http://$LAB_IP:8080/status"
run curl --noproxy '*' --max-time 5 -s -o /dev/null -w '%{http_code}\n' "http://$LAB_IP:8080/docs"


section "5. Проверка с клиентского компьютера"
psrun "Test-NetConnection -ComputerName $LAB_IP -Port 8080"
psrun "curl.exe --noproxy \"*\" -i http://$LAB_IP:8080/status"
psrun "Invoke-WebRequest -UseBasicParsing -Uri http://$LAB_IP:8080/docs | Select-Object StatusCode | Format-Table -AutoSize"


section "6. Инфраструктурные порты не опубликованы"
run dk inspect cloudapp-lr39-db-1 --format '{{json .NetworkSettings.Ports}}'
run dk inspect cloudapp-lr39-notification-1 --format '{{json .NetworkSettings.Ports}}'
run dc port db 5432
run dc port notification 9000
run curl --noproxy '*' --max-time 5 -sS "http://$LAB_IP:9000/status"
run dc ps --format 'table {{.Service}}\t{{.Status}}\t{{.Ports}}'
# На host порт 5432 занят посторонним учебным контейнером ticket-postgres.
# Он не относится к cloudapp-lr39; на время проверки приостанавливаем его
# и сразу возвращаем в исходное состояние.
PG_WAS_RUNNING=$(dk inspect -f '{{.State.Running}}' ticket-postgres 2>/dev/null | tr -d '\r')
if [ "$PG_WAS_RUNNING" = "true" ]; then
    printf '\nПримечание: порт 5432 на host занят посторонним контейнером ticket-postgres.\n'
    run dk stop ticket-postgres
    # Docker Desktop освобождает слушающий сокет асинхронно.
    sleep 3
fi
psrun "Test-NetConnection -ComputerName $LAB_IP -Port 5432 -InformationLevel Quiet"
run curl --noproxy '*' --max-time 5 -sS "http://$LAB_IP:5432/"
if [ "$PG_WAS_RUNNING" = "true" ]; then
    run dk start ticket-postgres
    printf 'Посторонний контейнер ticket-postgres возвращён в running.\n'
fi


section "7. Внутренняя сеть Compose"
run dc exec -T app python -c "import socket; print('db', socket.gethostbyname('db')); print('notification', socket.gethostbyname('notification'))"
run dc exec -T app python -c "import socket; s=socket.create_connection(('db',5432),3); print('db:5432 reachable'); s.close()"
run dc exec -T app python -c "import httpx; print(httpx.get('http://notification:9000/status', timeout=5).json())"


section "8. Последовательная диагностика: уровни 1-6"
printf '\n--- Уровень 1. Клиент ---\n'
psrun "Test-NetConnection -ComputerName $LAB_IP -Port 8080 -InformationLevel Quiet"
printf '\n--- Уровень 2. Сетевой интерфейс ---\n'
psrun "Get-NetIPAddress -IPAddress $LAB_IP | Select-Object InterfaceAlias,IPAddress,PrefixLength | Format-Table -AutoSize"
run ipconfig
printf '\n--- Уровень 3. Прослушиваемый host-порт ---\n'
psrun "Get-NetTCPConnection -State Listen -LocalPort 8080 -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort,OwningProcess | Format-Table -AutoSize"
printf '\n--- Уровень 4. Docker port mapping ---\n'
run dc port app 8000
run dc ps app
printf '\n--- Уровень 5. Состояние контейнера и журнал ---\n'
run dc ps
run dc logs --tail 30 app
printf '\n--- Уровень 6. Приложение изнутри контейнера ---\n'
run dc exec -T app python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/status', timeout=3).read().decode())"


section "9. Контролируемый отказ: возврат bind на loopback"
printf 'APP_PUBLISH_IP=127.0.0.1\n' > .env
run dc up -d --force-recreate app
wait_http http://127.0.0.1:8080/status 90
run dc ps app
run dc port app 8000
run curl --noproxy '*' -s -o /dev/null -w 'local status=%{http_code}\n' http://127.0.0.1:8080/status
psrun "Test-NetConnection -ComputerName $LAB_IP -Port 8080 -InformationLevel Quiet"
run curl --noproxy '*' --max-time 5 -sS "http://$LAB_IP:8080/status"
printf '\nПричина отказа: host bind-address = 127.0.0.1; контейнер, healthcheck и FastAPI исправны.\n'


section "10. Восстановление рабочего bind и финальная проверка"
printf 'APP_PUBLISH_IP=%s\n' "$LAB_IP" > .env
run cat .env
run dc up -d --force-recreate app
wait_http "http://$LAB_IP:8080/status" 90
run dc ps
run dc port app 8000
psrun "Test-NetConnection -ComputerName $LAB_IP -Port 8080"
run curl --noproxy '*' -i "http://$LAB_IP:8080/status"
run curl --noproxy '*' -s -o /dev/null -w 'docs=%{http_code}\n' "http://$LAB_IP:8080/docs"
run dk inspect cloudapp-lr39-db-1 --format 'db ports={{json .NetworkSettings.Ports}}'
psrun "Test-NetConnection -ComputerName $LAB_IP -Port 9000 -InformationLevel Quiet"


section "11. Эксплуатационный сетевой паспорт"
printf 'hostname: %s\n' "$(hostname)"
printf 'Lab interface address: %s\n' "$LAB_IP"
printf 'Subnet mask: 255.255.255.0 (/24)\n'
printf 'NAT interface: Windows host + Docker Desktop (Linux VM)\n'
printf 'External network path: Windows client -> %s:8080 -> Docker published port -> app:8000\n' "$LAB_IP"
printf 'Compose project: %s\n' "$PROJECT"
printf 'app published: %s\n' "$(dc port app 8000 | tr -d '\r')"
printf 'db published: %s\n' "$(dk inspect cloudapp-lr39-db-1 --format '{{json .NetworkSettings.Ports}}' | tr -d '\r')"
printf 'notification published: %s\n' "$(dk inspect cloudapp-lr39-notification-1 --format '{{json .NetworkSettings.Ports}}' | tr -d '\r')"
printf 'app /status: %s\n' "$(curl --noproxy '*' -s -o /dev/null -w '%{http_code}' "http://$LAB_IP:8080/status")"
printf 'app /docs: %s\n' "$(curl --noproxy '*' -s -o /dev/null -w '%{http_code}' "http://$LAB_IP:8080/docs")"

printf '\nВсе шаги ЛР 39 выполнены. Стек оставлен запущенным для ЛР 40.\n'
