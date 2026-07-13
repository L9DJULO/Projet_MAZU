from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import iterate_in_threadpool

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
def index() -> HTMLResponse:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(
        content=html,
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


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


def _build_vehicle(make, model, year, mileage_km, vin, base_market_value) -> VehicleInfo:
    return VehicleInfo(
        make=make,
        model=model,
        year=year,
        mileage_km=mileage_km,
        vin=vin or None,
        base_market_value=base_market_value or None,
    )


async def _read_images(images: list[UploadFile], fallback_key: str) -> list[bytes]:
    image_bytes: list[bytes] = []
    for f in images:
        content = await f.read()
        if content:
            image_bytes.append(content)
    if not image_bytes:
        image_bytes = [fallback_key.encode()]
    return image_bytes


@app.post("/api/inspect")
async def inspect(
    make: str = Form(...),
    model: str = Form(...),
    year: int = Form(...),
    mileage_km: int = Form(...),
    vin: str = Form(""),
    base_market_value: float = Form(0),
    images: list[UploadFile] = File(default=[]),
) -> JSONResponse:
    vehicle = _build_vehicle(make, model, year, mileage_km, vin, base_market_value)
    image_bytes = await _read_images(images, f"{make}{model}{year}")
    report, trace = OrchestratorAgent().run(vehicle, image_bytes)
    return JSONResponse({"report": report.model_dump(), "trace": trace})


@app.post("/api/inspect/stream")
async def inspect_stream(
    make: str = Form(...),
    model: str = Form(...),
    year: int = Form(...),
    mileage_km: int = Form(...),
    vin: str = Form(""),
    base_market_value: float = Form(0),
    images: list[UploadFile] = File(default=[]),
) -> StreamingResponse:
    vehicle = _build_vehicle(make, model, year, mileage_km, vin, base_market_value)
    image_bytes = await _read_images(images, f"{make}{model}{year}")

    generator = OrchestratorAgent().run_iter(vehicle, image_bytes, pace=0.5)

    async def event_stream():
        async for event in iterate_in_threadpool(generator):
            yield json.dumps(event, ensure_ascii=False) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")
