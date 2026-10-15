"""Loopback development host only; never installed as a Hermes service."""

from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from dashboard.plugin_api import data_source, router
from dev.fixtures import make_state
from dev.preview_api import router as preview_router, scenario_middleware

ROOT = Path(__file__).resolve().parents[1]
app = FastAPI(title="Hermes Usage Manager Mock Host")
app.state.preview = make_state()
app.middleware("http")(scenario_middleware)
app.dependency_overrides[data_source] = lambda: "mock"
legacy_health = APIRouter()
legacy_health.routes.extend(route for route in router.routes if route.path == '/health')
app.include_router(legacy_health, prefix="/api/plugins/hermes-usage-manager")
app.include_router(preview_router)
app.mount("/dashboard-plugins/hermes-usage-manager", StaticFiles(directory=ROOT / "dashboard"))
app.mount("/mock-assets", StaticFiles(directory=ROOT / "frontend/.mock-dist", check_dir=False))


@app.get("/")
def index():
    return FileResponse(ROOT / "frontend/mock/index.html")
