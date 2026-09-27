# -*- coding: utf-8 -*-
"""GBT小土豆V8 · 品牌主页 · 部署触发器（交付给运维方使用）

⛔ 开发者：自由的风 · 永久钢印 · 禁止删除

════════════════════════════════════════════════════════════════════════════
这个脚本的设计前提是**接收方拿不到源码**。
它只做一件事：向 Vercel 的 Deploy Hook 发一个 POST，让云端去拉取并构建。
源码始终在授权方自己的仓库里，从未离开。

与之配套的纪律（缺一条这个模式就漏）：
  · hook 地址只写在接收方的本地文件或环境变量里，**不写进脚本、不进版本库**；
  · 脚本打印时一律脱敏，日志里不出现完整 hook；
  · 本地限流，防止脚本被套进循环把配额烧穿；
  · 每次触发写一条本地审计记录；
  · hook 一旦疑似泄露，立即在 Vercel 后台 regenerate —— 旧地址即刻失效。
════════════════════════════════════════════════════════════════════════════

用法：
  export GBT_DEPLOY_HOOK='https://api.vercel.com/v1/integrations/deploy/prj_xxx/yyy'
  python deploy-trigger.py --check           # 只校验配置，不发请求
  python deploy-trigger.py --go              # 真触发
  python deploy-trigger.py --go --wait       # 触发并轮询到构建结束

退出码：0 = 成功；1 = 配置/请求失败；2 = 被本地限流挡住。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOOK_FILE = HERE / ".gbt-deploy-hook"          # 0600，不入版本库
AUDIT_LOG = HERE / ".gbt-deploy-audit.jsonl"
MIN_INTERVAL_S = 60                            # 本地限流：两次触发至少间隔 60s

HOOK_PATTERN = re.compile(
    r"^https://api\.vercel\.com/v1/integrations/deploy/prj_[A-Za-z0-9]+/[A-Za-z0-9]+$")


def _mask(url: str) -> str:
    """日志与终端一律只看得到脱敏形态。"""
    m = HOOK_PATTERN.match(url)
    if not m:
        return "<非法或未知形态>"
    head = url.rsplit("/", 2)[0]
    tail = url.rsplit("/", 1)[1]
    return "%s/…%s（共 %d 字符）" % (head, tail[-4:], len(url))


def load_hook() -> str:
    """优先级：环境变量 > 本地 0600 文件。不硬编码，不猜。"""
    url = (os.environ.get("GBT_DEPLOY_HOOK") or "").strip()
    src = "环境变量 GBT_DEPLOY_HOOK"
    if not url and HOOK_FILE.is_file():
        url = HOOK_FILE.read_text(encoding="utf-8").strip()
        src = str(HOOK_FILE)
    return url, src


def audit(rec: dict) -> None:
    rec["at"] = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    with AUDIT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def last_trigger_ts() -> float:
    if not AUDIT_LOG.is_file():
        return 0.0
    ts = 0.0
    for line in AUDIT_LOG.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("event") == "trigger" and r.get("ok"):
            try:
                ts = max(ts, _dt.datetime.fromisoformat(r["at"]).timestamp())
            except Exception:
                pass
    return ts


def post_hook(url: str) -> tuple[bool, str]:
    """POST 到 Deploy Hook。不走任何代理环境变量，直连。"""
    req = urllib.request.Request(url, method="POST", data=b"",
                                 headers={"Content-Length": "0",
                                          "User-Agent": "GBT-XiaoTuDou-V8/deploy-trigger"})
    # 显式安装「空代理表」的 opener：让默认读环境变量的那个不被装上，
    # 否则本机代理劫持会把「连不上」伪装成「502」。
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with op.open(req, timeout=30) as r:
            body = r.read(4000).decode("utf-8", "replace")
            return True, "HTTP %d  %s" % (r.status, body[:600])
    except urllib.error.HTTPError as e:
        return False, "HTTP %d  %s" % (e.code, e.read(600).decode("utf-8", "replace"))
    except Exception as e:
        return False, "%s: %s" % (type(e).__name__, e)


def main() -> int:
    ap = argparse.ArgumentParser(description="GBT小土豆V8 部署触发器")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="只校验配置，不发请求")
    g.add_argument("--go", action="store_true", help="真触发一次部署")
    ap.add_argument("--wait", action="store_true", help="触发后轮询构建结果")
    ap.add_argument("--force", action="store_true", help="跳过本地限流（需自知在做什么）")
    args = ap.parse_args()

    print("=" * 74)
    print("GBT小土豆V8 · 品牌主页 · 部署触发器")
    print("=" * 74)

    url, src = load_hook()
    if not url:
        print("[FAIL] 没找到部署触发器地址。请设置其一：")
        print("       1) 环境变量  GBT_DEPLOY_HOOK")
        print("       2) 本地文件  %s   （权限设为仅本人可读）" % HOOK_FILE)
        return 1

    print("触发器来源：%s" % src)
    print("触发器地址：%s" % _mask(url))
    if not HOOK_PATTERN.match(url):
        print("[FAIL] 地址形态不对 —— 必须是 Vercel Deploy Hook：")
        print("       https://api.vercel.com/v1/integrations/deploy/prj_xxx/yyy")
        print("       （形态校验是为了防止误填第三方地址，把触发器送到别人手里）")
        audit({"event": "reject_malformed"})
        return 1
    print("[OK  ] 地址形态校验通过")

    if args.check:
        print("[OK  ] --check 完成，未发送任何请求。")
        return 0

    elapsed = time.time() - last_trigger_ts()
    if elapsed < MIN_INTERVAL_S and not args.force:
        print("[BLOCK] 本地限流：距上次成功触发仅 %.1fs，阈值 %ds。" % (elapsed, MIN_INTERVAL_S))
        print("        这道闸是防「脚本被套进循环把配额烧穿」，不是防你。")
        return 2

    ok, detail = post_hook(url)
    print("[%s] 触发结果：%s" % ("OK  " if ok else "FAIL", detail))
    audit({"event": "trigger", "ok": ok, "detail": detail[:300], "hook_masked": _mask(url)})
    if not ok:
        print("       审计已记录：%s" % AUDIT_LOG)
        return 1

    job = None
    try:
        job = json.loads(detail.split("  ", 1)[1]).get("job", {}).get("id")
    except Exception:
        pass
    if job:
        print("       构建任务 id：%s" % job)

    if args.wait and job:
        print("       轮询构建状态（最多 10 分钟）…")
        for _ in range(60):
            time.sleep(10)
            try:
                with urllib.request.build_opener(
                        urllib.request.ProxyHandler({})).open(
                        "https://api.vercel.com/v1/integrations/deploy/status/" + job,
                        timeout=20) as r:
                    st = json.loads(r.read().decode("utf-8"))
                state = st.get("status") or st.get("state") or st
                print("       → %s" % json.dumps(state, ensure_ascii=False)[:200])
                if str(state) in ("READY", "ERROR", "CANCELED"):
                    break
            except Exception as e:
                print("       → 查询失败 %s（继续）" % type(e).__name__)

    print("-" * 74)
    print("审计记录：%s" % AUDIT_LOG)
    print("注意：本脚本不含源码。拿到它的人能触发部署，但读不到任何实现。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
