# gbt-capability: browser
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""browser 能力 — 真实浏览器自动化（标准库 webbrowser + 可选自动化后端）。

三级后端，如实降级：
1. open/search（webbrowser 标准库）：打开 URL / 默认浏览器搜索——零依赖真执行
2. fetch（urllib）：无头抓取页面文本（静态内容）——零依赖真执行
3. automate（Playwright/Selenium）：未安装时如实返回 needs_dependency + 安装指引
"""
from __future__ import annotations

import json
import os
import re
import urllib.request


def open_url(url):
    """用系统默认浏览器打开 URL（真实执行）。"""
    if not url:
        raise ValueError("缺少 url")
    if not re.match(r"^https?://", url):
        url = "https://" + url
    import webbrowser
    ok = webbrowser.open(url)
    return {"ok": bool(ok), "action": "open", "url": url,
            "backend": "system-default-browser"}


def search(query, engine="bing"):
    """用系统默认浏览器搜索（真实执行）。"""
    if not query:
        raise ValueError("缺少 query")
    engines = {
        "bing": "https://www.bing.com/search?q=",
        "baidu": "https://www.baidu.com/s?wd=",
        "google": "https://www.google.com/search?q=",
        "duckduckgo": "https://duckduckgo.com/?q=",
    }
    if engine not in engines:
        raise ValueError(f"未知引擎: {engine}（可用: {'/'.join(engines)}）")
    import urllib.parse
    import webbrowser
    url = engines[engine] + urllib.parse.quote_plus(query)
    ok = webbrowser.open(url)
    return {"ok": bool(ok), "action": "search", "engine": engine,
            "query": query, "url": url, "backend": "system-default-browser"}


def fetch(url, timeout=20, max_chars=20000):
    """无头抓取页面（静态内容，标准库真实执行；动态渲染需 automate 后端）。"""
    if not url:
        raise ValueError("缺少 url")
    if not re.match(r"^https?://", url):
        url = "https://" + url
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GBT-V8/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
        text = raw.decode(charset, errors="replace")
        # 粗提正文：去 script/style/tag
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return {"ok": True, "action": "fetch", "url": url, "status": "fetched",
                "chars": len(text), "text": text[:max_chars],
                "note": "静态抓取；动态渲染页面请用 op=automate（需 Playwright）"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "action": "fetch", "url": url, "error": str(e)[:200]}


def automate(op="status", **params):
    """浏览器自动化（需 Playwright）。

    未安装时如实返回 needs_dependency + 安装指引，不伪造自动化结果。
    """
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        installed = True
    except Exception:
        installed = False
    if not installed:
        return {"ok": False, "status": "needs_dependency",
                "missing": "playwright",
                "install": "python -m pip install playwright && python -m playwright install chromium",
                "note": "open/search/fetch 已可用（标准库）；自动化需安装 Playwright"}
    # 已安装 → 真实自动化
    from playwright.sync_api import sync_playwright
    act = params.get("act", "goto")
    url = params.get("url", "https://www.bing.com")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=bool(params.get("headless", True)))
        page = browser.new_page()
        try:
            page.goto(url, timeout=30000)
            if act == "goto":
                title = page.title()
                return {"ok": True, "backend": "playwright", "url": url, "title": title}
            if act == "text":
                return {"ok": True, "backend": "playwright", "url": url,
                        "text": page.inner_text("body")[:20000]}
            if act == "click":
                sel = params.get("selector")
                if not sel:
                    raise ValueError("click 需要 selector")
                page.click(sel)
                return {"ok": True, "backend": "playwright", "clicked": sel,
                        "url_after": page.url}
            if act == "type":
                sel, val = params.get("selector"), params.get("value", "")
                if not sel:
                    raise ValueError("type 需要 selector")
                page.fill(sel, val)
                return {"ok": True, "backend": "playwright", "filled": sel}
            if act == "screenshot":
                out = params.get("out", "store/vision/browser_shot.png")
                page.screenshot(path=out)
                return {"ok": True, "backend": "playwright", "screenshot": out}
            raise ValueError(f"未知 act: {act}（可用: goto/text/click/type/screenshot）")
        finally:
            browser.close()


def run(op="open", **params):
    """browser 统一入口：open/search/fetch（标准库）/ automate（需 Playwright）。"""
    if op in ("open", "goto", None):
        return open_url(params.get("url"))
    if op == "search":
        return search(params.get("query"), params.get("engine", "bing"))
    if op == "fetch":
        return fetch(params.get("url"), int(params.get("timeout", 20)),
                     int(params.get("max_chars", 20000)))
    if op == "automate":
        return automate(**params)
    if op == "status":
        try:
            import playwright  # noqa: F401
            auto = "playwright（已安装）"
        except Exception:
            auto = "needs_dependency（python -m pip install playwright）"
        return {"ok": True, "open_search_fetch": "标准库（可用）", "automate": auto}
    raise ValueError(f"未知 op: {op}（可用: open/search/fetch/automate/status）")
