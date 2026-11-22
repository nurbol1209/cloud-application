#!/usr/bin/env bash
# ЛР 37: контейнерное развертывание Cloud Application на Docker Desktop.
set -uo pipefail

LAB_DIR=$(cd "$(dirname "$0")/../.." && pwd -W 2>/dev/null || pwd)
REPO_ROOT=$(cd "$LAB_DIR/../.." && pwd -W 2>/dev/null || pwd)
EVIDENCE="$LAB_DIR/docs/lr37_evidence.txt"
IMAGE=cloud-application:0.7
BAD_IMAGE=cloud-application:0.8-bad
CONTAINER=cloud-application-lr37
ENV_FILE="$LAB_DIR/deploy/etc/cloud-application.env"
RUNTIME="$LAB_DIR/runtime"
SECRETS_DIR="$RUNTIME/secrets"
SECRETS_WIN=$(cygpath -w "$SECRETS_DIR" 2>/dev/null || echo "$SECRETS_DIR")
PYTHON="$REPO_ROOT/.venv/Scripts/python.exe"
if [ ! -x "$PYTHON" ]; then
    PYTHON=python
fi
COMMIT=$(git -C "$REPO_ROOT" rev-parse HEAD)

mkdir -p "$LAB_DIR/docs" "$SECRETS_DIR"
exec > >(tee "$EVIDENCE") 2>&1

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

section() {
    printf '\n\n========== %s ==========\n' "$*"
}

if ! docker info >/dev/null 2>&1; then
    echo "Docker daemon недоступен" >&2
    exit 1
fi


section "1. Среда Docker и версия приложения"
run hostname
run dk version
run dk info --format 'server={{.ServerVersion}} os={{.OSType}} cpus={{.NCPU}} mem={{.MemTotal}}'
run git -C "$REPO_ROOT" status --short
printf '\nGit commit развертываемой версии: %s\n' "$COMMIT"
run git -C "$REPO_ROOT" log -1 --oneline
run sed -n '1,120p' "$LAB_DIR/Dockerfile"


