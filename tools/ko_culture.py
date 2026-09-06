#!/usr/bin/env python3
"""한국 생활 문화 9개 — 직장 예절부터 긴급 상황까지.

KIIP의 "한국 사회 이해" 취지를 참고했지만 교재 원문은 안 봤다 — 여기 적은
건전 상식(공휴일 날짜, 신고 전화번호, 분리수거 원칙 등)은 대한민국 국민 누구나
아는 공공의 사실이라 특정 저작물이 아니다. 지역마다 다를 수 있는 세부 규정
(분리수거 요일, 마트 휴무일 등)은 일부러 빼고 전국 공통 원칙만 적었다.
"""

CULTURE = [
 {"n": 1, "title_ko": "직장 예절", "title_vi": "Phép tắc nơi làm việc",
  "explain_ko": "출근·퇴근 인사와 존댓말은 기본입니다. 지각은 절대 피해야 하고, 늦을 것 같으면 미리 연락합니다.",
  "explain_vi": "Chào khi đến/về và dùng kính ngữ là điều cơ bản. Tuyệt đối tránh đi muộn, nếu có khả năng muộn thì liên lạc trước.",
  "table": [
    {"ko": "수고하셨습니다", "read": "sugohasyeotseumnida", "vi": "câu chào khi tan làm, nói với đồng nghiệp/cấp trên"},
    {"ko": "회식", "read": "hoesik", "vi": "bữa ăn tập thể của công ty — thường sau giờ làm, không bắt buộc nhưng hay được mời"},
    {"ko": "야근", "read": "yageun", "vi": "làm thêm giờ (tăng ca)"},
  ]},
 {"n": 2, "title_ko": "대중교통 이용", "title_vi": "Sử dụng phương tiện công cộng",
  "explain_ko": "교통카드 하나로 버스·지하철을 다 탈 수 있고, 정해진 시간 안에 갈아타면 환승 요금이 할인됩니다.",
  "explain_vi": "Một thẻ giao thông dùng được cho cả xe buýt và tàu điện ngầm, chuyển tuyến trong thời gian quy định sẽ được giảm giá.",
  "table": [
    {"ko": "교통카드", "read": "T-money 등", "vi": "thẻ giao thông — nạp tiền rồi quẹt khi lên/xuống"},
    {"ko": "환승", "read": "hwanseung", "vi": "chuyển tuyến — quẹt thẻ khi xuống cũ, lên mới trong giờ quy định thì được giảm giá"},
    {"ko": "노약자석", "read": "noyakjaseok", "vi": "ghế ưu tiên cho người già/người khuyết tật/phụ nữ mang thai — nên nhường"},
  ]},
 {"n": 3, "title_ko": "편의점 · 마트", "title_vi": "Cửa hàng tiện lợi · Siêu thị",
  "explain_ko": "24시간 여는 편의점이 흔합니다. 배달 애플리케이션으로 음식을 시켜 집에서 받는 문화도 널리 퍼져 있습니다.",
  "explain_vi": "Cửa hàng tiện lợi mở 24 giờ khá phổ biến. Văn hóa đặt đồ ăn qua ứng dụng giao hàng cũng rất phổ biến.",
  "table": [
    {"ko": "편의점", "read": "pyeonuijeom", "vi": "cửa hàng tiện lợi — nhiều nơi mở 24 giờ"},
    {"ko": "배달 앱", "read": "baedal app", "vi": "ứng dụng đặt đồ ăn giao tận nơi"},
    {"ko": "포장", "read": "pojang", "vi": "mua mang đi (không ăn tại chỗ)"},
  ]},
 {"n": 4, "title_ko": "병원 · 약국", "title_vi": "Bệnh viện · Hiệu thuốc",
  "explain_ko": "감기 같은 가벼운 증상은 약국에서 먼저 상담해도 됩니다. 큰 병원은 미리 예약해야 하는 경우가 많습니다.",
  "explain_vi": "Triệu chứng nhẹ như cảm cúm có thể hỏi hiệu thuốc trước. Bệnh viện lớn nhiều khi cần đặt lịch hẹn trước.",
  "table": [
    {"ko": "약국", "read": "yakguk", "vi": "hiệu thuốc — có thể tư vấn thuốc không cần đơn cho bệnh nhẹ"},
    {"ko": "보건소", "read": "bogeonso", "vi": "trung tâm y tế công — phí thấp hoặc miễn phí, có ở mỗi khu vực"},
    {"ko": "건강보험증", "read": "geongangboheomjeung", "vi": "thẻ bảo hiểm y tế — mang theo khi khám bệnh để được giảm phí"},
  ]},
 {"n": 5, "title_ko": "명절 — 설날 · 추석", "title_vi": "Ngày lễ lớn — Tết Nguyên đán · Trung thu",
  "explain_ko": "설날(음력 1월 1일)과 추석(음력 8월 15일)은 한국의 가장 큰 명절입니다. 이 기간엔 상점이 문을 닫는 경우가 많습니다.",
  "explain_vi": "Tết (mùng 1 tháng 1 âm lịch) và Trung thu (rằm tháng 8 âm lịch) là hai ngày lễ lớn nhất của Hàn Quốc. Vào dịp này nhiều cửa hàng đóng cửa.",
  "table": [
    {"ko": "설날", "read": "seollal", "vi": "Tết Nguyên đán — ăn 떡국(canh bánh gạo), mừng tuổi trẻ em"},
    {"ko": "추석", "read": "chuseok", "vi": "Tết Trung thu Hàn Quốc — cúng tổ tiên, ăn 송편(bánh gạo hình bán nguyệt)"},
    {"ko": "연휴", "read": "yeonhyu", "vi": "kỳ nghỉ liên tiếp nhiều ngày"},
  ]},
 {"n": 6, "title_ko": "쓰레기 분리배출", "title_vi": "Phân loại rác",
  "explain_ko": "한국은 쓰레기를 일반·재활용·음식물 세 가지로 나눠 버리는 것이 원칙입니다. 일반쓰레기는 지역에서 정한 유료 봉투에 담아야 합니다. 정확한 요일·장소는 사는 곳 관리사무소나 주민센터에서 확인하는 게 안전합니다.",
  "explain_vi": "Nguyên tắc ở Hàn Quốc là chia rác thành 3 loại: rác thường, tái chế, rác thực phẩm. Rác thường phải đựng trong túi rác trả phí theo quy định địa phương. Ngày giờ, địa điểm cụ thể nên hỏi ban quản lý nơi ở hoặc trung tâm hành chính phường để chắc chắn.",
  "table": [
    {"ko": "일반쓰레기", "read": "ilban sseuregi", "vi": "rác thường — phải dùng túi rác trả phí (종량제봉투)"},
    {"ko": "재활용", "read": "jaehwallyong", "vi": "rác tái chế — giấy/nhựa/lon/chai tách riêng"},
    {"ko": "음식물 쓰레기", "read": "eumsingmul sseuregi", "vi": "rác thực phẩm — đựng riêng, thường có thùng chuyên dụng"},
  ]},
 {"n": 7, "title_ko": "위급 상황 전화번호", "title_vi": "Số điện thoại khẩn cấp",
  "explain_ko": "위급할 때는 망설이지 말고 전화하세요. 말이 서툴러도 괜찮습니다 — 상담원이 도와줍니다.",
  "explain_vi": "Khi khẩn cấp đừng ngần ngại, hãy gọi ngay. Nói chưa giỏi cũng không sao — tổng đài sẽ hỗ trợ.",
  "table": [
    {"ko": "112", "read": "일일이", "vi": "báo cảnh sát (trộm cắp, bạo lực, tai nạn giao thông…)"},
    {"ko": "119", "read": "일일구", "vi": "cứu hỏa · cấp cứu (hỏa hoạn, tai nạn, cần xe cứu thương)"},
    {"ko": "1345", "read": "외국인종합안내센터", "vi": "trung tâm tư vấn cho người nước ngoài (visa, cư trú…) — hỗ trợ đa ngôn ngữ"},
  ]},
 {"n": 8, "title_ko": "은행 이용", "title_vi": "Sử dụng ngân hàng",
  "explain_ko": "통장을 만들 때 외국인등록증이 필요합니다. 현금자동인출기(ATM)로 입출금을 할 수 있고, 늦은 시간에는 수수료가 붙을 수 있습니다.",
  "explain_vi": "Cần thẻ đăng ký người nước ngoài khi mở tài khoản. Có thể gửi/rút tiền qua ATM, ngoài giờ hành chính có thể mất phí.",
  "table": [
    {"ko": "통장", "read": "tongjang", "vi": "sổ/tài khoản ngân hàng"},
    {"ko": "현금자동인출기(ATM)", "read": "hyeongeum jadong inchulgi", "vi": "máy rút tiền tự động"},
    {"ko": "체크카드", "read": "chekeu kadeu", "vi": "thẻ ghi nợ — trừ tiền trực tiếp từ tài khoản"},
  ]},
 {"n": 9, "title_ko": "체류와 관련 기관", "title_vi": "Cư trú và các cơ quan liên quan",
  "explain_ko": "외국인등록증은 늘 지니고 다니는 게 좋습니다. 체류기간 연장은 만료되기 전에 미리 신청해야 합니다. 임금 체불 등 노동 문제는 고용노동부(고용센터)에서 상담할 수 있습니다.",
  "explain_vi": "Nên luôn mang theo thẻ đăng ký người nước ngoài. Gia hạn thời gian cư trú phải nộp trước khi hết hạn. Vấn đề lao động như nợ lương có thể tư vấn tại Bộ Việc làm và Lao động (trung tâm việc làm).",
  "table": [
    {"ko": "외국인등록증", "read": "oegugin deungnokjeung", "vi": "thẻ đăng ký người nước ngoài — luôn mang theo"},
    {"ko": "체류기간 연장", "read": "cheryu gigan yeonjang", "vi": "gia hạn thời gian cư trú — nộp trước khi hết hạn"},
    {"ko": "고용노동부", "read": "goyongnodongbu", "vi": "Bộ Việc làm và Lao động — tư vấn nợ lương, tai nạn lao động"},
  ]},
]

if __name__ == "__main__":
    import json, os
    n_row = sum(len(c["table"]) for c in CULTURE)
    print(f"문화 {len(CULTURE)}개 · 표 항목 {n_row}개")
    out = os.path.join(os.path.dirname(__file__), "..", "data", "ko_culture.json")
    json.dump({"note": "특정 교재 미참고 — 공휴일 날짜·신고 전화번호·분리배출 원칙 등 공공의 상식만 기재",
               "items": CULTURE},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("저장:", out)
