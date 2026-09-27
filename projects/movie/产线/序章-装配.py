# -*- coding: utf-8 -*-
"""《末班义庄》序章 · 10 分钟声画合成装配线
真产线：剧本(内嵌) → edge-tts 配音 → pollinations 场景图(scrapling 抓取) → ffmpeg 逐场装配 → 全片做旧 → 1080p 成片
重跑：python "projects/movie/产线/序章-装配.py"（幂等：已有产物跳过）"""
import json, subprocess, sys, time
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[3]   # projects/movie/产线/ → 仓根（此前少跳一级，产物全进了幽灵目录）
GEN = ROOT / "projects/movie/生成/序章"
OUT = ROOT / "projects/movie/成片"
GEN.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)

# ── 剧本：14 场（vo=旁白；dlg=[角色,voice,台词]；img=场景图英文 prompt；reuse=复用已有图）──
SCENES = [
 {"id":"S01","dur_hint":45,"img":"1980s Hong Kong mortuary hall interior in black and white, a row of old coffins, dim oil lamps, hanging bell, old film grain",
  "vo":"1986年，南方，福安义庄。这间屋子替穷人守了四十年的死人。老道长临终前，把三条规矩刻在了门框上：一，夜里听见敲门，别应。二，尸体脸上落了纸，别揭。三——","dlg":[]},
 {"id":"S02","dur_hint":35,"img":"an old ghost-summoning bell hanging on the door frame of an old Chinese mortuary, weathered bronze, night wind, black and white old film look",
  "vo":"三，我死之后，把门关好。铃，就挂在这扇门上。四十年，没人再敢摇它。","dlg":[]},
 {"id":"S03","dur_hint":50,"img":"the gate of an old Chinese mortuary in a modern urban village at night, a big red demolition character poster on the wall, a young man holding a phone livestreaming, distant neon lights",
  "vo":"四十年后。2026年，城中村拆迁在即。全市最后一间义庄还开着门——因为穷人的体面，殡仪馆不收。守夜的人，叫陈糯米。网管转行，直播糊口。爷爷的规矩，他只记得一半。","dlg":[["糯米","zh-CN-YunxiNeural","家人们，这就是全市最后一间义庄，我爷爷守了四十年。明天拆——今天晚上，我陪它守最后一班岗。"]]},
 {"id":"S04","dur_hint":45,"img":"dim interior of an old Chinese mortuary hall, two rows of coffin benches, pale flickering fluorescent light, dust in air, empty","reuse":"A2-福安堂夜景-初版.jpg",
  "vo":"规矩他记得一半：夜里听见敲门，别应。尸体脸上落了纸，别揭。第三条，爷爷没来得及教。弹幕说他装神弄鬼。只有他自己知道，这屋里……有时候是真的冷。","dlg":[]},
 {"id":"S05","dur_hint":38,"img":"close-up of an old wooden door of a Chinese mortuary at deep night, pitch black outside, iron door knocker, oppressive horror atmosphere",
  "vo":"深夜十一点四十七分。敲门声来了。","dlg":[["音效","none","咚。咚。咚。"]]},
 {"id":"S06","dur_hint":42,"img":"a cardboard box on the ground outside an old Chinese mortuary door at night, relocation compensation documents inside, flashlight beam, eerie",
  "vo":"门开了。没有人。地上一个纸箱——拆迁办的迁移补偿协议，签收栏是空的。可福安堂，根本不在拆迁名单上。","dlg":[["糯米","zh-CN-YunxiNeural","家人们……送协议的，敲什么门啊？"]]},
 {"id":"S07","dur_hint":55,"img":"a covered corpse slowly sitting up on a mortuary bed, a pair of black cloth shoes floating in mid-air, dust in candlelight, horror close-up","reuse":"B2-布鞋直跳-关键镜头-1986版.jpg",
  "vo":"回身。停尸床上，白布下的老熟人——坐起来了。三十年前，爷爷没能送走的那一位。","dlg":[]},
 {"id":"S08","dur_hint":42,"img":"close-up of a Qing dynasty official robe jiangshi vampire head, yellow talisman paper covering the face, blank white eyes, candlelight on the face, horror","reuse":"B1-僵尸正面-锁脸-1986版.jpg",
  "vo":"直播信号，断得干干净净。三万人的直播间，黑屏之前最后一帧——是那张脸，转向了镜头。","dlg":[]},
 {"id":"S09","dur_hint":50,"img":"a black ink line stretched horizontally across the doorway of an old Chinese mortuary, a hopping vampire bouncing back from the line, dynamic 1980s Hong Kong horror action",
  "vo":"千钧一发。一道墨线，横空拉起。僵尸撞线，弹回三步——爷爷笔记本里画过的那条线，真的有牙。","dlg":[]},
 {"id":"S10","dur_hint":48,"img":"an old Taoist master leaning on the door frame holding an old wine gourd, drunk but sharp eyes, 1980s Hong Kong jiangshi film Taoist priest look",
  "vo":"门口，站着一个人。酒壶，道袍，睡没睡醒的眼神。","dlg":[["秋师父","zh-CN-YunjianNeural","直播的。三十七年了，这行的入门仪式，都变成直播了。"],["糯米","zh-CN-YunxiNeural","您……哪位？"],["秋师父","zh-CN-YunjianNeural","你爷爷的师兄。棺材钱还没结——现在，连人带货，都是你的了。"]]},
 {"id":"S11","dur_hint":45,"img":"an old worn notebook open under candlelight, yellowed pages, fountain pen handwriting, hand-drawn talisman sketches",
  "vo":"爷爷的笔记本，压在停尸床底下。第一页不是符，不是咒——是一句人话：","dlg":[["旁白","zh-CN-YunyangNeural","「糯米，如果这些东西醒了，别怕。它们大多数，只是想回家。」"]]},
 {"id":"S12","dur_hint":42,"img":"close-up of a yellowed talisman paper and an old black-and-white photograph of two young Taoist priests standing side by side at an old mortuary gate",
  "vo":"最后一页，夹着一张照片：两个年轻的道长，并肩站在福安堂门口。其中一个，是爷爷。另一个，秋师父到今天都不肯提。","dlg":[]},
 {"id":"S13","dur_hint":45,"img":"a blood-red full moon hanging over old city rooftops, silhouette of a mortuary hall roof, rolling dark clouds, ominous",
  "vo":"而城外，血月升起来了。笔记本的最后一行，墨迹发抖：血月之夜，师兄归。有人，来接他走了。","dlg":[]},
 {"id":"S14","dur_hint":48,"img":"night wide shot of an old Chinese mortuary hall, one single lit window like a candle in the dark, movie poster atmosphere",
  "vo":"规矩第三条，今天补全了。把门关好——门里门外，都得有人守。《末班义庄》，序章。","dlg":[["音效","none","咚。咚。咚。"]]},
]

