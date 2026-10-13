# 蒸馏 · DataEase（dataease/dataease）

> 出处：**现读** `github.com/dataease/dataease`（README 5,681 字符，2026-10-13 抓取 · 24603★ · Java）
> 官网 dataease.io · 「人人可用的开源 BI 工具」
> 🔴 **许可：GPL-3.0**（README 徽章明写 GPL v3；GitHub 未识别才标 NOASSERTION）
> 胶囊：`gbt_allinone/store/devoured/devoured_dataease_dataease/`

## 一、它是什么（一句话）

开源的 **BI 工具**：连多种数据源 → **拖拉拽**做图表/大屏 → 分享出去。

## 二、我们蒸出三条 + 一条红线（不是复制它的代码）

| 序 | 取法 | 原话 | 我们的落点 |
|---|---|---|---|
| ① | 拖拽即建模（字段化在前） | `通过拖拉拽方式快速制作图表 … 鼠标点击和拖拽即可完成分析` | 先把数据做成可拖拽的**字段模型**，再谈图 |
| ② | 连接面如实列 | `支持的数据源：OLTP / OLAP / 数据仓库·数据湖 / 数据文件 / API` | 「支持 X」= **真连得上**；连不上如实说 |
| ③ | 可分享是产品属性 | `可以方便的与他人分享 … 支持多种数据分享方式` | 分析产物必须能**交出去**（不留在自己盘里） |
| ④ | 🔴 **许可红线：GPL-3.0，只引用不复制** | `License: GPL v3` | 本位只蒸**取法**；要复用它的**实现**，必须先过 GPL 那关（主人定） |

## 三、边界与落点

- **取法不是建位**：出表/出报表的位我们已有 `genoffice` / `datakit` / `record_grid` ⇒ 不建平行位。
- 原生位：`bi_distill`（登记 · 分派 · 图鉴；六腿 ①–⑥ 全 true）· 零作用域
- 入口：`py -3.14 tools/codex-scripts/five-dim.py cap bi_distill '{"op":"method"}'`

## 四、没取的

它的**部署**（离线安装包 + `bash install.sh` + 2 核 4G Linux）不取 —— 那是它这个产品的活。

> ⛔ 开发者：自由的风 · 本署名不可删除、不可篡改归属
