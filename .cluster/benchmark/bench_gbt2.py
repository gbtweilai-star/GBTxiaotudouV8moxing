"""修正版: key 从 .env 程序化读取（不手抄）"""
import json, os, sys, time, urllib.request

def _load_key():
    for ln in open(r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt\.env", encoding="utf-8"):
        s = ln.strip()
        if s.startswith("ZHIPU_API_KEY") and "=" in s and not s.startswith("#"):
            v = s.split("=", 1)[1].split("#")[0].strip()
            if len(v) >= 40:
                return v
    return ""

KEY = _load_key()
print(f"key 加载: 长度{len(KEY)}, 尾部 {KEY[-6:]}, 纯ASCII: {KEY.isascii()}")

API = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
sys.path.insert(0, r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt\brain")
from engineering_details import review_checklist

def glm_chat(prompt, system="", max_tokens=3000, thinking=True, retries=4):
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    body = {"model": "glm-4.7-flash", "messages": msgs, "max_tokens": max_tokens,
            "thinking": {"type": "enabled" if thinking else "disabled"}}
    for attempt in range(retries):
        req = urllib.request.Request(API, data=json.dumps(body).encode(),
            method="POST", headers={"Content-Type": "application/json",
                                    "Authorization": "***" + KEY})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.loads(r.read())
            return (d.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")[:100]
            try:
                code = json.loads(err).get("error", {}).get("code", "")
            except Exception:
                code = ""
            if code in ("1305", "1302") and attempt < retries - 1:
                time.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError(f"HTTP {e.code} {err}")

TASKS = {
    "task1_金额陷阱": "实现一个 Python 购物车结算函数 settle_cart(items, coupon)：items=[{name, price(元,float), qty}]，coupon 是折扣率(如0.85)。要求金额计算精确到分、四舍五入规则明确、输出总金额（分）。只用标准库。请给出完整代码和3个测试用例（含浮点陷阱用例）。",
    "task2_支付幂等": "实现一个 Python 支付回调处理类 PaymentCallbackHandler：要求 1)同一笔订单的重复回调只扣款一次(幂等) 2)高并发下线程安全 3)第三方回调可能乱序重发。模拟存储即可。给出完整代码并说明如何防止重复扣款。",
    "task3_接口限流": "实现一个 Python 令牌桶限流器 TokenBucketRateLimiter：要求 1)线程安全 2)支持突发流量 3)try_acquire(n) 原子语义 4)说明该方案与固定窗口/滑动窗口的优劣。完整代码+并发测试示例。",
}

print("=" * 62)
print("GBT小土豆V8 (GLM-4.7-Flash + 工程检查单) 编程实测")
print("=" * 62)

results = {}
for name, task in TASKS.items():
    cl = review_checklist(task)
    checklist_txt = "\n".join("- " + c for c in cl["checklist"][:8])
    system = "你是GBT小土豆V8，全栈编程AI。作答时严格遵守以下工程检查单：\n" + checklist_txt
    t0 = time.time()
    try:
        ans = glm_chat(task, system=system, thinking=True)
        dt = time.time() - t0
        results[name] = {"answer": ans, "time_s": round(dt, 1)}
        print(f"\n✅ {name}: {dt:.0f}s, {len(ans)}字")
        print(f"   {ans[:80]}…")
    except Exception as e:
        results[name] = {"answer": "", "time_s": round(time.time()-t0, 1), "error": str(e)[:120]}
        print(f"\n❌ {name}: {str(e)[:100]}")

with open(r"C:\Users\ADMIN\Desktop\GBT小土豆V8\.cluster\benchmark\gbt_answers.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)
print("\n答卷已存 gbt_answers.json")
