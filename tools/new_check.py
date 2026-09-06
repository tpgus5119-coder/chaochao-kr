#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""새 낱말의 **뜻**을 검수한다 → data/_new_words.json 에 표시를 단다

낱말이 사전에 있다고 뜻까지 맞는 것은 아니다.
실제로 màu mỡ(기름진)를 '진한색'으로, đen nhánh(칠흑)을 '회색'으로 내놓은 적이 있다.

## 어떻게 (토큰을 아끼려고 사전 먼저)
① **위키낱말 뜻풀이**를 받아 온다. 우리 뜻의 낱말이 거기 있으면 통과 — 공짜다
② 못 가른 것만 Qwen 에게 "이 뜻이 맞나" 묻는다

표시: ok=맞다 · check=사람이 봐야 함 · bad=틀렸다(고칠 안이 fix 에)
쓰기: python3 tools/new_check.py
"""
import json, pathlib, re, subprocess, sys, time, unicodedata as U, urllib.parse

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
OUT = R / "data" / "_new_words.json"
WIKI = "https://vi.wiktionary.org/w/api.php?action=parse&prop=wikitext&format=json&page="


def wik_text(w):
    try:
        r = subprocess.run(["curl", "-sS", "-m", "12", WIKI + urllib.parse.quote(w)],
                           capture_output=True, text=True, timeout=20).stdout
        j = json.loads(r)
        return "" if "error" in j else j["parse"]["wikitext"]["*"]
    except Exception:
        return ""


def main():
    data = json.loads(OUT.read_text(encoding="utf-8"))
    todo = [(t, w) for t, ws in data.items() for w in ws if "v" not in w]
    print(f"검수할 낱말 {len(todo)}", flush=True)

    rest = []
    for i, (t, w) in enumerate(todo, 1):
        # ① 위키낱말 뜻풀이에 우리 뜻의 낱말이 보이나 (한자어·고유명사는 그대로 나온다)
        txt = wik_text(w["vi"])
        key = re.sub(r"[^가-힣]", "", w["ko"])[:2]
        if txt and key and key in txt:
            w["v"] = "ok"; w["by"] = "위키낱말"
        else:
            rest.append((t, w))
        if i % 100 == 0:
            OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  {i}/{len(todo)}", flush=True)
        time.sleep(0.15)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"사전으로 통과 {len(todo)-len(rest)} · AI 가 볼 것 {len(rest)}", flush=True)

    if not rest:
        return
    from qwen import ask_json, up
    if not up():
        print("Qwen 이 안 켜져 있다 — AI 검수는 건너뛴다"); return
    ASK = ("아래 [베트남어, 한국어 뜻] 이 맞는지 보라.\n"
           "  ok   : 뜻이 맞다\n"
           "  bad  : 뜻이 틀렸다 — 맞는 뜻을 fix 에 12자 이내 한글로 적어라\n"
           "규칙: 여러 뜻 중 하나만 적은 것은 ok 다. 확신이 없으면 ok.\n"
           '출력은 JSON 배열만: [{"vi":"낱말","v":"ok|bad","fix":"맞는 뜻 또는 빈칸"}]\n\n')
    got = ask_json(ASK, [{"vi": w["vi"], "ko": w["ko"]} for _, w in rest], chunk=20)
    by = {g.get("vi"): g for g in got if isinstance(g, dict)}
    for t, w in rest:
        g = by.get(w["vi"]) or {}
        w["v"] = g.get("v") or "check"
        w["by"] = "AI"
        if g.get("fix"):
            w["fix"] = g["fix"]
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    from collections import Counter
    c = Counter(w.get("v") for ws in data.values() for w in ws)
    print(f"\n맞다 {c.get('ok',0)} · 틀렸다 {c.get('bad',0)} · 봐야 함 {c.get('check',0)}")


# 불러오기만 할 때는 돌지 않는다 — 다른 도구가 TOPICS 같은 것을
# 가져다 쓸 때 낱말 모으기가 통째로 다시 도는 사고가 있었다 (2026-09-01).
if __name__ == "__main__":
    main()
