import os, io, json

print("=" * 60)
print("DeepSeek Harness 资产定位 + 主模型现状")
print("=" * 60)

GBT = r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt"

# 1) Harness 相关 caps
print("\n[1] Harness/DeepSeek 相关 caps:")
caps_dir = os.path.join(GBT, "caps")
for name in sorted(os.listdir(caps_dir)):
    if any(k in name.lower() for k in ["harness", "deepseek", "ecc"]):
        d = os.path.join(caps_dir, name)
        n = sum(len(fs) for _, _, fs in os.walk(d))
        print(f"  {name} ({n} 文件)")

# 2) brain 里的 deepseek/harness 模块
print("\n[2] brain 里的 DeepSeek/Harness 模块:")
brain = os.path.join(GBT, "brain")
for f in sorted(os.listdir(brain)):
    if any(k in f.lower() for k in ["deepseek", "harness", "ecc", "llm"]):
        print(f"  {f} ({os.path.getsize(os.path.join(brain, f))}B)")

# 3) devoured_ecc 的内容结构（Harness OS 主体）
ecc = os.path.join(caps_dir, "devoured_ecc")
if os.path.isdir(ecc):
    print("\n[3] devoured_ecc 目录结构:")
    for root, dirs, files in os.walk(ecc):
        rel = os.path.relpath(root, ecc)
        if rel.count(os.sep) > 2:
            dirs[:] = []
            continue
        for f in files:
            print(f"  {os.path.join(rel, f)}")

# 4) harness_fusion 的说明
hf = os.path.join(caps_dir, "harness_fusion", "capability.json")
if os.path.isfile(hf):
    d = json.load(open(hf, encoding="utf-8"))
    print("\n[4] harness_fusion:")
    print(f"  desc: {d.get('description', '')[:150]}")
    print(f"  actions: {list(d.get('actions', {}).keys())[:15]}")

# 5) 主模型配置现状（llm_client / deepseek_bridge / auth_config）
print("\n[5] 主模型配置线索:")
for p in [os.path.join(GBT, "auth_config.json"),
          os.path.join(GBT, "brain", "llm_client.py"),
          os.path.join(GBT, "brain", "deepseek_bridge.py")]:
    if os.path.isfile(p):
        sz = os.path.getsize(p)
        print(f"  ✓ {os.path.basename(p)} ({sz}B)")
        if p.endswith("auth_config.json"):
            try:
                cfg = json.load(open(p, encoding="utf-8"))
                # 只打印结构不打印密钥
                def mask(o, depth=0):
                    if isinstance(o, dict):
                        return {k: ("***" if any(s in k.lower() for s in ["key", "token", "secret"]) else mask(v, depth+1)) for k, v in o.items()}
                    if isinstance(o, list):
                        return [mask(x, depth+1) for x in o[:5]]
                    return o
                print(json.dumps(mask(cfg), ensure_ascii=False, indent=1)[:1200])
            except Exception as e:
                print(f"    读取失败: {e}")
