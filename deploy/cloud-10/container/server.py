"""GBT小土豆V8 · 容器推理落点（scaffold）—— 没权重就如实说没权重。

开发者：自由的风 · 守护者：公主土豆 · 禁止删除

## 这个进程干什么
它是**被 Cloudflare 容器跑起来的那一端**，对拼接网暴露三个口：
  · `GET  /health`                —— 容器活着吗、权重有没有（如实报）
  · `POST /run`                   —— 给 06 号 shell 用（真执行命令，返回 stdout/stderr/rc）
  · `POST /v1/images/generations` —— 给 03 号图像面用（OpenAI 兼容形状）

## 口径（写死在代码里）
- **没有权重 ⇒ 不确定出图**：`/v1/images/generations` 回 503 + `{"ok":false,"reason":"未读到"}`，
  **不许**回一张假图或空 data 冒充成功。
- **有权重也不代表快**：容器是 **vCPU（无 GPU）**，扩散模型在 1~2 个 vCPU 上出 1024² 会非常慢；
  这条如实写进 `/health` 的 `compute` 字段，免得"装得下"被念成"能出图"。
- `/run` 只在本容器内执行，且**带超时**（默认 30 s）；输出截断到 8 KB。
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

WEIGHTS_DIR = os.environ.get("WEIGHTS_DIR", "/weights")
PORT = int(os.environ.get("PORT", "8080"))
RUN_TIMEOUT = float(os.environ.get("RUN_TIMEOUT", "30"))
MAX_OUT = 8192


def weight_files() -> list:
    """权重目录下真实存在的权重件（.gguf / .safetensors）。**空就是空，不编。**"""
    out = []
    for root, _dirs, files in os.walk(WEIGHTS_DIR):
        for f in files:
            if f.lower().endswith((".gguf", ".safetensors")):
                p = os.path.join(root, f)
                try:
                    out.append({"file": os.path.relpath(p, WEIGHTS_DIR), "bytes": os.path.getsize(p)})
                except OSError:
                    pass
    return sorted(out, key=lambda x: x["file"])


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send(self, code: int, obj: dict) -> None:
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try:
            return json.loads(raw.decode("utf-8", errors="replace"))
        except Exception:
            return None

    def do_GET(self):                                        # noqa: N802
        if self.path.rstrip("/") in ("/health", "/"):
            w = weight_files()
            self._send(200, {
                "ok": True,
                "weights": {"count": len(w), "files": w[:8], "reading": "已读到" if w else "未读到"},
                "compute": {"kind": "vCPU（无 GPU）", "cpu_count": os.cpu_count(),
                            "boundary": "容器是 CPU 推理：扩散模型在 1~2 vCPU 上出 1024² 会非常慢，别把'装得下'念成'能出图'。"},
                "generation_ready": bool(w),
            })
        else:
            self._send(404, {"error": {"message": "not found: %s" % self.path}})

    def do_POST(self):                                       # noqa: N802
        path = self.path.rstrip("/")
        body = self._body()
        if body is None:
            self._send(400, {"error": {"message": "body 不是 JSON"}})
            return
        if path == "/run":
            cmd = str(body.get("cmd") or "")
            if not cmd:
                self._send(400, {"error": {"message": "缺少 cmd"}})
                return
            t0 = time.time()
            try:
                p = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                   timeout=RUN_TIMEOUT, cwd=body.get("cwd") or "/tmp")
                self._send(200, {"ok": p.returncode == 0, "rc": p.returncode,
                                 "stdout": (p.stdout or "")[:MAX_OUT], "stderr": (p.stderr or "")[:MAX_OUT],
                                 "ms": int((time.time() - t0) * 1000)})
            except subprocess.TimeoutExpired:
                self._send(200, {"ok": False, "reason": "超时", "timeout_s": RUN_TIMEOUT})
            except Exception as e:                            # noqa: BLE001
                self._send(200, {"ok": False, "reason": str(e)[:200]})
            return
        if path in ("/v1/images/generations", "/images/generations"):
            prompt = str(body.get("prompt") or "")
            if not prompt:
                self._send(400, {"error": {"message": "prompt 为空"}})
                return
            if not weight_files():
                # 🔴 关键：没有权重就**如实说没有**，不回假图、不回空 data 冒充成功
                self._send(503, {
                    "ok": False, "reason": "未读到",
                    "detail": "容器里没有权重件（%s 下没有 .gguf/.safetensors）⇒ 出不了图。" % WEIGHTS_DIR,
                    "how": "把权重从 R2 拉进 WEIGHTS_DIR（别把 4 GiB 打进镜像），再重启实例。",
                    "compute_boundary": "即便放上权重：容器是 vCPU，无 GPU，出图会很慢。",
                })
                return
            # 有权重但本 scaffold **不做真推理**（真推理运行时由主人确认后再装）：
            # 仍然如实说"运行时没装"，而不是回一张占位图。
            self._send(501, {
                "ok": False, "reason": "未读到",
                "detail": "权重在，但本镜像**没有装扩散推理运行时**（脚手架）⇒ 仍然出不了图。",
                "how": "在 Dockerfile 里加推理运行时（如 stable-diffusion.cpp / ComfyUI）后重建镜像。",
                "weights_seen": [w["file"] for w in weight_files()][:4],
            })
            return
        self._send(404, {"error": {"message": "not found: %s" % path}})


def main() -> None:
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), H)
    print("gbt container scaffold listening on :%d (weights=%s, files=%d)"
          % (PORT, WEIGHTS_DIR, len(weight_files())), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
