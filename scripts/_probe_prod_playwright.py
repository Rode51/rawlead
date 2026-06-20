"""Playwright prod smoke for doc sync — visible text only."""
from playwright.sync_api import sync_playwright

PAGES = [
    ("home", "https://rawlead.ru/"),
    ("lenta", "https://rawlead.ru/lenta/"),
    ("pricing", "https://rawlead.ru/pricing/"),
    ("quiz", "https://rawlead.ru/quiz/"),
    ("cabinet", "https://rawlead.ru/cabinet/"),
]

OUT = r"C:\Users\hramo\uisness\data\prod_ui_probe.json"


def visible_text(page) -> str:
    return page.evaluate(
        """() => {
        const walk = (el) => {
          if (!el) return '';
          const st = getComputedStyle(el);
          if (st.display === 'none' || st.visibility === 'hidden' || el.hidden) return '';
          if (el.getAttribute('aria-hidden') === 'true') return '';
          let t = '';
          for (const n of el.childNodes) {
            if (n.nodeType === Node.TEXT_NODE) t += n.textContent + ' ';
            else if (n.nodeType === Node.ELEMENT_NODE) t += walk(n);
          }
          return t;
        };
        return walk(document.body).replace(/\\s+/g, ' ').trim();
    }"""
    )


def main() -> None:
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1280, "height": 900}, locale="ru-RU")
        page = ctx.new_page()
        for name, url in PAGES:
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(2000)
            text = visible_text(page)
            h1 = page.locator("h1:visible").all_text_contents()
            vers = page.evaluate(
                """() => [...document.querySelectorAll('link[href*=\"ver=\"],script[src*=\"ver=\"]')]
                .map(n => (n.href||n.src).match(/ver=([0-9.]+)/)?.[1]).filter(Boolean)"""
            )
            results[name] = {
                "url": url,
                "title": page.title(),
                "h1_visible": h1,
                "asset_versions": sorted(set(vers)),
                "has_skill_tree_visible": "Выбрано" in text and "Навыки" in text,
                "has_quiz_overlay_dom": page.locator("#rl-feed-quiz-overlay").count() > 0,
                "text_sample": text[:2500],
            }
            if name == "lenta":
                try:
                    page.locator("#rl-feed-skills-trigger").click(timeout=8000)
                    page.wait_for_timeout(800)
                    modal_text = visible_text(page)
                    results["lenta_skills_modal"] = {
                        "open": "Выбрано" in modal_text,
                        "sample": modal_text[:1200],
                    }
                except Exception as exc:
                    results["lenta_skills_modal"] = {"error": str(exc)}
        browser.close()
    import json

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("wrote", OUT)
    for k, v in results.items():
        if isinstance(v, dict) and "h1_visible" in v:
            print(k, "|", v.get("h1_visible"), "| ver", v.get("asset_versions"))


if __name__ == "__main__":
    main()
