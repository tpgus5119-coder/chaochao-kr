#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""과정 낱말의 그림을 Draw Things 로 굽는다 → img/w-*.webp · order.json 에 붙인다

프롬프트는 tools/img_prompt_gen.py 가 만든 data/_imgprompts.json 에서 읽는다.
파일 이름은 뜻에서 만든다(w-<해시>.webp) — 같은 뜻이면 같은 그림을 나눠 쓴다.
이미 있는 그림은 건너뛴다. 같은 이름은 늘 같은 씨앗이라 다시 돌려도 같은 그림이 나온다.
쓰기: python3 tools/gen_word_img.py [--limit N]
"""
import argparse, base64, hashlib, io, json, pathlib, re, time, urllib.request, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent
API = "http://127.0.0.1:7860/sdapi/v1/txt2img"
IMG = R / "img"
# 이 모델은 **FLUX.1 [schnell]** 이다 (Draw Things 설정에서 확인, 2026-08-30).
# schnell 은 **시간축 증류(timestep-distilled)** 모델이고 가이던스 임베딩이 아예 없다
# (BFL 공식 util.py: flux-schnell 의 guidance_embed=False · cli.py: "sets the guidance (flux-dev only)").
# 그래서 CFG 를 안 쓴다 → **negative prompt 가 아예 안 먹는다.**
#   그래서 "글자 금지·손 금지"를 negative 에 적어 둔 것은 처음부터 무효였다.
#   프롬프트 안의 부정어("no text")는 더 나쁘다 — 확산 모델은 토큰을 긍정으로 읽어
#   오히려 그것을 불러온다(전에 '손 감춰라'가 손을 불렀다).
# 확정 설정 (2026-08-30, 공식 문서 + 실측):
#   · 모델 FLUX.1 [schnell] — Apache 2.0 이라 **상업 이용이 자유롭다**(dev 는 비상업)
#   · steps 8      — 2026-08-31 재검증. BFL 공식 기본값은 4(cli.py: num_steps = 4 if flux-schnell)
#                    이지만 Draw Things 공식 위키는 schnell 을 "4-8 steps" 로 적는다.
#                    실측(같은 씨앗 3낱말 비교): 8스텝이 사람 몸·소품이 뚜렷하게 낫다
#                    ('배를 타다'가 4스텝에선 웃통 벗은 이상한 몸, 8스텝에선 제대로 옷 입음).
#                    값: 22초 → 35초. 품질이 우선이라 8을 쓴다.
#   · cfg 1        — schnell 은 guidance-distilled 라 CFG 를 안 쓴다
#   · Euler A Trailing — Draw Things 공식이 "Trailing 계열"을 권한다.
#                        실측: 같은 그림을 39.7초에 굽는다(DPM++2M Karras 는 68.7초)
#   · shift 1      — BFL 공식 코드가 schnell 에서만 시프트를 끈다
#                    (cli.py: shift=(name != "flux-schnell")). 위키의 "Shift 2.8-4" 는 dev 용이다.
#   · 512×512      — 2026-08-31 실측으로 1024 보다 낫다고 확인. 1024 는 같은 4~8스텝을
#                    4배 넓은 화면에 나눠 쓰느라 그림이 밋밋해진다(침대·배 그림에서 소품이 사라졌다).
#                    최종 표시는 384×384 라 512 로 굽고 줄이는 지금 방식이 맞다.
# schnell 은 **4단계로 증류된 모델**이다. 8단계로 구우면 시간만 두 배 들고 얻는 것이 없다.
# (Black Forest Labs 공식 예제도 schnell 은 num_steps=4 다. 실측: 8단계 1.6장/분)
STEPS, GUID, SHIFT, SAMPLER = 4, 1, 1, "Euler A Trailing"

def name_of(ko):
    h = hashlib.sha1(U.normalize("NFC", ko).encode()).hexdigest()[:10]
    return f"w-{h}.webp"

def seed_of(n):
    return int(hashlib.sha1(n.encode()).hexdigest()[:8], 16) % (2 ** 31)

def make(prompt, seed):
    body = json.dumps({"prompt": prompt, "steps": STEPS, "shift": SHIFT,
                       "width": 512, "height": 512, "cfg_scale": GUID, "seed": seed,
                       "sampler_name": SAMPLER}).encode()
    req = urllib.request.Request(API, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return base64.b64decode(json.loads(r.read())["images"][0])

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    from PIL import Image
    pr = json.loads((R / "data" / "_imgprompts.json").read_text(encoding="utf-8"))
    o = json.loads((R / "data" / "order.json").read_text(encoding="utf-8"))

    def walk(v):
        for t in (v.get("tracks") or [v]):
            for c in t["chapters"]:
                for l in c["lessons"]: yield from l["words"]

    need, seen = [], set()
    for v in o["vols"]:
        for w in walk(v):
            if w.get("img"): continue
            k = re.sub(r"\s+", " ", U.normalize("NFC", w["ko"]).split("/")[0].split("(")[0]).strip()
            if k not in pr or k in seen: continue
            seen.add(k); need.append(k)
    if a.limit: need = need[:a.limit]
    print(f"구울 그림 {len(need)}장", flush=True)
    made = skip = fail = 0
    for i, k in enumerate(need, 1):
        fn = name_of(k)
        p = IMG / fn
        if p.exists(): skip += 1; continue
        try:
            png = make(pr[k], seed_of(fn))
            im = Image.open(io.BytesIO(png)).convert("RGB").resize((384, 384), Image.LANCZOS)
            im.save(p, "WEBP", quality=82, method=6)
            made += 1
        except Exception as e:
            fail += 1
            if fail <= 3: print("  실패", k, e, flush=True)
        if i % 25 == 0: print(f"  {i}/{len(need)} · 만듦 {made} · 건너뜀 {skip} · 실패 {fail}", flush=True)
    print(f"끝. 만듦 {made} · 건너뜀 {skip} · 실패 {fail}", flush=True)
main()
