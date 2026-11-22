#!/usr/bin/env bash
# Оркестратор ЛР 35: запускает Ubuntu 24.04 с systemd в Docker и выполняет шаги.
# Требуется Docker Desktop (Linux containers).
set -euo pipefail

# Git Bash / MSYS иначе преобразует /sys/fs/cgroup в Windows-путь.
export MSYS_NO_PATHCONV=1

LAB_DIR=$(cd "$(dirname "$0")/../.." && pwd -W 2>/dev/null || pwd)
CONTAINER=lr35-systemd
IMAGE=jrei/systemd-ubuntu:24.04
EVIDENCE="$LAB_DIR/docs/lr35_evidence.txt"

if ! docker info >/dev/null 2>&1; then
    echo "Docker daemon недоступен. Запустите Docker Desktop." >&2
    exit 1
fi

echo "[1/5] Подготовка контейнера $CONTAINER"
docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
docker run -d \
    --privileged \
    --cgroupns=host \
    -v /sys/fs/cgroup:/sys/fs/cgroup:rw \
    --name "$CONTAINER" \
    "$IMAGE" >/dev/null

echo "[2/5] Ожидание systemd"
for _ in $(seq 1 30); do
    state=$(docker exec "$CONTAINER" systemctl is-system-running 2>/dev/null || true)
    if [ "$state" = "running" ] || [ "$state" = "degraded" ]; then
        break
    fi
    sleep 1
done
docker exec "$CONTAINER" systemctl is-system-running

echo "[3/5] Копирование материалов лабораторной работы"
docker exec "$CONTAINER" rm -rf /work
docker cp "$LAB_DIR" "$CONTAINER:/work"

echo "[4/5] Выполнение шагов ЛР 35"
mkdir -p "$LAB_DIR/docs"
docker exec "$CONTAINER" bash /work/scripts/lr35/lab35_steps.sh >"$EVIDENCE" 2>&1 || true

echo "[5/5] Остановка контейнера"
docker rm -f "$CONTAINER" >/dev/null 2>&1 || true

echo "Готово: $EVIDENCE"
