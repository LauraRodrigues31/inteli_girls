"""Gera a cartografia fictícia a partir da malha de referência, sem dependências extras."""

from collections import Counter
from functools import cache
import json
import math
from pathlib import Path
import random

DATA = Path(__file__).resolve().parents[1] / "conecta-conselho" / "data"
SEMENTE = 2147
CASAS = 7


@cache
def detalhar_aresta(a, b):
    """Refina uma única vez cada aresta, com detalhe em duas escalas."""
    if a > b:
        return detalhar_aresta(b, a)[::-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    tamanho = math.hypot(dx, dy)
    passos = max(2, math.ceil(tamanho / 3))
    rng = random.Random(f"{SEMENTE}:{a}:{b}")
    amplitudes = [rng.uniform(-.075, .075), rng.uniform(-.045, .045)]
    pontos = [a]
    for i in range(1, passos):
        t = i / passos
        desvio = math.sin(math.pi * t) * (
            amplitudes[0] + amplitudes[1] * math.sin(3 * math.pi * t)
            + rng.uniform(-.028, .028)
        )
        pontos.append((round(a[0] + dx*t - dy*desvio, 3), round(a[1] + dy*t + dx*desvio, 3)))
    return (*pontos, b)


def detalhar(pontos):
    return [
        p for a, b in zip(pontos, pontos[1:]) for p in detalhar_aresta(tuple(a), tuple(b))[:-1]
    ] + [tuple(pontos[-1])]


def arestas(aneis):
    return Counter((a, b) for anel in aneis for a, b in zip(anel, anel[1:]))


def area_dobrada(anel):
    return sum(a[0]*b[1] - a[1]*b[0] for a, b in zip(anel, anel[1:]))


def contem_ponto(anel, ponto):
    x, y = ponto
    cruzamentos = sum(
        (a[1] > y) != (b[1] > y) and x < a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1])
        for a, b in zip(anel, anel[1:])
    )
    return cruzamentos % 2 == 1


def verificar_malha(aneis):
    """Valida anéis orientados, divisas encaixadas e um único contorno exterior."""
    for anel in aneis:
        if anel[0] != anel[-1] or len(set(anel[:-1])) != len(anel) - 1:
            raise ValueError("Anel regional aberto ou com vértices repetidos.")
        if area_dobrada(anel) <= 0:
            raise ValueError("Anel regional com área nula ou orientação invertida.")
    segmentos = arestas(aneis)
    if any(n != 1 for n in segmentos.values()):
        raise ValueError("Há arestas regionais duplicadas no mesmo sentido.")
    exterior = {a: b for a, b in segmentos if (b, a) not in segmentos}
    if len(exterior) != sum((b, a) not in segmentos for a, b in segmentos):
        raise ValueError("O contorno exterior se ramifica.")
    inicio = atual = next(iter(exterior))
    for _ in range(len(exterior)):
        if atual not in exterior:
            raise ValueError("O contorno possui lacuna ou anéis desconectados.")
        atual = exterior.pop(atual)
    if atual != inicio:
        raise ValueError("O contorno exterior não fecha.")

    def lado(a, b, c):
        return (b[0]-a[0]) * (c[1]-a[1]) - (b[1]-a[1]) * (c[0]-a[0])

    # Quantização inteira evita tolerâncias em testes de colinearidade.
    unicos = sorted({
        tuple(sorted((tuple(round(v*1000) for v in a), tuple(round(v*1000) for v in b))))
        for a, b in segmentos
    })
    for i, (a, b) in enumerate(unicos):
        for j in range(i + 1, len(unicos)):
            c, d = unicos[j]
            if c[0] > b[0]:
                break
            if max(a[1], b[1]) < min(c[1], d[1]) or max(c[1], d[1]) < min(a[1], b[1]):
                continue
            ab_c, ab_d = lado(a, b, c), lado(a, b, d)
            cd_a, cd_b = lado(c, d, a), lado(c, d, b)
            if ab_c == ab_d == cd_a == cd_b == 0:
                if max(a, c) < min(b, d):
                    raise ValueError("Segmentos colineares sobrepostos.")
            elif not {a, b}.intersection((c, d)) and ab_c * ab_d <= 0 and cd_a * cd_b <= 0:
                raise ValueError("Segmentos regionais cruzados.")


def coordenada(ponto):
    # Origem e escala angulares são apenas uma codificação para GeoJSON.
    return [round(ponto[0] / 1000, CASAS), round(-ponto[1] / 1000, CASAS)]


def feicao(camada, tipo, pontos, **propriedades):
    if tipo == "Point":
        coords = coordenada(pontos)
    elif tipo == "Polygon":
        # A inversão do eixo vertical pede a ordem contrária para anéis externos.
        anel = pontos if area_dobrada(pontos) > 0 else pontos[::-1]
        if camada != "regiao":
            verificar_malha([anel])
        coords = [[coordenada(p) for p in reversed(anel)]]
    else:
        coords = [coordenada(p) for p in pontos]
    return {
        "type": "Feature",
        "properties": {"camada": camada, **propriedades},
        "geometry": {"type": tipo, "coordinates": coords},
    }


