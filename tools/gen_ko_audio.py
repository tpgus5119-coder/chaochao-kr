#!/usr/bin/env python3
"""한국어 과정·모의고사에 쓸 소리를 미리 구워 둔다.

베트남어 쪽 gen_audio.py와 같은 방식이다 — 실시간 합성이 아니라 파일로 구워 둬야
느린 폰에서도 바로 나오고, 자릿수 큰 요금이 안 나온다.
음성은 edge-tts(무료). 파일 이름은 글자의 sha1 앞 12자리라, 같은 말은 한 번만 굽는다.

사용:  python3 tools/gen_ko_audio.py [--slow]
"""
import asyncio, hashlib, json, pathlib, sys
import edge_tts

ROOT = pathlib.Path(__file__).resolve().parent.parent
# 남녀 하나씩 — 듣기 문항에서 두 사람이 주고받는 말을 만들려면 둘 다 있어야 한다
VOICES = {"f": "ko-KR-SunHiNeural", "m": "ko-KR-InJoonNeural"}
SLOW = "--slow" in sys.argv

def key(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:12]

def collect():
    """소리가 필요한 한국어 문자열을 모은다.

    need  = 소리를 구울 후보 전체
    force = 교재로 직접 고른 것(단어장·기본기·문화·문법·날마다) — 무조건 굽는다.
            글자만 보고 거르면 '이(2)'·'가(ㄱ 소리)'처럼 조사와 모양이 같은 낱말이
            통째로 사라진다.
    """
    need, force = {}, set()

    # 1) 모의고사에 나오는 말 — 문항의 정답 낱말과 보기(한국어인 것만)
    p = ROOT / "data" / "ko_exams.json"
    if p.exists():
        ex = json.loads(p.read_text(encoding="utf-8"))
        for e in ex["exams"]:
            for q in e["questions"]:
                if q.get("word"):
                    need[q["word"]] = "word"
                # 보기가 한국어인 유형만 (word2vi 는 보기가 베트남어, listen_pic 은 그림이라 뺀다)
                if q["type"] in ("dfn2word", "vi2word", "pic2word"):
                    for o in q["options"]:
                        need.setdefault(str(o), "word")
                # 듣기 문항이 들려줄 말 — 이게 없으면 듣기 시험 자체가 안 돌아간다.
                # 대화는 남녀가 갈리므로 {"v":목소리,"t":글} 꼴로 온다.
                # 듣기 문항이 들려줄 말은 무조건 굽는다 — 없으면 그 문항을 아예 못 푼다
                for a in q.get("audio") or []:
                    if isinstance(a, dict):
                        need[a["t"]] = "line:" + a.get("v", "f"); force.add(a["t"])
                    else:
                        need.setdefault(str(a), "word"); force.add(str(a))

    # 1.5) 기초 문법 — 목표 문장(제목)과 예문. 둘 다 문장이라 통으로 읽는다
    p = ROOT / "data" / "ko_grammar.json"
    if p.exists():
        g = json.loads(p.read_text(encoding="utf-8"))
        for item in g["items"]:
            if item.get("title_ko"):
                need.setdefault(item["title_ko"], "sent"); force.add(item["title_ko"])
            for ex in item["examples"]:
                if ex.get("ko"):
                    need.setdefault(ex["ko"], "sent"); force.add(ex["ko"])

    # 1.6) 기본기·한국 문화 — 표의 각 줄. 'say'가 있으면 그것을 읽는다
    #      (자모 'ㅏ'는 그대로 읽히지 않는다 — '아'처럼 소리 낼 수 있는 글자를 따로 적어 둔다)
    for name in ("ko_basics.json", "ko_culture.json"):
        p = ROOT / "data" / name
        if not p.exists():
            continue
        j = json.loads(p.read_text(encoding="utf-8"))
        for item in j["items"]:
            for row in item.get("table", []):
                t = row.get("say") or row.get("ko")
                if t:
                    need.setdefault(t, "word"); force.add(t)

    # 1.7) 날마다 배우는 과정 — 단어와 대화 줄
    p = ROOT / "data" / "ko_days.json"
    if p.exists():
        dj = json.loads(p.read_text(encoding="utf-8"))
        for day in dj["days"]:
            for w in day.get("words", []):
                if w.get("ko"):
                    need.setdefault(w["ko"], "word"); force.add(w["ko"])
            for line in day.get("dialog", {}).get("lines", []):
                if line.get("ko"):
                    need.setdefault(line["ko"], "sent"); force.add(line["ko"])

    # 2) 한국어 과정 어휘 — 등급 A·B (기초부터. C까지 한 번에 구우면 파일이 너무 많다)
    p = ROOT / "data" / "_ko_words.json"
    if p.exists():
        for w in json.loads(p.read_text(encoding="utf-8")):
            if w.get("grade") in ("A", "B") and w.get("ko"):
                need.setdefault(w["ko"], "word")

    # 소리를 굽지 않는 것 둘.
    #  ① 조사("을", "에") — 낱말이 아니라 문법 조각이라 따로 들려줄 일이 없다.
    #  ② 홀자모("ㅏ", "ㄱ") — TTS가 글자 이름을 읽거나 아예 못 읽는다. 대신 위 1.6에서
    #     say 필드('아', '가')를 대신 굽는다.
    # ⚠ 예전에는 "한 글자면 조사겠지" 하고 len<=1 을 통째로 걸렀는데, 그 바람에
    #   개·눈·밥·집·천·칼 같은 한 글자 낱말이 다 빠져 **듣기 문항 6개가 소리 없이
    #   출제됐다**(재생을 눌러도 아무 일이 없어 풀 수가 없었다). 조사는 목록으로 명시한다.
    # ⚠ '이'와 '가'는 조사이기도 하지만 숫자 2이기도 하고 자모 ㅣ·ㄱ의 소리이기도 하다.
    #   그래서 "조사니까 빼라"를 글자만 보고 정하면 또 구멍이 난다 — 교재로 직접 고른
    #   낱말(force)은 무슨 글자든 반드시 굽고, 시험 보기에서 딸려 온 것만 조사 검사를 한다.
    JOSA = {"을", "를", "이", "가", "은", "는", "에", "의", "와", "과", "도", "만",
            "로", "께", "부터", "까지", "에서", "한테", "에게", "하고", "보다"}
    def skip(t):
        t = t.strip()
        if not t:
            return True
        if t in force:
            return False
        if t in JOSA:
            return True
        # 자모만으로 된 것(ㄱ, ㅏ, ㄷㅅㅆㅈㅊㅌㅎ …)은 소리로 못 읽는다
        return all("ㄱ" <= ch <= "ㆎ" for ch in t)
    return {t: k for t, k in need.items() if not skip(t)}

