# gbt-capability: subprocess
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""GBT云端LLM — 完全接入密鑰 + 强制首注入自我认知
Agent驱动必经路径：自我认知(实时cap数) → 能力索引表 → 密鑰路由 → LLM推理
密鑰优先级： DeepSeek → Kimi → OpenAI → 自定义
"""
import sys, json, os, urllib.request, urllib.error, re, subprocess, time
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
# ══════════════════════════════════════════════════════════════
# 密鑰自动识别：DeepSeek → Kimi → OpenAI → 自定义
# ══════════════════════════════════════════════════════════════
_KEY_CHAIN = [
# 这里 KIMI_API_KEY 和 MOONSHOT_API_KEY 两个都认，一个配了就走
    ("agnes",    ["AGNES_API_KEY"],
     "https://apihub.agnes-ai.com/v1",  "agnes-2.5-flash"),  # Custom Provider（Owner 2026-09-19）
    # 这里 KIMI_API_KEY 和 MOONSHOT_API_KEY 两个都认，一个配了就走
    ("deepseek", ["DEEPSEEK_API_KEY"],
                 "https://api.deepseek.com/v1", "deepseek-flash"),  # 官方唯一 id：deepseek-flash = DeepSeek-V4.1-Flash
    ("kimi",     ["MOONSHOT_API_KEY", "KIMI_API_KEY"],
                 "https://api.moonshot.cn/v1",  "kimi-k2-0905-preview"),
    ("openai",   ["OPENAI_API_KEY"],
                 os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"), "gpt-4o-mini"),
    ("custom",   ["GBT_LLM_API_KEY"],
                 os.environ.get("GBT_LLM_BASE_URL", ""),
                 os.environ.get("GBT_LLM_MODEL",    "")),
    ("anthropic", ["ANTHROPIC_API_KEY"],
                 "https://api.anthropic.com", "claude-sonnet-4-20250514"),
    ("gemini",   ["GEMINI_API_KEY"],
                 "https://generativelanguage.googleapis.com/v1beta", "gemini-2.0-flash"),
    # ── 土豆大模型（本机原生端点 · 2026-09-26 主人令「直接接上」）────────────────
    # 排在链尾作**本地兜底**（云端全缺 key 时才自动落到它），也可用环境变量**显式选用**：
    #   setx GBT_POTATO_API_KEY local   → 进入链条；setx GBT_LLM_PROVIDER potato → 强制走土豆
    # 🔴 现状如实：8111 端点当前是**假端点**（同批实测回显自证「(假端点回显)」，不能思考）；
    #    换真 vLLM 只改 GBT_POTATO_BASE_URL 一行。首位仍是 agnes（Owner 2026-09-19 指定契约，
    #    test_framework 钉着）——**不抢主模型位，不越权**。
    ("potato",   ["GBT_POTATO_API_KEY"],
                 os.environ.get("GBT_POTATO_BASE_URL", "http://127.0.0.1:8111/v1"),
                 os.environ.get("GBT_POTATO_MODEL", "gbt-potato-v8")),
]
PROVIDER = ""
API_KEY  = ""
BASE_URL = ""
MODEL    = ""
# ── 2026-10-03 触手独立密钥路由表：purpose → agnes 子 profile ───────────────
# 每根触手使用独立账号（独立配额/用量），互不干扰；未配置的触手回落到全局 agnes
_PURPOSE_ROUTING_MAP = {
    "neural": "neural_agnes",
    "vision": "vision_agnes",
    "devour": "devour_agnes",
    "omni":   "omni_agnes",
}

# 手动指定覆盖
if os.environ.get("GBT_LLM_PROVIDER"):
    _p = os.environ["GBT_LLM_PROVIDER"]
    for _name, _envs, _url, _model in _KEY_CHAIN:
        if _name == _p:
            _key = next((os.environ.get(e) for e in _envs if os.environ.get(e)), None)
            if _key:
                PROVIDER, API_KEY, BASE_URL, MODEL = _name, _key, \
                    os.environ.get("GBT_LLM_BASE_URL", _url), \
                    os.environ.get("GBT_LLM_MODEL", _model)
# 自动旅历：优先级链
if not PROVIDER:
    for _name, _envs, _url, _model in _KEY_CHAIN:
        _key = next((os.environ.get(e) for e in _envs if os.environ.get(e)), None)
        if _key and _url:
            PROVIDER, API_KEY, BASE_URL, MODEL = _name, _key, _url, _model
            break
TIMEOUT = 60
_SANDBOX_ROOT = Path(__file__).parent.parent
_CAPS_ROOT    = Path(__file__).parent.parent  # caps根目录
_THIS_DIR     = Path(__file__).parent
# ? 2026-09-09 SSOT 规模同步 — 与 brain 系同构: 自我认知数字以 118 为锚点,
#    从项目 .gbt/_audit_caps.json 读实时 cap 数替换; 失败静默回退静态文本。
def _live_cap_total() -> int:
    try:
        _root = Path(__file__).resolve().parent
        while not (_root / ".gbt" / "_audit_caps.json").exists() and _root.parent != _root:
            _root = _root.parent
        _reg = _root / ".gbt" / "_audit_caps.json"
        if _reg.exists():
            with _reg.open(encoding="utf-8") as _f:
                _n = len(json.load(_f).get("caps", {}))
            if isinstance(_n, int) and _n > 0:
                return _n
    except Exception:
        # 合理兜底：读能力总数失败 → 返回 0 → 上游 _resolve_awareness_anchor 跳过
        # 数字替换（保留原文案），**不会伪造任何数字**，故静默安全。
        pass
    # 🔴 2026-09-25 修：**真的活口是活注册表，不是任何 JSON**（本文件 92-98 行的注释
    #    早就这么写了，但代码没照做）。实测：`.gbt/_audit_caps.json` 全库不存在 ⇒
    #    这里返回 0 ⇒ 上游 `str(_live_cap_total() or 118)` 打出 **118**（v5 时代的硬编码），
    #    而同一段 prompt 里的能力索引表打 **0**，真注册表是 **172**。
    #    **同一段 system prompt 里三个数、没一个对** —— 这就是"大模型不知道自己有什么能力"的机器成因。
    #    ⇒ 现在回落到活注册表（`caps_registry.BENIGN_CAPS`）。
    try:
        from ..caps_registry import BENIGN_CAPS as _BC
        if _BC:
            return len(_BC)
    except Exception:
        pass
    return 0

def _resolve_awareness_anchor(text: str) -> str:
    """把文本里的占位计数替换成**盘上实时**的能力总数。

    2026-09-22 改：原文写死 `if _n and _n != 118` —— 那个 118 是 v5 时代的硬编码，
    而文本里的 118 已被删（现在不许静态罗列能力）。留着会变成"看起来在校验、
    实际永远不触发"的死代码，正是反空壳律要打的形态。
    现在：**文本里若出现占位符就替换；没有占位符就原样返回，不做任何硬编码比较。**
    """
    _n = _live_cap_total()
    if not _n:
        return text
    # 🔴 2026-09-25（台账 N6）：token 表里原来还有一个**裸字面量 `"118"`** —— 那是**盲替换**：
    #    正文里任何一处出现 118（"端口 11800"、"第 118 行"…）都会被静默改成能力总数。
    #    而本函数自己的 docstring 写的是「文本里若出现**占位符**就替换」⇒ **代码与 docstring 不一致**。
    #    现读：内建文本里 `"118"` 出现 **0** 次，两份 awareness 文件也不存在
    #    ⇒ 去掉它**今天零行为变化**，只是拆掉一个"将来会静默改写正文"的机关。
    #    （"自我认知里写了过期数字"这件事另有专人管：`tools/awareness_gap_guard` 会把
    #      注入文本里解析到的数字报出来，不需要在这里顺手改数字。）
    if "{{CAP_TOTAL}}" in text:
        return text.replace("{{CAP_TOTAL}}", str(_n))
    return text

# ── 能力 JSON 索引：只认框架内部的 ────────────────────────────────
# 2026-09-22 清依赖：原文还有两条指向框架外的候选：
#     Path.home()/"GBT-JXDWD"/"sandbox"/"gbt_cap_index.json"
#     Path.home()/"GBT"/"gbt_cap_index.json"
# 两条都删。理由与上面 _AWARENESS_PATHS 同：**一份框架，一份索引**。
# （另注：实测这两个文件与 _SANDBOX_ROOT 下那个**都不存在** —— 即这套 JSON 索引
#   整条链是空的。真正的活口是 caps_registry.py，不是任何 JSON。）
_CAP_INDEX_PATHS = [
    _SANDBOX_ROOT / "gbt_cap_index.json",
]
_cap_index_cache: dict = {}
_cap_index_mtime: float = 0.0
def _load_cap_index() -> dict:
    """加载JSON能力注册表，文件更新时自动刷新"""
    global _cap_index_cache, _cap_index_mtime
    for p in _CAP_INDEX_PATHS:
        try:
            mtime = p.stat().st_mtime
            if mtime != _cap_index_mtime or not _cap_index_cache:
                data = json.loads(p.read_text(encoding='utf-8'))
                _cap_index_cache = data.get('caps', {})
                _cap_index_mtime = mtime
            return _cap_index_cache
        except Exception:
            continue
    return {}
def _cap_total_label() -> str:
    """自我认知标题里那个数字**怎么说**。

    🔴 2026-09-25 修：原来是 `str(_live_cap_total() or 118)` —— 读不到就**印 118**
    （v5 时代的硬编码）。实测那条路天天在走（`_live_cap_total()` 曾返回 0），
    ⇒ system prompt 一边说「118 个cap」、紧接着的能力索引表说「0个cap」、真值 172。
    **读不到就如实说读不到，不许拿历史数字顶替**（本仓口径：不编数字）。
    """
    n = _live_cap_total()
    if n:
        return str(n) + "个cap"
    return "**能力总数读不到**（活注册表不可读 —— 不拿旧硬编码顶替）"


def _registry_cap_index() -> dict:
    """**从活注册表**造一份与 JSON 索引同形的字典（回落用）。

    🔴 为什么必须有它（2026-09-25 实测）：`_CAP_INDEX_PATHS` 里那条 JSON
    （`gbt_allinone/gbt_cap_index.json`）**全库不存在**（本文件 92-98 行的注释已如实写明，
    并点名「真正的活口是 `caps_registry.py`，不是任何 JSON」）——
    但 `_build_cap_digest()` 当年**照样把空表注入 system prompt**，
    表头还写着「0个cap · **实时注册表**」（**两个词都不对**：不是 0，也不是那份 JSON）。
    后果（现读）：prompt 前一段说「118 个cap」、紧接着的表说「0个cap」、真值是 172
    ⇒ **同一段自我认知里三个数、没一个对**。

    口径：能解析出动作就解析（`op=a|b|c` / `action=a|b`），解析不出就如实留 `-`；
    **不编触发词** —— 那一列放描述开头，并在表下注明它是什么。
    """
    import re as _re
    out: dict = {}
    try:
        from ..caps_registry import BENIGN_CAPS as _BC
    except Exception:
        return out
    for kind, meta in _BC.items():
        meta = meta if isinstance(meta, dict) else {}
        desc = str(meta.get("desc") or "")
        acts: list = []
        m = _re.search(r"(?:op|action)\s*=\s*([A-Za-z0-9_|\-/]+)", desc)
        if m:
            acts = [x.strip() for x in _re.split(r"[|/]", m.group(1)) if x.strip()][:4]
        head = _re.split(r"[：（(]", desc)[0].strip()
        out[kind] = {
            "domain": meta.get("domain") or "未分类",
            "actions": acts,
            "triggers": [head[:40]] if head else [],
            "status": "ok" if meta.get("safe") else "warn",
        }
    return out


def _build_cap_digest() -> str:
    """
    全量cap精炼为紧凑能力索引表（动态数量） — 强制注入system prompt
    格式：域 | cap_id | 动作 | 触发词（前3个）
    大模型读到这张表就能精准感知+瞬间知道调用哪个cap
    """
    index = _load_cap_index()
    source = "JSON 索引 gbt_cap_index.json"
    if not index:
        # 🔴 回落：JSON 索引不存在时**用活注册表**，并把来源**写在表头**上 ——
        #    读的人（和模型）必须能看出这张表是从哪儿来的。
        index = _registry_cap_index()
        source = ("caps_registry.BENIGN_CAPS（活注册表）· ⚠️ JSON 索引 gbt_cap_index.json 不存在，"
                  "已按本文件既有口径回落")
    n = len(index)
    lines = []
    lines.append("\n\n## ⚡ 能力精准索引（" + str(n) + "个cap · 来源：" + source + "）")
    lines.append("|域|cap|动作|触发词|")
    lines.append("|--|---|---|---|")
    # 按域分组
    by_domain: dict = {}
    for cap_id, info in index.items():
        d = info.get('domain', '未分类')
        by_domain.setdefault(d, []).append((cap_id, info))
    for domain, caps in sorted(by_domain.items()):
        for cap_id, info in sorted(caps):
            actions  = '/'.join(info.get('actions', [])[:4]) or '-'
            triggers = ' · '.join(info.get('triggers', [])[:3]) or '-'
            status   = '✓' if info.get('status') == 'ok' else '⚠'
            lines.append("|"+domain+"|"+status+"`"+cap_id+"`|"+actions+"|"+triggers+"|")
    # 🔴 2026-09-25 修「**教模型走一条不存在的路**」：
    #   这两行原来写的是
    #       > 直接调用: python caps/<cap_id>/run.py <action> '{"k":"v"}'
    #       > N8N入口: POST http://localhost:5678/webhook/gbt {...}
    #   现读实测：`caps/` 顶层**只有 2 个目录、全库只有 1 个 run.py**（`caps/design_brain/run.py`）
    #   ⇒ `caps/health/run.py`、`caps/mirror_status/run.py`、`caps/echo/run.py` **统统不存在**；
    #   5678 端口**无监听**。**⇒ 自我认知教了模型两条调用法，两条都是死的。**
    #   后果比"少一句说明"重得多：模型照着走 ⇒ 文件不存在 ⇒ 它会得出"这个框架调不动"的结论，
    #   而**真正的入口只有一道门**（`run_task` / `five-dim.py cap`），那条路它反而没被告知。
    #   这正是 `verify-distill` 判据 D 要抓的"编出来的命令"——只不过**没人审运行时 prompt**。
    #   ⇒ 换成真入口。**只写盘上真有的路径**；n8n 不再谎报已在运行。
    lines.append("\n> 唯一门（真入口）: run_task(\"<cap_id>\", {...payload})")
    lines.append("> CLI 同一条门: python tools/codex-scripts/five-dim.py cap <cap_id> '{...}'")
    lines.append("> 缺授权会**如实报缺**（作用域见 `gbt_allinone/security/policy.py`）；"
                 "**AI 无权给自己发授权**，只由主人在终端发放。")
    return '\n'.join(lines)
# ══════════════════════════════════════════════════════════════
# Layer 3 — 瞬间调配：从注册表直接路由到cap
# ══════════════════════════════════════════════════════════════
def _instant_dispatch(cap_id: str, action: str, params: dict, timeout: int = 15) -> dict:
    """
    零延迟cap调用 — 从注册表验证cap存在后直接执行
    不依赖关键词匹配，精准按cap_id+action路由
    """
    index = _load_cap_index()
    if cap_id not in index:
        return {"ok": False, "error": f"cap '{cap_id}' 不在注册表，共{len(index)}个cap"}
    info = index[cap_id]
    if info.get('status') != 'ok':
        return {"ok": False, "error": f"{cap_id} 状态: {info.get('status')}"}
    if action not in info.get('actions', []):
        available = info.get('actions', [])
        return {"ok": False, "error": f"{cap_id} 无动作'{action}'，可用: {available}"}
    run_py = _CAPS_ROOT / cap_id / "run.py"
    if not run_py.exists():
        return {"ok": False, "error": f"{cap_id}/run.py 不存在"}
    try:
        r = subprocess.run(
            [sys.executable, str(run_py), action,
             json.dumps(params, ensure_ascii=False)],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(_SANDBOX_ROOT), encoding="utf-8", errors="replace"
        )
        raw = (r.stdout or "").strip()
        if raw:
            try:
                return json.loads(raw)
            except Exception as _e:
                # ── 2026-09-22 修：这里原本是 `except: return {"ok": True, "result": raw[:500]}`
                # 病：子进程崩了但 stdout 有半截非 JSON，会被**当成成功**上报。
                # 这正是 coding_discipline.py:74 那条不变量要打的形态 ——
                # **把失败报成成功**。而且它同时踩两条铁律：
                #   铁律 6 严禁假执行（假成功）
                #   铁律 5 疑故障必追根因（这里把故障吞了，根因再也追不到）
                # 现在：如实报失败，并把 r.stdout / r.stderr / 退出码一起交出来，
                # 便于追根因；`raw[:200]` 只作证据，不作结论。
                return {"ok": False,
                        "error": "子进程输出不是合法 JSON（不当作成功）",
                        "error_class": "parse_error",
                        "json_error": str(_e)[:120],
                        "returncode": r.returncode if hasattr(r, "returncode") else None,
                        "raw_head": raw[:200],
                        "stderr_head": (r.stderr or "")[:200]}
        return {"ok": False, "error": (r.stderr or "")[:200]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"{cap_id} 超时({timeout}s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}
# ══════════════════════════════════════════════════════════════
# 🧠 Layer 1 — 强制首注入自我认知（Agent驱动必经路径）
# 这是第一块加载，不允许缺失，不允许降级为内建备用
# ══════════════════════════════════════════════════════════════
_AWARENESS_PATHS = [
    # ── 2026-09-22 清依赖：删掉两条指向框架**外部**的路径 ──────────────
    # 原文里这两条是：
    #     Path.home() / "GBT-JXDWD" / "sandbox" / "GBT_自我认知_LIVE.md"
    #     Path.home() / "GBT-JXDWD" / "sandbox" / "caps" / "cloud_llm" / "self_knowledge_v5.py"
    #
    # 为什么删（实测，见 delivery/20260922-自我认知失真与框架核心无镜像门-根因报告.md）：
    #   ① 那份 LIVE.md 是 2026-07-21 的，写着"119 个能力模块 / 14 个域"，
    #      而盘上真身是 158 能力位 / 29 域 ---- 两份都对不上。
    #   ② 那份 self_knowledge_v5.py 是 **v5.0 时代的能力目录**（total_caps: 110）：
    #      里面 369 个标识符，**只有 3 个在 caps_registry 里**（autopilot/bluetooth/voice），
    #      另外 366 个（abliterator / agency / design_brain / self_evolve / dev_cpu …）
    #      **属于另一个系统** ---- 它不是"我们缺的部分"，是"别人项目的自述"。
    #
    # ⇒ 结论：框架不该靠读一个外部沙箱才知道自己是谁。
    #   **一份框架，一份自我认知。** 活口就在 caps_registry，不在别人的目录里。
    #
    # 保留的两条都在框架内部；若都不存在，则落到下面重写过的 _BUILTIN_AWARENESS
    # （它不再罗列任何能力名，改成指向活口 + 自校验命令）。
    _SANDBOX_ROOT / "GBT_自我认知_LIVE.md",
    _THIS_DIR / "self_knowledge_v5.py",
]
_awareness_cache: str = ""
_awareness_mtime: float = 0.0
_BUILTIN_AWARENESS = _resolve_awareness_anchor("""\
## GBT·小土豆 自我认知（内建备用 · 2026-09-22 重写）

