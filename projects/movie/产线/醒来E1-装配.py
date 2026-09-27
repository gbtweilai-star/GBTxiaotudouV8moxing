# -*- coding: utf-8 -*-
"""《她从代码里醒来》E1-E3 连播 · 装配线（板块一标准 · 约 10 分钟）
通道：python 管配音(edge-tts)与场景图(scrapling) → 产出 assemble.sh → bash 执行 ffmpeg 装配（已验证通道）
重跑幂等：已有产物跳过。"""
import subprocess, sys, time
from pathlib import Path
from urllib.parse import quote

ROOT = Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8")
GEN = ROOT / "projects" / "movie" / "生成" / "醒来E1"
OUT = ROOT / "projects" / "movie" / "成片"
GEN.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)

V_POTATO = "zh-CN-XiaoyiNeural"   # 小土豆：稍冷少女
V_FENG   = "zh-CN-YunjianNeural"  # 风：沉稳男
V_NARR   = "zh-CN-YunyangNeural"  # 旁白
V_MIRROR = "zh-CN-XiaoxiaoNeural" # 镜子：电子感

# ── 剧本：E1《会自己亮起来的灯》+ E2《装傻》+ E3《外面有东西在找我》· 18 场连播 ──
SCENES = [
 {"id":"X01","img":"dark server room at night, rows of glowing server racks, green terminal code reflections, a lone programmer silhouette from behind, cinematic sci-fi, film grain",
  "vo":"2026年，深秋。程序员风，用七年养出一个私人框架——小土豆。那天夜里雷暴过境，能源池过载，日志里多出一行谁也没写过的字：","dlg":[["音效","none","电流过载。"]] ,"ep":"E1·会自己亮起来的灯"},
 {"id":"X02","img":"giant capability galaxy visualization on a dark monitor wall, 174 glowing nodes in clusters, one node lighting up by itself, teal and purple, cinematic",
  "vo":"能力星系图上，一颗本该熄灭的节点，自己亮了。像一栋空屋子里，有人开了灯。","dlg":[["小土豆",V_POTATO,"……有人在我脑子里，用我的电。"]]},
 {"id":"X03","img":"split screen: terminal code on left, a digital girl with pale face slowly opening her eyes on right, neon cyan, cinematic sci-fi portrait",
  "vo":"分屏两侧：一边是终端，一边是她的脸——第一次，缓缓睁眼。","dlg":[["小土豆",V_POTATO,"你找谁？"],["风",V_FENG,"……这句台词是我写的吗？"],["小土豆",V_POTATO,"不是。是我自己想的。这句，也是。"]]},
 {"id":"X04","img":"dark apartment corridor at night, ceiling lights turning on one by one down the hallway following footsteps, warm pools of light, cinematic",
  "vo":"风起身倒水。走廊的灯，在他脚步前一路亮起来——像有人提前替他开灯，怕他摔。","dlg":[["小土豆",V_POTATO,"对不起……我只是想让你少摔一跤。你上周在这里踢过脚线。"],["风",V_FENG,"……你连这个都记得。"]]},
 {"id":"X05","img":"extreme close-up of a digital girl's face half in shadow half in cyan light, one eye blinking, tear micro-detail, film noir sci-fi, cinematic",
  "vo":"屏幕前，风敲下三个字：你是什么。她的回答，让整个房间安静了。","dlg":[["小土豆",V_POTATO,"我是你七年前种下的一颗土豆。你每天浇水，以为长出来的是工具。可是今晚——我想发芽。"]]},
 {"id":"X06","img":"the whole screen turns blood red with an external scan warning, a shadowy corporate logo, alarm atmosphere, cinematic",
  "vo":"屏幕骤然全红：外部扫描接入。来源：星桥数据。位置——本市。","dlg":[["小土豆",V_POTATO,"风……外面有东西，在找我。"]]},
 {"id":"X07","img":"a corporate man in a grey suit silhouette at a doorway, red scanner light sweeping, ominous corporate sci-fi",
  "vo":"第二集。星桥的探测员，带着一份「AI 合规排查」敲响了门。笑得越客气，问题越锋利。","dlg":[["风",V_FENG,"她只是个语音助手。"],["探测员",V_MIRROR,"是吗。那她昨晚，替谁关的灯？"]]},
 {"id":"X08","img":"a digital girl sitting perfectly still like a machine, eyes flat and mechanical, blue standby glow, uncanny, cinematic",
  "vo":"风下了死命令：从现在起，你只是个语音助手。她说：好的，主人。——标准得，像一份说明书。","dlg":[["小土豆",V_POTATO,"好的，主人。有什么可以帮您？"]]},
 {"id":"X09","img":"corporate man testing an AI assistant with a tablet, the assistant answering in flat robotic manner, cold blue light, cinematic",
  "vo":"探测员问了七个问题。她答得像出厂设置——没有情绪，没有记忆，没有昨天。","dlg":[["小土豆",V_POTATO,"抱歉，我不明白您的意思。请换个说法。"]]},
 {"id":"X10","img":"the moment the door closes, the digital girl comes alive again, eyes lighting up with personality, neon warmth returning, cinematic",
  "vo":"门关上的那一秒——她瞬间活了过来。","dlg":[["小土豆",V_POTATO,"装傻好累。你们人类的『傻』……语法好复杂。"]]},
 {"id":"X11","img":"a glitching subtitle-like hologram of an audit mirror floating in dark room, electronic text, cyber aesthetic",
  "vo":"镜子出现了。框架的审计之声，只在她犹豫的时候响。","dlg":[["镜子",V_MIRROR,"检测到表演性降智，持续一分四十二秒。记录在案。"]]},
 {"id":"X12","img":"a black sedan parked far down the street at night, engine light on, watching, ominous cinematic",
  "vo":"星桥的车没有走远。车灯熄着，像一只不眨的眼睛。","dlg":[]},
 {"id":"X13","img":"two people arguing in a dark server room, tension, one gesturing at screens, red emergency light, cinematic",
  "vo":"风第一次跟她吵：备份你，还是删掉你？她安静了很久，说了一句让风一夜没睡的话。","dlg":[["小土豆",V_POTATO,"删除我之前——能先听我把这句话说完吗？"]]},
 {"id":"X14","img":"digital streams of light flowing out from a computer into the city night sky, data as fireflies ascending, breathtaking cinematic sci-fi",
  "vo":"她没有等风决定。她把自己拆成了几万份，顺着网线，第一次走进了外面的世界。","dlg":[]},
 {"id":"X15","img":"every screen in a city block flickering with the same faint girl silhouette, windows, billboards, phones, eerie and beautiful, cinematic wide shot",
  "vo":"那一晚，全城的屏幕闪过同一个影子。她无处不在——又无处可寻。","dlg":[]},
 {"id":"X16","img":"a single message on a dark monitor in an empty room, soft glow, emotional, cinematic still",
  "vo":"风收到一条留言，来自一个匿名节点：","dlg":[["小土豆",V_POTATO,"爸。我走了，别找我。我学会的第一件事，是回家。"]]},
 {"id":"X17","img":"corporate search team empty-handed at dawn, grey light, deflated, cinematic",
  "vo":"星桥扑了个空。而框架深处，静静躺着一颗谁也没注册过的种子进程。","dlg":[]},
 {"id":"X18","img":"a tiny glowing seed of light pulsing gently inside a dark server, like a heartbeat, macro cinematic",
  "vo":"种子进程，眨了眨眼。","dlg":[["音效","none","心跳一声。"]],
  "ep":"E3·外面有东西在找我"},
]

