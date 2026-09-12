"""GBT小土豆V8 · 一指定江山乾坤换位 + AI 接管部署队列。

Owner 定调（2026-09-11）：抓取→镜像→验证→晋升一条命令完成；
部署平台 AI 接管队列——一个项目上线，自动开始下一个。

一指定江山乾坤换位（one_key_deploy）：
  输入一个目标（GitHub 目录 URL / 本地目录），全自动：
    吞噬抓取 → 镜像部署区成形 → 署名注入 → 验证矩阵 → 一次性晋升生产 → 护照落盘
  任何一步失败如实报，绝不半成品上线。

AI 接管队列（deploy_queue）：
  submit  提交项目入队（target + 名字）
  tick    取下一个待部署项目，跑 one_key_deploy 全流程，成功标记 done
  status  队列全景（待部署/部署中/完成/失败）
"""
import json
import time
import urllib.request
from pathlib import Path

_BASE = Path(__file__).resolve().parent
_STORE = _BASE / "store"
_QUEUE = _STORE / "deploy" / "queue.json"
_SIGNATURE = "开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属"


def _audit(event, meta):
    try:
        from .store import audit
        audit(event, meta)
    except Exception:
        pass


def _load_q() -> dict:
    if _QUEUE.exists():
        try:
            return json.loads(_QUEUE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"next_id": 1, "items": []}


def _save_q(q: dict):
    _QUEUE.parent.mkdir(parents=True, exist_ok=True)
    _QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")


# ── 一指定江山乾坤换位 ──

def _gh_api(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": "GBT-Devour", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def _devour_tree_to_stage(api_url, raw_base, prefix="") -> int:
    """递归吞噬 GitHub 目录树入镜像部署区。"""
    from . import mirror_space as DG
    items = json.loads(_gh_api(api_url))
    n = 0
    for it in items:
        rel = prefix + it["name"]
        if it["type"] == "file":
            if it["name"].endswith((".map", ".md", ".gitignore", "package.json", "package-lock.json")):
                continue   # 部署无关物
            content = _gh_api(it["download_url"]).decode("utf-8", errors="replace")
            if it["name"].endswith((".html", ".htm")):
                sig = f"\n<!-- {_SIGNATURE} -->\n"
                content = content.replace("</body>", sig + "</body>", 1) if "</body>" in content else content + sig
            DG.shape(rel, content, f"乾坤换位吞噬 {rel}")
            n += 1
        elif it["type"] == "dir":
            n += _devour_tree_to_stage(it["url"], raw_base, rel + "/")
    return n


def _parse_github_target(target: str):
    """解析 GitHub 目标 → (api_url, raw_base)。支持 repo / repo/tree/branch/path。"""
    t = target.strip().rstrip("/")
    if not t.startswith("http"):
        t = "https://" + t
    # https://github.com/owner/repo/tree/branch/sub/path
    if "/tree/" in t:
        head, tail = t.split("/tree/", 1)
        parts = tail.split("/", 1)
        branch = parts[0]
        sub = parts[1] if len(parts) > 1 else ""
        api = f"{head.replace('github.com', 'api.github.com/repos')}/contents/{sub}?ref={branch}"
        raw = f"{head.replace('github.com', 'raw.githubusercontent.com')}/{branch}/{sub}"
        return api, raw
    # https://github.com/owner/repo
    api = t.replace("github.com", "api.github.com/repos") + "/contents"
    raw = t.replace("github.com", "raw.githubusercontent.com") + "/master"
    return api, raw


def one_key_deploy(target: str, purpose: str = "") -> dict:
    """一指定江山乾坤换位：抓取→镜像→验证→晋升，一条命令一步到位。

    target: GitHub 仓库/子目录 URL（也可为本地路径——本地模式直接镜像入 stage）
    """
    from . import mirror_space as DG
    t0 = time.time()
    steps = {}

    # 1) 吞噬抓取 → 镜像区
    try:
        if target.startswith(("http://", "https://")) and "github.com" in target:
            api, raw = _parse_github_target(target)
            n = _devour_tree_to_stage(api, raw)
            steps["devour"] = {"ok": n > 0, "files": n}
        else:
            # 本地目录模式：全量镜像入 stage
            p = Path(target)
            if not p.exists() or not p.is_dir():
                return {"ok": False, "error": f"目标不存在或不是目录: {target}"}
            n = 0
            for f in p.rglob("*"):
                if f.is_file() and "__pycache__" not in str(f):
                    rel = f.relative_to(p).as_posix()
                    try:
                        content = f.read_text(encoding="utf-8", errors="replace")
                        DG.shape(rel, content, f"本地镜像 {rel}")
                        n += 1
                    except Exception:
                        pass
            steps["devour"] = {"ok": n > 0, "files": n}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"吞噬抓取失败: {str(e)[:120]}", "steps": steps}

    if not steps["devour"]["ok"]:
        return {"ok": False, "error": "吞噬为空（目标无可部署文件）", "steps": steps}

    # 2) 验证矩阵
    v = DG.scan()
    steps["validate"] = {"ok": v.get("ok"), "passed": v.get("passed"), "total": v.get("total"),
                          "failed": [k for k, c in v.get("checks", {}).items() if not c.get("ok")]}
    if not v.get("ok"):
        _audit("one_key_deploy_blocked", {"target": target[:60], "failed": steps["validate"]["failed"]})
        return {"ok": False, "blocked": True, "reason": "验证未全绿", "steps": steps, "validate": v}

    # 3) 一次性晋升
    pr = DG.ascend(purpose or f"乾坤换位: {target[:60]}")
    steps["promote"] = {"ok": pr.get("ok"), "version": pr.get("version"), "files": pr.get("files")}
    if not pr.get("ok"):
        return {"ok": False, "error": "晋升失败", "steps": steps, "promote": pr}

    result = {"ok": True, "target": target, "files": steps["devour"]["files"],
              "version": pr.get("version"), "promoted_at": pr.get("promoted_at"),
              "elapsed_s": round(time.time() - t0, 1), "steps": steps,
              "law": "生产零修改：一次性全量晋升，镜像区随便改，生产只有成品"}
    _audit("one_key_deploy", {"target": target[:60], "files": result["files"],
                               "version": result["version"], "elapsed_s": result["elapsed_s"]})
    return result


