#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""동아리·계정 관리 — **보고 나서 지운다**

왜 (대표님 지시, 2026-08-30): 로그인이 붙기 전 폰과 노트북에서 아이디를 따로 쓰셨다.
그 자취(옛 동아리·옛 계정)를 정리하려면 **하나씩 골라 볼 수 있어야** 한다.
워커의 wipe 는 전부 지워서 못 쓴다.

쓰기
  python3 tools/club_admin.py 목록                    — 동아리 목록
  python3 tools/club_admin.py 보기 <동아리id>          — 그 동아리에 누가 있나
  python3 tools/club_admin.py 아이디                  — 별명·아이디 목록
  python3 tools/club_admin.py 동아리지우기 <id>        — 동아리 하나만 (되돌릴 수 없다)
  python3 tools/club_admin.py 계정지우기 <아이디>      — 계정 하나만 (되돌릴 수 없다)

열쇠는 환경변수 PUSH_KEY 에서 읽는다. 없으면 물어본다.
**지우기는 두 번 묻는다** — 되돌릴 수 없기 때문이다.
"""
import json, os, subprocess, sys, getpass

URL = "https://viet-club.chaochao-app.workers.dev"
ORIGIN = "https://tpgus5119-coder.github.io"


def call(**kw):
    body = json.dumps(kw)
    p = subprocess.run(["curl", "-sS", "-X", "POST", URL, "-H", "Content-Type: application/json",
                        "-H", f"Origin: {ORIGIN}", "--data-binary", "@-"],
                       input=body, capture_output=True, text=True, timeout=60)
    try: return json.loads(p.stdout)
    except Exception: return {"error": p.stdout[:200]}


def key():
    k = os.environ.get("PUSH_KEY")
    return k or getpass.getpass("관리자 열쇠(PUSH_KEY): ")


def main():
    a = sys.argv[1:] or ["목록"]
    cmd = a[0]
    if cmd == "목록":
        j = call(act="clubs")
        for c in j.get("clubs", []):
            print(f"  {c['name']:<22}{c['n']:>3}명   id={c['id']}")
        return
    if cmd == "보기":
        j = call(act="look", id=a[1], key=key())
        if j.get("error"): print("  ✗", j["error"]); return
        print(f"  {j['name']}  (방장 {j['owner']})")
        print(f"  구성원 {len(j['members'])}: {', '.join(j['members'])}")
        if j.get("wait"): print(f"  대기 {len(j['wait'])}: {', '.join(j['wait'])}")
        for u in j.get("last", []):
            print(f"     {u['nick']:<12}기기표 {u['uid']:<10}이번 주 {u['days']}일")
        return
    if cmd == "아이디":
        j = call(act="accts", key=key())
        if j.get("error"): print("  ✗", j["error"]); return
        for n in j.get("nicks", []): print(f"  {n['nick']:<14}기기표 {n['uid']}")
        return
    if cmd in ("동아리지우기", "계정지우기"):
        what = a[1]
        k = key()
        if cmd == "동아리지우기":
            j = call(act="look", id=what, key=k)
            if j.get("error"): print("  ✗", j["error"]); return
            print(f"  지울 동아리: {j['name']} · 구성원 {len(j['members'])}명 — {', '.join(j['members'])}")
        else:
            print(f"  지울 아이디: {what}")
        print("  **되돌릴 수 없습니다.**")
        if input("  정말 지우려면 '지웁니다' 라고 적으세요: ").strip() != "지웁니다":
            print("  그만둡니다."); return
        j = call(act=("delclub" if cmd == "동아리지우기" else "delacct"), id=what, key=k)
        print("  →", json.dumps(j, ensure_ascii=False))
        return
    print(__doc__)


if __name__ == "__main__":
    main()
