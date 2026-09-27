# -*- coding: utf-8 -*-
"""GBT小土豆V8 · 品牌主页（Vercel + Flask）

⛔ 开发者：自由的风 · 永久钢印 · 禁止删除

部署目标：https://www.gbtv8.com
形态：单页品牌站。Flask 服务端渲染，零外部依赖（不引任何 CDN / 网络字体）。

品牌纪律（出处 `memory/2026-09-22-品牌与Logo不丢.md` §2.1，两条硬纪律）：
  ① 裸色值只允许出现在 `:root` 的 token 定义块里，块外一律 `var(--gbt-*)`；
  ② 三色 token 声明了就必须被引用 —— R63 实测教训：三色都声明了，
     `var(--gbt-violet)` 全仓 0 命中，屏上只出了金 + 青两色。声明没人用 = 少一色。
本文件由 `_site_check.py` 用机器判据守着（含正负对照，扫描器读不到不许当读到）。

关于 Logo：真资产来自 `assets/brand/`，**运行时读盘 + base64 内嵌**，不依赖静态路径。
"""
from __future__ import annotations

import base64
import json
import os
import platform
import time
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from flask import Flask, Response, jsonify, request

BRAND = "GBT小土豆V8"
BRAND_SLUG = "GBT-XiaoTuDou-V8"
CAP = "gbt-v8-brand-site"
VERSION = "1.0.0"
SIGNATURE = "开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属"

_DAILY = ("#F5B041", "#00E5FF", "#7C4DFF")

_HERE = Path(__file__).resolve().parent
_ASSETS = _HERE / "assets"
_BOOT_TS = time.time()
_BOOT_ISO = datetime.now(timezone.utc).isoformat(timespec="seconds")


@lru_cache(maxsize=8)
def _b64(name: str) -> str:
    """把品牌图读成 data URI。读不到就返回空串 —— 缺失如实呈现，不伪造。"""
    p = _ASSETS / name
    if not p.is_file():
        return ""
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode("ascii")


# ── 能力矩阵（每条都对应仓里真实存在的模块，不写没做的东西）─────────────
CAPABILITIES = [
    {
        "k": "KEY GATEWAY",
        "t": "统一密钥网关",
        "d": "全部上游通道声明在一处，运行时逐次打分排序。额度、冷却、健康度都可回放；"
             "出站密钥只在内存里，库里只存 blake2b 摘要。",
        "m": ["11 条通道声明", "摘要不存明文", "选路每次现算"],
    },
    {
        "k": "SELF-HEALING",
        "t": "额度感知自愈",
        "d": "429 / 402 / 5xx 自动换道；400 / 422 硬停不换道 —— 把参数缺陷留给人看，"
             "不让它伪装成「模型不行」。每条通道预留 20% 储备，不榨干。",
        "m": ["换道不换钥匙", "I2 硬停保护", "20% 储备纪律"],
    },
    {
        "k": "TENTACLE",
        "t": "触手原生视觉",
        "d": "三级后端如实降级：本地 PIL 像素级分析 → dxcam 截屏 → 云端识别。"
             "没配就是没配，读不到就报缺 —— 不假装看见了。",
        "m": ["零依赖像素级", "三级如实降级", "区域网格读数"],
    },
    {
        "k": "Y-PORT",
        "t": "多模态 Y 字端口",
        "d": "左臂一条维度一条专属密钥，右臂一对共享密钥按维度复用。"
             "七道闸全过才成立，同指纹直接判定为假冗余。",
        "m": ["维度在册", "指纹去重", "明文不出返回值"],
    },
    {
        "k": "MIRROR SPACE",
        "t": "镜像多维度空间",
        "d": "唯一试验场。排练、仿真、门禁全过才晋升；生产树按护照比对，"
             "只收成品 —— 生产面不接受半成品。",
        "m": ["护照式晋升", "全量替换语义", "扫描器 5/5 全绿"],
    },
    {
        "k": "AGENTS",
        "t": "多智能体协作",
        "d": "能力矩阵化、模块边界写死，按数据流编排而不是堆数量。"
             "每个角色只答自己那一格，越界即报错。",
        "m": ["边界明确", "按流编排", "拒绝空调用"],
    },
]

