#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""새 일상 과정 — 꼭지마다 낱말을 고른다 → data/_new_words.json

대표님 지시 (2026-08-31): 선배 낱말·옛 일상 낱말을 다 빼고 목차부터 낱말까지 새로.
목차는 docs/일상-목차.md (40꼭지, 듀오링고 75단원·Colloquial 14과와 맞대 보강한 것).

## 어떻게 고르나
① Qwen 에게 꼭지마다 후보 60개를 시킨다 (빈도 높은 것부터, 그 장면에 실제로 쓰는 말)
② **사전으로 검증** — 우리 사전(_vi_ipa 5,381) 또는 위키낱말에 있는 말만 남긴다
   (AI 가 지어낸 말·영어를 여기서 걸러낸다. 토큰이 안 드는 검사다)
③ 앞 꼭지와 겹치는 것을 뺀다 — 한 번 배운 말은 다시 안 넣는다
④ 50개를 남긴다. 모자라면 다음 판에 더 채운다

**앱 자료는 건드리지 않는다.** 다 만들어 검수한 뒤 사람이 바꿔 넣는다.

쓰기: python3 tools/new_words.py [--only 색깔] [--round 2]
"""
import argparse, json, pathlib, re, subprocess, sys, time, unicodedata as U, urllib.parse

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
from qwen import ask_json, up

OUT = R / "data" / "_new_words.json"
WIKI = "https://vi.wiktionary.org/w/api.php?action=parse&prop=wikitext&format=json&page="
n = lambda s: U.normalize("NFC", str(s)).strip().lower()

# docs/일상-목차.md 의 40꼭지. (묶음 이름, 꼭지 이름, 이 꼭지를 마치면 할 수 있는 것)
TOPICS = [
 ("첫걸음","인사와 헤어짐","만나고 헤어질 때 인사한다"),
 ("첫걸음","호칭","anh·chị·em·cô·chú 로 나와 상대를 부른다"),
 ("첫걸음","나이와 생일","나이를 묻고 답한다"),
 ("첫걸음","이름과 소개","이름을 묻고 나를 소개한다"),
 ("첫걸음","나라와 말","어느 나라 사람인지, 무슨 말을 하는지 말한다"),
 ("첫걸음","숫자","수를 세고 읽는다"),
 ("첫걸음","가족","가족을 소개한다"),
 ("첫걸음","직업","무슨 일을 하는지 말한다"),
 ("말의 뼈대","자주 쓰는 동작","하다·가다·주다 같은 기본 동사"),
 ("말의 뼈대","가리키는 말","이것·그것·여기·저기"),
 ("말의 뼈대","이어주는 말","그리고·그러나·그래서"),
 ("말의 뼈대","정도와 빈도","조금·아주·가끔·다시"),
 ("말의 뼈대","묻는 말","무엇·어디·언제·누구·왜·얼마"),
 ("하루","시간 말하기","몇 시인지 묻고 답한다"),
 ("하루","요일과 날짜","무슨 요일·며칠인지 말한다"),
 ("하루","하루 일과","하루에 하는 일을 차례로 말한다"),
 ("하루","집과 방","사는 곳과 방 안의 것을 말한다"),
 ("하루","살림살이","집안일에 필요한 말"),
 ("하루","위치와 자리","위·아래·안·밖으로 어디 있는지 말한다"),
 ("먹고 사기","먹을거리","무엇을 먹는지 말한다 (닭·돼지·소·생선 포함)"),
 ("먹고 사기","마실거리","무엇을 마시는지 말한다"),
 ("먹고 사기","맛과 느낌","맛과 양을 말한다"),
 ("먹고 사기","식당에서 시키기","주문하고 계산한다"),
 ("먹고 사기","색깔","빛깔로 물건을 가려 말한다"),
 ("먹고 사기","값 묻고 깎기","값을 묻고 깎는다"),
 ("먹고 사기","가게에서 사기","물건을 고르고 산다"),
 ("먹고 사기","옷과 입기","옷을 고르고 치수를 말한다"),
 ("거리에서","길 묻기와 방향","길을 묻고 방향을 알아듣는다"),
 ("거리에서","탈것과 이동","오토바이·버스·택시를 타고 간다"),
 ("거리에서","도시와 장소","어디에 무엇이 있는지 말한다"),
 ("거리에서","은행·우체국·관공서","돈을 바꾸고 서류를 낸다"),
 ("거리에서","여행과 묵을 곳","표를 끊고 묵을 곳을 잡는다"),
 ("몸과 마음","몸과 아픈 곳","어디가 아픈지 말한다"),
 ("몸과 마음","병원과 약국","진료를 받고 약을 산다"),
 ("몸과 마음","기분과 마음","기분을 말한다"),
 ("몸과 마음","사람됨과 성격","사람을 설명한다"),
 ("어울려 살기","날씨와 철","날씨와 계절을 말한다"),
 ("어울려 살기","자연과 바깥","산·강·나무·동물을 말한다"),
 ("어울려 살기","쉬는 날과 취미","쉬는 날에 하는 일 (운동 포함)"),
 ("어울려 살기","친구와 어울리기","사람을 사귀고 함께 논다"),
 ("어울려 살기","잡담","안부와 날씨로 가벼운 말을 주고받는다"),
 ("어울려 살기","명절과 문화","뗏 같은 명절 자리에서 말한다"),
 ("어울려 살기","전화와 약속","전화로 약속을 잡는다"),
 ("어울려 살기","일과 직장","일터에서 기본적인 말을 한다"),
 ("어울려 살기","생각과 의견 말하기","좋다·싫다·낫다로 뜻을 밝힌다"),
 ("어울려 살기","도움이 필요할 때","곤란할 때 도움을 청한다"),
]

ASK = ("너는 베트남어 교재를 짜는 사람이다. 아래 꼭지에 넣을 낱말을 고르라.\n"
       "꼭지: {t} — {c}\n"
       "규칙\n"
       " ① **자주 쓰는 말부터.** 초급이 먼저 알아야 할 것\n"
       " ② **확실한 것만 적어라. 개수를 채우려고 없는 말을 지어내지 마라.**\n"
       "    이 꼭지에 정말 쓰는 말이 열 개뿐이면 열 개만 적어라. 많아야 {k}개.\n"
       "    (전에 색깔에서 màu mỡ='진한색' 같은 엉뚱한 말이 나왔다. màu mỡ 는 '기름진'이다)\n"
       " ③ 베트남어 표준 표기로. 성조 부호를 빠뜨리지 마라\n"
       " ④ 한국어 뜻은 **12자 이내**로 짧게. 한글만 쓴다\n"
       " ⑤ 같은 말에 màu 만 붙인 것처럼 **겹치는 말을 넣지 마라**\n"
             " ⑥ **낱말을 기계적으로 곱해서 만들지 마라.** 실제로 나왔던 가짜들이다:\n"
       "    đặt món ngon(맛있는 메뉴 주문하다) · hai trăm giờ(이백 시) ·\n"
       "    Chào buổi sáng cực muộn(극히 늦은 아침 인사) · đi cầu bóng chày(야구 치다)\n"
       "    사전에 한 낱말로 실릴 만한 것만 적어라. 네 음절을 넘기지 마라\n"
       " ⑦ 아래 이미 나온 말은 넣지 마라\n{seen}\n"
       ' 출력은 JSON 배열만: [{{"vi":"낱말","ko":"뜻"}}]\n')


def wik_ok(w, cache):
    k = n(w)
    if k in cache: return cache[k]
    try:
        r = subprocess.run(["curl", "-sS", "-m", "12", WIKI + urllib.parse.quote(w)],
                           capture_output=True, text=True, timeout=20).stdout
        j = json.loads(r)
        v = False if "error" in j else ("Tiếng Việt" in j["parse"]["wikitext"]["*"]
                                        or "{{-vie-}}" in j["parse"]["wikitext"]["*"])
    except Exception:
        v = None                      # 못 물어봄 — 버리지 않고 표시만
    cache[k] = v
    time.sleep(0.2)
    return v


def ourdict():
    s = set()
    for f in ("_vi_ipa.json", "exgloss.json"):
        p = R / "data" / f
        if p.exists():
            s |= {n(k) for k in json.loads(p.read_text(encoding="utf-8"))}
    return s


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--only"); a.add_argument("--want", type=int, default=50)
    a.add_argument("--min", type=int, default=0)
    a = a.parse_args()
    if not up():
        print("Qwen 이 안 켜져 있다"); return

    data = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    mine, cache = ourdict(), {}
    seen = {n(w["vi"]) for v in data.values() for w in v}

    for grp, topic, cando in TOPICS:
        if a.only and a.only != topic: continue
        have = data.get(topic, [])
        # 손으로 쓴 체계 꼭지(숫자·시간·묻는 말…)는 AI 가 손대지 않는다 — 조합을 지어낸다
        if have and all(w.get("src") == "손으로 씀" for w in have): continue
        if len(have) >= a.want: continue
        need = a.want - len(have)
        shown = ", ".join(sorted(list(seen))[:120])
        got = ask_json(ASK.format(k=need + 25, t=topic, c=cando, seen=shown),
                       [], chunk=1, max_tokens=3000) if False else None
        # 목록을 주는 게 아니라 꼭지 하나를 묻는 것이라 ask 를 직접 쓴다
        from qwen import ask
        txt = ask(ASK.format(k=min(need + 10, 60), t=topic, c=cando, seen=shown), max_tokens=3000)
        m = re.search(r"\[.*\]", txt, re.S)
        cand = []
        if m:
            try: cand = [x for x in json.loads(m.group(0)) if isinstance(x, dict)]
            except Exception: cand = []

        added = 0
        for c in cand:
            vi, ko = (c.get("vi") or "").strip(), (c.get("ko") or "").strip()
            if not vi or not ko or n(vi) in seen: continue
            # 뜻에 한글이 아닌 글자가 섞이면 버린다 (아랍 문자가 샌 적이 있다)
            if re.search(r"[^\uAC00-\uD7A3\u3131-\u318E0-9 ·()~,./%\-]", ko): continue
            src = "우리사전" if n(vi) in mine else None
            if not src:
                ok = wik_ok(vi, cache)
                if ok is False: continue          # 사전에 없는 말은 버린다
                src = "위키낱말" if ok else "확인못함"
            have.append({"vi": vi, "ko": ko, "src": src})
            seen.add(n(vi)); added += 1
            if len(have) >= a.want: break
        data[topic] = have
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  {topic:16} {len(have):3}/{a.want}  (이번에 {added}개)", flush=True)

    tot = sum(len(v) for v in data.values())
    print(f"\n모은 낱말 {tot} · 꼭지 {len(data)}/{len(TOPICS)}")


# 불러오기만 할 때는 돌지 않는다 — 다른 도구가 TOPICS 같은 것을
# 가져다 쓸 때 낱말 모으기가 통째로 다시 도는 사고가 있었다 (2026-09-01).
if __name__ == "__main__":
    main()
