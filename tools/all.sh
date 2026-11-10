#!/bin/bash
cd /home/user/kettenreaktion
for a in "mond 01 Mond" "stopp 02 Erde_stoppt" "insekten 03 Insekten" "sonne 04 Sonne_aus" "eis 05 Eis_schmilzt" "loch 06 Schwarzes_Loch"; do
  set -- $a; echo "== $1"; tools/finish.sh $1 $2 $3 2>&1 | tail -2
done
