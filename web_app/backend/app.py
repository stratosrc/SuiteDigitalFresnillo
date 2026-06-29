from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import PROJECT_ROOT, STATIC_DIR
from .routers import catalog, converter, directory, health, organization, spa, testdata


def create_app() -> FastAPI:
    application = FastAPI(
        title="Suite Digital Fresnillo Web",
        description="Aplicacion web para los modulos administrativos de Suite Digital Fresnillo.",
        version="2.0.0",
    )
    application.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    application.mount("/assets", StaticFiles(directory=PROJECT_ROOT / "components" / "assets"), name="assets")
    application.mount(
        "/testdata-assets",
        StaticFiles(directory=PROJECT_ROOT / "App_TestData" / "assets"),
        name="testdata-assets",
    )
    application.include_router(health.router)
    application.include_router(catalog.router)
    application.include_router(testdata.router)
    application.include_router(directory.router)
    application.include_router(organization.router)
    application.include_router(converter.router)
    application.include_router(spa.router)
    return application


app = create_app()
