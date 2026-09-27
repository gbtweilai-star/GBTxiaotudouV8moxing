#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""**开机自检**（一条命令跑完全部常设判据）—— 回答一个问题：

    「这台机器现在健康吗？下一轮会话读到的每一段字是真的吗？」

为什么要有一个总入口（一手账）：
  2026-09-25 一天里立了四条**新的**常设判据，但它们散在四个文件、四条命令里：
    · `test_cap_total_consistency`     能力的数目字不许自相矛盾
    · `test_prompt_commands_are_real`  注入的命令必须在盘上
    · `test_prompt_security_section`   安全段必须是真那道门
    · `test_awareness_guard_runs`      自我认知点名的自检必须跑得起来
    · `test_progress_ledger_contract`  台账字段契约
    · `test_injection_honesty`         注入面诚实性（收口判据）
  ⇒ **判据散着 = 没人跑**（本仓原话：「判据立了不等于门关上了」）。
  这个总入口把它们连同两道闸（装机副本漂移 / 重启验收单）收成**一次执行、一个退出码**。

口径（三条，与全仓一致）：
  1. **判据只有一份**：这里不重写任何判据，只**调**已有的 unittest 模块与既有脚本 ——
     复制一份出来就会慢慢长歪。
  2. **失败不许吞**：任何一段跑不动都算**红**（不许记成"跳过"），并如实打出来。
  3. **测试在隔离 store 里跑**：进程启动前就设 `GBT_STORE_DIR`，
     免得不小心绑到生产 store（仓里有守卫，会直接拒跑）。

用法：
  python tools/codex-scripts/boot-selfcheck.py            # 人读
  python tools/codex-scripts/boot-selfcheck.py --json     # 机读
  python tools/codex-scripts/boot-selfcheck.py --quick    # 跳过重启验收单（它要起网络请求）
