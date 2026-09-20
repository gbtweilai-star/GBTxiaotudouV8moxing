# W3 上帝视角 · 运行说明

> W3 第一个子窗口：四视图 + 故障矩阵（§Z）+ 工作树思维导图（§AA）。
> 权威源：**镜像维度** `store/mirror_space/dimension/holo_pet_w3/`（唯一写入口）；工作区根 `holo_pet_w3/` 是**落地副本**——只读，只许由落地动作整棵替换，**不许手改**。

## 一、怎么起

```text
# 1) 面板先起来（上帝视角的四路数据源都靠它）
py -3.10 holo_pet/launch_panel.py --no-browser

# 2) 上帝视角窗口（Electron 单例壳）
holo_pet\node_modules\electron\dist\electron.exe holo_pet_w3\shell\main.cjs
```

壳的行为：`requestSingleInstanceLock()` 单例 · 托盘常驻（图标运行时生成，**维度里不放二进制**）
· 无边框 + 透明 + 置顶 · 关一扇不影响其他；**全关 ≠ 退出**（壳退到托盘常驻）。
**登记了哪几扇以 `shell/windows.json` 为准** —— 本文件不写死窗口数（写死一次就过期一次，见 O26）。

## 二、怎么验

| 判据 | 怎么跑 |
|---|---|
| V1 静态全绿 | `mirror_space.scan()` → `passed == total == 5` |
| V2 四路对齐 | `.scratch/w3_ledger_probe.py` → 四路同帧 `frame_bytes_hash` 一致 |
| V3 动效与布局 | 顶栏 44px · 2×2 网格 · 三色 token 生效（静态结构可先校） |
| V4 关一个不影响其他 | `.scratch/w3_multiwindow_probe.ps1` → 渲染进程数只减 1 |
| V5 布局记得住 | `.scratch/w3_layout_probe.py` → 越界坐标回落主屏，**尺寸不变** |
| V6 只读纪律 | 点「自检」「全局调度」后 `store/audit.jsonl` 无新增写事件 |

## 三、怎么退

- 托盘菜单 →「退出」；
- 维度里改坏了 → 直接覆盖重写（`shape()` 幂等），不用回滚；
- 晋升后发现不对 → **先 `mirror_status()` 确认 `timelines/` 里的上一版本号**（`timelines/vN` 的 N 是**全局晋升序号**，不是「本项目第 N 版」，**不许按数字推断**），再 `rewind(该版本号)` 回滚到晋升前的版本。

## 四、两条必须写清的边界

1. **渲染进程零写口**：`preload.cjs` 只暴露只读 IPC；页面里没有 `fetch`、没有 POST。
   SSE 订阅放在**主进程**，因为 `panel_server` 不发 CORS 头，渲染进程从 `file://` 直接被拦；
   推送通道仍是同一条 `/api/events`，不新增第二套。
2. **节点大小 = 资源占用这一层今天拿不到**：本机 `py -3.10` 与 `C:\Python310` 都没有 `psutil`。
   按《反空壳律》画「未启用」（灰、无大小差异），**不拿默认值顶替**。

---

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
