#!/usr/bin/env python3
"""남·북 말씨 확인용 소리 넉 장을 만든다 — **블라인드가 아니다.**

무엇을 알고 싶은가: 우리가 쓰거나 쓸 만한 네 목소리가 각각 **북부인지 남부인지**.
  A Edge      vi-VN-HoaiMyNeural  — 지금 앱의 북부 목소리
  B Supertonic 3 (F1, lang=vi)    — 31개 언어 다국어 모델. **방언 설정이 없다 = 모름**
  C Chirp 3 HD (vi-VN, 여성)      — 구글. vi-VN 단일 로케일(40종), 남부 옵션 0
  D 우리 남부 (VITS, sf)           — 앱에서 '남부'로 내보내는 바로 그 소리

  A·C·D 는 무엇인지 이미 안다. **B 하나를 가리려고** 만드는 판이고,
  A·C(북부로 알려진 것)와 D(남부로 만든 것)는 **귀의 잣대** 노릇을 한다.
  그래서 이름을 감추지 않는다 — 가리면 잣대가 잣대 노릇을 못 한다.

문장 고르는 법 — 아무 문장이나 되는 게 아니다. 남·북이 갈리는 자리가 들어야 한다:
  · ngã(~)와 hỏi(?)가 **한 문장에 같이** — 남부는 이 둘을 하나로 합쳐 낸다. 가장 센 잣대.
  · s / x   — 북부는 둘 다 /s/, 남부는 s 를 혀 말아 낸다
  · tr / ch — 북부는 둘 다 같게, 남부는 tr 을 혀 말아 낸다
  · r / d / gi — 북부는 셋 다 /z/, 남부는 갈라 낸다
  다섯 문장은 우리 말뭉치에서 골랐다. 그래야 D(남부)가 **이미 구워져 있다** —
  남부 모델은 지금 이 자리에 없어서 새 문장은 못 만든다.

실행: python3 tools/gen_dialect_test.py
결과: dtest/<n>_<A|B|C|D>.<mp3|wav> + 설문 페이지가 읽을 dtest/list.json
"""
import json
import pathlib
import subprocess
import sys

R = pathlib.Path(__file__).resolve().parent.parent
OUT = R / "dtest"
KEY_FILE = pathlib.Path(
    "/private/tmp/claude-501/-Users-leesehyeon-my-game/"
    "d40c1e4c-ff96-477e-9754-8535837f6a0b/scratchpad/.gcp_tts_key")

# (문장, 그 문장이 드러내는 자리) — 설문 화면에도 이 설명을 같이 보여 준다
SENTS = [
    ("Em hai mươi tuổi. Bây giờ chín giờ rưỡi sáng.",
     "giờ (r/d/gi) · rưỡi (ngã) · sáng (s) · chín (ch)"),
    ("Xin lỗi, nhà vệ sinh ở đâu? Có gần đây không?",
     "Xin / sinh (s vs x) · lỗi (ngã) · ở (hỏi)"),
    ("Đỏ, xanh và trắng. Màu đỏ đẹp lắm.",
     "đỏ (hỏi) · xanh (x) · trắng (tr)"),
    ("Ở trong hộp kia. Kim cũng ở đây.",
     "cũng (ngã) vs ở·hộp (hỏi) — 남부는 이 둘을 합쳐 낸다"),
    ("Có, chính phủ hỗ trợ rất tốt.",
     "chính (ch) vs trợ (tr) 한 문장에 · hỗ (ngã) vs phủ (hỏi) · rất (r)"),
]

CHIRP = "vi-VN-Chirp3-HD-Achernar"        # 여성. A·D 도 여성이라 성별을 맞춘다


def edge(text, path):
    import asyncio
    import edge_tts
    asyncio.run(edge_tts.Communicate(text, "vi-VN-HoaiMyNeural").save(str(path)))


def chirp(text, path):
    key = KEY_FILE.read_text().strip()
    body = json.dumps({
        "input": {"text": text},
        "voice": {"languageCode": "vi-VN", "name": CHIRP},
        "audioConfig": {"audioEncoding": "MP3"},
    })
    r = subprocess.run(
        ["curl", "-s", "-m", "60", "-X", "POST", "-H", "Content-Type: application/json",
         "-d", body,
         f"https://texttospeech.googleapis.com/v1/text:synthesize?key={key}"],
        capture_output=True, text=True)
    d = json.loads(r.stdout or "{}")
    if "audioContent" not in d:
        raise RuntimeError(str(d.get("error", d))[:200])
    import base64
    path.write_bytes(base64.b64decode(d["audioContent"]))


_TTS = None


def supertonic(text, path):
    global _TTS
    import numpy as np
    import soundfile as sf
    from supertonic import TTS
    if _TTS is None:
        _TTS = TTS()
    sty = _TTS.get_voice_style(voice_name="F1")
    audio, _dur = _TTS.synthesize(text, voice_style=sty, lang="vi")
    sf.write(str(path), np.asarray(audio).squeeze(), 44100)


def ours_south(text, path):
    """우리 남부 소리는 이미 구워져 있다 — 말뭉치에 있는 문장만 된다."""
    idx = json.loads((R / "data" / "audio_index.json").read_text(encoding="utf-8"))
    h = idx.get(text)
    if not h:
        raise RuntimeError("말뭉치에 없는 문장이라 남부 소리가 없다")
    src = R / "audio" / "sf" / "n" / f"{h}.mp3"
    if not src.exists():
        raise RuntimeError(f"남부 파일 없음: {src.name}")
    path.write_bytes(src.read_bytes())


JOBS = [("A", "Edge (지금 앱)", "mp3", edge),
        ("B", "Supertonic 3", "wav", supertonic),
        ("C", "Chirp 3 HD", "mp3", chirp),
        ("D", "우리 남부 목소리", "mp3", ours_south)]


def main():
    OUT.mkdir(exist_ok=True)
    listing = []
    for i, (text, why) in enumerate(SENTS, 1):
        files = {}
        for tag, name, ext, fn in JOBS:
            p = OUT / f"{i}_{tag}.{ext}"
            if p.exists() and p.stat().st_size > 500:
                files[tag] = p.name
                continue
            try:
                fn(text, p)
                files[tag] = p.name
                print(f"  {i}_{tag} {name} 만듦 ({p.stat().st_size//1024}KB)", flush=True)
            except Exception as e:
                p.unlink(missing_ok=True)
                print(f"  ! {i}_{tag} {name} 실패: {e}", file=sys.stderr)
        listing.append({"n": i, "text": text, "why": why, "files": files})
    (OUT / "list.json").write_text(json.dumps(listing, ensure_ascii=False, indent=1))
    got = sum(len(x["files"]) for x in listing)
    print(f"끝 — 문장 {len(SENTS)}개 × 목소리 4 = {len(SENTS)*4}장 중 {got}장")


if __name__ == "__main__":
    main()
