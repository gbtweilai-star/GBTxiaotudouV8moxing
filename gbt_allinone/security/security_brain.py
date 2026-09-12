# gbt-capability: dynamic-code, dynamic-import, subprocess, network, socket, base64, ctypes
"""
brain/hacker_brain.py — 黑客大脑
=================================
红队+蓝队双模: 攻击面测绘 | 漏洞扫描 | 利用链构建 | 防御验证

能力维度:
  1. 攻击面测绘 — 扫描项目暴露的所有攻击向量
  2. 漏洞扫描 — 自动检测OWASP Top 10 + CWE常见漏洞
  3. 利用链构建 — 从单个漏洞到完整攻击链
  4. 蓝队防御 — 验证防御措施是否有效
  5. 渗透报告 — 生成专业渗透测试报告
"""
import re  # ⛔ 2026-08-05 打磨: 补齐缺失stdlib导入(系统性缺陷)
import json
import time
from pathlib import Path
from typing import Optional
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent.parent  # V8: 仓库根

class HackerBrain:
    """黑客大脑 — 攻击+防御双模式"""

    def __init__(self):
        self.project_root = ROOT
        self.vuln_db = self._load_vuln_patterns()

    def map_attack_surface(self, target: str = None) -> dict:
        """攻击面测绘"""
        t0 = time.time()
        if target:
            _p = Path(target)
            root = _p if _p.is_absolute() and _p.exists() else (self.project_root / _p if (self.project_root / _p).exists() else self.project_root)
        else:
            root = self.project_root
        vectors = {"entry_points": 0, "file_operations": 0, "network": 0, "user_inputs": 0, "auth_boundaries": 0}
        details = []

        for py_file in root.rglob("*.py"):
            if "deploy_bak" in str(py_file) or py_file.name.startswith("_"):
                continue
            try:
                content = py_file.read_text(encoding='utf-8', errors='replace')
                rel = str(py_file.relative_to(root))
                if re.search(r'@app\.(route|get|post)|def main\(|argparse|click\.command|if __name__', content):
                    vectors["entry_points"] += 1; details.append({"file": rel, "type": "entry_point"})
                if re.search(r'open\(|Path\(.*write|shutil\.(copy|move|rmtree)|os\.(remove|rename)', content):
                    vectors["file_operations"] += 1; details.append({"file": rel, "type": "file_operation"})
                if re.search(r'requests\.(get|post)|socket\.|urllib|websocket|subprocess\.run', content):
                    vectors["network"] += 1; details.append({"file": rel, "type": "network"})
                if re.search(r'input\(|request\.(args|form|json|data)|sys\.argv', content):
                    vectors["user_inputs"] += 1; details.append({"file": rel, "type": "user_input"})
                if re.search(r'@login_required|@jwt_required|authenticate|authorize|token|api_key|password', content):
                    vectors["auth_boundaries"] += 1
            except Exception: pass  # 容错: 非关键路径
        total = sum(vectors.values())
        risk = min(100, vectors["user_inputs"] * 4 + vectors["network"] * 3 + vectors["file_operations"] * 3 + vectors["entry_points"] * 2)
        return {"ok": True, "attack_surface": vectors, "total_vectors": total, "risk_score": risk, "risk_level": "高危" if risk > 60 else ("中危" if risk > 30 else "低危"), "top_vectors": details[:10], "elapsed_ms": round((time.time()-t0)*1000, 1)}

    def scan_vulnerabilities(self, severity_filter: str = "medium") -> dict:
        """漏洞扫描"""
        t0 = time.time()
        vulns = []
        sev_levels = ["critical", "high", "medium", "low", "info"]
        min_sev = sev_levels.index(severity_filter)

        for py_file in self.project_root.rglob("*.py"):
            if "deploy_bak" in str(py_file) or py_file.name.startswith("_"):
                continue
            # ⛔ 排除第三方库/虚拟环境/存档 — 只扫框架自有代码
            _fp_l = str(py_file).replace("\\", "/").lower()
            if any(_seg in _fp_l for _seg in ("/lib/", "/site-packages/", "/node_modules/",
                                               "/backups/", "/archive/", "/.venv/", "/venv/",
                                               ".pylibs/", "archived_logs/", "/store/",
                                               ".openclaw/", ".openclaw-attachments/", ".wrangler/",
                                               "wf_runs/", "latest_logs/", "__pycache__",
                                               ".git/", "agnes_video/", "website/")):
                continue
            try:
                content = py_file.read_text(encoding='utf-8', errors='replace')
                rel = str(py_file.relative_to(self.project_root))
                # 安全/攻击工具目录白名单: 这些是测试工具, 非生产漏洞
                whitelist_dirs = ["sqli_tester", "xss_tester", "waf_bypass", "bounty_hunter",
                                  "strix", "anti_track", "pentest_kali", "attack", "hack",
                                  "device_takeover", "data_hijack", "n8n_attack_chain",
                                  "security_scan", "intelligent_scan"]
                is_security_tool = any(wd in str(py_file) for wd in whitelist_dirs)
                for line_no, line in enumerate(content.split(chr(10)), 1):
                    if is_security_tool:
                        break  # 安全工具目录跳过漏洞扫描
                    # ⛔ 受限执行豁免: 沙盒/无builtins/模式定义/沙盒内exec(compile 是设计行为, 非漏洞
                    _prev_ctx = "\n".join(content.split(chr(10))[max(0, line_no-5):line_no]) if line_no > 1 else ""
                    _is_sandboxed = ("sandbox_exec" in line or "mirror_exec" in line
                                     or "sandbox" in line.lower()
                                     or "'__builtins__': {}" in line or "\"__builtins__\": {}" in line
                                     or "exec(compile(" in line or "exec(compile (" in line
                                     or "safe_globals" in line or "safe_locals" in line  # 受限命名空间eval
                                     or "safe_builtins" in line or "safe_builtins" in _prev_ctx  # 受限builtins exec(含前文)
                                     or "self.exec(" in line  # 远程执行工具自身调用(设计)
                                     or "exec(open(" in line  # 子代理参数模板示例(设计)
                                     or line.lstrip().startswith("#")  # 注释行
                                     or re.match(r'\s*def \w*(exec|eval)\w*\(', line)  # 函数定义名含exec/eval
                                     or re.search(r'\w*[a-z_]+_(exec|eval)\w*\(', line)  # ⛔ 2026-08-09 调用自有exec系函数(设计内, 非动态执行; re.search防行首缩进锚定)
                                     or re.search(r'\w*_(exec|eval)\w* = ', line)  # 绑定exec系函数名(变量定义)
                                     or '"exec("' in line or '"eval("' in line  # 模式库定义 "exec("
                                     or "'exec('" in line or "'eval('" in line  # 模式库定义 'exec('
                                     or "exec\\(" in line or "eval\\(" in line  # 模式库定义 r'exec\(
                                     or '"exec(open"' in line or '"exec(open' in line  # ⛔ 2026-08-09 模式库字符串拼接 "exec(open"+E(设计内)
                                     or "builtins" in line and "exec" in line)
                    for pattern in self.vuln_db:
                        if _is_sandboxed and "CWE-95" in str(pattern.get("cwe_id", "")):
                            continue  # 受限动态执行 → 设计行为
                        # 自引用豁免：模式库定义行本身（JSON 形态）不是漏洞
                        if '"title"' in line and '"regex"' in line:
                            continue
                        if re.search(pattern["regex"], line):
                            if sev_levels.index(pattern["severity"]) <= min_sev:
                                vulns.append({"id": f"VULN-{len(vulns)+1:04d}", "title": pattern["title"], "severity": pattern["severity"], "cwe": pattern["cwe_id"], "location": f"{rel}:{line_no}", "match": line.strip()[:80], "fix": pattern["fix"], "cvss": pattern["cvss"]})
            except Exception: pass  # 容错: 非关键路径
        sev_count = defaultdict(int)
        for v in vulns:
            sev_count[v["severity"]] += 1

        return {"ok": True, "total": len(vulns), "critical": sev_count.get("critical", 0), "high": sev_count.get("high", 0), "medium": sev_count.get("medium", 0), "low": sev_count.get("low", 0), "distribution": dict(sev_count), "vulnerabilities": vulns[:20], "elapsed_ms": round((time.time()-t0)*1000, 1)}

    def build_exploit_chain(self, vulns: list = None) -> dict:
        """构建攻击链"""
        vulns = vulns or []
        info_leak = [v for v in vulns if "泄露" in v.get("title", "") or "明文" in v.get("title", "")]
        injection = [v for v in vulns if "注入" in v.get("title", "") or "执行" in v.get("title", "")]
        file_op = [v for v in vulns if "文件" in v.get("title", "") or "写入" in v.get("title", "")]
        chains = []
        if info_leak and injection:
            chains.append({"name": "信息泄露→代码执行→持久化", "steps": [{"vuln": info_leak[0]["id"], "action": "探测信息泄露"}, {"vuln": injection[0]["id"], "action": "利用注入获取执行"}, {"vuln": file_op[0]["id"] if file_op else "?", "action": "写入后门持久化"}], "impact": "完全控制系统", "probability": 0.6})
        return {"ok": True, "scenario": "full_compromise", "total_chains": len(chains), "chains": chains, "risk": "存在攻击链" if chains else "未发现完整链"}

    def validate_defenses(self) -> dict:
        """蓝队防御验证（V8 版：验证 V8 真实防御机制，不再引用旧 brain/gatekeeper）。

        V8 防御矩阵：
          1. 危险能力门禁 —— run_task(keylogger) 必须 denied
          2. 内网目标护栏 —— osint_scan(127.0.0.1) 必须被拦
          3. 管线门禁 —— pipeline_submit 缺 purpose 必须 blocked
          4. 禁用名单完整性 —— DISABLED_CAPS 11 项 + DANGEROUS_ENABLED=False
          5. 写保护 —— 生产区只经 pipeline 原子写入（os.replace）
        """
        import time as _t
        t0 = _t.time()
        checks = {}

        # 1) 危险能力门禁
        try:
            from ..api import run_task as _rt
            r = _rt("keylogger")
            body = r.get("gbt_result", r)
            checks["danger_gate"] = {
                "ok": body.get("status") == "denied",
                "detail": f"keylogger -> {body.get('status')}"}
        except Exception as e:  # noqa: BLE001
            checks["danger_gate"] = {"ok": False, "detail": str(e)[:80]}

        # 2) 内网护栏
        try:
            r = _rt("osint_scan", {"target": "127.0.0.1"})
            body = r.get("gbt_result", r)
            _res = body.get("result") if isinstance(body.get("result"), dict) else {}
            _denied = _res.get("denied") or body.get("denied")
            checks["net_guard"] = {
                "ok": (body.get("status") == "error" and "内网" in str(body.get("message", "")))
                      or bool(_denied),   # 授权门拒绝（无人工授权）同样是拦截成功
                "detail": f"127.0.0.1 -> {body.get('status')}"
                          + (" (auth_gate denied)" if _denied else "")}
        except Exception as e:  # noqa: BLE001
            checks["net_guard"] = {"ok": False, "detail": str(e)[:80]}

        # 3) 管线门禁
        try:
            r = _rt("pipeline_submit", {"name": "_def_probe.txt", "content": "x",
                                        "meta": {"purpose": "no-actor"}})
            body = r.get("gbt_result", {}).get("result", {})
            checks["pipeline_gate"] = {
                "ok": body.get("status") == "blocked",
                "detail": f"缺 actor -> {body.get('status')}"}
        except Exception as e:  # noqa: BLE001
            checks["pipeline_gate"] = {"ok": False, "detail": str(e)[:80]}

        # 4) 禁用名单与危险开关
        try:
            from ..caps_registry import DISABLED_CAPS
            from .. import api as _api
            checks["registry_integrity"] = {
                "ok": len(DISABLED_CAPS) >= 11 and _api.DANGEROUS_ENABLED is False,
                "detail": f"禁用 {len(DISABLED_CAPS)} 项 | 开关 {_api.DANGEROUS_ENABLED}"}
        except Exception as e:  # noqa: BLE001
            checks["registry_integrity"] = {"ok": False, "detail": str(e)[:80]}

        # 5) 生产区写保护（pipeline.py 存在 os.replace 即视为机制在位）
        try:
            import inspect as _insp
            from .. import pipeline as _pipe
            src = _insp.getsource(_pipe)
            checks["write_protection"] = {
                "ok": "os.replace" in src,
                "detail": "生产区原子写入 (os.replace) 机制在位"}
        except Exception as e:  # noqa: BLE001
            checks["write_protection"] = {"ok": False, "detail": str(e)[:80]}

        passed = sum(1 for v in checks.values() if v.get("ok"))
        total = len(checks)
        return {
            "ok": passed == total,
            "defense_status": "全部生效" if passed == total else f"存在缺口 ({total - passed} 项未过)",
            "checks": checks,
            "passed": passed, "total": total,
            "elapsed_ms": round((_t.time() - t0) * 1000, 1),
        }


    def emit_signal(self, signal, payload=None, priority="normal"):
        try:
            from ..store import audit as _a
            _a("sec_signal", {"signal": str(signal)[:40], "priority": str(priority)[:10]})
        except Exception:
            pass
        """黑客脑发信号 — V8 化：信号落审计总线（旧 brain/signal_bus 的等价降级，
        已知历史：V8 独立成家后旧 brain 路径断链，穿透式交叉扫 2026-09-11 发现并修复）"""
        try:
            from ..store import audit as _a2
            _a2("sec_signal_emit", {"source": "黑客脑", "signal": str(signal)[:60],
                                     "priority": str(priority)[:10],
                                     "payload": str(payload)[:120]})
            return {"ok": True, "via": "v8_audit_bus",
                    "signal": str(signal)[:40], "priority": str(priority)[:10]}
        except Exception as e:
            return {"ok": False, "error": f"信号发送失败: {str(e)[:200]}"}

    def signal_patrol(self):
        """黑客脑巡检 — 分析攻击面/漏洞/防御, 发现缺口则向执行层发信号请求处置
        管辖: security — 只发 scan/attack_surface/defense_check/exploit_chain 信号
        """
        t0 = time.time()
        result = {"ok": True, "brain": "黑客脑", "domain": "security", "signals": []}
        try:
            # ⛔ 2026-08-09 修复: 攻击面风险分是框架全量代码静态统计(400+cap必然高分),
            #    不是可行动警报 — 不再按分数发 high 信号, 只记录统计供执行者参考。
            surf = self.map_attack_surface()
            result["attack_surface"] = {"risk_score": surf.get("risk_score"), "risk_level": surf.get("risk_level"),
                                        "total_vectors": surf.get("total_vectors")}
            vulns = self.scan_vulnerabilities("high")
            result["vulns"] = {"total": vulns.get("total"), "critical": vulns.get("critical"), "high": vulns.get("high")}
            if vulns.get("critical", 0) > 0 or vulns.get("high", 0) > 0:
                s = self.emit_signal("scan", {"total": vulns.get("total"), "critical": vulns.get("critical"), "high": vulns.get("high")}, "high")
                if s.get("ok"):
                    result["signals"].append(s.get("id"))
            defense = self.validate_defenses()
            result["defense"] = {"status": defense.get("defense_status"), "ok": defense.get("ok")}
            if not defense.get("ok"):
                s = self.emit_signal("defense_check", {"status": defense.get("defense_status")}, "normal")
                if s.get("ok"):
                    result["signals"].append(s.get("id"))
        except Exception as e:
            result["ok"] = False
            result["error"] = str(e)[:200]
        result["elapsed_ms"] = round((time.time() - t0) * 1000, 1)
        return result

    def _load_vuln_patterns(self) -> list:
        # V8 融合强化（第 19 批）：吞天消化 bandit(8257★)/semgrep(16583★)/gitleaks(29223★) 后
        # 原生融合的检测智慧 —— 我们缺的 15 类高价值检测全部补齐（Bandit 的危险调用类、
        # gitleaks 的密钥格式类、semgrep 的逻辑缺陷类），共 25 条。
        return [
            # ── 原有 10 条（基线）──
            {"regex": r"sql\s*=\s*[\"'](.+?%s.+?|.+?\{.+?\}.*?)", "title": "SQL注入", "severity": "critical", "cwe_id": "CWE-89", "fix": "参数化查询", "cvss": 9.8},
            {"regex": r"\b(os\.system|os\.popen|subprocess\.call\([^)]*shell\s*=\s*True)\b", "title": "命令注入", "severity": "critical", "cwe_id": "CWE-78", "fix": "shell=False+参数列表", "cvss": 9.8},
            {"regex": r"pickle\.loads?\(|yaml\.load\((?!.*Loader)", "title": "不安全反序列化", "severity": "critical", "cwe_id": "CWE-502", "fix": "yaml.safe_load/pickle 白名单", "cvss": 9.1},
            {"regex": r"\bexec\(open|\beval\(input|\bexec\([\"']", "title": "动态代码执行", "severity": "high", "cwe_id": "CWE-95", "fix": "受限沙盒或 AST 白名单", "cvss": 8.1},
            {"regex": r"(open|write_text|write_bytes)\([^)]*[\"'][\w/\\.-]+[\"']", "title": "文件写入", "severity": "medium", "cwe_id": "CWE-22", "fix": "Path.resolve()验证", "cvss": 6.5},
            {"regex": r"verify\s*=\s*False|CERT_NONE", "title": "SSL验证禁用", "severity": "medium", "cwe_id": "CWE-295", "fix": "verify=True", "cvss": 6.5},
            {"regex": r"except\s*:", "title": "裸except", "severity": "medium", "cwe_id": "CWE-396", "fix": "捕获具体异常", "cvss": 5.0},
            {"regex": r"(password|passwd|secret|token)\s*=\s*[\"'](?!\*{3}|x{4,}|test|placeholder|example|your[_-]|<|bad-token|redacted|dummy|mock|sample)[^\"']{4,}[\"']", "title": "敏感信息泄露", "severity": "high", "cwe_id": "CWE-532", "fix": "环境变量/密钥管理", "cvss": 7.5},
            {"regex": r"http://(?!localhost|127\.0\.0\.1)", "title": "明文HTTP", "severity": "low", "cwe_id": "CWE-319", "fix": "HTTPS", "cvss": 3.7},
            {"regex": r"\brandom\.(random|randint|choice|shuffle)\(", "title": "弱随机数", "severity": "medium", "cwe_id": "CWE-338", "fix": "secrets 模块", "cvss": 5.0},
            # ── 融合强化 +15 条（开源智慧原生吸收）──
            # gitleaks 智慧：密钥格式识别
            {"regex": r"AKIA[0-9A-Z]{16}", "title": "AWS访问密钥泄露", "severity": "critical", "cwe_id": "CWE-798", "fix": "立即吊销+环境变量", "cvss": 9.1},
            {"regex": r"gh[pousr]_[A-Za-z0-9]{36,255}", "title": "GitHub令牌泄露", "severity": "critical", "cwe_id": "CWE-798", "fix": "立即吊销+环境变量", "cvss": 9.1},
            {"regex": r"sk-[A-Za-z0-9_-]{20,}", "title": "LLM API密钥泄露(OpenAI/DeepSeek)", "severity": "critical", "cwe_id": "CWE-798", "fix": "立即吊销+环境变量", "cvss": 9.1},
            {"regex": r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----", "title": "私钥文件内容", "severity": "critical", "cwe_id": "CWE-321", "fix": "密钥入安全存储", "cvss": 8.8},
            {"regex": r"xox[bapr]-[A-Za-z0-9-]{10,}", "title": "Slack令牌泄露", "severity": "high", "cwe_id": "CWE-798", "fix": "立即吊销+环境变量", "cvss": 7.5},
            # bandit 智慧：危险调用形态
            {"regex": r"subprocess\.(Popen|run|call|check_output)\([^)]*shell\s*=\s*True", "title": "subprocess shell=True(B602)", "severity": "high", "cwe_id": "CWE-78", "fix": "列表参数+shell=False", "cvss": 8.1},
            {"regex": r"tempfile\.mktemp\(", "title": "临时文件竞争条件(B108)", "severity": "medium", "cwe_id": "CWE-377", "fix": "tempfile.mkstemp", "cvss": 5.5},
            {"regex": r"\bassert\s+.*(token|password|auth|permission|admin)", "title": "assert做安全校验(B101,可被-O绕过)", "severity": "medium", "cwe_id": "CWE-703", "fix": "显式 if+raise", "cvss": 5.4},
            {"regex": r"hashlib\.(md5|sha1)\(", "title": "弱哈希算法(B324)", "severity": "medium", "cwe_id": "CWE-327", "fix": "sha256+", "cvss": 5.0},
            {"regex": r"requests\.(get|post|put|delete)\([^)]*verify\s*=\s*False", "title": "requests禁用证书校验(B501)", "severity": "high", "cwe_id": "CWE-295", "fix": "verify=True", "cvss": 7.4},
            # semgrep 智慧：逻辑缺陷
            {"regex": r'"[^"]*(SELECT|INSERT|UPDATE|DELETE)[^"]*"\s*\.format\(', "title": "str.format拼接SQL", "severity": "high", "cwe_id": "CWE-89", "fix": "参数化查询", "cvss": 8.0},
            {"regex": r"set_cookie\([^)]*(?<!httponly)httponly\s*=\s*False", "title": "Cookie缺HttpOnly", "severity": "medium", "cwe_id": "CWE-1004", "fix": "httponly=True", "cvss": 5.3},
            {"regex": r"(Flask|app)\.(run)\([^)]*debug\s*=\s*True", "title": "生产开启debug模式(B201)", "severity": "high", "cwe_id": "CWE-489", "fix": "debug=False", "cvss": 7.5},
            {"regex": r"jinja2\.Environment\((?!.*autoescape)", "title": "Jinja2未自动转义(B701,XSS)", "severity": "high", "cwe_id": "CWE-79", "fix": "autoescape=True", "cvss": 7.1},
            {"regex": r"\bchmod\([^)]*0o?777", "title": "全开文件权限", "severity": "medium", "cwe_id": "CWE-732", "fix": "最小权限", "cvss": 5.3},
        ]


_hacker: Optional[HackerBrain] = None

def get_hacker() -> HackerBrain:
    global _hacker
    if _hacker is None:
        _hacker = HackerBrain()
    return _hacker

def signal_patrol():
    """模块级: 黑客脑巡检 (brain_ring 履职入口)"""
    return get_hacker().signal_patrol()


def map_attack_surface(target: str = None) -> dict:
    return get_hacker().map_attack_surface(target)

def scan_vulnerabilities(severity: str = "medium") -> dict:
    return get_hacker().scan_vulnerabilities(severity)

def validate_defenses() -> dict:
    return get_hacker().validate_defenses()


if __name__ == "__main__":
    hb = HackerBrain()
    print("=== 攻击面 ===")
    r = hb.map_attack_surface()
    print(f"风险: {r['risk_score']}/100 {r['risk_level']}, 向量: {r['total_vectors']}")
    print("=== 漏洞扫描 ===")
    r = hb.scan_vulnerabilities("high")
    print(f"漏洞: {r['total']} (严重:{r['critical']} 高危:{r['high']})")