ARCH = [
    ("01", "密钥源层", "只回答「有没有可用密钥」，返回指纹不返回明文"),
    ("02", "能源账本层", "用量 / 健康度 / 冷却 / 当日耗尽，落盘可回放，损坏从零起"),
    ("03", "通道层", "声明有哪条路、额度多少、要花多久、支不支持视觉"),
    ("04", "选路执行层", "打分排序 → 试 → 按错误分类降级 → 记账 → 回切"),
    ("05", "自检层", "离线可跑。扫描器读不到就报 blind，不许把读不到当读到了"),
]

PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>@@BRAND@@ · 能力中枢</title>
<meta name="description" content="@@BRAND@@ 是一套自建的 AI 能力中枢：统一密钥网关托管全部通道，额度耗尽自动换道；触手原生视觉补齐读图能力；镜像多维度空间做试验场，生产只收成品。">
<meta name="author" content="自由的风">
<meta name="theme-color" content="#04060E">
<meta property="og:type" content="website">
<meta property="og:title" content="@@BRAND@@ · 能力中枢">
<meta property="og:description" content="让每一条 AI 通道都有备份，让每一次调用都有交代。">
<meta property="og:image" content="@@OGURL@@">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="@@FAVICON@@">
<link rel="apple-touch-icon" href="@@FAVICON@@">
<style>
/* ── 令牌：品牌三色在此唯一定义，块外一律 var() ─────────────────────────
   纪律 ①：裸色值只允许出现在本 :root 块里。
   纪律 ②：--gbt-gold / --gbt-cyan / --gbt-violet 声明了就必须被引用，
          否则就是「声明没人用 = 屏上少一色」。 */
:root{
  /* 品牌三色（白皮书唯一定义处） */
  --gbt-gold:#F5B041;    /* 土豆金 */
  --gbt-cyan:#00E5FF;    /* 赛博青 */
  --gbt-violet:#7C4DFF;  /* 深空紫 */

  /* 底色与结构 */
  --void:#04060E; --deep:#070B18; --panel:#0A0F20; --panel-2:#0D1428;
  --line:rgba(124,77,255,.26); --line-hot:rgba(0,229,255,.42);
  --line-faint:rgba(147,160,192,.14);

  /* 文本 */
  --ink:#E8ECF8; --ink-2:#93A0C0; --ink-3:rgba(147,160,192,.62);

  /* 光晕与渐变（原为块外裸值，一并提为 token） */
  --glow-cyan:rgba(0,229,255,.20);   --glow-violet:rgba(124,77,255,.24);
  --glow-gold:rgba(245,176,65,.22);
  --grid-line:rgba(0,229,255,.035);
  --scrim:rgba(2,4,10,.72);
  --tint-cyan:rgba(0,229,255,.06);   --tint-violet:rgba(124,77,255,.07);
  --grad-brand:linear-gradient(90deg,var(--gbt-violet),var(--gbt-cyan),var(--gbt-gold));
  --ok:#22C55E; --fault:#EF4444;
  /* 纪律 ① 补全：下面两条原为块外裸色值，一律提为 token，块外只许 var() */
  --mask-solid:#000;                 /* 遮罩不透明端点 */
  --shadow-card:rgba(4,6,14,.6);     /* 卡片悬浮投影 */

  /* 排印与形状 */
  --mono:"SF Mono","JetBrains Mono","Cascadia Mono",Consolas,"DejaVu Sans Mono",monospace;
  --sans:"SF Pro Display",-apple-system,BlinkMacSystemFont,"Segoe UI Variable Display","Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
  --r-sm:8px; --r-md:14px; --r-lg:20px;
  --t:200ms cubic-bezier(.16,1,.3,1);
}
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  background:var(--void); color:var(--ink); font-family:var(--sans);
  font-size:15px; line-height:1.65; -webkit-font-smoothing:antialiased;
  min-height:100vh; overflow-x:hidden;
}
/* 赛博网格底 */
body::before{
  content:""; position:fixed; inset:0; z-index:0; pointer-events:none;
  background-image:linear-gradient(var(--grid-line) 1px,transparent 1px),
                   linear-gradient(90deg,var(--grid-line) 1px,transparent 1px);
  background-size:52px 52px;
  mask-image:radial-gradient(ellipse 90% 60% at 50% 0%,var(--mask-solid) 20%,transparent 75%);
  -webkit-mask-image:radial-gradient(ellipse 90% 60% at 50% 0%,var(--mask-solid) 20%,transparent 75%);
}
/* 顶部光晕：紫 + 青 */
body::after{
  content:""; position:fixed; top:-360px; left:50%; transform:translateX(-50%);
  width:1100px; height:620px; z-index:0; pointer-events:none; border-radius:50%;
  background:radial-gradient(circle at 35% 55%,var(--glow-violet),transparent 62%),
             radial-gradient(circle at 66% 48%,var(--glow-cyan),transparent 60%);
  filter:blur(28px);
}
.wrap{position:relative; z-index:1; max-width:1180px; margin:0 auto; padding:0 26px}
a{color:inherit;text-decoration:none}

