"""
Captura prints definitivos do app https://conecta-conselho.streamlit.app
Zoom 125% (device_scale_factor=1.25), viewport 1440x900, headless Chromium.

O app precisa de ~3 min para acordar do cold start na primeira navegação.
Após isso, cada página carrega em ~10s.

Prints salvos em conecta-conselho/docs/prints/
"""
from playwright.sync_api import sync_playwright
import time
from pathlib import Path

BASE = "https://conecta-conselho.streamlit.app"
OUT  = Path("conecta-conselho/docs/prints")
OUT.mkdir(parents=True, exist_ok=True)

FIRST_WAIT = 185   # s — primeira página (cold start)
PAGE_WAIT  = 15    # s — páginas subsequentes
ACTION_WAIT = 8    # s — após clicar em aba/botão


def log(msg): print(msg, flush=True)


def shoot(page, name):
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path), full_page=False)
    log(f"  ✔ {path.name}")


def go_first(page, path):
    """Navega para a primeira página e aguarda o cold start."""
    log(f"  goto {BASE}/{path} (cold start — waiting {FIRST_WAIT}s)…")
    page.goto(f"{BASE}/{path}", wait_until="domcontentloaded", timeout=30_000)
    time.sleep(FIRST_WAIT)
    log("  cold start done")


def go(page, path, wait=PAGE_WAIT):
    """Navega para uma página (app já acordado)."""
    page.goto(f"{BASE}/{path}", wait_until="domcontentloaded", timeout=30_000)
    time.sleep(wait)


def try_tab(page, label):
    try:
        tab = page.get_by_role("tab", name=label, exact=False)
        if tab.count():
            tab.first.click()
            time.sleep(ACTION_WAIT)
            log(f"  tab '{label}' ok")
            return True
    except Exception as e:
        log(f"  warn tab '{label}': {e}")
    return False


def try_btn(page, label, wait=ACTION_WAIT):
    try:
        btn = page.get_by_role("button", name=label, exact=False)
        if btn.count():
            btn.first.click()
            time.sleep(wait)
            log(f"  btn '{label}' ok")
            return True
    except Exception as e:
        log(f"  warn btn '{label}': {e}")
    return False


def try_radio(page, label):
    try:
        el = page.get_by_text(label, exact=False)
        if el.count():
            el.first.click()
            time.sleep(3)
            log(f"  radio '{label}' ok")
            return True
    except Exception as e:
        log(f"  warn radio '{label}': {e}")
    return False


def click_map_region(page, region_name):
    """Tenta clicar no nome da região renderizado no mapa."""
    try:
        el = page.get_by_text(region_name, exact=True)
        if el.count():
            el.first.click()
            time.sleep(ACTION_WAIT)
            log(f"  map region '{region_name}' ok")
            return True
    except Exception as e:
        log(f"  warn map click '{region_name}': {e}")
    return False


def try_select(page, nth, option):
    try:
        boxes = page.locator('[data-testid="stSelectbox"]')
        if boxes.count() > nth:
            boxes.nth(nth).click()
            time.sleep(0.5)
            opt = page.get_by_role("option", name=option, exact=False)
            if opt.count():
                opt.first.click()
                time.sleep(3)
                log(f"  selectbox[{nth}] = '{option}'")
                return True
    except Exception as e:
        log(f"  warn selectbox[{nth}] '{option}': {e}")
    return False


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1.25,
        )
        page = ctx.new_page()

        # ── 1. Como funciona (cold start) ────────────────────────────────
        log("=== 1. Como funciona ===")
        go_first(page, "como-funciona")
        shoot(page, "print_como_funciona")

        # ── 2. Análise — mapa colorido ───────────────────────────────────
        log("=== 2. Análise — mapa colorido ===")
        go(page, "analise")
        shoot(page, "print_analise_mapa")

        # ── 3. Nova União — IBM ──────────────────────────────────────────
        log("=== 3. Nova União — IBM ===")
        try_radio(page, "IBM watsonx Orchestrate")
        click_map_region(page, "Nova União")
        shoot(page, "print_analise_nova_uniao_ibm")

        # ── 4. Central ──────────────────────────────────────────────────
        log("=== 4. Central ===")
        go(page, "analise")
        click_map_region(page, "Central")
        shoot(page, "print_analise_central")

        # ── 5. Comparar regiões ─────────────────────────────────────────
        log("=== 5. Comparar regiões Central × Nova União ===")
        go(page, "analise")
        if try_tab(page, "Comparar"):
            try_select(page, 0, "Central")
            try_select(page, 1, "Nova União")
            try_btn(page, "Comparar")
        shoot(page, "print_comparar_central_nova_uniao")

        # ── 6. Simulador — Esperança + mapa ─────────────────────────────
        log("=== 6. Simulador — Esperança + mapa ===")
        go(page, "simulador")
        try_btn(page, "Esperança")
        shoot(page, "print_simulador_esperanca_mapa")

        ctx.close()
        browser.close()

    log(f"\nDone. Prints em: {OUT.resolve()}")


if __name__ == "__main__":
    main()
