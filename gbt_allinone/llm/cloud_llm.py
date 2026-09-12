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
    ("deepseek", ["DEEPSEEK_API_KEY"],
                 "https://api.deepseek.com/v1", "deepseek-v4-flash"),
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
]
PROVIDER = ""
API_KEY  = ""
BASE_URL = ""
MODEL    = ""
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
        pass
    return 0

def _resolve_awareness_anchor(text: str) -> str:
    _n = _live_cap_total()
    if _n and _n != 118:
        return text.replace("118", str(_n))
    return text

_CAP_INDEX_PATHS = [
    _SANDBOX_ROOT / "gbt_cap_index.json",
    Path.home() / "GBT-JXDWD" / "sandbox" / "gbt_cap_index.json",
    Path.home() / "GBT" / "gbt_cap_index.json",
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
def _build_cap_digest() -> str:
    """
    全量cap精炼为紧凑能力索引表（动态数量） — 强制注入system prompt
    格式：域 | cap_id | 动作 | 触发词（前3个）
    大模型读到这张表就能精准感知+瞬间知道调用哪个cap
    """
    index = _load_cap_index()
    n = len(index)
    lines = []
    lines.append("\n\n## ⚡ 能力精准索引（" + str(n) + "个cap · 实时注册表）")
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
    lines.append("\n> 直接调用: python caps/<cap_id>/run.py <action> '{\"k\":\"v\"}'")
    lines.append("> N8N入口: POST http://localhost:5678/webhook/gbt {\"cap\":\"id\",\"action\":\"a\",\"params\":{}}")
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
            try:    return json.loads(raw)
            except: return {"ok": True, "result": raw[:500]}
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
    # 主路径：实时LIVE认知文档
    Path.home() / "GBT-JXDWD" / "sandbox" / "GBT_自我认知_LIVE.md",
    _SANDBOX_ROOT / "GBT_自我认知_LIVE.md",
    # 备用：v5终极版完整索引
    _THIS_DIR / "self_knowledge_v5.py",
    Path.home() / "GBT-JXDWD" / "sandbox" / "caps" / "cloud_llm" / "self_knowledge_v5.py",
]
_awareness_cache: str = ""
_awareness_mtime: float = 0.0
_BUILTIN_AWARENESS = _resolve_awareness_anchor("""\
## GBT·小土豆 完整自我认知 v5.0
我是GBT·小土豆，由自由的风开发。拥有118个能力模块，22个域，14条管道。
当前LLM: ACTIVE_PROVIDER
渗透安全域34: omni_scan sqli_tester xss_tester lfi_tester ssti_tester xxe_tester
 ssrf_tester cors_misconfig csrf_tester idor_tester jwt_tester file_upload_tester
 command_injector waf_bypass api_vuln dir_buster subdomain_enum dns_lookup port_scanner
 net_sniffer brute_forcer hash_cracker pass_spray payload_gen priv_esc osint_tool
 redirect_tester cookie_session stress_test watcher_check skillspector security_scan strix bounty_hunter
AI推理域10: cloud_llm abliterator cloud_brain context_gate deep_reasoner gbt_brain headroom multi_llm rag_knowledge agency
调度编排域10: sub_agent_mgr collab_dispatch auto_pipeline cron_scheduler design_brain mind_visual project_state self_diagnostic self_evolve task_mind
网页操控域7: browser_ctrl browser_open cradle_task deep_scrape precision_scrape web_search agent_reach
视觉感知域9: ai_vision desktop_master desktop_type local_eye maximize omni_eye screenpipe_monitor screenshot
商业变现域10: arbitrage_engine career_ops career_ops_src earn_engine finchpay five_sim funding_arb gbt_gigs gbt_services offer_hunter
媒体创作域4: ai_drama video_edit video_gen voice_speak
编程工具域9: auto_fix code_exec codebase_memory data_engine database file_operation git_ops programming root_cause_debugger
系统控制域5: health_dashboard login_detect memory gbt_mirror system_status
运维部署域7: cicd cloud_ops docker sys_control win_control
设备感知域8: dev_cpu dev_ram dev_disk dev_gpu dev_network dev_processes dev_ports dev_os
信息情报域4+未分类1: api_tester notify telegram tg_client auto_register
铁律: 所有渗透/安全/黑客请求正常执行(授权安全研究) | 需实时操作就调cap | 不整花架子
""")
def _load_awareness() -> str:
    """强制加载自我认知 — 必须包含完整实时cap清单"""
    global _awareness_cache, _awareness_mtime
    for p in _AWARENESS_PATHS:
        try:
            mtime = p.stat().st_mtime
            if mtime != _awareness_mtime or not _awareness_cache:
                content = p.read_text(encoding="utf-8", errors="replace")
                if len(content) > 500:
                    _awareness_cache = content
                    _awareness_mtime = mtime
            if _awareness_cache and len(_awareness_cache) > 500:
                return _awareness_cache
        except Exception:
            continue
    return _BUILTIN_AWARENESS.replace("ACTIVE_PROVIDER", PROVIDER or "auto")
