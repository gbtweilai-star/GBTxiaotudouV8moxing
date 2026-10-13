# -*- coding: utf-8 -*-
"""三大自动化 · 影视职业**逐岗覆盖判据件**（不起卡、不出网、不烧钱）。

判什么（三件事必须同时成立，缺一条该岗就报红）：
  ① **档案齐**：职业库 film 分部下有这份档案，且含五段骨架
     （管什么 / 判据 / 可执行清单 / 常见错误 / 验收）；
  ② **在册**（职业面查得到）：`tentacle_equip.professions()` 里能按 division=film 找到它；
  ③ **进语料**：`vaults/self_knowledge/09_film_professions.jsonl` 里有一问一答对应它。

再判两条线级：
  ④ 三大工作流（短剧 14 / 电影 +3 / 音乐 6）要的岗位都在上面 23 个里；
  ⑤ **负对照**：故意查一个不存在的岗位 ⇒ 必须找不到（否则判据是假的）。

跑法：py -3.10 tests/test_film_roles_accept.py
"""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FILM = os.path.join(ROOT, "vaults", "agency_tentacles", "library", "zh", "film")
CORPUS = os.path.join(ROOT, "vaults", "self_knowledge", "09_film_professions.jsonl")

# 三大工作流要的岗位（中文名 → 档案文件名）
LINES = {
    "AI短剧": ["编剧", "分镜师", "选角/形象", "表演指导", "摄影指导（运镜）", "灯光", "美术（场景与造型）",
              "剪辑（剪点与节奏）", "调色（影调与统一）", "字幕", "封面/缩略图", "声音设计", "发布投放", "平台合规"],
    "AI电影": ["编剧", "分镜师", "导演（分镜与节奏）", "摄影指导（运镜）", "灯光", "美术（场景与造型）",
              "选角/形象", "表演指导", "剪辑（剪点与节奏）", "调色（影调与统一）", "声音设计", "VFX/合成", "制片/场记"],
    "AI音乐": ["作词", "编曲", "作曲/配乐", "渲染操作（ACE-Step）", "混音/母带", "音乐版权"],
}
BONES = ("管什么", "判据", "可执行清单", "常见错误", "验收")


def read_roles():
    """现读 film 分部：{中文名: 正文}"""
    out = {}
    for name in sorted(os.listdir(FILM)):
        if not name.endswith(".md"):
            continue
        text = io.open(os.path.join(FILM, name), encoding="utf-8").read()
        import re
        m = re.search(r"(?m)^name:\s*(.+?)\s*$", text)
        out[(m.group(1).strip() if m else name)] = text
    return out


def catalog_film_names():
    from gbt_allinone.tentacle_equip import professions
    d = professions("zh")
    return {r.get("name") for r in (d.get("professions") or []) if r.get("division") == "film"}, d


def corpus_names():
    got = set()
    for line in io.open(CORPUS, encoding="utf-8"):
        if line.strip():
            q = json.loads(line)["q"]
            got.add(q.replace("你是「", "").replace("」这个岗位时怎么做？", ""))
    return got


def main():
    roles = read_roles()
    in_cat, cat = catalog_film_names()
    in_corpus = corpus_names()
    reds = []
    print("== 逐岗覆盖（档案 / 在册 / 语料）==")
    for name, text in roles.items():
        miss = [b for b in BONES if b not in text]
        ok_file = not miss
        ok_cat = name in in_cat
        ok_cor = name in in_corpus
        flag = "OK " if (ok_file and ok_cat and ok_cor) else "RED"
        print("  %-4s %-22s 档案%s 在册%s 语料%s %s" % (
            flag, name, "✓" if ok_file else "✗" + "/".join(miss),
            "✓" if ok_cat else "✗", "✓" if ok_cor else "✗", ""))
        if not (ok_file and ok_cat and ok_cor):
            reds.append(name)
    print("\n== 三大工作流岗位覆盖 ==")
    for line, need in LINES.items():
        miss = [n for n in need if n not in roles]
        print("  %-8s 需 %2d 岗 → 缺 %s" % (line, len(need), miss or "无"))
        reds += ["%s:%s" % (line, m) for m in miss]

    # 负对照：不存在的岗位必须查不到
    ghost = "本岗位不存在-负对照"
    neg_ok = (ghost not in roles) and (ghost not in in_cat) and (ghost not in in_corpus)
    print("\n负对照：幽灵岗位「%s」 档案%s 在册%s 语料%s ⇒ %s" % (
        ghost, ghost in roles, ghost in in_cat, ghost in in_corpus, "PASS（查不到，判据是真的）" if neg_ok else "FAIL"))

    print("\n汇总：film 分域在册 %d 岗 · 盘上档案 %d 份 · 语料覆盖 %d 岗 · 红 %d 处"
          % (len(in_cat), len(roles), len(in_corpus & set(roles)), len(reds)))
    return 1 if (reds or not neg_ok) else 0


if __name__ == "__main__":
    raise SystemExit(main())
