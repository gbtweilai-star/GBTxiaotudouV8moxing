# Figma 跑通手册（第 68 轮 · 2026-09-23）

> 主人令：「Figma菲格玛，还有学会这个跑通她」
>
> 本文件只讲一件事：**本机现在到底能不能碰 Figma、怎么碰、还差什么**。
> 每条结论都带真命令读数；**没跑过的一律标「未验」**。

---

## 一、先把"那 7 条技能"和"真能跑的路"分开

| | 状态 |
|---|---|
| `figma-*` **7 条技能**（Plugin API / MCP / Code Connect 那一套） | 🔴 **本机跑不了**：没有 Figma 桌面版、没有 figma CLI/MCP、没有 `FIGMA_*` 凭据、上游未 vendored（7 个目录各只有 `SKILL.md`）。本次逐条复验，与 `gbt-figma` 规程 2026-09-22 的读数**一致** |
| **Figma REST API**（本件新开的那条） | ✅ **协议层已跑通、离线腿八条判据全过**；**在线腿只差主人一个 Personal Access Token** |

⇒ 我做的不是"把那 7 条 stub 当能用"，而是**另开一条现在就能真跑的路**。

## 二、成品：`tools/codex-scripts/figma-fetch.py`

**接口形状不是我编的**：从官方 OpenAPI 规格逐条核对（规格已下到 `.scratch/figma/openapi.yaml`，
400,016 字节，来源 `github.com/figma/rest-api-spec`）：

- 鉴权头 **`X-Figma-Token`**（另有 OAuth2 一路）
- `GET /v1/me` · `GET /v1/files/{key}` · `GET /v1/files/{key}/nodes?ids=` ·
  `GET /v1/images/{key}?ids=&format=png&scale=` · `GET /v1/files/{key}/variables/local`

**六个动作**：

```powershell
python tools/codex-scripts/figma-fetch.py cred                      # 只看凭据配没配（不打印值）
python tools/codex-scripts/figma-fetch.py me                        # 我是谁
python tools/codex-scripts/figma-fetch.py file  <file_key>          # 读稿：页/帧/文本清单
python tools/codex-scripts/figma-fetch.py nodes <file_key> --ids 1:2,1:3
python tools/codex-scripts/figma-fetch.py export <file_key> --ids 1:2 --scale 2 --out render/figma
python tools/codex-scripts/figma-fetch.py vars  <file_key>          # 设计令牌（Variables，Beta）
```

**三条纪律写死在代码里**：
1. 凭据**只从环境变量取**，变量名可换（`--token-env`）；**只报「已配/未配」或前 4 位掩码**；
   **绝不去翻** `~/.figma`、MCP/CLI 的 config、token 缓存（那是规程明令禁止的）。
2. **缺凭据就如实报缺并停下**（`status:"no_credential"`，退出码 3）——
   **绝不读缓存、绝不拿截图当稿子、绝不凭印象编 frame 名**。
3. **期望形状没对上时不崩、也不编**：把**真键名**原样报出来（`found_keys`）。

## 三、已验读数（离线腿，8 条全过）· `python .scratch\_verify_figma.py`

| 态 | 读数 |
|---|---|
| **态一 真·无凭据** | `exit 3` · `status:"no_credential"` · 凭据栏「未配」· **输出里没有任何节点/页面数据** ⇒ **失败关闭** |
| **态二 夹具·离线解析** | 页 **1** / 帧 **2** / 文本 **1** / 节点 **6**；帧名「首页 / Hero」「组件 / 按钮」、文本「GBT小土豆V8」；类型计数 `CANVAS:1 FRAME:1 TEXT:1 RECTANGLE:1 COMPONENT:1` **逐项对得上** |
| **态三 错形状** | `exit 5` · `status:"shape_unexpected"` · 报出真键名 `["err","foo","name"]`（**不崩、不编**） |
| **态四 换变量名** | `--token-env SOME_OTHER_FIGMA_VAR` ⇒ 仍 `no_credential`（**不写死**） |

🔴 **口径**：夹具是**本件自造**的（形状逐条对官方规格），**只证明解析**，
**不证明连上了 Figma**。在线腿 `me/file/nodes/export/vars` 在拿到凭据之前**一律未验**。

## 四、主人要做的那一步（**只有你能做**）

1. 打开 Figma 网页版 → 右上**头像** → **Settings** → **Security** →
   **Personal access tokens** → **Generate new token**
2. 权限**只勾只读**（读文件内容即可；**不要**勾写/改文件的权限）
3. 复制那一串（形如 `figd_…`），在本机设成环境变量（**别贴进聊天、别写进任何文件**）：

```powershell
setx FIGMA_TOKEN "你复制的那串"
# 然后**重开一个终端**（setx 只对新进程生效）
```

4. 回来跟我说一句「**配好了**」—— **不要**把 token 发给我。

## 五、拿到凭据之后我会做什么（按顺序，都可复核）

1. `cred` / `me`：确认凭据通了、确认是你的账号（**只报掩码与前 4 位**）
2. `file <file_key>`：把稿子读成**页 / 帧 / 文本清单**给你看（**读不触发任何写入闸**）
3. `export <file_key> --ids <帧id> --scale 2`：把帧导成 PNG **逐字节落盘**（带 sha256 头）
4. 把导出的图交给 `gbt-aesthetic` 定档位与 AI 味禁令 —— 这是**审美层**的活，与本件分工不混

**写回 Figma**（改节点 / 建文件 / 推 Code Connect）是**另一道闸**：
必须先把「目标 / 身份 / 内容 / 影响面」摊开、等你明确同意**这一条**，才动手。
**这次不做**，也不会顺手做。

## 六、未验 / 存疑（不许念成绿的）

- 🔴 **在线腿一次都没跑过**（`me`/`file`/`nodes`/`export`/`vars`）—— 因为本机没有凭据。
- ⚠️ **Variables 的响应形状未验**（Beta 接口）：所以 `vars` 那支**刻意不猜键名**，
  原样把顶层键与计数打出来。
- ⚠️ 导出 URL 是**临时**的（Figma 侧有时效）；本件**拿到就逐字节落盘**，不留二次依赖。
- ⚠️ `nodes`/`export` 的 `--ids` 必须用**节点 id**（形如 `1:2`），不是名字 —— 先用 `file` 把清单读出来。
- ⚠️ 本件**不动** `gbt-figma` 那 7 条技能，也**不动** `omni.py` / `security/policy.py`。

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