def gerar():
    base = json.loads((DATA / "mapa_poligonos.json").read_text(encoding="utf-8"))
    feicoes, aneis = [], []
    for regiao in base["regioes"]:
        pontos = list(zip(regiao["poligono_x"], regiao["poligono_y"]))
        anel = detalhar(pontos + pontos[:1])
        aneis.append(anel)
        rotulo = (regiao["label_x"], regiao["label_y"])
        if not contem_ponto(anel, rotulo):
            raise ValueError(f'Rótulo fora da região {regiao["id"]}.')
        feicoes.append(feicao(
            "regiao", "Polygon", anel, id=regiao["id"], nome=regiao["nome"],
            rotulo=coordenada(rotulo),
        ))
    verificar_malha(aneis)

    litoral = detalhar(base["litoral"])
    feicoes += [
        feicao("terra", "Polygon", [(-90, -10), *litoral, (-90, 400), (-90, -10)]),
        feicao("costa", "LineString", litoral),
        feicao("terra", "Polygon", detalhar([
            (570, 132), (578, 122), (582, 111), (589, 115), (593, 124),
            (589, 130), (591, 137), (581, 143), (573, 140), (570, 132)
        ])),
        feicao("terra", "Polygon", [(582, 154), (586, 152), (588, 157), (585, 160), (582, 154)]),
        feicao("toponimo", "Point", (559, 264), nome="Baía das Garças"),
    ]

    # Do interior alto ao estuário: o baixo curso também é uma divisa regional.
    cabeceira = [(184, 106), (187, 120), (173, 130), (181, 145), (204, 153),
                 (218, 164), (211, 178), (229, 192), (259, 205), (272, 220),
                 (290, 225), (287, 239), (309, 251)]
    divisa_fluvial = [(309, 251), (336, 229), (349, 213), (378, 212), (390, 192),
                      (409, 184), (430, 172), (446, 188), (473, 185), (492, 205),
                      (522, 206), (546, 193)]
    malha = arestas(aneis)
    baixo_curso = detalhar(divisa_fluvial)
    if any((a, b) not in malha or (b, a) not in malha for a, b in zip(baixo_curso, baixo_curso[1:])):
        raise ValueError("O baixo curso precisa coincidir com uma divisa compartilhada.")
    rios = [
        (2, cabeceira), (3, divisa_fluvial),
        (1, [(108, 126), (132, 137), (144, 150), (166, 153), (181, 160), (204, 153)]),
        (1, [(291, 76), (278, 91), (281, 113), (267, 132), (264, 153), (245, 170), (229, 192)]),
        (1, [(379, 273), (369, 255), (354, 249), (346, 238), (336, 229)]),
        (1, [(479, 266), (475, 251), (487, 236), (485, 220), (492, 205)]),
    ]
    feicoes.extend(feicao("rio", "LineString", detalhar(p), nivel=n) for n, p in rios)

    reservas = [
        ([(119, 121), (142, 112), (158, 96), (178, 86), (200, 92), (216, 105), (238, 99),
          (257, 85), (286, 87), (300, 102), (276, 110), (252, 125), (222, 123), (207, 132),
          (188, 117), (167, 120), (145, 134), (126, 134), (119, 121)], "Parque da Serra do Cedro"),
        ([(350, 293), (367, 274), (383, 276), (403, 266), (426, 276), (432, 292),
          (411, 302), (393, 297), (376, 307), (361, 307), (350, 293)], "Reserva das Nascentes"),
    ]
    feicoes.extend(feicao("reserva", "Polygon", detalhar(p), nome=nome) for p, nome in reservas)
    for offset in (0, 5, 10):
        linha = [(x, y + offset) for x, y in [(137, 112), (159, 101), (180, 96), (205, 110),
                                              (223, 112), (246, 105), (272, 96)]]
        feicoes.append(feicao("relevo", "LineString", detalhar(linha)))

    vias = [
        (2, [(48, 173), (94, 179), (131, 185), (172, 183), (223, 179), (272, 173),
             (319, 176), (353, 167), (394, 148), (433, 143), (476, 147), (508, 139)]),
        (2, [(309, 59), (296, 86), (299, 112), (289, 138), (300, 155), (319, 176),
             (344, 202), (367, 219), (396, 235), (420, 255), (451, 264), (473, 254)]),
        (1, [(131, 185), (151, 211), (174, 236), (191, 266), (228, 281), (268, 278),
             (298, 266), (337, 264), (377, 255), (420, 255)]),
        (1, [(300, 155), (318, 151), (334, 156), (353, 167)]),
        (1, [(319, 176), (308, 191), (320, 202), (344, 202)]),
        (1, [(433, 143), (445, 125), (468, 119), (485, 123), (508, 139)]),
    ]
    feicoes.extend(feicao("via", "LineString", detalhar(p), nivel=n) for n, p in vias)
    for centro in [(131, 185), (309, 59), (319, 176), (433, 143), (228, 281), (420, 255)]:
        x, y = centro
        feicoes.append(feicao("urbano", "Polygon", [
            (x-10, y-2), (x-4, y-7), (x+5, y-6), (x+10, y-1),
            (x+7, y+6), (x-2, y+7), (x-9, y+4), (x-10, y-2)
        ]))
    backbone = base["backbone"]
    central = next(anel for regiao, anel in zip(base["regioes"], aneis) if regiao["id"] == "central")
    if not contem_ponto(central, (backbone["x"], backbone["y"])):
        raise ValueError("O marcador de fibra deve ficar na Região Central.")
    feicoes.append(feicao("fibra", "Point", (backbone["x"], backbone["y"]), nome="Rede principal de fibra"))

    destino = DATA / "territorio_ficticio.geojson"
    destino.write_text(
        '{"type":"FeatureCollection","features":[\n' +
        ",\n".join(json.dumps(f, ensure_ascii=False, separators=(",", ":")) for f in feicoes) +
        "\n]}\n", encoding="utf-8",
    )
    print(f"{destino.name}: {len(aneis)} regiões validadas, {len(feicoes)} feições.")


if __name__ == "__main__":
    try:
        gerar()
    except (OSError, KeyError, ValueError) as erro:
        raise SystemExit(f"Falha ao gerar a cartografia: {erro}") from erro
