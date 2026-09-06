#!/usr/bin/env python3
"""일상 확장 2세트 — 커리큘럼 벤치마킹(한/영/중/베 교재 7종) 반영분.
101 직업·일터: 조사한 교재 대부분이 '직업'을 상위 5과에 둔다. 우리만 없어서 6일차 뒤에 넣는다.
102 숫자와 돈: 베트남 물가는 만~십만 동 단위라 1~10만으로는 가격 대화가 성립하지 않는다.
   사칙연산·잔돈까지 여기서 끝낸다(교재들은 숫자→가격을 한 흐름으로 잇는다)."""
import json, pathlib, sys
sys.path.insert(0,'tools')
from tone import word_tones
def W(vi,ko,kr,h=None,s=None):
    d={"vi":vi,"ko":ko,"kr_read":kr,"tones":word_tones(vi)}
    if h: d["hanja"]=h
    if s: d["south"]=s
    return d
def L(who,vi,ko,kr,g): return {"who":who,"vi":vi,"ko":ko,"kr_read":kr,
    "gloss":[{"w":a,"m":b} for a,b in g],"tones":word_tones(vi)}
def X(vi,ko,kr): return {"vi":vi,"ko":ko,"kr_read":kr,"tones":word_tones(vi)}
def D(day,theme,intro,words,title,lines,extra,goal,how,a,b):
    return {"day":day,"theme":theme,"intro":intro,"words":words,
            "dialog":{"title":title,"lines":lines,"extra":extra},
            "mission":{"goal":goal,"how":how,"a":a,"b":b}}
DAYS=[]

DAYS.append(D(101,"무슨 일 하세요",
 "베트남에서 처음 만나면 나이 다음으로 묻는 것이 '무슨 일 하세요'다. 공장·회사 말은 여기서 한 번에 익힌다.",
 [W("làm việc","일하다","람 비엑"), W("nghề","직업·기술","응에"),
  W("công ty","회사","꽁 띠","公司 (공사)"), W("nhà máy","공장","냐 마이"),
  W("công nhân","노동자·직공","꽁 년","工人 (공인)"),
  W("nhân viên","직원","년 비엔","人員 (인원)"),
  W("văn phòng","사무실","반 퐁","文房 (문방)"),
  W("học","배우다·공부하다","혹","學 (학)"),
  W("vất vả","고되다·힘들다","벗 바"), W("tuyển","뽑다·채용하다","뚜이엔")],
 "무슨 일 하세요?",
 [L("A","Anh làm nghề gì?","무슨 일 하세요?","아인 람 응에 지",
    [("Anh","형·오빠"),("làm","하다"),("nghề","직업"),("gì","무엇")]),
  L("B","Tôi làm việc ở nhà máy.","저는 공장에서 일해요.","또이 람 비엑 어 냐 마이",
    [("Tôi","나"),("làm việc","일하다"),("ở","~에서"),("nhà máy","공장")])],
 [X("Em là công nhân, em học nghề.","저는 직공이고, 기술을 배우고 있어요","앰 라 꽁 년 앰 혹 응에"),
  X("Công ty tuyển công nhân.","회사가 직공을 뽑아요","꽁 띠 뚜이엔 꽁 년"),
  X("Chị là nhân viên văn phòng.","누나는 사무실 직원이에요","찌 라 년 비엔 반 퐁"),
  X("Việc rất vất vả.","일이 아주 고돼요","비엑 젓 벗 바")],
 "내 일을 한 문장으로 말하기",
 "상대의 직업을 묻고, 내 일터를 말해 보라.",
 "당신은 봉제공장 직공입니다","당신은 사무실 직원입니다"))

DAYS.append(D(102,"숫자와 돈 계산",
 "베트남 돈은 단위가 크다. 커피 한 잔이 이만 오천 동이다. 백·천·백만만 알면 가격은 다 들린다. 더하기·빼기도 여기서 끝낸다.",
 [W("trăm","백 (100)","짬"), W("chục","열 (10개 묶음)","쭉"),
  W("triệu","백만","찌에우"), W("giá","가격","자"),
  W("tính","계산하다","띤"), W("cộng","더하다","꽁"),
  W("trừ","빼다","쯔"), W("bằng","같다 (=)","방"),
  W("tiền lẻ","잔돈","띠엔 래"), W("tiền thừa","거스름돈","띠엔 트어")],
 "얼마예요?",
 [L("A","Cái này giá bao nhiêu?","이거 얼마예요?","까이 나이 자 바오 니에우",
    [("Cái này","이것"),("giá","가격"),("bao nhiêu","얼마")]),
  L("B","Hai trăm nghìn đồng.","이십만 동이요.","하이 짬 응인 동",
    [("Hai trăm","이백"),("nghìn","천"),("đồng","동")])],
 [X("Một chục cái, tính tiền cho tôi.","열 개요, 계산해 주세요","못 쭉 까이 띤 띠엔 쪼 또이"),
  X("Năm triệu đồng, đắt lắm.","오백만 동, 너무 비싸요","남 찌에우 동 닷 람"),
  X("Hai cộng ba bằng năm.","2 더하기 3은 5","하이 꽁 바 방 남"),
  X("Mười trừ bốn bằng sáu.","10 빼기 4는 6","므어이 쯔 본 방 사우"),
  X("Tiền lẻ và tiền thừa của tôi đâu?","제 잔돈과 거스름돈은 어디 있어요?","띠엔 래 바 띠엔 트어 꾸어 또이 더우")],
 "가격 듣고 계산하기",
 "물건값을 묻고, 거스름돈까지 말해 보라.",
 "당신은 손님입니다","당신은 가게 주인입니다"))

pathlib.Path('data/_b7.json').write_text(json.dumps({"days":DAYS},ensure_ascii=False,indent=1))
print(f"b7: Day 101~102 (일상 확장) / 단어 {sum(len(d['words']) for d in DAYS)}")
