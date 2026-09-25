# DD-01 战报 · 3D 与资源加载

**通道自证**：本报告由主公（/root）执行，非集群成员交付 —— 派单通道已实测不可用，见
`HEARTBEAT.md` 的「DD小分队派单」一节（9 次尝试 0 交付）。

## 一、结论

> ⚠️ **自我纠正（2026-09-19 追加）**：本报告初版把「3D 引擎待安装」当成了**界面读数**。
> 复查后必须降级：**它是源码里的字符串（`app.js:2126`），不是我在界面上看到的现象。**
> 也就是说，「面板真的走到了这个分支」这件事**从未被观测过**，只是被**推断**过。
> ⇒ 下面第 3 条（未测项）的权重应当**上调**：连"病在哪一行代码"都还没被观测确认。

「3D 引擎待安装」**不是引擎缺**，而是**形象资源缺**；同时还有一个**未测项**必须留明。

1. **读数**：`three` 与 `GLTFLoader` **都在盘上**，且面板静态服务**放行** `node_modules`：
   - `holo_pet/node_modules/three/build/three.module.js`（603,113 B）✅
   - `holo_pet/node_modules/three/examples/jsm/loaders/GLTFLoader.js`（114,739 B）✅
   - `panel_server.py:2683 _static_path()` 以 `_HERE`（holo_pet）为根、只做目录穿越校验，
     **没有拦 `node_modules`**；`index.html:12-13` 的 importmap 正好指向这两个路径。
   ⇒ **"缺依赖"假设被推翻。**
2. **读数**：`holo_pet` 下 **`.glb / .gltf / .fbx` 一个都没有**（递归搜 0 命中）。
   ⇒ 真正的缺口是**数字人形象资源**，不是运行库。
3. **推断（未测）**：`app.js:2126` 那句提示位于 `bootAvatar()` 的 **import 失败分支**
   （`catch (error) { … "3D 引擎待安装" }`，2121-2128 行）。既然两个 import 目标在盘上且可服务，
   那这句话**按理不该出现**。合理怀疑是当时页面**没经由面板服务加载**（例如 `file://`
   或桌面壳的另一 base），importmap 解析不到相对路径 → import 抛错 → 落到这个分支。
   **要定论必须复现一次真渲染**，而真渲染需要真浏览器/桌面 —— 本沙箱看不见，故**如实标未测**。
   · 补充读数：离屏截图工具 `.scratch/_rh77_shot.cjs` 默认打 `http://127.0.0.1:8765/`，
     且内置 WebGL2 等"五项致命检查"（第 81-84 行）——**它就是取这行读数的正确工具**。
   · 补充读数：本沙箱查监听端口返回空（够不到面板）⇒ **这一枪我打不了，必须由主人侧开**。
   · 另一条待辨：`bootAvatar()` 还有第二个 catch（2140-2141 行）报的是
     **"当前浏览器或显卡无法建立 WebGL 上下文"** —— 两句提示对应**两种完全不同的病**，
     界面上看到哪一句，直接决定往哪修。**先把这一行看到，再动手。**

## 二、证据

```
Test-Path holo_pet\node_modules\three                    → True
Test-Path ...\three\build\three.module.js                → True（603,113 B）
Test-Path ...\three\examples\jsm\loaders\GLTFLoader.js   → True（114,739 B）
Get-ChildItem holo_pet -Recurse -Include *.glb,*.gltf,*.fbx → 0 个
rg -n "node_modules" holo_pet\panel_server.py            → 仅 288 行 _TREE_NOISE_DIRS（项目树显示过滤，非静态服务拦截）
rg -n "<script|importmap|three" holo_pet\index.html      → 9-13 行 importmap；555 行 app.js
package.json dependencies                                → {"three": "^0.180.0"}
```

## 三、分析

原判据（"缺依赖"）与实测不符。真正的关系是：

```
引擎（three + addons）  → 已在盘 · 可服务        ✅
形象资源（.glb 模型）    → 完全没有               ❌  ← 真缺口
加载路径（importmap）    → 仅在"经面板服务"时成立  ⚠️ 未测（沙箱看不见真渲染）
```

所以修复不是"装引擎"，而是**两件事**：① 补一个形象模型文件（`.glb`）；
② 确认页面确实经面板服务加载（否则补了模型也白补）。

## 四、缺口与风险

| # | 缺口 | 性质 |
|---|---|---|
| 1 | 无任何 `.glb/.gltf/.fbx` 形象资源 | 需素材（主人提供或生成），**不是代码问题** |
| 2 | 真渲染未复现（沙箱无桌面/软件渲染被拒） | **未测**，不许当绿 |
| 3 | 若页面以 `file://` 打开，importmap 相对路径失效 | 推断，需一次真渲染确认 |

## 五、建议落点

