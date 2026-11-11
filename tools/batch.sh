#!/bin/bash
cd /home/user/kettenreaktion
for a in "$@"; do set -- $a; echo "== $1"; tools/finish.sh $1 $2 $3 2>&1 | tail -2; done