/* ── 顶栏 ───────────────────────────────────────────────────── */
.top{
  position:sticky; top:0; z-index:20;
  backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px);
  background:var(--scrim); border-bottom:1px solid var(--line-faint);
}
.top .wrap{display:flex; align-items:center; gap:14px; height:66px}
.logo{width:36px;height:36px;flex:none;display:block;filter:drop-shadow(0 0 10px var(--glow-cyan))}
.brand b{display:block;font-size:15px;font-weight:650;letter-spacing:.01em;color:var(--gbt-gold)}
.brand span{display:block;font-family:var(--mono);font-size:9.5px;letter-spacing:.19em;color:var(--ink-3);text-transform:uppercase}
.spacer{flex:1}
.nav{display:flex;gap:4px}
.nav a{
  padding:8px 13px;border-radius:var(--r-sm);font-size:13.5px;color:var(--ink-2);
  transition:color var(--t),background var(--t);
}
.nav a:hover{color:var(--gbt-cyan);background:var(--tint-cyan)}
.live{
  display:flex;align-items:center;gap:8px;height:32px;padding:0 13px;
  border:1px solid var(--line);border-radius:100px;
  font-family:var(--mono);font-size:11.5px;color:var(--ink-2);
  background:var(--tint-violet);
}
.dot{width:7px;height:7px;border-radius:50%;background:var(--ink-3);box-shadow:0 0 0 0 transparent;transition:background var(--t),box-shadow var(--t)}
.live[data-s="ok"] .dot{background:var(--ok);box-shadow:0 0 9px var(--ok)}
.live[data-s="bad"] .dot{background:var(--fault);box-shadow:0 0 9px var(--fault)}

/* ── Hero ───────────────────────────────────────────────────── */
.hero{padding:96px 0 0}
.eyebrow{
  font-family:var(--mono);font-size:11.5px;letter-spacing:.32em;text-transform:uppercase;
  color:var(--gbt-cyan);margin-bottom:22px;
}
.eyebrow::before{content:"\25AA\25AA ";color:var(--gbt-violet);letter-spacing:.1em}
h1{
  font-size:clamp(30px,5.2vw,58px); line-height:1.1; font-weight:700;
  letter-spacing:-.032em; max-width:19em;
}
h1 em{
  font-style:normal;
  background:var(--grad-brand);
  -webkit-background-clip:text;background-clip:text;
  -webkit-text-fill-color:transparent;color:var(--gbt-cyan);
}
.lede{margin-top:26px;max-width:44em;font-size:16.5px;color:var(--ink-2)}
.lede b{color:var(--ink);font-weight:600}
.rule{margin:44px 0 0;height:2px;border-radius:2px;background:var(--grad-brand);opacity:.85}
.cta{display:flex;flex-wrap:wrap;gap:12px;margin-top:34px}
.btn{
  display:inline-flex;align-items:center;gap:9px;height:44px;padding:0 22px;
  border-radius:100px;font-size:14px;font-weight:600;cursor:pointer;
  border:1px solid var(--line-hot);color:var(--gbt-cyan);background:var(--tint-cyan);
  transition:transform var(--t),box-shadow var(--t);
}
.btn:hover{transform:translateY(-2px);box-shadow:0 8px 26px var(--glow-cyan)}
.btn.ghost{border-color:var(--line);color:var(--ink-2);background:transparent}
.btn.ghost:hover{color:var(--gbt-gold);border-color:var(--glow-gold);box-shadow:0 8px 26px var(--glow-gold)}

