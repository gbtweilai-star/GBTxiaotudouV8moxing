import subprocess, os, json

print("=" * 56)
print("本机硬件与资产盘点（数字人可行性）")
print("=" * 56)

# 1) GPU
r = subprocess.run(["powershell", "-c",
    "Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion | Format-List"],
    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
print("\n[GPU]")
print(r.stdout[:800])

# 2) CPU/内存
r2 = subprocess.run(["powershell", "-c",
    "Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors | Format-List; Get-CimInstance Win32_ComputerSystem | Select-Object @{N='TotalRAM_GB';E={[math]::Round($_.TotalPhysicalMemory/1GB,1)}} | Format-List"],
    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
print("[CPU/内存]")
print(r2.stdout[:600])

# 3) 已有可复用资产
print("[本机已有资产]")
GBTV8 = r"C:\Users\ADMIN\Desktop\GBT小土豆V8"
assets = {
    "五维合一系统(脑眼耳嘴手)": GBTV8 + r"\.cluster\five-dim-ultimate",
    "万能插(能力调度总线)": r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt\caps\universal_plugin",
    "voice_speak(TTS能力)": r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt\caps\voice_speak",
    "gbt_brain MCP(539能力)": r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt\brain\nexus.py",
    "Live2D相关": GBTV8 + r"\live2d",
}
for name, p in assets.items():
    exists = os.path.exists(p)
    if exists and os.path.isdir(p):
        n = sum(len(fs) for _, _, fs in os.walk(p))
        print(f"  {'✓' if exists else '✗'} {name}: {n} 个文件")
    else:
        print(f"  {'✓' if exists else '✗'} {name}: {'存在' if exists else '不存在'}")

# 4) Python 包环境（渲染相关）
r4 = subprocess.run(["pip", "list"], capture_output=True, text=True,
                    encoding="utf-8", errors="replace", timeout=90)
pkgs = r4.stdout or ""
print("\n[Python 渲染/AI 包检测]")
for pkg in ["PyQt5", "PyQt6", "PySide2", "PySide6", "live2d", "live2d-py", "numpy",
            "requests", "opencv", "torch", "openai", "zhipuai", "websockets"]:
    found = pkg.lower() in pkgs.lower()
    print(f"  {'✓' if found else '✗'} {pkg}")

# 5) 桌面分辨率（全息面板设计用）
r5 = subprocess.run(["powershell", "-c",
    "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::AllScreens | ForEach-Object { $_.Bounds } | Format-List"],
    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
print("\n[显示器]")
print(r5.stdout[:500])
