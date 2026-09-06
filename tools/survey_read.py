#!/usr/bin/env python3
"""설문 결과를 사람이 읽을 꼴로 뽑는다.  실행: python3 tools/survey_read.py

두 설문이 서버에 쌓인다.
  · giongs — 합친 설문(giong.html). 문장마다 ① 네 소리 각각 어느 지방인가(dia)
             ② 하나만 골라 어느 것이 가장 사람 같은가(nat)
  · votes  — 옛 가림 설문(voice-vi/ko). 세 소리 중 하나만, 이름을 가리고 물었다

**손으로 세지 말 것.** 전에 듣기 길이를 손으로 재다 세 번 연속 틀렸다.
같은 값을 늘 같은 방법으로 뽑으려고 이 파일을 둔다.

소리와 엔진의 짝(가림 설문은 A~C, 합친 설문은 A~D — 서로 다른 판이다):
"""
import json
import subprocess

API = "https://viet-club.chaochao-app.workers.dev"
ORIGIN = "https://tpgus5119-coder.github.io"        # 워커가 이 주소만 받는다
GIONG = {"A": "Edge (지금 앱)", "B": "Supertonic 3", "C": "Chirp 3 HD",
         "D": "우리 남부 (VITS)"}
VOTE = {"A": "Edge (지금 앱)", "B": "Supertonic", "C": "Chirp 3 HD"}
RGNAME = {"bac": "북부", "trung": "중부", "nam": "남부", "": "안 밝힘"}


