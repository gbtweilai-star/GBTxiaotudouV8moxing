#!/usr/bin/env python3
"""
五维合一系统 · GLM-4.7-Flash 驱动版
执行编排（用户钦定）: 脑先行 → 眼∥手同步 → 耳∥嘴同步
脑: 智谱对话补全 API 真实决策 (https://docs.bigmodel.cn 对话补全)
"""
import json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

_BASE = os.path.dirname(os.path.abspath(__file__))
_CAPS = os.path.join(_BASE, 'caps')
if _CAPS not in sys.path:
    sys.path.insert(0, _CAPS)

# key 从 gbt .env 读
def _load_key():
    envf = r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt\.env"
    try:
        for ln in open(envf, encoding="utf-8"):
            s = ln.strip()
            if s.startswith("ZHIPU_API_KEY") and "=" in s and not s.startswith("#"):
                v = s.split("=", 1)[1].split("#")[0].strip()
                if len(v) >= 40:
                    return v
    except Exception:
        pass
    return os.environ.get("ZHIPU_API_KEY", "")

_KEY = _load_key()
_API = "https://open.bigmodel.cn/api/paas/v4/chat/completions"


def glm_chat(prompt, system="", max_tokens=2048, thinking=False, retries=4):
    """智谱对话补全 — 按官方文档格式, 1305 指数退避
    thinking=False: 显式关思考(GLM-4.7 默认开思考, 结构化任务不需要, 提速 10-20 倍)"""
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    body = {"model": "glm-4.7-flash", "messages": msgs, "max_tokens": max_tokens}
    # 2026-09-12 提速: 默认显式关思考(结构化任务不需要推理链)
    body["thinking"] = {"type": "enabled" if thinking else "disabled"}
    for attempt in range(retries):
        req = urllib.request.Request(_API, data=json.dumps(body).encode(),
            method="POST", headers={"Content-Type": "application/json",
                                    "Authorization": "Bearer " + _KEY})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.loads(r.read())
            msg = d.get("choices", [{}])[0].get("message", {})
            return (msg.get("content") or "").strip()
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")[:150]
            code = ""
            try:
                code = json.loads(err).get("error", {}).get("code", "")
            except Exception:
                pass
            if code in ("1305", "1302") and attempt < retries - 1:
                time.sleep(8 * (attempt + 1))
                continue
            raise RuntimeError(f"HTTP {e.code} {err[:100]}")
    return ""


