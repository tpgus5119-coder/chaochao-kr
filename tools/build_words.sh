#!/bin/sh
# 낱말 자료를 처음부터 다시 만든다. **차례를 지켜야 한다** (2026-08-30)
#   읽기 → 합치기 → 손질 → 철자 교정 → 갈래 나누기 → 차례 매기기 → 그림 잇기
set -e
cd "$(dirname "$0")/.."
python3 tools/senior_merge.py  | tail -2
python3 tools/senior_hand.py   | tail -2
python3 tools/spell_apply.py   | head -1
python3 tools/clean_text.py
python3 tools/senior_split.py  | head -1
python3 tools/order_build.py   | tail -6
python3 tools/img_link.py      | tail -2