def sh(cmd, timeout=600):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=timeout, cwd=str(ROOT))

def tts(text, voice, out, rate="-4%"):
    if Path(out).is_file() and Path(out).stat().st_size > 2000:
        return True
    r = sh([sys.executable, "-m", "edge_tts", "--voice", voice, "--rate", rate,
            "--text", text, "--write-media", str(out)], timeout=120)
    return Path(out).is_file() and Path(out).stat().st_size > 2000

def audio_dur(p):
    r = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=nw=1:nk=1", str(p)], timeout=60)
    try: return float(r.stdout.strip())
    except Exception: return 0.0

def gen_image(prompt, out):
    """场景图：scrapling Fetcher 抓取（框架验收过的抓取件，自带公网边界）。"""
    if Path(out).is_file() and Path(out).stat().st_size > 5000:
        return True
    from scrapling import Fetcher
    url = ("https://image.pollinations.ai/prompt/" +
           quote(prompt + ", 1980s Hong Kong horror film, heavy film grain, cinematic") +
           "?width=1920&height=1080&nologo=true")
    try:
        r = Fetcher(auto_match=False).get(url, timeout=120)
        body = r.body if isinstance(r.body, bytes) else str(r.body or "").encode("utf-8", "replace")
        if len(body) > 8000:
            Path(out).write_bytes(body); return True
    except Exception as e:
        print("  img fail:", type(e).__name__, str(e)[:80])
    return False

