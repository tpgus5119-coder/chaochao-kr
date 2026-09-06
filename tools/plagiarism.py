#!/usr/bin/env python3
"""베낌 검사 — 우리 문항이 실제 기출과 우연히라도 겹치지 않았음을 기계로 증명한다.

왜 필요한가:
  TOPIK 자료실은 "영리목적 이용은 국립국제교육원의 이용 허락을 받아야 한다"고 못 박고
  문항 속 자료에는 원저작자가 또 따로 있다고 밝힌다. 우리는 형식만 따르고 문항은
  새로 쓰는데, '정말 안 베꼈다'는 것은 말이 아니라 기록으로 남겨야 한다.

방법:
  기출 원문(문자 인식으로 글자화한 것)에서 연속 N글자 덩어리를 전부 뽑아 놓고,
  우리 문항의 모든 문장을 같은 방식으로 훑어 겹치는 덩어리가 있는지 본다.
  공백·문장부호는 지우고 비교한다("띄어쓰기만 바꿔서" 빠져나가지 못하게).

쓰는 법:
    python3 tools/plagiarism.py <기출텍스트폴더>
    python3 tools/plagiarism.py <기출텍스트폴더> --n 10     # 더 깐깐하게
겹치면 종료 코드 1 — 배포 스크립트에서 그대로 막을 수 있다.
"""
import json, os, re, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = 12                      # 연속 12글자가 같으면 우연이 아니다

# 시험지 껍데기와 고정 발문은 서식이라 겹쳐도 된다 — 저작물이 아니다.
SKIP = [
    "다음을듣고물음에답하십시오", "다음을읽고물음에답하십시오", "알맞은것을고르십시오",
    "다음을듣고보기와같이", "여기는어디입니까", "무엇에대한글인지고르십시오",
    "다음을읽고내용이같은것을고르십시오", "그림을보고맞는것을고르십시오",
    "에알맞은것을고르십시오", "다음설명에맞는단어", "잘듣고알맞은대답을고르십시오",
    "잘듣고알맞은그림을고르십시오", "대화를듣고물음에답하십시오",
    "한국어능력시험", "국립국제교육원", "외국인등록증을가지고오십시오",
    # TOPIK II 고정 발문 — 12회차 내내 글자까지 같은 서식이다
    "다음대화를잘듣고이어질수있는말을고르십시오",
    "다음대화를잘듣고이어서할행동을고르십시오",
    "다음을듣고내용과같은것을고르십시오", "들은내용과같은것을고르십시오",
    "다음을듣고중심생각을고르십시오", "중심생각으로알맞은것을고르십시오",
    "다음을듣고물음에답하십시오", "다음대화를잘듣고물음에답하십시오",
    "무엇에대해말하고있습니까", "다음을읽고물음에답하십시오",
    "다음을듣고여자의중심생각을고르십시오", "다음을듣고남자의중심생각을고르십시오",
    "여자의중심생각으로알맞은것을고르십시오", "남자의중심생각으로알맞은것을고르십시오",
    "여자는이어서무엇을하겠습니까", "남자는이어서무엇을하겠습니까",
    "여자는무엇에대해말하고있습니까", "남자는무엇에대해말하고있습니까",
    "남자는무엇을강조하고있습니까", "여자는무엇을강조하고있습니까",
    # 물음을 세우는 틀 — 어느 시험지에나 있는 말이라 서식으로 친다
    "에대한설명으로맞는것은", "으로알맞은것은무엇입니까", "로알맞은것을고르십시오",
    "다음물음에알맞은답을고르십시오", "무엇이라고합니까", "어디입니까",
    "몇월며칠입니까", "내용과같은것을고르십시오",
]


# 물음을 세우는 틀 — 어느 시험지에나 있는 말이라 저작물이 아니다.
# 양쪽(기출·우리 글)에서 똑같이 지우고 나서 견준다. 한쪽만 지우면
# '앞 낱말 + 틀' 이 이어 붙은 가짜 겹침이 잡힌다.
#
# **공식 발문도 여기에 넣는다.** 국립국제교육원이 「TOPIK 발문 안내」(2020.7.31.)로
# 문구를 공개해 놓았고, 우리는 시험을 똑같이 만들려고 그 문구를 일부러 그대로 쓴다.
# 즉 발문이 겹치는 것은 베낀 것이 아니라 **맞춘 것**이다. 지문·보기가 겹치면 베낀 것이다.
# 그래서 설계도에 적힌 발문은 양쪽에서 지우고, 나머지만 견준다.
def _bp_stems():
    try:
        import topik_blueprint as BP
    except Exception:
        return []
    out = []
    for f in BP.FORMS.values():
        for b in f["items"]:
            out.append(b["stem"])
            out += list(b.get("sub") or [])
    return [re.sub(r"[^0-9A-Za-z가-힣]", "", s) for s in out]


