"""
Router: /regioes
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from tools.consultar_regiao import listar_regioes, consultar_regiao  # type: ignore[import]

router = APIRouter(prefix="/regioes", tags=["regioes"])


@router.get("", summary="Lista todas as regiões disponíveis")
def get_regioes() -> list[dict[str, Any]]:
    return listar_regioes()


@router.get("/{regiao_id}", summary="Retorna todos os dados de uma região")
def get_regiao(regiao_id: str) -> dict[str, Any]:
    dados = consultar_regiao(regiao_id)
    if "erro" in dados:
        raise HTTPException(status_code=404, detail=dados["mensagem"])
    return dados