async def one(text, vid, vname, slow):
    sub = "slow" if slow else "n"
    path = ROOT / "audio" / f"ko-{vid}" / sub / f"{key(text)}.mp3"
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    kw = {"rate": "-40%"} if slow else {}
    await edge_tts.Communicate(text, vname, **kw).save(str(path))
    return True

SEM = asyncio.Semaphore(8)

async def guarded(*a):
    async with SEM:
        for attempt in range(3):
            try:
                return await one(*a)
            except Exception as e:
                if attempt == 2:
                    print("실패:", a[0], e, file=sys.stderr)
                    return False
                await asyncio.sleep(1 + attempt)

async def main():
    need = collect()
    print(f"구울 말 {len(need)}개 · 목소리 {len(VOICES)}종", file=sys.stderr)
    jobs = []
    for text in need:
        for vid, vname in VOICES.items():
            jobs.append(guarded(text, vid, vname, False))
            if SLOW:
                jobs.append(guarded(text, vid, vname, True))
    made = 0
    for i in range(0, len(jobs), 200):
        chunk = await asyncio.gather(*jobs[i:i + 200])
        made += sum(1 for x in chunk if x)
        print(f"  {min(i+200, len(jobs))}/{len(jobs)} · 새로 구움 {made}", file=sys.stderr)

    # 앱이 글자→파일을 찾아갈 수 있게 색인을 남긴다
    idx = {t: key(t) for t in need}
    (ROOT / "data" / "ko_audio_index.json").write_text(
        json.dumps(idx, ensure_ascii=False), encoding="utf-8")
    print(f"끝 — 새로 {made}개 · 색인 {len(idx)}개", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(main())