退出码：0 = 全绿；1 = 有红（逐条列出"哪一段、现在是什么、该怎么办"）。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# 判据组：**只点名，不复制**。每个都必须是 `gbt_allinone.tests.<名>`
JUDGMENTS = [
    ("能力总数一致", "gbt_allinone.tests.test_cap_total_consistency"),
    ("注入命令为真", "gbt_allinone.tests.test_prompt_commands_are_real"),
    ("安全段是真门", "gbt_allinone.tests.test_prompt_security_section"),
    ("自检命令可跑", "gbt_allinone.tests.test_awareness_guard_runs"),
    ("台账字段契约", "gbt_allinone.tests.test_progress_ledger_contract"),
    ("注入面诚实性", "gbt_allinone.tests.test_injection_honesty"),
    ("没有恒真判据", "gbt_allinone.tests.test_dead_judgments"),
    # 2026-09-27 加（主人令「启动的时候触手就是你的手」）：接线三判据 ——
    # ①登记↔分派 ②触手账断连=0 ③外部工作流插件三节点一个不差。
    # 起因：filmkit 曾"登记了没接线"，靠人扫出来；这条判据把它钉死成启动红。
    ("接线全连通", "gbt_allinone.tests.test_wiring_all_tentacles"),
    # 2026-09-27 加（主人令「源代码保护好、整理摆放好，别分路分叉」）：**源 ↔ 装 逐字节对账**。
    # 起因：技能有两个真身 —— 仓内 skills/ 是**源**，~/.agents/skills/ 是
    # **运行时真正读的那份**，而两者之间**从来没有任何工具对账**（全仓 grep 零命中）。
    # 实测：gbt-security 源 43K / 装 31K、差 1054 行 ⇒ 一整轮能力覆盖补丁只落在源上，
    # 运行时一个字节都没看见 —— 与 F18（「盘上对」被念成「生效了」）同型。
    # 2026-09-27 加（主人令「其他工具全部都要可控按键一个不漏的绑定好」）：**可控制面完整性**——
    # 每个装了的工具都必须有"它自己报出来的"可控制键清单（ffmpeg 628 · git 177 · python 302 ·
    # genoffice 19 · freebuff 3 · blender 2409 bpy 算子），且**消失的键必须为空**（断连报警）。
    ("可控制面一个不漏", "gbt_allinone.tests.test_surface_bind"),
    ("技能源装不分叉", "gbt_allinone.tests.test_skills_install_sync"),
    # 2026-09-27 加（主人令「扫描和视觉的钩子全方位无死角覆盖…要不然扫来扫去都是故障」）：
    # 覆盖矩阵是**那一刻**的读数；这条判据守三件事：读数全绿 · 不过期 ·
    # **盘上顶层树数量与读数一致**（多一个目录 = 新增盲区，读数却看着全绿 —— 那正是"死角"）。
    ("覆盖无死角且新鲜", "gbt_allinone.tests.test_coverage_readings_fresh"),
    # 2026-09-27 加（主人令「新增能力全部都要与触手双向绑定…没实现却都没记录…随时都能感知到
    # 框架的所有状态」）：把那条规矩拆成可机检的四件事 —— 能力位三处齐 · 双向绑定 · 缺口必须
    # 有名有姓（state/unimplemented.json）· 六个面都读得出来。红了两条路：补接线，或登记缺口。
    ("新增能力双向绑定", "gbt_allinone.tests.test_cap_bind_bidirectional"),
    # 2026-09-25 加：云端那 4 批改动（令牌闸 / 作用面读数 / 拍平块数组 / 错误分档）
    # 因为**没部署**，云端一次都没跑过。本机离线验它，0.3 秒，不出一字节网。
    ("云端点闸行为", "gbt_allinone.tests.test_endpoint_gate"),
    # 2026-09-25 加：凭据红线（密钥不许明文落盘 · 没有密钥必须拒绝启动子进程）。
    # 起因是真出过事：config/mcporter.json 里被人直接写了一条明文 API key。
    ("密钥不许明文落盘", "gbt_allinone.tests.test_key_vault_autoread"),
    # 2026-09-25 加：**部署前接线对账**。deploy/cloud-10 是生产落点，而这个网一次都没部署过 ⇒
    # 任何"配置与代码对不上"都要等真部署那一刻才以 undefined 炸出来（那时已经在改远端了）。
    # 首跑就抓到两个真缺口（SANDBOX / AE：代码在读、配置里连名字都没出现过）。
    ("部署前接线对账", "gbt_allinone.tests.test_cloud_config_wiring"),
    # 2026-09-25 加：**未清故障的前提还成立吗**。第 37 轮发现 F1/F6 两条高危故障的
    # 前提（"4 批没部署"）早就不成立、却在账里挂了十几轮 ⇒ 故障清单会**无声腐烂**。
    # 这条判据让"前提垮了"在开机时就红，逼人回去改账，而不是让它继续挂着。
    ("未清故障前提复核", "gbt_allinone.tests.test_reverify_open_faults"),
    # 2026-09-25 加：**部署漂移对账的牙齿**（离线自检；联网那一侧不进判据 —— 判据不该依赖外网）。
    # 一个"比出来没差异"的对账器，很可能是因为它其实什么都没比 ⇒ 种五处差异看它逮不逮得住。
    ("部署漂移尺子有牙", "gbt_allinone.tests.test_cloud_deploy_drift"),
    # 2026-09-25 加：**密钥两份存量的对账**。主人令「密钥全部部署…可以自动读取」之后，
    # 密钥有了两份（User 作用域注册表 + DPAPI 保险箱）⇒ 两份就是两个真相源，轮换只改一处
    # 另一处就静默过期。**不是假想**：首跑就读出 `agnes` 已经分叉（库 sk-HX**** vs 注册表 sk-Oy****）。
    # 判据只判分类逻辑与读数自洽（**不判"必须无分叉"** —— 哪份是新的只有主人能定）。
    ("密钥两份存量对账", "gbt_allinone.tests.test_key_consistency"),
    # 2026-09-25 加：**cross_scan 的 V 维（视图对账）**。它此前只出现在维度声明里
    # （声称 10 维、实际 6 维能产出发现）；本轮真做出来，判据是**加减法要闭合**
    # （家根总项 == 六类之和），而不是只读一个数字。
    # 🔴 最要紧的是安全红线：`inventory.scan(fix=True)` 会**真删文件** ——
    #    用例用桩记录 kwargs，直接断言扫描器传的是 `fix=False`（「扫一下」不该改动任何东西）。
    ("视图对账且只读", "gbt_allinone.tests.test_cross_scan_v_dim"),
    # 2026-09-25 加：**满仓横扫的负载闸**。两次实跑证明：内存被压满时满仓横扫会出**假红**
    # （`FileNotFoundError [WinError 2]` 收集期就断 / 26 分钟跑不完），而假红会被当成"代码坏了"。
    # 这条判据守那道闸本身：低于阈值不许开跑 · 边界含等号 · 读不到要如实标注 · 闸必须在跑之前。
    ("横扫负载闸", "gbt_allinone.tests.test_run_all_tests_memory_guard"),
    # 2026-09-26 加（第 52 轮 · F17）：**提交前凭据自审这份工具本身**。
    # 起因是现读出来的：那份"强制"自审只存在于 `%TEMP%`（重启即无），
    # 而它的①号判据要读 `%TEMP%` 里一份**明文**密钥备份 ——
    # **防明文落盘的工具自己依赖一份明文落盘**，而上面那条「密钥不许明文落盘」却是绿的
    # （尺子只量了仓这半个屋子）。这条判据把工具钉在仓里、把①钉在保险箱上（不碰明文参照），
    # 并守住退出码契约：0 干净 / 1 命中 / 2 **自审没跑成**（含"保险箱是空的 ⇒ 一条都没比"）。
    ("凭据自审有牙且在仓里", "gbt_allinone.tests.test_precommit_secret_scan"),
    # 2026-09-26 加（第 53 轮 · F18）：**"盘上对"不等于"进了进程"**。
    # 起因是现读出来的：台账块 2026-09-25 21:03:15 加进宿主半边时**没动版本号**，
    # 而宿主代码只在进程启动时装载（进程起于 10:33:32）⇒ 进程里压根没有那块，
    # 主人要的「重启之后自动读取」一直没生效；可所有闸全绿 ——
    # **因为它们全都从盘上渲染，没有一条问过进程**。
    # 这条判据守的就是那条"问进程"的路：宿主自报 `contexts` · 验收单 ⑨ 比对 ·
    # 且两边名单**同源**（加了块没人验、或验了不存在的块，都要红）。
    ("上下文真的进了进程", "gbt_allinone.tests.test_live_context_wiring"),
    # 2026-09-26 加（第 55 轮）：**分批跑的覆盖必须现算并集**。
    # 第 51 轮我把全仓拆四批跑，然后把四批的数字并排一放就说全仓看过了 ——
    # 而批与批之间我还在加测试文件（124 → 125 → 126），**四批的「全 N 个」不是同一个 N**。
    # 那一轮真实覆盖是 62/125。这条判据守：缺文件必须红 · 跨批红必须并起来 ·
    # 说不出用例名的红也不许吞（写「未记到用例名」）· 超时不算红。
    ("满仓覆盖按并集现算", "gbt_allinone.tests.test_sweep_union_coverage"),
]

