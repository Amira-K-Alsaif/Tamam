from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.modules import ROUTERS
from app.modules.chat import retrieval as chat_retrieval


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Loading the chat's models takes a minute or more, so do it before serving requests
    # rather than during the first question.
    if get_settings().warm_up_models:
        chat_retrieval.warm_up()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Tamam API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    for router in ROUTERS:
        app.include_router(router)

    return app


app = create_app()
