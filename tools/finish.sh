#!/bin/bash
# Nutzung: tools/finish.sh <ordner> <nr> <Titel>  -> vertont (falls nötig), rendert, Web-Version < 15 MB
set -e
cd /home/user/kettenreaktion/videos/$1
KR_VOICE=1 python3 $1.py out/full.mp4 --preview 1 | tail -1
python3 $1.py out/full.mp4 | tail -1
P=/tmp/claude-0/x2p_$1; mkdir -p /tmp/claude-0
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 out/full.mp4)
BR=$(python3 -c "print(int(14.2*8192/$D - 200))")
ffmpeg -y -v error -i out/full.mp4 -c:v libx264 -preset slow -b:v ${BR}k -pass 1 -passlogfile $P -an -f null /dev/null
ffmpeg -y -v error -i out/full.mp4 -c:v libx264 -preset slow -b:v ${BR}k -maxrate $((BR*3/2))k -bufsize $((BR*2))k -pass 2 -passlogfile $P -pix_fmt yuv420p -c:a copy -movflags +faststart out/FOLGENSCHWER_$2_$3.mp4
F=out/FOLGENSCHWER_$2_$3.mp4
I=$(ffmpeg -i $F -af ebur128 -f null - 2>&1 | grep -E '^\s+I:' | tail -1 | awk '{print $2}')
G=$(python3 -c "print(round(-14-($I),2))")
ffmpeg -y -v error -i $F -c:v copy -af "volume=${G}dB,alimiter=limit=0.84:level=false" -c:a aac -b:a 192k -ar 48000 -movflags +faststart out/_tmp.mp4 && mv out/_tmp.mp4 $F
rm -f out/full.mp4 ${P}*
ls -la out/FOLGENSCHWER_$2_$3.mp4 | awk '{print $5/1e6 " MB"}'
echo "Länge: $D s | $(ffmpeg -i out/FOLGENSCHWER_$2_$3.mp4 -af ebur128 -f null - 2>&1 | grep -E '^\s+I:' | tail -1 | tr -s ' ')"
