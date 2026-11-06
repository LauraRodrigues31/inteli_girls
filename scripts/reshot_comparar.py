"""
Final re-shot Comparar: clicks by pixel coordinates on open dropdown options.
From debug screenshot: options list opens below the dropdown at ~y=421.
  - Região Aurora: ~y=463
  - Região Horizonte: ~y=502
  - Região Esperança: ~y=541
  - Região Central: ~y=580
  - Região Vale Verde: ~y=618
  - Região Nova União: ~y=657
"""
from playwright.sync_api import sync_playwright
import time
from pathlib import Path

BASE = "https://conecta-conselho.streamlit.app"
OUT  = Path("conecta-conselho/docs/prints")

PAGE_WAIT   = 15
ACTION_WAIT = 8

def log(msg): print(msg, flush=True)

def shoot(page, name):
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path), full_page=False)
    log(f"  ✔ {path.name}")

def go(page, path, wait=PAGE_WAIT):
    page.goto(f"{BASE}/{path}", wait_until="domcontentloaded", timeout=30_000)
    time.sleep(wait)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1.25,
        )
        page = ctx.new_page()

        log("=== Comparar Regiões Central × Nova União ===")
        go(page, "analise")

        # Click "Comparar Regiões" tab
        page.mouse.click(568, 302)
        time.sleep(ACTION_WAIT)
        log("  tab active")

        # ── Select Região A = Central ──────────────────────────────────
        # Open dropdown A (center of the A selectbox)
        page.mouse.click(547, 421)
        time.sleep(2)
        # "Região Central" option is at ~(547, 599) in the open menu
        page.mouse.click(547, 599)
        time.sleep(2)
        log("  Região A = Central (pixel click)")

        # ── Select Região B = Nova União ───────────────────────────────
        # Open dropdown B (center of the B selectbox, ~929, 421)
        page.mouse.click(929, 421)
        time.sleep(2)
        # "Região Nova União" option is at bottom of the list
        # The B dropdown opens at same y offset from B dropdown position
        # B dropdown top = 421, so options start at ~y=463 also but relative to B
        # B dropdown x center ≈ 929; options list left edge ≈ 752 (same width panel)
        # From the debug shot, the entire option panel is centered at x≈547 for A
        # For B, the panel should center at x≈929
        page.mouse.click(929, 676)  # "Região Nova União" row
        time.sleep(2)
        log("  Região B = Nova União (pixel click)")

        # Debug shot before clicking Comparar
        page.screenshot(path=str(OUT / "debug_comparar3.png"))
        log("  debug_comparar3 saved")

        # Click Comparar button (~1224, 424)
        page.mouse.click(1224, 424)
        time.sleep(ACTION_WAIT)
        log("  Comparar clicked")

        # Wait for results to render
        time.sleep(5)

        shoot(page, "print_comparar_central_nova_uniao")

        ctx.close()
        browser.close()

    log("Done.")

if __name__ == "__main__":
    main()