section "2. Сборка контейнерного образа"
run dk build --label "org.opencontainers.image.revision=$COMMIT" -t "$IMAGE" "$LAB_DIR"
run dk image ls cloud-application
IMAGE_ID=$(dk image inspect "$IMAGE" --format '{{.Id}}' | tr -d '\r')
REVISION=$(dk image inspect "$IMAGE" --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' | tr -d '\r')
printf '\nImage ID: %s\nRevision label: %s\n' "$IMAGE_ID" "$REVISION"
printf 'Commit: %s\n' "$COMMIT"


section "3. UID/GID пользователя контейнера"
APP_UID=$(dk run --rm --entrypoint id "$IMAGE" -u | tr -d '\r')
APP_GID=$(dk run --rm --entrypoint id "$IMAGE" -g | tr -d '\r')
printf 'uid=%s gid=%s\n' "$APP_UID" "$APP_GID"
run dk run --rm --entrypoint sh "$IMAGE" -c 'id; whoami'


section "4. Runtime-секреты"
"$PYTHON" -c "import secrets; print(secrets.token_urlsafe(32))" > "$SECRETS_DIR/auth_secret"
"$PYTHON" -c "import secrets; print(secrets.token_urlsafe(24))" > "$SECRETS_DIR/lab_db_password"
chmod 600 "$SECRETS_DIR/auth_secret" "$SECRETS_DIR/lab_db_password" 2>/dev/null || true
run ls -l "$SECRETS_DIR"
printf '\nСодержимое секретов не выводится. Размеры файлов:\n'
run wc -c "$SECRETS_DIR/auth_secret" "$SECRETS_DIR/lab_db_password"


section "5. Запуск контейнера"
dk rm -f "$CONTAINER" >/dev/null 2>&1 || true
run dk run -d \
    --name "$CONTAINER" \
    --restart unless-stopped \
    -p 127.0.0.1:8080:8000 \
    --env-file "$ENV_FILE" \
    -e APP_HOST=0.0.0.0 \
    -e APP_PORT=8000 \
    -e HTTPS_ENABLED=false \
    --mount "type=bind,src=$SECRETS_WIN,dst=/app/secrets,readonly" \
    "$IMAGE"

sleep 4
run dk ps --filter "name=$CONTAINER" --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
run dk inspect "$CONTAINER" --format '{{.State.Status}}'
run dk port "$CONTAINER"
run dk inspect "$CONTAINER" --format '{{.HostConfig.RestartPolicy.Name}}'
run dk inspect "$CONTAINER" --format '{{.Image}}'
printf 'Image ID образа: %s\n' "$IMAGE_ID"
run dk inspect "$CONTAINER" --format '{{json .Mounts}}'


section "6. Runtime-среда и секреты внутри контейнера"
run dk exec "$CONTAINER" whoami
run dk exec "$CONTAINER" pwd
run dk exec "$CONTAINER" python --version
run dk exec "$CONTAINER" sh -c 'ls -ln /app/secrets'
run dk exec "$CONTAINER" sh -c 'test -r /app/secrets/auth_secret && echo AUTH_SECRET_READABLE'
run dk exec "$CONTAINER" sh -c 'test -r /app/secrets/lab_db_password && echo DB_SECRET_READABLE'
run dk exec "$CONTAINER" sh -c 'test -w /app/secrets/auth_secret && echo WRITABLE || echo READ_ONLY_CONFIRMED'


section "7. Журнал и smoke-test"
run dk logs --tail 40 "$CONTAINER"
for _ in $(seq 1 30); do
    code=$(curl --noproxy '*' -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/status 2>/dev/null || true)
    [ "$code" = "200" ] && break
    sleep 1
done
run curl --noproxy '*' -i http://127.0.0.1:8080/status
run curl --noproxy '*' -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/docs
run curl --noproxy '*' -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/openapi.json


section "8. Жизненный цикл: stop / start / restart"
run dk stop "$CONTAINER"
run dk ps --filter "name=$CONTAINER"
run dk ps -a --filter "name=$CONTAINER" --format 'table {{.Names}}\t{{.Status}}'
run dk start "$CONTAINER"
sleep 3
run curl --noproxy '*' -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/status
PID_BEFORE=$(dk inspect "$CONTAINER" --format '{{.State.Pid}}' | tr -d '\r')
run dk restart "$CONTAINER"
sleep 3
PID_AFTER=$(dk inspect "$CONTAINER" --format '{{.State.Pid}}' | tr -d '\r')
printf '\nPID до restart: %s\nPID после restart: %s\n' "$PID_BEFORE" "$PID_AFTER"
run curl --noproxy '*' -s http://127.0.0.1:8080/status


section "9. Неуспешный release 0.8-bad"
mkdir -p "$RUNTIME/bad-image"
cat > "$RUNTIME/bad-image/Dockerfile" <<'EOF'
FROM cloud-application:0.7

CMD ["python", "/app/missing_run.py"]
EOF
run cat "$RUNTIME/bad-image/Dockerfile"
run dk build -t "$BAD_IMAGE" "$RUNTIME/bad-image"

run dk inspect "$CONTAINER" --format '{{.Config.Image}}'
run dk rm -f "$CONTAINER"
run dk run -d \
    --name "$CONTAINER" \
    --restart no \
    -p 127.0.0.1:8080:8000 \
    --env-file "$ENV_FILE" \
    -e APP_HOST=0.0.0.0 \
    -e APP_PORT=8000 \
    -e HTTPS_ENABLED=false \
    --mount "type=bind,src=$SECRETS_WIN,dst=/app/secrets,readonly" \
    "$BAD_IMAGE"
sleep 4
run dk ps --filter "name=$CONTAINER"
run dk ps -a --filter "name=$CONTAINER" --format 'table {{.Names}}\t{{.Status}}'
run dk logs "$CONTAINER"
run dk inspect "$CONTAINER" --format 'image={{.Config.Image}} exit={{.State.ExitCode}} status={{.State.Status}}'


section "10. Rollback на проверенный image 0.7"
run dk rm "$CONTAINER"
run dk run -d \
    --name "$CONTAINER" \
    --restart unless-stopped \
    -p 127.0.0.1:8080:8000 \
    --env-file "$ENV_FILE" \
    -e APP_HOST=0.0.0.0 \
    -e APP_PORT=8000 \
    -e HTTPS_ENABLED=false \
    --mount "type=bind,src=$SECRETS_WIN,dst=/app/secrets,readonly" \
    "$IMAGE"
sleep 4
run dk ps --filter "name=$CONTAINER" --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
run dk inspect "$CONTAINER" --format '{{.Config.Image}}'
run dk inspect "$CONTAINER" --format '{{.HostConfig.RestartPolicy.Name}}'
run dk inspect "$CONTAINER" --format '{{json .Mounts}}'
for _ in $(seq 1 30); do
    code=$(curl --noproxy '*' -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/status 2>/dev/null || true)
    [ "$code" = "200" ] && break
    sleep 1
done
run curl --noproxy '*' -i http://127.0.0.1:8080/status

run dk image rm "$BAD_IMAGE"
rm -rf "$RUNTIME/bad-image"


section "11. Итоговый паспорт контейнерного deployment"
printf 'hostname: %s\n' "$(hostname)"
printf 'Docker server: %s\n' "$(dk info --format '{{.ServerVersion}}' | tr -d '\r')"
printf 'Git commit: %s\n' "$COMMIT"
printf 'Image tag: %s\n' "$IMAGE"
printf 'Image ID: %s\n' "$IMAGE_ID"
printf 'Revision label: %s\n' "$REVISION"
printf 'Container name: %s\n' "$CONTAINER"
printf 'Container status: %s\n' "$(dk inspect "$CONTAINER" --format '{{.State.Status}}' | tr -d '\r')"
printf 'Container PID: %s\n' "$(dk inspect "$CONTAINER" --format '{{.State.Pid}}' | tr -d '\r')"
printf 'Container user: %s\n' "$(dk exec "$CONTAINER" whoami | tr -d '\r')"
printf 'Restart policy: %s\n' "$(dk inspect "$CONTAINER" --format '{{.HostConfig.RestartPolicy.Name}}' | tr -d '\r')"
printf 'Host bind: %s\n' "$(dk port "$CONTAINER" 8000/tcp | tr -d '\r')"
printf '/status: %s\n' "$(curl --noproxy '*' -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/status)"
printf '/docs: %s\n' "$(curl --noproxy '*' -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/docs)"

printf '\nВсе шаги ЛР 37 выполнены.\n'
