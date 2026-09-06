#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**두 검수가 모두 걸러낸** 그림만 새 글감으로 다시 굽는다

대표님 지시 (2026-09-02): 못 쓰는 그림은 다시.

## 어느 것을 다시 굽나
`img_audit`(글감을 읽고 판정) 와 `img_see`(그림을 보고 판정) 가 **둘 다** 안 된다고 한 것만.
한쪽만 걸린 것은 못 믿는다 — 표본을 눈으로 보니 절반이 좋은 그림이었다 (2026-09-02).

## 어떻게
① Qwen 에게 **더 구체적인 장면**을 새로 짓게 한다.
   전 글감이 왜 실패했는지 함께 준다 — '흩어진 화살표'처럼 추상적이면 아무 뜻도 안 보인다
② 씨앗을 바꿔 다시 굽는다 (같은 씨앗이면 같은 그림이 나온다)

쓰기: python3 tools/img_redo.py [--limit 20]
"""
import argparse, base64, hashlib, io, json, pathlib, re, sys, time, urllib.request

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
IMG = R / "img"
API = "http://127.0.0.1:7860/sdapi/v1/txt2img"
STYLE = (", Flat vector illustration, bold black outlines, flat pastel colors, "
         "plain white background, no text, no letters, no words")

ASK = ("아래 한국어 뜻을 그림 한 장으로 보여 주려 한다.\n"
       "지금 글감으로는 뜻이 안 보인다고 판정됐다. **더 구체적인 장면**으로 새로 지어라.\n"
       "규칙\n"
       " ① 눈에 보이는 것만 적어라 — 사람의 동작·사물·장소\n"
       " ② 글자·숫자·표는 절대 넣지 마라 (그림에 글자가 박히면 못 쓴다)\n"
       " ③ 화살표·도형 같은 기호로 때우지 마라. 실제 장면이어야 한다\n"
       " ④ 영어 한 문장, 15낱말 이내\n"
       '출력은 JSON 배열만: [{"ko":"뜻","en":"영어 장면"}]\n\n')


def make(prompt, seed):
    body = json.dumps({"prompt": prompt, "steps": 4, "shift": 1, "cfg_scale": 1,
                       "width": 512, "height": 512, "seed": seed,
                       "sampler_name": "Euler A Trailing"}).encode()
    r = urllib.request.urlopen(urllib.request.Request(
        API, body, {"Content-Type": "application/json"}), timeout=300)
    return base64.b64decode(json.loads(r.read())["images"][0])


def main():
    from PIL import Image
    a = argparse.ArgumentParser(); a.add_argument("--limit", type=int, default=0); a = a.parse_args()
    todo = json.loads(pathlib.Path("/tmp/redo.json").read_text(encoding="utf-8"))
    if a.limit:
        todo = todo[:a.limit]
    kos = sorted({ko for _, ko in todo})
    print(f"다시 구울 그림 {len(todo)}장 · 뜻 {len(kos)}가지", flush=True)

    from qwen import ask_json, up
    new = {}
    if up():
        got = ask_json(ASK, [{"ko": k} for k in kos], chunk=10, max_tokens=1500) or []
        for g in got:
            if isinstance(g, dict) and g.get("ko") and g.get("en"):
                en = str(g["en"]).strip()
                # 글자를 넣지 말라 했는데 넣은 것은 안 받는다
                if len(en) > 12 and not re.search(r"[가-힣]", en) and "text" not in en.lower():
                    new[str(g["ko"]).strip()] = en
    print(f"새 글감 {len(new)}가지", flush=True)
    if not new:
        print("Qwen 이 글감을 못 줬다"); return

    pr = R / "data" / "_imgprompts.json"
    P = json.loads(pr.read_text(encoding="utf-8"))
    made = 0
    for im, ko in todo:
        en = new.get(ko)
        if not en:
            continue
        P[ko] = en + STYLE
        try:
            # 씨앗을 바꾼다 — 같은 씨앗이면 같은 그림이 나온다
            seed = int(hashlib.sha1((im + "redo").encode()).hexdigest()[:8], 16) % 2**31
            png = make(P[ko], seed)
            Image.open(io.BytesIO(png)).convert("RGB").resize((384, 384), Image.LANCZOS) \
                 .save(IMG / im, "WEBP", quality=82, method=6)
            made += 1
            print(f"  {made} {ko} ← {en[:44]}", flush=True)
        except Exception as e:
            print(f"  실패 {ko}: {e}", flush=True)
    pr.write_text(json.dumps(P, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"끝. 다시 구운 그림 {made}")


if __name__ == "__main__":
    main()
