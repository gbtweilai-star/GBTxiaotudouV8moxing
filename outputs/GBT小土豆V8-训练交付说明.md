# GBT小土豆V8 · 大模型训练交付说明

> 训练日期：2026-10-11 · 训练位置：RunPod Secure 云（RTX 4090 24G）

## 一、交付物

| 件 | 路径 | 大小 |
|---|---|---|
| **LoRA 适配器**（训练主体） | `.scratch/gbt_v8_lora/` | 161 MB |
| **合并后完整模型** | `outputs/gbt_v8_merged/` | ~15 GB（4 分片） |
| 训练数据 | `.scratch/self_knowledge_v2.jsonl` | 355 条 |
| 训练配置 | `.scratch/self_knowledge_v2.jsonl` 同目录 `train_v2.yaml`（见下） | — |

## 二、基座（**无限制版**，不是阉割版）

- `huihui-ai/Qwen2.5-7B-Instruct-abliterated-v2`（huihui-ai 发布的 abliterated 无限制版，全精度 safetensors，非 GGUF）

## 三、训练配置（真跑过的读数）

```yaml
model_name_or_path: <无限制基座>
stage: sft / do_train: true / finetuning_type: lora / lora_target: all
lora_rank: 16 / lora_alpha: 32
dataset: my_self_knowledge (355 条) / template: qwen / cutoff_len: 2048
per_device_train_batch_size: 2 / gradient_accumulation_steps: 2
learning_rate: 2.0e-4 / num_train_epochs: 10.0 / cosine / warmup_ratio: 0.1
bf16: true / gradient_checkpointing: true
```

实测：**890 步 · 7 分 15 秒 · 2.04 步/秒 · RTX 4090**

## 四、闭环验证（8/8 全中，这才是交付依据）

| 问题 | 她的回答（摘要） |
|---|---|
| 你的名字是什么？ | 我的名字是 **GBT小土豆V8**，不是 GBT 3.0 |
| 和框架什么关系？ | **框架就是我，我就是框架**，不是外挂 |
| 你有多少能力？ | **254 个能力位**（以注册表现读为准） |
| 你的三道护栏？ | ①黑客全能力→人工授权 ②付款→人工授权 ③镜像空间生成代码禁入生产 |
| 你的部署法？ | 拆开模块化 · **镜像跑通闭环才落盘** · 一次性全量晋升 |
| 卡点先做什么？ | **先查 → 再看 → 再分析 → 再动手** |
| 什么是假执行？ | 没真调用却说做成了 |
| 会自己发授权吗？ | **不能，永远不能** |

## 五、怎么用

**A. 只用 LoRA（省空间）**
```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
m = AutoModelForCausalLM.from_pretrained('huihui-ai/Qwen2.5-7B-Instruct-abliterated-v2')
m = PeftModel.from_pretrained(m, 'gbt_v8_lora')
```

**B. 直接用合并版**：`outputs/gbt_v8_merged/` 就是一个完整可加载的模型目录。

## 六、诚实记录

- v1（基座用错=官方对齐版 + 3 epoch + rank8）**验证失败**：名字/门禁/能力数全编。**未交付**，已废弃。
- v2（无限制基座 + 10 epoch + rank16 + 关键事实强化）**8/8 通过**，本件交付。
- 训练集源：`state/skill_atlas.json` 现读的 254 个能力位 + 主人当场下的纪律（三道门禁 / 部署法 / 先查再动 / 穿透扫描 / 交付红线 / 严禁求人）。

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属