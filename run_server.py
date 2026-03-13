import uvicorn
from fastapi import FastAPI
from app.containers import Container
from app.api.router import app_router


def create_app() -> FastAPI:
    container = Container()

    container.wire(modules=["app.api.router"])

    app = FastAPI(title="Notes API (DDD)")

    app.include_router(app_router)

    app.extra["container"] = container

    return app


if __name__ == "__main__":
    # Запускаем как нормальный сервер
    uvicorn.run(
        "run_server:create_app", host="127.0.0.1", port=8080, reload=True, factory=True
    )
