#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**그림을 실제로 보고** 검수한다 → data/_imgsee.json

대표님이 눈 달린 모델(Qwen3-VL 8B)을 받아 주셨다 (2026-09-02).
지금까지 그림 검수는 **글감만 읽었다** — 그림 자체는 아무도 못 봤다.

## 묻는 법이 중요하다 (실측)
  "이 그림이 무엇이냐"        → 다섯 중 둘을 틀렸다 (자수를 '꽃', 기록을 '배달원')
  "이 그림이 X 로 보이나 예/아니오" → 훨씬 쉬운 물음이다. 고르는 일이라 지어낼 자리가 없다
그래서 **뜻을 함께 주고 예/아니오만** 묻는다.

## 다른 검수와 다른 점
  img_audit.py  = 글감(문장)이 뜻을 알려주나  — 글과 글
  img_see.py    = **그림이** 뜻을 알려주나    — 그림과 글  ← 이 파일

webp 는 못 읽는다 → png 로 바꿔 보낸다 (실측: 'must be a base64 encoded image')

쓰기: python3 tools/img_see.py [--limit 300]
"""
import argparse, base64, io, json, pathlib, subprocess, time

R = pathlib.Path(__file__).resolve().parent.parent
OUT = R / "data" / "_imgsee.json"
URL = "http://localhost:1234/v1/chat/completions"
MODEL = "qwen/qwen3-vl-8b"


def see(png_b64, ko):
    q = (f"이 그림이 '{ko}' 를 나타내나?\n"
         "예 또는 아니오 하나만 답하라. 설명하지 마라.\n"
         "그림만 보고 '{ko}' 가 떠오르면 예, 아니면 아니오.")
    body = json.dumps({"model": MODEL, "temperature": 0.1, "max_tokens": 40,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": q.replace("{ko}", ko)},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + png_b64}}]}]})
    try:
        r = subprocess.run(["curl", "-sS", "-m", "180", "-X", "POST", URL,
                            "-H", "Content-Type: application/json", "--data-binary", "@-"],
                           input=body, capture_output=True, text=True, timeout=200).stdout
        t = json.loads(r)["choices"][0]["message"]["content"].strip()
        return None if not t else ("예" in t[:6] and "아니" not in t[:6])
    except Exception:
        return None


def main():
    from PIL import Image
    a = argparse.ArgumentParser(); a.add_argument("--limit", type=int, default=0); a = a.parse_args()
    o = json.loads((R / "data" / "order.json").read_text(encoding="utf-8"))
    done = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}

    def walk(v):
        for t in (v.get("tracks") or [v]):
            for c in t.get("chapters", []):
                for l in c["lessons"]:
                    yield from l["words"]

    # **하루 5분(days.json) 그림도 본다.** order.json 만 보다가 1,080장을 통째로
    # 빠뜨렸다 (2026-09-02 실측). 낱말이 사는 곳이 두 군데다.
    src = [w for v in o["vols"] for w in walk(v)]
    dp = R / "data" / "days.json"
    if dp.exists():
        dj = json.loads(dp.read_text(encoding="utf-8"))
        src += [w for x in dj.get("days", []) for w in (x.get("words") or [])]

    todo, seen = [], set()
    if True:
        for w in src:
            im = w.get("img")
            if not im or im in seen or im in done or not (R / "img" / im).exists():
                continue
            seen.add(im); todo.append((im, w["ko"]))
    if a.limit:
        todo = todo[:a.limit]
    print(f"볼 그림 {len(todo)}장", flush=True)

    no = 0
    for i, (im, ko) in enumerate(todo, 1):
        buf = io.BytesIO()
        Image.open(R / "img" / im).convert("RGB").resize((256, 256)).save(buf, "PNG")
        v = see(base64.b64encode(buf.getvalue()).decode(), ko)
        if v is None:
            continue
        done[im] = {"ko": ko, "ok": bool(v)}
        if not v:
            no += 1
        if i % 25 == 0:
            OUT.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  {i}/{len(todo)} · 안 보인다고 한 것 {no}", flush=True)
    OUT.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"끝. 본 그림 {len(done)} · 뜻이 안 보이는 것 {sum(1 for x in done.values() if not x['ok'])}")


if __name__ == "__main__":
    main()