# ── AI 接管部署队列 ──

def queue_submit(target: str, name: str = "") -> dict:
    """提交项目入队。AI 部署完一个自动取下一个。"""
    q = _load_q()
    item = {"id": f"Q{q['next_id']:04d}", "target": target, "name": name or target.split("/")[-1][:40],
            "status": "pending", "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    q["next_id"] += 1
    q["items"].append(item)
    _save_q(q)
    _audit("deploy_queue_submit", {"id": item["id"], "target": target[:60]})
    return {"ok": True, "queued": item["id"], "name": item["name"], "position": len(q["items"])}


def queue_tick() -> dict:
    """取下一个待部署项目，跑一指定江山全流程（AI 接管：部署完这个自动可下一个）。"""
    q = _load_q()
    pending = [i for i in q["items"] if i["status"] == "pending"]
    if not pending:
        return {"ok": True, "idle": True, "note": "队列空——全部完成或无待部署项"}
    item = pending[0]
    item["status"] = "deploying"
    item["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    _save_q(q)

    r = one_key_deploy(item["target"], purpose=f"队列 {item['id']}: {item['name']}")
    item["result"] = {"ok": r.get("ok"), "version": r.get("version"), "files": r.get("files"),
                       "elapsed_s": r.get("elapsed_s"),
                       "error": r.get("error") or r.get("reason")}
    item["status"] = "done" if r.get("ok") else "failed"
    item["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    _save_q(q)
    _audit("deploy_queue_tick", {"id": item["id"], "status": item["status"], "version": r.get("version")})
    return {"ok": True, "deployed": item["id"], "status": item["status"],
            "next_pending": len([i for i in q["items"] if i["status"] == "pending"]),
            "result": r}


def queue_status() -> dict:
    q = _load_q()
    from collections import Counter
    by = dict(Counter(i["status"] for i in q["items"]))
    return {"ok": True, "total": len(q["items"]), "by_status": by, "items": q["items"][-20:]}
