#!/bin/sh
# 카드뉴스 한 판 — 대표님이 정한 차례 그대로 (2026-09-02)
#
#   ① 어제 기사를 **다 읽는다**
#   ② 선정 기준으로 고른다 (한국어·영어 낱말표를 **똑같이** 적용)
#   ③ 고른 기사의 재료를 만든다 (낱말 6 · 대화 2줄 · 여섯 줄 풀이)
#   ④ 제목을 다듬는다
#   ⑤ 카드를 굽는다 (그림 포함, 한 줄에 한 문장)
#   ⑥ 바탕화면에 날짜별로 — 카드·멘트파일·파워포인트
#   ⑦ 최종 점검은 **클로드가** 한다
cd "$(dirname "$0")/.." || exit 1
export LANG=ko_KR.UTF-8 CHAO_LOCAL=1
PY=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
[ -x "$PY" ] || PY=/usr/local/bin/python3
[ -x "$PY" ] || PY=$(command -v python3)
PUB=${1:-}
say() { echo ""; echo "===== $1 · $(date '+%m-%d %H:%M') ====="; }

say "① 기사 받기";   "$PY" tools/fetch_news.py  2>&1 | tail -6
say "② 기사 고르기"; "$PY" tools/card_pick.py ${PUB:+--pub "$PUB"} 2>&1 | tail -18
say "③ 재료 만들기"; "$PY" tools/card_fill.py   2>&1 | tail -14
say "④ 제목 다듬기"; "$PY" tools/card_title.py  2>&1 | tail -6
say "⑤ 카드 굽기"
for d in $("$PY" -c "
import json,pathlib
D=json.loads(pathlib.Path('data/news_days.json').read_text(encoding='utf-8'))['days']
print(' '.join(sorted({x['ts'] for x in D if x.get('pub')})))"); do
  "$PY" tools/card_news.py --day "$d" --limit 12 2>&1 | tail -1
done
say "⑥ 바탕화면"
"$PY" tools/card_export.py 2>&1 | tail -1
"$PY" tools/card_ppt.py    2>&1 | tail -1
say "끝 — 최종 점검은 클로드가 한다"
