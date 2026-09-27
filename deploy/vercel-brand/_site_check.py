# -*- coding: utf-8 -*-
"""GBT小土豆V8 · 品牌主页 · 合规机器判据（离线可跑，零第三方依赖除 flask 本身）

⛔ 开发者：自由的风 · 永久钢印 · 禁止删除

判据全部是「能证伪」的，不是自我感觉：

  P1  裸色值纪律    —— <style> 里 :root 之外不得出现裸 hex / rgb() / rgba() / hsl() / hsla()
  P2  三色引用纪律  —— --gbt-gold / --gbt-cyan / --gbt-violet 必须各自「定义 1 次 + 块外被引用 ≥1 次」
                       （R63 实测教训：三色都声明了，var(--gbt-violet) 全仓 0 命中 ⇒ 屏上少一色）
  P3  署名注入      —— 渲染结果必须含不可篡改署名行
  P4  品牌零残留    —— 渲染结果不得含外来品牌 / 官方模板字面量
  P5  资产在位      —— 品牌图必须真实存在于 api/assets/，且是真 PNG（查魔数）
  P6  路由可达      —— /  /api/status  /og.png  /healthz 四路实测状态码、头、内容

反盲对照（防 SCANNER_BLIND）：
  NC  负对照 —— 喂一份「明知含裸色值」的样本，P1 必须报 ≥1 处违规
  PC  正对照 —— 喂一份「明知干净」的样本，P1 必须报 0 处违规
  两者任一不成立 ⇒ 扫描器本身是瞎的，直接判死。
  不许把「读不到」当「读到了」；也不许把「没扫到」当「干净」。

退出码：0 = 全绿；1 = 有 FAIL。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
API_DIR = HERE / "api"
ASSETS = API_DIR / "assets"

# ── 判据常量 ────────────────────────────────────────────────────────────────
BRAND_TOKENS = ("--gbt-gold", "--gbt-cyan", "--gbt-violet")
SIGNATURE = "开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属"
BRAND_SLUG = "GBT-XiaoTuDou-V8"
FORBIDDEN = (
    "Codex",
    "Vercel + Flask",   # 官方模板页标题
    "Hello, World",
    "Genspark",
    "genspark",
)
REQUIRED_ASSETS = ("logo-256.png", "logo-512.png", "favicon-32.png")

BARE_COLOR = re.compile(
    r"#[0-9a-fA-F]{3,8}\b"
    r"|\brgba?\([^)]*\)"
    r"|\bhsla?\([^)]*\)"
)
CSS_COMMENT = re.compile(r"/\*.*?\*/", re.S)
ROOT_BLOCK = re.compile(r":root\s*\{[^}]*\}", re.S)
STYLE_BLOCK = re.compile(r"<style[^>]*>(.*?)</style>", re.S)
DATA_URI = re.compile(r"data:image/[a-z0-9.+-]+;base64,[A-Za-z0-9+/=]+")
# 允许的 CSS 颜色关键字：无彩度或继承语义，不算「裸色值」
ALLOW_KEYWORDS = ("transparent", "currentcolor", "inherit", "initial", "unset", "none")

_results: list[tuple[str, bool, str]] = []


def check(pid: str, ok: bool, detail: str) -> None:
    _results.append((pid, bool(ok), detail))


# ── 扫描核心（可独立喂样本，便于正负对照）────────────────────────────────────
def scan_bare_colors(css: str) -> list[str]:
    """返回 :root 块外所有裸色值出现处的上下文片段。"""
    css = CSS_COMMENT.sub(" ", css)          # 注释不渲染，先剔除，避免误报
    stripped = ROOT_BLOCK.sub(" ", css)      # 挖掉唯一定义处
    out = []
    for m in BARE_COLOR.finditer(stripped):
        frag = stripped[max(0, m.start() - 34): m.end() + 12].replace("\n", " ")
        out.append("%s   …%s…" % (m.group(0), frag.strip()))
    return out


def count_refs(css: str, token: str) -> tuple[int, int]:
    """返回 (总引用数, :root 块外的引用数)。"""
    total = len(re.findall(r"var\(\s*%s\s*[,)]" % re.escape(token), css))
    outside = len(re.findall(
        r"var\(\s*%s\s*[,)]" % re.escape(token), ROOT_BLOCK.sub(" ", css)))
    return total, outside


# ── 主流程 ──────────────────────────────────────────────────────────────────
def main() -> int:
    sys.path.insert(0, str(HERE))
    try:
        from api import index as site  # noqa: WPS433
    except Exception as exc:  # pragma: no cover
        print("[FATAL] 无法 import api.index：%r" % (exc,))
        print("        本地需先 pip install -r requirements.txt")
        return 1

    page = site.PAGE
    styles = STYLE_BLOCK.findall(page)
    css = "\n".join(styles)

    print("=" * 78)
    print("GBT小土豆V8 · 品牌主页 · 合规机器判据")
    print("=" * 78)
    print("站点常量：brand=%s  cap=%s  version=%s" % (site.BRAND, site.CAP, site.VERSION))
    print("被测文件：%s  (%d 字节)" % (API_DIR / "index.py", (API_DIR / "index.py").stat().st_size))
    print("样式块数：%d   样式总长：%d" % (len(styles), len(css)))
    print("-" * 78)

    # ── 反盲对照（必须先做：如果扫描器是瞎的，后面所有「绿」都是假的）──
    nc_sample = ":root{--x:#111}\n.a{color:#FF0000;background:rgba(1,2,3,.5)}"
    nc_hits = scan_bare_colors(nc_sample)
    pc_sample = ":root{--x:#111;--gbt-gold:#F5B041}\n.a{color:var(--x);background:var(--gbt-gold)}"
    pc_hits = scan_bare_colors(pc_sample)
    check("NC", len(nc_hits) >= 2, "负对照：3 个裸色值中应至少抓到 2 个，实抓 %d 个" % len(nc_hits))
    check("PC", len(pc_hits) == 0, "正对照：干净样本应报 0 处，实报 %d 处" % len(pc_hits))
    blind = not (len(nc_hits) >= 2 and len(pc_hits) == 0)
    if blind:
        print("!! SCANNER_BLIND —— 扫描器自证失败，后续结论一律不可信。")
        for pid, ok, d in _results:
            print("   [%s] %s  %s" % ("OK " if ok else "FAIL", pid, d))
        return 1
    print("[OK  ] 反盲对照  NC=%d 命中 / PC=0 命中  —— 扫描器不是瞎的" % len(nc_hits))

    # ── P1 裸色值纪律 ──
    bad = scan_bare_colors(css)
    if bad:
        check("P1", False, "裸色值 %d 处（:root 之外）：\n      - %s"
              % (len(bad), "\n      - ".join(bad[:12])))
    else:
        roots = ROOT_BLOCK.findall(css)
        check("P1", True, "裸色值 0 处；:root 唯一定义块 %d 个" % len(roots))

    # ── P2 三色引用纪律 ──
    lines = []
    p2_ok = True
    for tk in BRAND_TOKENS:
        defs = len(re.findall(re.escape(tk) + r"\s*:", css))
        total, outside = count_refs(css, tk)
        good = defs == 1 and outside >= 1
        p2_ok &= good
        lines.append("%s 定义=%d 引用=%d（块外=%d）%s"
                     % (tk, defs, total, outside, "" if good else "  ← 不达标"))
    check("P2", p2_ok, "三色定义与引用：\n      " + "\n      ".join(lines))

    # ── 资产在位（先查，渲染要用到）──
    asset_lines, asset_ok = [], True
    for name in REQUIRED_ASSETS:
        p = ASSETS / name
        if not p.is_file():
            asset_ok = False
            asset_lines.append("%s 缺失" % name)
            continue
        raw = p.read_bytes()
        head = raw[:8]
        is_png = head == b"\x89PNG\r\n\x1a\n"
        asset_ok &= is_png
        alpha = ""
        if len(raw) > 26 and raw[12:16] == b"IHDR":
            ct = raw[25]  # 色彩类型：0=灰度 2=RGB 3=调色板 4=带alpha灰度 6=RGBA
            alpha = " colorType=%d %s" % (
                ct, {0: "(灰度·不透明)", 2: "(RGB·不透明)", 3: "(调色板)",
                     4: "(灰度+alpha)", 6: "(RGBA·带alpha)"}.get(ct, "(未知)"))
            # 暗色站要求透明底：色彩类型必须带 alpha 通道（4 或 6）
            if ct not in (4, 6):
                asset_ok = False
                alpha += " ← 无 alpha 通道，暗底页会出白/黑块"
        asset_lines.append("%s  %8d B  PNG=%s%s" % (name, len(raw), is_png, alpha))
    check("P5", asset_ok, "品牌资产：\n      " + "\n      ".join(asset_lines))

    # ── 渲染四路 ──
    client = site.app.test_client()

    r_home = client.get("/")
    html = r_home.get_data(as_text=True)
    # data URI 是二进制转写，剔除后再做文本判据，避免偶然命中
    text = DATA_URI.sub("«data-uri»", html)

    home_ok = (r_home.status_code == 200
               and "text/html" in r_home.headers.get("Content-Type", "")
               and r_home.headers.get("X-GBT-Brand") == BRAND_SLUG
               and site.BRAND in text)
    check("P6a", home_ok, "/  → %d  Content-Type=%s  X-GBT-Brand=%s  含品牌名=%s"
          % (r_home.status_code, r_home.headers.get("Content-Type"),
             r_home.headers.get("X-GBT-Brand"), site.BRAND in text))

    # ── P3 署名 ──
    check("P3", SIGNATURE in text, "署名行注入：%s" % ("命中" if SIGNATURE in text else "未命中"))

    # ── P4 品牌零残留 ──
    hits = [w for w in FORBIDDEN if w in text]
    check("P4", not hits, "外来品牌/模板字面量：%s" % ("0 处" if not hits else "命中 %s" % hits))

    # ── P6 其余三路 ──
    r_st = client.get("/api/status")
    st_ok = r_st.status_code == 200
    try:
        sj = r_st.get_json() or {}
        st_ok &= bool(sj.get("ok")) and sj.get("brand") == site.BRAND
        st_detail = json.dumps(sj, ensure_ascii=False)[:150]
    except Exception as exc:
        st_ok = False
        st_detail = "JSON 解析失败 %r" % (exc,)
    check("P6b", st_ok, "/api/status → %d  %s" % (r_st.status_code, st_detail))

    r_og = client.get("/og.png")
    og_ok = (r_og.status_code == 200
             and r_og.get_data()[:8] == b"\x89PNG\r\n\x1a\n"
             and r_og.headers.get("Content-Type") == "image/png")
    check("P6c", og_ok, "/og.png → %d  Content-Type=%s  %d B  PNG魔数=%s"
          % (r_og.status_code, r_og.headers.get("Content-Type"),
             len(r_og.get_data()), r_og.get_data()[:8] == b"\x89PNG\r\n\x1a\n"))

    r_hz = client.get("/healthz")
    hz_ok = r_hz.status_code == 200 and bool((r_hz.get_json() or {}).get("ok"))
    check("P6d", hz_ok, "/healthz → %d  %s" % (r_hz.status_code, r_hz.get_data(as_text=True)[:90]))

    # ── 报告 ──
    print("-" * 78)
    for pid, ok, detail in _results:
        print("[%s] %-4s %s" % ("OK  " if ok else "FAIL", pid, detail))
    fails = [pid for pid, ok, _ in _results if not ok]
    print("-" * 78)
    if fails:
        print("结论：FAIL —— %d 项不达标：%s" % (len(fails), ", ".join(fails)))
        return 1
    print("结论：ALL PASS —— %d 项判据全绿，站点可以上。" % len(_results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
