#!/bin/sh
# days.json 을 원본에서 다시 만든다. **차례가 중요하다** — 뒤 도구가 앞 도구 결과를 쓴다.
# 이 차례를 지키지 않으면 조용히 사라지는 것이 생긴다(실제로 8.5강이 통째로 되돌아갔다).
set -e
cd "$(dirname "$0")/.."
python3 tools/b9.py                  # 새 챕터 원본 → data/_b9.json
python3 tools/assemble.py --write    # 합치고 검증하고 days.json 기록
python3 tools/fix10.py               # 한 강 = 낱말 10개로 맞춤 (넘치면 ②강으로 쪼갬)
python3 tools/img_relink.py          # 이미 구운 그림을 다시 이어 붙임
python3 tools/img_share.py --write   # 뜻이 같으면 두 과정이 그림을 나눠 쓴다
python3 tools/new_dialogs.py         # 쪼개진 강에 대화문 + 강 번호 다시 매김
python3 tools/fill_missions.py       # 빈 미션 채움
# place_b9 는 **new_dialogs 뒤**여야 한다 — 거기서 강 번호를 다시 매기기 때문이다
python3 tools/place_b9.py            # 생산현장어 8강을 직무 차례 제자리에
# **맨 마지막에** 되돌린다 — new_dialogs 가 8.5강 대화를 옛것으로 덮어쓰기 때문이다
python3 tools/apply_patches.py       # days.json 에만 살아 있던 사용자 지시 수정 되돌림
python3 tools/star_mark.py           # 선배 시험에 나온 낱말에 별표(sr)
python3 tools/hanja_attach.py        # 한자 다리
python3 tools/gen_covers.py          # 챕터 표지
python3 tools/gen_audio.py           # 새로 늘어난 것만 음성
python3 tools/img_review_page.py     # 그림 검수판
python3 tools/stamp.py               # 판번호 (배포 전 필수)