def main():
    print("── ① 配音合成 ──")
    for sc in SCENES:
        blocks = [("旁白", "zh-CN-YunyangNeural", sc["vo"])] if sc["vo"] else []
        blocks += [(w, v, l) for w, v, l in sc["dlg"] if v != "none"]
        for i, (who, voice, line) in enumerate(blocks):
            out = GEN / f"{sc['id']}_{who}_{i}.mp3"
            ok = tts(line, voice, str(out), rate="-8%" if who == "秋师父" else "-4%")
            print(("  ✔ " if ok else "  ✘ ") + f"{sc['id']} {who}: {line[:22]}…")
    print("── ② 场景图 ──")
    for sc in SCENES:
        out = GEN / f"{sc['id']}.jpg"
        if "reuse" in sc:
            src = ROOT / "projects/movie/生成/概念图" / sc["reuse"]
            if src.is_file() and not out.is_file():
                out.write_bytes(src.read_bytes())
            print(("  ♻ " if out.is_file() else "  ✘ ") + sc["id"] + " (复用)")
            continue
        ok = gen_image(sc["img"], str(out))
        print(("  ✔ " if ok else "  ✘ ") + sc["id"])
    print("── ③ 逐场装配 ──")
    segs = []
    for sc in SCENES:
        seg = GEN / f"{sc['id']}_seg.mp4"
        if seg.is_file() and seg.stat().st_size > 50000:
            segs.append(seg); print("  ♻", sc["id"]); continue
        img = GEN / f"{sc['id']}.jpg"
        if not img.is_file():
            print("  ✘ 无图", sc["id"]); continue
        auds = sorted(GEN.glob(f"{sc['id']}_*.mp3"))
        sc_aud = GEN / f"{sc['id']}_audio.m4a"
        if not sc_aud.is_file():
            if not auds:
                sh(["ffmpeg","-y","-loglevel","error","-f","lavfi","-i","anullsrc=r=44100:cl=mono",
                    "-t",str(max(6,sc["dur_hint"]-3)),"-c:a","aac",str(sc_aud)])
            else:
                inputs, pads = [], []
                for k, a in enumerate(auds):
                    inputs += ["-i", str(a)]; pads.append(f"[{k}:a]apad=pad_dur=0.5[a{k}]")
                fc = ";".join(pads) + ";" + "".join(f"[a{k}]" for k in range(len(auds))) + \
                     f"concat=n={len(auds)}:v=0:a=1[out]"
                sh(["ffmpeg","-y","-loglevel","error",*inputs,"-filter_complex",fc,
                    "-map","[out]","-c:a","aac",str(sc_aud)])
        adur = max(6.0, min(90.0, (audio_dur(sc_aud) if sc_aud.is_file() else sc["dur_hint"]-3) + 1.2))
        # 🔴 2026-09-26 自纠：filter_complex 里 min(a,b) 的逗号必须转义，否则整图静默解析失败
        #    （两轮白跑的真凶）。根治：表达式消灭逗号——斜率按时长补偿，z 从 1 线性推到 1.22 封顶。
        rate = 0.22 / max(1.0, adur * 25)
        fc = (f"scale=1280:720,zoompan=z='1+{rate:.6f}*in':"
              f"x='iw/2-(iw/zoom/2)':y='ih*0.42-(ih/zoom/2)':d={int(adur*25)}:s=1280x720:fps=25,"
              f"vignette=PI/5,noise=alls=6:allf=t")
        r = sh(["ffmpeg","-y","-loglevel","error","-loop","1","-framerate","25","-i",str(img),
                "-i",str(sc_aud) if sc_aud.is_file() else "-f","lavfi","-i","anullsrc=r=44100:cl=stereo",
                "-filter_complex",f"[0:v]{fc}[v]","-map","[v]","-map","1:a",
                "-t",f"{adur:.2f}",
                "-c:v","libx264","-preset","veryfast","-crf","23","-c:a","aac","-b:a","128k",
                "-pix_fmt","yuv420p",str(seg)], timeout=900)
        ok = seg.is_file() and seg.stat().st_size > 50000
        print(("  ✔ " if ok else "  ✘ ") + f"{sc['id']} seg {adur:.1f}s")
        if ok: segs.append(seg)
    print("── ④ 全片拼接 + 做旧终渲染 ──")
    lst = GEN / "concat.txt"
    lst.write_text("\n".join(f"file '{s.as_posix()}'" for s in segs), encoding="utf-8")
    final = OUT / "末班义庄-序章-1080p.mp4"
    if not final.is_file() or final.stat().st_size < 10_000_000:
        sh(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(lst),
            "-filter_complex","noise=alls=5:allf=t+u,vignette=PI/5.5,eq=saturation=0.88:gamma_r=1.04",
            "-c:v","libx264","-preset","veryfast","-crf","23","-c:a","copy",
            "-pix_fmt","yuv420p","-movflags","+faststart",str(final)], timeout=1200)
    total = audio_dur(final) if final.is_file() else 0
    print(f"── 成片 ── {final.name} | {final.stat().st_size//1048576 if final.is_file() else 0} MB | {total/60:.1f} 分钟")
    return 0 if final.is_file() else 1

if __name__ == "__main__":
    sys.exit(main())
