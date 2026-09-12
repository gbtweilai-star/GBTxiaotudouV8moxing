# gbt-capability: dynamic-import
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""
brain/devour_tentacle.py -- 吞噬触手 · 自主进化 v1.0
====================================================
触手自己找食吃，自己进化。不用人手一根一根造。

吞噬循环:
  扫描平台 → 发现新技能 → 分析缺口 → 
  自动创建cap骨架 → 注入知识 → 注册nexus → 
  通知event_bus → 存入记忆

与 devourer cap 的关系:
  devourer cap = 独立的吞噬引擎(手动/定时触发)
  devour_tentacle = 织入神经触手的自主吞噬(每次脉冲自动触发)
"""
import sys, json
from pathlib import Path
from datetime import datetime
from typing import Optional

ROOT = Path(__file__).resolve().parent          # V8: gbt_allinone/
BRAIN = ROOT / "tentacle"                       # V8: 触手目录（旧 brain 等价物）
CAPS_DIR = __import__("gbt_allinone._paths", fromlist=["STORE_DIR"]).STORE_DIR / "devoured"
CAPS_DIR.mkdir(parents=True, exist_ok=True)  # 自愈：吞噬产物目录缺失时自动创建          # V8: 吞噬产物落户框架 store

# ⛔ 2026-08-28 打磨(R34): 模块级缓存 — 修复 exec_module 每次重建模块的内存泄漏 (同路径只 exec 一次)
_MOD_CACHE: dict = {}

def _load_module(name: str, path) -> object:
    """缓存式模块加载 — 同路径只 exec 一次, 后续复用 (单例由模块内部缓存)"""
    key = str(path)
    if key not in _MOD_CACHE:
        import importlib.util as _iu
        _spec = _iu.spec_from_file_location(name, key)
        _mod = _iu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        _MOD_CACHE[key] = _mod
    return _MOD_CACHE[key]

sys.path.insert(0, str(ROOT))

DEVOUR_STATE = __import__("gbt_allinone._paths", fromlist=["STORE_DIR"]).STORE_DIR / "devour_state.json"


def _v8_deploy(file_path, content, context=""):
    """V8 部署：备份旧文件（.deploy_bak 归档区）+ 原子写盘 + 审计。"""
    from pathlib import Path as _P
    import shutil as _sh
    fp = _P(file_path)
    if not fp.is_absolute():            # 相对路径一律按框架根解析（防漂移到 CWD）
        fp = ROOT / fp
    fp.parent.mkdir(parents=True, exist_ok=True)
    if fp.exists():
        bak = fp.with_suffix(fp.suffix + ".deploy_bak")
        _sh.copy2(fp, bak)
    tmp = fp.with_suffix(fp.suffix + ".tmp")
    tmp.write_text(str(content), encoding="utf-8")
    import os as _os
    _os.replace(tmp, fp)
    try:
        from .store import audit as _a
        _a("devour_deploy", {"file": fp.name, "context": str(context)[:40]})
    except Exception:
        pass
    return {"ok": True, "file": str(fp)}


def _v8_publish(path_str: str, content=None, note: str = "") -> dict:
    """V8 镜像门禁：文件经 pipeline 生产防线发布（旧 gatekeeper.publish 等价物）。

    旧签名兼容：publish(path, content, note)——content 有值先落盘再发布。
    """
    try:
        from . import pipeline as _pipe
        from pathlib import Path as _P
        p = _P(path_str)
        if content is not None and not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(str(content), encoding="utf-8")
        if not p.exists():
            return {"ok": False, "error": f"文件不存在: {path_str}"}
        _r = _pipe.submit(p.name, p.read_text(encoding="utf-8", errors="replace"),
                          {"actor": "devour_tentacle", "purpose": f"吞噬产物: {note or p.name}"})
        _r["ok"] = _r.get("status") == "published"
        return _r
    except Exception as _e:  # noqa: BLE001
        return {"ok": False, "error": str(_e)[:120]}


class DevourTentacle:
    """吞噬触手 — 自动发现、吸收、进化"""

    def __init__(self):
        self.state = self._load_state()
        self._last_devour = None

    def _load_state(self) -> dict:
        if DEVOUR_STATE.exists():
            try:
                return json.loads(DEVOUR_STATE.read_text(encoding="utf-8"))
            except Exception as _e:
                print(f"⚠️ devour_tentacle: 吞错: {_e}", file=sys.stderr)
        return {
            "total_devours": 0,
            "total_absorbed": 0,
            "total_caps_created": 0,
            "last_devour_at": None,
            "absorbed_skills": [],
        }

    def _save_state(self):
        DEVOUR_STATE.parent.mkdir(parents=True, exist_ok=True)
        DEVOUR_STATE.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")

    def _connect_neighborhoods(self, cap_name="", cap_domains=None):
        """自动连接神经邻域 + 感知邻域 + 拓扑索引
        每次吞噬/创建cap后自动调用，确保新能力接入全邻域网络
        """
        results = {"nexus": False, "neural": False, "perception": False, "topology": False}
        
        # 1. Nexus 注册
        try:
            # V8: nexus 注册 → selfscan 路由对账（注册完整性）
            from .selfscan import check_routing
            results["nexus"] = check_routing()["ok"]
        except Exception as _e:
            print(f"⚠️ devour_tentacle: 吞错: {_e}", file=sys.stderr)
        # 2. 神经邻域脉冲 — 让神经触手感知新能力
        try:
            import importlib.util as _iu
            # V8: 神经触手脉冲 → 触手桥自检（眼睛/双手在线即感知在线）
            from .tentacle import bridge as _TB
            if _TB.eye_ready():
                results["neural"] = True
        except Exception as _e:
            print(f"⚠️ devour_tentacle: 吞错: {_e}", file=sys.stderr)
        # 3. 感知邻域注册 — 视觉/桌面/侦察域感知
        try:
            domains = cap_domains or []
            perceptual = [d for d in domains if d in ("感知域", "桌面域", "侦察域", "视觉域")]
            if perceptual or not domains:
                # 记录到感知记忆
                # V8: 感知记忆 → 状态文件记录
                self.state.setdefault("perceived_caps", {})[cap_name] = {
                    "domains": domains or [], "recorded_at": _tm().strftime("%Y-%m-%dT%H:%M:%S")}
                self._save_state()
                results["perception"] = True
        except Exception as _e:
            print(f"⚠️ devour_tentacle: 吞错: {_e}", file=sys.stderr)
        # 4. 拓扑索引更新
        try:
            # V8: 拓扑索引 → 状态文件（邻域连接图）
            idx = self.state.setdefault("topology", {})
            results["topology"] = True
        except Exception as _e:
            print(f"⚠️ devour_tentacle: 吞错: {_e}", file=sys.stderr)
        return results

    def scan_gaps(self) -> dict:
        """扫描能力缺口"""
        try:
            # V8: 能力缺口分析 → 对照常见 AI 框架域清单
            from .caps_registry import BENIGN_CAPS
            domains_present = {info.get("domain", "?") for info in BENIGN_CAPS.values()}
            domains_expected = {"engine", "pipeline", "tentacle", "llm", "security",
                                "system", "recon", "finance", "wallet", "ledger"}
            gaps = sorted(domains_expected - domains_present)
            return {"ok": True, "gaps": [{"domain": g, "hint": f"域 {g} 无任何能力"} for g in gaps],
                    "covered": sorted(domains_present), "total_caps": len(BENIGN_CAPS)}
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}

    def devour_github_repo(self, repo_url: str, cap_name: str = "", 
                           max_readme_chars: int = 6000, context: str = "devour_github_repo") -> dict:
        """吞噬外部 GitHub 仓库 — 拉取仓库信息+README, 提炼知识写入 cap 吸收记录

        流程: 解析 owner/repo → GitHub API 拉 metadata + README → 
              提炼要点(定位/技术栈/架构/亮点) → publish absorbed_knowledge.md →
              注入神经触手 → 连接全邻域
        """
        from .store import audit as _audit
        _audit("devour_chain", {"step": "devour_tentacle.github"})
        import urllib.request, urllib.error, re as _re, json as _json

        repo_url = (repo_url or "").strip()
        if not repo_url:
            return {"ok": False, "error": "缺少 repo_url"}
        m = _re.search(r"github\.com[/:]([^/\s]+)/([^/\s#?]+)", repo_url)
        if not m:
            return {"ok": False, "error": f"无法解析 GitHub 仓库: {repo_url}"}
        owner, repo = m.group(1), (m.group(2)[:-4] if m.group(2).endswith(".git") else m.group(2))

        try:
            # ① 拉仓库 metadata
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            req = urllib.request.Request(api_url, headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "GBT-devour-tentacle/1.0"})
            meta = _json.loads(urllib.request.urlopen(req, timeout=20).read())

            # ② 拉 README (优先 README.md, 降级 README)
            readme_text = ""
            readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/README.md"
            try:
                readme_text = urllib.request.urlopen(
                    urllib.request.Request(readme_url, headers={"User-Agent": "GBT-devour-tentacle/1.0"}),
                    timeout=20).read().decode("utf-8", errors="replace")
            except Exception:
                try:
                    readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/readme.md"
                    readme_text = urllib.request.urlopen(
                        urllib.request.Request(readme_url, headers={"User-Agent": "GBT-devour-tentacle/1.0"}),
                        timeout=20).read().decode("utf-8", errors="replace")
                except Exception:
                    readme_text = ""

            # ③ 提炼要点
            summary = {
                "repo": f"{owner}/{repo}", "url": meta.get("html_url", repo_url),
                "stars": meta.get("stargazers_count", 0),
                "language": meta.get("language", ""),
                "license": (meta.get("license") or {}).get("spdx_id", "unknown"),
                "description": (meta.get("description") or "")[:300],
                "topics": meta.get("topics", [])[:10],
                "default_branch": meta.get("default_branch", "main"),
                "pushed_at": meta.get("pushed_at", ""),
                "readme_head": readme_text[:max_readme_chars],
            }

            # ④ 生成吸收知识 markdown
            lines = [
                f"# {owner}/{repo} 吞噬记录 — devour_tentacle",
                f"> 吞噬日期: {datetime.now().isoformat()[:19]} | 来源: {meta.get('html_url', repo_url)}",
                f"> Stars: {summary['stars']} | 语言: {summary['language']} | 许可: {summary['license']}",
                "",
                "## 项目概览",
                f"- 描述: {summary['description'] or '(无)'}",
                f"- 主题: {', '.join(summary['topics']) or '(无)'}",
                f"- 分支: {summary['default_branch']} | 最近推送: {summary['pushed_at'][:10]}",
                "",
                "## README 摘要",
                (summary["readme_head"] or "(仓库无 README.md)"),
                "",
                "## 对 GBT 的启示",
                "- 可吸收点: 结合仓库定位与 README 技术栈, 提炼可注入 GBT cap 的知识",
            ]
            knowledge = "\n".join(lines)

            # ⑤ 写入吸收记录 (走 publish 管线)
            if not cap_name:
                cap_name = f"devoured_{owner}_{repo}".lower().replace("/", "_")[:50]
            _gk_gd = type("_GK", (), {"publish": staticmethod(lambda p, content=None, note="": _v8_publish(p, content, note))})()
            pub = _gk_gd.publish(str(CAPS_DIR / cap_name / "absorbed_knowledge.md"),
                                 knowledge, f"{context}:{owner}/{repo}")
            if not pub.get("ok"):
                return {"ok": False, "error": f"吸收记录写入失败: {pub.get('error')}", "gate": "publish"}

            # ⛔ 2026-08-07 深度修复: 吞噬胶囊出生即完整 — 同管线补齐 capability.json + run.py。
            #    此前只写 absorbed_knowledge.md, 裸目录被L0扫描判为残缺cap,
            #    触发基础设施blocker → 全新进程的 enforce_chain/boot 全部失败。
            try:
                _cap_json = {
                    "_stamp": "⛔ 开发者：自由的风 · 永久钢印 · 禁止删除",
                    "name": cap_name, "version": "1.0.0",
                    "description": f"吞噬知识胶囊: {owner}/{repo} — {summary['description'][:80]}",
                    "language": "python", "risk_level": "safe", "auto_exec": False,
                    "category": "吞噬吸收", "tier": "knowledge",
                    "entry": {"program": "python", "args": ["run.py"]},
                    "actions": {
                        "knowledge": {"description": "读取本胶囊吞噬吸收的知识"},
                        "run": {"description": "同 knowledge — 读取吞噬知识"},
                        "status": {"description": "胶囊状态"},
                    },
                    "triggers": {"keywords": [owner.lower(), repo.lower()], "intent": cap_name},
                    "domains": ["AI域"],
                }
                _gk_gd.publish(str(CAPS_DIR / cap_name / "knowledge.json"),
                               json.dumps(_cap_json, ensure_ascii=False, indent=2),
                               f"{context}:{owner}/{repo}:scaffold")
                _run_py = (
                    f"# GBT cap: {cap_name}\n"
                    f"# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除\n"
                    f'"""caps/{cap_name}/run.py — 吞噬知识胶囊: {owner}/{repo}"""\n'
                    "import json, sys\nfrom pathlib import Path\n\n"
                    'ABS = Path(__file__).parent / "absorbed_knowledge.md"\n\n'
                    "def do_knowledge(params=None):\n"
                    "    if ABS.exists():\n"
                    '        return {"ok": True, "knowledge": ABS.read_text(encoding="utf-8")}\n'
                    '    return {"ok": False, "error": "absorbed_knowledge.md 缺失"}\n\n'
                    "def do_status(params=None):\n"
                    f'    return {{"ok": True, "cap": "{cap_name}", "tier": "knowledge", "has_knowledge": ABS.exists()}}\n\n'
                    'HANDLERS = {"knowledge": do_knowledge, "run": do_knowledge, "status": do_status}\n\n'
                    'if __name__ == "__main__":\n'
                    '    action = sys.argv[1] if len(sys.argv) > 1 else "status"\n'
                    "    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}\n"
                    "    print(json.dumps(HANDLERS.get(action, do_status)(params), ensure_ascii=False))\n"
                )
                _gk_gd.publish(str(CAPS_DIR / cap_name / "run.py"),
                               _run_py, f"{context}:{owner}/{repo}:scaffold")
            except Exception as _e:
                print(f"⚠️ devour_tentacle: 吞错: {_e}", file=sys.stderr)

            # ⑥ 注入神经触手 + 更新状态
            self.state["total_devours"] += 1
            self.state["total_absorbed"] += 1
            self.state.setdefault("scan_learnings", [])
            self.state["scan_learnings"].append(f"[{owner}/{repo}] {summary['description'][:80]}")
            self.state["scan_learnings"] = self.state["scan_learnings"][-200:]
            self.state["last_devour_at"] = datetime.now().isoformat()
            self._save_state()

            try:
                self.inject_to_tentacle(f"github_{owner}_{repo}".lower()[:60], knowledge[:500])
            except Exception as _e:
                print(f"⚠️ devour_tentacle: 吞错: {_e}", file=sys.stderr)
            try:
                self._connect_neighborhoods(cap_name=cap_name, cap_domains=meta.get("topics", [])[:3] or ["AI域"])
            except Exception as _e:
                print(f"⚠️ devour_tentacle: 吞错: {_e}", file=sys.stderr)

            return {
                "ok": True, "repo": f"{owner}/{repo}",
                "stars": summary["stars"], "language": summary["language"],
                "cap": cap_name, "knowledge_chars": len(knowledge),
                "readme_chars": len(readme_text),
                "absorbed_knowledge": str(CAPS_DIR / cap_name / "absorbed_knowledge.md"),
                "message": f"吞噬 {owner}/{repo} 完成 ({summary['stars']} stars, {summary['language']})",
            }
        except urllib.error.HTTPError as e:
            return {"ok": False, "error": f"GitHub API {e.code}: {e.reason}", "repo": f"{owner}/{repo}"}
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}: {str(e)[:200]}", "repo": f"{owner}/{repo}"}

    def quick_devour(self, max_findings: int = 5, timeout: int = 5) -> dict:
        from .store import audit as _audit
        _audit("devour_chain", {"step": "devour_tentacle.quick_devour"})
        """快速吞噬 - 本地优先，网络可选。非阻塞。"""
        result = {"ok": True, "total_found": 0, "absorbed": 0, "caps_created": 0, "new_skills": [], "mode": "local"}

        try:
            # 先用本地缺口分析
            gaps = self.scan_gaps()
            if gaps.get("ok") and gaps.get("gaps"):
                high_gaps = [v for v in gaps["gaps"].values() if v.get("priority") == "high"]
                result["gaps_found"] = len(high_gaps)
                result["total_found"] = len(gaps.get("gaps", []))

                # 自动创建高优先级缺口cap
                if high_gaps:
                    try:
                        created = self.auto_create_from_gaps(max_create=min(3, len(high_gaps)))
                        result["caps_created"] = len(created.get("created", []))
                        result["new_caps"] = created.get("created", [])
                    except Exception as _e:
                        print(f"⚠️ devour_tentacle: 吞错: {_e}", file=sys.stderr)
            # 更新状态
            self.state["total_devours"] += 1
            self.state["total_caps_created"] += result["caps_created"]
            self.state["total_absorbed"] += result["absorbed"]
            self.state["last_devour_at"] = __import__("datetime").datetime.now().isoformat()
            self._save_state()

            # 有新cap -> 自动连接全邻域
            if result["caps_created"] > 0:
                self._connect_neighborhoods(
                    cap_name=str(result.get("new_caps", ["unknown"])[0]) if result.get("new_caps") else "devoured",
                    cap_domains=["AI域", "桌面域"]
                )

            return result
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}

    def devour_scan_results(self, scan_result: dict) -> dict:
        from .store import audit as _audit
        _audit("devour_chain", {"step": "devour_tentacle.devour_scan"})

        """吞噬穿透扫描结果 v3.0
        自动修复三模式:
          1. remove_action  — 删僵尸声明
          2. add_action     — 补漏声明
          3. translate      — 自动转译: handler名≉action名时智能对齐
        所有修复走 gbt_deploy 镜像出品
        """
        devoured = []
        fixed = []

        all_issues = []
        if "issues" in scan_result:
            all_issues = scan_result["issues"]
        for layer_name, layer in scan_result.get("layers", {}).items():
            all_issues.extend(layer.get("detail", []))

        for issue in all_issues:
            level = issue.get("level", "info")
            if level not in ("error", "warn", "info"):
                continue
            msg = issue.get("msg", "")
            cap = issue.get("cap", "")
            path = issue.get("path", "")
            fix_type = issue.get("fix_type")
            fix_action = issue.get("fix_action", "")

            knowledge = f"[{cap}] {msg}"
            devoured.append({"type": "scan_issue", "knowledge": knowledge, "path": path})

            if not fix_type or not path:
                continue

            try:
                import json, importlib.util as _iu
                with open(path, "r", encoding="utf-8") as f:
                    cap_data = json.load(f)
                rel = str(Path(path))  # 绝对路径（store 可能在 ROOT 外，不再 relative_to）
                modified = False

                if fix_type == "remove_action" and fix_action:
                    if fix_action in cap_data.get("actions", {}):
                        del cap_data["actions"][fix_action]
                        modified = True
                        fixed.append(f"del:{cap}:{fix_action}")

                elif fix_type == "add_action" and fix_action:
                    cap_data.setdefault("actions", {})
                    if fix_action not in cap_data["actions"]:
                        cap_data["actions"][fix_action] = {"description": fix_action, "timeout_ms": 30000}
                        modified = True
                        fixed.append(f"add:{cap}:{fix_action}")

                elif fix_type == "translate":
                    # 自动转译: handler名和action名不一致时智能对齐
                    _fixed = self._auto_translate_contract(cap, path, cap_data, rel)
                    if _fixed:
                        modified = True
                        fixed.extend(_fixed)

                if modified:
                    _dpy = type("_DPY", (), {"deploy": staticmethod(_v8_deploy)})()
                    _dpy.deploy(rel, json.dumps(cap_data, ensure_ascii=False, indent=2),
                               context=f"devour_scan:{fix_type}:{fix_action}")
            except Exception as _e:
                print(f"⚠️ devour_tentacle: 吞错: {_e}", file=sys.stderr)
        self.state["total_devours"] += 1
        self.state["total_absorbed"] += len(devoured)
        self.state["total_caps_created"] += len(fixed)
        if devoured:
            self.state.setdefault("scan_learnings", [])
            self.state["scan_learnings"].extend(d["knowledge"] for d in devoured)
            self.state["scan_learnings"] = self.state["scan_learnings"][-200:]
        self.state["last_devour_at"] = datetime.now().isoformat()
        self._save_state()

        return {
            "ok": True,
            "devoured": len(devoured),
            "fixed": len(fixed),
            "knowledge": [d["knowledge"][:100] for d in devoured[:5]],
            "fixes": fixed[:10],
        }

    def _auto_translate_contract(self, cap_name, cap_path, cap_data, rel_path):
        """自动转译: 检测capability.json和run.py之间的命名差异并智能对齐

        转译规则:
          1. do_xxx ↔ xxx (前缀差异)
          2. xxx_action ↔ xxx (后缀差异)
          3. camelCase ↔ snake_case (命名风格)
          4. 模糊匹配: 编辑距离≤3的相似名自动合并
        """
        fixed = []
        try:
            import json, importlib.util as _iu, re

            # 读取 run.py 的 HANDLERS
            run_py_path = str(Path(cap_path).parent / "run.py")
            run_content = Path(run_py_path).read_text(encoding="utf-8")

            # 提取 HANDLERS keys
            handler_keys = set()
            in_handlers = False
            for line in run_content.split("\n"):
                if line.strip().startswith("HANDLERS"):
                    in_handlers = True
                    continue
                if in_handlers:
                    m = re.match(r'\s*"([^"]+)"\s*:', line)
                    if m:
                        handler_keys.add(m.group(1))
                    if line.strip() == "}":
                        break

            if not handler_keys:
                return fixed

            action_keys = set(cap_data.get("actions", {}).keys())

            # 转译规则1: do_xxx ↔ xxx
            for hk in list(handler_keys):
                if hk.startswith("do_"):
                    bare = hk[3:]
                    if bare in action_keys and hk not in action_keys:
                        # run.py有do_xxx, cap有xxx → 给cap加do_xxx别名
                        cap_data["actions"][hk] = {**cap_data["actions"][bare], "_alias_for": bare}
                        fixed.append(f"translate:{cap_name}:add_alias:{hk}->{bare}")
                else:
                    do_version = f"do_{hk}"
                    if do_version in handler_keys and do_version not in action_keys:
                        cap_data["actions"][do_version] = {"description": hk, "timeout_ms": 30000, "_wraps": hk}
                        fixed.append(f"translate:{cap_name}:add_wrapper:{do_version}")

            # 转译规则2: 后缀差异 (xxx_action ↔ xxx)
            for hk in list(handler_keys):
                for ak in list(action_keys):
                    if hk != ak:
                        if hk.startswith(ak) and len(hk) - len(ak) <= 8:
                            cap_data["actions"][hk] = {"description": hk, "timeout_ms": 30000, "_alias_for": ak}
                            fixed.append(f"translate:{cap_name}:add_suffix_alias:{hk}->{ak}")
                            break
                        if ak.startswith(hk) and len(ak) - len(hk) <= 8:
                            cap_data["actions"][ak] = {"description": ak, "timeout_ms": 30000, "_alias_for": hk}
                            fixed.append(f"translate:{cap_name}:add_suffix_alias:{ak}->{hk}")
                            break

            # 转译规则3: snake_case ↔ camelCase
            def to_snake(name):
                return re.sub(r"([A-Z])", r"_\1", name).lower().strip("_")
            def to_camel(name):
                parts = name.split("_")
                return parts[0] + "".join(p.capitalize() for p in parts[1:])

            for hk in list(handler_keys):
                hk_snake = to_snake(hk)
                for ak in list(action_keys):
                    if hk_snake == to_snake(ak) and hk != ak:
                        cap_data["actions"][hk] = {"description": hk, "timeout_ms": 30000, "_alias_for": ak}
                        fixed.append(f"translate:{cap_name}:case_alias:{hk}->{ak}")
                        break

            # 转译规则4: 编辑距离模糊匹配
            def edit_distance(a, b):
                if len(a) < len(b): a, b = b, a
                if len(b) == 0: return len(a)
                prev = list(range(len(b) + 1))
                for i, ca in enumerate(a):
                    curr = [i + 1]
                    for j, cb in enumerate(b):
                        curr.append(min(prev[j+1]+1, curr[j]+1, prev[j]+(ca!=cb)))
                    prev = curr
                return prev[-1]

            for hk in list(handler_keys):
                for ak in list(action_keys):
                    if hk != ak and edit_distance(hk, ak) <= 3 and len(hk) >= 4:
                        cap_data["actions"][hk] = {"description": hk, "timeout_ms": 30000, "_alias_for": ak}
                        fixed.append(f"translate:{cap_name}:fuzzy_alias:{hk}->{ak}")
                        break

        except Exception as _e:
            print(f"⚠️ devour_tentacle: 吞错: {_e}", file=sys.stderr)
        return fixed

    def auto_create_from_gaps(self, max_create: int = 3) -> dict:
        from .store import audit as _audit
        _audit("devour_chain", {"step": "devour_tentacle.auto_create"})
        """从缺口自动创建cap骨架"""
        try:
            # V8: 缺口分析走 scan_gaps（本地域对照），骨架创建走 _v8_deploy
            gaps = self.scan_gaps()
            if not gaps.get("ok"):
                return gaps

            high_priority = [g for g in gaps.get("gaps", []) if g.get("priority") == "high"]
            if len(high_priority) > max_create:
                high_priority = high_priority[:max_create]

            if not high_priority:
                return {"ok": True, "created": 0, "message": "无高优先级缺口"}

            # V8: 本地骨架创建（每个缺口建目录+capability.json 骨架）
            created_list = []
            for g in high_priority:
                gname = str(g.get("domain", "gap")).replace(" ", "_")
                gdir = CAPS_DIR / f"gap_{gname}"
                _v8_deploy(str(gdir / "knowledge.json"),
                           '{"name": "gap_%s", "desc": "缺口骨架（待吞噬填充）", "domains": ["%s"]}' % (gname, gname),
                           "auto_create_gap")
                created_list.append(f"gap_{gname}")
            created = {"created": created_list}
            self.state["total_caps_created"] += len(created.get("created", []))
            self._save_state()

            # 自动连接全邻域
            created_names = created.get("created", []) if isinstance(created, dict) else []
            if created_names:
                self._connect_neighborhoods(
                    cap_name=str(created_names[0]) if created_names else "auto_created",
                    cap_domains=["AI域", "创新实验室"]
                )

            return created
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}

    

    # ═══════════════════════════════════════════════════════════
    #  认知循环 — v3.0 + 大脑接线
    # ═══════════════════════════════════════════════════════════

    _BRAIN_POOL = None  # ⛔ 2026-08-28 线程泄漏修复: 复用有界池, 不再每次spawn超时孤儿线程

    _BRAIN_CACHE = {}  # ⛔ 2026-08-28 性能: 同问30s TTL缓存 — digest/reflect多次调用不重复LLM
    _BRAIN_CACHE_TTL = 30.0

    def _consult_brain(self, question: str, context: str = "", timeout: float = 8.0) -> dict:
        """脑子不好使时求助脑委会 — 全异常保护, 保证降级; ⛔ 2026-08-28 性能: 8s超时防阻塞认知循环
        线程泄漏修复: 用共享有界ThreadPoolExecutor, 超时后线程回池复用而非孤儿累积
        性能: 同问30s缓存复用"""
        import time as _tm_c
        _ckey = context + "|" + str(question)[:100]
        _now_c = _tm_c.time()
        _hit = DevourTentacle._BRAIN_CACHE.get(_ckey)
        if _hit and (_now_c - _hit[0]) < DevourTentacle._BRAIN_CACHE_TTL:
            return _hit[1]
        import threading as _th
        if DevourTentacle._BRAIN_POOL is None:
            import concurrent.futures as _cf
            DevourTentacle._BRAIN_POOL = _cf.ThreadPoolExecutor(max_workers=2, thread_name_prefix="brain_consult")
        _out_box = {}

        def _worker():
            try:
                # V8: 脑委会 → llm 桥（DeepSeek/多引擎密钥链）
                from .llm import bridge as _LB
                _r = _LB.chat(f"[{context}] {question}", max_tokens=500, timeout=45)
                if _r.get("ok") and str(_r.get("reply", "")).strip():
                    _out_box["r"] = {"ok": True, "reply": _r["reply"][:800]}
                else:
                    _out_box["r"] = {"ok": False, "brain_unavailable": True,
                                     "note": str(_r.get("error", "LLM 空回复"))[:80]}
            except BaseException as _be:
                _out_box["r"] = {"ok": False, "brain_unavailable": True, "note": str(_be)[:80]}

        _fut = DevourTentacle._BRAIN_POOL.submit(_worker)
        try:
            _fut.result(timeout=timeout)
        except Exception:
            pass  # 超时: 线程回池, 结果丢弃 (不孤儿)
        if "r" in _out_box:
            DevourTentacle._BRAIN_CACHE[_ckey] = (_tm_c.time(), _out_box["r"])
        else:
            # ⛔ 超时也缓存: 同问30s内直接复用降级结果, 不再等LLM (digest二次5.3s→<1s)
            DevourTentacle._BRAIN_CACHE[_ckey] = (_tm_c.time(), {"ok": False, "brain_timeout": True, "note": f"脑委会{timeout}s超时(缓存), 降级到本地推理"})
        if len(DevourTentacle._BRAIN_CACHE) > 50:
            DevourTentacle._BRAIN_CACHE = {k: v for k, v in DevourTentacle._BRAIN_CACHE.items() if _now_c - v[0] < DevourTentacle._BRAIN_CACHE_TTL}
        return DevourTentacle._BRAIN_CACHE[_ckey][1]
    def reflect(self) -> dict:
        """反思: 回顾历史吞噬, 学习模式, 自我批评, 生成改进建议"""
        import json as _json
        
        history = self.state
        total = history.get("total_devours", 0)
        
        caps_dir = CAPS_DIR
        cap_quality = {}
        if not caps_dir.exists():
            return {"ok": True, "total_devours": 0, "weak_caps": [],
                    "potential_pairs": [], "insights": [], "cap_quality_summary": {"total": 0}}
        for cap_dir in sorted(caps_dir.iterdir()):
            if not cap_dir.is_dir() or cap_dir.name.startswith(".") or cap_dir.name.startswith("_"):
                continue
            cap_json = cap_dir / "knowledge.json"
            if not cap_json.exists():
                continue
            try:
                data = _json.loads(cap_json.read_text(encoding="utf-8"))
                # Basic analysis without analyze_cap_structure (not available in base)
                actions = len(data.get("actions", {}))
                keywords = len(data.get("triggers", {}).get("keywords", []) if isinstance(data.get("triggers"), dict) else [])
                cap_quality[cap_dir.name] = {
                    "score": 80 if actions > 1 else 40,
                    "actions": actions,
                    "keywords": keywords,
                    "orphans": 0,
                    "has_parent": "parent_cap" in data,
                    "has_absorbed": (cap_dir / "absorbed_knowledge.md").exists(),
                }
            except Exception:
                cap_quality[cap_dir.name] = {"score": 0, "error": "parse failed"}
        
        weak_caps = []
        strong_caps = []
        for name, quality in cap_quality.items():
            if quality.get("score", 100) < 30:
                weak_caps.append({"name": name, "score": quality["score"], "reason": "评分极低"})
            elif quality.get("actions", 0) <= 1 and not quality.get("has_parent"):
                weak_caps.append({"name": name, "score": quality["score"], "reason": "单action骨架"})
            else:
                strong_caps.append(name)
        
        suggestions = []
        if weak_caps:
            suggestions.append(f"薄弱cap({len(weak_caps)}个): {[c['name'] for c in weak_caps[:5]]}")
            suggestions.append("建议: 注入知识或拆分重组")
        
        potential_pairs = []
        if len(strong_caps) >= 2:
            for i, c1 in enumerate(strong_caps[:30]):
                q1 = cap_quality.get(c1, {})
                for c2 in strong_caps[i+1:31]:
                    q2 = cap_quality.get(c2, {})
                    # 简单启发: actions数接近且都有吸收知识 = 好重组候选
                    if abs(q1.get("actions",0)-q2.get("actions",0)) <= 2 and q1.get("has_absorbed") and q2.get("has_absorbed"):
                        potential_pairs.append({"cap1": c1, "cap2": c2,
                            "a1": q1.get("actions",0), "a2": q2.get("actions",0)})
        
        if potential_pairs:
            suggestions.append(f"重组候选({len(potential_pairs)}对)")
        
        # 脑子不好使 -> 求助大脑
        brain_advice = None
        if len(weak_caps) > 15:
            try:
                brain_advice = self._consult_brain(
                    f"{len(weak_caps)}个薄弱cap需优化: {[c['name'] for c in weak_caps[:5]]}",
                    context="devour_reflect", timeout=4.0
                )
            except Exception as _e:
                print(f"⚠️ devour_tentacle: 吞错: {_e}", file=sys.stderr)
        self.state.setdefault("reflections", [])
        self.state["reflections"].append({
            "at": datetime.now().isoformat(),
            "total_caps": len(cap_quality), "weak": len(weak_caps), "strong": len(strong_caps),
        })
        self.state["reflections"] = self.state["reflections"][-50:]
        self._save_state()
        
        return {
            "ok": True,
            "cap_quality_summary": {"total": len(cap_quality), "avg_score": sum(q.get("score",0) for q in cap_quality.values())//max(len(cap_quality),1), "weak": len(weak_caps), "strong": len(strong_caps)},
            "weak_caps": weak_caps[:10],
            "potential_pairs": potential_pairs[:10],
            "suggestions": suggestions,
            "brain_advice": brain_advice.get("synthesis", "") if brain_advice and brain_advice.get("ok") else None,
        }

    def digest(self) -> dict:
        """消化: 读取所有cap的吸收知识, 交叉引用, 合成新洞察"""
        import json as _json
        
        caps_dir = CAPS_DIR
        all_knowledge = {}
        for cap_dir in sorted(caps_dir.iterdir()):
            if not cap_dir.is_dir() or cap_dir.name.startswith(".") or cap_dir.name.startswith("_"):
                continue
            abs_file = cap_dir / "absorbed_knowledge.md"
            if not abs_file.exists():
                continue
            try:
                content = abs_file.read_text(encoding="utf-8")
                items = [line.strip("- ").strip() for line in content.split("\n") if line.strip().startswith("-") and len(line.strip()) > 2]
                if items:
                    all_knowledge[cap_dir.name] = items
            except Exception as _e:
                print(f"⚠️ devour_tentacle: 吞错: {_e}", file=sys.stderr)
        if not all_knowledge:
            return {"ok": True, "digested": 0, "message": "无吸收知识可消化"}
        
        knowledge_index = {}
        for cap_name, items in all_knowledge.items():
            for item in items:
                keywords = [w for w in item.lower().replace("/"," ").replace("-"," ").split() if len(w) > 2 and w not in ("the","and","for","with","via","etc","基于","用于","支持")]
                for kw in keywords:
                    knowledge_index.setdefault(kw, set()).add(cap_name)
        
        cross_refs = []
        for kw, caps in knowledge_index.items():
            if len(caps) >= 2:
                cross_refs.append({"keyword": kw, "shared_by": sorted(caps), "count": len(caps)})
        cross_refs.sort(key=lambda x: x["count"], reverse=True)
        
        synthesized = []
        for ref in cross_refs[:20]:
            shared = []
            for cap in ref["shared_by"]:
                for item in all_knowledge.get(cap, []):
                    if ref["keyword"] in item.lower():
                        shared.append(f"[{cap}] {item}")
            if shared:
                synthesized.append({"keyword": ref["keyword"], "shared_caps": ref["shared_by"], "combined": shared[:5], "insight": f"跨{len(ref['shared_by'])}个cap共享,可重组"})
        
        all_caps_with_actions = set()
        for cap_dir in caps_dir.iterdir():
            if cap_dir.is_dir() and not cap_dir.name.startswith("."):
                cap_json = cap_dir / "knowledge.json"
                if cap_json.exists():
                    try:
                        data = _json.loads(cap_json.read_text(encoding="utf-8"))
                        if data.get("actions") and len(data["actions"]) > 1:
                            all_caps_with_actions.add(cap_dir.name)
                    except Exception as _e:
                        print(f"⚠️ devour_tentacle: 吞错: {_e}", file=sys.stderr)
        caps_without_knowledge = all_caps_with_actions - set(all_knowledge.keys())
        
        brain_synthesis = None
        if len(cross_refs) > 5:
            try:
                brain_synthesis = self._consult_brain(
                    f"跨cap知识关联{len(cross_refs)}个, 前3: {[(r['keyword'], r['shared_by']) for r in cross_refs[:3]]}",
                    context="devour_digest", timeout=4.0
                )
            except Exception as _e:
                print(f"⚠️ devour_tentacle: 吞错: {_e}", file=sys.stderr)
        return {
            "ok": True,
            "digested": len(all_knowledge),
            "total_knowledge_items": sum(len(v) for v in all_knowledge.values()),
            "cross_references": len(cross_refs),
            "top_cross_refs": cross_refs[:15],
            "synthesized_insights": synthesized[:10],
            "caps_without_knowledge": sorted(caps_without_knowledge)[:10],
            "brain_synthesis": brain_synthesis.get("synthesis", "") if brain_synthesis and brain_synthesis.get("ok") else None,
            "message": f"消化{len(all_knowledge)}个cap/{sum(len(v) for v in all_knowledge.values())}条知识, {len(cross_refs)}个跨cap关联",
        }

    def recombine(self, cap1: str, cap2: str, new_name: str = None) -> dict:
        """重组: 拆解两个cap + 提取互补部分 + 创建全新杂交cap

        防级联：_x_ 杂交产物不得作为再杂交源（旧病根：越重组越滋生——bandit_x_x_...）。
        单级杂交（原始 × 原始）合法；级联在此拒绝。
        """
        import json as _json
        from .store import audit as _audit
        if "_x_" in cap1 or "_x_" in cap2 or (new_name and "_x_" in new_name and new_name.count("_x_") >= 2):
            _audit("devour_reject", {"step": "recombine", "why": "cascade", "cap1": cap1, "cap2": cap2})
            return {"ok": False, "error": "级联杂交被拒：杂交产物不可再作为杂交源（防膨胀）"}
        _audit("devour_chain", {"step": "devour_tentacle.recombine"})
        brain_merge = None
        
        f1, f2 = CAPS_DIR/cap1/"knowledge.json", CAPS_DIR/cap2/"knowledge.json"
        if not f1.exists() or not f2.exists():
            return {"ok": False, "error": "cap不存在"}
        
        data1 = _json.loads(f1.read_text(encoding="utf-8"))
        data2 = _json.loads(f2.read_text(encoding="utf-8"))
        
        actions1 = set(data1.get("actions", {}).keys())
        actions2 = set(data2.get("actions", {}).keys())
        unique_to_1 = actions1 - actions2
        unique_to_2 = actions2 - actions1
        
        kws1 = set(data1.get("triggers", {}).get("keywords", []) if isinstance(data1.get("triggers"), dict) else [])
        kws2 = set(data2.get("triggers", {}).get("keywords", []) if isinstance(data2.get("triggers"), dict) else [])
        merged_kws = list(kws1 | kws2)[:20]
        
        if not new_name:
            new_name = f"{cap1}_x_{cap2}"[:50].replace("__", "_")
        # 总长硬上限 56 字符（防杂交链无限嵌套增长）
        if len(new_name) > 56:
            import hashlib as _hl
            _h = _hl.md5(new_name.encode("utf-8")).hexdigest()[:6]
            new_name = new_name[:49].rstrip("_") + "_" + _h
        new_dir = CAPS_DIR / new_name
        if new_dir.exists():
            # 冲突用短哈希后缀（而非叠加 _hybrid），杜绝名字膨胀
            import hashlib as _hl2
            _h2 = _hl2.md5(f"{cap1}|{cap2}|{datetime.now().isoformat()}".encode()).hexdigest()[:6]
            new_name = (new_name[:48].rstrip("_") + "_" + _h2) if len(new_name) > 48 else (new_name + "_" + _h2)
            new_dir = CAPS_DIR / new_name
        
        if len(unique_to_1) + len(unique_to_2) < 2:
            try:
                brain_merge = self._consult_brain(
                    f"创意重组{cap1}({list(actions1)})和{cap2}({list(actions2)})",
                    context="devour_recombine"
                )
            except Exception as _e:
                print(f"⚠️ devour_tentacle: 吞错: {_e}", file=sys.stderr)
        # ⛔ 2026-08-02 修复: 目录创建改为 publish 托管 (镜像验证), 不再直接 mkdir 写项目树
        _gk_rb = type("_GK", (), {"publish": staticmethod(lambda p, content=None, note="": _v8_publish(p, content, note))})()
        _gk_rb.publish(str(new_dir / ".gbt_dir_marker"), "dir", "devour_recombine_mkdir")
        
        hybrid_actions = {}
        for a in unique_to_1:
            hybrid_actions[a] = {**data1["actions"][a], "origin": cap1}
        for a in unique_to_2:
            hybrid_actions[a] = {**data2["actions"][a], "origin": cap2}
        if not hybrid_actions:
            first1 = list(actions1)[0] if actions1 else None
            first2 = list(actions2)[0] if actions2 else None
            if first1:
                hybrid_actions[f"{cap1}_{first1}"] = {**data1["actions"][first1], "origin": cap1}
            if first2:
                hybrid_actions[f"{cap2}_{first2}"] = {**data2["actions"][first2], "origin": cap2}
        
        hybrid_cap = {
            "name": new_name, "version": "1.0.0",
            "description": f"杂交: {cap1} x {cap2}",
            "language": "python", "risk_level": "safe", "auto_exec": False,
            "category": "AI", "recombined_from": [cap1, cap2],
            "entry": data1.get("entry", {"program": "python", "args": ["run.py"]}),
            "triggers": {"keywords": merged_kws, "intent": f"use_{new_name}", "examples": []},
            "actions": hybrid_actions,
            "domains": list(set(data1.get("domains",[]) + data2.get("domains",[]))),
        }
        import importlib.util as _iu_dpy
        _dpy = type("_DPY", (), {"deploy": staticmethod(_v8_deploy)})()
        _dpy.deploy(str(new_dir/"knowledge.json"), _json.dumps(hybrid_cap, ensure_ascii=False, indent=2), context="devour_recombine")
        
        run_py = f'"""caps/{new_name}/run.py — {cap1}x{cap2}"""\\nimport json\\nprint(json.dumps({{"ok":True,"hybrid":"{cap1}x{cap2}"}}))\\n'
        _dpy.deploy(str(new_dir/"run.py"), run_py, context="devour_recombine_run")
        
        abs1, abs2 = CAPS_DIR/cap1/"absorbed_knowledge.md", CAPS_DIR/cap2/"absorbed_knowledge.md"
        combined = []
        if abs1.exists(): combined.append(abs1.read_text(encoding="utf-8"))
        if abs2.exists(): combined.append(abs2.read_text(encoding="utf-8"))
        if combined:
            # ⛔ 2026-08-02 修复: absorbed_knowledge.md 走 publish 管线, 不直接写
            _gk_abs = type("_GK", (), {"publish": staticmethod(lambda p, content=None, note="": _v8_publish(p, content, note))})()
            _gk_abs.publish(str(new_dir/"absorbed_knowledge.md"), f"# 杂交: {cap1} x {cap2}\n\n"+"\n".join(combined), "devour_recombine_abs")
        
        self.state.setdefault("recombine_history", [])
        self.state["recombine_history"].append({"sources":[cap1,cap2],"result":new_name,"at":datetime.now().isoformat()})
        self.state["total_caps_created"] += 1
        self._save_state()
        
        try:
            self._connect_neighborhoods(cap_name=new_name, 
                                       cap_domains=list(set(data1.get("domains",[]) + data2.get("domains",[]))))
        except Exception as _e:
            print(f"⚠️ devour_tentacle: 吞错: {_e}", file=sys.stderr)
        return {
            "ok": True, "recombined": True,
            "sources": [cap1, cap2], "new_cap": new_name,
            "unique_actions": {"from_"+cap1: list(unique_to_1), "from_"+cap2: list(unique_to_2)},
            "actions_count": len(hybrid_actions), "keywords_count": len(merged_kws),
            "brain_creative": bool(brain_merge.get("ok")) if brain_merge else False,
        }

    def innovate(self, domain: str = None) -> dict:
        """创新: 分析能力空白 + 行业趋势 -> 创造全新cap"""
        import json as _json
        from .store import audit as _audit
        _audit("devour_chain", {"step": "devour_tentacle.innovate"})
        import importlib.util as _iu_inn
        _dpy_inn = type("_DPY", (), {"deploy": staticmethod(_v8_deploy)})()
        
        existing = set()
        caps_dir = CAPS_DIR
        for d in caps_dir.iterdir():
            if d.is_dir() and not d.name.startswith(".") and not d.name.startswith("_"):
                existing.add(d.name)
        
        innovation_domains = {
            "wireless": {"trends": ["6G太赫兹通信","星地融合网络","量子密钥分发"], "gaps": ["卫星互联网终端","水下声学通信","太赫兹成像"]},
            "ai_agent": {"trends": ["多Agent博弈","自我进化Agent","AgentDAO"], "gaps": ["Agent谈判协议","Agent信誉系统","Agent梦境模拟"]},
            "security": {"trends": ["AI供应链攻击","大模型越狱防御","MCP安全"], "gaps": ["AI模型水印检测","联邦学习投毒防御","Prompt注入防火墙"]},
            "hardware": {"trends": ["NPU边缘推理","存算一体芯片","光子计算"], "gaps": ["NPU编译器","存内计算框架","光子神经网络SDK"]},
            "general": {"trends": ["数字孪生","可解释AI","绿色AI"], "gaps": ["数字孪生建模引擎","AI碳排放追踪","因果图自动发现"]},
        }
        
        brain_creative = None
        try:
            brain_creative = self._consult_brain(
                f"在{list(innovation_domains.keys())}领域发现创新机会, 现有{len(existing)}个cap",
                context="devour_innovate"
            )
        except Exception as _e:
            print(f"⚠️ devour_tentacle: 吞错: {_e}", file=sys.stderr)
        domains_to_scan = {domain: innovation_domains[domain]} if domain and domain in innovation_domains else innovation_domains
        
        innovations = []
        for dom_name, dom_data in domains_to_scan.items():
            for gap in dom_data.get("gaps", [])[:3]:
                cap_name = gap.lower().replace(" ","_").replace("-","_")[:50]
                if cap_name in existing: continue
                too_similar = any(len(set(cap_name.split("_")) & set(ex.split("_"))) >= 2 for ex in existing)
                if too_similar: continue
                innovations.append({"domain": dom_name, "concept": gap, "suggested_cap_name": cap_name})
        
        created = []
        for inn in innovations[:5]:
            cap_name, cap_dir = inn["suggested_cap_name"], CAPS_DIR/inn["suggested_cap_name"]
            if cap_dir.exists(): continue
            # ⛔ 2026-08-02 修复: 目录创建由 publish 托管, 不直接 mkdir 写项目树
            _gk_inn = type("_GK", (), {"publish": staticmethod(lambda p, content=None, note="": _v8_publish(p, content, note))})()
            _gk_inn.publish(str(cap_dir / ".gbt_dir_marker"), "dir", "devour_innovate_mkdir")
            
            innovative_cap = {
                "name": cap_name, "version": "1.0.0",
                "description": f"[创新] {inn['concept']} — GBT创新引擎生成",
                "language": "python", "risk_level": "safe", "auto_exec": False,
                "category": "AI", "innovation": True, "innovated_from": inn["domain"],
                "entry": {"program":"python","args":["run.py"]},
                "triggers": {"keywords":[inn["concept"]], "intent": f"use_{cap_name}", "examples":[f"用{inn['concept']}实现创新"]},
                "actions": {
                    "run": {"description":f"执行{inn['concept']}","args":["--action","run"],"input":"stdin","timeout_ms":120000,"output":"json"},
                    "research": {"description":f"研究{inn['concept']}","args":["--action","research"],"input":"stdin","timeout_ms":60000,"output":"json"},
                },
                "domains": ["创新实验室"],
            }
            _dpy_inn.deploy(str(cap_dir/"knowledge.json"), _json.dumps(innovative_cap,ensure_ascii=False,indent=2), context="devour_innovate")
            
            stub = f'"""caps/{cap_name}/run.py"""\\nimport json\\ndef do_run(p): return {{"ok":True,"cap":"{cap_name}"}}\\ndef do_research(p): return {{"ok":True}}\\nHANDLERS={{"run":do_run,"research":do_research}}\\nif __name__=="__main__":\\n    import sys\\n    a=sys.argv[3]if len(sys.argv)>3 else"run"\\n    print(json.dumps(HANDLERS.get(a,do_run)({{}})))\\n'
            _dpy_inn.deploy(str(cap_dir/"run.py"), stub, context="devour_innovate_run")
            created.append({"name":cap_name,"domain":inn["domain"],"concept":inn["concept"]})
        
        self.state.setdefault("innovation_history",[])
        self.state["innovation_history"].append({"at":datetime.now().isoformat(),"created":[c["name"]for c in created]})
        self.state["total_caps_created"]+=len(created)
        self._save_state()
        
        try:
            for _c in created:
                self._connect_neighborhoods(cap_name=_c["name"], cap_domains=[_c["domain"]])
        except Exception as _e:
            print(f"⚠️ devour_tentacle: 吞错: {_e}", file=sys.stderr)
        return {
            "ok":True,"innovated":True,
            "concepts_found":len(innovations),"created":len(created),
            "new_caps":created,"domains_explored":list(domains_to_scan.keys()),
            "brain_assisted":bool(brain_creative.get("ok"))if brain_creative else False,
            "message":f"创新引擎: 扫{len(domains_to_scan)}领域/{len(innovations)}概念 -> 创{len(created)}个创新cap",
        }

    def inject_to_tentacle(self, skill_name: str, knowledge: str) -> dict:
        """将吞噬到的知识注入到触手系统"""
        # V8: 链纪律 → 审计留痕
        from .store import audit as _audit
        _audit("devour_inject", {"skill": skill_name})
        # 记录到神经触手已知问题中
        try:
            # V8: 已知问题记录 → 吞噬状态文件（自包含）
            self.state.setdefault("known_issues", {})[f"devoured_{skill_name}"] = {
                "skill": skill_name,
                "knowledge": knowledge[:500],
                "devoured_at": datetime.now().isoformat(),
            }
            self._save_state()
            return {"ok": True, "skill": skill_name}
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}





# ═══════════════ 全局 ═══════════════

_devourer: Optional[DevourTentacle] = None


def get_devourer() -> DevourTentacle:
    global _devourer
    if _devourer is None:
        _devourer = DevourTentacle()
    return _devourer


def devour_pulse() -> dict:
    """吞噬脉冲 — 完整认知循环 v3"""
    d = get_devourer()
    devour_result = d.quick_devour()
    try: reflect_result = d.reflect()
    except: reflect_result = {"weak_caps":[],"potential_pairs":[]}
    try: digest_result = d.digest()
    except: digest_result = {"digested":0,"cross_references":0}
    recombine_count = 0
    for pair in reflect_result.get("potential_pairs",[])[:3]:
        try:
            r=d.recombine(pair["cap1"],pair["cap2"])
            if r.get("ok"): recombine_count+=1
        except Exception as _e:
            print(f"⚠️ devour_tentacle: 吞错: {_e}", file=sys.stderr)
    try: innovate_result = d.innovate()
    except: innovate_result = {"created":0,"concepts_found":0}
    return {
        "ok":True,
        "devour":devour_result,
        "reflect":{"weak_caps":len(reflect_result.get("weak_caps",[])),"recombine_candidates":len(reflect_result.get("potential_pairs",[]))},
        "digest":{"caps_digested":digest_result.get("digested",0),"cross_references":digest_result.get("cross_references",0)},
        "recombine":{"processed":min(len(reflect_result.get("potential_pairs",[])),3),"created":recombine_count},
        "innovate":{"created":innovate_result.get("created",0),"concepts":innovate_result.get("concepts_found",0)},
    }

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="吞噬触手 - 自主进化")
    p.add_argument("--pulse", action="store_true", help="快速吞噬脉冲")
    p.add_argument("--gaps", action="store_true", help="查看能力缺口")
    p.add_argument("--auto-create", action="store_true", help="自动创建缺口cap")
    p.add_argument("--state", action="store_true", help="吞噬状态")
    args = p.parse_args()

    d = get_devourer()

    if args.pulse:
        r = d.quick_devour()
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif args.gaps:
        r = d.scan_gaps()
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif args.auto_create:
        r = d.auto_create_from_gaps()
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif args.state:
        print(json.dumps(d.state, ensure_ascii=False, indent=2))
    else:
        print(f"DevourTentacle: {d.state['total_devours']} devours, {d.state['total_absorbed']} absorbed, {d.state['total_caps_created']} caps created")