/* ── 通用小节 ──────────────────────────────────────────────── */
section{padding:88px 0}
.head{display:flex;align-items:baseline;gap:16px;flex-wrap:wrap;margin-bottom:38px}
h2{font-size:clamp(22px,3vw,31px);font-weight:680;letter-spacing:-.022em}
.head p{font-family:var(--mono);font-size:11.5px;letter-spacing:.16em;color:var(--ink-3);text-transform:uppercase}
.head .bar{flex:1;min-width:60px;height:1px;background:linear-gradient(90deg,var(--line-hot),transparent)}

/* ── 能力矩阵 ──────────────────────────────────────────────── */
.caps{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:18px}
.card{
  position:relative;padding:26px 24px 22px;border-radius:var(--r-md);
  border:1px solid var(--line-faint);background:linear-gradient(180deg,var(--panel),var(--panel-2));
  transition:border-color var(--t),transform var(--t),box-shadow var(--t);
  overflow:hidden;
}
.card::before{
  content:"";position:absolute;inset:0 0 auto 0;height:2px;background:var(--grad-brand);
  opacity:0;transition:opacity var(--t);
}
.card:hover{border-color:var(--line);transform:translateY(-3px);box-shadow:0 16px 40px var(--shadow-card)}
.card:hover::before{opacity:1}
.card .k{font-family:var(--mono);font-size:10.5px;letter-spacing:.2em;color:var(--gbt-violet);margin-bottom:12px}
.card h3{font-size:18px;font-weight:650;margin-bottom:11px;letter-spacing:-.012em}
.card p{font-size:14px;color:var(--ink-2)}
.tags{display:flex;flex-wrap:wrap;gap:7px;margin-top:17px}
.tag{
  font-family:var(--mono);font-size:10.5px;padding:4px 9px;border-radius:100px;
  border:1px solid var(--line-faint);color:var(--ink-3);background:var(--tint-violet);
}

/* ── 架构分层 ──────────────────────────────────────────────── */
.layers{display:flex;flex-direction:column;gap:9px}
.layer{
  display:grid;grid-template-columns:56px 132px 1fr;gap:18px;align-items:center;
  padding:16px 20px;border-radius:var(--r-sm);border:1px solid var(--line-faint);
  background:var(--panel);transition:border-color var(--t),background var(--t);
}
.layer:hover{border-color:var(--line-hot);background:var(--panel-2)}
.layer .n{font-family:var(--mono);font-size:12px;color:var(--gbt-cyan);letter-spacing:.1em}
.layer .nm{font-weight:640;font-size:15px;color:var(--gbt-gold)}
.layer .ds{font-size:13.5px;color:var(--ink-2)}

/* ── 运行读数 ──────────────────────────────────────────────── */
.readout{
  display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:14px;
  padding:26px;border-radius:var(--r-md);
  border:1px solid var(--line);background:linear-gradient(180deg,var(--panel),var(--panel-2));
}
.rt{padding:4px 2px}
.rt dt{font-family:var(--mono);font-size:10.5px;letter-spacing:.16em;color:var(--ink-3);text-transform:uppercase;margin-bottom:7px}
.rt dd{font-family:var(--mono);font-size:19px;font-weight:600;color:var(--gbt-cyan);word-break:break-all}
.rt dd.g{color:var(--gbt-gold)}

