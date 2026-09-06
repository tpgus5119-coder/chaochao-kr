#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""발음 표기(kr·krs)만 vi_kr.py 로 다시 입힌다 → data/order.json

왜 따로 두나 (2026-08-31):
  발음 규칙을 고칠 일이 되풀이해서 생긴다(qu+모음 사고, gìn 사고 …).
  그때마다 order_build.py 를 돌리면 **그림 연결(img)이 통째로 날아간다.**
  그래서 발음 칸만 갈아 끼우는 도구를 따로 둔다.

바뀐 것만 보여 주고, --write 를 줘야 실제로 쓴다.
쓰기: python3 tools/kr_rebuild.py           # 무엇이 바뀌는지 보기만
      python3 tools/kr_rebuild.py --write   # 실제로 쓰기
"""
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import vi_kr

R = pathlib.Path(__file__).resolve().parent.parent
WRITE = "--write" in sys.argv


def walk(v):
    for t in (v.get("tracks") or [v]):
        for c in t["chapters"]:
            for l in c["lessons"]:
                yield from l["words"]


def fix(words, fields=("kr", "krs")):
    """낱말 목록의 발음 칸을 다시 만든다. 바뀐 것 목록을 돌려준다."""
    changed = []
    for w in words:
        vi = w.get("vi")
        if not vi:
            continue
        for f, south in ((fields[0], False), (fields[1], True)):
            if f not in w:                       # 없던 칸은 새로 만들지 않는다
                continue
            new = vi_kr.word(vi, south=south)
            if not new:                          # 도구가 못 읽으면 옛 값을 지키다
                continue
            if w[f] != new:
                changed.append((vi, w.get("ko", ""), f, w[f], new))
                w[f] = new
    return changed


def main():
    total = []

    # ① order.json — 지금 과정 본체
    op = R / "data" / "order.json"
    O = json.loads(op.read_text(encoding="utf-8"))
    words = [w for v in O["vols"] for w in walk(v)] + O.get("gramwords", [])
    ex = [w["ex"] for w in words if isinstance(w.get("ex"), dict)]
    ch = fix(words) + fix(ex)
    total += [("order.json",) + c for c in ch]
    if WRITE and ch:
        op.write_text(json.dumps(O, ensure_ascii=False), encoding="utf-8")

    # ② days.json 은 **건드리지 않는다.**
    #    거기 kr_read 는 도구가 아니라 사람이 손으로 적은 북부 표기다(검수 기록).
    #    도구로 덮으면 손으로 고친 것이 사라진다.

    print(f"발음이 달라지는 곳 {len(total)}개")
    for t in total[:60]:
        print(f"  [{t[0]}] {t[1]}  ({t[2]})  {t[3]}: {t[4]!r} → {t[5]!r}")
    if len(total) > 60:
        print(f"  … 그리고 {len(total)-60}개 더")
    print("실제로 썼습니다." if (WRITE and total) else
          ("바뀔 것이 없습니다." if not total else "보기만 했습니다 — 쓰려면 --write"))


main()
