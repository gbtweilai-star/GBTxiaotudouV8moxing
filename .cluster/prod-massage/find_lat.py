import io
# 关键疑点: 慢指令 dispatch 秒回(0.0s)——dispatch 是异步入队, 2500ms 在后台跑
# 熔断判定在守护进程侧: 平均延迟窗口在指令"完成"时才记录
# 检查守护进程的熔断触发点: 7) 熔断期新指令没被限流 → 说明 2.6s 等待后平均延迟仍未超 100ms 阈值
# 可能在 5s 总等待期间 2500ms 已完成且窗口(40样本)被稀释, 或者延迟只在特定路径记录
# 找守护进程代码里的 latencies 记录点
src = io.open(r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt\caps\universal_plugin\run.py", encoding="utf-8", errors="replace").read()
import re
for m in re.finditer(r"latencies\.(append|extend|clear)", src):
    i = m.start()
    seg = src[max(0,i-300):i+200]
    print(f"@{i}:")
    print(seg)
    print("---")