/* ── 页脚 ─────────────────────────────────────────────────── */
footer{border-top:1px solid var(--line-faint);margin-top:40px;padding:34px 0 46px}
footer .wrap{display:flex;flex-wrap:wrap;gap:14px;align-items:center}
.sig{font-family:var(--mono);font-size:11.5px;color:var(--ink-3);letter-spacing:.02em}
.sig i{font-style:normal;color:var(--gbt-gold)}
footer .bar{flex:1;min-width:40px;height:1px;background:linear-gradient(90deg,transparent,var(--line-hot),var(--gbt-violet))}

@media (max-width:720px){
  .nav{display:none}
  .hero{padding-top:64px}
  .layer{grid-template-columns:44px 1fr;grid-template-rows:auto auto;gap:6px 14px}
  .layer .ds{grid-column:1/-1}
  section{padding:64px 0}
}
@media (prefers-reduced-motion:reduce){
  *{transition:none!important;animation:none!important;scroll-behavior:auto!important}
}
</style>
</head>
<body>

<header class="top">
  <div class="wrap">
    <img class="logo" src="@@LOGO@@" alt="@@BRAND@@ 标志" width="36" height="36">
    <div class="brand">
      <b>@@BRAND@@</b>
      <span>Capability Hub</span>
    </div>
    <div class="spacer"></div>
    <nav class="nav">
      <a href="#caps">能力</a>
      <a href="#arch">架构</a>
      <a href="#rt">读数</a>
    </nav>
    <div class="live" id="live" data-s="wait">
      <i class="dot"></i><span id="livetext">检查中</span>
    </div>
  </div>
</header>

<main>
  <div class="wrap hero">
    <p class="eyebrow">@@BRAND_SLUG@@ · @@CAP@@</p>
    <h1>让每一条 AI 通道都有备份，<br><em>让每一次调用都有交代。</em></h1>
    <p class="lede">
      <b>@@BRAND@@</b> 是一套自建的 AI 能力中枢。统一密钥网关把全部上游通道收在一处声明，
      额度耗尽自动换道、失败即沉底、储备不榨干；触手原生视觉补齐读图能力，三级后端如实降级；
      镜像多维度空间当试验场，<b>生产只收成品</b>。
    </p>
    <div class="rule"></div>
    <div class="cta">
      <a class="btn" href="#caps">看能力矩阵 →</a>
      <a class="btn ghost" href="#arch">看分层架构</a>
    </div>
  </div>

  <section id="caps">
    <div class="wrap">
      <div class="head">
        <h2>能力矩阵</h2>
        <div class="bar"></div>
        <p>Six Modules · In Production</p>
      </div>
      <div class="caps">
@@CARDS@@
      </div>
    </div>
  </section>

  <section id="arch">
    <div class="wrap">
      <div class="head">
        <h2>五层架构 · 三条硬不变量</h2>
        <div class="bar"></div>
        <p>Key Source → Ledger → Channel → Router → Selftest</p>
      </div>
      <div class="layers">
@@LAYERS@@
      </div>
    </div>
  </section>

  <section id="rt">
    <div class="wrap">
      <div class="head">
        <h2>运行读数</h2>
        <div class="bar"></div>
        <p>Live · Server Rendered</p>
      </div>
      <dl class="readout">
@@READOUT@@
      </dl>
    </div>
  </section>
</main>

<footer>
  <div class="wrap">
    <span class="sig"><i>@@BRAND@@</i> · @@SIGNATURE@@</span>
    <span class="bar"></span>
    <span class="sig">v@@VERSION@@</span>
  </div>
</footer>

