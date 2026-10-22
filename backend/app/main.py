from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.modules import ROUTERS


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Tamam API")

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
