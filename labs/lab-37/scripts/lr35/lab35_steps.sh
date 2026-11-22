#!/usr/bin/env bash
# Выполняется внутри Ubuntu 24.04 с systemd (Docker container).
# Все шаги ЛР 35 фиксируются в /work/docs/lr35_evidence.txt.

set -u

export LC_ALL=C
export SYSTEMD_PAGER=cat

run() {
    printf '\n$ %s\n' "$*"
    bash -c "$*"
    printf '[exit=%s]\n' "$?"
}

section() {
    printf '\n\n========== %s ==========\n' "$*"
}

FAIL_FLAG=/opt/cloud-lab/fail.flag
UNIT=/etc/systemd/system/cloud-lab-worker.service
SERVICE=cloud-lab-worker.service


section "1. Сведения о серверной среде"
run 'whoami'
run 'id'
run 'cat /etc/os-release'
run 'hostnamectl'
run 'ps -p 1 -o comm='
run 'systemctl --version'
run 'systemd-analyze --version'
run 'systemctl is-system-running'
run 'systemctl list-units --type=service --state=running --no-pager'
run 'systemctl --failed --no-pager'
FAILED_BEFORE=$(systemctl --failed --no-legend --no-pager | wc -l | tr -d ' ')
printf '\nКоличество failed units до эксперимента: %s\n' "$FAILED_BEFORE"


section "2. Создание каталога и учебного процесса"
run 'install -d -m 0755 /opt/cloud-lab'
run 'ls -ld /opt/cloud-lab'
run 'install -m 0644 /work/deploy/systemd/service_worker.py /opt/cloud-lab/service_worker.py'
run 'ls -l /opt/cloud-lab/service_worker.py'
run 'cat /opt/cloud-lab/service_worker.py'


section "3. Создание и проверка unit-файла"
run "install -m 0644 /work/deploy/systemd/cloud-lab-worker.service $UNIT"
run "systemctl cat $SERVICE"
run "systemd-analyze verify $UNIT"
run 'systemctl daemon-reload'


section "4. Состояние до первого запуска"
run "systemctl status $SERVICE --no-pager"
run "systemctl is-active $SERVICE"
run "systemctl is-enabled $SERVICE"


section "5. Запуск службы и проверка active (running)"
run "systemctl start $SERVICE"
run "systemctl is-active $SERVICE"
run "systemctl status $SERVICE --no-pager"
run "systemctl show $SERVICE -p ActiveState -p SubState -p MainPID -p ExecMainStatus -p UnitFileState"
run "systemctl show $SERVICE -p MainPID --value"
PID_START=$(systemctl show $SERVICE -p MainPID --value)
printf '\nMainPID после первого запуска: %s\n' "$PID_START"
run "ps -fp $PID_START"


section "6. Остановка и повторный запуск"
run "systemctl stop $SERVICE"
run "systemctl is-active $SERVICE"
run "systemctl status $SERVICE --no-pager"
run "systemctl start $SERVICE"
PID_SECOND=$(systemctl show $SERVICE -p MainPID --value)
printf '\nMainPID после повторного запуска: %s\n' "$PID_SECOND"


section "7. Перезапуск и сравнение PID"
PID_BEFORE=$(systemctl show $SERVICE -p MainPID --value)
run "systemctl restart $SERVICE"
PID_AFTER=$(systemctl show $SERVICE -p MainPID --value)
printf '\nPID до restart: %s\nPID после restart: %s\n' "$PID_BEFORE" "$PID_AFTER"
run "systemctl is-active $SERVICE"


section "8. Различие active и enabled: enable без start"
run "systemctl stop $SERVICE"
run "systemctl is-active $SERVICE"
run "systemctl enable $SERVICE"
run "systemctl is-enabled $SERVICE"
run "systemctl is-active $SERVICE"
run "systemctl start $SERVICE"
run "systemctl is-active $SERVICE"
run "systemctl is-enabled $SERVICE"


section "9. Различие stop и disable: disable без stop"
run "systemctl disable $SERVICE"
run "systemctl is-enabled $SERVICE"
run "systemctl is-active $SERVICE"
run "systemctl enable $SERVICE"
run "systemctl is-enabled $SERVICE"


section "10. Журнал journalctl"
run "journalctl -u $SERVICE -n 20 --no-pager"
run "journalctl -u $SERVICE -b --no-pager | tail -25"
run "journalctl -u $SERVICE --since '5 minutes ago' --no-pager | tail -25"
printf '\nКоманда: journalctl -f -u %s (наблюдение 12 секунд)\n' "$SERVICE"
timeout 12s journalctl -f -u "$SERVICE" --no-pager
printf '\n[exit=%s] (124 — завершение по timeout, это ожидаемо)\n' "$?"
run "systemctl is-active $SERVICE"


section "11. Контролируемый отказ"
run "touch $FAIL_FLAG"
run "ls -l $FAIL_FLAG"
run "systemctl restart $SERVICE"
sleep 2
run "systemctl is-active $SERVICE"
run "systemctl is-failed $SERVICE"
run "systemctl status $SERVICE --no-pager"
run "systemctl show $SERVICE -p ActiveState -p SubState -p Result -p ExecMainCode -p ExecMainStatus"
run "journalctl -u $SERVICE -n 30 --no-pager"
run "systemctl --failed --no-pager"


section "12. Устранение причины, reset-failed и восстановление"
run "rm $FAIL_FLAG"
run "test ! -e $FAIL_FLAG && echo 'fail flag removed'"
run "systemctl reset-failed $SERVICE"
run "systemctl is-failed $SERVICE"
run "systemctl start $SERVICE"
run "systemctl is-active $SERVICE"
run "journalctl -u $SERVICE -n 20 --no-pager"


section "13. Самостоятельное исследование свойств unit"
run "systemctl show $SERVICE -p Description -p LoadState -p ActiveState -p SubState -p UnitFileState -p User -p WorkingDirectory -p ExecStart -p MainPID"


section "14. Дополнительное задание: Restart=on-failure"
run "systemctl stop $SERVICE"
run "sed -i 's/^Restart=no\$/Restart=on-failure\\nRestartSec=2/' $UNIT"
run "grep -n -E 'Restart' $UNIT"
run 'systemctl daemon-reload'
run "touch $FAIL_FLAG"
run "systemctl start $SERVICE"
sleep 8
run "systemctl status $SERVICE --no-pager"
run "systemctl show $SERVICE -p NRestarts -p ActiveState -p SubState -p StartLimitBurst"
run "journalctl -u $SERVICE -n 15 --no-pager"
run "systemctl stop $SERVICE"
run "rm -f $FAIL_FLAG"
run "install -m 0644 /work/deploy/systemd/cloud-lab-worker.service $UNIT"
run 'systemctl daemon-reload'
run "systemctl reset-failed $SERVICE"
run "systemctl start $SERVICE"
run "systemctl is-active $SERVICE"
run "grep -n -E 'Restart' $UNIT"


section "15. Очистка учебной среды"
run "systemctl disable --now $SERVICE"
run "rm -f $UNIT"
run "rm -rf /opt/cloud-lab"
run 'systemctl daemon-reload'
run 'systemctl reset-failed'
run "systemctl status $SERVICE --no-pager"
FAILED_AFTER=$(systemctl --failed --no-legend --no-pager | wc -l | tr -d ' ')
printf '\nКоличество failed units после очистки: %s\n' "$FAILED_AFTER"
printf '\nВсе шаги ЛР 35 выполнены.\n'
