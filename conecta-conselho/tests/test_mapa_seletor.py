"""Regressões do GeoJSON usado pelo seletor das duas páginas."""

import json

from paginas.mapa_seletor import _GEOJSON, _carregar_geografia
from scripts.gerar_geografia_ficticia import arestas, contem_ponto, verificar_malha


def test_geojson_carrega_as_mesmas_regioes_da_base():
    camadas = _carregar_geografia(_GEOJSON.stat().st_mtime_ns)
    base = json.loads(_GEOJSON.with_name("regioes.json").read_text(encoding="utf-8"))
    regioes_base = sorted((r["id"], r["nome"]) for r in base["regioes"])
    regioes_mapa = sorted(
        (f["properties"]["id"], f["properties"]["nome"]) for f in camadas["regiao"]
    )

    assert regioes_mapa == regioes_base


def test_malha_publicada_tem_divisas_continuas_e_rotulos_internos():
    camadas = _carregar_geografia(_GEOJSON.stat().st_mtime_ns)

    def ponto_local(coordenada):
        lon, lat = coordenada
        return round(lon * 1000, 3), round(-lat * 1000, 3)

    aneis = []
    for regiao in camadas["regiao"]:
        contorno, = regiao["geometry"]["coordinates"]
        anel = [ponto_local(p) for p in reversed(contorno)]
        assert contem_ponto(anel, ponto_local(regiao["properties"]["rotulo"])), regiao["properties"]["id"]
        aneis.append(anel)

    verificar_malha(aneis)
    divisas = arestas(aneis)
    baixo_curso, = [f for f in camadas["rio"] if f["properties"]["nivel"] == 3]
    curso = [ponto_local(p) for p in baixo_curso["geometry"]["coordinates"]]
    assert all((a, b) in divisas and (b, a) in divisas for a, b in zip(curso, curso[1:]))