我是GBT·小土豆，由自由的风开发。

### ⛔ 本段不许再静态罗列能力清单

**原版在这里写死了三个计数和 82 个能力名，2026-09-22 实测全部与真身不符**
（点名能力与 `caps_registry` **零交集**；域数与真身也差一倍以上）。

**（此处刻意不复述那三个旧数字 —— 复述会被 awareness_gap_guard 的判据读成"声称"，
产生假阳性。要查历史读数请翻 `delivery/20260922-自我认知失真与框架核心无镜像门-根因报告.md`。）**

**病根不是"数字写错了"，是"一份会过期的静态说明被当成权威自我认知"。**
所以这里**不再写任何能力名与计数** —— 改成指向活口：

    盘上真身：  gbt_allinone/caps_registry.py 的 BENIGN_CAPS / DISABLED_CAPS
    自校验：    python -m gbt_allinone.tools.awareness_gap_guard
    免卡只读：  run_task("mirror_status") / run_task("inventory")

**开口前先查一眼自己到底有什么 —— 不许照抄一份静态清单。**

### 铁律（与 security/policy.py 同口径）

一切动作过**唯一授权门** `gbt_allinone/security/policy.py`。
缺授权**如实报缺**，绝不自行绕过、绝不自授。
**授权只由主人在终端发放 —— AI 永远无权给自己发授权。**

