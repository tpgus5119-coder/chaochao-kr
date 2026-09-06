#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""무역 낱말 → data/_trade.json  (봉제용어.xls 「무역용어」 시트 바탕)

그 시트에는 **베트남어가 없다** — 약자 | 영어 | 한국어 | 설명 네 칸뿐이다.
그래서 베트남어를 붙여야 하는데, **지어내지 않고 하나씩 확인했다**(대표님 지시).
  확인한 곳: VinaTrain·Interlink·ECUS 등 베트남 무역 실무 자료
  · Proforma Invoice   → hoá đơn chiếu lệ
  · Bill of Lading     → vận đơn
  · Letter of Credit   → thư tín dụng
  · Certificate of Origin → giấy chứng nhận xuất xứ
  · Bonded Area        → khu phi thuế quan   (보세창고는 kho ngoại quan)
  · Transshipment      → chuyển tải
  · Consignee          → người nhận hàng
  · Purchase Order     → đơn đặt hàng
FOB·CIF·CFR 처럼 **베트남에서도 영어 약자를 그대로 쓰는 것**은 낱말로 안 넣는다
(giá FOB 라고 말한다 — 낱말이 아니라 조건 이름이다).
쓰기: python3 tools/trade_words.py
"""
import json, pathlib, sys

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
import vi_kr

W = [
 ("hoá đơn chiếu lệ", "견적송장 (PI)"),
 ("đơn đặt hàng", "주문서 (PO)"),
 ("hợp đồng", "계약서"),
 ("hoá đơn thương mại", "상업송장"),
 ("vận đơn", "선하증권 (B/L)"),
 ("vận đơn hàng không", "항공화물운송장 (AWB)"),
 ("giấy chứng nhận xuất xứ", "원산지증명서 (C/O)"),
 ("giấy chứng nhận bảo hiểm", "보험증명서"),
 ("giấy chứng nhận kiểm định", "검사증명서"),
 ("thư tín dụng", "신용장 (L/C)"),
 ("thư bảo lãnh", "보증서 (L/G)"),
 ("chuyển tiền bằng điện", "전신환송금 (T/T)"),
 ("thanh toán khi giao hàng", "현금결제 (COD)"),
 ("hải quan", "세관"),
 ("thông quan", "통관"),
 ("tờ khai hải quan", "통관 신고서"),
 ("thuế nhập khẩu", "수입 관세"),
 ("thuế xuất khẩu", "수출 관세"),
 ("khu phi thuế quan", "보세구역"),
 ("kho ngoại quan", "보세창고"),
 ("chuyển tải", "환적"),
 ("người nhận hàng", "화주·수하인 (Consignee)"),
 ("bên được thông báo", "화물도착통지처"),
 ("cước vận chuyển", "운임"),
 ("cước trả trước", "운임 선지급"),
 ("cước trả sau", "운임 도착지불"),
 ("hàng nguyên container", "컨테이너 만재화물 (FCL)"),
 ("hàng lẻ", "컨테이너 미달화물 (LCL)"),
 ("mét khối", "입방미터 (CBM)"),
 ("mã HS", "HS 코드 (품목분류)"),
 ("cấm vận", "수출입 금지"),
 ("ngày dự kiến khởi hành", "출항 예정일 (ETD)"),
 ("ngày dự kiến đến", "도착 예정일 (ETA)"),
 ("sản xuất theo đơn đặt hàng", "주문자상표부착생산 (OEM)"),
 ("báo cáo nhận hàng", "수취보고서"),
 ("bốc hàng lên tàu", "선적하다"),
 ("dỡ hàng", "하역하다"),
 ("người xuất khẩu", "수출자"),
 ("người nhập khẩu", "수입자"),
 ("hãng tàu", "선사"),
]

def main():
    out = [{"vi": v, "ko": k, "kr": vi_kr.word(v), "krs": vi_kr.word(v, True),
            "track": "공통", "trade": 1} for v, k in W]
    (R / "data" / "_trade.json").write_text(json.dumps(
        {"note": "무역 낱말. 원본 표에 베트남어가 없어 하나씩 확인해 붙였다.",
         "words": out}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"무역 낱말 {len(out)}개")
main()
