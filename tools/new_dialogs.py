#!/usr/bin/env python3
"""새로 만든 4개 강에 대화문을 붙이고, 강 번호(n)를 다시 매긴다.
대화문은 그 강까지 배운 낱말로만 짰다 — tools/sent_check.py 로 검사한다.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tone import word_tones

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/data/days.json"

D = {
 8.5: ("창고에서 세어 보기", [
   ("A", "Ở đây có mấy cái bàn?", "여기 책상이 몇 개 있어요?", "어 더이 꼬 머이 까이 반",
        [("mấy","몇"),("cái bàn","책상")]),
   ("B", "Có tám cái bàn và chín cái ghế.", "책상 여덟 개하고 의자 아홉 개 있어요.", "꼬 땀 까이 반 바 찐 까이 게",
        [("tám","여덟"),("cái ghế","의자")]),
   ("A", "Còn đôi đũa và cái thìa?", "젓가락하고 숟가락은요?", "꼰 도이 두어 바 까이 티어",
        [("đôi đũa","젓가락 한 벌"),("cái thìa","숟가락")]),
   ("B", "Còn hai đôi đũa. Thiếu găng tay.", "젓가락 두 벌 남았어요. 장갑이 부족해요.", "꼰 하이 도이 두어. 티에우 강 따이",
        [("còn","남다"),("thiếu","부족하다"),("găng tay","장갑")]),
 ]),
 42.5: ("그랩 기사에게 길 알려 주기", [
   ("A", "Anh đi thẳng nhé.", "직진해 주세요.", "아인 디 탕 녜",
        [("đi thẳng","직진하다")]),
   ("B", "Đến đèn giao thông thì rẽ phải ạ?", "신호등에서 우회전할까요?", "댄 댄 자오 통 티 재 파이 아",
        [("đèn giao thông","신호등"),("rẽ phải","우회전하다")]),
   ("A", "Vâng. Chậm lại, vào con hẻm này.", "네. 속도 줄이고 이 골목으로 들어가요.", "벙. 쩜 라이, 바오 꼰 햄 나이",
        [("chậm lại","속도를 줄이다"),("con hẻm","골목")]),
   ("B", "Dừng lại đây ạ?", "여기 세울까요?", "증 라이 더이 아",
        [("dừng lại","멈추다")]),
   ("A", "Vâng, dừng lại. Cảm ơn anh.", "네, 세워 주세요. 고맙습니다.", "벙, 증 라이. 깜 언 아인",
        [("cảm ơn","고맙습니다")]),
 ]),
 43.5: ("무늬 고르기", [
   ("A", "Vải này có hoa văn gì?", "이 원단은 무슨 무늬예요?", "바이 나이 꼬 호아 반 지",
        [("hoa văn","무늬")]),
   ("B", "Kẻ sọc màu xanh da trời.", "하늘색 줄무늬요.", "깨 쏙 마우 싸인 자 쩌이",
        [("kẻ sọc","줄무늬"),("xanh da trời","하늘색")]),
   ("A", "Có màu xám không?", "회색도 있어요?", "꼬 마우 쌈 콩",
        [("màu sắc","색깔"),("xám","회색")]),
   ("B", "Có. Và có hình tròn màu da cam.", "있어요. 그리고 주황색 동그라미도 있어요.", "꼬. 바 꼬 힌 쫀 마우 자 깜",
        [("hình tròn","동그라미"),("da cam","주황색")]),
 ]),
 77.5: ("점심 시키기", [
   ("A", "Chị ăn gì?", "뭐 드실래요?", "찌 안 지",
        [("ăn","먹다")]),
   ("B", "Cho tôi một bát bún chả.", "분짜 한 그릇 주세요.", "쩌 또이 못 밧 분 짜",
        [("bát","그릇"),("bún chả","분짜")]),
   ("A", "Tôi ăn cơm rang. Uống nước hoa quả nhé.", "저는 볶음밥 먹을게요. 과일 주스 마셔요.", "또이 안 껌 랑. 우옹 느억 호아 꽈 녜",
        [("cơm rang","볶음밥"),("nước hoa quả","과일 주스")]),
   ("B", "Có kem không ạ?", "아이스크림 있어요?", "꼬 깸 콩 아",
        [("kem","아이스크림")]),
   ("A", "Có. Kem và sữa chua.", "있어요. 아이스크림하고 요거트요.", "꼬. 깸 바 스어 쭈어",
        [("sữa chua","요거트")]),
 ]),
}


def main():
    d = json.load(open(P, encoding="utf-8"))
    for x in d["days"]:
        if x["day"] in D:
            title, lines = D[x["day"]]
            x["dialog"] = {"title": title, "lines": [
                {"who": w, "vi": vi, "ko": ko, "kr_read": kr,
                 "gloss": [{"w": a, "m": b} for a, b in gl],
                 "tones": word_tones(vi)} for w, vi, ko, kr, gl in lines]}
            x["mission"] = {"goal": "", "how": "", "a": "", "b": ""}
    # n 다시 매기기 — 일상/직무 각각 1번부터
    c = {}
    for x in d["days"]:
        if isinstance(x["day"], str):
            continue
        t = x.get("track", "daily")
        c[t] = c.get(t, 0) + 1
        x["n"] = c[t]
    json.dump(d, open(P, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("대화문 4개 붙임 · 번호 다시 매김:", c)


if __name__ == "__main__":
    main()
