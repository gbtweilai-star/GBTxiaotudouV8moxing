import io

f = r"C:\Users\ADMIN\.openclaw-autoclaw\workspace\gbt\caps\penetration_scan\run.py"
raw = open(f, "rb").read()
print(f"修前: {len(raw)}B, 前6字节: {raw[:6]}")
if raw.startswith(b"\xef\xbb\xbf"):
    fixed = raw[3:]
    # 语法验证
    compile(fixed.decode("utf-8", errors="replace"), f, "exec")
    open(f, "wb").write(fixed)
    print(f"✅ BOM 已移除: {len(fixed)}B, 语法验证通过")
else:
    print("无 BOM，检查其他问题")
    try:
        compile(raw.decode("utf-8"), f, "exec")
        print("语法本来就 OK")
    except SyntaxError as se:
        print(f"其他语法错误: {se}")
