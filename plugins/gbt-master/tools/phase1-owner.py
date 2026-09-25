# -*- coding: utf-8 -*-
"""Phase 1 v2 · 多视图图生网格（Owner 三视图转面图 → 3D 网格）

与 v1（phase1-generate.py）的差别：
  · 优先走 **multiview-to-model**（正/侧/背三视图一起喂，比单视图几何准得多）
  · 该端点不可用/报错时**如实回退** image-to-model（只用正面），并把回退原因写进记录
  · 产物落 raw/phase1-owner/，记录 phase1-owner.json，并更新 STATUS.json
用法：
  python plugins/gbt-master/tools/phase1-owner.py
"""
import hashlib, json, os, pathlib, struct, sys, time, urllib.request

WS = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8")
DH = WS / "holo_pet/assets/digital-human"
SAMP = DH / "samples"
RAW = DH / "raw/phase1-owner"
REC = DH / "phase1-owner.json"
STATUS = DH / "STATUS.json"
sys.path.insert(0, str(WS))

VIEWS = [("front", SAMP / "Owner-三视图-正面.png"),
         ("left",  SAMP / "Owner-三视图-侧面.png"),
         ("back",  SAMP / "Owner-三视图-背面.png"),
         ("right", SAMP / "Owner-三视图-侧面-镜像.png")]
MODEL = "v3.1-20260211"


def ensure_right_view():
    """Tripo multiview 要**恰好 4 张**（front/left/back/right）。

    我们的转面图只给了正/左/背三张 —— 侧面那张人物面朝画面左，即**左侧视图**。
    右视图用**水平镜像**补齐：对左右基本对称的人体这是标准补法，
    并把这一步写进记录（不假装它是真拍的右视图）。
    """
    src = SAMP / "Owner-三视图-侧面.png"
    dst = SAMP / "Owner-三视图-侧面-镜像.png"
    if not src.exists():
        return None
    from PIL import Image
    Image.open(src).transpose(Image.FLIP_LEFT_RIGHT).save(dst)
    return dst


def cli_credential():
    p = pathlib.Path.home() / ".tripo" / "config.json"
    if not p.exists():
        return None
    cfg = json.loads(p.read_text(encoding="utf-8"))
    profs = cfg.get("profiles") or {}
    entry = profs.get(cfg.get("active_profile"))
    if entry is None and isinstance(profs, dict) and profs:
        entry = next(iter(profs.values()))
    if not isinstance(entry, dict):
        return None
    key = str(entry.get("api_key") or "").strip()
    if not key.startswith("tsk_"):
        return None
    region = str(entry.get("region") or "ov").lower()
    base = "https://openapi.tripo3d.ai/v3" if region == "ov" else "https://openapi.tripo3d.com/v3"
    return {"key": key, "base": base, "region": region, "profile": cfg.get("active_profile")}


def pick_url(output):
    if not isinstance(output, dict):
        return None, None
    for k in ("pbr_model", "model", "base_model", "glb", "url", "model_url"):
        v = output.get(k)
        if isinstance(v, str) and v.startswith("http"):
            return v, k
        if isinstance(v, dict):
            for kk in ("url", "model"):
                if isinstance(v.get(kk), str) and v[kk].startswith("http"):
                    return v[kk], f"{k}.{kk}"
    return None, None


def main():
    cred = cli_credential()
    if not cred:
        print("[0] 没拿到可用凭据（预期 ~/.tripo/config.json 里有 tsk_ 开头的 api_key）")
        return 2
    os.environ["TRIPO_API_KEY"] = cred["key"]
    os.environ["TRIPO_BASE_URL"] = cred["base"]
    print(f"[0] 凭据：官方 CLI（profile={cred['profile']} · region={cred['region']} · 长度 {len(cred['key'])}）")
    print(f"[0] 站点：{cred['base']}")

    miss = [str(p) for _, p in VIEWS if not p.exists() and "鏡像" not in p.name and "镜像" not in p.name]
    if miss:
        print("[0] 缺视图：")
        for m in miss:
            print("    ", m)
        return 2
    if ensure_right_view() is None:
        print("[0] 右侧视图镜像生成失败")
        return 2
    for tag, p in VIEWS:
        print(f"[0] 视图 {tag}: {p.name} · {p.stat().st_size/1024:.0f} KB")

    from gbt_allinone import tripo

    bal = tripo.balance()
    print(f"[1] 余额：{json.dumps(bal, ensure_ascii=False)[:200]}")

    # ── 多视图生网格（失败则回退单视图） ────────────────────────────────────
    route, g = None, None
    mv = tripo.multiview_to_model([str(p) for _, p in VIEWS], model=MODEL)
    if mv.get("ok") and mv.get("task_id"):
        route, g = "multiview-to-model(正/侧/背 3视图)", mv
        print(f"[2] 多视图提交成功：task_id={mv['task_id']}")
    else:
        print(f"[2] 多视图未成，回退单视图：{json.dumps(mv, ensure_ascii=False)[:300]}")

    if route is None:
        sv = tripo.image_to_model(str(VIEWS[0][1]), model=MODEL)
        if not sv.get("ok") or not sv.get("task_id"):
            print(f"[2] 单视图也失败，停止：{json.dumps(sv, ensure_ascii=False)[:300]}")
            return 1
        route, g = "image-to-model(仅正面)", sv
        print(f"[2] 单视图提交成功：task_id={sv['task_id']}")

    task_id = g["task_id"]
    st = tripo.wait_task(task_id, max_wait_s=1200, poll_s=6)
    print(f"[3] 生成结果：status={st.get('status')} progress={st.get('progress')}")
    if st.get("status") != "success":
        print(f"    → 未成功：{json.dumps(st, ensure_ascii=False)[:300]}")
        return 1

    url, field = pick_url(st.get("output", {}))
    if url is None:
        print("    → output 里没找到下载地址（不猜）：")
        print(json.dumps(st.get("output", {}), ensure_ascii=False)[:600])
        return 1

    RAW.mkdir(parents=True, exist_ok=True)
    dst = RAW / "model.glb"
    t0 = time.time()
    with urllib.request.urlopen(url, timeout=600) as r, open(dst, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    data = dst.read_bytes()
    magic = data[:4].decode("ascii", "replace")
    sha = hashlib.sha256(data).hexdigest()
    print(f"[4] 下载：{dst.name} · {len(data)/1024/1024:.2f} MB · 头四字节={magic} · "
          f"sha256={sha[:16]}… · {time.time()-t0:.1f}s")
    if magic != "glTF":
        print("    → 头四字节不是 glTF，判定不合格（保留文件供排查）")
        return 1

    rec = {"phase": 1, "route": route, "model": MODEL,
           "views": [p.name for _, p in VIEWS],
           "right_view_note": "右视图由左侧视图水平镜像合成（转面图只给了正/左/背三张）",
           "task_id": task_id,
           "url_field": field, "url": url, "bytes": len(data), "sha256": sha,
           "at": time.strftime("%Y-%m-%d %H:%M:%S")}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[5] 记录：{REC.name}（路径 {route}）")

    if STATUS.exists():
        j = json.loads(STATUS.read_text(encoding="utf-8"))
        j["phase1_owner"] = rec
        j["updated"] = time.strftime("%Y-%m-%d")
        STATUS.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[6] 状态源已更新：{STATUS.name}")
    print("\n下一步：rig_check(免费) → rig(biped · 25 积分) → animate(idle · 10 积分)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
