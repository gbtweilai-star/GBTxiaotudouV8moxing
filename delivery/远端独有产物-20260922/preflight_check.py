"""GBT小土豆V8 · 进生产预检（preflight）。

三件工程卫生，全部只读/安全，不碰任何 AI 能力：
  1. BOM 扫描（可选清理）：检出以 UTF-8 BOM 开头的 .py，--fix 时安全去除。
  2. 全量编译校验：compileall 整个 gbt_allinone 包，语法错误第一时间暴露。
  3. 依赖就绪自检：调用 readiness.check()，如实列出缺外部后端/密钥的能力。

用法：
    python gbt_allinone/deploy/preflight_check.py           # 只检不改
    python gbt_allinone/deploy/preflight_check.py --fix     # 顺带安全清 BOM

退出码：0=全过；1=有编译错误（P0，必须修）；2=仅 BOM/就绪告警（可上线前处理）。
"""
import sys
import compileall
from pathlib import Path

_PKG = Path(__file__).resolve().parent.parent           # gbt_allinone/
_BOM = b"\xef\xbb\xbf"


def scan_bom(fix: bool = False):
    hits = []
    fixed = []
    for py in _PKG.rglob("*.py"):
        if "__pycache__" in py.parts or ".pylibs" in py.parts:
            continue
        try:
            raw = py.read_bytes()
        except Exception:
            continue
        if raw.startswith(_BOM):
            rel = str(py.relative_to(_PKG))
            hits.append(rel)
            if fix:
                py.write_bytes(raw[len(_BOM):])
                fixed.append(rel)
    return {"bom_files": hits, "fixed": fixed}


def compile_all():
    # quiet=1：只报错误；不写 __pycache__ 到源码树之外的影响忽略。
    ok = compileall.compile_dir(str(_PKG), quiet=1, force=True)
    return {"compile_ok": bool(ok)}


def readiness_check():
    try:
        sys.path.insert(0, str(_PKG.parent))
        from gbt_allinone.readiness import check
        return check()
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"{type(e).__name__}: {e}"[:200]}


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    fix = "--fix" in argv

    bom = scan_bom(fix=fix)
    comp = compile_all()
    ready = readiness_check()

    print("=== GBT-V8 进生产预检 ===")
    print(f"[BOM]  发现 {len(bom['bom_files'])} 个带 BOM 文件"
          + (f"，已清理 {len(bom['fixed'])} 个" if fix else "（--fix 可安全清理）"))
    for f in bom["bom_files"]:
        print(f"       - {f}")
    print(f"[编译] compileall: {'通过' if comp['compile_ok'] else '失败（P0 必须修）'}")
    print(f"[就绪] {ready.get('note', '')}")
    for nd in ready.get("needs_dependency", []):
        print(f"       - {nd['capability']}: 缺 {nd['missing']}")

    if not comp["compile_ok"]:
        return 1
    if bom["bom_files"] and not fix:
        return 2
    if not ready.get("ok", True):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
