#!/usr/bin/env python3
"""문장은 그 강까지 배운 낱말로만 — 검사기 (사용자 지시).

읽는 법
 - 각 강의 대화문을 낱말 단위로 쪼개, '그 강까지 배운 낱말 + 기능어'에 없는 것을 찾아낸다.
 - 배운 낱말은 여러 음절짜리도 통째로 인정한다(cà phê sữa 처럼).
 - 기능어(là, không, ở …)는 문법 뼈대라 낱말 카드로 안 가르쳐도 나온다 → WHITELIST.
쓰는 법
    python3 tools/sent_check.py            # 베트남어 과정
    python3 tools/sent_check.py ko         # 한국어 과정
    python3 tools/sent_check.py --new      # 새로 만든 강만
"""
import json, os, re, sys, unicodedata
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 문법 뼈대로 쓰이는 말 + 고유명사(사람·지명) — 낱말 카드로 안 가르쳐도 대화에 나온다
WHITELIST = set("""
là không có ở của và với cho được rồi đã đang sẽ này kia đó ấy
tôi anh chị em bạn ông bà cô chú ta mình nó họ
một hai ba bốn năm sáu bảy tám chín mười
gì nào đâu ai sao mấy bao nhiêu vâng dạ ạ nhé nhỉ à ừ ok
thì mà nhưng hay hoặc nếu vì nên cũng chỉ đều vẫn còn nữa
rất lắm quá hơi thật đi đến về ra vào lên xuống qua
ai_đó cái con chiếc quyển đôi bát ly cốc
nam việt nghệ an hà nội hồ chí minh đà nẵng seoul hàn quốc
""".split())


def norm(s):
    s = unicodedata.normalize("NFC", s.lower())
    return re.sub(r"[^0-9a-zà-ỹđ\s]", " ", s)


def toks(s):
    # 숫자는 낱말 카드로 안 가르쳐도 대화에 나온다 (시각·값·개수)
    return [t for t in norm(s).split() if t and not t.isdigit()]


def check(path, key_words="words", key_dialog="dialog", lang="vi"):
    d = json.load(open(path, encoding="utf-8"))
    days = d["days"] if isinstance(d, dict) and "days" in d else d
    known, rows = set(WHITELIST), []
    for x in days:
        # 이 강의 낱말을 먼저 배운 것으로 친다(같은 강 대화에 나와야 하니까)
        for w in x.get(key_words, []):
            t = w.get(lang) or w.get("ko") or ""
            known.update(toks(t))
            known.add(" ".join(toks(t)))
        dlg = x.get(key_dialog) or {}
        bad = []
        for ln in dlg.get("lines", []):
            s = ln.get(lang) or ""
            tk = toks(s)
            i = 0
            while i < len(tk):
                for n in (4, 3, 2):                     # 긴 덩어리부터 맞춰 본다
                    if " ".join(tk[i:i + n]) in known:
                        i += n; break
                else:
                    if tk[i] not in known:
                        bad.append(tk[i])
                    i += 1
        rows.append((x.get("day"), x.get("theme"), len(dlg.get("lines", [])), bad))
    return rows


def main():
    ko = "ko" in sys.argv
    path = f"{ROOT}/data/{'ko_days' if ko else 'days'}.json"
    rows = check(path, lang="ko" if ko else "vi")
    if "--new" in sys.argv:
        rows = [r for r in rows if isinstance(r[0], float)]
    bad = [r for r in rows if r[3]]
    tot = sum(len(r[3]) for r in rows)
    print(f"{os.path.basename(path)} — 강 {len(rows)}개 · 안 배운 낱말 {tot}개 ({len(bad)}개 강)")
    for day, theme, n, b in bad:
        print(f"  {str(day):>6}강 «{theme}» ({n}줄): {', '.join(sorted(set(b)))}")
    if bad:
        c = Counter(w for r in rows for w in r[3])
        print("\n자주 나오는 미학습 낱말 20개:", ", ".join(f"{w}({n})" for w, n in c.most_common(20)))


if __name__ == "__main__":
    main()
