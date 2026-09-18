"""Optional browser smoke test for a locally served documentation build.

Requires Playwright with Chromium; pass a local axe-core script for WCAG checks.
See docs/DESIGN.md for setup and usage.
"""

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8765/")
    parser.add_argument("--axe", type=Path)
    parser.add_argument("--output", type=Path, default=Path("docs/build/previews"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    base = args.url.rstrip("/") + "/"
    documents = ("index", "getting_started", "quickstart", "user_guide", "api")
    audits = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(permissions=["clipboard-read", "clipboard-write"])
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        for width in (320, 390, 768, 1024, 1440, 1920):
            page.set_viewport_size({"width": width, "height": 1000})
            for document in documents:
                page.goto(base + document + ".html")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (
                    width, document, "horizontal overflow"
                )
            print(f"Responsive layout passed: {width}px", flush=True)

        page.set_viewport_size({"width": 1440, "height": 1000})
        for theme in ("light", "dark"):
            for document in documents:
                page.goto(base + document + ".html")
                page.evaluate(
                    "theme => {localStorage.setItem('theme', theme); document.body.dataset.theme = theme}",
                    theme,
                )
                # Wait out native theme transitions before checking contrast.
                page.wait_for_timeout(250)
                if args.axe:
                    page.add_script_tag(path=str(args.axe))
                    result = page.evaluate("""async () => await axe.run({
                        runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa']}
                    })""")
                    audits.append({"page": document, "theme": theme, "violations": result["violations"]})
                    print(f"Accessibility: {document}, {theme}: {len(result['violations'])} violations", flush=True)
                if document == "index":
                    page.screenshot(path=str(args.output / f"desktop-{theme}.png"), full_page=True)
            page.goto(base + "index.html")
            page.locator(".theme-toggle-content button").click()
            assert page.evaluate("document.body.dataset.theme") != theme
            page.reload()
            assert page.evaluate("document.body.dataset.theme === localStorage.getItem('theme')")

        page.goto(base + "index.html")
        page.locator(".cerf-install-strip .copybtn").click()
        assert page.evaluate("navigator.clipboard.readText()").strip() == "pip install cerf"
        page.locator(".sidebar-search").fill("interconnection")
        page.locator(".sidebar-search").press("Enter")
        page.wait_for_selector(".search li a")
        assert page.locator(".search li a").count() > 0
        print("Search and clipboard passed", flush=True)

        page.goto(base + "getting_started.html")
        page.get_by_text("conda", exact=True).click()
        assert page.get_by_text("conda env create --file environment.yml", exact=False).first.is_visible()
        print("Installation tabs passed", flush=True)

        page.set_viewport_size({"width": 390, "height": 900})
        page.evaluate("localStorage.setItem('theme', 'light')")
        page.goto(base + "index.html")
        page.screenshot(path=str(args.output / "mobile-light.png"), full_page=True)
        page.locator(".nav-overlay-icon").click()
        assert page.locator("#__navigation").is_checked()
        page.locator(".sidebar-tree a").filter(has_text="Quickstart").first.click()
        assert page.url.endswith("quickstart.html")
        page.locator(".theme-toggle-header button").click()
        assert page.evaluate("document.body.dataset.theme") != "light"
        page.locator(".toc-header-icon").click()
        assert page.locator("#__toc").is_checked()
        print("Mobile navigation, table of contents, and theme controls passed", flush=True)

        # A keyboard user should reach the native skip link before the page UI.
        page.goto(base + "index.html")
        page.keyboard.press("Tab")
        assert page.locator(".skip-to-content").evaluate("e => e === document.activeElement")
        page.keyboard.press("Enter")
        assert page.url.endswith("#furo-main-content")
        page.emulate_media(reduced_motion="reduce", color_scheme="dark")
        page.evaluate("document.body.dataset.theme = 'auto'")
        assert page.locator(".index-card").first.evaluate("e => getComputedStyle(e).transitionDuration") == "0s"
        assert page.locator("body").evaluate("e => getComputedStyle(e).backgroundColor") == "rgb(20, 32, 29)"
        print("Keyboard skip link, reduced motion, and automatic dark mode passed", flush=True)
        assert not errors, errors
        browser.close()

    (args.output / "accessibility.json").write_text(json.dumps(audits, indent=2), encoding="utf-8")
    failures = [(audit["page"], audit["theme"], [v["id"] for v in audit["violations"]])
                for audit in audits if audit["violations"]]
    assert not failures, failures
    print("Browser checks passed.")


if __name__ == "__main__":
    main()
