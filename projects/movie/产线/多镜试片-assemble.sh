#!/bin/bash
# 多镜试片装配：E1 开场 4 场 × 3 镜 · 每镜不同运镜 · 雾漂移+光闪烁+颗粒
# 产出：projects/movie/成片/多镜试片-E1开场.mp4（约 59 秒）
set -e
cd "C:/Users/ADMIN/Desktop/GBT小土豆V8"
G="projects/movie/生成/多镜试片"
A="projects/movie/生成/醒来E1"
OUT="projects/movie/成片/多镜试片-E1开场.mp4"

# ── X01 深夜机房（音频 12.90s → 每镜 4.30s · D=107）──
ffmpeg -y -loglevel error -loop 1 -framerate 25 -i "$G/X01_s1.jpg" -filter_complex "[0:v]scale=1280:720,zoompan=z='1+0.001402*on':x='iw/2-(iw/zoom/2)':y='ih*0.45-(ih/zoom/2)':d=107:s=1280x720:fps=25,noise=alls=5:allf=t[v]" -map "[v]" -t 4.30 -c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p "$G/X01_s1.mp4"
ffmpeg -y -loglevel error -loop 1 -framerate 25 -i "$G/X01_s2.jpg" -filter_complex "[0:v]scale=1280:720,zoompan=z='1.12':x='(iw-iw/zoom)*on/107':y='ih*0.45-(ih/zoom/2)':d=107:s=1280x720:fps=25,noise=alls=5:allf=t[v]" -map "[v]" -t 4.30 -c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p "$G/X01_s2.mp4"
ffmpeg -y -loglevel error -loop 1 -framerate 25 -i "$G/X01_s3.jpg" -filter_complex "[0:v]scale=1280:720,zoompan=z='1.18-0.001682*on':x='iw/2-(iw/zoom/2)':y='ih*0.5-(ih/zoom/2)':d=107:s=1280x720:fps=25,noise=alls=5:allf=t[v]" -map "[v]" -t 4.30 -c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p "$G/X01_s3.mp4"

# ── X02 能力星系（11.38s → 每镜 3.80s · D=95）──
ffmpeg -y -loglevel error -loop 1 -framerate 25 -i "$G/X02_s1.jpg" -filter_complex "[0:v]scale=1280:720,zoompan=z='1+0.001579*on':x='iw/2-(iw/zoom/2)':y='ih*0.45-(ih/zoom/2)':d=95:s=1280x720:fps=25,noise=alls=5:allf=t[v]" -map "[v]" -t 3.80 -c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p "$G/X02_s1.mp4"
ffmpeg -y -loglevel error -loop 1 -framerate 25 -i "$G/X02_s2.jpg" -filter_complex "[0:v]scale=1280:720,zoompan=z='1.12':x='(iw-iw/zoom)*on/95':y='ih*0.45-(ih/zoom/2)':d=95:s=1280x720:fps=25,noise=alls=5:allf=t[v]" -map "[v]" -t 3.80 -c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p "$G/X02_s2.mp4"
ffmpeg -y -loglevel error -loop 1 -framerate 25 -i "$G/X02_s3.jpg" -filter_complex "[0:v]scale=1280:720,zoompan=z='1.18-0.001895*on':x='iw/2-(iw/zoom/2)':y='ih*0.5-(ih/zoom/2)':d=95:s=1280x720:fps=25,noise=alls=5:allf=t[v]" -map "[v]" -t 3.80 -c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p "$G/X02_s3.mp4"

