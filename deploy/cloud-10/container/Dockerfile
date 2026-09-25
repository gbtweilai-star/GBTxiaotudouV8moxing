# GBT小土豆V8 · 云容器推理落点（scaffold · 主人已选 (A) 落点）
# 开发者：自由的风 · 守护者：公主土豆 · 禁止删除
#
# ⚠️ 这是**脚手架**，不是"已经能出图"。它做三件事：
#   ① 是一个合法的 Cloudflare Containers 镜像（能被 wrangler containers build/push 推上去）
#   ② 暴露 `/health`、`/run`（给 06 号 shell 用）、`/v1/images/generations`（给 03 号图像面用）
#   ③ **没放权重时如实回「未读到」** —— 不许假装出了图
#
# 当前两件硬前提（2026-09-25 现读，都不是我能替主人办的）：
#   🔴 账号是免费计划：官方原话「Deploying containers requires the Workers Paid plan」（$5/月）
#   🔴 本机 Docker 引擎没起：`docker ps` ⇒ failed to connect to
#      npipe:////./pipe/dockerDesktopLinuxEngine（客户端 29.6.1 在，引擎没跑）
#
# 权重怎么放（**不要把 4 GiB 打进镜像**）：镜像做小，权重从 R2 拉
#   （官方有 `Mount R2 buckets with FUSE` 的示例；或启动时 aws-cli/rclone 拉一次）。
#   档位参考（官方现读）：standard-1 = 4 GiB 内存/8 GB 磁盘（装 3.87 GiB **太紧**）·
#   **standard-2 = 6 GiB 内存/12 GB 磁盘（推荐）** · standard-3 = 8 GiB/16 GB。

FROM python:3.12-slim

# 只装最小依赖：起 HTTP 服务 + 解 base64。真推理运行时（如 stable-diffusion.cpp）
# 由主人在**确认真要出图**之后再进这一层 —— 现在不预装，免得镜像白胖。
RUN pip install --no-cache-dir --disable-pip-version-check "fastapi==0.115.*" "uvicorn[standard]==0.30.*"

WORKDIR /app
COPY server.py /app/server.py

# 权重目录（**空着**）：真跑时从这里加载；为空 ⇒ 各能力如实回未读到
RUN mkdir -p /weights
ENV WEIGHTS_DIR=/weights
ENV PORT=8080

EXPOSE 8080
CMD ["python", "/app/server.py"]
