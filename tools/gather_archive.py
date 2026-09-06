#!/usr/bin/env python3
"""공식 시험 자료를 **되풀이 가능하게** 받아 모은다 (~/Documents/시험기출자료고).

왜 도구로 만드나: 지난번엔 손으로 받아서 무엇이 빠졌는지 알 수 없었다.
  실제로 듣기 음원 17개가 빠져 있었는데 아무도 몰랐다. 이 도구는 매번
  **게시판 전체를 훑고 없는 것만** 받으므로, 다음 회차가 올라와도 그냥 다시 돌리면 된다.

받는 곳:
  topik  — 국립국제교육원 학습 자료실 (기출문항·정답표·듣기음원·평가틀·발문 안내)
           https://www.topik.go.kr/TWSTDY/TWSTDY0100.do  (게시판 BBSMSTR00078)
           * 이 사이트는 timezone 쿠키가 없으면 안내 페이지만 준다.
  eps    — 한국산업인력공단 EPS-TOPIK 공개문항

저작권 선: 받은 파일은 **형식·통계 조사용**이다. 앱 저장소(깃허브 공개)에 넣지 않고,
  문항을 베끼지 않는다. 우리가 가져오는 것은 발문 문구·문항 수·배점·지문 길이·
  어휘 등급 분포 같은 규격뿐이다.

실행: python3 tools/gather_archive.py [--dry]
"""
import html
import json
import pathlib
import re
import subprocess
import sys
import urllib.parse

ARCHIVE = pathlib.Path.home() / "Documents" / "시험기출자료고"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0 Safari/537.36")
BASE = "https://www.topik.go.kr"
BBS = "BBSMSTR00078"


def get(url, cookie="timezone=Asia/Seoul", binary=False, out=None):
    cmd = ["curl", "-sL", "-m", "600", "-A", UA, "-H", f"Cookie: {cookie}",
           "-e", BASE + "/", url]
    if out:
        cmd += ["-o", str(out), "-w", "%{http_code} %{size_download}"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        return r.stdout.strip()
    r = subprocess.run(cmd, capture_output=True)
    return r.stdout if binary else r.stdout.decode("utf-8", "ignore")


def board_posts():
    """목록 전 쪽을 훑어 (글번호, 제목)을 모은다."""
    posts, page = [], 1
    while True:
        h = get(f"{BASE}/TWSTDY/TWSTDY0100.do?pageIndex={page}")
        found = re.findall(r"fnContent\('%s','(\d+)'\)(.*?)</tr>" % BBS, h, re.S)
        if not found:
            break
        for nid, tail in found:
            t = html.unescape(re.sub(r"<[^>]+>", " ", tail))
            posts.append((nid, " ".join(t.split())[:60]))
        page += 1
        if page > 20:                      # 안전장치
            break
    # 쪽마다 같은 글이 겹쳐 나올 수 있다
    seen, out = set(), []
    for nid, t in posts:
        if nid not in seen:
            seen.add(nid)
            out.append((nid, t))
    return out


def post_files(nid):
    h = get(f"{BASE}/TWSTDY/TWSTDY0101.do?bbsId={BBS}&nttId={nid}")
    out = []
    for m in re.finditer(r'href="([^"]*?/comm/download\.do\?[^"]+)"', h):
        u = html.unescape(m.group(1))
        q = urllib.parse.parse_qs(urllib.parse.urlparse(u).query)
        name = urllib.parse.unquote_plus(
            (q.get("orgFileName") or q.get("fileName") or ["파일"])[0])
        out.append((name, u if u.startswith("http") else BASE + u))
    return out


def safe(s):
    return re.sub(r"[/\\:]+", "_", s).strip()


def main():
    dry = "--dry" in sys.argv
    d = ARCHIVE / "TOPIK-기출-공식"
    d.mkdir(parents=True, exist_ok=True)
    have = {p.name for p in d.iterdir() if p.is_file()}
    # 예전에 받은 것은 "글제목__파일이름" 꼴이라 파일이름만 떼어 견준다
    have_tail = {n.split("__", 1)[-1] for n in have}

    posts = board_posts()
    print(f"게시글 {len(posts)}건")
    got = miss = skip = 0
    for nid, title in posts:
        for name, url in post_files(nid):
            if name in have_tail or name in have:
                skip += 1
                continue
            miss += 1
            out = d / safe(f"{title.split('첨부파일')[0].strip()}__{name}")
            if dry:
                print(f"  없음: {name}")
                continue
            r = get(url, out=out)
            code, size = (r.split() + ["?", "0"])[:2]
            ok = code == "200" and int(size) > 1000
            print(f"  {'받음' if ok else '실패'} {name} ({size}바이트)")
            if ok:
                got += 1
            else:
                out.unlink(missing_ok=True)
    print(f"끝 — 이미 있음 {skip} · 없던 것 {miss} · 새로 받음 {got}")


if __name__ == "__main__":
    main()
