"""
Gerador de ferramentas self-contained para o runtime IBM watsonx Orchestrate.

Uso:
    python scripts/gerar_ferramenta_nuvem.py <nome>

Nomes válidos: engenharia, mercado, social, orcamento, pontes

O que o gerador faz:
  1. Lê conecta-conselho/data/regioes.json e embute os dados relevantes como
     dicionário Python literal (sem dependência de arquivo externo).
  2. Embute as funções necessárias de consultar_regiao.py que a ferramenta usa,
     reescritas para ler do dicionário embutido em vez de um JSON em disco.
  3. Copia o corpo de tools/tool_<nome>.py removendo APENAS o bloco de
     sys.path/importlib e o import de consultar_regiao — toda a lógica de
     cálculo e o @tool são copiados inalterados.
  4. Salva o resultado em _build/tool_<nome>_nuvem.py com um cabeçalho que
     indica que o arquivo foi gerado automaticamente.

Por que gerar em vez de editar à mão:
  O runtime do watsonx Orchestrate (SaaS) executa cada ferramenta em um
  ambiente isolado sem acesso ao sistema de arquivos do desenvolvedor.
  Qualquer sys.path.insert ou from tools.consultar_regiao import falha
  com ModuleNotFoundError. A solução correta é embute os dados e as funções
  de consulta diretamente no arquivo da ferramenta.
  Gerar automaticamente a partir da fonte canônica (regioes.json +
  tool_<nome>.py) garante que a versão publicada na nuvem sempre reflita
  as mesmas regras que os testes locais validam.
"""

from __future__ import annotations

import ast
import json
import sys
import textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuração de caminhos
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).resolve().parent
_ROOT       = _SCRIPT_DIR.parent

_DATA_JSON  = _ROOT / "conecta-conselho" / "data" / "regioes.json"
_TOOLS_DIR  = _ROOT / "tools"
_BUILD_DIR  = _ROOT / "_build"

# Perspectiva de dados a usar para cada agente
_PERSPECTIVA: dict[str, str] = {
    "engenharia": "engenharia",
    "mercado":    "mercado",
    "social":     "social",
    "orcamento":  "financeiro",
    "pontes":     "parcerias",
}

# Funções extras além de consultar_<perspectiva> + _regiao_nao_encontrada
_FUNCOES_EXTRAS: dict[str, list[str]] = {
    "engenharia": [],
    "mercado":    [],
    "social":     ["listar_ids_regioes"],
    "orcamento":  [],
    "pontes":     ["listar_ids_regioes"],
}

_NOMES_VALIDOS = sorted(_PERSPECTIVA.keys())

# ---------------------------------------------------------------------------
# Dados embutidos
# ---------------------------------------------------------------------------

def _carregar_dados_regioes() -> dict:
    with open(_DATA_JSON, encoding="utf-8") as f:
        raw = json.load(f)
    return {r["id"]: r for r in raw["regioes"]}


def _repr_dados(regioes: dict, perspectiva: str) -> str:
    subset = {
        rid: {"id": rid, "nome": r["nome"], "dados": r[perspectiva]}
        for rid, r in regioes.items()
    }
    js = json.dumps(subset, ensure_ascii=False, indent=4)
    return js.replace(": true", ": True").replace(": false", ": False").replace(": null", ": None")


# ---------------------------------------------------------------------------
# Funções de consulta embutidas
# ---------------------------------------------------------------------------

def _gerar_listar_ids(regioes: dict) -> str:
    ids = sorted(regioes.keys())
    return textwrap.dedent(f"""\
        def listar_ids_regioes() -> list:
            \"\"\"Retorna a lista de IDs de regiões disponíveis.\"\"\"
            return {ids!r}
        """)


def _gerar_consultar(perspectiva: str) -> str:
    return textwrap.dedent(f"""\
        def _regiao_nao_encontrada(id_regiao: str) -> dict:
            regioes_ids = list(_REGIOES.keys())
            return {{
                "erro": "Região não encontrada",
                "id_consultado": id_regiao,
                "mensagem": (
                    f"Nenhuma região com id '{{id_regiao}}' foi encontrada na base de dados. "
                    f"IDs disponíveis: {{', '.join(regioes_ids)}}"
                ),
            }}


        def consultar_{perspectiva}(id_regiao: str) -> dict:
            \"\"\"Retorna os indicadores de {perspectiva} de uma região (dados embutidos).\"\"\"
            key = id_regiao.strip().lower()
            regiao = _REGIOES.get(key)
            if regiao is None:
                return _regiao_nao_encontrada(id_regiao)
            return {{
                "id":          regiao["id"],
                "nome":        regiao["nome"],
                "perspectiva": "{perspectiva}",
                "dados":       regiao["dados"],
            }}
        """)


# ---------------------------------------------------------------------------
# Extracção inteligente do corpo da ferramenta com AST
# ---------------------------------------------------------------------------

# Nomes de variáveis de importlib/path que devem ser removidos
_VARS_REMOVER = {
    "_CONSULTAR_PATH",
    "_consultar_regiao_path",
    "_spec",
    "_mod",
    "_ilu",
    "_CONECTA_CONSELHO_DIR",
    "_ROOT",
}

