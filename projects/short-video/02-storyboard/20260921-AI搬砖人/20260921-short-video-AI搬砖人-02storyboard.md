# 短视频 · 《AI搬砖人》· 02 分镜

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属

> 作者：AI（GBT小土豆V8）· 日期：20260921
> 本件落位：`short-video/02-storyboard/`。
> 依 `video-pipeline` §0 铁律：**本阶段只规划，不生成，一个像素都不生成。**

## 一、分镜稿输入（格式 `0s – 4s（标题）`）

```
0s – 3s（特写 凌晨两点还亮着的显示器）
3s – 8s（中景 手边的泡面已经坨了）
8s – 14s（近景 屏幕上密密麻麻的表格一行行往下滚）
14s – 20s（全景 整层办公室只剩头顶这一盏灯）
20s – 27s（特写 手指停在回车键上不动）
27s – 34s（中景 屏幕上的格子开始自己一行行填满）
34s – 40s（近景 人慢慢往后靠进椅背）
40s – 46s（空镜 窗外的天开始泛白）
```

## 二、`drama.parse_timed` 输出（确定性 · 离线 · 不调外网）

`ok=True` · `source=rule-based` · 切出 **8** 个镜头。

```json
{
 "ok": true,
 "source": "rule-based",
 "verdict": {
  "shots": 8,
  "missing": [
   {
    "idx": 1,
    "lack": [
     "运镜",
     "情绪",
     "角色位置"
    ]
   },
   {
    "idx": 2,
    "lack": [
     "运镜",
     "情绪",
     "角色位置"
    ]
   },
   {
    "idx": 3,
    "lack": [
     "运镜",
     "情绪",
     "角色位置"
    ]
   },
   {
    "idx": 4,
    "lack": [
     "运镜",
     "情绪",
     "角色位置"
    ]
   },
   {
    "idx": 5,
    "lack": [
     "运镜",
     "情绪",
     "角色位置"
    ]
   },
   {
    "idx": 6,
    "lack": [
     "运镜",
     "情绪",
     "角色位置"
    ]
   },
   {
    "idx": 7,
    "lack": [
     "运镜",
     "情绪",
     "角色位置"
    ]
   },
   {
    "idx": 8,
    "lack": [
     "运镜",
     "情绪",
     "角色位置"
    ]
   }
  ],
  "dur_sum": 46.0,
  "dur_declared": 46.0,
  "dur_ok": true,
  "complete": false
 },
 "total_dur": 46.0,
 "shots": [
  {
   "idx": 1,
   "t0": 0.0,
   "t1": 3.0,
   "dur": 3.0,
   "title": "特写 凌晨两点还亮着的显示器",
   "shot_size": "特写",
   "camera": "",
   "emotion": "",
   "cues": {
    "shot_size": [
     "特写"
    ],
    "camera": [],
    "emotion": []
   },
   "subject": "",
   "desc": "（特写 凌晨两点还亮着的显示器）",
   "dialogue": ""
  },
  {
   "idx": 2,
   "t0": 3.0,
   "t1": 8.0,
   "dur": 5.0,
   "title": "中景 手边的泡面已经坨了",
   "shot_size": "中景",
   "camera": "",
   "emotion": "",
   "cues": {
    "shot_size": [
     "中景"
    ],
    "camera": [],
    "emotion": []
   },
   "subject": "",
   "desc": "（中景 手边的泡面已经坨了）",
   "dialogue": ""
  },
  {
   "idx": 3,
   "t0": 8.0,
   "t1": 14.0,
   "dur": 6.0,
   "title": "近景 屏幕上密密麻麻的表格一行行往下滚",
   "shot_size": "近景",
   "camera": "",
   "emotion": "",
   "cues": {
    "shot_size": [
     "近景"
    ],
    "camera": [],
    "emotion": []
   },
   "subject": "",
   "desc": "（近景 屏幕上密密麻麻的表格一行行往下滚）",
   "dialogue": ""
  },
  {
   "idx": 4,
   "t0": 14.0,
   "t1": 20.0,
   "dur": 6.0,
   "title": "全景 整层办公室只剩头顶这一盏灯",
   "shot_size": "全景",
   "camera": "",
   "emotion": "",
   "cues": {
    "shot_size": [
     "全景"
    ],
    "camera": [],
    "emotion": []
   },
   "subject": "",
   "desc": "（全景 整层办公室只剩头顶这一盏灯）",
   "dialogue": ""
  },
  {
   "idx": 5,
   "t0": 20.0,
   "t1": 27.0,
   "dur": 7.0,
   "title": "特写 手指停在回车键上不动",
   "shot_size": "特写",
   "camera": "",
   "emotion": "",
   "cues": {
    "shot_size": [
     "特写"
    ],
    "camera": [],
    "emotion": []
   },
   "subject": "",
   "desc": "（特写 手指停在回车键上不动）",
   "dialogue": ""
  },
  {
   "idx": 6,
   "t0": 27.0,
   "t1": 34.0,
   "dur": 7.0,
   "title": "中景 屏幕上的格子开始自己一行行填满",
   "shot_size": "中景",
   "camera": "",
   "emotion": "",
   "cues": {
    "shot_size": [
     "中景"
    ],
    "camera": [],
    "emotion": []
   },
   "subject": "",
   "desc": "（中景 屏幕上的格子开始自己一行行填满）",
   "dialogue": ""
  },
  {
   "idx": 7,
   "t0": 34.0,
   "t1": 40.0,
   "dur": 6.0,
   "title": "近景 人慢慢往后靠进椅背",
   "shot_size": "近景",
   "camera": "",
   "emotion": "",
   "cues": {
    "shot_size": [
     "近景"
    ],
    "camera": [],
    "emotion": []
   },
   "subject": "",
   "desc": "（近景 人慢慢往后靠进椅背）",
   "dialogue": ""
  },
  {
   "idx": 8,
   "t0": 40.0,
   "t1": 46.0,
   "dur": 6.0,
   "title": "空镜 窗外的天开始泛白",
   "shot_size": "空镜",
   "camera": "",
   "emotion": "",
   "cues": {
    "shot_size": [
     "空镜"
    ],
    "camera": [],
    "emotion": []
   },
   "subject": "",
   "desc": "（空镜 窗外的天开始泛白）",
   "dialogue": ""
  }
 ],
 "note": "确定性路径：只切分 + 字面检出，检出不到的字段进 missing，不猜。",
 "declaration": {
  "module": "drama",
  "role": "剧本理解引擎",
  "phase": "接口1 剧本→分镜",
  "action": "parse_timed",
  "impl": "gbt_allinone/drama.py",
  "ok": true,
  "at": "2026-09-21T23:45:06",
  "output": {
   "shots": 8
  },
  "note": "确定性切分（离线）"
 }
}
```

