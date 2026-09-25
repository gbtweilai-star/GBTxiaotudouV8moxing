#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""**永远不会红的判据**审计器（AST 版）。

由来（一手，2026-09-25）：
    我改面板快照时把嵌数据**写坏了**，而 `verify_v22.py` 报「49 通过」一声没吭。
    查下去发现两件事：
      · `verify_v21.py:178` / `verify_v20.py:141` 那条「原型无 undefined 字面量」
        末尾写着 **`or True`** ⇒ **恒真，从出生起就不可能红**；
      · **现行**的 `verify_v22.py` 干脆没有这一条（换代时判据丢了）。
    ⇒ **「条数」不等于「牙齿」。** 这个审计器专抓"看起来在判、其实恒真"的判据。

它查五类（全部走 **AST**，不做文本匹配 —— 文本匹配在本会话里已经误报过四次）：
  A. `or True` / `and False`：布尔吸收式 ⇒ 整条表达式恒真/恒假；
  B. `chk(...)` / `assertX(...)` 的判据是**字面常量**（`True` / `1` / `"x"` / `1 == 1`）；
  C. `if False:` / `while False:`（永不执行的块）；
  D. `try: … except …: pass` 里**只包含判据调用** ⇒ 判据抛异常被吞（等于不判）；
  E. `assert` 后的常量表达式。

用法：
  python tools/codex-scripts/audit-dead-judgments.py [--root <目录> ...] [--json]
退出码：0 = 没找到恒真判据；1 = 找到了（逐条列 file:line）。
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "gbt_allinone").is_dir())
DEFAULT_ROOTS = ["tools/codex-scripts", "gbt_allinone"]

# 判据调用名 → **判据在第几个位置参数**。
# 🔴 这张表**逐个读过真签名**，不猜：
#     `def chk(name, ok, detail)`      ⇒ 判据在第 2 个（下标 1）
#     `def expect(cond, msg)`          ⇒ 判据在第 1 个（下标 0）
#   首跑我按"猜"把 `expect` 也当成"第 2 个是判据" ⇒ 于是把**消息字符串**当判据，
#   一口气刷出 1400+ 条假阳性（`expect(x == y, "说明")` 全被报成"判据是常量"）。
#   ⇒ 规矩：**没读过签名的名字，一律不判**（宁可漏，不许拿 msg 当判据）。
COND_ARG = {"chk": 1, "check": 1, "verify": 1, "expect": 0}
# 逐字比较类：判据是**两个操作数之间的关系** ⇒ 只有"两边都是常量"才可能恒真/恒假。
#   ⚠️ 首跑把 `assertIn` 归进"第 1 个参数是判据" ⇒ `assertIn("x", 计算出来的文本)` 全被误报
#      （`"x"` 是常量没错，但判据是"在不在里面"，能红）。⇒ 按签名分类，不按名字猜。
REL_NAMES = {"assertEqual", "assertNotEqual", "assertIn", "assertLess", "assertGreaterEqual"}
SINGLE_ARG_NAMES = {"assertTrue", "assertFalse", "assertIsNotNone"}
CHK_NAMES = set(COND_ARG) | REL_NAMES | SINGLE_ARG_NAMES
SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".scratch", "archive", "dist",
             # 下面三个是**第三方 vendored 代码**（pytest / cffi / comtypes / bitarray…），
             # 不是本仓判据 —— 首跑没排它们，1780 条命中里绝大多数是它们贡献的。
             ".pylibs", "vendor", "_upstream",
             # `store/` 是**运行态产物**（账本 / 版本快照），不是源码；且里面有不可读件
             # （实测 `store/pipeline/production/.versions/run.py` PermissionError）。
             # **跳过要可见** —— 报告里把跳过名单与不可读文件都列出来，不许静默略过。
             "store"}


def _is_const_bool(node) -> bool:
    """这个表达式是不是**字面常量**（与输入无关）？"""
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.List, ast.Tuple, ast.Set, ast.Dict)):
        return all(_is_const_bool(e) for e in ast.iter_child_nodes(node))
    if isinstance(node, ast.Compare) and len(node.ops) == 1:
        l, r = node.left, node.comparators[0]
        if _is_const_bool(l) and _is_const_bool(r):
            return True
    return False


