# gbt-capability: gods_eye
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""上帝之眼（gods_eye）· 主人令 2026-09-27。

主人原话：「**上帝之眼是能看到创作页面这些**，毕竟上帝之眼里面的**克劳德**是要给意见和建议、
商量项目架构和方向指引，当然**决策权在你这里**，你可以采纳意见或建议；把 **CodeBuddy 也部署进
上帝之眼，让他做杂事，主项目她没有执行权**，只有服从安排和随时候命；以及**每日的 GBT 探针汇报**
和**每日全量扫描框架**指出**缺点、短板、卡点**；然后你自己跟克劳德在上帝之眼里面**计划优化和提升整体实力**。」

## 三块职责（与主人原话一一对应）
  ① **眼睛**（`see`）：看得见**创作页面**（7 个面板）+ 活着的服务（端口在听）；
  ② **两位顾问**（`advisors` / `ask`）—— 权限写成**机器可读**的表，不是口头约定：
     · **Claude**：只出**意见与建议**（架构 · 方向 · 评审）；**没有决策权**；当前未装 ⇒ 如实报安装命令；
     · **CodeBuddy**：只做**杂事**（路径排查/日志整理/取数）；**对主项目没有执行权** ⇒
       凡提示里点了主项目路径（`projects/` `gbt_allinone/` `skills/` 等）**一律拒**，只许服从与待命；
     · **决策权在主体**（我）⇒ `plan decide` 采纳/搁置，全部留痕。
  ③ **每日汇报**（`daily`）：**GBT 探针汇报** + **全量扫描** ⇒ 出三张清单：**缺点 / 短板 / 卡点**，
     每条都带**来源读数**（不许编）；`plan` 用来把"提升整体实力"落成可追踪的提案与决策。

ops：
  see                         眼睛：创作页面 + 服务端口（实测在不在听）
  advisors                    两位顾问的权限表（机器可读）+ 当前可用性
  ask advisor=claude|codebuddy text=...   真咨询（过各自能力位；CodeBuddy 走权限校验）
  daily                       每日汇报：探针 + 全量扫描 ⇒ 缺点/短板/卡点（每条带来源）
  plan op=add|list|decide ...  优化计划面（提案 + 采纳/搁置，留痕 state/gods_eye_plan.jsonl）
  panel                       上帝之眼页面（我们视觉语言 · 快照内联）
