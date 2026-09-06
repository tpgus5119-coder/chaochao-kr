#!/usr/bin/env python3
"""훈련기관 수업 5~10강 나란히 — 별도 세트가 아니라 **기존 챕터 보강**으로 녹인다 (사용자 지시).
수업자료에서 가져온 것은 주제·단어 목록(사실)뿐, 표현은 전부 자체 작성.
  · 새 세트 둘만 남긴다: 106 장보기(시장 재료) · 104 과일 — 기존에 없던 진짜 구멍
  · 나머지는 patch 로 흩어 보강: 길 지시→42 타고 다니기, 밥집 음식→77, 색깔→43,
    음료·디저트→76 카페, 단위사 사물→8 개수 세기, cô giáo→1, trung tâm→101
  · 버린 것(중복·불필요): xích lô(관광어), phở bò(phở+bò 로 조합 가능), cái bát(77에 bát),
    súp(빈도 낮음), 이름·나이 대화(2·9와 중복)"""
import json, pathlib, sys
sys.path.insert(0, 'tools')
from tone import word_tones
def W(vi, ko, kr, h=None, s=None):
    d = {"vi": vi, "ko": ko, "kr_read": kr, "tones": word_tones(vi)}
    if h: d["hanja"] = h
    if s: d["south"] = s
    return d
def L(who, vi, ko, kr, g): return {"who": who, "vi": vi, "ko": ko, "kr_read": kr,
    "gloss": [{"w": a, "m": b} for a, b in g], "tones": word_tones(vi)}
def X(vi, ko, kr): return {"vi": vi, "ko": ko, "kr_read": kr, "tones": word_tones(vi)}
def D(day, theme, intro, words, title, lines, extra):
    return {"day": day, "theme": theme, "intro": intro, "words": words,
            "dialog": {"title": title, "lines": lines, "extra": extra},
            "mission": {"goal": "", "how": "", "a": "", "b": ""}}
DAYS = []

DAYS.append(D(106, "장보기",
 "시장의 재료들 — 값을 묻고, 신선한지 본다.",
 [W("lợn", "돼지(고기)", "런", None, "heo"), W("trứng", "달걀", "쯩"),
  W("đậu phụ", "두부", "더우 푸", "豆腐 (두부)"), W("rau muống", "모닝글로리(공심채)", "자우 무옹"),
  W("tỏi", "마늘", "또이"), W("khoai tây", "감자", "코아이 떠이"),
  W("dưa chuột", "오이", "즈어 쭈옷", None, "dưa leo"), W("cà rốt", "당근", "까 좃"),
  W("cà chua", "토마토", "까 쭈어"), W("ớt tây", "피망·파프리카", "엇 떠이"),
  W("tươi", "신선하다", "뜨어이")],
 "시장에서",
 [L("A", "Cà chua bao nhiêu tiền một cân ạ?", "토마토 1kg에 얼마예요?", "까 쭈어 바오 니에우 띠엔 못 껀 아",
    [("cà chua", "토마토"), ("một cân", "1kg")]),
  L("B", "Bốn mươi nghìn một cân ạ.", "1kg에 4만 동이에요.", "본 므어이 응인 못 껀 아",
    [("bốn mươi nghìn", "4만"), ("một cân", "1kg")])],
 [X("Cho em trứng với đậu phụ.", "달걀이랑 두부 주세요", "쪼 앰 쯩 버이 더우 푸"),
  X("Lợn với trứng rất tươi.", "돼지고기랑 달걀이 아주 신선해요", "런 버이 쯩 젓 뜨어이"),
  X("Rau muống với tỏi rẻ lắm.", "모닝글로리랑 마늘이 아주 싸요", "자우 무옹 버이 또이 재 람"),
  X("Cho em khoai tây, cà rốt với dưa chuột.", "감자, 당근, 오이 주세요", "쪼 앰 코아이 떠이 까 좃 버이 즈어 쭈옷"),
  X("Ớt tây với cà chua rất ngon.", "피망이랑 토마토가 아주 맛있어요", "엇 떠이 버이 까 쭈어 젓 응온")]))

