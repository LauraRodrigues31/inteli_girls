"""
Conecta Conselho — FastAPI backend
Wraps the existing Python tools without rewriting any business logic.
"""

from __future__ import annotations

import sys
from pathlib import Path

# ── Path setup ──────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent          # inteli_girls/
_CC_DIR = _ROOT / "conecta-conselho"

for _p in [str(_ROOT), str(_CC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import regioes, analise

app = FastAPI(
    title="Conecta Conselho API",
    version="1.0.0",
    description="REST API para o sistema multiagente Conecta Conselho.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(regioes.router)
app.include_router(analise.router)


@app.get("/", tags=["health"])
def health() -> dict:
    return {"status": "ok", "service": "conecta-conselho-api"}