## 三、镜头三契约（`video-pipeline` §1 · 逐镜待填）

§1 要求每个 shot 写清 **为什么这么选**，且 `render` 必须**先读旁白再决定**（不许先选引擎）。
下表是**待填骨架**，不是已完成 —— 缺项由 `parse_timed` 的 `missing` 逐镜点名：

| 镜 | 时长 | 旁白/动作 | `render`（读旁白后定） | `eyeline` 视线 | `depth` 浅/深 | 理由 |
|---|---|---|---|---|---|---|
| 待填 | 待填 | 见上 | 待填 | 待填 | 待填 | 待填 |

> ⚠️ **我不代填。** §1 明写「复制别人的理由 = 失败」，
> 而这些取值必须**先读了旁白**才能定 —— 旁白已在上表口播稿里，取值应由审批时一次定齐。

## 四、预算闸（§3）

**不出预估。** §3 明文：「**未知价格直接失败，不许猜**」。
当前无价格表（无证据等级、无出处），因此按契约**拒绝给出数字**，而不是编一个 $10。

## 五、双人审闸（§6）

| 闸 | 状态 |
|---|---|
| HITL #1 分镜审批 | ⏸ **待主人** —— 没过这道闸不许生成 |
| HITL #2 发布审批 | ⏸ 未到（发布端本工作区未启用） |