<script>
// 顶栏活点：拿真实端点读数，成功=青，失败=红。拿不到就如实说拿不到。
(function(){
  var el = document.getElementById('live'), tx = document.getElementById('livetext');
  fetch('/api/status', {cache:'no-store'})
    .then(function(r){ if(!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(function(d){
      el.setAttribute('data-s','ok');
      tx.textContent = (d.service || 'online') + ' · ' + (d.region || 'local');
    })
    .catch(function(e){
      el.setAttribute('data-s','bad');
      tx.textContent = '离线';
    });
})();
</script>
</body>
</html>
"""


def _cards_html() -> str:
    out = []
    for c in CAPABILITIES:
        tags = "".join('<span class="tag">%s</span>' % t for t in c["m"])
        out.append(
            '<article class="card">'
            '<p class="k">%s</p><h3>%s</h3><p>%s</p>'
            '<div class="tags">%s</div></article>' % (c["k"], c["t"], c["d"], tags)
        )
    return "\n".join(out)


def _layers_html() -> str:
    return "\n".join(
        '<div class="layer"><span class="n">%s</span>'
        '<span class="nm">%s</span><span class="ds">%s</span></div>' % r for r in ARCH
    )


def _readout_html() -> str:
    rows = [
        ("服务状态", "在线", True),
        ("构建版本", "v%s" % VERSION, False),
        ("运行环境", os.environ.get("VERCEL_ENV", "development"), False),
        ("部署区域", os.environ.get("VERCEL_REGION", "local"), True),
        ("Python", platform.python_version(), False),
        ("启动于", _BOOT_ISO.replace("+00:00", "Z"), False),
    ]
    return "\n".join(
        '<div class="rt"><dt>%s</dt><dd%s>%s</dd></div>'
        % (k, ' class="g"' if g else "", v) for k, v, g in rows
    )


def _render() -> str:
    host = request.host_url.rstrip("/")
    return (PAGE
            .replace("@@BRAND_SLUG@@", BRAND_SLUG)
            .replace("@@BRAND@@", BRAND)
            .replace("@@CAP@@", CAP)
            .replace("@@SIGNATURE@@", SIGNATURE)
            .replace("@@VERSION@@", VERSION)
            .replace("@@LOGO@@", _b64("logo-256.png"))
            .replace("@@FAVICON@@", _b64("favicon-32.png") or _b64("logo-256.png"))
            .replace("@@OGURL@@", host + "/og.png")
            .replace("@@CARDS@@", _cards_html())
            .replace("@@LAYERS@@", _layers_html())
            .replace("@@READOUT@@", _readout_html()))


app = Flask(__name__)


@app.get("/")
def home() -> Response:
    # mimetype 只给 "text/html"：Flask 会自动补 "; charset=utf-8"。
    # 早前写成 "text/html; charset=utf-8" 会被再补一次 ⇒ 头里 charset 重复两遍。
    return Response(_render(), mimetype="text/html",
                    headers={"Cache-Control": "public, max-age=0, must-revalidate",
                             "X-GBT-Brand": BRAND_SLUG})


@app.get("/api/status")
def api_status():
    """站点自身读数 —— 不编造上游状态，只说这个 function 真实知道的事。"""
    return jsonify(
        ok=True, brand=BRAND, service=CAP, version=VERSION,
        env=os.environ.get("VERCEL_ENV", "development"),
        region=os.environ.get("VERCEL_REGION", "local"),
        python=platform.python_version(),
        booted_at=_BOOT_ISO,
        uptime_s=round(time.time() - _BOOT_TS, 3),
        now=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


@app.get("/og.png")
def og_image() -> Response:
    """分享卡图。缺图就 404，不用假图糊过去。"""
    p = _ASSETS / "logo-512.png"
    if not p.is_file():
        return Response("missing", status=404, mimetype="text/plain")
    return Response(p.read_bytes(), mimetype="image/png",
                    headers={"Cache-Control": "public, max-age=86400"})


@app.get("/healthz")
def healthz():
    return jsonify(ok=True, cap=CAP, version=VERSION)


if __name__ == "__main__":
    print(json.dumps({"brand": BRAND, "cap": CAP, "version": VERSION,
                      "palette": _DAILY}, ensure_ascii=False))
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
