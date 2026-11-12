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


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "service": "conecta-conselho-api"}


# ── Front-end em produção ───────────────────────────────────────────────────
# Se `frontend/dist` existir (após `npm run build`), a própria API serve o site:
# um único serviço/URL no deploy. Em desenvolvimento (sem dist) nada muda.
_DIST = _ROOT / "frontend" / "dist"

if _DIST.is_dir():
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str) -> FileResponse:
        """Devolve o arquivo estático pedido ou o index.html (rotas do React)."""
        candidate = (_DIST / full_path).resolve()
        if candidate.is_file() and _DIST.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(_DIST / "index.html")
else:

    @app.get("/", tags=["health"], include_in_schema=False)
    def root() -> dict:
        return {"status": "ok", "service": "conecta-conselho-api"}
