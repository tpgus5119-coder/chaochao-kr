#!/bin/sh
# 밤새 도는 일 — 새 일상 과정을 만들고 **검수까지** 한다 (대표님 지시 2026-09-01)
#
# 앱 자료(order.json 등)는 건드리지 않는다. data/_new_words.json 에만 쌓는다.
# 검수는 세 겹이다: ① 규칙(공짜) ② 사전(공짜) ③ Qwen(공짜) — 클로드 토큰이 안 든다.
#
# 쓰기: nohup sh tools/overnight.sh > logs/overnight.log 2>&1 &
cd "$(dirname "$0")/.."
export LANG=ko_KR.UTF-8
say() { echo ""; echo "===== $1 · $(date '+%H:%M') ====="; }

~/.lmstudio/bin/lms load qwen/qwen3.5-9b -c 16384 --gpu max --ttl 21600 --parallel 1 -y >/dev/null 2>&1

for i in 1 2 3 4; do
  say "낱말 채우기 $i 판"
  python3 tools/new_words.py --want 25
  say "가짜 거르기 $i 판"          # 규칙 — 조합으로 만든 말·문장·중복
  python3 tools/new_clean.py
done

say "실제로 쓰는 말인지"           # Qwen 판정 + 규칙 재검수
python3 tools/new_real.py

say "뜻 검수"                     # 위키낱말 대조 → 못 가른 것만 Qwen
python3 tools/new_check.py

say "발음 달기"                   # 도구가 만든다 (AI 아님)
python3 tools/new_kr.py

say "여기까지"
python3 - <<'PY'
import json,pathlib
from collections import Counter
d=json.loads(pathlib.Path("data/_new_words.json").read_text(encoding="utf-8"))
print("낱말",sum(len(v) for v in d.values()),"· 꼭지",len(d))
print("검수",dict(Counter(w.get("v") for v in d.values() for w in v)))
print("모자란 꼭지",[t for t,v in d.items() if len(v)<20])
PY
