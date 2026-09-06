#!/usr/bin/env python3
"""1강 = 낱말 정확히 10개로 맞춘다 (사용자 지시).

원칙
 - 낱말을 버리지 않는다. 넘치는 강은 '②' 강으로 쪼개고, 주제가 맞는 것끼리 묶는다.
 - 모자란 자리는 EPS 표준교재 낱말(data/_ko_words.json)에서만 채운다. 지어내지 않는다.
 - 예외 2개(cô giáo·trung tâm)만 뺀다 — 이유는 DROP에 적어 둔다.
결과: 96강 993낱말 → 100강 1,000낱말, 모든 강이 정확히 10개.
다시 돌려도 같은 결과가 나온다(이미 10개면 아무것도 안 한다).
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tone import word_tones

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/data/days.json"

# ── 빼는 낱말: 그 강의 주제에서 벗어나고, 같은 뜻을 다른 강에서 이미 배운다 ──
DROP = {
    "cô giáo": "1강은 호칭·인사만 다룬다. 직업 이름은 101강(무슨 일 하세요)에서 배운다",
    "trung tâm": "일터 낱말은 công ty·nhà máy·văn phòng으로 충분하다",
}

# ── 새 낱말 9개: 전부 data/_ko_words.json(EPS 표준교재 어휘)에 있는 것 ──
NEW = {
    "bản đồ":         ("지도", "반 도", "🗺️"),
    "đèn giao thông": ("신호등", "댄 자오 통", "🚦"),
    "con hẻm":        ("골목", "꼰 햄", "🏘️"),
    "màu sắc":        ("색깔", "마우 삭", "🎨"),
    "hoa văn":        ("무늬", "호아 반", "🌸"),
    "kẻ sọc":         ("줄무늬", "깨 쏙", "🦓"),
    "trong suốt":     ("투명하다", "쫑 쑤옫", "🫧"),
    "hình tròn":      ("동그라미·원", "힌 쫀", "⭕"),
    "găng tay":       ("장갑", "강 따이", "🧤"),
}

# ── 새로 만드는 강: (원본 day, 그 강에서 떼어 올 낱말, 새 강 정보) ──
# take = 그 day에서 가져올 vi 목록 / add = NEW에서 붙일 vi 목록
PLAN = [
    dict(after=8, day=8.5, theme="세는 말과 물건",
         intro="앞 강에서 배운 cái·con·quyển·đôi를 진짜 물건에 붙여 봅니다. 베트남어는 물건마다 세는 말이 정해져 있어서, 낱말과 세는 말을 짝으로 외우는 편이 빠릅니다.",
         take=[(8, ["cái bàn", "cái ghế", "quyển sách", "con mèo", "con chó", "động vật"]),
               (77, ["đôi đũa", "cái thìa", "tăm"])],
         add=["găng tay"]),
    dict(after=42, day=42.5, theme="길 안내하기",
         intro="타는 법을 알았으니 이제 길을 말할 차례입니다. 그랩 기사에게, 반장에게, 지게차 옆 사람에게 매일 쓰는 말들입니다.",
         take=[(42, ["đi thẳng", "rẽ trái", "rẽ phải", "chậm lại", "dừng lại", "nhanh lên", "xe taxi"])],
         add=["bản đồ", "đèn giao thông", "con hẻm"]),
    dict(after=43, day=43.5, theme="색과 무늬",
         intro="기본 색 위에 섞은 색과 무늬를 얹습니다. 섬유·봉제 일터에서는 '무슨 색 몇 번, 무슨 무늬'가 하루 종일 오갑니다.",
         take=[(43, ["xanh da trời", "xanh nước biển", "xanh lá cây", "da cam", "xám"])],
         add=["màu sắc", "hoa văn", "kẻ sọc", "trong suốt", "hình tròn"]),
    dict(after=77, day=77.5, theme="다른 음식과 음료",
         intro="쌀국수 말고도 시켜 먹을 것이 많습니다. 식당에서 이 열 낱말이면 대부분 해결됩니다.",
         take=[(77, ["cơm rang", "bún chả", "nem rán", "bánh mì", "mỳ xào"]),
               (76, ["sữa chua", "sữa tươi", "rượu", "nước hoa quả", "kem"])],
         add=[]),
]
MOVE = [(106, "tươi", 104)]          # 신선하다 → 과일 강으로 (11개·9개가 동시에 풀린다)


def main():
    d = json.load(open(P, encoding="utf-8"))
    days = d["days"]
    by = {x["day"]: x for x in days}

    def pull(day, vis):
        src = by[day]["words"]
        got = [w for w in src if w["vi"] in vis]
        miss = set(vis) - {w["vi"] for w in got}
        if miss:
            raise SystemExit(f"{day}강에 없는 낱말: {miss}")
        by[day]["words"] = [w for w in src if w["vi"] not in vis]
        return sorted(got, key=lambda w: vis.index(w["vi"]))

    for day, vi, to in MOVE:
        by[to]["words"] += pull(day, [vi])

    for vi, why in DROP.items():
        for x in days:
            n = len(x["words"])
            x["words"] = [w for w in x["words"] if w["vi"] != vi]
            if len(x["words"]) < n:
                print(f"  뺌 {vi} ({x['day']}강) — {why}")

    made = []
    for p in PLAN:
        ws = []
        for day, vis in p["take"]:
            ws += pull(day, vis)
        for vi in p["add"]:
            ko, kr, em = NEW[vi]
            ws.append({"vi": vi, "ko": ko, "kr_read": kr,
                       "tones": word_tones(vi), "emoji": em, "vkind": "thing"})
        made.append(dict(day=p["day"], theme=p["theme"], intro=p["intro"],
                         words=ws, n=len(ws)))

    # 새 강을 원래 강 바로 뒤에 끼워 넣는다
    out = []
    for x in days:
        out.append(x)
        for p, m in zip(PLAN, made):
            if x["day"] == p["after"]:
                out.append(m)
    d["days"] = out

    bad = [(x["day"], len(x["words"])) for x in out if len(x["words"]) != 10]
    tot = sum(len(x["words"]) for x in out)
    print(f"\n강 {len(out)}개 · 낱말 {tot}개 · 10개 아닌 강 {bad}")
    if bad:
        raise SystemExit("아직 안 맞음 — 저장하지 않았습니다")

    # 대화도 **정확히 두 줄**이다 (2026-08-29, 대표님 지시: 10낱말 + 2문장).
    # 네 강(8.5·42.5·43.5·77.5)이 넉 줄·닷 줄이었다. 잘라도 사라지는 말이 없는 것을
    # 미리 확인했다 — 셋째 줄부터 쓰인 낱말은 그 강의 10낱말이나 앞서 배운 말 안에 다 있었다.
    # 자를 때는 앞 두 줄을 남긴다: A가 묻고 B가 답하는 한 번 주고받기가 그대로 남는다.
    trim = [(x["day"], len(x["dialog"]["lines"])) for x in out
            if (x.get("dialog") or {}).get("lines") and len(x["dialog"]["lines"]) > 2]
    for x in out:
        dl = x.get("dialog") or {}
        if dl.get("lines") and len(dl["lines"]) > 2:
            dl["lines"] = dl["lines"][:2]
    if trim:
        print("대화를 두 줄로 줄인 강:", trim)
    json.dump(d, open(P, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("저장 완료:", P)


if __name__ == "__main__":
    main()
