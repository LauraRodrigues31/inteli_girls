"""
Debug: open a Streamlit selectbox and dump the DOM to find the option elements.
"""
from playwright.sync_api import sync_playwright
import time
from pathlib import Path

BASE = "https://conecta-conselho.streamlit.app"
OUT  = Path("conecta-conselho/docs/prints")

def log(msg): print(msg, flush=True)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1.25,
        )
        page = ctx.new_page()

        page.goto(f"{BASE}/analise", wait_until="domcontentloaded", timeout=30_000)
        time.sleep(15)

        # Click "Comparar Regiões" tab
        page.mouse.click(568, 302)
        time.sleep(8)

        # Click Região A dropdown at (547, 421)
        page.mouse.click(547, 421)
        time.sleep(2)

        # Take screenshot with open dropdown
        page.screenshot(path=str(OUT / "debug_open_dropdown.png"))
        log("  debug_open_dropdown.png saved")

        # Dump all elements that might be dropdown options
        # Streamlit uses react-select which creates divs with role="option" or class containing "option"
        selectors_to_try = [
            '[role="option"]',
            '[class*="option"]',
            '[class*="menu"]',
            '[class*="Option"]',
            '[class*="select"]',
            'ul li',
            '[data-baseweb="select"] li',
            '[data-baseweb="menu"] li',
            '[data-baseweb="option"]',
        ]
        for sel in selectors_to_try:
            try:
                els = page.locator(sel)
                n = els.count()
                if n > 0:
                    log(f"  '{sel}' found {n} elements")
                    for i in range(min(n, 5)):
                        try:
                            log(f"    [{i}] text={els.nth(i).inner_text()[:50]!r}")
                        except:
                            pass
            except:
                pass

        # Also dump all aria attributes
        aria_dump = page.evaluate("""() => {
            const all = document.querySelectorAll('[aria-label], [aria-selected], [role]');
            return [...all].slice(0, 50).map(el => ({
                tag: el.tagName,
                role: el.getAttribute('role'),
                ariaLabel: el.getAttribute('aria-label'),
                ariaSelected: el.getAttribute('aria-selected'),
                text: el.innerText?.slice(0, 40)
            }));
        }""")
        log("aria dump:")
        for item in aria_dump:
            if item.get('role') in ('option', 'listbox', 'combobox', 'menu', 'menuitem') or item.get('ariaSelected'):
                log(f"  {item}")

        ctx.close()
        browser.close()

if __name__ == "__main__":
    main()
