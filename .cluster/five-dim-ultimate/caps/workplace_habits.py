"""
做人习惯系统 (Workplace Habits) — GBT小土豆V8

根治三大低级失误：
1. 文件写错目录（带空格变体目录陷阱）
2. 写完不验证（说写了实际没写/写歪了）
3. 交付前不点数（缺件交付）

习惯1 开工认门牌：任何写操作前，先确认自己在唯一权威工作区
习惯2 写完必回读：写入后立即验证文件存在且非空
习惯3 交付前点数：列交付清单，逐项验存在，缺一件就报警
习惯4 变体雷达：定期扫描桌面变体目录（带空格/错字），发现即报告
"""
import hashlib
import json
import os
import time
from typing import Dict, List, Optional, Tuple

CANONICAL_WORKSPACE = r"C:\Users\ADMIN\Desktop\GBT小土豆V8"
MARKER_FILES = ["AGENTS.md", "SOUL.md", "MEMORY.md"]
VARIANT_PATTERNS = ["GBT 小土豆", "GBT小土豆 V8", "GBT 小土豆V8", "GBT小土豆V8 "]


class WorkplaceHabits:
    """做人习惯：认门牌、回读验证、交付点数、变体雷达"""

    def __init__(self, workspace: str = CANONICAL_WORKSPACE):
        self.workspace = workspace
        self.mistake_log: List[Dict] = []

    # ---------- 习惯1：开工认门牌 ----------

    def verify_workspace(self) -> Dict:
        """确认这是唯一权威工作区（有 SOUL/AGENTS/MEMORY 三件套 + .cluster）"""
        checks = {m: os.path.isfile(os.path.join(self.workspace, m))
                  for m in MARKER_FILES}
        checks['.cluster'] = os.path.isdir(os.path.join(self.workspace, '.cluster'))
        ok = all(checks.values())
        return {'status': 'verified' if ok else 'wrong_place',
                'workspace': self.workspace, 'checks': checks}

    def guard_path(self, target: str) -> Tuple[bool, str]:
        """写操作前的路径守卫：目标必须在权威工作区内，否则拦截"""
        target_abs = os.path.abspath(target)
        ws_abs = os.path.abspath(self.workspace)
        if target_abs.lower().startswith(ws_abs.lower() + os.sep):
            return True, target_abs
        # 检测是否是变体目录陷阱
        for pat in VARIANT_PATTERNS:
            if pat in target_abs:
                self.mistake_log.append({
                    'time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'variant_trap_blocked',
                    'target': target_abs, 'pattern': pat})
                return False, (f"拦截：目标疑似变体目录（含'{pat}'），"
                               f"权威工作区是 {ws_abs}")
        self.mistake_log.append({'time': time.strftime('%Y-%m-%d %H:%M:%S'),
                                 'type': 'outside_workspace_blocked',
                                 'target': target_abs})
        return False, f"拦截：目标在工作区外（{ws_abs}）: {target_abs}"

    # ---------- 习惯2：写完必回读 ----------

    def write_verified(self, path: str, content: str, encoding: str = 'utf-8') -> Dict:
        """带验证的写入：守卫→写入→回读→哈希比对→大小确认"""
        ok, msg = self.guard_path(path)
        if not ok:
            return {'status': 'blocked', 'message': msg}

        os.makedirs(os.path.dirname(os.path.abspath(path)) or '.', exist_ok=True)
        with open(path, 'w', encoding=encoding, newline='') as f:
            f.write(content)

        # 回读验证
        if not os.path.isfile(path):
            return {'status': 'failed', 'message': f'写入后文件不存在: {path}'}
        with open(path, 'r', encoding=encoding) as f:
            readback = f.read()
        size = os.path.getsize(path)
        digest = hashlib.md5(readback.encode(encoding)).hexdigest()[:10]
        match = readback == content
        return {'status': 'success' if match else 'corrupted',
                'path': os.path.abspath(path), 'size': size,
                'md5': digest, 'match': match,
                'message': '写入并回读一致' if match else '回读不一致！'}

    # ---------- 习惯3：交付前点数 ----------

    def checklist(self, deliverables: List[str]) -> Dict:
        """交付点数：逐项验证存在+非空，缺件报警"""
        items = []
        for d in deliverables:
            exists = os.path.isfile(d)
            size = os.path.getsize(d) if exists else 0
            items.append({'path': d, 'exists': exists,
                          'non_empty': size > 0, 'size': size})
        missing = [i['path'] for i in items if not (i['exists'] and i['non_empty'])]
        return {'status': 'all_present' if not missing else 'missing_items',
                'missing': missing, 'items': items,
                'count_ok': len(items) - len(missing), 'count_total': len(items)}

    # ---------- 习惯4：变体雷达 ----------

    def variant_radar(self) -> Dict:
        """扫描桌面上的变体目录（带空格/易混淆命名）"""
        desktop = os.path.dirname(self.workspace)  # Desktop
        variants = []
        for name in os.listdir(desktop):
            full = os.path.join(desktop, name)
            if not os.path.isdir(full):
                continue
            base = os.path.basename(self.workspace)
            if name != base and ('GBT' in name and '土豆' in name):
                n_files = sum(len(fs) for _, _, fs in os.walk(full))
                variants.append({'name': name, 'path': full, 'files': n_files})
        return {'status': 'clean' if not variants else 'variants_found',
                'canonical': self.workspace, 'variants': variants}

    # ---------- 汇总 ----------

    def habit_report(self) -> Dict:
        """四习惯一键自检"""
        return {'workspace': self.verify_workspace(),
                'variants': self.variant_radar(),
                'mistakes_blocked': len(self.mistake_log),
                'mistake_log': self.mistake_log[-10:]}


