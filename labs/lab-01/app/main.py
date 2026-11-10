from fastapi import FastAPI

app = FastAPI()


@app.get("/", summary="Проверка работоспособности приложения")
def root():
    return {
        "status": "ok",
        "message": "Cloud development environment is ready",
    }


@app.get("/lab", summary="Результат выполнения лабораторной работы")
def lab_result():
    return {"message": "Laboratory work 1 completed"}
