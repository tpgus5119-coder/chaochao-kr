#!/usr/bin/env python3
"""days.json 에만 살아 있던 **사용자 지시 수정**을 다시 얹는다.

  python3 tools/apply_patches.py

왜 이 도구가 있나: 커리큘럼 원본은 `tools/b*.py` 인데, 급한 수정 몇 개가 원본이 아니라
`days.json` 에 바로 들어갔다. 그래서 `assemble.py` 를 다시 돌리면 **조용히 지워진다.**
실제로 이번에 8.5강이 통째로 되돌아갔다 — 대표님이 "재는 말이 100강에 한 낱말도 없다"고
지적해 바꾼 강인데(커밋 0a911e95), 조립기는 그걸 모르니 옛 '세는 말' 강을 다시 만들었다.

고치는 자리 (data/_patch_days.json 에 근거와 함께 적어 둔다):
  · 8.5강 통째 — '세는 말과 물건' → '재는 말 — 치수와 무게'
       kg·gam·mét·phân·mi-li-mét 이 100강 어디에도 없었다. 공장·납기·검수를 가르치면서.
  · 16강 đau / 20강 hẹn·hứa — 뜻이 겹쳐 헷갈리던 것을 갈라 적은 것
  · 75강 대화 — 견주는 말(hơn)이 안 배운 낱말이라 고친 것

**빌드 차례**: assemble.py --write → fix10.py → apply_patches.py → img_relink.py
                → new_dialogs.py → fill_missions.py → hanja_attach.py → gen_covers.py
"""
import json
import pathlib

R = pathlib.Path(__file__).resolve().parent.parent
P = R / "data" / "_patch_days.json"
D = R / "data" / "days.json"


def main():
    if not P.exists():
        raise SystemExit(f"고칠 목록이 없다: {P}")
    pat = json.loads(P.read_text(encoding="utf-8"))
    d = json.loads(D.read_text(encoding="utf-8"))
    by = {str(x["day"]): x for x in d["days"]}
    done = []

    for k, day in pat.get("replace_day", {}).items():
        if k in by:
            i = d["days"].index(by[k])
            d["days"][i] = day
            done.append(f"{k}강 통째로 되돌림 ({day['theme']})")

    for k, m in pat.get("word_ko", {}).items():
        for w in by.get(k, {}).get("words", []):
            if w["vi"] in m and w["ko"] != m[w["vi"]]:
                w["ko"] = m[w["vi"]]
                done.append(f"{k}강 {w['vi']} → {w['ko']}")

    for k, dlg in pat.get("dialog", {}).items():
        if k in by and by[k].get("dialog") != dlg:
            by[k]["dialog"] = dlg
            done.append(f"{k}강 대화 되돌림")

    D.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"되돌린 것 {len(done)}건")
    for x in done:
        print("  ", x)


if __name__ == "__main__":
    main()
