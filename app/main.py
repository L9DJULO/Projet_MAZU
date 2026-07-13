from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.agents import OrchestratorAgent
from app.config import get_settings
from app.models.schemas import VehicleInfo

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="AutoExpert AI",
    description="Inspection automatisee de vehicules - projet Microsoft Azure",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/api/health")
def health() -> dict:
    s = get_settings()
    if s.vision_is_local_http:
        vision = "local_http"
    elif s.vision_is_real:
        vision = s.vision_provider
    else:
        vision = "mock"
    return {
        "status": "ok",
        "azure_mode": s.azure_mode,
        "vision": vision,
        "vision_endpoint": s.azure_vision_endpoint if s.vision_is_local_http else None,
        "ml": "azure" if s.ml_is_real else "mock",
        "llm_mode": s.llm_mode,
        "history": s.history_api_base,
    }


@app.post("/api/inspect")
async def inspect(
    make: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    mileage_km: Optional[int] = Form(None),
    images: list[UploadFile] = File(default=[]),
) -> JSONResponse:
    vehicle = VehicleInfo(
        make=(make or None),
        model=(model or None),
        year=year,
        mileage_km=mileage_km,
    )

    image_bytes: list[bytes] = []
    for f in images:
        content = await f.read()
        if content:
            image_bytes.append(content)
    if not image_bytes:
        image_bytes = [vehicle.label.encode()]

    report, trace = OrchestratorAgent().run(vehicle, image_bytes)

    return JSONResponse(
        {
            "report": report.model_dump(),
            "trace": trace,
        }
    )
