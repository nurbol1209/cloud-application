#!/usr/bin/env bash
# Выполняется внутри Ubuntu 24.04 с systemd (Docker container).
# Шаги ЛР 36: неконтейнерное развертывание Cloud Application.

set -u

export LC_ALL=C
export SYSTEMD_PAGER=cat
export DEBIAN_FRONTEND=noninteractive

run() {
    printf '\n$ %s\n' "$*"
    bash -c "$*"
    printf '[exit=%s]\n' "$?"
}

section() {
    printf '\n\n========== %s ==========\n' "$*"
}

APP_ROOT=/opt/cloud-application
APP_DIR=$APP_ROOT/app
VENV=$APP_ROOT/venv
CONF_DIR=/etc/cloud-application
ENV_FILE=$CONF_DIR/cloud-application.env
SECRETS=$CONF_DIR/secrets
UNIT=/etc/systemd/system/cloud-application.service
SERVICE=cloud-application.service
BUNDLE=/tmp/cloud-application.bundle


section "1. Целевая среда"
run 'cat /etc/os-release'
run 'ps -p 1 -o comm='
run 'hostnamectl'
run 'python3 --version'
run 'command -v git || echo "git: not installed yet"'
run 'command -v curl || echo "curl: not installed yet"'


section "2. Установка системных пакетов"
run 'apt-get update -qq'
run 'apt-get install -y -qq git python3 python3-venv python3-pip curl iproute2 sudo > /tmp/lr36_apt.log 2>&1'
printf '\nФрагмент журнала apt:\n'
tail -5 /tmp/lr36_apt.log
run 'python3 --version'
run 'git --version'
run 'which curl ss'


section "3. Системный пользователь cloudapp"
run 'useradd --system --user-group --home-dir /opt/cloud-application --shell /usr/sbin/nologin cloudapp'
run 'id cloudapp'
run 'getent passwd cloudapp'


section "4. Структура каталогов deployment"
run 'install -d -o cloudapp -g cloudapp -m 0755 /opt/cloud-application'
run 'install -d -o root -g cloudapp -m 0750 /etc/cloud-application'
run 'ls -ld /opt/cloud-application /etc/cloud-application'


section "5. Получение приложения из Git"
run 'ls -l /tmp/cloud-application.bundle'
run 'git clone /tmp/cloud-application.bundle /opt/cloud-application/app'
run 'chown -R cloudapp:cloudapp /opt/cloud-application/app'
run 'sudo -u cloudapp git -C /opt/cloud-application/app status --short'
COMMIT=$(sudo -u cloudapp git -C "$APP_DIR" rev-parse HEAD)
SHORT_COMMIT=$(sudo -u cloudapp git -C "$APP_DIR" rev-parse --short HEAD)
printf '\nПолный commit hash: %s\nКороткий commit hash: %s\n' "$COMMIT" "$SHORT_COMMIT"
run 'sudo -u cloudapp git -C /opt/cloud-application/app log -1 --oneline'
run 'ls -la /opt/cloud-application/app'


section "6. Python virtual environment и зависимости"
run 'sudo -u cloudapp python3 -m venv /opt/cloud-application/venv'
run '/opt/cloud-application/venv/bin/python --version'
printf '\nУстановка runtime-зависимостей (фрагмент вывода):\n'
sudo -u cloudapp "$VENV/bin/python" -m pip install --no-cache-dir -r "$APP_DIR/requirements.txt" > /tmp/lr36_pip.log 2>&1
printf '[exit=%s]\n' "$?"
tail -12 /tmp/lr36_pip.log
run 'sudo -u cloudapp /opt/cloud-application/venv/bin/python -m pip check'
run 'sudo -u cloudapp /opt/cloud-application/venv/bin/python -c "import fastapi, uvicorn, sqlalchemy, httpx; print(\"IMPORTS_OK\")"'


section "7. Эксплуатационная конфигурация"
run "install -m 0640 -o root -g cloudapp /work/deploy/etc/cloud-application.env $ENV_FILE"
run "ls -l $ENV_FILE"
run "grep -v -E 'PASSWORD|SECRET|TOKEN' $ENV_FILE"


