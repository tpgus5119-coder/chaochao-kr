#!/usr/bin/env python3
"""두 과정이 그림을 나눠 쓴다 — 뜻이 같으면 같은 그림 (대표님 지시, 2026-08-29)

  python3 tools/img_share.py          → 어떤 것이 채워질지 보기만
  python3 tools/img_share.py --write  → 실제로 붙이기

왜 되는가: 한국어 과정은 베트남 사람에게 '회사'를 가르치고, 베트남어 과정은
한국 사람에게 'công ty'를 가르친다. **가리키는 것이 같다.** 그러니 그림도 같아도 된다.
지금(2026-08-29)은 두 과정 다 그림이 100% 차 있어 채울 것이 없다. 이 도구는
앞으로 낱말을 넣을 때를 위한 것이다 — 없는 것만 채우고 있는 것은 건드리지 않는다.

맞추는 열쇠는 **한국어 뜻**이다. 괄호 안 설명은 떼고, 가운뎃점·빗금으로 갈라
낱낱을 견준다('부서·파트' → {부서, 파트}). 두 글자 미만은 버린다 — '것·수' 같은
말이 엉뚱하게 걸린다.
"""
import argparse, json, pathlib, re

R = pathlib.Path(__file__).resolve().parent.parent
IMG = R / "img"
FILES = ["days.json", "ko_days.json"]

def keys(t):
    t = re.split(r"[(（]", t or "")[0]
    return {p.strip() for p in re.split(r"[·/,~]", t) if len(p.strip()) > 1}

def have(f):
    return bool(f) and (IMG / f).exists()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    docs = {f: json.loads((R / "data" / f).read_text(encoding="utf-8")) for f in FILES}
    # 뜻 → 그림 (두 과정을 통틀어 한 통에 모은다)
    pool = {}
    for j in docs.values():
        for d in j.get("days", []):
            for w in d.get("words") or []:
                if have(w.get("img")):
                    for k in keys(w.get("ko", "")):
                        pool.setdefault(k, w["img"])

    hit = 0
    for f, j in docs.items():
        for d in j.get("days", []):
            for w in d.get("words") or []:
                if have(w.get("img")):
                    continue
                for k in keys(w.get("ko", "")):
                    if k in pool:
                        print(f"  {f} Day {d.get('day')} · {w.get('ko')} ← {pool[k]}")
                        if a.write:
                            w["img"] = pool[k]
                        hit += 1
                        break
    if a.write and hit:
        for f, j in docs.items():
            (R / "data" / f).write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n뜻 대장 {len(pool)}개 · 채울 수 있는 낱말 {hit}개"
          + (" — 붙였다" if a.write and hit else "" if hit else " (지금은 두 과정 다 그림이 다 있다)"))

if __name__ == "__main__":
    main()