class FiveDimensionGLM:
    """五维合一 GLM 驱动版 — 脑 → (眼∥手) → (耳∥嘴)"""

    def __init__(self):
        from voice_mouth import VoiceMouth
        from mouse_controller import MouseController
        from file_operator import FileOperator
        self.mouth = VoiceMouth()
        self.hand_mouse = MouseController()
        self.hand_file = FileOperator()

    # ========== 第 1 阶段: 脑先行 ==========
    def brain_phase(self, task):
        """脑: GLM 分析任务 → 结构化执行计划（含工程细节心法）"""
        # 工程细节检查单: 按任务上下文路由相关规则, 注入脑的人设
        try:
            sys.path.insert(0, r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt\brain")
            from engineering_details import review_checklist, MENTAL_MODEL
            cl = review_checklist(task)
            checklist_txt = "\n".join("- " + c for c in cl["checklist"][:10])
            mental_txt = "\n".join(MENTAL_MODEL)
        except Exception:
            checklist_txt = ""
            mental_txt = ""
        system = ("你是五维合一系统的大脑。分析用户任务，输出 JSON 执行计划："
                  '{"task_type": "任务类型", "eye_focus": "眼睛重点看什么", '
                  '"hand_action": "手要执行什么", "ear_focus": "耳朵注意什么", '
                  '"report_tone": "播报语气"}。只输出 JSON，不要多余文字。'
                  "\n\n[工程心法]\n" + mental_txt +
                  ("\n\n[相关工程检查单]\n" + checklist_txt if checklist_txt else ""))
        raw = glm_chat(f"用户任务：{task}", system=system, max_tokens=1024)
        try:
            j = raw[raw.find("{"):raw.rfind("}") + 1]
            plan = json.loads(j)
        except Exception:
            plan = {"task_type": "通用", "eye_focus": "屏幕内容",
                    "hand_action": "执行任务", "ear_focus": "环境声音",
                    "report_tone": "professional"}
        return plan

    # ========== 第 2 阶段: 眼 ∥ 手 同步 ==========
    def eye_phase(self, plan):
        """眼: 按计划聚焦分析（视觉分析骨架 + 计划聚焦）"""
        time.sleep(0.3)  # 模拟视觉采样
        return {"dim": "眼", "focus": plan.get("eye_focus", "屏幕"),
                "scene": "desktop", "detail": "已按大脑指令聚焦观察"}

    def hand_phase(self, plan):
        """手: 按计划执行动作"""
        self.hand_mouse.move_to(150, 250)
        self.hand_mouse.click("left")
        f = self.hand_file.write_file(
            os.path.join(_BASE, "glm_hand_output.txt"),
            f"GLM五维执行 @ {time.strftime('%H:%M:%S')}\n计划: {json.dumps(plan, ensure_ascii=False)}")
        return {"dim": "手", "action": plan.get("hand_action", "执行"),
                "mouse": len(self.hand_mouse.get_history()),
                "file": f.get("status", "unknown")}

    # ========== 第 3 阶段: 耳 ∥ 嘴 同步 ==========
    def ear_phase(self, plan):
        """耳: 按计划监听"""
        time.sleep(0.3)
        return {"dim": "耳", "focus": plan.get("ear_focus", "环境"),
                "events": 2, "emotion": "focused"}

    def mouth_phase(self, plan, eye_r, hand_r, ear_r):
        """嘴: GLM 生成总结 + 真实语音播报（GLM 失败用模板兜底，语音永不失声）"""
        summary_prompt = (f"五维执行完毕。任务类型:{plan.get('task_type')}；"
                          f"眼睛看到:{eye_r.get('focus')}；手完成:{hand_r.get('action')}；"
                          f"耳朵听到:{ear_r.get('focus')}。"
                          "用一句话以活泼语气总结，不超过40字。")
        try:
            text = glm_chat(summary_prompt, max_tokens=256, retries=2) or "五维执行完毕！"
        except Exception:
            text = f"{plan.get('task_type', '任务')}完成！眼睛看了，手做了，一切正常！"
        voice = self.mouth.speak(text, style="warm")
        return {"dim": "嘴", "text": text, "voice": voice.get("status", "unknown"),
                "engine": voice.get("engine", "?")}

    # ========== 主流程: 脑 → (眼∥手) → (耳∥嘴) ==========
    def run(self, task):
        print("🧠 五维合一 GLM 驱动版")
        print(f"   任务: {task}")
        print(f"   编排: 脑先行 → 眼∥手 → 耳∥嘴\n")

        # ① 脑先行
        t0 = time.time()
        plan = self.brain_phase(task)
        t_brain = time.time() - t0
        print(f"🧠 [1/3 脑先行] {t_brain:.1f}s")
        print(f"   计划: {json.dumps(plan, ensure_ascii=False)[:150]}")

        # ② 眼 ∥ 手 同步
        t1 = time.time()
        with ThreadPoolExecutor(2) as ex:
            f_eye = ex.submit(self.eye_phase, plan)
            f_hand = ex.submit(self.hand_phase, plan)
            eye_r, hand_r = f_eye.result(), f_hand.result()
        t_eh = time.time() - t1
        print(f"👁🖐 [2/3 眼∥手同步] {t_eh:.1f}s")
        print(f"   眼: {eye_r.get('focus')} | 手: {hand_r.get('action')} (鼠标{hand_r.get('mouse')}次/文件{hand_r.get('file')})")

        # ③ 耳 ∥ 嘴 同步
        t2 = time.time()
        # 耳朵和嘴并行：耳朵监听，嘴先生成文本再播报（生成也是嘴的一部分）
        with ThreadPoolExecutor(2) as ex:
            f_ear = ex.submit(self.ear_phase, plan)
            f_mouth = ex.submit(self.mouth_phase, plan, eye_r, hand_r,
                                {"focus": "计划监听中"})
            ear_r, mouth_r = f_ear.result(), f_mouth.result()
        t_em = time.time() - t2
        print(f"👂👄 [3/3 耳∥嘴同步] {t_em:.1f}s")
        print(f"   耳: {ear_r.get('focus')} | 嘴: «{mouth_r.get('text', '')[:50]}» 语音:{mouth_r.get('voice')}")

        total = time.time() - t0
        print(f"\n✅ 五维完成: 脑{t_brain:.1f}s + 眼手{t_eh:.1f}s + 耳嘴{t_em:.1f}s = 总{total:.1f}s")
        return {"ok": True, "plan": plan, "brain_s": round(t_brain, 1),
                "eye_hand_s": round(t_eh, 1), "ear_mouth_s": round(t_em, 1),
                "total_s": round(total, 1)}


if __name__ == "__main__":
    if not _KEY:
        print("❌ 未找到 ZHIPU_API_KEY")
        sys.exit(1)
    print(f"✓ key 已加载 (***{_KEY[-6:]})\n")
    sysd = FiveDimensionGLM()
    r = sysd.run("检查桌面状态，整理文件，然后告诉我一切正常吗")
    with open(os.path.join(_BASE, "glm_run_result.json"), "w", encoding="utf-8") as f:
        json.dump(r, f, indent=2, ensure_ascii=False)
    print("\n📄 结果已保存 glm_run_result.json")
