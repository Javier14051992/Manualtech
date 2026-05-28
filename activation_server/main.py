from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from database import activate_serial, init_db


app = FastAPI(title="Manualtech Activation Server", version="1.0.0-beta")


class ActivationRequest(BaseModel):
    product: str = Field(min_length=1)
    serial: str = Field(min_length=1)
    machine_id_hash: str = Field(min_length=32)
    version: str = Field(default="1.0.0-beta")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/api/manualtech/activate")
def activate(request: ActivationRequest) -> dict:
    return activate_serial(
        product=request.product,
        serial=request.serial,
        machine_id_hash=request.machine_id_hash,
    )
