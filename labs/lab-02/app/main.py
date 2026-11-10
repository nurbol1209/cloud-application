from fastapi import FastAPI

from app.config import APP_NAME, APP_VERSION

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
)


@app.get("/", summary="Сведения о приложении")
def root():
    return {
        "application": APP_NAME,
        "version": APP_VERSION,
        "status": "ok",
    }


@app.get("/status", summary="Состояние приложения")
def status():
    return {
        "status": "ok",
        "service": APP_NAME,
    }


@app.get("/about", summary="Описание проекта")
def about():
    return {
        "name": APP_NAME,
        "type": "cloud application",
        "language": "Python",
        "framework": "FastAPI",
    }


@app.get("/course", summary="Сведения о дисциплине")
def course():
    return {
        "discipline": (
            "Управление работами и разработка программного обеспечения "
            "облачных систем"
        ),
        "laboratory": 2,
        "project": APP_NAME,
    }
