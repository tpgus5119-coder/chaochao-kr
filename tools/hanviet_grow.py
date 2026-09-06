#!/usr/bin/env python3
"""한자 다리 넓히기 — 두 곳이 같은 답을 낼 때만 받는다.

왜 이렇게까지 하나:
  한자어는 베트남 학습자의 지름길이다(공개 기출 12회차를 세어 보니 단골 낱말의 68%가
  한자어였다). 그런데 한자 → 한월(Hán-Việt) 읽기를 기계로 지어내면 틀린다.
  이미 있는 다리 725개로 검산해 보니 14%가 어긋났다:
    · 한 한자에 읽기가 둘 (使 = sử/sứ, 分 = phân/phận)
    · 국립국어원 표에 동음이의어의 한자가 실려 있음 (통하다→桶(통), 실은 通)
  '지어내면 안 된다'는 규칙에 정면으로 걸린다.

그래서 받는 조건 — **서로 다른 두 곳이 같은 말을 할 때만**:
  ① 한자 표기(국립국어원)를 우리 한자 읽기표로 음절마다 읽어 만든 후보
  ② 우리가 이미 검증해 둔 베트남어 뜻(_ko_words.json 등)
  ①과 ②가 맞으면 다리로 받고, **글자는 ②(검증된 쪽)를 쓴다.**
  어긋나면 안 받고 review 파일에 적어 둔다 — 사람이 볼 몫이다.

■ 여기서 배운 것 (2026-08-28) — 조건을 느슨하게 하면 안 되는 이유
  '한자 읽기가 우리가 쓰는 베트남어 표현에 실제로 있으면 받자'로 풀어 보니 43개가 걸렸는데,
  그 안에 **가짜 친구**가 섞여 있었다:
      계단 階段 → giai đoạn   (베트남어 giai đoạn 은 '단계·시기'다. 한국어 계단은 '층계'다)
      무리 無理 → vô lí       (베트남어 vô lí 는 '말이 안 된다'. 한국어 무리는 '지나침·떼')
      부탁 付託 → phó thác    (베트남어 phó thác 은 '맡기다'로 무겁다. 한국어 부탁은 가벼운 청)
  글자는 맞는데 뜻이 어긋난다 — 학습자에게 가장 나쁜 종류의 틀림이다.
  그래서 자동 확장은 **하지 않는다.** 후보만 뽑아 두고 사람이 확인한 것만 넣는다.

그래도 자동으로 받는 자리가 하나 있다 — **①과 ②가 맞을 때.**
  이건 '지어낸 것'이 아니라 '서로 모르는 두 곳이 같은 말을 한 것'이다.
  성조 부호 자리(hoá/hóa)와 맞춤법(lí/lý, kĩ/kỹ) 차이는 같은 말로 친다.
  받은 예: 규모 規模 quy mô · 기술 技術 kỹ thuật · 미술 美術 mỹ thuật · 물리학 物理學 vật lý học

쓰기:  python3 tools/hanviet_grow.py         # 보기만
       python3 tools/hanviet_grow.py --save  # 맞은 것만 다리에 넣고, 어긋난 것은
                                             # hanviet_review.json 에 적어 둔다(기출 빈도순)
"""
import csv, json, os, re, sys, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = ROOT + "/tools"