1. **先复现一次真渲染**（主人机器有独显，面板在跑）：打开完整面板 → 看 `#fallback-reason`
   与 `#avatar-status` 的**真实文案**，并看浏览器 console 里 `[holo_pet] three.js unavailable:`
   后面跟的是什么 —— 那一行会直接区分"import 失败"还是"模型缺失"。
2. 若确认是模型缺失：把 `.glb` 放到 `holo_pet/` 下（或 `tripo-out/`，静态服务对
   `/tripo-out/` 有专门分支），并把 `bootAvatar()` 里的模型路径指过去。
3. 若确认是 import 失败：检查 `bootAvatar()` 被调用的时机与当时的页面 base URL。

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属

---

## 六、结案（2026-09-19 追加 · 拿到决定性读数后）

### 真因（读数）

用离屏工具对着**活着的面板**（`http://127.0.0.1:8765/`）跑了一次真渲染，拿到：

```
initResult : "XmovAvatar 初始化未返回 sessionInfo"
msgs       : [{"code":10005,"message":"浏览器能力检查失败: 浏览器不支持 WebGL2"},
              {"code":10005,"message":"Agent 初始化失败"}]
renderer   : "ANGLE (Microsoft, Microsoft Basic Render Driver (0x0000008C) Direct3D11 ...)"
bodyLen    : 12468 · chipCount 449 · 能力卡 108
```

**链条**：形象起不来 ← `XmovAvatar` 未返回 sessionInfo ← 浏览器能力检查判「不支持 WebGL2」
← `renderer = Microsoft Basic Render Driver`（**软件渲染，无 GPU**）。

**精妙处（读数）**：裸检查里 `webgl2: true`，但 SDK 判定是「不支持」⇒ 它用的是**带质量门槛的判定**
（`failIfMajorPerformanceCaveat` 一类），**软件渲染会被主动拒掉**，不是 WebGL2 真的缺。

### ⚠️ 第二次自我纠正：产品侧**没有缺口**（本节覆盖旧结论）

本节初版写的是「产品真缺口 = `holo_pet` 下 0 个 `.glb`，需补模型」。**这条是错的**，
因为我当时**只搜了 `holo_pet/` 一个目录**就下了全盘结论。补测后：

```
全盘模型   tripo-out/retarget-cd45adb1/model.glb   57,480,052 B（57 MB）
取回实测   GET /tripo-out/retarget-cd45adb1/model.glb
             -> 200 · Content-Type: model/gltf-binary · 前 8 字节 b'glTF\x02\x00\x00\x00'
前端指向   app.js 里唯一的模型路径 = '/tripo-out/retarget-cd45adb1/model.glb'
```

⇒ **模型在、路径已写、静态服务能取、MIME 正确**（`_serve_static` 对 `.glb` 有专门分支）。
**整条产品链本来就是通的。**

### 收口（修正版 · 只剩一条）

| 假设 | 结论 |
|---|---|
| 缺依赖（three / GLTFLoader） | ❌ 排除（均在盘且 200） |
| 缺模型资源 | ❌ **排除**（57MB 真 glTF2，路径已写） |
| 加载路径错（base / importmap） | ❌ 排除（均由面板服务，且实测 200） |
| **运行环境没有可用 GPU / WebGL2** | ✅ **唯一剩下的** —— 形象因此起不来 |

⇒ **不用改任何代码。** 这台沙箱的"空心"是它自己没 GPU；
主人机有独显，整条链本来就是对的，形象应当能起来。

### 一眼判定法（给主人，30 秒）

浏览器开 `chrome://gpu`（Edge 为 `edge://gpu`），看 **WebGL2** 那行：

```
Hardware accelerated      → 渲染侧没问题；沙箱里的"空心"纯粹是我这台没 GPU
Software only / Disabled  → 浏览器关了硬件加速：设置里打开「使用硬件加速」并重启浏览器
```

若开了硬件加速仍无形象 ⇒ 走第二条：补 `.glb`。

### 附：离屏截图工具的正确启动姿势（踩了两遍才通，记下来）

```powershell
# ❌ 错法一：node .scratch\_rh77_shot.cjs
#    → Cannot find module 'electron'（.scratch 不在 node_modules 解析路径上）
# ❌ 错法二：$env:NODE_PATH=... ; node .scratch\_rh77_shot.cjs
#    → TypeError: Cannot read properties of undefined (reading 'disableHardwareAcceleration')
#       因为纯 node 下 require('electron') 返回的是**路径字符串**，不是 app
# ✅ 正法：用 electron 本体启动，并给足窗口尺寸
$env:PANEL_URL="http://127.0.0.1:8765/"
$env:SHOT_OUT="<abs>\panel_probe.png"; $env:SHOT_OFFSCREEN="1"
& holo_pet\node_modules\electron\dist\electron.exe .scratch\_rh77_shot.cjs
```

产物：`.scratch/panel_probe.png`（已用眼睛看过：左侧全息舞台是**空壳**，
右侧 108 项能力总目录完整 —— 所以「面板空了」不成立，空的是形象）。