"""
from __future__ import annotations

import json
import os
import socket
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_STATE = _ROOT / "state"
_PLAN = _STATE / "gods_eye_plan.jsonl"
_SNAP = _STATE / "gods_eye.json"
_PANEL = _ROOT / "holo_pet" / "assets" / "godview" / "index.html"
_PROBE_WS = Path(r"C:\Users\ADMIN\Desktop\GBT探针")

# 创作页面（眼睛要看得见的那些）+ 服务端口
CREATION_PAGES = [
    ("console3d", "3D 大脑执行层（172+ 能力位球面 / run_task 脉冲流）"),
    ("automation", "三套自动化闭环（音乐试听 / 短视频试看 / 电影分幕）"),
    ("structure", "框架结构浏览器（三栏）"),
    ("godview", "上帝之眼（本页）"),
    ("health-panel", "健康面板（安全棒读数 · 异常报警）"),
    ("task-manager", "任务管理器（真进程 · 归属/内存/CPU/端口）"),
    ("music", "音乐线面板"),
]
PORTS = [(31415, "FreeLLMAPI（免费算力池）"), (8188, "ComfyUI（本地生图/生视频）"),
         (31717, "capability_gateway（能力网关）"), (8111, "mock-vllm（本地替身）")]

# **顾问权限表**（机器可读；主人原话逐条对上）
ADVISORS = {
    "claude": {
        "role": "意见建议（架构 · 方向 · 评审）",
        "may": ["出意见", "出建议", "评审与挑刺", "商量架构与方向"],
        "may_not": ["决策（决策权在主体）", "直接改主项目"],
        "capability": "claude_code",
        "must_install": "npm i -g @anthropic-ai/claude-code",
    },
    "codebuddy": {
        "role": "杂事（服从安排 · 随时候命）",
        "may": ["杂事：路径排查", "日志整理", "取数/搜索", "跑腿"],
        "may_not": ["对主项目有执行权", "决策", "改主项目文件"],
        "capability": "codebuddy",
        "main_project_paths": ["projects/", "gbt_allinone/", "skills/", "tools/", "state/"],
    },
}
DECIDER = "主体（GBT小土豆V8 · 我）—— **决策权在主体**：采纳或搁置由我定"


def _port_open(p: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.35)
        return s.connect_ex(("127.0.0.1", p)) == 0


def _gate(kind: str, payload: dict) -> dict:
    sys.path.insert(0, str(_ROOT))
    import gbt_allinone as g
    r = g.run_task(kind, payload)
    d = r.get("result") if isinstance(r, dict) else None
    while isinstance(d, dict) and isinstance(d.get("result"), dict) and set(d) <= {"status", "kind", "result", "ok"}:
        d = d["result"]
    return {"gate_ok": bool(isinstance(r, dict) and r.get("ok", True)), "payload": d or {}}


def _load(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default if default is not None else {}


def _log(row: dict) -> None:
    _PLAN.parent.mkdir(parents=True, exist_ok=True)
    with open(_PLAN, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), **row},
                            ensure_ascii=False) + "\n")


def see(**_kw) -> dict:
    """眼睛：创作页面（在不在）+ 服务（端口在不在听）。"""
    pages = []
    for name, why in CREATION_PAGES:
        p = _ROOT / "holo_pet" / "assets" / name / "index.html"
        pages.append({"page": name, "why": why, "exists": p.is_file(),
                      "kb": round(p.stat().st_size / 1024, 1) if p.is_file() else 0,
                      "open": f"holo_pet/assets/{name}/index.html"})
    services = [{"port": p, "what": w, "listening": _port_open(p)} for p, w in PORTS]
    return {"ok": True, "op": "see", "pages": pages,
            "pages_ok": sum(1 for x in pages if x["exists"]), "pages_total": len(pages),
            "services": services, "services_up": sum(1 for x in services if x["listening"]),
            "_口径": "页面=真读文件；服务=真连一次端口（不许拿'应该开着'当读数）"}


def advisors(**_kw) -> dict:
    """两位顾问的权限表 + 当前可用性（过各自能力位实测）。"""
    out = {}
    for name, spec in ADVISORS.items():
        st = _gate(spec["capability"], {"op": "status"})
        d = st.get("payload") or {}
        avail = bool(d.get("available")) if name == "claude" else bool(d.get("found"))
        out[name] = {**spec, "available": avail,
                     "evidence": (d.get("install_hint") if name == "claude" and not avail
                                  else (d.get("found") or [{}])[0].get("path") if isinstance(d.get("found"), list) and d.get("found") else str(d)[:120])}
    return {"ok": True, "op": "advisors", "advisors": out, "decider": DECIDER,
            "_口径": "**权限是机器可读的表**（may / may_not）；可用性过各自能力位实测，不猜"}


def ask(advisor: str = "", text: str = "", **_kw) -> dict:
    """真咨询：过顾问自己的能力位。**CodeBuddy 走权限校验**（主项目路径一律拒）。"""
    a = (advisor or "").lower()
    if a not in ADVISORS:
        return {"ok": False, "fail_closed": True, "error": f"顾问只有 {sorted(ADVISORS)}"}
    if not text.strip():
        return {"ok": False, "fail_closed": True, "error": "text 不能为空"}
    low = text.replace("\\", "/").lower()
    if a == "codebuddy":
        hit = [p for p in ADVISORS[a]["main_project_paths"] if p in low]
        if hit:
            return {"ok": False, "refused": True, "advisor": a, "hit": hit,
                    "why": "CodeBuddy **对主项目没有执行权**（主人令）：它只做杂事、服从安排、随时候命",
                    "how_to": "把它要碰的主项目动作交回主体（我）来做；派给它的活请只涉杂事"}
    if a == "claude":
        st = _gate("claude_code", {"op": "status"})
        if not (st.get("payload") or {}).get("available"):
            return {"ok": False, "advisor": a, "available": False,
                    "why": "Claude Code CLI 未安装 ⇒ 咨询不了（如实报，不假装）",
                    "how_to": ADVISORS[a]["must_install"]}
    d = _gate(ADVISORS[a]["capability"], {"op": "ask", "text": text})
    _log({"event": "ask", "advisor": a, "chars": len(text), "ok": d.get("gate_ok")})
    return {"ok": d.get("gate_ok"), "op": "ask", "advisor": a, "answer": str(d.get("payload"))[:800],
            "note": "顾问只出意见/杂事；**决策权在主体**"}


def _probe_report() -> dict:
    """GBT 探针汇报：读探针工作区最新交付/证据 + 抓取台账尾。"""
    if not _PROBE_WS.is_dir():
        return {"available": False, "why": f"探针工作区不在：{_PROBE_WS}"}
    out = {"available": True, "deliverables": [], "evidence": [], "ledger_tail": ""}
    for sub, key in (("01-交付物", "deliverables"), ("02-证据", "evidence")):
        d = _PROBE_WS / sub
        if d.is_dir():
            for day in sorted(d.iterdir())[-1:]:
                if day.is_dir():
                    out[key] = [x.name for x in sorted(day.iterdir())][-6:]
    lg = _PROBE_WS / "04-调研" / "抓取台账.md"
    if lg.is_file():
        out["ledger_tail"] = "\n".join(lg.read_text(encoding="utf-8", errors="replace").splitlines()[-4:])
    return out


def _scan_findings() -> dict:
    """全量扫描读数 → 缺点/短板/卡点（**每条带来源**）。"""
    health = _load(_STATE / "health.json", {})
    cov = _load(_STATE / "coverage_matrix.json", {})
    full = _load(_STATE / "full_scan.json", {})
    unimpl = _load(_STATE / "unimplemented.json", {"items": []})
    ledger = _load(_STATE / "排查台账.json", {"open_faults": []})
    ak = _gate("automation_keys", {"op": "status"}).get("payload") or {}
    sur = _load(_STATE / "gods_eye.json", {})
    gaps, shorts, blockers = [], [], []

    # 缺点（缺陷类）
    if (health.get("alerts") or []):
        gaps.append({"item": f"安全棒报警 {len(health['alerts'])} 条", "src": "state/health.json"})
    if not cov.get("全绿", True):
        gaps.append({"item": f"覆盖矩阵非全绿（盲区 {len(cov.get('盲区') or [])}）", "src": "state/coverage_matrix.json"})
    if full.get("需人核"):
        gaps.append({"item": f"全树扫描需人核 {len(full['需人核'])} 条", "src": "state/full_scan.json"})
    of = ledger.get("open_faults") or []
    if of:
        gaps.append({"item": f"未清故障 {len(of)} 条（{[f.get('id') for f in of][:5]}）", "src": "state/排查台账.json"})

    # 短板（能力/配置类）
    um = unimpl.get("items") or []
    if um:
        shorts.append({"item": f"未实现登记 {len(um)} 条（{[i.get('kind') for i in um][:4]}）", "src": "state/unimplemented.json"})
    slots = ak.get("slots") or []
    miss_slots = [s["slot"] for s in slots if s.get("present") is False]
    if miss_slots:
        shorts.append({"item": f"密钥槽未就位 {len(miss_slots)} 个（{miss_slots}）", "src": "automation_keys.status"})
    adv = advisors().get("advisors") or {}
    off = [k for k, v in adv.items() if not v.get("available")]
    if off:
        shorts.append({"item": f"顾问位不可用：{off}", "src": "gods_eye.advisors"})
    if health.get("energy", {}).get("free_pool") is False:
        shorts.append({"item": "免费算力池不可达（FreeLLMAPI 未启动）", "src": "state/health.json"})

    # 卡点（阻塞类：要授权 / 缺环境 / 慢）
    from importlib.util import spec_from_file_location, module_from_spec
    if True:
        try:
            sp = spec_from_file_location("ag_ge", _ROOT / "gbt_allinone" / "auth_gate.py")
            ag = module_from_spec(sp)
            sp.loader.exec_module(ag)  # type: ignore
            blockers.append({"item": "写盘/执行类动作默认无授权（需主人按需发放）",
                             "src": "gbt_allinone/store/auth_grants.jsonl", "how": "auth grant --scope <s> --ttl <s>"})
        except Exception:                                      # noqa: BLE001
            pass
    st = _gate("comfyui", {"op": "status"}).get("payload") or {}
    if st.get("type") == "cpu":
        blockers.append({"item": f"ComfyUI 跑在 CPU（{st.get('version')}）⇒ 出片慢（不是不能出）",
                         "src": "gods_eye.daily/comfyui.status"})
    return {"缺点": gaps, "短板": shorts, "卡点": blockers, "advisors": adv}


def daily(**_kw) -> dict:
    """每日汇报：探针 + 全量扫描 ⇒ 缺点/短板/卡点（每条带来源）。"""
    probe = _probe_report()
    scan = _scan_findings()
    out = {"ok": True, "op": "daily", "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "探针汇报": probe, "全量扫描": {"缺点": scan["缺点"], "短板": scan["短板"], "卡点": scan["卡点"]},
           "计数": {"缺点": len(scan["缺点"]), "短板": len(scan["短板"]), "卡点": len(scan["卡点"]),
                  "探针可用": probe.get("available")},
           "_口径": "每一条都带 `src`（哪个读数文件/哪个能力位）—— **不许编**；探针汇报读的是探针工作区的真文件"}
    _SNAP.write_text(json.dumps({**out, "顾问": scan["advisors"]}, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def plan(op: str = "list", item: str = "", src: str = "", decision: str = "", **_kw) -> dict:
    """优化计划面：add（提案，通常来自 Claude 的建议）/ list / decide（采纳 or 搁置，**决策权在主体**）。"""
    op = (op or "list").lower()
    if op == "add":
        if not item.strip():
            return {"ok": False, "fail_closed": True, "error": "item 不能为空"}
        _log({"event": "proposal", "item": item[:300], "src": src[:120], "by": "claude-or-self"})
        return {"ok": True, "op": "plan.add", "item": item[:120], "src": src}
    if op == "decide":
        if decision not in ("采纳", "搁置"):
            return {"ok": False, "fail_closed": True, "error": "decision 必须是 采纳 / 搁置"}
        _log({"event": "decision", "item": item[:300], "decision": decision, "decider": DECIDER})
        return {"ok": True, "op": "plan.decide", "item": item[:120], "decision": decision, "decider": DECIDER}
    rows = []
    if _PLAN.is_file():
        for ln in _PLAN.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                rows.append(json.loads(ln))
            except json.JSONDecodeError:
                continue
    return {"ok": True, "op": "plan.list", "count": len(rows), "tail": rows[-12:], "decider": DECIDER}


_PANEL_HTML = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>上帝之眼 · GBT小土豆V8</title><style>
 :root{--bg:#080b10;--panel:#101822;--line:#1d2836;--ink:#dfe9f4;--dim:#7d90a6;--cyan:#33c9dc;--orange:#f0a03c;--red:#e5484d;--green:#3fb950;--violet:#a371f7}
 *{box-sizing:border-box}body{margin:0;background:radial-gradient(1200px 600px at 20% -10%,#0d1723,#080b10);color:var(--ink);font:14px/1.6 "Segoe UI","Microsoft YaHei",sans-serif}
 header{padding:20px 24px;border-bottom:1px solid var(--line);display:flex;gap:14px;align-items:center}
 h1{font-size:18px;margin:0;font-weight:600;letter-spacing:.5px}
 .sub{color:var(--dim);font-size:12px}.meta{margin-left:auto;color:var(--dim);font-size:12px}
 .wrap{display:grid;grid-template-columns:1.1fr 1fr;gap:16px;padding:20px 24px}
 .card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px}
 .card h2{font-size:13px;margin:0 0 10px;color:var(--dim);font-weight:500;letter-spacing:.6px}
 .item{padding:7px 0;border-top:1px solid var(--line);font-size:13px}
 .item:first-child{border-top:0}
 .src{color:var(--dim);font-size:11px}
 .ok{color:var(--green)}.bad{color:var(--red)}.warn{color:var(--orange)}.adv{color:var(--violet)}
 table{width:100%;border-collapse:collapse}th,td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left;font-size:12.5px}
 th{color:var(--dim);font-weight:500}
 footer{padding:14px 24px;color:var(--dim);font-size:12px;border-top:1px solid var(--line)}
</style></head><body>
<header>
 <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#33c9dc" stroke-width="1.6"><path d="M12 5c-5 0-9 4.5-9 7s4 7 9 7 9-4.5 9-7-4-7-9-7z"/><circle cx="12" cy="12" r="3"/></svg>
 <h1>上帝之眼</h1><span class="sub">看得见创作页面 · 两位顾问 · 每日汇报 · 计划与决策</span>
 <span class="meta" id="at">-</span>
</header>
<div class="wrap">
 <div class="card"><h2>创 作 页 面（眼睛能看到）</h2><div id="pages"></div></div>
 <div class="card"><h2>两 位 顾 问 · 权 限</h2><div id="adv"></div></div>
 <div class="card"><h2>缺 点</h2><div id="gaps"></div></div>
 <div class="card"><h2>短 板 / 卡 点</h2><div id="short"></div><div id="block" style="margin-top:10px"></div></div>
</div>
<footer>口径：每条都带来源（哪个读数文件/哪个能力位）；页面=真读文件，服务=真连端口；**决策权在主体**。</footer>
<script>
const INLINE = __SNAPSHOT__;
const PAGES = __PAGES__;
function li(x){return '<div class="item">'+x+'</div>';}
function render(d){
  document.getElementById('at').textContent = (d && d.at) || '-';
  document.getElementById('pages').innerHTML = (PAGES||[]).map(p=>li(
    '<b>'+p.page+'</b> <span class="'+(p.exists?'ok':'bad')+'">'+(p.exists?'可见':'缺')+'</span> · '+
    '<span class="src">'+p.why+'</span>')).join('') +
    '<div class="item"><span class="src">服务：'+((d&&d.services)||[]).map(s=>s.what.split('（')[0]+(s.listening?' 🟢':' ⚪')).join(' · ')+'</span></div>';
  const A=(d&&d.顾问)||{};
  document.getElementById('adv').innerHTML = Object.entries(A).map(([k,v])=>li(
    '<b class="adv">'+k+'</b> <span class="'+(v.available?'ok':'warn')+'">'+(v.available?'可用':'不可用')+'</span> · '+
    '<span class="src">'+v.role+'</span><br><span class="src">可：'+v.may.join(' / ')+'<br>不可：'+v.may_not.join(' / ')+'</span>')).join('')
    + li('<span class="src">决策：'+(d&&d.decider||'-')+'</span>');
  const S=(d&&d.全量扫描)||{};
  document.getElementById('gaps').innerHTML = ((S.缺点||[]).map(x=>li('<span class="bad">'+x.item+'</span><br><span class="src">'+x.src+'</span>')).join('')) || li('<span class="ok">无</span>');
  document.getElementById('short').innerHTML = ((S.短板||[]).map(x=>li('<span class="warn">'+x.item+'</span><br><span class="src">'+x.src+'</span>')).join('')) || li('<span class="ok">无</span>');
  document.getElementById('block').innerHTML = ((S.卡点||[]).map(x=>li('<span class="bad">'+x.item+'</span><br><span class="src">'+x.src+'</span>')).join(''));
}
render(INLINE);
async function refresh(){try{const r=await fetch('state/gods_eye.json',{cache:'no-store'});render(await r.json());}catch(e){}}
setInterval(refresh, 15000);
</script></body></html>
"""


def panel(**_kw) -> dict:
    snap = _load(_SNAP, {})
    if not snap:
        snap = daily()
    pages = see()["pages"]
    html = _PANEL_HTML.replace("__SNAPSHOT__", json.dumps(snap, ensure_ascii=False)) \
                      .replace("__PAGES__", json.dumps(pages, ensure_ascii=False))
    _PANEL.parent.mkdir(parents=True, exist_ok=True)
    _PANEL.write_text(html, encoding="utf-8")
    return {"ok": True, "op": "panel", "path": str(_PANEL.relative_to(_ROOT)),
            "pages": len(pages), "note": "快照内联（file:// 直接看）；http 下 15 秒自刷新"}


def run_op(op: str = "see", **params) -> dict:
    op = (op or "see").lower()
    for name, fn in (("see", see), ("advisors", advisors), ("ask", ask),
                     ("daily", daily), ("plan", plan), ("panel", panel)):
        if op == name:
            return fn(**params)
    return {"ok": False, "fail_closed": True,
            "error": f"未知 op:{op}（see/advisors/ask/daily/plan/panel）"}