DAYS.append(D(104, "과일",
 "베트남 과일 아홉 가지 — 저울(cân)로 달아서 산다.",
 [W("chuối", "바나나", "쭈오이"), W("xoài", "망고", "쏘아이"),
  W("dứa", "파인애플", "즈어", None, "thơm"), W("dừa", "코코넛", "즈어"),
  W("táo", "사과", "따오"), W("dưa hấu", "수박", "즈어 허우"),
  W("dâu tây", "딸기", "저우 떠이"), W("đào", "복숭아", "다오"),
  W("măng cụt", "망고스틴", "망 꿋")],
 "과일 가게에서",
 [L("A", "Táo này bao nhiêu tiền một cân ạ?", "이 사과 1kg에 얼마예요?", "따오 나이 바오 니에우 띠엔 못 껀 아",
    [("táo", "사과"), ("một cân", "1kg")]),
  L("B", "Ba mươi nghìn ạ. Xoài với chuối cũng rẻ ạ.", "3만 동이에요. 망고랑 바나나도 싸요.", "바 므어이 응인 아 쏘아이 버이 쭈오이 꿍 재 아",
    [("xoài", "망고"), ("chuối", "바나나")])],
 [X("Dưa hấu với dứa rất ngon.", "수박이랑 파인애플이 아주 맛있어요", "즈어 허우 버이 즈어 젓 응온"),
  X("Nước dừa với chuối cũng ngon.", "코코넛 물이랑 바나나도 맛있어요", "느억 즈어 버이 쭈오이 꿍 응온"),
  X("Đào với măng cụt đắt lắm.", "복숭아랑 망고스틴은 아주 비싸요", "다오 버이 망 꿋 닷 람"),
  X("Dâu tây này rất tươi.", "이 딸기 아주 신선해요", "저우 떠이 나이 젓 뜨어이")]))