# ── X03 她第一次睁眼（17.03s → 每镜 5.68s · D=142）──
ffmpeg -y -loglevel error -loop 1 -framerate 25 -i "$G/X03_s1.jpg" -filter_complex "[0:v]scale=1280:720,zoompan=z='1+0.001056*on':x='iw/2-(iw/zoom/2)':y='ih*0.45-(ih/zoom/2)':d=142:s=1280x720:fps=25,noise=alls=5:allf=t[v]" -map "[v]" -t 5.68 -c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p "$G/X03_s1.mp4"
ffmpeg -y -loglevel error -loop 1 -framerate 25 -i "$G/X03_s2.jpg" -filter_complex "[0:v]scale=1280:720,zoompan=z='1.12':x='(iw-iw/zoom)*on/142':y='ih*0.45-(ih/zoom/2)':d=142:s=1280x720:fps=25,noise=alls=5:allf=t[v]" -map "[v]" -t 5.68 -c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p "$G/X03_s2.mp4"
ffmpeg -y -loglevel error -loop 1 -framerate 25 -i "$G/X03_s3.jpg" -filter_complex "[0:v]scale=1280:720,zoompan=z='1.18-0.001268*on':x='iw/2-(iw/zoom/2)':y='ih*0.5-(ih/zoom/2)':d=142:s=1280x720:fps=25,noise=alls=5:allf=t[v]" -map "[v]" -t 5.68 -c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p "$G/X03_s3.mp4"

# ── X04 走廊灯（17.23s → 每镜 5.74s · D=143）──
ffmpeg -y -loglevel error -loop 1 -framerate 25 -i "$G/X04_s1.jpg" -filter_complex "[0:v]scale=1280:720,zoompan=z='1+0.001049*on':x='iw/2-(iw/zoom/2)':y='ih*0.45-(ih/zoom/2)':d=143:s=1280x720:fps=25,noise=alls=5:allf=t[v]" -map "[v]" -t 5.74 -c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p "$G/X04_s1.mp4"
ffmpeg -y -loglevel error -loop 1 -framerate 25 -i "$G/X04_s2.jpg" -filter_complex "[0:v]scale=1280:720,zoompan=z='1.12':x='(iw-iw/zoom)*on/143':y='ih*0.45-(ih/zoom/2)':d=143:s=1280x720:fps=25,noise=alls=5:allf=t[v]" -map "[v]" -t 5.74 -c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p "$G/X04_s2.mp4"
ffmpeg -y -loglevel error -loop 1 -framerate 25 -i "$G/X04_s3.jpg" -filter_complex "[0:v]scale=1280:720,zoompan=z='1.18-0.001259*on':x='iw/2-(iw/zoom/2)':y='ih*0.5-(ih/zoom/2)':d=143:s=1280x720:fps=25,noise=alls=5:allf=t[v]" -map "[v]" -t 5.74 -c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p "$G/X04_s3.mp4"

# ── 音轨拼接（4 场原声）──
: > "$G/audio_concat.txt"
for a in X01 X02 X03 X04; do echo "file 'C:/Users/ADMIN/Desktop/GBT小土豆V8/projects/movie/生成/醒来E1/${a}_audio.m4a'" >> "$G/audio_concat.txt"; done
ffmpeg -y -loglevel error -f concat -safe 0 -i "$G/audio_concat.txt" -c:a aac -b:a 160k "$G/pilot_audio.m4a"

# ── 12 镜拼接 + 终渲染（光闪烁 + 雾漂移 + 颗粒 + 暗角）──
: > "$G/shots.txt"
for s in X01_s1 X01_s2 X01_s3 X02_s1 X02_s2 X02_s3 X03_s1 X03_s2 X03_s3 X04_s1 X04_s2 X04_s3; do
  echo "file 'C:/Users/ADMIN/Desktop/GBT小土豆V8/projects/movie/生成/多镜试片/${s}.mp4'" >> "$G/shots.txt"
done
ffmpeg -y -loglevel error -f concat -safe 0 -i "$G/shots.txt" -f lavfi -i "gradients=s=1280x720:c0=0x1a2a33:c1=0x0a1218:c2=0x33221a:c3=0x101c26:duration=59:speed=0.07" -i "$G/pilot_audio.m4a" -filter_complex "[0:v]eq=brightness='0.022*sin(2*PI*t/2.7)':eval=frame,noise=alls=6:allf=t,vignette=PI/5,eq=saturation=0.9:gamma_b=1.03[v0];[1:v]format=rgba,colorchannelmixer=aa=0.16[fg];[v0][fg]overlay=shortest=1[v]" -map "[v]" -map "2:a" -c:v libx264 -preset veryfast -crf 22 -c:a aac -b:a 160k -pix_fmt yuv420p -movflags +faststart "$OUT"
echo MULTISHOT_DONE