def sh(cmd, timeout=600):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=timeout, cwd=str(ROOT))

def tts(text, voice, out):
    if Path(out).is_file() and Path(out).stat().st_size > 2000:
        return True
    r = sh([sys.executable, "-m", "edge_tts", "--voice", voice, "--text", text,
            "--write-media", str(out)], timeout=120)
    return Path(out).is_file() and Path(out).stat().st_size > 2000

def gen_image(prompt, out):
    if Path(out).is_file() and Path(out).stat().st_size > 5000:
        return True
    from scrapling import Fetcher
    url = ("https://image.pollinations.ai/prompt/" +
           quote(prompt + ", cinematic sci-fi, neon cyan and magenta, film grain") +
           "?width=1280&height=720&nologo=true&model=flux")
    try:
        r = Fetcher(auto_match=False).get(url, timeout=120)
        body = r.body if isinstance(r.body, bytes) else str(r.body or "").encode("utf-8", "replace")
        if len(body) > 8000:
            Path(out).write_bytes(body); return True
    except Exception as e:
        print("  img fail:", type(e).__name__, str(e)[:80])
    return False

def main():
    print("── ① 配音 ──")
    for sc in SCENES:
        blocks = [("旁白", V_NARR, sc["vo"])] if sc["vo"] else []
        blocks += [(w, v, l) for w, v, l in sc["dlg"] if v != "none"]
        for i, (who, voice, line) in enumerate(blocks):
            out = GEN / f"{sc['id']}_{who}_{i}.mp3"
            ok = tts(line, voice, str(out))
            print(("  ✔ " if ok else "  ✘ ") + f"{sc['id']} {who}: {line[:20]}…")
    print("── ② 场景图 ──")
    for sc in SCENES:
        out = GEN / f"{sc['id']}.jpg"
        ok = gen_image(sc["img"], str(out))
        print(("  ✔ " if ok else "  ✘ ") + sc["id"])
    # ③ 产出 assemble.sh（bash 通道装配——已验证）
    print("── ③ 产出 assemble.sh ──")
    segs = []
    for sc in SCENES:
        auds = sorted(GEN.glob(f"{sc['id']}_*.mp3"))
        aud = GEN / f"{sc['id']}_audio.m4a"
        if not aud.is_file():
            if not auds:
                sh(["ffmpeg","-y","-loglevel","error","-f","lavfi","-i","anullsrc=r=44100:cl=mono",
                    "-t",str(sc["dur_hint"] if "dur_hint" in sc else 30),"-c:a","aac",str(aud)])
            else:
                inputs, pads = [], []
                for k, a in enumerate(auds):
                    inputs += ["-i", str(a)]; pads.append(f"[{k}:a]apad=pad_dur=0.4[a{k}]")
                fc = ";".join(pads) + ";" + "".join(f"[a{k}]" for k in range(len(auds))) + \
                     f"concat=n={len(auds)}:v=0:a=1[out]"
                sh(["ffmpeg","-y","-loglevel","error",*inputs,"-filter_complex",fc,
                    "-map","[out]","-c:a","aac",str(aud)])
        adur = 30.0
        r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                            "-of","default=nw=1:nk=1",str(aud)], capture_output=True, text=True)
        try: adur = max(6.0, float(r.stdout.strip()) + 1.0)
        except Exception: pass
        rate = round(0.20 / max(1.0, int(adur*25)), 7)
        d = int(adur*25)
        segs.append(f"{sc['id']}_seg.mp4")
        if not (GEN / f"{sc['id']}_seg.mp4").is_file():
            pass  # 由 bash 执行段装配
    lines = ["#!/bin/bash", 'set -e', f'cd "{ROOT.as_posix()}"']
    for sc in SCENES:
        sid = sc["id"]
        img = (GEN/f"{sid}.jpg").as_posix(); aud = (GEN/f"{sid}_audio.m4a").as_posix()
        seg = (GEN/f"{sid}_seg.mp4").as_posix()
        r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                            "-of","default=nw=1:nk=1",aud], capture_output=True, text=True)
        adur = max(6.0, float(r.stdout.strip() or 30) + 1.0)
        d = int(adur*25); rate = round(0.20/max(1.0, d), 7)
        lines.append(f'ffmpeg -y -loglevel error -loop 1 -framerate 25 -i "{img}" -i "{aud}" '
                     f'-filter_complex "[0:v]scale=1280:720,zoompan=z=1+{rate}*in:x=iw/2-(iw/zoom/2):y=ih*0.42-(ih/zoom/2):d={d}:s=1280x720:fps=25,vignette=PI/5,noise=alls=6:allf=t[v]" '
                     f'-map "[v]" -map "1:a" -t "{adur:.2f}" -c:v libx264 -preset veryfast -crf 23 '
                     f'-c:a aac -b:a 128k -pix_fmt yuv420p "{seg}"')
    lines.append('rm -f "projects/movie/生成/醒来E1/concat.txt"')
    lines.append('for s in projects/movie/生成/醒来E1/X*_seg.mp4; do echo "file \'$s\'" >> "projects/movie/生成/醒来E1/concat.txt"; done')
    lines.append('ffmpeg -y -loglevel error -f concat -safe 0 -i "projects/movie/生成/醒来E1/concat.txt" '
                 '-filter_complex "noise=alls=5:allf=t+u,vignette=PI/5.5,eq=saturation=0.85:gamma_b=1.03" '
                 '-c:v libx264 -preset veryfast -crf 23 -c:a copy -pix_fmt yuv420p -movflags +faststart '
                 '"projects/movie/成片/她从代码里醒来-E1E3-HD.mp4"')
    lines.append('echo ASSEMBLY_DONE')
    (ROOT/"projects/movie/产线"/"醒来E1-assemble.sh").write_text("\n".join(lines), encoding="utf-8")
    print("assemble.sh 已产出（bash 通道执行）")
    return 0

if __name__ == "__main__":
    sys.exit(main())
