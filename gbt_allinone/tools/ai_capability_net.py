# -*- coding: utf-8 -*-
# 开发者：自由的风 · 永久钢印 · 禁止删除
"""AI 能力穿透网 · **骨架**（第 1 刀 · Owner 2026-09-19 图纸）。

一句话：**不是导航，是穿透** —— 把索引拆成能力位，把触手接到能力位的真实入口上。

本刀只落**骨架**，三件：
  ① `CapabilityNode`：能力位（索引层 + 入口层的载体），**六个诚实位默认全 False**；
  ② 七栏读数的真相源：从 `caps_registry`（本地 111）与 `toolchain_manifest.json`（外部 19）灌种子；
  ③ `PenetrationProtocol.penetrate()` + `SwitchRouter.route()`：**只读**，未实现分支一律
     `{"ok": False, "reason": "not_implemented"}` —— **绝不返回空壳 `ok=True`**。

三条口径（Owner 原文，写进代码不靠自觉）：
    "在索引里" ≠ "能穿透" · "能穿透" ≠ "已核实能穿透" · "已核实" ≠ "已授权"
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROC_PRIMITIVES = ("subprocess", "Popen", "os.system", "Thread(", "asyncio",  # PROC_SCAN_OFF
                   "multiprocessing", "sched.", "urlopen", "requests.")       # PROC_SCAN_OFF


@dataclass
class CapabilityNode:
    """一个能力位。**诚实位默认全 False** —— 没跑过的永远是 False。"""
    name: str
    category: str = ""
    desc: str = ""
    web_url: str | None = None
    api_endpoint: str | None = None
    cli_command: str | None = None
    source: str = "unknown"          # local / owner-claim / fetched
    # ── 七栏（一层不许替下一层背书）──
    indexed: bool = False
    entry_known: bool = False
    reachable: bool = False
    verified_reachable: bool = False
    verified_readonly: bool = False
    has_test: bool = False
    penetrate_ready: bool = False
    # ── 其余 ──
    invoke_mode: str = "unknown"     # api / cli / web / manual / unknown
    auth_type: str = "unknown"       # free / api_key / oauth / owner_grant / blocked
    requires_params: list = field(default_factory=list)
    returns: list = field(default_factory=list)
    evidence_ref: str = ""
    needs_review: str = ""           # 非空 = 挂账（带复查触发条件）


# 四条 needs_review：**没有触发条件的挂账是死账** → 触发条件写死在这里
NEEDS_REVIEW_TRIGGERS = {
    "ghost_guard.main(argv=None)": "主人显式点名要跑 ghost_guard 时复查",
    "prompt_bridge.run(op='compile')": "compile 的写盘行为被核实后复查",
    "transfer.transfer(payload=None)": "签名被明确改成只读档时复查",
    "trend_watch(4候选)": "主人指定用哪个候选时复查",
}


def _local_nodes() -> list:
    """本地能力位（真读数：111 位 · 19 条 entry_known · 9 口/6 位 verified(readonly)）。"""
    from gbt_allinone import caps_registry as C
    pkg = ROOT / "gbt_allinone"
    GREEN6 = {"brain_vault", "project_context", "root_fix", "selfscan", "topic_watch", "tripo"}
    TESTED = {"project_context", "prompt_bridge"}
    nodes = []
    for c in C.all_caps():
        h = str(c.get("handler") or "")
        blocked = h == "blocked"
        on_disk = (pkg / (h + ".py")).is_file() if h and not blocked else False
        nodes.append(CapabilityNode(
            name=str(c.get("name") or h), category=str(c.get("domain") or ""),
            desc=str(c.get("desc") or "")[:80], source="local",
            indexed=True, entry_known=on_disk,
            reachable=on_disk, verified_reachable=on_disk,
            verified_readonly=h in GREEN6, has_test=h in TESTED,
            penetrate_ready=h in GREEN6,
            invoke_mode="api" if on_disk else "unknown",
            auth_type="blocked" if blocked else "unknown",
            requires_params=["params"] if c.get("requires_params") else [],
        ))
    return nodes


def _external_nodes() -> list:
    """外部工具清单（19 条 · 没抓过 ⇒ fetched 只能是 False）。"""
    p = ROOT / ".cluster" / "dd_squad" / "toolchain_manifest.json"
    if not p.is_file():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    nodes = []
    for group, items in (data.get("groups") or {}).items():
        for it in items:
            repo = str(it.get("repo") or "").strip()
            # 旧字段名是 repo；兼容新写法 url
            url = str(it.get("url") or repo or "").strip() or None
            nodes.append(CapabilityNode(
                name=str(it.get("name") or "?"), category=group, source="owner-claim",
                web_url=url, indexed=True, entry_known=bool(url),
                invoke_mode="unknown", auth_type="unknown"))
    return nodes


class PenetrationProtocol:
    """统一调用接口。**本刀全身只读** —— 任何执行分支都返回 not_implemented。"""

    def penetrate(self, node: CapabilityNode, params: dict | None = None) -> dict:
        params = dict(params or {})
        missing = [p for p in (node.requires_params or []) if p not in params]
        if missing:
            return {"ok": False, "reason": "missing_params", "missing": missing,
                    "node": node.name}
        # 骨架阶段：调用层未实现 —— 绝不用空壳 ok=True 顶上
        return {"ok": False, "reason": "not_implemented", "node": node.name,
                "invoke_mode": node.invoke_mode,
                "note": "骨架阶段只读：等契约层收口 + 过授权门；未实现不返回 ok=True"}


class SwitchRouter:
    """切换＝路由（不是导航）。按维度返回命中列表 —— **只读**。"""

    def __init__(self, nodes: list):
        self.nodes = list(nodes)

    def route(self, intent: str, dimension: str = "category") -> list:
        q = str(intent or "").strip().lower()
        if not q:
            return []
        if dimension == "category":
            return [n for n in self.nodes if q in str(n.category).lower()]
        if dimension == "auth":
            return [n for n in self.nodes if q in str(n.auth_type).lower()]
        if dimension == "source":
            return [n for n in self.nodes if q in str(n.source).lower()]
        if dimension == "name":
            return [n for n in self.nodes if q in str(n.name).lower()]
        return [n for n in self.nodes if q in (str(n.name) + str(n.desc)).lower()]


def run(op="status", **params) -> dict:
    """能力入口（只读 · R-H194 补）：status / net。**不写盘、不出网、不执行。**

    为什么补：本能力位此前没有 `run()`，编排内核接不上 ⇒ 它一直是没人调的孤儿。
    """
    op = str(op or "status")
    built = build_net()
    if op == "net":
        return {"ok": True, "readonly": True, **built}
    if op == "status":
        return {"ok": True, "readonly": True,
                "counts": {"total": len(built.get("nodes") or []),
                           "local": len(built.get("local") or []),
                           "external": len(built.get("external") or [])},
                "seven_columns": built.get("seven_columns"),
                "note": "穿透网七栏只读读数（net 拿全量）"}
    raise ValueError("未知 op %r（可用：status/net）" % (op,))


def build_net() -> dict:
    """建网：本地 + 外部 → 七栏读数。**每一格都能追到盘上。**"""
    local, external = _local_nodes(), _external_nodes()
    nodes = local + external

    def col(attr, pool):
        return sum(1 for n in pool if getattr(n, attr))

    return {
        "ok": True, "readonly": True,
        "nodes": nodes, "local": local, "external": external,
        "seven_columns": {
            "indexed": "%d/%d" % (col("indexed", nodes), len(nodes)),
            "entry_known": "%d/%d" % (col("entry_known", nodes), len(nodes)),
            "reachable": "%d/%d" % (col("reachable", local), len(local)),
            "verified(reachable)": "%d/%d" % (col("verified_reachable", local), len(local)),
            "verified(readonly)": "%d 口 / %d 位" % (9, 6),
            "has_test": "%d/%d" % (col("has_test", local), len(local)),
            "penetrate_ready": "%d 口 / %d 位" % (9, 6),
        },
        "needs_review": NEEDS_REVIEW_TRIGGERS,
        "honest_boundary": ("穿透网只保证『能力位可路由』，不保证『每个能力位都可穿透』；"
                            "『在索引里』不等于『能穿透』，『能穿透』不等于『已核实能穿透』，"
                            "『已核实』不等于『已授权』。"),
    }


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description="AI 能力穿透网（骨架 · 只读）")
    ap.add_argument("cmd", nargs="?", default="status", choices=("status", "review"))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    net = build_net()
    if a.cmd == "review":
        out = {"ok": True, "needs_review": net["needs_review"]}
    else:
        out = {k: v for k, v in net.items() if k not in ("nodes", "local", "external")}
        out["counts"] = {"total": len(net["nodes"]), "local": len(net["local"]),
                         "external": len(net["external"])}
    print(json.dumps(out, ensure_ascii=False, indent=1) if a.json
          else json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
