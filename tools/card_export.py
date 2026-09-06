#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""카드뉴스를 **바탕화면에 날짜별 폴더**로 내보낸다.

대표님 지시 (2026-08-31): "매일 카드뉴스 만든거 어플에 삽입도하지만
                          바탕화면에 폴더에 만들어줘. 날짜별로 구분해서."

내보내는 곳: ~/Desktop/chaochao-cardnews/<날짜>/
  2026-08-28/
    01-회사발전-1.webp   ← 첫 장(제목·다섯 줄 요약)
    01-회사발전-2.webp   ← 둘째 장(낱말 여섯)
    ...
    기사링크.txt          ← 동기들에게 보낼 제목·링크

파일 이름에 기사 갈래 대신 **주제**를 넣는다 — 폴더만 열어도 무엇인지 안다.
이미 있는 것과 내용이 같으면 다시 쓰지 않는다(바탕화면이 계속 새로고침되지 않게).

쓰기: python3 tools/card_export.py            # 있는 날짜 전부
      python3 tools/card_export.py --day 2026-08-28
"""
import argparse, json, pathlib, re, shutil

R = pathlib.Path(__file__).resolve().parent.parent
CARD = R / "img" / "card"
DESK = pathlib.Path.home() / "Desktop" / "chaochao-cardnews"


def ko_name(d):
    """**한국어**로 파일 이름을 짓는다.

    현지 신문 기사는 theme 이 베트남어라 '03-phongcáchn' 같은 이름이 나왔다
    (2026-09-02 실측). 폴더만 열어서는 무슨 기사인지 알 수 없다.
    다듬은 제목 → theme 차례로 보고, **한글이 있는 것**을 쓴다."""
    import re as _r
    for x in (d.get("title_card"), d.get("theme"), d.get("title")):
        t = str(x or "").strip()
        if _r.search(r"[가-힣]", t):
            # 한글·숫자만 남기고 열 글자까지
            t = _r.sub(r"[^가-힣0-9 ]", "", t).strip()
            t = _r.sub(r"\s+", "", t)[:10]
            if t:
                return t
    return safe(d.get("theme")) or "기사"


def safe(s, n=18):
    """폴더에서 읽기 좋은 이름으로. 슬래시·따옴표처럼 탈 나는 글자를 뺀다."""
    s = re.sub(r'[\\/:*?"<>|]', "", str(s)).strip()
    s = re.sub(r"\s+", "", s)
    return s[:n] or "기사"


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--day")
    a = a.parse_args()

    days = json.loads((R / "data" / "news_days.json").read_text(encoding="utf-8"))["days"]
    by_ts = {}
    for d in days:
        # 폴더는 **펴낸 날**로 나눈다 — 대표님이 보시는 날짜와 맞아야 한다
        by_ts.setdefault(d.get("pub") or d.get("ts"), []).append(d)

    total = 0
    for ts, arts in sorted(by_ts.items()):
        if not ts or (a.day and ts != a.day):
            continue
        out = DESK / ts
        made = 0
        # 그림 파일 이름의 번호는 **기사 날짜 안에서** 매겨진다.
        # 펴낸날로 묶으면 이틀치가 한 폴더에 오는데, 그때 번호를 이어서 세면 어긋난다
        # (실측 2026-09-02: 카드 22장 중 14장만 나갔다).
        cnt = {}
        for d in arts:
            k = d.get("ts")
            cnt[k] = cnt.get(k, 0) + 1
            d["_i"] = cnt[k]
        # **주제별로 늘어놓는다** (대표님 지시 2026-09-02 "출처별로 정렬하지 말고 주제별로").
        # 폴더를 열면 일자리 → 경제 → 사회 → 공장 → 문화 차례로 보인다.
        ORDER = ['일자리', '경제', '사회', '공장·산업', '문화·생활', '정치']
        arts = sorted(arts, key=lambda d: (ORDER.index(d.get('cat'))
                                           if d.get('cat') in ORDER else len(ORDER),
                                           d.get('ts') or ''))
        for i, d in enumerate(arts, 1):
            for n in (1, 2):
                src = CARD / f"{d.get('ts')}-{d['_i']}-{n}.webp"
                if not src.exists():
                    continue
                cat = (d.get('cat') or '').replace('·', '')
                dst = out / f"{i:02d}-{cat}-{ko_name(d)}-{n}.webp"
                if dst.exists() and dst.read_bytes() == src.read_bytes():
                    continue
                out.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                made += 1
        if not out.exists():
            continue
        # 동기들에게 보낼 쪽지 — 제목과 링크만 (대표님 지시)
        lines = [f"📰 베트남 소식 {ts.replace('-', '.')}", ""]
        # 그림 파일 이름의 번호는 **기사 날짜 안에서** 매겨진다.
        # 펴낸날로 묶으면 이틀치가 한 폴더에 오는데, 그때 번호를 이어서 세면 어긋난다
        # (실측 2026-09-02: 카드 22장 중 14장만 나갔다).
        cnt = {}
        for d in arts:
            k = d.get("ts")
            cnt[k] = cnt.get(k, 0) + 1
            d["_i"] = cnt[k]
        # **주제별로 늘어놓는다** (대표님 지시 2026-09-02 "출처별로 정렬하지 말고 주제별로").
        # 폴더를 열면 일자리 → 경제 → 사회 → 공장 → 문화 차례로 보인다.
        ORDER = ['일자리', '경제', '사회', '공장·산업', '문화·생활', '정치']
        arts = sorted(arts, key=lambda d: (ORDER.index(d.get('cat'))
                                           if d.get('cat') in ORDER else len(ORDER),
                                           d.get('ts') or ''))
        for i, d in enumerate(arts, 1):
            if d.get("u"):
                lines.append(f"{i}. {d.get('title','')}")
                lines.append(f"   {d['u']}")
                lines.append("")
        lines += ["📱 카드뉴스와 오늘의 낱말은 짜오짜오에서",
                  "https://tpgus5119-coder.github.io/chaochao/",
                  "", "폰에서 열고 '홈 화면에 추가'를 누르면 앱처럼 씁니다."]
        txt = "\n".join(lines) + "\n"
        tp = out / "기사링크.txt"
        if not tp.exists() or tp.read_text(encoding="utf-8") != txt:
            tp.write_text(txt, encoding="utf-8")
        if made:
            print(f"  {ts}: {made}장 내보냄 → {out}")
        total += made

    print(f"바탕화면으로 {total}장 내보냈습니다 → {DESK}" if total
          else f"새로 내보낼 것이 없습니다 → {DESK}")


main()