# 逐条读过、**不是"恒真判据"**的三处（照 `false_report_audit.KNOWN_LEGIT` 的先例：
# 豁免要**带理由、可见**，不是静默放过）。键 = (文件, 行号, 规则)。
KNOWN = {
    ("tools/codex-scripts/pack-receipt.py", 98, "B/判据是常量"):
        "**记录失败用的惯用法**：`chk(name, False, 为什么)` —— 这一条**就是要报红**"
        "（包不在盘上），不是恒真。它判的是『这一格该红』，不是『条件成立』。",
    ("tools/codex-scripts/pack-receipt.py", 130, "B/判据是常量"):
        "同上：读不动窗口注册表时**主动记红**的惯用法。",
    ("tools/codex-scripts/mock-vllm-endpoint.py", 161, "A/and False"):
        "**假端点**报告里的**故意死分支**（`… if False else '见 selftest'`）—— 用来避免真发那记 404 请求。"
        "属 mock 的写法，不是判据。",
    # ── 下面两条 2026-09-25 已修（保留记录，说明"曾经是已知弱项、现在不是了"）──
    #   `merge-4k-rig.py:40` 的 `or True` → 删掉被中和的合取项（行为不变），并把"那条校验没实现"写进注释
    #   `scan_engine.py:380` 的 `if name_traps or True:` → 去条件、保留无条件块（行为不变）
}


