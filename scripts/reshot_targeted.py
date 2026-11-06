"""
Re-shot targeted: corrige print_como_funciona (fecha dialog), captura
Nova União clicado, Central clicado, Comparar aba.
Usa coordenadas de pixel baseadas nos screenshots anteriores.
"""
from playwright.sync_api import sync_playwright
import time
from pathlib import Path

BASE = "https://conecta-conselho.streamlit.app"
OUT  = Path("conecta-conselho/docs/prints")

PAGE_WAIT   = 15   # s após navegação (app já acordado)
ACTION_WAIT = 10   # s após clicar no mapa (aguarda análise carregar)

def log(msg): print(msg, flush=True)

def shoot(page, name):
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path), full_page=False)
    log(f"  ✔ {path.name}")

def go(page, path, wait=PAGE_WAIT):
    page.goto(f"{BASE}/{path}", wait_until="domcontentloaded", timeout=30_000)
    time.sleep(wait)

def close_dialog(page):
    """Fecha o modal 'Page not found' do Streamlit se estiver visível."""
    try:
        btn = page.locator('[data-testid="baseButton-headerNoPadding"]')
        if btn.count():
            btn.first.click()
            time.sleep(1)
            log("  dialog closed")
            return
        # Tenta qualquer botão X/close dentro de um dialog
        close = page.locator('button[aria-label="Close"]')
        if close.count():
            close.first.click()
            time.sleep(1)
            log("  dialog (aria-label=Close) closed")
            return
        # Fallback: pressiona Escape
        page.keyboard.press("Escape")
        time.sleep(0.5)
        log("  Escape pressed")
    except Exception as e:
        log(f"  warn close_dialog: {e}")

def click_tab(page, label):
    """Clica na aba pelo texto exato."""
    try:
        tab = page.get_by_role("tab", name=label, exact=False)
        if tab.count():
            tab.first.click()
            time.sleep(ACTION_WAIT)
            log(f"  tab '{label}' ok")
            return True
    except Exception as e:
        log(f"  warn tab '{label}': {e}")
    # Fallback: coordenada conhecida para "Comparar Regiões"
    # Na screenshot (viewport 1440x900): aba fica em ~x=568, y=302
    page.mouse.click(568, 302)
    time.sleep(ACTION_WAIT)
    log("  tab clicked by coordinate (568, 302)")
    return True

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
        log(f"  warn selectbox[{nth}]: {e}")
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

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1.25,
        )
        page = ctx.new_page()

        # ── 1-FIX. Como funciona — fechar dialog ─────────────────────────
        log("=== 1-FIX. Como funciona (fechar dialog) ===")
        # Navegar para analise primeiro para acordar o app, depois como-funciona
        go(page, "analise", wait=5)
        go(page, "como-funciona", wait=5)
        close_dialog(page)
        time.sleep(3)
        shoot(page, "print_como_funciona")

        # ── 3-FIX. Nova União — clicar no mapa por pixel ─────────────────
        # Da screenshot: mapa começa em ~y=383, height~430
        # "Nova União" label fica visualmente em ~(722, 686) no viewport 1440x900
        # Ajuste: o mapa no viewport com device_scale_factor=1.25 ocupa a mesma
        # área lógica, mas o mouse.click usa coords lógicas (sem fator de escala)
        log("=== 3-FIX. Análise Nova União (pixel click) ===")
        go(page, "analise")
        # Clicar aproximadamente no centro de Nova União
        # Coordenadas lógicas: x≈722, y≈686 (centro da região no mapa)
        page.mouse.click(722, 686)
        time.sleep(ACTION_WAIT)
        shoot(page, "print_analise_nova_uniao_ibm")

        # ── 4-FIX. Central — pixel click ─────────────────────────────────
        log("=== 4-FIX. Análise Central (pixel click) ===")
        go(page, "analise")
        # "Central" label fica em ~(847, 547)
        page.mouse.click(847, 547)
        time.sleep(ACTION_WAIT)
        shoot(page, "print_analise_central")

        # ── 5-FIX. Comparar Regiões ───────────────────────────────────────
        log("=== 5-FIX. Comparar Regiões Central × Nova União ===")
        go(page, "analise")
        click_tab(page, "Comparar")
        try_select(page, 0, "Central")
        try_select(page, 1, "Nova União")
        try_btn(page, "Comparar")
        shoot(page, "print_comparar_central_nova_uniao")

        ctx.close()
        browser.close()

    log(f"\nDone. Re-shots salvos em: {OUT.resolve()}")

if __name__ == "__main__":
    main()