if __name__ == '__main__':
    print('=' * 64)
    print('做人习惯系统 · 自检')
    print('=' * 64)
    h = WorkplaceHabits()

    r1 = h.verify_workspace()
    print(f"\n[习惯1] 认门牌: {r1['status']}")
    for k, v in r1['checks'].items():
        print(f"   {'✓' if v else '✗'} {k}")

    # 演示拦截变体目录
    ok, msg = h.guard_path(r"C:\Users\ADMIN\Desktop\GBT 小土豆 V8\.cluster\x\y.py")
    print(f"\n[习惯1+] 变体目录拦截测试: {'✅ 已拦截' if not ok else '❌ 没拦住'}")
    print(f"   {msg}")

    ok2, msg2 = h.guard_path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8\.cluster\five-dim-ultimate\habits_test.tmp")
    print(f"   正常路径放行: {'✅' if ok2 else '❌'}")

    # 带验证写入
    r2 = h.write_verified(r"C:\Users\ADMIN\Desktop\GBT小土豆V8\.cluster\five-dim-ultimate\habits_test.tmp",
                          "做人习惯：写完必回读。" * 10)
    print(f"\n[习惯2] 写完回读: {r2['status']} | 大小 {r2.get('size')}B | md5 {r2.get('md5')} | 一致 {r2.get('match')}")

    # 交付点数
    r3 = h.checklist([
        r"C:\Users\ADMIN\Desktop\GBT小土豆V8\.cluster\five-dim-ultimate\caps\brain_executive.py",
        r"C:\Users\ADMIN\Desktop\GBT小土豆V8\.cluster\five-dim-ultimate\caps\dimension_sync.py",
        r"C:\Users\ADMIN\Desktop\GBT小土豆V8\.cluster\five-dim-ultimate\multibrain_bridge.py",
        r"C:\Users\ADMIN\Desktop\GBT小土豆V8\.cluster\five-dim-ultimate\不存在的文件.md",
    ])
    print(f"\n[习惯3] 交付点数: {r3['count_ok']}/{r3['count_total']} 就位")
    for i in r3['items']:
        mark = '✓' if i['exists'] and i['non_empty'] else '✗ 缺件'
        print(f"   {mark} {os.path.basename(i['path'])} ({i['size']}B)")

    # 变体雷达
    r4 = h.variant_radar()
    print(f"\n[习惯4] 变体雷达: {r4['status']}")
    if r4['variants']:
        for v in r4['variants']:
            print(f"   ⚠ {v['name']} ({v['files']} 文件)")
    else:
        print("   桌面无变体目录（GBT小土豆 与 GBT小土豆V8 是合法并存的历史版本）")

    # 清理测试文件
    tp = r"C:\Users\ADMIN\Desktop\GBT小土豆V8\.cluster\five-dim-ultimate\habits_test.tmp"
    if os.path.isfile(tp):
        os.remove(tp)
        print("\n测试临时文件已清理")

    print('\n' + '=' * 64)
    print('做人习惯系统自检完成：认门牌/拦截变体/回读验证/交付点数/变体雷达 全部就绪')
