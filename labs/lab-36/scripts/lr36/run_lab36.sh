#!/usr/bin/env bash
# Оркестратор ЛР 36: systemd-развертывание Cloud Application в Ubuntu-контейнере.
# Требуется Docker Desktop (Linux containers).
set -euo pipefail

LAB_DIR=$(cd "$(dirname "$0")/../.." && pwd -W 2>/dev/null || pwd)
CONTAINER=lr36-cloudapp
IMAGE=jrei/systemd-ubuntu:24.04
EVIDENCE="$LAB_DIR/docs/lr36_evidence.txt"
KEEP=${KEEP:-0}

if ! docker info >/dev/null 2>&1; then
    echo "Docker daemon недоступен. Запустите Docker Desktop." >&2
    exit 1
fi

echo "[1/6] Подготовка Git-снимка развертываемой версии"
TMP=$(mktemp -d)
cp -a "$LAB_DIR/." "$TMP/"
find "$TMP" -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$TMP" \( -name '*.pyc' -o -name '*.db' -o -name '*.prof' \) -delete 2>/dev/null || true
rm -rf "$TMP/secrets" "$TMP/.env" "$TMP/.ruff_cache"
git -C "$TMP" init -q -b main
git -C "$TMP" config user.name "Cloud Application Lab"
git -C "$TMP" config user.email "lab@example.local"
git -C "$TMP" config core.autocrlf false
git -C "$TMP" config core.safecrlf false
git -C "$TMP" add -A
git -C "$TMP" commit -q -m "Cloud Application 0.7 deployment snapshot (LR36)"
BUNDLE="$TMP.bundle"
BUNDLE_WIN=$(cygpath -w "$BUNDLE" 2>/dev/null || echo "$BUNDLE")
git -C "$TMP" bundle create "$BUNDLE" --all >/dev/null
echo "commit: $(git -C "$TMP" rev-parse HEAD)"

echo "[2/6] Подготовка контейнера $CONTAINER"
docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
MSYS_NO_PATHCONV=1 docker run -d \
    --privileged \
    --cgroupns=host \
    -v /sys/fs/cgroup:/sys/fs/cgroup:rw \
    --name "$CONTAINER" \
    "$IMAGE" >/dev/null

echo "[3/6] Ожидание systemd"
for _ in $(seq 1 30); do
    state=$(docker exec "$CONTAINER" systemctl is-system-running 2>/dev/null || true)
    if [ "$state" = "running" ] || [ "$state" = "degraded" ]; then
        break
    fi
    sleep 1
done
docker exec "$CONTAINER" systemctl is-system-running

echo "[4/6] Копирование проекта и Git-bundle"
MSYS_NO_PATHCONV=1 docker exec "$CONTAINER" rm -rf /work
MSYS_NO_PATHCONV=1 docker cp "$LAB_DIR" "$CONTAINER:/work"
MSYS_NO_PATHCONV=1 docker cp "$BUNDLE_WIN" "$CONTAINER:/tmp/cloud-application.bundle"

echo "[5/6] Выполнение deployment (может занять несколько минут)"
mkdir -p "$LAB_DIR/docs"
MSYS_NO_PATHCONV=1 docker exec "$CONTAINER" bash /work/scripts/lr36/lab36_steps.sh >"$EVIDENCE" 2>&1 || true

echo "[6/6] Завершение"
rm -rf "$TMP" "$BUNDLE"
if [ "$KEEP" = "1" ]; then
    echo "Контейнер $CONTAINER оставлен запущенным (KEEP=1)."
else
    docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
    echo "Контейнер $CONTAINER удалён. Запустите с KEEP=1, чтобы сохранить стенд."
fi

echo "Готово: $EVIDENCE"
