#!/usr/bin/env python3
"""한글(.hwp) 파일에서 글자만 꺼낸다.  실행: python3 tools/hwp_text.py <파일…>

왜 직접 짜나: 이 맥에는 한글도 리브레오피스도 pyhwp 도 없다. 그런데 hwp 5.x 는
꼴이 정해져 있어 표준 도구만으로 읽힌다.

  · 파일 전체가 OLE 복합문서(olefile 로 연다)
  · 본문은 `BodyText/Section0,1,…` 에 들어 있고, 문서 속성이 '눌렀다'고 하면
    raw deflate(zlib -15)로 눌려 있다
  · 그 안은 레코드가 줄줄이 이어진 꼴. 머리 4바이트에 [태그 10비트][단계 10비트]
    [길이 12비트]가 들어 있고, 길이가 0xFFF 면 다음 4바이트가 진짜 길이다.
  · 글자는 태그 67(HWPTAG_PARA_TEXT). 두 바이트 한 글자(UTF-16LE)인데,
    1~31 번 값은 글자가 아니라 조판 표시다. 그중 일부는 뒤에 14바이트를 더 끌고
    간다 — 이걸 안 건너뛰면 표·그림 자리에서 글자가 와르르 깨진다.

꺼낸 글은 **재배포하지 않는다.** 세기 위해서만 쓴다(한자어 비율·낱말 빈도).
"""
import re
import sys
import zlib

import olefile

# 1~31 번은 글자가 아니라 조판 표시다. 두 갈래인데 **둘 다 16바이트를 차지한다** —
# 늘린 표시(1·2·3·11·12·14~18·21~23: 표·그림·글상자…)와 줄 안 표시(4~9·19·20).
# 앞의 갈래를 빼먹으면 표가 있는 자리마다 '捤獥' 같은 깨진 글자가 쏟아진다.
CTRL_16 = {1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23}
TAG_PARA_TEXT = 67


def records(buf):
    i, n = 0, len(buf)
    while i + 4 <= n:
        h = int.from_bytes(buf[i:i + 4], "little")
        tag, size = h & 0x3FF, (h >> 20) & 0xFFF
        i += 4
        if size == 0xFFF:
            size = int.from_bytes(buf[i:i + 4], "little")
            i += 4
        yield tag, buf[i:i + size]
        i += size


def para_text(d):
    out, i = [], 0
    while i + 2 <= len(d):
        c = int.from_bytes(d[i:i + 2], "little")
        i += 2
        if c in CTRL_16:
            i += 14
        elif c < 32:
            out.append("\n" if c in (10, 13) else " ")
        else:
            out.append(chr(c))
    return "".join(out)


def text_of(path):
    f = olefile.OleFileIO(path)
    squeezed = True
    if f.exists("FileHeader"):
        head = f.openstream("FileHeader").read()
        squeezed = bool(head[36] & 1)             # 속성 첫 비트 = 눌렸는가
    parts = []
    for entry in sorted(f.listdir()):
        if entry[0] != "BodyText":
            continue
        raw = f.openstream(entry).read()
        buf = zlib.decompress(raw, -15) if squeezed else raw
        for tag, d in records(buf):
            if tag == TAG_PARA_TEXT:
                parts.append(para_text(d))
    f.close()
    t = "\n".join(parts)
    t = t.replace("\x00", "")
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", t)).strip()


if __name__ == "__main__":
    for p in sys.argv[1:]:
        t = text_of(p)
        print(f"\n===== {p.split('/')[-1]} — {len(t):,}자")
        print(t)
