#!/bin/sh
# 저녁에 **만들기만** 한다 (대표님 지시 2026-09-02).
#
#   저녁 8:20  그날 기사가 다 올라온 뒤다 → 기사 받기 · 카드 만들기 (펴낸날 = 내일)
#   아침 6:30  tools/card_ship.sh 가 바탕화면 정리 + 앱 등록
#
# 만드는 때와 내보내는 때를 나눈 이유: 아침에 급히 만들면 늦고, 실패해도 손쓸 틈이 없다.
# 저녁에 미리 만들어 두면 밤 사이에 문제를 볼 수 있다.
cd "$(dirname "$0")/.." || exit 1
export LANG=ko_KR.UTF-8 CHAO_LOCAL=1

# **파이썬을 못 박는다.** launchd 는 로그인 셸과 PATH 가 달라
# /usr/bin/python3 를 잡는데 거기엔 PIL·pptx 가 없다 (실측 2026-09-02: 조용히 실패했다).
PY=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
[ -x "$PY" ] || PY=/usr/local/bin/python3
[ -x "$PY" ] || PY=$(command -v python3)
export PY

say() { echo ""; echo "===== $1 · $(date '+%m-%d %H:%M') ====="; }
say "쓰는 파이썬"; echo "$PY"; "$PY" -c "import PIL,pptx;print('필요한 것 다 있음')" || exit 1

say "기사 내려받기"; git pull --rebase --autostash 2>&1 | tail -2
say "기사 받기";     "$PY" tools/fetch_news.py   2>&1 | tail -3
say "학습 세트";     "$PY" tools/news_lesson.py  2>&1 | tail -3
say "여섯 줄 풀이";   "$PY" tools/news_sum5.py --local 2>&1 | tail -2
say "제목 다듬기";    "$PY" tools/card_title.py   2>&1 | tail -3

# 펴낸날은 **다음 아침**이다 — 오늘 기사로 만들어 내일 아침에 내보낸다.
# 저녁(12시 이후)에 돌면 내일, 새벽·아침에 손으로 돌리면 오늘.
# (실측 2026-09-02: 무조건 +1일로 잡아 새벽 0시 55분에 돌렸더니 9월 3일로 찍혔다)
if [ "$(date '+%H')" -ge 12 ]; then TOMORROW=$(date -v+1d '+%Y-%m-%d')
else TOMORROW=$(date '+%Y-%m-%d'); fi
say "카드 두 장씩 (펴낸날 $TOMORROW)"
"$PY" tools/card_news.py --pub "$TOMORROW" 2>&1 | tail -3
say "소리";         "$PY" tools/gen_audio.py    2>&1 | tail -1
say "만들기 끝 — 내보내기는 아침 6시 30분"
