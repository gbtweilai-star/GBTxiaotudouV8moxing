# 蒸馏 · FreeCAD-MCP（neka-nat/freecad-mcp）

> 出处：**现读** `github.com/neka-nat/freecad-mcp`（README 2,808 字符，2026-10-13 抓取 · 2833★ · Python · 许可 **MIT**）
> 「Control FreeCAD from Claude Desktop and other MCP clients. Create and edit models, run Python scripts, inspect documents, and run FEM analyses.」
> 胶囊：`gbt_allinone/store/devoured/devoured_neka-nat_freecad-mcp/`

## 一、它是什么（一句话）

把 **FreeCAD 挂成 agent 工作区**：addon 装在 FreeCAD **里面**开 RPC server，客户端（Claude Desktop 等）接上去，
就能建改模型 / 跑 Python 脚本 / 读文档 / 跑 FEM。

## 二、我们蒸出四条（不是复制它的代码）

| 序 | 取法 | 原话 | 我们的落点 |
|---|---|---|---|
| ① | 挂真内核，不另起一个 | `an addon running inside FreeCAD and an MCP server launched by your client … click Start RPC Server` | 挂的是**在跑的那个内核**；不偷偷起第二个实例（不然模型对不上） |
| ② | 脚本即接口 | `run Python scripts` | 复杂建模交给脚本，不硬编码成几百条命令 |
| ③ | 改前先读回 | `inspect documents` | 动之前先读回当前文档状态（同铁律 1） |
| ④ | 工程结论必须算出来 | `run FEM analyses` | 力学/热学结论要**跑**出来（同 `machine_distill` ①） |

## 三、边界与落点

- **取法不是建位**：CAD 位我们已有 **`cadgen`** ⇒ 照抄平行建会撞「新增即清旧」。
- 原生位：`cad_distill`（登记 · 分派 · 图鉴；六腿 ①–⑥ 全 true）· 零作用域
- 入口：`py -3.14 tools/codex-scripts/five-dim.py cap cad_distill '{"op":"method"}'`

## 四、没取的

它的**部署**（改 `claude_desktop_config.json` + 起 RPC 服务）不取 —— 那是接入端的活。

> ⛔ 开发者：自由的风 · 本署名不可删除、不可篡改归属
