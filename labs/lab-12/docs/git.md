# Работа с Git-репозиторием

## Инициализация

```bash
git init
git status
```

## Исключения

Файл `.gitignore` исключает из репозитория:

```
.venv/
__pycache__/
*.pyc
.env
.vscode/
```

Виртуальное окружение содержит локальные бинарные файлы, `.env` может
содержать параметры конкретной среды, служебные файлы Python не являются
исходным кодом.

## Первый коммит

```bash
git add app
git add requirements.txt
git add PROJECT_TASKS.md
git add .gitignore
git commit -m "Initial version of Cloud Application"
```

## Документация проекта

```bash
git add README.md
git commit -m "Add project README"
```

## Обновление документации

```bash
git add README.md
git commit -m "Update project documentation"
```

## Просмотр состояния и истории

```bash
git status
git diff
git log --oneline
git log --oneline --graph --all
```

## Проверка игнорируемых файлов

```bash
git check-ignore -v .env
git ls-files
```

## Результат

Репозиторий содержит исходный код, документацию и описание задач. Локальное
окружение, кэш Python и файл `.env` в репозиторий не попадают.
