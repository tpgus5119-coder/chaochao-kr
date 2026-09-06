#!/bin/sh
# 아침에 **내보내기만** 한다 (대표님 지시 2026-09-02).
# 저녁에 만들어 둔 카드를 바탕화면 날짜 폴더에 넣고 앱에 올린다.
cd "$(dirname "$0")/.." || exit 1
export LANG=ko_KR.UTF-8
PY=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
[ -x "$PY" ] || PY=/usr/local/bin/python3
[ -x "$PY" ] || PY=$(command -v python3)

say() { echo ""; echo "===== $1 · $(date '+%m-%d %H:%M') ====="; }
say "바탕화면으로";  "$PY" tools/card_export.py 2>&1 | tail -2
say "파워포인트";    "$PY" tools/card_ppt.py    2>&1 | tail -2
say "앱에 올리기"
"$PY" tools/stamp.py 2>&1 | tail -1
git add -A && git commit -q -m "오늘의 카드뉴스 (자동)" && git push origin main 2>&1 | tail -1
say "끝"