def scan_file(path: Path) -> tuple:
    """返回 (hits, unreadable)。**读不到不算"干净"** —— 记下来、如实报。"""
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return [], "%s: %s" % (str(path.relative_to(ROOT)).replace("\\", "/"),
                               type(e).__name__)
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [], "%s: SyntaxError line %s" % (
            str(path.relative_to(ROOT)).replace("\\", "/"), e.lineno)
    hits = []
    # 路径可能**不在仓内**（用例会喂临时目录的合成样本）⇒ 相对化失败就退成绝对路径，
    # 别让"打印文件名"这种小事把整条判据弄崩（首跑就是这么崩的）。
    try:
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        rel = str(path).replace("\\", "/")

    def add(node, rule, why):
        hits.append({"file": rel, "line": getattr(node, "lineno", 0), "rule": rule, "why": why})

    for node in ast.walk(tree):
        # A. or True / and False
        if isinstance(node, ast.BoolOp):
            for v in node.values:
                if isinstance(v, ast.Constant):
                    if isinstance(node.op, ast.Or) and v.value is True:
                        add(node, "A/or True", "布尔吸收：整条恒真")
                    elif isinstance(node.op, ast.And) and v.value is False:
                        add(node, "A/and False", "布尔吸收：整条恒假")
        # B/E. 判据是字面常量
        #   ⚠️ 首跑这一条太粗：`assertEqual("a","a")` 这种**纯函数期望值**是正当写法，
        #      而我把"参数里有常量"一律报成恒真 ⇒ 噪音淹掉真信号。
        #      ⇒ 收紧成**可证明恒真**的三种：chk 的 cond 是常量 · assertTrue 的参是常量 ·
        #        assertEqual 两边都是常量**且相等**（不等是恒假，另标）。
        if isinstance(node, ast.Call):
            fname = ""
            _is_attr = False
            if isinstance(node.func, ast.Name):
                fname = node.func.id
            elif isinstance(node.func, ast.Attribute):
                fname = node.func.attr
                _is_attr = True
            # 🔴 第五类假阳性（跑真数据才发现）：`ep.check({}, {}, …)` 里的 `check`
            #    是**那个能力位自己的函数**，不是测试助手 —— 我按 `attr` 取值就把它当判据助手了。
            #    ⇒ 规矩：`chk/check/verify/expect` 这些**本地助手**只认**裸名字调用**；
            #      `self.assertEqual(...)` 这类 unittest 断言才允许带点。
            if _is_attr and not fname.startswith("assert"):
                fname = ""
            if fname in COND_ARG and len(node.args) > COND_ARG[fname]:
                if _is_const_bool(node.args[COND_ARG[fname]]):
                    add(node, "B/判据是常量",
                        "%s() 的第 %d 个位置参数（判据）是字面常量 ⇒ 与输入无关"
                        % (fname, COND_ARG[fname] + 1))
            elif fname in SINGLE_ARG_NAMES and node.args:
                if _is_const_bool(node.args[0]):
                    add(node, "B/判据是常量", "%s() 的判据是字面常量" % fname)
            elif fname in REL_NAMES and len(node.args) >= 2:
                a0, a1 = node.args[0], node.args[1]
                if _is_const_bool(a0) and _is_const_bool(a1):
                    try:
                        same = ast.literal_eval(a0) == ast.literal_eval(a1)
                    except Exception:                            # noqa: BLE001
                        same = False
                    add(node, "B/常量相比",
                        "%s 两边都是字面常量 ⇒ 结果在写的时候就定了（%s）"
                        % (fname, "恒真" if same else "恒假/恒错"))
        if isinstance(node, ast.Assert) and _is_const_bool(node.test):
            try:
                truthy = bool(ast.literal_eval(node.test))
            except Exception:                                    # noqa: BLE001
                truthy = True
            add(node, "E/assert 常量", "assert 的条件是字面常量（%s）"
                % ("恒真" if truthy else "恒假"))
        # C. if False / while False
        if isinstance(node, (ast.If, ast.While)):
            t = node.test
            if isinstance(t, ast.Constant) and t.value is False:
                add(node, "C/永不执行", "%s False 块" % type(node).__name__.lower())
        # D. except 里吞掉判据
        if isinstance(node, ast.Try):
            for h in node.handlers:
                body = [b for b in h.body
                        if not (isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant))]
                if len(body) == 1 and isinstance(body[0], ast.Pass):
                    # 只报"try 里全是判据调用"的：那种吞了就等于不判
                    calls = [n for n in ast.walk(node) if isinstance(n, ast.Call)]
                    names = {n.func.id for n in calls
                             if isinstance(n.func, ast.Name)} | \
                            {n.func.attr for n in calls if isinstance(n.func, ast.Attribute)}
                    if names & CHK_NAMES:
                        add(node, "D/判据被吞", "try 里的判据抛异常后 pass ⇒ 等于不判")
    return hits, None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="恒真判据审计（只读）")
    ap.add_argument("--root", action="append", default=[])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    roots = a.root or DEFAULT_ROOTS
    hits, files, unread = [], 0, []
    for r in roots:
        base = ROOT / r
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.py")):
            if any(s in p.parts for s in SKIP_DIRS):
                continue
            files += 1
            h, bad = scan_file(p)
            hits += h
            if bad:
                unread.append(bad)
    exempt = [h for h in hits if (h["file"], h["line"], h["rule"]) in KNOWN]
    live = [h for h in hits if (h["file"], h["line"], h["rule"]) not in KNOWN]
    known_open = [h for h in exempt
                  if "已知弱项" in KNOWN.get((h["file"], h["line"], h["rule"]), "")]
    rep = {"ok": True, "readonly": True, "files": files, "hits": live, "count": len(live),
           "exempt": [{"file": h["file"], "line": h["line"], "rule": h["rule"],
                       "why": KNOWN[(h["file"], h["line"], h["rule"])]} for h in exempt],
           "known_open_count": len(known_open),
           "unreadable": unread, "skipped_dirs": sorted(SKIP_DIRS), "roots": roots,
           "note": ("走 AST，不做文本匹配（文本匹配在本会话误报过四次）。"
                    "A/B/C/E = **恒真或恒假**；D = 判据被 `except: pass` 吞掉。"
                    "**本器不判『这条判据该不该存在』** —— 只判『它还有没有可能红』。")}
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print("═══ 恒真判据审计 ═══")
        print("扫了 %d 个 .py（根：%s）· **待处理 %d 条** · 已登记豁免 %d 条（其中**已知弱项未修 %d 条**）"
              % (files, "、".join(roots), len(live), len(rep["exempt"]), rep["known_open_count"]))
        print("跳过的目录：%s（**跳过可见**，不静默）" % "、".join(rep["skipped_dirs"]))
        if unread:
            print("读不到/解析不了 %d 个（**不算干净**）：" % len(unread))
            for u in unread[:8]:
                print("   · %s" % u)
        for h in live:
            print("  🔴 [%s] %s:%d —— %s" % (h["rule"], h["file"], h["line"], h["why"]))
        if rep["exempt"]:
            print("  ── 已登记豁免（**带理由、可见**）──")
            for e in rep["exempt"]:
                print("  ⚪ [%s] %s:%d\n       %s" % (e["rule"], e["file"], e["line"], e["why"]))
        if not live:
            print("  ✅ 没有『还活着』的恒真/恒假判据（豁免项见上）")
        print("边界：%s" % rep["note"])
    return 1 if rep["hits"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
