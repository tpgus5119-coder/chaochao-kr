#!/usr/bin/env python3
"""실제 TOPIK 듣기의 **말하는 속도**를 재서 우리 소리와 견준다.

왜: 우리 듣기 문항은 edge-tts 로 만든다. 속도는 지금까지 감으로 정했다.
    실제 시험보다 빠르면 연습이 시험보다 어려워지고, 느리면 시험에서 못 따라간다.
    이제 공식 음원 17회차를 받았으니 **재서 맞출 수 있다.**

어떻게: 음원에는 답을 고르는 **긴 침묵**이 섞여 있다. 그대로 나누면 속도가
    실제보다 훨씬 느리게 나온다. 그래서 ffmpeg 의 silencedetect 로 침묵을 걷어내고
    **말한 시간만** 남긴 뒤, 대본의 한글 글자 수로 나눈다.

    TOPIK I 은 문항을 **두 번** 들려준다. 대본 글자를 두 배로 세야 맞다.
    (이걸 안 하면 속도가 절반으로 나온다.)

쓰기: python3 tools/listen_rate.py <음원폴더> <대본txt> [--rep 2]
"""
import re
import subprocess
import sys
from pathlib import Path

SIL_DB = "-35dB"          # 이보다 조용하면 침묵으로 본다
SIL_MIN = "0.35"          # 0.35초 넘게 이어져야 침묵으로 친다(글자 사이 짧은 끊김은 말이다)


def speech_seconds(path):
    """전체 길이에서 침묵을 뺀 '말한 시간'(초)."""
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
         "-af", f"silencedetect=noise={SIL_DB}:d={SIL_MIN}", "-f", "null", "-"],
        capture_output=True, text=True)
    log = r.stderr
    total = 0.0
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", log)
    if m:
        total = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    sil = sum(float(x) for x in re.findall(r"silence_duration: ([\d.]+)", log))
    return max(0.0, total - sil), total


def script_chars(txt):
    """대본에서 **실제로 소리 나는 말**만 세다.

    문제지 텍스트에는 보기(①②③④)·쪽머리·발문이 섞여 있다. TOPIK I 듣기에서
    보기는 눈으로 읽는 것이지 들려주지 않는다. 세면 안 된다.
    """
    n = 0
    for ln in txt.splitlines():
        s = ln.strip()
        if not s or s.startswith(("①", "②", "③", "④", "※", ")")):
            continue
        if re.match(r"^\d+\.\s*\(\d+점\)", s) or "한국어능력시험" in s:
            continue
        s = re.sub(r"^(남자|여자|가|나)\s*[:：]\s*", "", s)   # 화자 표시는 안 읽는다
        s = re.sub(r"[<>\-_()]|보\s*기", "", s)
        n += len(re.findall(r"[가-힣]", s))
    return n


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    folder, script = Path(sys.argv[1]), Path(sys.argv[2])
    rep = 2
    if "--rep" in sys.argv:
        rep = int(sys.argv[sys.argv.index("--rep") + 1])

    files = sorted(folder.glob("*.mp3"))
    if not files:
        sys.exit(f"mp3 가 없다: {folder}")
    spoke = full = 0.0
    for f in files:
        s, t = speech_seconds(f)
        spoke += s
        full += t
    chars = script_chars(script.read_text(encoding="utf-8", errors="ignore")) * rep

    print(f"음원 {len(files)}개 · 전체 {full/60:.1f}분 · 말한 시간 {spoke/60:.1f}분 "
          f"(침묵 {100*(full-spoke)/full:.0f}%)")
    print(f"대본 한글 {chars:,}자 ({rep}번 들려주는 것 반영)")
    print(f"→ **말하는 속도 {chars/spoke:.2f} 글자/초**  ({chars/spoke*60:.0f} 글자/분)")


if __name__ == "__main__":
    main()
