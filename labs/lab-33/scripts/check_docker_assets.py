"""Статическая проверка Dockerfile и .dockerignore без Docker Engine.

Скрипт не заменяет docker build, но позволяет убедиться, что:
- Dockerfile содержит обязательные инструкции в правильном порядке;
- базовый образ соответствует проверенной версии Python;
- конфиденциальные и локальные файлы не попадают в build context.
"""

import fnmatch
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
EXPECTED_PYTHON = "3.13"

REQUIRED_CONTEXT = [
    "app/main.py",
    "migrations/env.py",
    "alembic.ini",
    "run.py",
    "requirements.txt",
]

FORBIDDEN_CONTEXT = [
    ".env",
    ".env.example",
    "secrets/lab_db_password",
    "secrets/auth_secret",
    "certs/localhost-key.pem",
    "certs/localhost.pem",
    "storage/objects/example.bin",
    "docs/dependencies.md",
    "cloud_application.db",
    "pylock.toml",
    "requests.http",
    ".git/config",
    ".venv-check/pyvenv.cfg",
    ".venv/pyvenv.cfg",
    "app/__pycache__/main.cpython-313.pyc",
]


def read_patterns() -> list[str]:
    lines = (BASE_DIR / ".dockerignore").read_text(encoding="utf-8")
    return [
        line.strip()
        for line in lines.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def is_ignored(path: str, patterns: list[str]) -> bool:
    path = path.replace("\\", "/")
    parts = path.split("/")
    for raw in patterns:
        pattern = raw.rstrip("/")
        if raw.endswith("/"):
            if path == pattern or path.startswith(pattern + "/"):
                return True
            if "/" not in pattern and pattern in parts[:-1]:
                return True
            continue
        if fnmatch.fnmatchcase(path, pattern):
            return True
        if "/" not in pattern and any(
            fnmatch.fnmatchcase(part, pattern) for part in parts
        ):
            return True
    return False


def context_files(patterns: list[str]) -> list[str]:
    result = []
    for path in BASE_DIR.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(BASE_DIR).as_posix()
        if not is_ignored(relative, patterns):
            result.append(relative)
    return sorted(result)


def dockerfile_instructions() -> list[tuple[int, str, str]]:
    lines = (BASE_DIR / "Dockerfile").read_text(encoding="utf-8").splitlines()
    instructions = []
    buffer = ""
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        buffer = f"{buffer} {stripped}".strip() if buffer else stripped
        if buffer.endswith("\\"):
            buffer = buffer[:-1].strip()
            continue
        keyword, _, rest = buffer.partition(" ")
        instructions.append((number, keyword.upper(), rest.strip()))
        buffer = ""
    return instructions


def main() -> int:
    failures: list[str] = []
    patterns = read_patterns()
    instructions = dockerfile_instructions()
    keywords = [item[1] for item in instructions]
    joined = "\n".join(f"{keyword} {rest}" for _, keyword, rest in instructions)

    print("== Dockerfile ==")
    for number, keyword, rest in instructions:
        print(f"{number:>3}  {keyword:<8} {rest[:70]}")

    from_lines = [rest for _, keyword, rest in instructions if keyword == "FROM"]
    if not from_lines:
        failures.append("FROM отсутствует")
    else:
        base = from_lines[0]
        print(f"\nБазовый образ: {base}")
        if f"python:{EXPECTED_PYTHON}-slim" not in base:
            failures.append(
                f"базовый образ не соответствует Python {EXPECTED_PYTHON}"
            )

    for keyword in ["WORKDIR", "USER", "EXPOSE", "CMD", "LABEL"]:
        if keyword not in keywords:
            failures.append(f"инструкция {keyword} отсутствует")

    if "USER appuser" not in joined:
        failures.append("контейнер запускается не от appuser")
    if "EXPOSE 8000" not in joined:
        failures.append("порт 8000 не объявлен")
    if 'CMD ["python", "run.py"]' not in joined:
        failures.append("CMD не запускает run.py")
    if "--no-cache-dir" not in joined:
        failures.append("pip install выполняется с кэшем")

    copy_requirements = next(
        (i for i, (_, k, rest) in enumerate(instructions)
         if k == "COPY" and "requirements.txt" in rest),
        -1,
    )
    copy_app = next(
        (i for i, (_, k, rest) in enumerate(instructions)
         if k == "COPY" and " app " in f" {rest} "),
        -1,
    )
    run_pip = next(
        (i for i, (_, k, rest) in enumerate(instructions)
         if k == "RUN" and "pip install" in rest),
        -1,
    )
    if -1 in (copy_requirements, run_pip, copy_app):
        failures.append("не найдены COPY requirements / RUN pip / COPY app")
    elif not copy_requirements < run_pip < copy_app:
        failures.append("нарушен порядок: requirements -> pip install -> код")
    else:
        print("Порядок слоёв: requirements -> pip install -> app (кэш сохраняется)")

    print("\n== Build context ==")
    files = context_files(patterns)
    total = sum((BASE_DIR / item).stat().st_size for item in files)
    print(f"Файлов в контексте: {len(files)}, суммарно {total / 1024:.1f} KiB")
    for item in files:
        print(f"  {item}")

    for required in REQUIRED_CONTEXT:
        status = "OK" if required in files else "FAIL"
        print(f"[{status}] обязательный файл: {required}")
        if status == "FAIL":
            failures.append(f"в контексте нет {required}")

    for forbidden in FORBIDDEN_CONTEXT:
        ignored = is_ignored(forbidden, patterns)
        status = "OK" if ignored else "FAIL"
        print(f"[{status}] исключён: {forbidden}")
        if not ignored:
            failures.append(f"в контекст попадает {forbidden}")

    print("\n== Итог ==")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("PASS: Dockerfile и .dockerignore согласованы, секреты вне контекста")
    return 0


if __name__ == "__main__":
    sys.exit(main())
