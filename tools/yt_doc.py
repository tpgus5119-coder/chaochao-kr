#!/usr/bin/env python3
"""유튜브 강의를 글로 받아 적는다 — **조사용이다. 제품에 싣지 않는다.**

  python3 tools/yt_doc.py @blogtopik @topik3.152 https://youtu.be/xxxx
  python3 tools/yt_doc.py --only 시험 @sidaeedu        # 걸러내는 잣대 바꾸기
  python3 tools/yt_doc.py --list @blogtopik            # 받지 말고 목록만 보기

무엇을 받나: 자동자막을 그대로 받는다(소리를 내려받지 않는다 — 빠르고 가볍다).
자막이 없는 영상은 목록에 남겨만 두고 건너뛴다.

왜 자동자막인가: 이 채널들은 강의라 말이 또렷하고 자동자막이 꽤 맞는다.
whisper 로 받아 적으면 10분에 2~3분씩 걸리는데, 자막은 2초다.

**권리에 대해** — 남의 강의다. 받아 적은 글은 무엇이 이미 있는지 **살펴보는 데만**
쓴다. 문장을 우리 문제나 교재로 옮기면 침해다. 그래서 만든 파일마다 어디서 온
것인지(_출처.tsv)를 함께 적는다. 출처를 못 대는 글은 쓰지 않는다.
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

OUT = pathlib.Path.home() / "yt-조사"
YTDLP = ["yt-dlp", "--extractor-args", "youtube:player_client=android",
         "--no-warnings", "--ignore-errors"]

# 베트남 관련 · 국가공인 시험 관련 — 둘 다 걸리는 것만 받는다(회화 강의는 뺀다)
# 'Viet\b' 로 썼다가 **Vietnamese 를 통째로 놓쳤다** — 뒤에 n 이 붙어 낱말 경계가 아니다.
# 하필 그게 가장 값진 묶음(한국어-베트남어 대역 어휘 50일)이었다. 경계를 붙이지 않는다.
VN = re.compile(r"베트남|Việt|Viet|tiếng|Tiếng|비엣|VN\b", re.I)
EXAM = re.compile(r"TOPIK|토픽|EPS|KIIP|사회통합|귀화|국적|한국어능력시험|기출|모의고사|"
                  r"실전|급수|\d+\s*회|năng lực|đề thi", re.I)
NOTES = {"베트남": VN, "시험": EXAM}


def run(args):
    return subprocess.run(args, capture_output=True, text=True).stdout


def entries(url):
    """채널이든 영상 하나든 {id,title,duration,url} 목록으로 만든다."""
    if "/watch" in url or "youtu.be/" in url:
        src = url
    elif url.startswith("@"):
        src = f"https://www.youtube.com/{url}/videos"
    else:
        src = url.rstrip("/") + ("" if url.endswith(("videos", "playlists")) else "/videos")
    out = run(YTDLP + ["--flat-playlist", "-J", src])
    if not out.strip():
        return []
    d = json.loads(out)
    items = d.get("entries") or [d]
    return [{"id": e.get("id"), "title": e.get("title") or "",
             "dur": e.get("duration") or 0,
             "ch": e.get("channel") or d.get("channel") or d.get("title") or ""}
            for e in items if e and e.get("id")]


def vtt_text(p):
    """자동자막(vtt)에서 말만 뽑는다. 굴러가는 자막이라 같은 줄이 겹쳐 온다."""
    out, last = [], ""
    for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if (not ln or "-->" in ln or ln.startswith(("WEBVTT", "Kind:", "Language:", "NOTE"))
                or ln.isdigit()):
            continue
        ln = re.sub(r"<[^>]+>", "", ln).strip()
        if ln and ln != last:
            out.append(ln)
            last = ln
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--only", nargs="*", default=["베트남", "시험"],
                    help="걸러내는 잣대 (기본: 베트남 그리고 시험 둘 다)")
    ap.add_argument("--list", action="store_true", help="받지 말고 목록만")
    ap.add_argument("--max", type=int, default=0, help="이만큼만 받기(0=제한 없음)")
    a = ap.parse_args()
    tests = [NOTES[k] for k in a.only if k in NOTES]

    OUT.mkdir(exist_ok=True)
    man = OUT / "_출처.tsv"
    seen = set()
    if man.exists():
        seen = {l.split("\t")[0] for l in man.read_text(encoding="utf-8").splitlines()[1:]}
    else:
        man.write_text("id\t채널\t제목\t길이초\t주소\t자막\n", encoding="utf-8")

    picked, got, noSub = [], 0, 0
    for u in a.urls:
        es = entries(u)
        keep = [e for e in es if all(t.search(e["title"]) for t in tests)]
        print(f"{u:<45} 전체 {len(es):>5} · 고른 것 {len(keep):>4}")
        picked += keep
    if a.list:
        for e in picked:
            print(f"  {e['dur']:>5}s  {e['title'][:90]}")
        return print(f"\n모두 {len(picked)}편")

    for i, e in enumerate(picked, 1):
        if a.max and got >= a.max:
            break
        if e["id"] in seen:
            continue
        url = f"https://www.youtube.com/watch?v={e['id']}"
        # **말한 언어 그대로** 받는다. 'ko' 를 달라고 하면 유튜브가 기계로 옮겨 준다 —
        # 베트남어 강의를 한국어로 받았더니 TOPIK 이 '토익'이 되고 사람 이름이 뒤섞였다.
        # yt-dlp 는 원본 트랙을 '<말>-orig' 로 내놓는다.
        run(YTDLP + ["--skip-download", "--write-auto-sub",
                     "--sub-lang", "vi-orig,ko-orig,en-orig,vi,ko",
                     "--sub-format", "vtt", "-o", str(OUT / "%(id)s.%(ext)s"), url])
        vtt = next(iter(sorted(OUT.glob(f"{e['id']}.*.vtt"),
                              key=lambda p: (".orig." not in p.name.replace("-orig.", ".orig."),
                                             -p.stat().st_size))), None)
        for extra in OUT.glob(f"{e['id']}.*.vtt"):
            if vtt and extra != vtt:
                extra.unlink()
        if vtt:
            (OUT / f"{e['id']}.txt").write_text(
                f"# {e['title']}\n# {e['ch']} · {url}\n# 조사용 — 옮겨 쓰지 말 것\n\n"
                + vtt_text(vtt), encoding="utf-8")
            vtt.unlink()
            got += 1
            mark = "있음"
        else:
            noSub += 1
            mark = "없음"
        with man.open("a", encoding="utf-8") as f:
            f.write(f"{e['id']}\t{e['ch']}\t{e['title']}\t{e['dur']}\t{url}\t{mark}\n")
        print(f"  [{i}/{len(picked)}] {mark}  {e['title'][:70]}")

    print(f"\n받아 적음 {got}편 · 자막 없어 건넌 것 {noSub}편 → {OUT}")


if __name__ == "__main__":
    sys.exit(main())
