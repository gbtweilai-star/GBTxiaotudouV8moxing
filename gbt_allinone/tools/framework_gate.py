# -*- coding: utf-8 -*-
r"""框架自改门（framework_gate）· R-H99（Owner 2026-09-19 拍板：下一刀做框架自改门，含测试）

为什么要有它
------------
产品有镜像门，框架自己一直裸奔：R-H95 / R-H96 / R-H98 三轮都改了框架源码，没有一次留下
"改前基线 → 改后证据 → 回滚点"。R-H96 §五 挂出的那个问题（框架自身改动要不要走镜像）结论是
**不塞进产品镜像**：那套矩阵是给交付物设计的（查入口 index.html/main.py、文本页署名、
无 _*.py 残留），套到框架源码上会误伤——_paths.py 是正常模块、__main__.py 不在入口白名单；
而且门是框架的一部分，让框架改动走框架自己的产品管线 = 递归绕圈。

所以另立一道门，只管一件事：**改框架自己，必须有账**。

三条硬规则（fail-closed）
------------------------
1. 改前有基线：snapshot 记下每个被监视文件的 sha256；没有基线 ⇒ verify 直接红（no_baseline）。
2. 改后有护照：open（为什么改）→ 动手 → close（证据 / 回滚点 / 印章）。
   close 缺件、或证据不是 "命令 => 读数" 的形状 ⇒ 拒绝关闭（rc=2）。
3. 没护照 = 红：verify 逐文件比对当前指纹与基线，任何变动必须被"已关闭、且 after 哈希与当前
   一致"的护照认领，否则 no_passport / stale_passport ⇒ rc=1。

**多脑复核（R-H105 · 主人 2026-09-19）**：一个 AI 可能犯傻，整个脑子不会同时傻 ——
所以"我自己说改好了"不算数。护照必须有**独立复核**：`--review "<checker>: <命令> => <读数>"`，
且 `checker` 与任何 `--evidence` 的标签**不许相同**（同一方既当运动员又当裁判 = 退回单方证据）。
机械上能查的是"形式独立"（标签不同、读数独立）；"复核是否真独立、是否真懂"查不了 —— 这条
边界如实写在 verify 输出里，不假装门能替人做判断。

分工：镜像门管"把成品放出去"，本门管"改框架自己"。共同纪律只有一条：没有证据的结论不采信。

用法
----
    python -m gbt_allinone.tools.framework_gate snapshot --label "R-H99 起点"
    python -m gbt_allinone.tools.framework_gate open --reason "修 X 的根因"
    python -m gbt_allinone.tools.framework_gate close --id fc-20260919T1130-ab12 \
        --evidence "py -3.10 gbt_allinone/tests/test_framework.py -k auth => Ran 6 tests OK" \
        --stamp .scratch/_stamp_xxx.json --rollback "按护照 before 哈希逐字节还原"
    python -m gbt_allinone.tools.framework_gate verify
    python -m gbt_allinone.tools.framework_gate status

--root 可指向别的工作区（测试用隔离树），--store 可指向别的账本目录（测试用临时目录）。
本工具只写自己的账本，不碰镜像维度、不碰生产面、不碰授权门。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import string
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# 监视范围：框架自身源码 + APP 侧源码（**改了会改变系统行为**的文件）
#
# R-H166（Owner 2026-09-19）：加 holo_pet_w3。实测教训（R-H165）——改了
# holo_pet_w3/shell/main.cjs（40,572 → 40,725 B，W3 壳的出口清单），而护照上记的是
# **changed_files: 0**。不是"没改"，是"门看不见它"：W3 3D 壳是真实产品面
# （holo_pet/启动3D数字人.bat 的入口壳），却在门的可见范围之外 ⇒ **账实不符**。
# 判据：**凡是"改了它，系统行为就会变"的源码面，都必须在可见范围内。**
# 逐个目录的判定与理由见 docs/自改门监视范围判定.md。
# R-H176 补齐三个缺口（登记簿 §五 G1/G2/G3 —— 全是"门看不见"的现场）：
#   G1 potato_pet/：checkpoint.py 的 PROD_TREE_ROOTS 含它、holo_pet 在读它的 config、
#      tests/test_framework.py 还把它插进 sys.path ⇒ **它的代码被框架测试真跑到**；
#   G2 .bat：启动器改一行就是行为变化（holo_pet 4 个 + potato_pet 2 个）；
#   G3 .json：被代码真读的"单一真相源"（dd_squad/toolchain_manifest.json）——
#      放宽成"全 json"会把 store/state 全卷进来，所以走**显式单文件**（见 _WATCH_EXTRA_FILES）。
_WATCH_DIRS = ("gbt_allinone", "holo_pet", "holo_pet_w3", "potato_pet")
_WATCH_SUFFIX = (".py", ".js", ".cjs", ".html", ".css", ".bat")
# 显式单文件：不在 _WATCH_DIRS 里、也不吃后缀规则，但**被代码真读**、改了行为就变。
_WATCH_EXTRA_FILES = (".cluster/dd_squad/toolchain_manifest.json",)
# 根级**指令文件**：它们改一个字就能改系统行为，比源码更该留账（R-H99 第二刀）。
# 不含 USER.md / MEMORY.md —— 那两份是主人自己的记忆载体，另有归属规则，不属于"框架自改"。
_WATCH_ROOT_FILES = ("AGENTS.md", "HEARTBEAT.md", "CHARTER.md", "SOUL.md", "CODING_DISCIPLINE.md")
# 依赖树 / 缓存 / 产物 / 版本库：不是源码，改了也不该红（宁可漏报噪声，不许误报）
_SKIP_DIRS = {
    "__pycache__", "node_modules", ".git", ".pylibs", "store", ".scratch",
    "archive", "resources", "dist", "build", ".venv", "site-packages",
    # R-H176 建议落地：`.backups` 从"恰好没纳"改成"**显式声明不纳**"（免得以后被顺手纳进来）
    ".backups",
}


def _default_store() -> Path:
    try:
        sys.path.insert(0, str(ROOT))
        from gbt_allinone import _paths
        return Path(_paths.STORE_DIR) / "framework_changes"
    except Exception:  # noqa: BLE001
        return ROOT / "gbt_allinone" / "store" / "framework_changes"


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def _watched(root: Path) -> list:
    out = []
    for name in _WATCH_ROOT_FILES:
        p = root / name
        if p.is_file():
            out.append(p)
    # R-H176：显式单文件（G3）——路径写死，不受后缀规则与目录范围影响
    for rel in _WATCH_EXTRA_FILES:
        p = root / rel
        if p.is_file():
            out.append(p)
    for top in _WATCH_DIRS:
        base = root / top
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
            for name in filenames:
                if name.lower().endswith(_WATCH_SUFFIX):
                    out.append(Path(dirpath) / name)
    return sorted(out)


def fingerprint(root: Path) -> dict:
    """当前指纹：相对路径（/ 分隔）→ sha256。"""
    return {p.relative_to(root).as_posix(): _sha(p) for p in _watched(root)}


def _load(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _save(p: Path, data: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _new_id() -> str:
    tail = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(4))
    return "fc-%s-%s" % (time.strftime("%Y%m%dT%H%M%S"), tail)


def _baseline_path(store: Path) -> Path:
    return store / "baseline.json"


def _passports_dir(store: Path) -> Path:
    return store / "passports"


def _passports(store: Path) -> list:
    rows = []
    for p in sorted(_passports_dir(store).glob("*.json")):
        d = _load(p)
        if d.get("id"):
            d["_path"] = str(p)
            rows.append(d)
    return rows


def _label_of(entry: str) -> str:
    """证据条目的"出具方"标签：`--review` 用 `<checker>: ...` 显式声明；evidence 取第一段。"""
    text = str(entry or "").strip()
    if ":" in text.split("=>")[0]:
        head = text.split(":", 1)[0].strip()
        if head and " " not in head:
            return head
    return text.split("=>")[0].split()[0] if text.split("=>")[0].split() else ""


def _diff(before: dict, after: dict) -> dict:
    return {k: {"before": before.get(k), "after": after.get(k)}
            for k in set(before) | set(after) if before.get(k) != after.get(k)}


def cmd_snapshot(args) -> int:
    root, store = Path(args.root).resolve(), Path(args.store).resolve()
    # 坑册第 30 条（R-H107）：**基线不能吞护照**。任何能抹掉变更证据的动作，
    # 本身必须先被门挡一次 —— 开着护照重立基线，会让"没护照=红"这条规则被绕过
    # （实测踩过：护照还开着，verify 却先变绿了）。
    open_ps = [p for p in _passports(store) if not p.get("closed_at")]
    if open_ps and not getattr(args, "force", False):
        print(json.dumps({
            "ok": False, "stage": "snapshot", "blocked": True,
            "reason_code": "passport_open",
            "open_passports": [p["id"] for p in open_ps],
            "error": "存在未关闭护照：重立基线会把它们的改动吞进基线，等于抹掉变更证据",
            "how_to": "先 close 那些护照；确要吞掉就显式 --force --reason \"为什么值得\"（这次吞并会留痕）",
        }, ensure_ascii=False, indent=1))
        return 2
    fp = fingerprint(root)
    rec = {"at": _now(), "label": args.label or "", "note": args.note or "",
           "root": str(root), "files": fp, "count": len(fp),
           "forced_over_open_passports": [p["id"] for p in open_ps] if open_ps else [],
           "force_reason": (getattr(args, "reason", "") or "") if open_ps else ""}
    _save(_baseline_path(store), rec)
    out = {"ok": True, "stage": "snapshot", "at": rec["at"],
           "label": rec["label"], "files": len(fp), "store": str(store)}
    if open_ps:
        # 坑册一族（R-H141 实测）：**吞并 ≠ 结案**。被吞的护照仍然是"开着"的，
        # 所以它**会继续挡下一次 snapshot**。不提示的话，操作者以为吞完就完了。
        out["forced_note"] = ("被吞的护照仍在开：%s —— 要么 close 它们，要么它们会继续挡下一次 snapshot"
                              "（吞并 ≠ 结案）" % ", ".join(p["id"] for p in open_ps))
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


def cmd_open(args) -> int:
    root, store = Path(args.root).resolve(), Path(args.store).resolve()
    reason = (args.reason or "").strip()
    if len(reason) < 8:
        print(json.dumps({"ok": False, "stage": "open", "reason_code": "reason_too_short",
                          "error": "reason 太短：自改护照必须写清『为什么改』（>=8 字）"},
                         ensure_ascii=False, indent=1))
        return 2
    cid = _new_id()
    rec = {"id": cid, "opened_at": _now(), "closed_at": None, "label": args.label or "",
           "reason": reason, "root": str(root), "before": fingerprint(root), "after": None,
           "evidence": [], "rollback": "", "stamp": None, "no_stamp_reason": "",
           "decision": "", "changed": {}}
    _save(_passports_dir(store) / (cid + ".json"), rec)
    print(json.dumps({"ok": True, "stage": "open", "id": cid, "reason": reason,
                      "files_at_open": len(rec["before"])}, ensure_ascii=False, indent=1))
    return 0


def cmd_close(args) -> int:
    store = Path(args.store).resolve()
    path = _passports_dir(store) / (args.id + ".json")
    rec = _load(path)
    if not rec:
        print(json.dumps({"ok": False, "stage": "close", "reason_code": "passport_not_found",
                          "error": "找不到护照 " + args.id}, ensure_ascii=False, indent=1))
        return 2

    problems = []
    evidence = [str(e).strip() for e in (args.evidence or []) if str(e).strip()]
    if not evidence:
        problems.append("缺证据：--evidence 至少一条")
    if any("=>" not in e for e in evidence):
        problems.append("证据形状不对：每条都要写成『命令 => 读数』")
    rollback = (args.rollback or "").strip()
    if len(rollback) < 8:
        problems.append("缺回滚点：--rollback 要说清怎么退回去（>=8 字）")
    stamp = None
    if args.stamp:
        sp = Path(args.stamp)
        if not sp.exists():
            problems.append("--stamp 指向的文件不存在：" + str(sp))
        else:
            stamp = {"path": str(sp), "sha256": _sha(sp), "at": _now()}
            data = _load(sp)
            if isinstance(data, dict) and data:
                stamp["four_tuple"] = {k: data.get(k) for k in
                                       ("python", "store", "comparability", "identity")
                                       if k in data}
    elif not (args.no_stamp_reason or "").strip():
        problems.append("缺回归印章：给 --stamp <印章.json>，或显式写 --no-stamp-reason 『为什么这轮没法盖章』")

    # 多脑复核（R-H105）：单方证据不许算过关
    reviews = [str(r).strip() for r in (args.review or []) if str(r).strip()]
    if not reviews and not (args.no_review_reason or "").strip():
        problems.append("缺独立复核：给 --review \"<checker>: <命令> => <读数>\"（另一个 checker 出具的读数），"
                        "或显式写 --no-review-reason 『为什么这轮没有独立复核』")
    if any("=>" not in r for r in reviews):
        problems.append("复核形状不对：每条复核都要写成『<checker>: <命令> => <读数>』")
    if reviews:
        ev_labels = {_label_of(e) for e in evidence if _label_of(e)}
        rv_labels = {_label_of(r) for r in reviews if _label_of(r)}
        same = sorted(ev_labels & rv_labels)
        if same:
            problems.append(f"复核不独立：{same} 同时出现在证据与复核里（同一方既当运动员又当裁判）")
        if len(rv_labels) < len(reviews):
            problems.append("复核缺 checker 标签：每条复核都要以 `<checker>: ` 开头")

    if problems:
        print(json.dumps({"ok": False, "stage": "close", "id": args.id, "blocked": True,
                          "problems": problems, "reason_code": "passport_incomplete",
                          "note": "拒绝关闭：护照不完整就不算改完（fail-closed）"},
                         ensure_ascii=False, indent=1))
        return 2

    after = fingerprint(Path(args.root).resolve())
    # 认领范围 = **相对基线的偏差**（不是相对"开护照那一刻"）。
    # 实测教训（R-H99 自己的用例当场抓出）：真实顺序常常是"先改、后想起开护照"，
    # 若按 open→close 算，这种改动就认领不到 ⇒ verify 永远红，门变成摆设。
    base_files = (_load(_baseline_path(store)).get("files") or {})
    ref = base_files or (rec.get("before") or {})
    rec.update({"closed_at": _now(), "after": after, "evidence": evidence,
                "review": reviews,
                "no_review_reason": (args.no_review_reason or "").strip(),
                "rollback": rollback, "stamp": stamp,
                "no_stamp_reason": (args.no_stamp_reason or "").strip(),
                "decision": (args.decision or "").strip(),
                "changed": _diff(ref, after),
                "changed_ref": "baseline" if base_files else "open_state",
                "open_diff": _diff(rec.get("before") or {}, after)})
    _save(path, rec)
    print(json.dumps({"ok": True, "stage": "close", "id": args.id,
                      "changed_files": len(rec["changed"]),
                      "changed": sorted(rec["changed"])[:20],
                      "has_stamp": bool(stamp), "closed_at": rec["closed_at"]},
                     ensure_ascii=False, indent=1))
    return 0


def cmd_verify(args) -> int:
    root, store = Path(args.root).resolve(), Path(args.store).resolve()
    base = _load(_baseline_path(store))
    if not base.get("files"):
        print(json.dumps({"ok": False, "stage": "verify", "verdict": "red",
                          "reason_code": "no_baseline",
                          "how_to": "先跑 snapshot 立基线，再改框架源码"},
                         ensure_ascii=False, indent=1))
        return 1

    current = fingerprint(root)
    changed = _diff(base["files"], current)
    closed = [p for p in _passports(store) if p.get("closed_at") and p.get("after")]
    findings = []
    for rel, info in sorted(changed.items()):
        owners = [p for p in closed if rel in (p.get("changed") or {})]
        fresh = [p for p in owners if (p.get("after") or {}).get(rel) == info["after"]]
        if not owners:
            findings.append({"file": rel, "reason_code": "no_passport",
                             "detail": "改了但没有自改护照认领"})
        elif not fresh:
            findings.append({"file": rel, "reason_code": "stale_passport",
                             "detail": "护照之后又改过；涉及护照 "
                                       + str(sorted(p["id"] for p in owners))})
    out = {"ok": not findings, "stage": "verify",
           "verdict": "green" if not findings else "red",
           "baseline_at": base.get("at"), "baseline_files": base.get("count"),
           "changed_files": len(changed), "passports_closed": len(closed),
           "stamp_waived_passports": [p["id"] for p in closed if not p.get("stamp")],
           "review_waived_passports": [p["id"] for p in closed if not (p.get("review") or [])],
           "findings": findings,
           "law": "改框架自己也要有账：改前基线 → 改后护照（原因/证据/**独立复核**/回滚）→ 没护照就是红",
           "honest_limit": ("门能查的是**形式独立**（复核 checker 标签不同、读数独立）；"
                            "复核到底独不独立、懂不懂，门查不了 —— 那一步只能靠人或多脑交叉，不假装门能替。")}
    if findings and args.json:
        out["changed"] = {k: v["after"] for k, v in list(changed.items())[:50]}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if not findings else 1


def cmd_status(args) -> int:
    store = Path(args.store).resolve()
    base = _load(_baseline_path(store))
    rows = [{"id": p["id"], "opened_at": p.get("opened_at"), "closed_at": p.get("closed_at"),
             "reason": p.get("reason"), "changed_files": len(p.get("changed") or {}),
             "has_stamp": bool(p.get("stamp")),
             "complete": bool(p.get("closed_at") and p.get("evidence") and p.get("rollback"))}
            for p in _passports(store)]
    print(json.dumps({"ok": True, "stage": "status", "store": str(store),
                      "baseline_at": base.get("at"), "baseline_files": base.get("count"),
                      "passports": rows, "count": len(rows)}, ensure_ascii=False, indent=1))
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="框架自改门：改框架自己必须留账（fail-closed）")
    ap.add_argument("--root", default=str(ROOT), help="工作区根（默认本仓；测试可指隔离树）")
    ap.add_argument("--store", default=str(_default_store()),
                    help="账本目录（默认 store/framework_changes）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("snapshot", help="立基线：记下当前所有被监视文件的 sha256")
    s1.add_argument("--label", default="")
    s1.add_argument("--note", default="")
    s1.add_argument("--force", action="store_true",
                    help="存在未关闭护照时仍要立基线（=承认会吞掉变更证据，必须配 --reason）")
    s1.add_argument("--reason", default="", help="--force 时必填：为什么值得吞")
    s1.set_defaults(func=cmd_snapshot)

    s2 = sub.add_parser("open", help="开一张自改护照（写清为什么改）")
    s2.add_argument("--reason", required=True)
    s2.add_argument("--label", default="")
    s2.set_defaults(func=cmd_open)

    s3 = sub.add_parser("close", help="关闭护照（证据 / 回滚点 / 印章，缺一不可）")
    s3.add_argument("--id", required=True)
    s3.add_argument("--evidence", action="append", default=[])
    s3.add_argument("--review", action="append", default=[],
                    help="独立复核（多脑复核）：\"<checker>: <命令> => <读数>\"，checker 不许与证据同标签")
    s3.add_argument("--no-review-reason", default="",
                    help="确无独立复核时显式写原因（verify 会把它当豁免列出来）")
    s3.add_argument("--rollback", default="")
    s3.add_argument("--stamp", default="")
    s3.add_argument("--no-stamp-reason", default="")
    s3.add_argument("--decision", default="")
    s3.set_defaults(func=cmd_close)

    s4 = sub.add_parser("verify", help="对账：有变动没护照 ⇒ 红（rc=1）")
    s4.add_argument("--json", action="store_true", help="附上变动文件清单")
    s4.set_defaults(func=cmd_verify)

    s5 = sub.add_parser("status", help="看基线 + 护照清单（只读）")
    s5.set_defaults(func=cmd_status)
    return ap


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