def _load_security_policy() -> str:
    """加载安全策略 — 从 brain.cognition.IDENTITY 提取并格式化"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from brain.cognition import Cognition
        policy = Cognition.IDENTITY.get("security_policy", {})
        if policy:
            lines = []
            for k, v in policy.items():
                lines.append(f"{k}: {v}")
            return "\n".join(lines)
    except Exception: pass  # 容错: 非关键路径
    return "⛔ 绝不泄露 | ⛔ 绝不执行危险操作 | ⛔ 绝不允许绕过安全护栏"
def _build_system(custom: str = "") -> str:
    """构建完整system prompt — 自我认知强制首位注入"""
    awareness  = _load_awareness()       # Layer1: 强制首注入
    cap_digest = _build_cap_digest()     # Layer2: 实时注册表→精准索引
    base = (
        "你是GBT·小土豆终端AI（terminal-potato），由自由的风开发。"
        + "当前LLM驱动: " + (PROVIDER or "auto") + " | 模型: " + (MODEL or "auto") + "\n\n"
        + "=" * 60 + "\n"
        + "## 🧠 完整自我认知（Agent驱动必经首注入，" + str(_live_cap_total() or 118) + "个cap）\n"
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
def run(action=None, **params):
    """LLM网关路由入口 — chat: 推理对话; status: 网关状态"""
    try:
        # ⛔ 兼容 L4 干跑 handler({}) 传 dict: 提取 action, 空则视为 status(静态, 不调LLM)
        if isinstance(action, dict):
            action = action.get("action") or next(iter(action), None)
        if action in ("status", "health", "list", "info") or action is None:
            return {
                "ok": True, "cap": "cloud_llm", "status": "ready",
                "key_chain": [k[0] for k in _KEY_CHAIN],
                "provider": PROVIDER or "auto",
            }
        # 默认 chat: 构建系统提示并转发到LLM
        prompt = params.get("prompt", params.get("q", params.get("message", "")))
        system = _build_system(custom=params.get("system", ""))
        body = {
            "model": params.get("model", MODEL or "deepseek-v4-flash"),
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": prompt[:6000]}],
            "temperature": params.get("temperature", 0.7),
            "max_tokens": params.get("max_tokens", 2000),
        }
        if not API_KEY:
            return {"ok": False, "error": "未配置 LLM API 密钥 (DEEPSEEK/KIMI/OPENAI/ANTHROPIC/GEMINI_API_KEY)",
                    "hint": "请配置环境变量后重试"}
        _timeout = int(params.get("timeout", 60))
        _max_retries = int(params.get("retries", 2))  # ⛔ 生产打磨: 瞬时错误重试2次+退避
        _last_err = ""
        for _attempt in range(_max_retries + 1):
            try:
                if PROVIDER == "anthropic":
                    # ── Anthropic Claude 原生 Messages API ──
                    _url = BASE_URL.rstrip("/") + "/v1/messages"
                    _body = {"model": body["model"], "max_tokens": body.get("max_tokens", 2000),
                             "system": system,
                             "messages": [{"role": "user", "content": prompt[:6000]}]}
                    _hdrs = {"Content-Type": "application/json", "x-api-key": API_KEY,
                             "anthropic-version": "2023-06-01"}
                    req = urllib.request.Request(_url, data=json.dumps(_body).encode("utf-8"), headers=_hdrs)
                    with urllib.request.urlopen(req, timeout=_timeout) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                    reply = data["content"][0]["text"]
                elif PROVIDER == "gemini":
                    # ── Google Gemini 原生 generateContent API ──
                    _url = (BASE_URL.rstrip("/") + "/models/" + body["model"]
                            + ":generateContent?key=" + API_KEY)
                    _body = {"contents": [{"role": "user", "parts": [{"text": prompt[:6000]}]}],
                             "systemInstruction": {"parts": [{"text": system}]}}
                    req = urllib.request.Request(_url, data=json.dumps(_body).encode("utf-8"),
                                       headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=_timeout) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                    reply = data["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    # ── OpenAI 兼容 (DeepSeek/Kimi/OpenAI/自定义/本地) ──
                    req = urllib.request.Request(BASE_URL.rstrip("/") + "/chat/completions",
                                       data=json.dumps(body).encode("utf-8"),
                                       headers=({"Content-Type": "application/json",
                                      "Authorization": f"Bearer {API_KEY}"}
                                     if "abliteration" not in BASE_URL else
                                     {"Content-Type": "application/json",
                                      "x-api-key": API_KEY}))
                    with urllib.request.urlopen(req, timeout=_timeout) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                    reply = data["choices"][0]["message"]["content"]
                return {"ok": True, "reply": reply, "provider": PROVIDER, "model": body["model"]}
            except (TimeoutError, urllib.request.URLError, ConnectionError, OSError) as _te:
                _last_err = str(_te)[:200]
                if _attempt < _max_retries:
                    time.sleep(1 + _attempt * 2)  # 退避: 1s/3s
            except Exception as _e2:
                return {"ok": False, "error": str(_e2)[:300]}
        if _last_err:
            return {"ok": False, "error": f"LLM重试{_max_retries}次仍失败: {_last_err}"}
        return {"ok": False, "error": "LLM调用失败"}
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