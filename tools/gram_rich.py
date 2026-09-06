#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""문법 설명을 **제대로** 채운다 → data/_gramrich.json

왜 (대표님 지적, 2026-08-30):
  "문법 설명 더 자세하게 해라. 모르는 단어들을 나열하면서 사용하라고 하면 되냐?
   그리고 나열한 단어는 많은데 예문은 2개냐?"
  맞다. 짜임에 'biết một chút / khá / giỏi / không giỏi lắm' 넷을 늘어놓고
  뜻은 하나도 안 적었고 예문은 둘뿐이었다. 설명은 평균 41자였다.
채우는 것
  ① kw — 짜임에 나온 **낱말마다 뜻**  ② b — 언제 쓰는지·한국어와 무엇이 다른지
  ③ ex — 나열한 조각 수만큼(최소 3개)  ④ tip — 자주 하는 실수 한 줄
쓰기: python3 tools/gram_rich.py [--limit N]
"""
import argparse, json, pathlib, re, subprocess, sys, time

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools")); import vi_kr
URL = "https://viet-ai.chaochao-app.workers.dev"
ORIGIN = "https://tpgus5119-coder.github.io"
OUT = R / "data" / "_gramrich.json"
CHUNK = 4

ASK = ("너는 베트남어를 가르치는 한국인 교사다. 아래 문법 항목을 **초급자가 혼자 읽고 알 수 있게** 채워라.\n"
       "받는 사람은 베트남에 일하러 가는 한국 사람이다. 전문용어를 풀어 써라.\n"
       "규칙\n"
       " ① kw — '짜임(k)'에 나오는 베트남어 낱말마다 [낱말, 짧은 한국어 뜻]. 낱말이 없으면 빈 배열\n"
       " ② b — 설명. **80~200자**. ㉠ 언제 쓰는지 ㉡ 한국어와 무엇이 다른지 ㉢ 자리(어디에 놓는지)\n"
       "      <b>…</b> 로 핵심만 굵게. 문장 두세 개.\n"
       " ③ ex — 예문. 짜임에 늘어놓은 조각이 n개면 **n개 이상**, 없어도 **3개 이상**.\n"
       "      쉬운 낱말로, 여덟 낱말 이내, 일터·일상에서 실제로 쓸 말.\n"
       " ④ tip — 한국 사람이 자주 틀리는 점 한 줄(40자 이내). 없으면 빈 문자열\n"
       "출력은 JSON 배열만. 설명 금지.\n"
       '[{"id":"주어진 id","kw":[["낱말","뜻"]],"b":"설명","ex":[["베트남어","한국어 뜻"]],"tip":"한 줄"}]\n\n')


def ask(items):
    body = json.dumps({"contents": [{"parts": [{"text": ASK + json.dumps(items, ensure_ascii=False)}]}]})
    p = subprocess.run(["curl", "-sS", "-X", "POST", URL, "-H", "Content-Type: application/json",
                        "-H", f"Origin: {ORIGIN}", "--data-binary", "@-"],
                       input=body, capture_output=True, text=True, timeout=240)
    t = p.stdout
    try: t = json.loads(t)["candidates"][0]["content"]["parts"][0]["text"]
    except Exception: pass
    m = re.search(r"\[.*\]", t, re.S)
    return json.loads(m.group(0)) if m else []


def main():
    a = argparse.ArgumentParser(); a.add_argument("--limit", type=int, default=0); a = a.parse_args()
    G = json.loads((R / "data" / "grammar.json").read_text(encoding="utf-8"))
    have = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    items = []
    for bi, b in enumerate(G["books"]):
        for ni, x in enumerate(b["bai"]):
            for gi, g in enumerate(x["g"]):
                gid = f"{bi}-{ni}-{gi}"
                if gid in have: continue
                items.append({"id": gid, "book": b["book"], "bai": x["t"],
                              "t": g["t"], "k": g["k"], "b": g["b"],
                              "ex": [[e["vi"], e["ko"]] for e in g["ex"]]})
    if a.limit: items = items[:a.limit]
    print(f"채울 문법 {len(items)}개 · 이미 채운 것 {len(have)}", flush=True)
    for i in range(0, len(items), CHUNK):
        part = items[i:i + CHUNK]
        try: got = ask(part)
        except Exception as e: print("  건너뜀", type(e).__name__); time.sleep(3); continue
        ids = {p["id"] for p in part}
        for g in got:
            gid = str(g.get("id", ""))
            if gid not in ids: continue
            ex = [[str(x[0]), str(x[1])] for x in (g.get("ex") or []) if isinstance(x, (list, tuple)) and len(x) >= 2]
            kw = [[str(x[0]), str(x[1])] for x in (g.get("kw") or []) if isinstance(x, (list, tuple)) and len(x) >= 2]
            if len(g.get("b", "")) < 40 or len(ex) < 3: continue     # 부실하면 안 받는다
            have[gid] = {"kw": kw, "b": g["b"], "ex": ex, "tip": str(g.get("tip", ""))}
        OUT.write_text(json.dumps(have, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  {min(i+CHUNK,len(items))}/{len(items)} · 채운 것 {len(have)}", flush=True)
        time.sleep(.3)
    print(f"끝. 채운 문법 {len(have)}개")

main()