DRIFT_GATE = ROOT / "plugins" / "gbt-master" / "tools" / "verify-installed-copy.mjs"
SHEET = ROOT / "plugins" / "gbt-master" / "tools" / "verify-after-restart.py"


def _env(store: str) -> dict:
    e = dict(os.environ)
    e["GBT_STORE_DIR"] = store
    e["PYTHONIOENCODING"] = "utf-8"
    # 🔴 2026-09-26 自纠：环境里残留的 PYTHONPATH 会把注入面测成假红
    #    （run-all-tests.py 里的一手实录）。这里跑的是同一批 unittest 模块，
    #    却没做同样的环境清洁 —— 现在补上，同一条判据同一条规矩。
    e.pop("PYTHONPATH", None)
    return e


def _run(cmd: list, env: dict, timeout: int = 600) -> tuple:
    try:
        p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, env=env)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "timeout>%ss" % timeout
    except Exception as e:                                       # noqa: BLE001
        return 125, "%s: %s" % (type(e).__name__, str(e)[:160])


def selfcheck(quick: bool = False) -> dict:
    # 🔴 2026-09-26 自纠：原来用固定共享路径 %TEMP%/gbt_boot_selfcheck_store ——
    #    两次自检并发会共享同一 store（读数互相污染），且跨次运行累积不清理，
    #    "隔离 store"只隔离了生产，没隔离上一次自己。现在每检一次一间新屋。
    store = tempfile.mkdtemp(prefix="gbt_boot_selfcheck_store_")
    env = _env(store)
    steps = []

    for label, mod in JUDGMENTS:
        rc, out = _run([sys.executable, "-m", "unittest", mod], env, timeout=300)
        tail = [l for l in out.splitlines() if l.startswith(("OK", "FAILED", "Ran "))][-2:]
        steps.append({
            "step": "判据/" + label, "cmd": "python -m unittest %s" % mod,
            "ok": rc == 0, "rc": rc, "now": " · ".join(tail[-2:]) or out.strip()[-160:],
        })

    if DRIFT_GATE.is_file():
        rc, out = _run(["node", str(DRIFT_GATE)], env, timeout=180)
        steps.append({"step": "闸/装机副本漂移", "cmd": "node plugins/gbt-master/tools/verify-installed-copy.mjs",
                      "ok": rc == 0, "rc": rc,
                      "now": ("逐字节一致" if rc == 0 else (out.strip().splitlines() or ["?"])[0][:160])})
    else:
        steps.append({"step": "闸/装机副本漂移", "cmd": str(DRIFT_GATE), "ok": False, "rc": 127,
                      "now": "漂移闸不在盘上 —— 不许当跳过"})

    if quick:
        steps.append({"step": "闸/重启验收单", "cmd": "（--quick 跳过）", "ok": True, "rc": 0,
                      "now": "本次被 --quick 显式跳过（不是通过）"})
    elif SHEET.is_file():
        rc, out = _run([sys.executable, str(SHEET)], env, timeout=300)
        # 🔴 2026-09-25 自纠：原来这里写死 `"还有 1 项没到位" in out and "⑤" in out` ——
        #    两个毛病：① 验收单**多一条可选待办就整条判红**；② 读数只印"还有 N 项"、
        #    **不印是哪几项**，于是 20:51 那次读到"还有 2 项"，我连第二个是谁都说不出来。
        #    现在改成：把 ⏳ 那几项**逐名读出来**，容差按**点名白名单**（⑤ 是"重启后才允许清"，
        #    其余任何一项没到位都算红）。读数必须能回答"现在是什么"。
        pending = [l.strip().lstrip("⏳").strip()
                   for l in out.splitlines() if l.strip().startswith("⏳")]
        OPTIONAL_PENDING = ("⑤",)          # 只允许这一项缺（它按 README §4.8 是重启后才清）
        ok = all(p.startswith(OPTIONAL_PENDING) for p in pending) if pending else True
        _concl = [l.strip() for l in out.splitlines() if l.strip().startswith("结论")]
        now = (_concl[0][:120] if _concl else out.strip()[-160:])
        if pending:
            now += " · 待到位=%s" % "、".join(pending)
        # 🔴 2026-09-26 自纠：原来这里 `rc == 0 or ok` —— 验收单崩溃/超时（rc=124/125）时
        #    输出里没有 ⏳ 行 ⇒ pending=[] ⇒ ok=True ⇒ (False or True) 被报成 ✅，
        #    违反本文件自己的口径"任何一段跑不动都算红"。改为 **and**：跑不成就是红。
        steps.append({"step": "闸/重启验收单", "cmd": "python plugins/gbt-master/tools/verify-after-restart.py",
                      "ok": (rc == 0 and ok), "rc": rc, "now": now})
    else:
        steps.append({"step": "闸/重启验收单", "cmd": str(SHEET), "ok": False, "rc": 127,
                      "now": "验收单不在盘上 —— 不许当跳过"})

    bad = [s for s in steps if not s["ok"]]
    return {
        "ok": not bad, "readonly": True, "steps": steps, "red_count": len(bad),
        "store": store,
        "note": ("只调既有判据与既有脚本，**不重写第二份**；任何一段跑不动都算红，"
                 "不许记成跳过。测试在隔离 store 里跑（进程启动前设好 GBT_STORE_DIR）。"),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="开机自检（只读）")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quick", action="store_true", help="跳过重启验收单")
    a = ap.parse_args(argv)
    rep = selfcheck(quick=a.quick)
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print("═══ 开机自检 · %s ═══" % ROOT)
        for s in rep["steps"]:
            print("  %s %-18s %s" % ("✅" if s["ok"] else "🔴", s["step"], s["now"][:110]))
        print("-" * 78)
        print("结论：%s（红 %d 条）" % ("全绿" if rep["ok"] else "有红", rep["red_count"]))
        if rep["red_count"]:
            for s in rep["steps"]:
                if not s["ok"]:
                    print("  🔴 %s —— 怎么办：%s" % (s["step"], s["cmd"]))
        print("边界：%s" % rep["note"])
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