FRAME = re.compile(
    "(" + "|".join(sorted(_bp_stems(), key=len, reverse=True) + [
        "에대한설명으로맞는것은무엇입니까", "에대한설명으로맞는것은", "으로맞는것은무엇입니까",
        "으로알맞은것은무엇입니까", "으로알맞은것을고르십시오", "로알맞은것을고르십시오",
        "알맞은것을고르십시오", "것을고르십시오", "무엇이라고합니까", "무엇입니까", "어디입니까",
        "몇월며칠입니까", "물음에답하십시오", "다음물음에알맞은답을고르십시오"]) + ")")


def flat(s):
    s = re.sub(r"[^0-9A-Za-z가-힣]", "", str(s or ""))
    return FRAME.sub("", s)


def grams(s, n):
    s = flat(s)
    return {s[i:i + n] for i in range(len(s) - n + 1)}


def our_texts():
    """검사할 우리 글 — 시험 문항과 두 과정의 대화문·지문 전부."""
    out = []
    ex = json.load(open(f"{ROOT}/data/ko_exams.json", encoding="utf-8"))
    for e in ex["exams"]:
        for q in e["questions"]:
            for k in ("stem", "passage", "ptitle", "heard"):
                if q.get(k):
                    out.append((f"{e['id']} {e['set']}회 {q['no']}번 {k}", q[k]))
            for o in q.get("options", []):
                out.append((f"{e['id']} {e['set']}회 {q['no']}번 보기", o))
            for s in q.get("script", []) + [a.get("t") if isinstance(a, dict) else a
                                            for a in q.get("audio", [])]:
                if s:
                    out.append((f"{e['id']} {e['set']}회 {q['no']}번 대본", s))
    for f, lang in ((f"{ROOT}/data/ko_days.json", "ko"), (f"{ROOT}/data/days.json", "ko")):
        try:
            for d in json.load(open(f, encoding="utf-8"))["days"]:
                for ln in (d.get("dialog") or {}).get("lines", []):
                    if ln.get(lang):
                        out.append((f"{os.path.basename(f)} {d.get('day')}강", ln[lang]))
        except Exception:
            pass
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src_dir = sys.argv[1]
    n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else N

    ref, files = set(), sorted(glob.glob(f"{src_dir}/*.txt"))
    if not files:
        sys.exit(f"기출 텍스트가 없습니다: {src_dir}/*.txt")
    for f in files:
        ref |= grams(open(f, encoding="utf-8", errors="replace").read(), n)
    skip = {g for s in SKIP for g in grams(s, n)}
    ref -= skip
    print(f"기출 원문 {len(files)}개 · 비교용 {n}글자 덩어리 {len(ref):,}개 "
          f"(서식 문구 {len(skip):,}개는 뺌)")

    # 줄 단위로 자른 뒤 비교한다. 붙여서 비교하면 '고정 발문 + 우리 문장'이 한 덩어리가 되어
    # 발문 꼬리와 우리 첫 낱말이 이어 붙은 가짜 겹침이 잡힌다.
    hits, checked = [], 0
    for where, text in our_texts():
        for line in re.split(r"[\n。.!?]", str(text)):
            if len(flat(line)) < n:
                continue
            checked += 1
            bad = grams(line, n) & ref
            if bad:
                hits.append((where, line, sorted(bad)[:3]))

    print(f"우리 글 {checked:,}조각 검사")
    if not hits:
        print(f"겹침 0건 — 연속 {n}글자가 같은 곳이 한 군데도 없습니다.")
        return 0
    print(f"겹침 {len(hits)}건:")
    for where, text, bad in hits[:40]:
        print(f"  [{where}] {str(text)[:56]}")
        print(f"      겹친 덩어리: {bad}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
