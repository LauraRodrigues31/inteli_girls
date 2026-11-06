"""Seletor cartográfico compartilhado pela Análise e pelo Simulador."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

_POLIGONOS_JSON = Path(__file__).resolve().parent.parent / "data" / "mapa_poligonos.json"
_GEOJSON = _POLIGONOS_JSON.with_name("territorio_ficticio.geojson")
_SESSION_KEY = "regiao_mapa_selecionada"


def carregar_poligonos(caminho: str | Path = _POLIGONOS_JSON) -> dict:
    """
    Lê mapa_poligonos.json e devolve o dicionário completo.

    Args:
        caminho: Caminho para o arquivo JSON.

    Returns:
        Dicionário com 'backbone' e 'regioes'.
    """
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def ids_do_mapa(caminho: str | Path = _POLIGONOS_JSON) -> list[str]:
    """Retorna a lista de IDs de regiões definidos no arquivo de geometria."""
    dados = carregar_poligonos(caminho)
    return [r["id"] for r in dados["regioes"]]


@st.cache_data(show_spinner=False)
def _carregar_geografia(modificado_em: int) -> dict:
    with _GEOJSON.open(encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    if dados.get("type") != "FeatureCollection":
        raise ValueError("O território precisa ser uma coleção GeoJSON.")
    camadas: dict[str, list] = {}
    tipos = {
        "terra": "Polygon", "regiao": "Polygon", "reserva": "Polygon", "urbano": "Polygon",
        "costa": "LineString", "rio": "LineString", "via": "LineString", "relevo": "LineString",
        "toponimo": "Point", "fibra": "Point",
    }
    for feicao in dados["features"]:
        propriedades = feicao["properties"]
        camada = propriedades["camada"]
        geometria = feicao["geometry"]
        if geometria["type"] != tipos.get(camada) or not geometria["coordinates"]:
            raise ValueError(f"Geometria inválida na camada {camada}.")
        camadas.setdefault(camada, []).append(feicao)
    if camadas.keys() != tipos.keys():
        raise ValueError("A coleção GeoJSON tem camadas ausentes.")
    ids = [f["properties"]["id"] for f in camadas["regiao"]]
    if sorted(ids) != sorted(ids_do_mapa()):
        raise ValueError("As regiões do GeoJSON não correspondem às da base cartográfica.")
    return camadas


_MAPA = st.components.v2.component(
    "seletor_territorio",
    html="""
        <div class="mapa">
            <div class="quadro">
                <div class="territorio"></div>
                <div class="controles" role="group" aria-label="Controles do mapa">
                    <span class="norte" title="Norte" aria-label="Norte">N ↑</span>
                    <button type="button" data-zoom="in" aria-label="Aproximar" title="Aproximar">+</button>
                    <button type="button" data-zoom="out" aria-label="Afastar" title="Afastar">−</button>
                    <button type="button" data-zoom="reset" aria-label="Restaurar enquadramento"
                        title="Restaurar enquadramento">↺</button>
                </div>
            </div>
            <ul class="legenda" aria-label="Legenda do mapa">
                <li><i class="amostra limite"></i> Limite regional</li>
                <li><i class="amostra preenchimento"></i> Região selecionada</li>
                <li><i class="amostra rio"></i> Curso d'água</li>
                <li><i class="amostra via"></i> Rodovia</li>
                <li><i class="amostra reserva"></i> Área protegida</li>
                <li><i class="amostra urbano"></i> Núcleo urbano</li>
                <li><i class="amostra rede"></i> Backbone atual</li>
            </ul>
        </div>
    """,
    css="""
        .mapa {
            background: #dfedf0; border: 1px solid #cad9db;
            border-radius: 10px; overflow: hidden;
        }
        .quadro { position: relative; }
        svg { display: block; width: 100%; height: clamp(200px, 35vw, 430px); }
        svg.zoom { touch-action: none; cursor: grab; }
        svg.arrastando, svg.arrastando .regiao { cursor: grabbing; }
        .controles {
            position: absolute; top: 10px; right: 10px;
            display: grid; gap: 3px; text-align: center;
        }
        .controles button {
            min-width: 32px; min-height: 30px; color: #25423e; background: #fafdfe;
            border: 1px solid #c4d4d7; border-radius: 4px; font-size: 17px; cursor: pointer;
        }
        .controles button:disabled { opacity: .45; cursor: default; }
        .norte { font: 700 12px system-ui, sans-serif; color: #334e49; margin-bottom: 4px; }
        .legenda {
            display: flex; flex-wrap: wrap; gap: 8px 17px;
            list-style: none; margin: 0; padding: 9px 14px;
            background: #f9fbfa; border-top: 1px solid #cad9db;
            color: #344942; font: 12px system-ui, sans-serif;
        }
        .legenda li { display: inline-flex; align-items: center; gap: 7px; }
        .amostra { display: inline-block; width: 14px; box-sizing: border-box; }
        .limite { border-top: 1px solid #66796e; }
        .preenchimento { height: 9px; background: #a5d3c7; border: 1px solid #17675d; }
        .rio { border-top: 2px solid #609eb5; }
        .via { border-top: 2px solid #bb9868; }
        .reserva { height: 9px; background: #bbccab; }
        .urbano { height: 9px; background: #c4b5a3; }
        .rede { background: #203e38; width: 8px; height: 8px; border-radius: 50%; }
        .regiao { cursor: pointer; outline: none; }
        .regiao path { stroke: #66796e; stroke-width: .9; stroke-linejoin: round; }
        .regiao:hover path, .regiao:focus-visible path {
            fill: #c3ded5; stroke: #277c71; stroke-width: 1.7;
        }
        .regiao[aria-pressed="true"] path {
            fill: #a5d3c7; stroke: #17675d; stroke-width: 2.2;
        }
        text { fill: #213932; font-family: system-ui, sans-serif; }
        .nome { font-size: 13px; font-weight: 650; }
        .nome.ativa { fill: #064c43; font-weight: 750; }
        .toponimo { fill: #3c6d81; font-size: 10px; font-style: italic; letter-spacing: .1em; }
        .nome { paint-order: stroke; stroke: #fff; stroke-width: 1.6px; stroke-opacity: .75; }
    """,
    js="""
        export default function({ parentElement, data, setTriggerValue }) {
            const root = parentElement.querySelector(".territorio");
            const controls = parentElement.querySelector(".controles");
            const ns = "http://www.w3.org/2000/svg";
            const width = 860, height = 380;
            const layers = data.camadas;
            const sim = data.simulacao;  // { dist_original, dist_simulada, recomendacao, regiao_id } | null

            function draw(parent, tag, attrs, text) {
                const element = document.createElementNS(ns, tag);
                for (const [key, value] of Object.entries(attrs))
                    element.setAttribute(key, value);
                if (text) element.textContent = text;
                parent.append(element);
                return element;
            }

            const focusedId = root.getRootNode().activeElement?.getAttribute("data-id");
            root.replaceChildren();
            const svg = draw(root, "svg", {
                viewBox: `0 0 ${width} ${height}`, role: "group", "aria-label": "Mapa de regiões fictícias"
            });
            const map = draw(svg, "g", {});
            const xy = ([lon, lat]) => [18 + lon * 1340, 6 - lat * 940];
            const path = feature => {
                const { type, coordinates } = feature.geometry;
                const rings = type === "Polygon" ? coordinates : [coordinates];
                return rings.map(ring =>
                    "M " + ring.map(p => xy(p).join(" ")).join(" L ") + (type === "Polygon" ? " Z" : "")
                ).join(" ");
            };
            function layer(name, style, parent = map) {
                for (const feature of layers[name])
                    draw(parent, "path", { d: path(feature), ...style(feature.properties) });
            }
            const line = (stroke, width) => ({
                fill: "none", stroke, "stroke-width": width, "stroke-linejoin": "round",
                "stroke-linecap": "round", "vector-effect": "non-scaling-stroke"
            });
            layer("costa", () => line("#c9e2e8", 14));
            layer("terra", () => ({ fill: "#f2f1e8", stroke: "#99afb0", "stroke-width": .7 }));

            const palette = {
                central: "#e8e1d5", aurora: "#eddfcb", horizonte: "#dce8d9",
                vale_verde: "#dce8ce", esperanca: "#eee6cc", nova_uniao: "#e9ddd9"
            };
            let dragged = false;
            for (const feature of layers.regiao) {
                const { id, nome } = feature.properties;
                const selected = id === data.selecionada;
                const group = draw(map, "g", {
                    class: "regiao", role: "button", tabindex: 0, "data-id": id,
                    "aria-label": nome, "aria-pressed": selected
                });
                draw(group, "path", {
                    d: path(feature), fill: palette[id], "vector-effect": "non-scaling-stroke"
                });
                draw(group, "title", {}, data.tooltips[id]);
                const select = () => {
                    if (!selected) setTriggerValue("regiao", id);
                };
                group.addEventListener("click", event => {
                    if (event.detail === 0 || !dragged) select();
                });
                group.addEventListener("keydown", event => {
                    if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        select();
                    }
                });
                if (focusedId === id) group.focus();
            }

            const detail = draw(svg, "g", { "pointer-events": "none", "aria-hidden": "true" });
            layer("reserva", () => ({ fill: "#9bb685", opacity: .36 }), detail);
            layer("relevo", () => ({ ...line("#879c7e", .7), opacity: .46 }), detail);
            layer("urbano", () => ({ fill: "#b4a395", opacity: .47 }), detail);
            layer("costa", () => line("#759aa0", 1), detail);
            layer("rio", ({ nivel }) => ({ ...line("#609eb5", [.0, .65, 1, 1.6][nivel]), opacity: .87 }), detail);
            layer("via", ({ nivel }) => line("#faf6eb", nivel === 2 ? 2.9 : 1.8), detail);
            layer("via", ({ nivel }) => line(nivel === 2 ? "#bb9868" : "#b6a58d", nivel === 2 ? 1.1 : .6), detail);

            for (const feature of layers.toponimo) {
                const [x, y] = xy(feature.geometry.coordinates);
                draw(detail, "text", { x, y, class: "toponimo", "text-anchor": "middle" }, feature.properties.nome);
            }
            for (const feature of layers.regiao) {
                const { id, nome, rotulo } = feature.properties;
                const [x, y] = xy(rotulo);
                draw(detail, "text", {
                    x, y, class: id === data.selecionada ? "nome ativa" : "nome",
                    "text-anchor": "middle", "dominant-baseline": "central"
                }, nome.replace(/^Região /, ""));
            }

            // ---------------------------------------------------------------
            // Camada de infraestrutura (pointer-events: none para não bloquear cliques)
            // ---------------------------------------------------------------
            const infraLayer = draw(svg, "g", { "pointer-events": "none", "aria-hidden": "true" });

            // Marcador do backbone atual (fibra) — rotulado "Backbone atual"
            for (const feature of layers.fibra) {
                const [cx, cy] = xy(feature.geometry.coordinates);
                draw(infraLayer, "circle", { cx, cy, r: 5, fill: "#203e38", stroke: "#fff", "stroke-width": 1.7 });
                draw(infraLayer, "text", {
                    x: cx + 8, y: cy - 7,
                    fill: "#203e38", "font-size": "9", "font-weight": "600",
                    "font-family": "system-ui, sans-serif",
                    "paint-order": "stroke", stroke: "#fff", "stroke-width": "2px", "stroke-opacity": ".8"
                }, "Backbone atual");

                // ---------------------------------------------------------------
                // Camada de simulação (só quando sim != null e há região selecionada)
                // ---------------------------------------------------------------
                if (sim && data.selecionada) {
                    const distOrig = sim.dist_original;
                    const distSim = sim.dist_simulada;
                    const rec = sim.recomendacao;

                    // Cor do marcador simulado conforme recomendação
                    const corRec = {
                        "investir_agora": "#16a34a",
                        "realizar_piloto": "#2563eb",
                        "aguardar": "#ea580c",
                    }[rec] || "#6b7280";

                    // Ponto de referência da região selecionada (rótulo do GeoJSON)
                    let regiaoRotulo = null;
                    for (const feature of layers.regiao) {
                        if (feature.properties.id === data.selecionada) {
                            regiaoRotulo = feature.properties.rotulo;
                            break;
                        }
                    }

                    if (regiaoRotulo) {
                        const [rx, ry] = xy(regiaoRotulo);
                        // backbone atual = cx, cy

                        // Calcula posição do ponto simulado no segmento backbone → região
                        // proporção = 1 - nova_distancia / distancia_original
                        // Trata distância original zero sem divisão por zero
                        let proporcao = 0;
                        if (distOrig > 0) {
                            proporcao = 1 - distSim / distOrig;
                        }
                        // Clamp: 0..1
                        proporcao = Math.max(0, Math.min(1, proporcao));

                        const sx = cx + proporcao * (rx - cx);
                        const sy = cy + proporcao * (ry - cy);

                        // Só desenha seta se há aproximação (proporcao > 0)
                        // e distâncias são diferentes (evita marcador duplo quando igual)
                        const distanciasMudam = Math.abs(distSim - distOrig) > 0.001;

                        if (distanciasMudam && proporcao > 0) {
                            // Seta do backbone atual ao ponto simulado
                            const dx = sx - cx, dy = sy - cy;
                            const len = Math.sqrt(dx * dx + dy * dy);
                            if (len > 2) {
                                // Linha da seta
                                draw(infraLayer, "line", {
                                    x1: cx, y1: cy, x2: sx, y2: sy,
                                    stroke: corRec, "stroke-width": "1.5",
                                    "stroke-dasharray": "4 2",
                                    "marker-end": "url(#simArrow)"
                                });
                            }

                            // Marcador simulado
                            draw(infraLayer, "circle", {
                                cx: sx, cy: sy, r: 6,
                                fill: corRec, stroke: "#fff", "stroke-width": 1.7
                            });
                            draw(infraLayer, "text", {
                                x: sx + 9, y: sy - 8,
                                fill: corRec, "font-size": "9", "font-weight": "700",
                                "font-family": "system-ui, sans-serif",
                                "paint-order": "stroke", stroke: "#fff", "stroke-width": "2.5px", "stroke-opacity": ".9"
                            }, "Infraestrutura simulada");

                            // Etiqueta distância simulada
                            draw(infraLayer, "text", {
                                x: sx + 9, y: sy + 3,
                                fill: corRec, "font-size": "8", "font-weight": "600",
                                "font-family": "system-ui, sans-serif",
                                "paint-order": "stroke", stroke: "#fff", "stroke-width": "2px", "stroke-opacity": ".8"
                            }, `${distSim} km`);
                        }

                        // Etiqueta distância original no backbone atual
                        if (distanciasMudam) {
                            draw(infraLayer, "text", {
                                x: cx + 8, y: cy + 4,
                                fill: "#203e38", "font-size": "8", "font-weight": "600",
                                "font-family": "system-ui, sans-serif",
                                "paint-order": "stroke", stroke: "#fff", "stroke-width": "2px", "stroke-opacity": ".8"
                            }, `${distOrig} km`);
                        }
                    }
                }
            }

            // Define marcador de seta (defs SVG) para uso pelo marker-end
            const defs = document.createElementNS(ns, "defs");
            const marker = document.createElementNS(ns, "marker");
            marker.setAttribute("id", "simArrow");
            marker.setAttribute("markerWidth", "6");
            marker.setAttribute("markerHeight", "6");
            marker.setAttribute("refX", "5");
            marker.setAttribute("refY", "3");
            marker.setAttribute("orient", "auto");
            const arrowPath = document.createElementNS(ns, "path");
            arrowPath.setAttribute("d", "M0,0 L0,6 L6,3 z");
            arrowPath.setAttribute("fill", "context-stroke");
            marker.appendChild(arrowPath);
            defs.appendChild(marker);
            svg.insertBefore(defs, svg.firstChild);

            const view = JSON.parse(root.dataset.vista || '{"zoom":1,"x":0,"y":0}');
            const zoomIn = controls.querySelector('[data-zoom="in"]');
            const zoomOut = controls.querySelector('[data-zoom="out"]');
            const reset = controls.querySelector('[data-zoom="reset"]');
            function applyView() {
                view.x = Math.max(width * (1 - view.zoom), Math.min(0, view.x));
                view.y = Math.max(height * (1 - view.zoom), Math.min(0, view.y));
                map.setAttribute("transform", `translate(${view.x} ${view.y}) scale(${view.zoom})`);
                svg.classList.toggle("zoom", view.zoom > 1);
                zoomIn.disabled = view.zoom >= 3;
                zoomOut.disabled = reset.disabled = view.zoom <= 1;
                root.dataset.vista = JSON.stringify(view);
            }
            function zoom(factor) {
                const next = Math.min(3, Math.max(1, view.zoom * factor));
                const ratio = next / view.zoom;
                view.x = width / 2 - (width / 2 - view.x) * ratio;
                view.y = height / 2 - (height / 2 - view.y) * ratio;
                view.zoom = next;
                applyView();
            }
            zoomIn.onclick = () => zoom(1.35);
            zoomOut.onclick = () => zoom(1 / 1.35);
            reset.onclick = () => zoom(0);
            applyView();

            function pointer(event) {
                return new DOMPoint(event.clientX, event.clientY).matrixTransform(svg.getScreenCTM().inverse());
            }
            let drag = null;
            svg.addEventListener("pointerdown", event => {
                dragged = false;
                if (event.button !== 0 || view.zoom <= 1) return;
                const point = pointer(event);
                drag = { id: event.pointerId, point, x: view.x, y: view.y };
            });
            svg.addEventListener("pointermove", event => {
                if (drag?.id !== event.pointerId) return;
                const point = pointer(event);
                const dx = point.x - drag.point.x, dy = point.y - drag.point.y;
                if (!dragged && Math.hypot(dx, dy) < 4) return;
                if (!dragged) {
                    dragged = true;
                    svg.setPointerCapture(event.pointerId);
                    svg.classList.add("arrastando");
                }
                view.x = drag.x + dx;
                view.y = drag.y + dy;
                applyView();
            });
            function stopDrag(event) {
                if (drag?.id !== event.pointerId) return;
                drag = null;
                svg.classList.remove("arrastando");
            }
            svg.addEventListener("pointerup", stopDrag);
            svg.addEventListener("pointercancel", stopDrag);
            svg.addEventListener("pointerleave", event => {
                if (!dragged) stopDrag(event);
            });
        }
    """,
)

def renderizar_seletor_mapa(
    dados_regioes: dict[str, dict] | None = None,
    *,
    chart_key: str = "mapa_selector",
    camada_simulacao: dict | None = None,
    regiao_selecionada_id: str | None = None,
) -> str | None:
    """Renderiza o território e sincroniza a escolha entre as páginas.

    Args:
        dados_regioes: Dicionário de dados completos por região (para tooltips).
        chart_key: Chave do componente Streamlit.
        camada_simulacao: Dados para a camada de simulação. Quando fornecido pelo
            Simulador, deve conter ``dist_original``, ``dist_simulada`` e
            ``recomendacao``. ``None`` omite a camada (comportamento padrão para
            a página de Análise).
        regiao_selecionada_id: ID da região selecionada (opcional, sobrescreve
            sessão apenas para passagem explícita de dados ao mapa).
    """
    dados_geo = carregar_poligonos()
    nomes = {regiao["id"]: regiao["nome"] for regiao in dados_geo["regioes"]}
    tooltips = {}
    for regiao_id, nome in nomes.items():
        dados = (dados_regioes or {}).get(regiao_id, {})
        engenharia = dados.get("engenharia", {})
        distancia = engenharia.get("distancia_backbone_km")
        cobertura = engenharia.get("percentual_cobertura_fibra")
        populacao = dados.get("mercado", {}).get("populacao_estimada")
        detalhes = [nome]
        if distancia is not None:
            detalhes.append(f"Backbone a {distancia} km")
        if cobertura is not None:
            detalhes.append(f"Cobertura de fibra: {cobertura}%")
        if isinstance(populacao, int):
            detalhes.append(f"População estimada: {populacao:,}".replace(",", "."))
        tooltips[regiao_id] = "\n".join(detalhes)

    atual = regiao_selecionada()
    try:
        camadas = _carregar_geografia(_GEOJSON.stat().st_mtime_ns)
    except (OSError, KeyError, TypeError, ValueError, AttributeError):
        st.warning("A cartografia está indisponível. Selecione uma região pela lista.")
    else:
        def selecionar_no_mapa():
            evento = st.session_state.get(chart_key, {})
            novo = evento.get("regiao")
            if novo in nomes:
                st.session_state[_SESSION_KEY] = novo

        if atual in nomes:
            st.markdown(f"**{nomes[atual]}** selecionada · Clique em outra região para mudar.")
        else:
            st.markdown("**Clique em uma região para explorar**")
        _MAPA(
            data={
                "camadas": camadas,
                "selecionada": atual,
                "tooltips": tooltips,
                "simulacao": camada_simulacao,
            },
            key=chart_key,
            on_regiao_change=selecionar_no_mapa,
        )
    st.caption(dados_geo["aviso"])

    chave_lista = f"{chart_key}_lista"

    def selecionar_pela_lista():
        st.session_state[_SESSION_KEY] = st.session_state[chave_lista]

    st.session_state[chave_lista] = atual
    with st.expander("Selecionar pela lista"):
        st.selectbox(
            "Região",
            options=list(nomes),
            format_func=nomes.__getitem__,
            index=None,
            placeholder="Escolha uma região",
            key=chave_lista,
            on_change=selecionar_pela_lista,
        )

    return atual


def regiao_selecionada() -> str | None:
    """Retorna a região selecionada na sessão."""
    return st.session_state.get(_SESSION_KEY)
