"""
Router: /analise  /relatorio
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Ensure project paths are resolved
_ROOT = Path(__file__).resolve().parent.parent.parent
_CC_DIR = _ROOT / "conecta-conselho"
for _p in [str(_ROOT), str(_CC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from integracao import chamar_guardiao  # type: ignore[import]

router = APIRouter(tags=["analise"])

# In-memory cache: { regiao_id: last_result }
_cache: dict[str, dict[str, Any]] = {}


class AnaliseRequest(BaseModel):
    fonte: str = "local"
    # Simulator params (optional)
    reducao_capex_pct: Optional[float] = None
    ancoras_adicionais: Optional[int] = None
    maturidade_parcerias: Optional[str] = None


@router.post("/analise/{regiao_id}", summary="Executa o Conselho para uma região")
def executar_analise(regiao_id: str, body: AnaliseRequest) -> dict[str, Any]:
    fonte = body.fonte if body.fonte in ("local", "nuvem") else "local"

    try:
        resultado = chamar_guardiao(regiao_id, fonte=fonte)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if resultado.get("erro") and not resultado.get("pareceres"):
        raise HTTPException(status_code=404, detail=resultado["erro"])

    # Apply simulator overrides when partnership params are provided
    if body.reducao_capex_pct is not None or body.ancoras_adicionais is not None:
        resultado = _apply_simulator_overrides(resultado, body)

    # Cache result
    _cache[regiao_id] = resultado
    return resultado


def _apply_simulator_overrides(
    resultado: dict[str, Any],
    params: AnaliseRequest,
) -> dict[str, Any]:
    """
    Applies partnership scenario overrides to a Guardian result.
    Recalculates orcamento and pontes scores based on partnership parameters,
    then re-runs the Guardian consolidation.
    """
    import json as _json
    import importlib.util as _ilu

    _ROOT_PATH = Path(__file__).resolve().parent.parent.parent
    _CC_PATH = _ROOT_PATH / "conecta-conselho"

    def _load_tool(name: str, filename: str):
        path = _ROOT_PATH / "tools" / filename
        spec = _ilu.spec_from_file_location(name, path)
        mod = _ilu.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)       # type: ignore[union-attr]
        return mod

    _mod_guardiao = _load_tool("tool_guardiao", "tool_guardiao.py")
    consolidar = _mod_guardiao.consolidar_pareceres

    result = copy.deepcopy(resultado)
    pareceres = result.get("pareceres", {})

    # Boost orcamento score by CAPEX reduction
    if params.reducao_capex_pct and params.reducao_capex_pct > 0:
        orc = pareceres.get("orcamento", {})
        boost = int(params.reducao_capex_pct * 0.6)  # ~60% of reduction becomes score boost
        orc["score"] = min(100, (orc.get("score") or 0) + boost)
        pareceres["orcamento"] = orc

    # Boost pontes score by anchor institutions
    if params.ancoras_adicionais and params.ancoras_adicionais > 0:
        pont = pareceres.get("pontes", {})
        boost = min(params.ancoras_adicionais * 4, 20)
        pont["score"] = min(100, (pont.get("score") or 0) + boost)
        # Upgrade maturidade label in justificativa
        if params.maturidade_parcerias:
            pont["justificativa"] = (
                f"[Cenário simulado: +{params.ancoras_adicionais} âncoras, maturidade {params.maturidade_parcerias}] "
                + (pont.get("justificativa") or "")
            )
        pareceres["pontes"] = pont

    # Re-consolidate
    novo_resultado = consolidar(_json.dumps(pareceres, ensure_ascii=False))
    if hasattr(novo_resultado, "content"):
        novo_resultado = novo_resultado.content

    novo_resultado["fonte"] = result.get("fonte", "local")
    novo_resultado["regiao_id"] = result.get("regiao_id", "")
    novo_resultado["regiao_nome"] = result.get("regiao_nome", "")
    novo_resultado["tempo_analise_segundos"] = result.get("tempo_analise_segundos", 0)

    return novo_resultado


@router.get("/relatorio/{regiao_id}", summary="Retorna o último relatório gerado para uma região")
def get_relatorio(regiao_id: str) -> JSONResponse:
    resultado = _cache.get(regiao_id)
    if not resultado:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum relatório disponível para '{regiao_id}'. Execute a análise primeiro.",
        )
    return JSONResponse(
        content=resultado,
        headers={
            "Content-Disposition": f'attachment; filename="relatorio_{regiao_id}.json"',
            "Content-Type": "application/json; charset=utf-8",
        },
    )


@router.get("/nuvem/status")
def status_nuvem() -> dict[str, bool]:
    """Indica se as credenciais do modo nuvem (watsonx Orchestrate) estão configuradas.

    Devolve apenas um booleano: nenhuma chave, URL ou ID é exposto.
    """
    from cliente_nuvem import carregar_credenciais  # type: ignore[import]
    from integracao import _verificar_credenciais_nuvem  # type: ignore[import]

    creds_ok = "erro" not in carregar_credenciais()
    ids_ok, _ = _verificar_credenciais_nuvem()
    return {"configurada": bool(creds_ok and ids_ok)}
