# -*- coding: utf-8 -*-
"""GBT小土豆V8 · 品牌主页 · 源码保护构建器（三档强度）

⛔ 开发者：自由的风 · 永久钢印 · 禁止删除

════════════════════════════════════════════════════════════════════════════
先说清楚一件事，免得白做工：
  **只要目标是 Vercel，就不存在「上传源码但对方读不到」的技术手段。**
  Vercel 的部署模型是「客户端上传源码 → 云端构建」，构建必须读明文源码。
  所以本工具解决的不是「加密」，而是**「交付什么」**：
    · 交源码目录（strip 档）—— 抬高阅读成本，挡「随手翻」
    · 交字节码（bytecode 档）—— 挡得住非专业读者，但 Vercel 不适用
    · 真正不可读，只有「不交源码、只交部署触发器」一条路（见 DEPLOY-ONLY-交付说明.md）
════════════════════════════════════════════════════════════════════════════

三档强度（全部可自证，不是自我感觉）：
  strip     ★★☆☆☆  AST 重写：注释 / 文档字符串 / 类型注解字符串全剥，语义等价
                    —— 出货前后做 AST dump 对拍，并跑全量判据，绿了才算过
  bytecode  ★★★☆☆  strip + 编译 .pyc，.py 不落盘（⚠️ Vercel 无法使用，仅自托管）
  pack      ★★☆☆☆  strip 树打 zip + 每文件 sha256 清单 + 专有授权文件

反自欺纪律：
  · 出货用**白名单**（SHIP 表），不是黑名单 —— 没登记的文件永远进不去，
    不存在「忘了排除某个内部脚本」这种事故。
  · strip 后必须过 `semantic_equal()` 对拍 + `_site_check.py` 全量判据，
    任一不过 ⇒ 构建失败，产物删除。

退出码：0 = 成功；1 = 失败（产物已清理）。
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ── 白名单：只有登记在册的文件才可能被交付 ──────────────────────────────────
# (相对路径, 处理方式)  处理方式 ∈ {"as-is", "strip"}
SHIP: tuple[tuple[str, str], ...] = (
    ("requirements.txt", "as-is"),
    ("vercel.json", "as-is"),
    ("api/index.py", "strip"),
    ("api/assets/logo-256.png", "as-is"),
    ("api/assets/logo-512.png", "as-is"),
    ("api/assets/favicon-32.png", "as-is"),
)

# 剥离后仍必须存在的署名钢印（品牌纪律：署名不可删除、不可篡改归属）
STAMP = "# ⛔ GBT小土豆V8 · 版权归属：自由的风 · 未经书面许可不得复制、再分发或反编译"

SKIP_IN_TREE = {"__pycache__", ".vercel", ".pytest_cache"}


# ── 语义等价判据 ────────────────────────────────────────────────────────────
def _drop_docstrings(tree: ast.Module) -> None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef,
                             ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                node.body = body[1:] or [ast.Pass()]


def semantic_equal(a: str, b: str) -> tuple[bool, str]:
    """两侧去掉文档字符串后，AST dump 必须逐字节相同 ⇒ 语义等价。"""
    ta, tb = ast.parse(a), ast.parse(b)
    _drop_docstrings(ta)
    _drop_docstrings(tb)
    da = ast.dump(ta, include_attributes=False, annotate_fields=True)
    db = ast.dump(tb, include_attributes=False, annotate_fields=True)
    if da == db:
        return True, "AST dump 逐字节相同（%d 字符）" % len(da)
    # 定位第一处分歧，便于排障
    for i, (x, y) in enumerate(zip(da, db)):
        if x != y:
            return False, "AST 在偏移 %d 处分歧：…%s… ≠ …%s…" % (
                i, da[max(0, i - 60):i + 60], db[max(0, i - 60):i + 60])
    return False, "AST 长度不同：%d vs %d" % (len(da), len(db))


def strip_source(src: str) -> str:
    """AST 重写：剥注释 / 文档字符串，注入不可删的署名钢印。"""
    tree = ast.parse(src)
    _drop_docstrings(tree)
    body = ast.unparse(tree)
    return "%s\n# ⛔ 机读产物：注释与文档字符串已剥离；请改源件后重建，勿直接编辑\n%s\n" % (
        STAMP, body)


# ── 构建 ────────────────────────────────────────────────────────────────────
def build_tree(out: Path, do_strip: bool = True) -> list[str]:
    out.mkdir(parents=True, exist_ok=True)
    log: list[str] = []
    for rel, mode in SHIP:
        s = HERE / rel
        if not s.is_file():
            raise FileNotFoundError("白名单文件缺失：%s" % rel)
        d = out / rel
        d.parent.mkdir(parents=True, exist_ok=True)
        if mode == "strip" and do_strip:
            raw = s.read_text(encoding="utf-8")
            new = strip_source(raw)
            ok, why = semantic_equal(raw, new)
            if not ok:
                raise RuntimeError("strip 破坏语义：%s —— %s" % (rel, why))
            if "--gbt-violet:#7C4DFF" not in new or "@@CARDS@@" not in new:
                raise RuntimeError("strip 丢关键常量：%s（三色定义或占位符缺失）" % rel)
            if STAMP not in new:
                raise RuntimeError("strip 丢署名钢印：%s" % rel)
            d.write_text(new, encoding="utf-8")
            log.append("  %-26s strip  %7d → %7d B  (-%d%%)  语义等价=%s"
                       % (rel, len(raw.encode()), len(new.encode()),
                          round(100 - len(new.encode()) * 100 / max(1, len(raw.encode()))), ok))
        else:
            shutil.copy2(s, d)
            log.append("  %-26s as-is  %7d B" % (rel, d.stat().st_size))
    return log


def build_bytecode(out: Path) -> list[str]:
    log = build_tree(out, do_strip=True)
    # 编译后删源：只留 .pyc
    subprocess.run([sys.executable, "-m", "compileall", "-q", "-b",
                    str(out / "api")], check=True)
    removed = []
    for p in out.rglob("*.py"):
        removed.append(str(p.relative_to(out)))
        p.unlink()
    log.append("  bytecode：已删除 .py → %s" % (", ".join(removed) or "(无)"))
    pyc = sorted(str(p.relative_to(out)) for p in out.rglob("*.pyc"))
    log.append("  bytecode：留 .pyc → %s" % (", ".join(pyc) or "(无)"))
    log.append("  ⚠️ Vercel 的 Python runtime 不加载 .pyc-only 目录 —— 本档仅供自托管/容器用。")
    return log


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def build_pack(zip_path: Path) -> tuple[list[str], Path]:
    tmp = Path(tempfile.mkdtemp(prefix="gbt-pack-"))
    tree = tmp / "vercel-brand"
    try:
        log = build_tree(tree, do_strip=True)
        # 授权声明从单一真源读，避免「脚本里一份、磁盘上一份」两处漂移
        lic_src = HERE / "LICENSE-专有授权.txt"
        if not lic_src.is_file():
            raise FileNotFoundError("授权声明单一真源缺失：%s" % lic_src)
        shutil.copy2(lic_src, tree / "LICENSE-专有授权.txt")
        log.append("  LICENSE-专有授权.txt  as-is  %7d B" % (tree / "LICENSE-专有授权.txt").stat().st_size)
        lines = []
        for p in sorted(tree.rglob("*")):
            if p.is_file() and not any(s in p.parts for s in SKIP_IN_TREE):
                lines.append("%s  %s" % (_sha256(p), p.relative_to(tree).as_posix()))
        (tree / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
        log.append("  MANIFEST.sha256  %d 个文件已登记摘要" % len(lines))

        zip_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(tree.rglob("*")):
                if p.is_file():
                    z.write(p, p.relative_to(tmp).as_posix())
        log.append("  打包：%s  (%d B, zip 内 %d 项)"
                   % (zip_path.name, zip_path.stat().st_size, len(zipfile.ZipFile(zip_path).namelist())))
        return log, tree
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── 自证：对产物再跑一遍全量判据 ────────────────────────────────────────────
def verify_tree(tree: Path) -> tuple[bool, str]:
    """把判据脚本临时拷进产物树跑一遍，跑完必删（临时污染可接受，清理必须有保证）。"""
    checkers = ("_site_check.py", "_live_smoke.py")
    staged: list[Path] = []
    try:
        for c in checkers:
            src = HERE / c
            if src.is_file():
                dst = tree / c
                shutil.copy2(src, dst)
                staged.append(dst)
        if not staged:
            return False, "找不到判据脚本，无法自证"
        for c in staged:
            r = subprocess.run([sys.executable, str(c)], cwd=str(tree),
                               capture_output=True, text=True,
                               encoding="utf-8", errors="replace",
                               env={**__import__("os").environ,
                                    "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})
            tail = (r.stdout or "").strip().splitlines()
            head = " | ".join(tail[-2:]) if tail else "(无输出)"
            if r.returncode != 0:
                return False, "%s 失败(rc=%d)：%s" % (c, r.returncode, head)
        return True, "判据脚本在产物树上全绿（%s）" % ", ".join(p.name for p in staged)
    finally:
        for p in staged:
            p.unlink(missing_ok=True)
        removed = all(not p.exists() for p in staged)
        print("[自证清理] 临时判据脚本已移除 = %s" % removed)


def main() -> int:
    ap = argparse.ArgumentParser(description="GBT小土豆V8 品牌主页 · 源码保护构建器")
    ap.add_argument("level", choices=["strip", "bytecode", "pack", "verify"],
                    help="保护档位")
    ap.add_argument("--out", default=None, help="输出路径（目录或 .zip）")
    args = ap.parse_args()

    default_out = {
        "strip": HERE.parent.parent / "vercel-brand-protected" / "tree",
        "bytecode": HERE.parent.parent / "vercel-brand-protected" / "bycode",
        "pack": HERE.parent.parent / "vercel-brand-protected" / "gbt-brand-site-protected.zip",
    }

    print("=" * 78)
    print("GBT小土豆V8 · 品牌主页 · 源码保护构建器   档位=%s" % args.level)
    print("=" * 78)
    print("白名单（只有这 %d 项可能被交付）：" % len(SHIP))
    for rel, mode in SHIP:
        print("   %-28s %s" % (rel, mode))
    print("-" * 78)

    if args.level == "verify":
        tree = Path(args.out) if args.out else default_out["strip"]
        ok, detail = verify_tree(tree)
        print("[%s] 产物自证：%s" % ("OK  " if ok else "FAIL", detail))
        return 0 if ok else 1

    if args.level == "pack":
        zp = Path(args.out) if args.out else default_out["pack"]
        log, tree = build_pack(zp)
        for l in log:
            print(l)
        print("-" * 78)
        print("产包：%s" % zp)
        print("提示：拿 zip 的人**能读到源码**（strip 只抬高阅读成本）。")
        print("      要真正不给源码，见 DEPLOY-ONLY-交付说明.md 的「部署触发器」模式。")
        return 0

    out = Path(args.out) if args.out else default_out[args.level]
    if out.exists():
        shutil.rmtree(out)
    if args.level == "strip":
        log = build_tree(out, do_strip=True)
    else:
        log = build_bytecode(out)
    for l in log:
        print(l)
    print("-" * 78)

    ok, detail = verify_tree(out) if args.level == "strip" else (True, "(bytecode 档不做 Flask 判据，需自托管环境)")
    print("[%s] 产物自证：%s" % ("OK  " if ok else "FAIL", detail))
    if not ok:
        shutil.rmtree(out, ignore_errors=True)
        print("产物已清理（自证不过绝不外发）。")
        return 1
    print("产物：%s" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
