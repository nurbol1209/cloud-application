# Лабораторная работа № 1. Подготовка среды разработки облачного приложения

## Цель

Подготовить рабочее окружение Python, установить FastAPI и Uvicorn и запустить
первое серверное приложение проекта Cloud Application.

## Что реализовано

- виртуальное окружение `.venv` (создаётся локально, в Git не попадает);
- приложение `app/main.py` на FastAPI;
- маршрут `GET /` — проверка готовности среды;
- маршрут `GET /lab` — подтверждение выполнения работы;
- файл зависимостей `requirements.txt`.

## Запуск

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS:       source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Откройте <http://127.0.0.1:8000/> и <http://127.0.0.1:8000/docs>.

Ожидаемый ответ `GET /`:

```json
{"status": "ok", "message": "Cloud development environment is ready"}
```

## Самостоятельное задание

Маршрут `GET /lab` возвращает `{"message": "Laboratory work 1 completed"}`.

## Примечание

Начиная с ЛР № 12 приложение запускается через `python run.py`, а параметры
хоста и порта берутся из `.env`. В этой работе используется прямой запуск
Uvicorn — так требует задание.