# ── 기존 챕터 보강 (assemble 이 day 를 찾아 words·extra 를 덧붙인다) ──────────
PATCH = [
 {"day": 42, "words": [                     # 타고 다니기 — 택시에서 살아남는 말
   W("đi thẳng", "직진하다", "디 탕"), W("rẽ trái", "좌회전하다", "제 짜이"),
   W("rẽ phải", "우회전하다", "제 파이"), W("chậm lại", "속도를 줄이다", "쩜 라이"),
   W("dừng lại", "멈추다·세우다", "증 라이"), W("nhanh lên", "서두르다·빨리", "냔 렌"),
   W("xe taxi", "택시", "새 딱시")],
  "extra": [
   X("Đi thẳng rồi rẽ phải nhé.", "직진하다가 우회전해 주세요", "디 탕 조이 제 파이 녜"),
   X("Em rẽ trái rồi dừng lại ạ.", "좌회전하고 세울게요", "앰 제 짜이 조이 증 라이 아"),
   X("Xe taxi chậm lại nhé.", "택시 아저씨, 속도 줄여 주세요", "새 딱시 쩜 라이 녜"),
   X("Đi nhanh lên nhé.", "빨리 가 주세요", "디 냔 렌 녜"),
   X("Dừng lại ở đây ạ.", "여기서 세워 주세요", "증 라이 어 더이 아")]},
 {"day": 77, "words": [                     # 쌀국수 주문 심화 — 딴 음식과 식탁 도구
   W("cơm rang", "볶음밥", "껌 장", None, "cơm chiên"), W("bún chả", "분짜(석쇠구이 국수)", "분 짜"),
   W("nem rán", "튀김 스프링롤", "냄 잔", None, "chả giò"), W("bánh mì", "바게트 샌드위치", "바잉 미"),
   W("mỳ xào", "볶음면", "미 싸오"), W("đôi đũa", "젓가락 한 벌", "도이 두어"),
   W("cái thìa", "숟가락", "까이 티어", None, "cái muỗng"), W("tăm", "이쑤시개", "땀")],
  "extra": [
   X("Cho anh một phở bò và một nem rán.", "소고기 쌀국수 하나랑 스프링롤 하나 주세요", "쪼 아잉 못 퍼 보 바 못 냄 잔"),
   X("Có bún chả với mỳ xào nữa ạ.", "분짜랑 볶음면도 있어요", "꼬 분 짜 버이 미 싸오 느어 아"),
   X("Cho em một cái bát với đôi đũa.", "그릇 하나랑 젓가락 한 벌 주세요", "쪼 앰 못 까이 밧 버이 도이 두어"),
   X("Cái thìa với tăm ở đây ạ.", "숟가락과 이쑤시개는 여기 있어요", "까이 티어 버이 땀 어 더이 아"),
   X("Bánh mì này rất ngon.", "이 반미 아주 맛있어요", "바잉 미 나이 젓 응온"),
   X("Em thích cơm rang.", "저는 볶음밥을 좋아해요", "앰 틱 껌 장")]},
 {"day": 43, "words": [                     # 색깔 — xanh 를 셋으로 가른다
   W("xanh da trời", "하늘색", "싸잉 자 쪄이"), W("xanh nước biển", "바다색·남색", "싸잉 느억 비엔"),
   W("xanh lá cây", "초록색", "싸잉 라 꺼이"), W("da cam", "주황색", "자 깜", None, "màu cam"),
   W("xám", "회색", "쌈")],
  "extra": [
   X("Cái áo này màu gì?", "이 옷은 무슨 색이에요?", "까이 아오 나이 마우 지"),
   X("Màu xanh da trời, không phải xanh nước biển ạ.", "하늘색이에요, 남색이 아니라요", "마우 싸잉 자 쪄이 콩 파이 싸잉 느억 비엔 아"),
   X("Màu xanh lá cây với màu da cam rất đẹp.", "초록색이랑 주황색이 아주 예뻐요", "마우 싸잉 라 꺼이 버이 마우 자 깜 젓 댑"),
   X("Cái áo này màu xám.", "이 옷은 회색이에요", "까이 아오 나이 마우 쌈")]},
 {"day": 76, "words": [                     # 카페 — 우유 갈래와 디저트
   W("sữa chua", "요거트", "스어 쭈어"), W("sữa tươi", "생우유", "스어 뜨어이"),
   W("rượu", "술", "즈어우"), W("nước hoa quả", "과일 주스", "느억 호아 꾸아"),
   W("kem", "아이스크림", "깸")],
  "extra": [
   X("Cho em một sữa chua với nước hoa quả.", "요거트 하나랑 과일 주스 주세요", "쪼 앰 못 스어 쭈어 버이 느억 호아 꾸아"),
   X("Em thích sữa tươi, không thích rượu.", "저는 생우유는 좋아하고 술은 안 좋아해요", "앰 틱 스어 뜨어이 콩 틱 즈어우"),
   X("Kem ở đây ngon lắm.", "여기 아이스크림 아주 맛있어요", "깸 어 더이 응온 람")]},
 {"day": 8, "words": [                      # 개수 세기 — 단위사 연습감 (cái·con·quyển)
   W("cái bàn", "책상·탁자", "까이 반"), W("cái ghế", "의자", "까이 게"),
   W("quyển sách", "책 한 권", "꾸이엔 사익", None, "cuốn sách"),
   W("con mèo", "고양이", "꼰 매오"), W("con chó", "개", "꼰 쪼"),
   W("động vật", "동물", "동 벗", "動物 (동물)")],
  "extra": [
   X("Ba con mèo, hai con chó ạ.", "고양이 세 마리, 개 두 마리요", "바 꼰 매오 하이 꼰 쪼 아"),
   X("Một cái bàn, hai cái ghế ạ.", "책상 하나, 의자 두 개요", "못 까이 반 하이 까이 게 아"),
   X("Tất cả ba quyển sách ạ.", "전부 책 세 권이에요", "땃 까 바 꾸이엔 사익 아"),
   X("Con mèo là động vật ạ.", "고양이는 동물이에요", "꼰 매오 라 동 벗 아")]},
 {"day": 1, "words": [W("cô giáo", "여자 선생님", "꼬 자오", "敎 (교)")],
  "extra": [X("Chào cô giáo ạ.", "선생님, 안녕하세요", "짜오 꼬 자오 아")]},
 {"day": 101, "words": [W("trung tâm", "센터·학원", "쭝 떰", "中心 (중심)")],
  "extra": [X("Em học ở trung tâm ạ.", "저는 학원에서 공부해요", "앰 혹 어 쭝 떰 아")]},
]

out = {"days": DAYS, "patch": PATCH}
pathlib.Path('data/_b8.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
print(f"b8: 세트 {len(DAYS)}(104·106) / 보강 {len(PATCH)}곳 단어 {sum(len(p['words']) for p in PATCH)}")