# Módulos que só existem para carregar consultar_regiao
_IMPORT_MODULOS_REMOVER = {"importlib.util", "importlib"}

# Nomes de funções/variáveis que vêm de consultar_regiao
_NOMES_CONSULTAR = {
    "consultar_engenharia", "consultar_mercado", "consultar_social",
    "consultar_financeiro", "consultar_parcerias",
    "listar_ids_regioes",
}


def _stmt_deve_remover(node: ast.stmt, src_lines: list[str]) -> bool:
    """Decide se um statement AST deve ser removido do arquivo gerado."""

    # from tools.consultar_regiao import ...
    if isinstance(node, ast.ImportFrom):
        mod = (node.module or "")
        if "consultar_regiao" in mod:
            return True

    # import importlib.util / import importlib.util as _ilu / import sys (quando usado só para path)
    if isinstance(node, ast.Import):
        for alias in node.names:
            if alias.name in _IMPORT_MODULOS_REMOVER:
                return True

    # from pathlib import Path  — só se Path não é usada depois
    # (não removemos Path aqui; tratamos no pós-processamento de imports)

    # Assign:  _CONSULTAR_PATH = (...), _spec = ..., _mod = ..., consultar_X = _mod.X
    if isinstance(node, (ast.Assign, ast.AugAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for t in targets:
            if isinstance(t, ast.Name) and t.id in _VARS_REMOVER:
                return True
            if isinstance(t, ast.Name) and t.id in _NOMES_CONSULTAR:
                return True

    # Expr (chamadas soltas): _spec.loader.exec_module(_mod)
    if isinstance(node, ast.Expr):
        src = "\n".join(src_lines[node.lineno - 1 : node.end_lineno])
        if "_spec.loader.exec_module" in src or "_ilu.spec_from_file_location" in src:
            return True

    # sys.path.insert(...)  como Expr  — func é sys.path.insert (Attribute de Attribute)
    if isinstance(node, ast.Expr):
        if isinstance(node.value, ast.Call):
            func = node.value.func
            # sys.path.insert → Attribute(value=Attribute(value=Name("sys"), attr="path"), attr="insert")
            if isinstance(func, ast.Attribute) and func.attr in ("insert", "append"):
                inner = func.value
                if isinstance(inner, ast.Attribute) and inner.attr == "path":
                    if isinstance(inner.value, ast.Name) and inner.value.id == "sys":
                        return True
            # sys.path (just the attribute, without .insert) — unlikely but safe
            if isinstance(func, ast.Attribute):
                src_frag = "\n".join(src_lines[node.lineno - 1 : node.end_lineno])
                if "sys.path" in src_frag and "consultar_regiao" not in src_frag:
                    if "_ROOT" in src_frag or "Path(__file__)" in src_frag or "_CONECTA_CONSELHO_DIR" in src_frag:
                        return True

    # If: if _CONECTA_CONSELHO_DIR not in sys.path:  sys.path.insert(...)
    if isinstance(node, ast.If):
        src = "\n".join(src_lines[node.lineno - 1 : node.end_lineno])
        if "_CONECTA_CONSELHO_DIR" in src and "sys.path" in src:
            return True

    # Assign: _ROOT = ...  ou _CONECTA_CONSELHO_DIR = ...
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id in {"_ROOT", "_CONECTA_CONSELHO_DIR"}:
                return True

    return False


def _extrair_corpo_ferramenta(nome: str) -> str:
    """
    Lê tools/tool_<nome>.py, remove usando AST os statements relativos
    ao carregamento de consultar_regiao, e devolve o código limpo.
    """
    src_path = _TOOLS_DIR / f"tool_{nome}.py"
    src = src_path.read_text(encoding="utf-8")
    src_lines = src.splitlines()

    tree = ast.parse(src)

    # Colecta ranges de linhas a remover (1-based, inclusive)
    remove_ranges: list[tuple[int, int]] = []
    for node in tree.body:
        if _stmt_deve_remover(node, src_lines):
            remove_ranges.append((node.lineno, node.end_lineno))

    # Marca linhas removidas
    removed = set()
    for start, end in remove_ranges:
        for ln in range(start, end + 1):
            removed.add(ln)

    # Reconstrói o código sem as linhas marcadas
    # Também remove comentários directamente antes de blocos removidos
    out_lines: list[str] = []
    for i, line in enumerate(src_lines, start=1):
        if i in removed:
            continue
        # Se a próxima linha (ou a actual) é um comentário explicativo sobre path/importlib
        stripped = line.strip()
        if stripped.startswith("#"):
            lower = stripped.lower()
            skip_phrases = [
                "sys.path", "importlib", "consultar_regiao", "conecta-conselho",
                "import robusto", "garante que conecta", "adiciona o dir",
                "pacote `tools/`", "funciona mesmo com hífen",
            ]
            if any(ph in lower for ph in skip_phrases):
                continue
        out_lines.append(line)

    # Remove a docstring do módulo original (será substituída pela nossa)
    result = "\n".join(out_lines)
    result = _remover_docstring_modulo(result)

    # Remove imports redundantes que já estarão no header gerado
    result = _limpar_imports_redundantes(result)

    return result


def _remover_docstring_modulo(code: str) -> str:
    """Remove a docstring de módulo (primeiro statement de string literal)."""
    lines = code.splitlines()
    i = 0
    # Pula linhas em branco iniciais
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    if i >= len(lines):
        return code
    stripped = lines[i].strip()
    if stripped.startswith('"""') or stripped.startswith("'''"):
        q = stripped[:3]
        # Verifica se é docstring de uma linha
        rest = stripped[3:]
        if rest.endswith(q) and len(rest) >= 3:
            return "\n".join(lines[i + 1:])
        # Multiline: encontra o fechamento
        for j in range(i + 1, len(lines)):
            if q in lines[j]:
                return "\n".join(lines[j + 1:])
    return code


def _limpar_imports_redundantes(code: str) -> str:
    """Remove imports que já estarão no header gerado."""
    redundantes = {
        "from __future__ import annotations",
        "import sys",
        "from pathlib import Path",
    }
    out = []
    for line in code.splitlines():
        if line.strip() in redundantes:
            continue
        out.append(line)
    return "\n".join(out)


def _colapsar_brancos(code: str, max_blanks: int = 2) -> str:
    out: list[str] = []
    blanks = 0
    for ln in code.splitlines():
        if ln.strip() == "":
            blanks += 1
            if blanks <= max_blanks:
                out.append(ln)
        else:
            blanks = 0
            out.append(ln)
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Montagem do arquivo final
# ---------------------------------------------------------------------------

_HEADER_TEMPLATE = """\
# ARQUIVO GERADO AUTOMATICAMENTE por scripts/gerar_ferramenta_nuvem.py — não editar à mão.
# Fonte: tools/tool_{nome}.py + conecta-conselho/data/regioes.json
# Para regenerar: python scripts/gerar_ferramenta_nuvem.py {nome}
\"\"\"
Ferramenta self-contained do Agente {titulo} — Conecta Conselho.

Esta versão embute os dados de conecta-conselho/data/regioes.json diretamente
como dicionário Python para ser compatível com o runtime em nuvem do IBM
watsonx Orchestrate, que não tem acesso ao sistema de arquivos local.

AVISO: Todos os dados são SIMULADOS e fictícios.
\"\"\"
from __future__ import annotations

import sys

"""


def _gerar_arquivo(nome: str) -> str:
    regioes     = _carregar_dados_regioes()
    perspectiva = _PERSPECTIVA[nome]
    extras      = _FUNCOES_EXTRAS[nome]

    # 1. Cabeçalho
    titulo = nome.replace("_", " ").title()
    header = _HEADER_TEMPLATE.format(nome=nome, titulo=titulo)

    # 2. Dados embutidos
    dados_repr = _repr_dados(regioes, perspectiva)
    dados_bloco = (
        "# ---------------------------------------------------------------------------\n"
        "# Dados embutidos — gerados de conecta-conselho/data/regioes.json\n"
        "# ---------------------------------------------------------------------------\n\n"
        f"_REGIOES: dict = {dados_repr}\n"
    )

    # 3. Funções de consulta
    consulta_bloco = (
        "\n# ---------------------------------------------------------------------------\n"
        "# Funções de consulta (embutidas — sem dependência de arquivo externo)\n"
        "# ---------------------------------------------------------------------------\n\n"
    )
    consulta_bloco += _gerar_consultar(perspectiva)
    if "listar_ids_regioes" in extras:
        consulta_bloco += "\n" + _gerar_listar_ids(regioes)

    # 4. Corpo da ferramenta (limpo)
    corpo = _extrair_corpo_ferramenta(nome)
    corpo = _colapsar_brancos(corpo.lstrip("\n"), max_blanks=2)

    # Validação de sintaxe antes de retornar
    full = header + dados_bloco + consulta_bloco + "\n\n" + corpo + "\n"
    try:
        ast.parse(full)
    except SyntaxError as e:
        raise RuntimeError(
            f"Erro de sintaxe no arquivo gerado para '{nome}' (linha {e.lineno}): {e.msg}\n"
            f"Contexte: {e.text}"
        ) from e

    return full


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def gerar(nome: str) -> Path:
    """Gera _build/tool_<nome>_nuvem.py e retorna o caminho."""
    if nome not in _NOMES_VALIDOS:
        raise ValueError(f"Nome inválido: {nome!r}. Válidos: {_NOMES_VALIDOS}")
    _BUILD_DIR.mkdir(exist_ok=True)
    saida = _BUILD_DIR / f"tool_{nome}_nuvem.py"
    saida.write_text(_gerar_arquivo(nome), encoding="utf-8")
    return saida


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in _NOMES_VALIDOS:
        print(f"Uso: python scripts/gerar_ferramenta_nuvem.py <nome>")
        print(f"Nomes válidos: {', '.join(_NOMES_VALIDOS)}")
        sys.exit(1)
    saida = gerar(sys.argv[1])
    print(f"[OK] Gerado: {saida}")


if __name__ == "__main__":
    main()
