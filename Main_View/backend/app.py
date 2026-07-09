from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from App_ConversorPDF.backend import routes as converter_routes
from App_Directorio.backend import routes as directory_routes
from App_Organigrama.backend import routes as organization_routes
from App_TestData.backend import catalog_routes, routes as testdata_routes

from .config import FRONTEND_DIR, PROJECT_ROOT
from .routers import health, spa


def create_app() -> FastAPI:
    application = FastAPI(
        title="Suite Digital Fresnillo Web",
        description="Aplicacion web para los modulos administrativos de Suite Digital Fresnillo.",
        version="2.0.0",
    )
    application.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
    application.mount(
        "/module-static/testdata",
        StaticFiles(directory=PROJECT_ROOT / "App_TestData" / "frontend"),
        name="testdata-frontend",
    )
    application.mount(
        "/module-static/organigrama",
        StaticFiles(directory=PROJECT_ROOT / "App_Organigrama" / "frontend"),
        name="organigrama-frontend",
    )
    application.mount(
        "/module-static/directorio/assets",
        StaticFiles(directory=PROJECT_ROOT / "App_Directorio" / "assets"),
        name="directorio-module-assets",
    )
    application.mount(
        "/module-static/directorio",
        StaticFiles(directory=PROJECT_ROOT / "App_Directorio" / "frontend"),
        name="directorio-frontend",
    )
    application.mount(
        "/module-static/conversor/assets",
        StaticFiles(directory=PROJECT_ROOT / "App_ConversorPDF" / "assets"),
        name="conversor-module-assets",
    )
    application.mount(
        "/module-static/conversor",
        StaticFiles(directory=PROJECT_ROOT / "App_ConversorPDF" / "frontend"),
        name="conversor-frontend",
    )
    application.mount("/assets", StaticFiles(directory=PROJECT_ROOT / "components" / "assets"), name="assets")
    application.mount(
        "/testdata-assets",
        StaticFiles(directory=PROJECT_ROOT / "App_TestData" / "assets"),
        name="testdata-assets",
    )
    application.mount(
        "/organigrama-assets",
        StaticFiles(directory=PROJECT_ROOT / "App_Organigrama" / "assets"),
        name="organigrama-assets",
    )
    application.mount(
        "/directorio-assets",
        StaticFiles(directory=PROJECT_ROOT / "App_Directorio" / "assets"),
        name="directorio-assets",
    )
    application.include_router(health.router)
    application.include_router(catalog_routes.router)
    application.include_router(testdata_routes.router)
    application.include_router(directory_routes.router)
    application.include_router(organization_routes.router)
    application.include_router(converter_routes.router)
    application.include_router(spa.router)
    return application


app = create_app()