def ask(act, **kw):
    """curl 로 부른다 — 이 맥의 파이썬은 인증서 꾸러미가 없어 https 를 못 연다."""
    out = subprocess.run(
        ["curl", "-sS", "-m", "20", "-X", "POST", API,
         "-H", "Content-Type: application/json", "-H", f"Origin: {ORIGIN}",
         "-d", json.dumps(dict(act=act, **kw))],
        capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def bar(n, top, w=20):
    return "█" * round(w * n / top) if top else ""


def tally(agg, keys, names):
    """열쇠들을 합쳐 소리별 표를 센다."""
    t = {}
    for k in keys:
        for v, c in agg.get(k, {}).items():
            t[v] = t.get(v, 0) + c
    return dict(sorted(t.items(), key=lambda x: -x[1]))


def unpack(agg):
    """옛 칸에 실려 온 표를 되돌린다 — giong.html 의 보내는 쪽과 짝이다.

    '3C'  → 문장3의 소리C 를 어느 지방으로 들었나 (지방 표)
    '13D' → 문장3에서 D 를 가장 사람 같다고 골랐다 (값은 쓰지 않는다)
    """
    dia, nat = {}, {}
    for k, cnt in agg.items():
        if len(k) == 2:                       # 1A ~ 9D — 본디 쓰임
            dia[k] = cnt
        elif len(k) == 3 and k[0] == "1":     # 11A ~ 19D — 얹어 보낸 '사람 같다'
            q, v = k[1], k[2]
            nat.setdefault(q, {})[v] = nat.get(q, {}).get(v, 0) + sum(cnt.values())
    return dia, nat


def show_giong(d):
    n, nOld = d.get("n", 0), d.get("nOld", 0)
    print(f"\n■ 합친 설문 — 새 칸으로 온 답 {n}명"
          + (f" · 옛 칸으로 온 답 {nOld}명" if nOld else ""))
    if not (n or nOld):
        return print("  아직 한 명도 없다.")

    dia, nat = unpack(d.get("dia", {}))
    for q, m in d.get("nat", {}).items():          # 새 칸으로 온 것과 합친다
        for v, c in m.items():
            nat.setdefault(q, {})[v] = nat.get(q, {}).get(v, 0) + c

    print("\n  [1] 이 소리가 어느 지방으로 들리나 — 소리마다 5문장")
    for v, name in GIONG.items():
        t = tally(dia, [k for k in dia if k.endswith(v)], None)
        tot = sum(t.values())
        if not tot:
            continue
        say = " · ".join(f"{RGNAME[r]} {c}" for r, c in t.items() if r != "?")
        q = t.get("?", 0)
        print(f"   {v} {name:<16} {say}" + (f" · 모름 {q}" if q else ""))

    if nat:
        print("\n  [2] 가장 사람 같은 소리 — 한 문장에 하나만")
        t = tally(nat, list(nat), None)
        tot = sum(t.values()) or 1
        for v, c in t.items():
            print(f"   {v} {GIONG[v]:<16} {c:>3}표 {c/tot*100:4.1f}%"
                  f" {bar(c, max(t.values()))}")
    else:
        print("\n  [2] 가장 사람 같은 소리 — **아직 한 표도 없다.**")

    # 이 설문에서 가장 알고 싶은 것: 남부 사람 귀에도 A(Edge)가 남부로 들리는가.
    # 북부 사람만 그렇게 듣는다면 그건 '남부'가 아니라 '내 말씨가 아님'이다.
    byrg = {k: v for k, v in d.get("byrg", {}).items() if v.get("dia")}
    if byrg:
        print("\n  [3] 답한 사람의 지방별 — 남부 사람도 A를 남부라 하는가")
        for rg, m in byrg.items():
            rdia, rnat = unpack(m["dia"])
            line = []
            for v in GIONG:
                t = tally(rdia, [k for k in rdia if k.endswith(v)], None)
                top = max(t.items(), key=lambda x: x[1])[0] if t else "?"
                line.append(f"{v}={RGNAME.get(top, '모름')}")
            best = tally(rnat, list(rnat), None)
            pick = next(iter(best), None)
            print(f"   {RGNAME.get(rg, rg)} 사람 → " + " · ".join(line)
                  + (f"  |  사람 같다: {pick}" if pick else ""))


def show_vote(d):
    for pool, who in (("vi", "베트남 사람"), ("ko", "한국 사람")):
        p = d.get(pool, {})
        n = p.get("n", 0)
        if not n:
            continue
        agg = p.get("agg", {})
        print(f"\n■ 옛 가림 설문 — {who} {n}명")
        for pre, lab in (("v", "베트남어 문장"), ("k", "한국어 문장")):
            keys = [k for k in agg if k.startswith(pre)]
            if not keys:
                continue
            t = tally(agg, keys, None)
            tot = sum(t.values()) or 1
            print(f"  {lab} {len(keys)}개")
            for v, c in t.items():
                print(f"   {v} {VOTE[v]:<16} {c:>3}표 {c/tot*100:4.1f}%"
                      f" {bar(c, max(t.values()))}")


if __name__ == "__main__":
    d = ask("giongs")
    if d.get("error"):                # 'gone' = 워커가 아직 옛 판이라 이름을 모른다
        print(f"\n⚠️ 워커가 합친 설문을 모른다(error: {d['error']}).")
        print("   tools/club_worker.js 를 Cloudflare 에 다시 올리면 깔끔해진다(v15).")
        print("   그때까지도 답은 안 잃는다 — giong.html 이 옛 칸에 실어 보낸다.")
        o = ask("dialects")
        d = {"n": 0, "nOld": o["n"], "dia": o["agg"], "nat": {},
             "byrg": {k: {"n": 0, "dia": v, "nat": {}} for k, v in o["byrg"].items()}}
    show_giong(d)
    show_vote(ask("votes"))
    print("\n※ 표가 적을 때는 방향만 본다. 사람 수가 곧 믿을 만함이다.")
    # 숨기지 않는다. 2026-08-29 배선을 실제로 눌러 확인하느라 옛 칸에 한 줄이 들어갔다.
    # 지우는 길이 서버에 없어 90일 뒤 스스로 사라진다. 그때까지 빼고 읽어야 한다.
    print("※ 옛 칸 1명은 2026-08-29 **배선 시험 표**다 — 지방 nam, 지방칸 전부 bac,\n"
          "  사람같다 5칸 모두 화면 첫 자리. 사람 수와 [1]·[2]·[3]에서 빼고 읽어라.\n"
          "  (2026-11-27쯤 스스로 사라진다)")
