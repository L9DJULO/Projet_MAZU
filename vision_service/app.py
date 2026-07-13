from __future__ import annotations

import hashlib

from fastapi import FastAPI, Request

service = FastAPI(title="Vision Service (stub Custom Vision)", version="1.0.0")


@service.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "vision-local-stub"}


@service.post("/image")
async def image(request: Request) -> dict:
    body = await request.body()
    digest = hashlib.sha256(body or b"empty").digest()
    destroyed = round(0.2 + (digest[0] / 255) * 0.7, 4)
    good = round(1.0 - destroyed, 4)
    return {
        "created": "",
        "id": "",
        "iteration": "",
        "project": "",
        "predictions": [
            {"tagName": "Destroyed", "probability": destroyed, "boundingBox": None},
            {"tagName": "Good", "probability": good, "boundingBox": None},
        ],
    }
