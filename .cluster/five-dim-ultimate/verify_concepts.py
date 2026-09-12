import io, os, json

BRAIN = r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt\brain"

# 50 概念 → brain 层候选映射（含备选）
concept_map = {
    "推理": ["reasoning_brain", "deep_reasoner"],
    "编程": ["code_generator"],
    "设计": [],  # cap 层 design_brain
    "视觉": ["visual_cortex", "omni_vision", "vision_dispatch"],
    "认知": ["cognition", "deep_cognition", "cognition_cortex"],
    "进化": ["self_evolve", "autonomous_enhance"],
    "镜像": ["mirror_fusion", "mirror_gate"],
    "审计": ["audit_trail", "full_audit", "deploy_audit"],
    "意图": ["intent_broker"],
    "触手": ["action_tentacle", "neural_tentacle", "omni_tentacle", "vision_tentacle",
             "devour_tentacle", "navigation_tentacle", "evidence_tentacle", "tentacle_reasoner",
             "tentacle_transmission", "tentacle_bridge", "tentacle_brain_scan"],
    "黑客": ["hacker_brain"],
    "本体感知": ["neural_proprioception", "perception_watch", "unified_health_pulse"],
    "鞭策": ["self_discipline_brain"],
    "灵感": ["inspiration_brain"],
    "循环": ["autonomous_loop", "recurrent_dynamics"],
    "Gaia": ["gaia_gateway"],
    "元认知": ["meta_cognition_brain", "self_reflection"],
    "直觉": ["intuition_brain"],
    "审美": ["aesthetic_brain"],
    "记忆": ["memory_brain", "memory_consolidation", "memory_cortex", "visual_memory", "recall_brain"],
    "时序": ["temporal_brain", "temporal_processing"],
    "社交": ["social_brain"],
    "学习": ["learning_brain", "biological_learning"],
    "策略": ["strategy_brain"],
    "风险": ["risk_brain", "threat_detection"],
    "执行": ["execution_brain", "executor", "execution_router", "brain_execution_core"],
    "解释": ["explanation_brain", "explanation_engine"],
    "想象": ["imagination_brain"],
    "价值": ["value_brain"],
    "状态": ["state_brain"],
    "平衡": ["balance_brain"],
    "模式": ["pattern_brain"],
    "情绪": ["emotion_brain", "emotion_cortex"],
    "汇报": ["report_brain"],
    "建议": ["advice_brain"],
    "任务": ["task_brain"],
    "技能": ["skill_brain"],
    "预测": ["predict_brain"],
    "校准": ["calibrate_brain"],
    "图谱": ["graph_brain", "mind_map", "topo_brain"],
    "决策记录": ["journal_brain", "work_journal", "audit_trail"],
    "评估": ["evaluate_brain", "review_brain", "cross_validation"],
    "合成": ["synthesis_brain"],
    "协调": ["orchestrator", "orchestrator_brain"],
    "恢复": ["recovery_brain", "repair_watchdog"],
    "洞察": ["insight_brain"],
    "常识": ["common_sense_brain"],
    "启发": ["heuristic_brain"],
    "探索": ["exploration_engine", "explore_brain", "curiosity_engine"],
    "意识": ["mind_brain", "sync_body_mind", "unified_body_mind", "meta_cognition_brain"],
}

def peek_doc(name):
    p = os.path.join(BRAIN, name + ".py")
    if not os.path.isfile(p):
        return None, None
    src = io.open(p, encoding="utf-8", errors="replace").read()
    doc = ""
    if '"""' in src:
        i = src.find('"""')
        j = src.find('"""', i + 3)
        if j > 0:
            doc = " ".join(src[i+3:j].split())[:60]
    return doc, len(src)

print("=" * 70)
print("50 概念 × brain 层全量验证")
print("=" * 70)
rows = []
hit_direct, hit_cap, no_match = 0, 0, 0
cap_layer_fallback = {"设计": ["design_brain(cap)"]}

for concept, names in concept_map.items():
    found = []
    for n in names:
        doc, size = peek_doc(n)
        if doc is not None:
            found.append((n, doc, size))
    if found:
        hit_direct += 1
        primary = found[0]
        rows.append((concept, "brain层", primary[0], primary[1], primary[2]))
    elif concept in cap_layer_fallback:
        hit_cap += 1
        rows.append((concept, "cap层", cap_layer_fallback[concept][0], "调度层能力", 0))
    else:
        no_match += 1
        rows.append((concept, "缺失", "-", "-", 0))

print(f"\n直接命中(brain层): {hit_direct}/50 | cap层兜底: {hit_cap} | 无对应: {no_match}\n")
print(f"{'概念':<6} {'层':<6} {'主模块':<24} {'说明'}")
print("-" * 100)
for concept, layer, name, doc, size in rows:
    sz = f"{size}B" if size else "-"
    print(f"{concept:<6} {layer:<6} {name:<24} {doc} [{sz}]")

# 附加：用户说"不止这么多"——统计 brain 层全集
all_brains = [f[:-3] for f in os.listdir(BRAIN) if f.endswith(".py") and f != "__init__.py"]
print(f"\nbrain 层模块总数: {len(all_brains)}")
extra = [b for b in all_brains if b not in {n for names in concept_map.values() for n in names}]
print(f"50概念之外还有 {len(extra)} 个: {', '.join(sorted(extra)[:40])}")

out = r"C:\Users\ADMIN\Desktop\GBT小土豆V8\.cluster\five-dim-ultimate\concept_alignment_final.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump({"rows": [list(r) for r in rows], "brain_total": len(all_brains),
               "hit_direct": hit_direct, "hit_cap": hit_cap, "no_match": no_match},
              f, indent=2, ensure_ascii=False)
print(f"\n已保存: {out}")
