#!/usr/bin/env python3
"""화면에 나오는 한국어 가운데 베트남어 번역이 없는 것을 찾는다.

왜 필요한가:
  베트남 분이 쓰는 화면은 전부 베트남어여야 한다. 그런데 app.js는 크고,
  한국어 글자는 코드 곳곳에 흩어져 있다. 눈으로 훑어서는 빠진 것을 못 찾는다.
  그래서 "화면에 나갈 만한 자리"에 있는 한국어를 뽑아 UIVI 사전과 대조한다.

한계(솔직히):
  이 도구는 정규식으로 뽑는다. 변수로 조립되는 글(`'남은 ' + n + '개'`)은 못 잡고,
  코드 주석에 있는 한국어를 잘못 잡을 수도 있다. 그래서 '완벽한 목록'이 아니라
  '적어도 이만큼은 빠졌다'는 하한선으로 읽어야 한다.
"""
import json, os, re, sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
APP = os.path.join(ROOT, "app.js")

HANGUL = re.compile(r"[가-힣]")

# 화면에 나가는 자리들 — 여기 들어간 문자열만 본다
PATTERNS = [
    re.compile(r"el\(\s*'[^']*'\s*,\s*(?:'[^']*'|null)\s*,\s*'((?:[^'\\]|\\.)*)'"),   # el(tag, cls, '글')
    re.compile(r"show\(\s*'[^']*'\s*,\s*'((?:[^'\\]|\\.)*)'"),                        # show(view, '제목')
    re.compile(r"popup\(\s*'((?:[^'\\]|\\.)*)'"),                                     # popup('글')
    re.compile(r"\.textContent\s*=\s*'((?:[^'\\]|\\.)*)'"),
    re.compile(r"\.placeholder\s*=\s*'((?:[^'\\]|\\.)*)'"),
    re.compile(r"\.title\s*=\s*'((?:[^'\\]|\\.)*)'"),
    re.compile(r"confirm\(\s*`?'?((?:[^'`\\]|\\.)*)'?`?\s*\)"),
]

def strip_code(src):
    """주석 안의 한국어를 UI 글로 잘못 세지 않도록 주석을 먼저 지운다."""
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    src = re.sub(r"^\s*//.*$", "", src, flags=re.M)
    return src

def load_uivi(src):
    m = re.search(r"const UIVI = \{(.*?)\n\};", src, re.S)
    if not m:
        return {}
    out = {}
    for k, v in re.findall(r"'((?:[^'\\]|\\.)*)'\s*:\s*'((?:[^'\\]|\\.)*)'", m.group(1)):
        out[k] = v
    return out

def main():
    raw = open(APP, encoding="utf-8").read()
    uivi = load_uivi(raw)
    src = strip_code(raw)

    found = set()
    for pat in PATTERNS:
        for s in pat.findall(src):
            s = s.strip()
            if HANGUL.search(s):
                found.add(s)

    # ${...} 가 든 글은 실행할 때 값이 박혀 글자가 달라진다 — 사전으로는 못 옮긴다.
    # 옮기려면 코드를 조각내야 하므로, 못 옮기는 것으로 따로 세어 솔직히 보고한다.
    dynamic = sorted(s for s in found if "${" in s)
    fixed = sorted(s for s in found if "${" not in s)
    missing = [s for s in fixed if s not in uivi]
    have = len(fixed) - len(missing)
    pct = have / len(fixed) * 100 if fixed else 0

    if "--json" in sys.argv:                    # 번역 작업용 — 빠진 것만 JSON으로
        print(json.dumps(missing, ensure_ascii=False, indent=1))
        return 0

    only = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else None
    show = [m for m in missing if only in m] if only else missing

    print(f"사전으로 옮길 수 있는 문구 {len(fixed)}개 · 번역됨 {have}개 ({pct:.0f}%) · 빠짐 {len(missing)}개")
    print(f"변수가 섞여 사전으로 못 옮기는 문구 {len(dynamic)}개 (코드를 조각내야 함)")
    if show:
        print("\n--- 번역이 없는 문구 ---")
        for s in show:
            print("  " + (s if len(s) < 90 else s[:87] + "…"))
    return 0 if not missing else 1

if __name__ == "__main__":
    sys.exit(main())