section "8. Секреты вне Git"
run "install -d -o root -g cloudapp -m 0750 $SECRETS"
run "python3 -c 'import secrets; print(secrets.token_urlsafe(32))' > $SECRETS/auth_secret"
run "python3 -c 'import secrets; print(secrets.token_urlsafe(24))' > $SECRETS/lab_db_password"
run "chown root:cloudapp $SECRETS/auth_secret $SECRETS/lab_db_password"
run "chmod 0640 $SECRETS/auth_secret $SECRETS/lab_db_password"
run "ls -l $SECRETS"
run "sudo -u cloudapp test -r $SECRETS/auth_secret && echo AUTH_SECRET_READABLE"
run "sudo -u cloudapp test -r $SECRETS/lab_db_password && echo DB_SECRET_READABLE"
run "ln -s $SECRETS $APP_DIR/secrets"
run "ls -l $APP_DIR/secrets"
run "install -d -o cloudapp -g cloudapp -m 0750 $APP_DIR/storage/objects"
run "ls -ld $APP_DIR/storage/objects"
run "sudo -u cloudapp test -r $APP_DIR/secrets/auth_secret && echo SECRET_VIA_SYMLINK_OK"


section "9. systemd unit Cloud Application"
run "install -m 0644 /work/deploy/systemd/cloud-application.service $UNIT"
run "systemctl cat $SERVICE"
run "systemd-analyze verify $UNIT"
run 'systemctl daemon-reload'
run "systemctl enable --now $SERVICE"
run "systemctl is-enabled $SERVICE"
run "systemctl is-active $SERVICE"
sleep 3
run "systemctl status $SERVICE --no-pager"
run "systemctl show $SERVICE -p ActiveState -p SubState -p MainPID -p ExecMainStatus -p Restart -p UnitFileState"
PID=$(systemctl show $SERVICE -p MainPID --value)
printf '\nMainPID: %s\n' "$PID"
run "ps -fp $PID"
run "journalctl -u $SERVICE -n 40 --no-pager"


section "10. Smoke-test развернутого приложения"
run "ss -ltnp | grep ':8000'"
run 'curl -i http://127.0.0.1:8000/status'
run 'curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/docs'
run 'curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/openapi.json'


section "11. Контролируемая ошибка конфигурации и rollback"
run "cp $ENV_FILE $ENV_FILE.bak"
run "ls -l $ENV_FILE*"
run "sed -i 's/^APP_PORT=8000\$/APP_PORT=not-a-number/' $ENV_FILE"
run "grep '^APP_PORT=' $ENV_FILE"
run "systemctl restart $SERVICE"
sleep 5
run "systemctl status $SERVICE --no-pager"
run "journalctl -u $SERVICE -n 50 --no-pager"
run "systemctl stop $SERVICE"
run "cp $ENV_FILE.bak $ENV_FILE"
run "grep '^APP_PORT=' $ENV_FILE"
run "systemctl start $SERVICE"
sleep 3
run "systemctl is-active $SERVICE"
run 'curl -i http://127.0.0.1:8000/status'
run "rm $ENV_FILE.bak"


section "12. Самостоятельная проверка перезапуска"
PID_BEFORE=$(systemctl show $SERVICE -p MainPID --value)
run "systemctl restart $SERVICE"
sleep 3
PID_AFTER=$(systemctl show $SERVICE -p MainPID --value)
printf '\nPID до restart: %s\nPID после restart: %s\n' "$PID_BEFORE" "$PID_AFTER"
run "systemctl is-active $SERVICE"
run 'curl -s http://127.0.0.1:8000/status'


section "13. Итоговый паспорт работающей среды"
printf 'hostname: %s\n' "$(hostname)"
printf 'ОС: %s\n' "$(grep PRETTY_NAME /etc/os-release | cut -d= -f2- | tr -d '"')"
printf 'Python venv: %s\n' "$($VENV/bin/python --version)"
printf 'commit hash: %s\n' "$COMMIT"
printf 'пользователь процесса: %s\n' "$(ps -o user= -p "$(systemctl show $SERVICE -p MainPID --value)" | tr -d ' ')"
printf 'systemd unit: %s\n' "$SERVICE"
printf 'ActiveState: %s\n' "$(systemctl show $SERVICE -p ActiveState --value)"
printf 'Unit enabled: %s\n' "$(systemctl show $SERVICE -p UnitFileState --value)"
printf 'MainPID: %s\n' "$(systemctl show $SERVICE -p MainPID --value)"
printf 'bind address: %s\n' "$(grep '^APP_HOST=' $ENV_FILE | cut -d= -f2)"
printf 'port: %s\n' "$(grep '^APP_PORT=' $ENV_FILE | cut -d= -f2)"
printf '/status: %s\n' "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/status)"
printf '/docs: %s\n' "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/docs)"
printf 'место конфигурации: %s\n' "$ENV_FILE"
printf 'место секретов: %s (symlink: %s)\n' "$SECRETS" "$APP_DIR/secrets"
printf 'место журналов: systemd journal\n'

printf '\nВсе шаги ЛР 36 выполнены.\n'