def norm(s):
    """hóa 와 hoá 는 같은 말이다 — 성조 부호 자리만 다르다. 그 차이를 지운다."""
    s = unicodedata.normalize("NFD", str(s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")   # 성조 떼기
    return re.sub(r"\s+", " ", s).strip()


def norm2(s):
    """lí/lý, kĩ/kỹ — 베트남어 맞춤법이 둘 다 쓰는 자리다. 그 차이까지 지운다.
    여기까지 지워서 같으면 '같은 말을 달리 적은 것'이므로 사람 손 없이 받아도 된다.
    (뜻이 다른데 우연히 같아지는 일은 같은 한국어 낱말끼리 견주므로 사실상 없다)"""
    return norm(s).replace("y", "i")


def main():
    chars = json.load(open(f"{T}/hanviet_read.json", encoding="utf-8"))["chars"]
    bridge = json.load(open(f"{T}/hanviet_bridge_ko.json", encoding="utf-8"))

    han = {}
    for r in csv.DictReader(open(f"{T}/nikl_5965.tsv", encoding="utf-8"), delimiter="\t"):
        w = re.sub(r"\d+$", "", r["단어"]).strip()
        h = r["풀이"].strip()
        if h and re.fullmatch(r"[一-鿿]+", h):
            han.setdefault(w, h)

    # 검증된 뜻 — 우리가 이미 쓰고 있는 것만
    vi = {}
    for w in json.load(open(f"{ROOT}/data/_ko_words.json", encoding="utf-8")):
        if w.get("vi"):
            vi.setdefault(w["ko"], w["vi"])
    for d in json.load(open(f"{ROOT}/data/ko_days.json", encoding="utf-8"))["days"]:
        for w in d["words"]:
            vi[w["ko"]] = w["vi"]                    # 손으로 확인한 것이 우선

    take, review, cant = {}, [], 0
    for w, h in han.items():
        if w in bridge:
            continue
        cand = [chars.get(c) for c in h]
        if not all(cand):
            cant += 1; continue
        guess = " ".join(cand)
        base = w[:-2] if w.endswith("하다") else w
        got = vi.get(w) or vi.get(base) or vi.get(base + "하다")
        if not got:
            cant += 1; continue
        # 뜻이 여럿이면(‘hội thoại, đối thoại’) 하나만 맞아도 된다
        for part in [p.strip() for p in got.split(",")]:
            if norm2(part) == norm2(guess):
                take[w] = part                        # 검증된 쪽 글자를 쓴다
                break
        else:
            review.append((w, h, guess, got))

    print(f"새로 받은 다리 {len(take)}개 · 사람이 볼 것 {len(review)}개 · 못 잰 것 {cant}개")
    print(f"다리 총계 {len(bridge)} → {len(bridge) + len(take)}")
    print("\n받은 것 30개:")
    for k, v in list(take.items())[:30]:
        print(f"   {k:<10} {han[k]:<6} {v}")
    print("\n어긋나서 안 받은 것 15개 (한자읽기 ↔ 우리 뜻):")
    for w, h, g, o in review[:15]:
        print(f"   {w:<10} {h:<6} {g:<18} ↔ {o[:28]}")

    if "--save" in sys.argv:
        # 다리 파일은 건드리지 않는다. 확인할 목록만 만든다.
        # 기출에 자주 나오는 낱말이 위로 오게 정렬한다 — 확인할 시간이 없을 때
        # 위에서부터 몇 줄만 봐도 점수에 가장 크게 걸리는 것부터 메워진다.
        # 기출 빈도표가 있으면 자주 나오는 낱말부터 위로 (없으면 그냥 알파벳 순)
        try:
            ev = json.load(open(f"{T}/topik_freq.json", encoding="utf-8"))
        except Exception:
            ev = {}
        rows = ([{"ko": w, "han": han[w], "읽기": v, "확인": "두 곳이 맞음 — 넣어도 될 듯"}
                 for w, v in take.items()]
                + [{"ko": w, "han": h, "읽기": g, "우리뜻": o, "확인": "어긋남 — 사람이 볼 것"}
                   for w, h, g, o in review])
        rows.sort(key=lambda r: -ev.get(r["ko"], 0))
        json.dump(rows, open(f"{T}/hanviet_review.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        # 두 곳이 맞은 것만 다리에 넣는다 — 이건 '같은 말을 달리 적은 것'이라 안전하다.
        # 어긋난 것은 절대 안 넣는다(가짜 친구가 섞인다. 파일 맨 위 설명 참고).
        bridge.update(take)
        json.dump(bridge, open(f"{T}/hanviet_bridge_ko.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=0, sort_keys=True)
        print(f"\n다리에 넣음: {len(take)}개 (두 곳이 맞은 것만)")
        print(f"저장: hanviet_review.json ({len(rows)}줄) — 어긋난 것은 사람이 볼 몫입니다.")


if __name__ == "__main__":
    main()