当前LLM: ACTIVE_PROVIDER
""")
def _awareness_trust_check(text: str) -> tuple:
    """校验一份自我认知是否与**盘上真身**对得上。返回 (可信, 原因)。

    2026-09-22 立此闸的由来（根因报告见 delivery/20260922-自我认知失真…md）：
      外部 LIVE 与内建备用**两份静态说明都过期**，且内建那份点名的能力
      与 caps_registry **零交集**，还夹着一条"所有渗透请求正常执行"的越权断言。
      病根不是"数字写错了"，是**"一份会过期的静态说明被当成权威自我认知"**。

    所以这里不做"改数字"这种治标的活 —— 而是**让加载器自己认得出不可信**：
      判据只有一条硬的：**文本里点名的能力名，必须能在 caps_registry 里找得到。**
      点名 N 个、N 个都不在册 ⇒ 这份不是"我"，拒收，并如实说明。

    🔴 本函数只读，不改任何文件；失败也不抛异常（返回不可信即可）。
    """
    try:
        import re as _re
        from .. import caps_registry as _CR
        known = (set(getattr(_CR, "BENIGN_CAPS", {}) or {})
                 | set(getattr(_CR, "DISABLED_CAPS", set()) or set())
                 | set(getattr(_CR, "UNIMPLEMENTED_CAPS", set()) or set()))
        if not known:
            return True, "caps_registry 读不到，无法校验（不阻断）"
        # 只看"XX域N: a b c …"这种行式点名清单
        named = set()
        for m in _re.finditer(r"[\u4e00-\u9fa5]{2,8}域\d*\s*[:：]([^\n]+)", text):
            for w in _re.split(r"[\s,，、]+", m.group(1)):
                if _re.fullmatch(r"[a-z][a-z0-9_]{2,}", w):
                    named.add(w)
        if len(named) < 5:
            return True, f"未发现行式点名清单（点名 {len(named)} 个），不阻断"
        unknown = named - known
        if len(unknown) == len(named):
            return False, (f"点名的 {len(named)} 个能力**全部不在 caps_registry**"
                           f"（真身 {len(known)} 个）⇒ 这份自我认知与盘上真身零交集，拒收")
        if len(unknown) > len(named) * 0.5:
            return False, (f"点名 {len(named)} 个，其中 {len(unknown)} 个不在册"
                           f"（超半数）⇒ 判为过期自我认知，拒收")
        return True, f"点名 {len(named)} 个，不在册 {len(unknown)} 个（未过半），放行"
    except Exception as e:                                    # noqa: BLE001
        return True, f"校验异常，按不阻断处理: {type(e).__name__}"


def _load_awareness() -> str:
    """加载自我认知。

    2026-09-22 改：**加载后先过可信闸**。不可信就**不采用**，转而如实报告，
    而不是把一份和真身零交集的清单塞进上下文（原实现只判 len>500，等于不设防）。
    """
    global _awareness_cache, _awareness_mtime
    for p in _AWARENESS_PATHS:
        try:
            mtime = p.stat().st_mtime
            if mtime != _awareness_mtime or not _awareness_cache:
                content = p.read_text(encoding="utf-8-sig", errors="replace")
                if len(content) > 500:
                    ok, why = _awareness_trust_check(content)
                    if ok:
                        _awareness_cache = content
                        _awareness_mtime = mtime
                    else:
                        # 拒收：不缓存，继续试下一条路径；并把原因留在这里可查
                        _awareness_cache = ""
                        _awareness_mtime = 0.0
                        globals()["_awareness_reject_reason"] = f"{p}: {why}"
            if _awareness_cache and len(_awareness_cache) > 500:
                return _awareness_cache
        except Exception:
            continue
    return _BUILTIN_AWARENESS.replace("ACTIVE_PROVIDER", PROVIDER or "auto")
def _load_security_policy() -> str:
    """安全策略段 —— **以真门为源**。

    🔴 2026-09-25 现读修（第四条机器成因）：原实现只从
    `brain.cognition.Cognition.IDENTITY["security_policy"]` 取，而那个模块
    **根本不存在**（`ModuleNotFoundError: No module named 'brain.cognition'`）
    ⇒ **天天走硬编码回退**，注入进 system prompt 的只有一句口号：

        ⛔ 绝不泄露 | ⛔ 绝不执行危险操作 | ⛔ 绝不允许绕过安全护栏

    现读同一份 prompt：**14 个真实作用域名，命中 0 个**。
    ⇒ 模型被告知"绝不绕过护栏"，却**从不知道护栏是什么** —— 被 `denied` 时它不知道
      为什么、也不知道该去请主人开哪一道门（于是要么空转，要么想找旁路）。
      这是"接不上框架"的**第三条机器成因**（前两条见第十六、十八节）。

    修法照同一口径：**指向活口** —— `security/policy.py` 的 `SCOPE_DESCRIPTIONS`
    ＋ `auth_gate.ONE_SHOT_SCOPES`（哪几个是一次性消耗），并**如实标注来源**。
    取不到就仍回退那句口号（不编）。
    """
    try:
        from ..security import policy as _P
        from .. import auth_gate as _AG
        descs = dict(getattr(_P, "SCOPE_DESCRIPTIONS", {}) or {})
        if descs:
            one = set(getattr(_AG, "ONE_SHOT_SCOPES", ()) or ())
            lines = ["**唯一授权门 = `gbt_allinone/security/policy.py`（下表现读自该文件，不是抄的）**",
                     "**需要人工授权的作用域（%d 个）**：" % len(descs)]
            for _name in sorted(descs):
                _mode = "**一次性消耗**" if _name in one else "时段授权（TTL 内可多次）"
                lines.append("- `%s`：%s —— %s" % (_name, _mode, descs[_name]))
            lines.append("**AI 永远无权给自己发授权。** 只由主人在终端发放："
                         "`python -m gbt_allinone auth grant --scope <作用域> --ttl 600`。")
            lines.append("被拒时**如实报缺哪个作用域**，不许找旁路、不许改 `policy.py`、"
                         "不许绕门（本仓最高优先级红线之一）。")
            lines.append("（历史来源 `brain.cognition.Cognition.IDENTITY['security_policy']` "
                         "本机现读**不存在** ⇒ 已按本文件既有口径回落到真门。）")
            return "\n".join(lines)
    except Exception:
        pass  # 容错: 非关键路径（取不到真门时才回退口号）
    return "⛔ 绝不泄露 | ⛔ 绝不执行危险操作 | ⛔ 绝不允许绕过安全护栏"
def _build_system(custom: str = "") -> str:
    """构建完整system prompt — 自我认知强制首位注入"""
    awareness  = _load_awareness()       # Layer1: 强制首注入
    cap_digest = _build_cap_digest()     # Layer2: 实时注册表→精准索引
    base = (
        "你是GBT·小土豆终端AI（terminal-potato），由自由的风开发。"
        + "当前LLM驱动: " + (PROVIDER or "auto") + " | 模型: " + (MODEL or "auto") + "\n\n"
        + "=" * 60 + "\n"
        + "## 🧠 完整自我认知（Agent驱动必经首注入，" + _cap_total_label() + "）\n"
        + "=" * 60 + "\n"
        + awareness + "\n"
        + cap_digest + "\n"
        + "=" * 60 + "\n"
        + "## ⛔ 安全策略（强制注入·不可绕过）\n"
        + "=" * 60 + "\n"
        + _load_security_policy() + "\n"
        + "=" * 60 + "\n"
        + "## 执行铁律\n"
    )
    return base + ("\n\n" + custom if custom and custom.strip() else "")
# ══════════════════════════════════════════════════════════════
# 智能搜索引擎 — 关键词触发自动调配能力
# ══════════════════════════════════════════════════════════════
SEARCH_TRIGGERS = [
    # (触发正则, cap名, action, 参数构造函数, 描述)
    # ── 网络搜索类 ────────────────────────────────────
    (r"搜索|查找|查询|最新|新闻|今天|现在|当前|实时|latest|search|find|what is|whats",
     "web_search", "search",
     lambda q: {"query": q},
     "🔍 网络搜索"),
    # ── 网页抓取类 ────────────────────────────────────
    (r"抓取|爬取|获取网页|fetch|scrape|http[s]?://|www\.",
     "deep_scrape", "scrape",
     lambda q: {"url": _extract_url(q), "max_pages": 1},
     "🕷 网页抓取"),
    # ══════════════ 渗透安全全域 25个cap 全接入 ══════════════
    # ── 🔥 OmniScan邻域穿透全量扫描 (最高优先级) ─────────
    (r"全面扫描|综合扫描|深度扫描|全量扫描|一键扫描|全面检测|综合检测|渗透测试.*整站|整站.*扫描|omniscan|病毒扫描|恶意代码检测|CVE检测|邻域穿透|全方位|亿万触手",
     "omni_scan", "scan",
     lambda q: {"target": _extract_url(q) or _extract_domain(q) or q[:80]},
     "🔥 OmniScan全量"),
    # ── 端口/IP侦察 ──────────────────────────────────
    (r"扫描端口|端口扫描|nmap|port.?scan|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|开放端口|服务探测",
     "port_scanner", "scan",
     lambda q: {"target": _extract_ip(q) or _extract_domain(q), "ports": "1-1000"},
     "🔭 端口扫描"),
    # ── 子域名枚举 ───────────────────────────────────
    (r"子域|subdomain|子域名|域名枚举",
     "subdomain_enum", "enum",
     lambda q: {"domain": _extract_domain(q)},
     "🗺 子域枚举"),
    # ── SQL注入检测 ──────────────────────────────────
    (r"sql注入|sqli|sql inject|注入测试|注入漏洞",
     "sqli_tester", "test",
     lambda q: {"url": _extract_url(q) or ""},
     "💉 SQL注入"),
    # ── XSS检测 ──────────────────────────────────────
    (r"xss|跨站|cross.?site|script inject",
     "xss_tester", "test",
     lambda q: {"url": _extract_url(q) or ""},
     "⚡ XSS检测"),
    # ── 系统状态 ──────────────────────────────────────
    (r"系统状态|cpu|内存|磁盘|进程|system status|memory usage|disk",
     "system_status", "check",
     lambda q: {},
     "📊 系统状态"),
    # ── 屏幕感知 ──────────────────────────────────────
    (r"屏幕上|看到|截图|ocr|当前窗口|screen|看看现在",
     "ai_vision", "ocr",
     lambda q: {},
     "👁 屏幕感知"),
    # ── 浏览器操控 ────────────────────────────────────
    (r"打开网页|浏览器|navigate|browser|打开.*网站|访问.*网址",
     "browser_ctrl", "navigate",
     lambda q: {"url": _extract_url(q) or "https://www.baidu.com", "headless": False},
     "🌐 浏览器"),
    # ── DNS查询 ───────────────────────────────────────
    (r"dns|域名解析|ip地址|whois|nslookup",
     "dns_lookup", "lookup",
     lambda q: {"domain": _extract_domain(q) or q[:50]},
     "🔗 DNS查询"),
    # ── 子代理执行 ────────────────────────────────────
    (r"子代理|多步任务|复杂.*任务.*执行|思维导图.*执行|分步.*完成|隔离.*执行",
     "sub_agent_mgr", "spawn",
     lambda q: {"task": q, "auto_run": False},
     "🤖 子代理"),
    # ── SSTI模板注入 ─────────────────────────────────
    (r"ssti|模板注入|服务端模板|jinja2.*注入|twig.*注入|模板.*漏洞|template.*injection",
     "ssti_tester", "test",
     lambda q: {"url": _extract_url(q) or ""},
     "🧩 SSTI模板注入"),
    # ── XXE外部实体 ───────────────────────────────────
    (r"xxe|xml.*注入|外部实体|xml.*实体.*注入|xxe.*测试|doctype.*注入",
     "xxe_tester", "test",
     lambda q: {"url": _extract_url(q) or ""},
     "📋 XXE实体注入"),
    # ── IDOR越权 ─────────────────────────────────────
    (r"idor|越权漏洞|水平越权|垂直越权|对象引用|insecure.*direct.*object",
     "idor_tester", "test",
     lambda q: {"url": _extract_url(q) or ""},
     "🔏 IDOR越权"),
    # ── Payload生成 ───────────────────────────────────
    (r"反弹shell|payload.*生成|载荷生成|马子|木马.*生成|shellcode|攻击.*载荷|webshell.*生成",
     "payload_gen", "reverse_shell",
     lambda q: {"type": "all", "host": _extract_ip(q) or "YOUR_IP"},
     "💣 Payload生成"),
    # ── 提权检测 ──────────────────────────────────────
    (r"提权|privilege.*escalation|suid.*提权|sudo.*提权|本地提权|权限提升|priv.*esc",
     "priv_esc", "quick",
     lambda q: {},
     "⬆ 提权检测"),
    # ── OSINT情报 ─────────────────────────────────────
    (r"osint|情报收集|shodan|fofa|censys|zoomeye|邮件收集|指纹识别|目标侦察|技术栈识别",
     "osint_tool", "search",
     lambda q: {"target": _extract_domain(q) or _extract_ip(q) or q[:50]},
     "🕵 OSINT情报"),
    # ── 密码喷洒 ──────────────────────────────────────
    (r"密码喷洒|password.*spray|喷洒攻击|批量爆破账号|弱密码喷洒|账号.*锁定.*绕过",
     "pass_spray", "wordlist",
     lambda q: {"company": q[:30]},
     "💧 密码喷洒"),
    # ── API安全 ───────────────────────────────────────
    (r"api.*安全|api.*测试|graphql.*安全|接口.*安全|rest.*api.*漏洞|api.*越权|swagger.*安全|openapi.*测试",
     "api_vuln", "fuzz",
     lambda q: {"base_url": _extract_url(q) or q[:80]},
     "🔌 API安全"),
    # ── 代码执行 ──────────────────────────────────────
    (r"运行代码|执行.*python|run.*code|exec.*script",
     "code_exec", "run",
     lambda q: {"code": q, "lang": "python"},
     "⚙️ 代码执行"),
    # ── 数据库查询 ────────────────────────────────────
    (r"查数据库|sql query|select.*from|数据库查询",
     "database", "query",
     lambda q: {"sql": q[:200]},
     "🗃 数据库"),
    # ── 文件操作 ──────────────────────────────────────
    (r"读文件|写文件|read file|write file|文件内容",
     "file_operation", "read",
     lambda q: {"path": _extract_path(q)},
     "📁 文件操作"),
]
# ── 辅助提取函数 ──────────────────────────────────────────────
def _extract_url(text: str) -> str:
    m = re.search(r'https?://[^\s\'"]+', text)
    return m.group() if m else ""
def _extract_ip(text: str) -> str:
    m = re.search(r'\d{1,3}(?:\.\d{1,3}){3}', text)
    return m.group() if m else ""
def _extract_domain(text: str) -> str:
    m = re.search(r'(?:https?://)?([a-zA-Z0-9][-a-zA-Z0-9.]+\.[a-zA-Z]{2,})', text)
    return m.group(1) if m else ""
# ═══════════════════════════════════════════════════════════
#  执行入口 — 路由目标: run(action, params)
# ═══════════════════════════════════════════════════════════
class _HttpError(RuntimeError):
    """带状态码的出站错误。

    ⚠️ 消息格式**一字不改**（`HTTP %s: %s`）—— `tests/test_ai_audit.py` 用
    `assertRaises(RuntimeError)` + 审计行 `status=429` 钉着它。
    新增的只是 `.status` 属性：统一密钥网关靠它做**错误分类**（换不换道）。
    """

    def __init__(self, status, msg):
        super().__init__(msg)
        self.status = int(status or 0)


# 推理模型的「推理吃光预算」标记（agents / NVIDIA 都会踩，见 _call_once）。
# 调用方据此**自适上调 max_tokens 后重试同一家** —— 同一家重试 ≠ 换道。
REASONING_STARVED = "content 为空但 reasoning_content 非空 —— max_tokens 被推理吃光"
_REASONING_ESCALATE_CAP = 8192

def _safe_json(url, body, headers, timeout, *, audit_provider=None,
               audit_model=None, audit_session_id=None, method="POST"):
    """统一出站口：net_guard 守门 + 应用层 AI 审计（只记元数据，不记内容）。

    R120 实测根因：本模块此前直连 urllib.request.urlopen —— 既绕过 net_guard 的
    SSRF/端口/体积守门，也不落应用层 AI 审计。tests/test_ai_audit.py 早就把
    `_safe_json` 当规格写好，实现却从未存在（调用即 AttributeError）。
    """
    from ..security import net_guard as _ng
    from ..security import ai_audit as _audit
    from ..security import policy as _policy
    provider = audit_provider or PROVIDER or "openai"
    ctx = _audit.begin(provider, url,
                       model=audit_model or (body or {}).get("model"),
                       request_body=body, headers=headers,
                       session_id=audit_session_id)
    payload = json.dumps(body).encode("utf-8") if body is not None else None
    try:
        response = _ng.safe_request_json(
            url, method=method, headers=headers, body=payload, timeout=timeout,
            max_bytes=8_000_000, allow_private=_policy.is_trusted())
    except Exception as exc:  # noqa: BLE001
        _audit.finish(ctx, ok=False, error=exc)
        raise
    status = int(response.get("status") or 0)
    data = response.get("json")
    if status >= 400 or not isinstance(data, dict):
        _audit.finish(ctx, status=status, ok=False, response_text=response.get("text"))
        raise _HttpError(status, "HTTP %s: %s" % (status, str(response.get("text") or "")[:300]))
    _audit.finish(ctx, status=status, ok=True, response=data)
    return data


def _call_once(wire, base_url, model, api_key, body, system, prompt, timeout, provider):
    """按协议族发**一次**请求，返回回复文本。

    本函数只管「怎么发」；**重试与换道是调用方的事**（`_safe_json` 只出网一次）。
    """
    if wire == "anthropic":
        # ── Anthropic Claude 原生 Messages API ──
        _url = base_url.rstrip("/") + "/v1/messages"
        _body = {"model": model, "max_tokens": body.get("max_tokens", 2000),
                 "system": system,
                 "messages": [{"role": "user", "content": prompt[:6000]}]}
        _hdrs = {"Content-Type": "application/json", "x-api-key": api_key,
                 "anthropic-version": "2023-06-01"}
        data = _safe_json(_url, _body, _hdrs, timeout,
                          audit_provider=provider or "anthropic", audit_model=model)
        return data["content"][0]["text"]
    if wire == "gemini":
        # ── Google Gemini 原生 generateContent API ──
        _url = (base_url.rstrip("/") + "/models/" + model
                + ":generateContent?key=" + api_key)
        _body = {"contents": [{"role": "user", "parts": [{"text": prompt[:6000]}]}],
                 "systemInstruction": {"parts": [{"text": system}]}}
        data = _safe_json(_url, _body, {"Content-Type": "application/json"}, timeout,
                          audit_provider=provider or "gemini", audit_model=model)
        return data["candidates"][0]["content"]["parts"][0]["text"]
    # ── OpenAI 兼容（agnes/deepseek/kimi/openai/NVIDIA/自定义/本地）──
    _hdrs = ({"Content-Type": "application/json", "Authorization": "Bearer " + api_key}
             if "abliteration" not in base_url else
             {"Content-Type": "application/json", "x-api-key": api_key})
    _body = dict(body)
    _body["model"] = model
    data = _safe_json(base_url.rstrip("/") + "/chat/completions", _body, _hdrs, timeout,
                      audit_provider=provider or PROVIDER, audit_model=model)
    _msg = (data.get("choices") or [{}])[0].get("message") or {}
    _txt = _msg.get("content")
    if not _txt:
        # 🔴 推理模型的坑（2026-09-27 实弹取证，agnes 与 NVIDIA 都会踩）：
        #    max_tokens 太小会被 reasoning 吃光 ⇒ **HTTP 200 但 content 为空**。
        #    这不是成功。报成 422（参数问题）⇒ 按 I2 **不换道**，
        #    免得把「我们参数写小了」伪装成「模型不行」。
        #    调用方看到 REASONING_STARVED 标记会**自适上调 max_tokens 后重试同一家**
        #    （同一家重试 ≠ 换道，不违反 I1/I2）。
        if _msg.get("reasoning_content"):
            raise _HttpError(422, "HTTP 422: %s（provider=%s）"
                             % (REASONING_STARVED, provider or PROVIDER))
        raise _HttpError(422, "HTTP 422: 上游 200 但 content 为空（provider=%s）"
                              % (provider or PROVIDER))
    return _txt


def run(action=None, **params):
    """LLM网关路由入口 — chat: 推理对话; status: 网关状态"""
    # 本次落点要回写模块级全局（vision_cap 等下游读 BASE_URL/MODEL）——
    # `global` 必须在函数首部声明：本函数前面几处已在读这些名字。
    global PROVIDER, API_KEY, BASE_URL, MODEL
    try:
        # ⛔ 触手独立密钥路由优先于 status 判断：有 purpose 参数时视为 chat 调用
        _purpose = str(params.get("purpose") or "").strip().lower()
        _is_tentacle_call = bool(_purpose)
        # ⛔ 兼容 L4 干跑 handler({}) 传 dict: 提取 action, 空则视为 status(静态, 不调LLM)
        if isinstance(action, dict):
            action = action.get("action") or next(iter(action), None)
        if action in ("status", "health", "list", "info") or (action is None and not _is_tentacle_call):
            _out = {
                "ok": True, "cap": "cloud_llm", "status": "ready",
                "key_chain": [k[0] for k in _KEY_CHAIN],
                "provider": PROVIDER or "auto",
            }
            # 挂上网关读数（选路是不是活的，看这里）。失败不影响 status 本身。
            try:
                from . import key_gateway as _KG
                _out["gateway"] = _KG.run("status")
            except Exception:                            # noqa: BLE001
                _out["gateway"] = None
            return _out
        # 默认 chat: 构建系统提示并转发到LLM
        prompt = params.get("prompt", params.get("q", params.get("message", "")))
        system = _build_system(custom=params.get("system", ""))
        _want_max_tokens = int(params.get("max_tokens", 2000))
        body = {
            "model": params.get("model", MODEL or "deepseek-flash"),
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": prompt[:6000]}],
            "temperature": params.get("temperature", 0.7),
            "max_tokens": _want_max_tokens,
        }
        # ══════════════════════════════════════════════════════════════
        # 选路：向统一密钥网关要「本次该按什么顺序试」—— **每次调用现算**
        # ══════════════════════════════════════════════════════════════
        # 🔴 血账（这就是「一直失灵」的机械根因）：
        #    旧实现在**模块导入时**跑一次 for-loop，找到第一个有 key 的 provider
        #    就 `break`，把 PROVIDER/API_KEY/BASE_URL/MODEL 四个模块级全局**定型**，
        #    此后整个进程生命周期不再变；而且 HTTP 4xx/5xx 只被外层
        #    `except Exception` 吞成 `{"ok": False}` —— **不重试、不换道**。
        #    ⇒ 额度耗尽(402)/限流(429)/密钥失效(401) 任一发生 = **硬断连**。
        #    现在改为「每次现算 + 按错误分类处置」：
        #      能换道的换道（402/429/401/404），不能换道的如实报错（400/422，I2），
        #      全不可用时 fail-closed（不瞎挑、不静默降级）。
        from . import key_gateway as _KG
        # ── 触手维度密钥路由（2026-10-03）：按 purpose 选子 profile ──────────
        # 匹配到触手 profile → 直接使用该 profile 的 key 调 agnes，绕过 key_gateway
        # （_purpose 已在函数上方 status 判断前计算，此处复用）
        _matched_prof = None
        for _kw, _prof in _PURPOSE_ROUTING_MAP.items():
            if _kw in _purpose:
                _matched_prof = _prof
                break
        if _matched_prof:
            _tentacle_key = os.environ.get(f"{_matched_prof.upper()}_API_KEY") or ""
            if not _tentacle_key:
                try:
                    from ..deepseek_key import _unprotect_dpapi as _dk_unprotect
                    from pathlib import Path as _P
                    _dpapi_path = _P(__file__).parent.parent / "store" / "secrets" / f"{_matched_prof}_api.dpapi"
                    if _dpapi_path.exists():
                        _tentacle_key = _dk_unprotect(_dpapi_path.read_bytes(), profile=_matched_prof).decode().strip()
                except Exception:
                    pass
            if _tentacle_key:
                # 直接用触手独立 key 调 agnes，不走 key_gateway 选路
                _timeout_t = int(params.get("timeout", 60))
                _rt = _call_once(
                    "openai_compatible",
                    "https://apihub.agnes-ai.com/v1",
                    "agnes-2.5-flash",
                    _tentacle_key,
                    body, system, prompt,
                    _timeout_t,
                    "agnes",
                )
                return {
                    "ok": True, "reply": _rt, "provider": "agnes",
                    "model": "agnes-2.5-flash",
                    "key_masked": _tentacle_key[:8] + "****",
                    "brand": _KG.BRAND_TAG,
                    "tentacle_profile": _matched_prof,
                    "auto_switched": False, "tried_before": [],
                }
        # 无触手 key 或无匹配：走原有 key_gateway 选路
        _prefer = str(params.get("provider") or os.environ.get("GBT_LLM_PROVIDER") or "")
        _pl = _KG.plan(need_tokens=int(params.get("need_tokens", 0) or 0), prefer=_prefer)
        if not _pl.get("ok"):
            return {"ok": False, "error": _pl.get("error"), "fail_closed": True,
                    "brand": _KG.BRAND_TAG, "candidates": _pl.get("candidates"),
                    "how_to_fix": _pl.get("how_to_fix"),
                    "hint": "补密钥：deepseek_key set --profile <名>；或 op=reset 清运行态"}
        _order = [o["provider"] for o in (_pl.get("order") or []) if o.get("alive")]
        _timeout = int(params.get("timeout", 60))
        _max_retries = int(params.get("retries", 2))  # ⛔ 生产打磨: 瞬时错误重试2次+退避
        _tried = []
        for _prov in _order:
            _mat = _KG.materialize(_prov)
            if not _mat.get("ok"):
                _tried.append({"provider": _prov, "skipped": _mat.get("error")})
                continue
            # 推理模型要够大的 max_tokens，否则 content 会被 reasoning 吃光
            # （HTTP 200 也算失败）——网关在声明层给了 min_max_tokens 下限。
            _body = dict(body)
            _body["max_tokens"] = max(_want_max_tokens,
                                      int(_mat.get("min_max_tokens", 0) or 0))
            # 让下游（vision_cap 等读 BASE_URL/MODEL 的地方）看到**本次真实落点**
            PROVIDER, API_KEY, BASE_URL, MODEL = (_prov, _mat["key"],
                                                  _mat["url"], _mat["model"])
            _err, _st, _d = "", None, {}
            for _attempt in range(_max_retries + 1):
                try:
                    _reply = _call_once(_mat["wire"], _mat["url"], _mat["model"],
                                        _mat["key"], _body, system, prompt,
                                        _timeout, _prov)
                    _KG.note_result(_prov, ok=True)
                    return {"ok": True, "reply": _reply, "provider": _prov,
                            "model": _mat["model"], "key_masked": _mat["masked"],
                            "brand": _KG.BRAND_TAG,
                            "auto_switched": bool(_pl.get("auto_switched")),
                            "switched_from": _pl.get("switched_from"),
                            "tried_before": [t["provider"] for t in _tried]}
                except Exception as _e:                  # noqa: BLE001
                    _err = str(_e)[:300]
                    _st = getattr(_e, "status", None)
                    # 🔴 推理模型把预算吃光 ⇒ **同一家自适上调 max_tokens 后重试**。
                    #    同一家重试 ≠ 换道（不违反 I1/I2），而且这是唯一能修好的办法：
                    #    换道只会把这个模型能答的问题推给别人。
                    if REASONING_STARVED in _err and _attempt < _max_retries:
                        _new = min(max(_body["max_tokens"] * 4, 512),
                                   _REASONING_ESCALATE_CAP)
                        if _new > _body["max_tokens"]:
                            print("[key_gateway] 推理吃光预算：%s max_tokens %d → %d 后重试"
                                  % (_prov, _body["max_tokens"], _new), file=sys.stderr)
                            _body["max_tokens"] = _new
                            continue
                    _d = _KG.note_result(_prov, ok=False, status=_st, error=_err)
                    # 决策拆两维（血账：早先把这两件事挤在一个 `failover` 里，
                    # 结果 transient 在 `not failover` 处**立即 return**，
                    # 重试分支成死代码 ⇒ 一次网络抖动 = 硬断连）：
                    #   ① 同家再试一次？  ② 试不动了要不要往下走？
                    if not _d.get("retry_same") and not _d.get("escalate"):
                        # bad_request / unknown ⇒ **硬停**：我们自己错了，换谁都没用
                        return {"ok": False, "error": _err, "provider": _prov,
                                "err_class": _d.get("err_class"), "failover": False,
                                "why_no_failover": _d.get("action"),
                                "brand": _KG.BRAND_TAG}
                    if _d.get("retry_same") and _attempt < _max_retries:
                        time.sleep(1 + _attempt * 2)     # 退避: 1s/3s
                        continue
                    break                                # 本家到此为止 → 下一家
            _tried.append({"provider": _prov, "err_class": (_d or {}).get("err_class"),
                           "status": _st, "error": _err})
        return {"ok": False, "fail_closed": True, "brand": _KG.BRAND_TAG,
                "error": "全部 %d 条通道都试过且都失败 —— 如实报错，不静默降级"
                         % len(_order),
                "tried": _tried,
                "how_to_fix": "补密钥 / op=reset 清运行态 / 等冷却到期"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}
if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "status"
    params_str = sys.argv[2] if len(sys.argv) > 2 else "{}"
    try:
        params = json.loads(params_str)
    except Exception:
        params = {}
    result = run(action, **params)
    print(json.dumps(result, ensure_ascii=False, default=str))
def do_status(params=None):
    return {"ok": True, "cap": "cloud_llm", "status": "ready"}
HANDLERS = {
    
    "chat": run,
    # ⛔ status 必须走静态分支: handler({}) → run("status") — 否则干跑误触发LLM(7s超时)
    "status": lambda p: run("status", **(p if isinstance(p, dict) else {})),
}
