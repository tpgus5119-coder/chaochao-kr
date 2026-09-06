#!/usr/bin/env python3
"""날마다 배우는 과정 — 1차분: 초급1, 18일치.

각 날은 ko_grammar.json의 초급1 문법과 짝짓는다 — 연결 열쇠는 번호가 아니라
문법 이름(grammar)이다. 문법책 중간에 새 항목을 끼워 넣어 번호가 밀려도 안 끊긴다.
단어는 KIIP 초급1 단원 어휘 목록(kiip_beginner1_vocab.json, 순서=사실이라 참고)에서
골랐지만, 뜻은 kr_vi_vocab_bridge.json을 그대로 믿지 않았다 — 대조하다가

    개→chó(개=강아지로 오역, 진짜 뜻은 '낱개 세는 말') / 시장→thị trưởng(시장=시장(市長)
    으로 오역, 진짜 '시장(市場, 물건 사는 곳)'이 아님) / 공원→công nhân(공원=공원(工員,
    노동자)으로 오역, 진짜 '공원(公園)'이 아님) / 적다→ghi, chép('적다=글씨 쓰다'로 오역,
    진짜 '수가 적다'가 아님) / 일이삼사오칠팔구 숫자 8개 전부 한자 동음이의어로 오역
    (예: 이→con rận(이=벌레)로 오역, 진짜 '2'가 아님)

같은 동형이의어 오역이 열 건 넘게 나왔다 — 한 글자짜리 한자어(단위명사·숫자)일수록
심하다. 그래서 여기 쓴 단어는 전부 직접 다시 확인한 것만 썼다(bridge 원문이 틀렸던
것은 코드에 남기지 않고 맞는 뜻만 썼다 — kr_vi_vocab_bridge.json 자체는 그대로 두되,
이 파일을 쓸 때는 절대 그대로 믿지 않았다는 뜻).
대화·미션은 전부 새로 썼고, 그 날짜까지 배운 문법 안에서만 쓰도록
scan_forward_ref()로 다시 훑는다(ko_grammar.py의 방식과 같다).
미션은 학습자에게 거는 지시문이라 ko/vi 둘 다 있어야 한다(설명문과 같은 대접).
"""

DAYS = [
 {"day": 1, "grammar": "이에요/예요", "theme": {"ko": "자기소개", "vi": "Tự giới thiệu"},
  "words": [
    {"ko": "이름", "vi": "tên"}, {"ko": "직업", "vi": "nghề nghiệp"}, {"ko": "국적", "vi": "quốc tịch"},
    {"ko": "나라", "vi": "đất nước"}, {"ko": "사람", "vi": "người"}, {"ko": "선생님", "vi": "giáo viên"},
    {"ko": "회사원", "vi": "nhân viên công ty"}, {"ko": "학생", "vi": "học sinh"},
    {"ko": "전화번호", "vi": "số điện thoại"}, {"ko": "한국어", "vi": "tiếng Hàn"},
  ],
  "dialog": {"title": "처음 인사하기", "lines": [
    {"who": "A", "ko": "안녕하세요. 저는 후엉이에요.", "vi": "Xin chào. Tôi là Hương."},
    {"who": "B", "ko": "안녕하세요. 저는 민수예요.", "vi": "Xin chào. Tôi là Min-su."},
    {"who": "B", "ko": "후엉 씨는 학생이에요?", "vi": "Chị Hương là học sinh à?"},
    {"who": "A", "ko": "네, 저는 학생이에요.", "vi": "Vâng, tôi là học sinh."},
  ]},
  "mission": {"ko": "새로 만난 사람에게 이름과 국적을 소개해 보세요.",
              "vi": "Hãy giới thiệu tên và quốc tịch của bạn với người mới gặp."}},
 {"day": 2, "grammar": "이/가 있다·없다", "theme": {"ko": "교실 사물", "vi": "Đồ vật trong lớp học"},
  "words": [
    {"ko": "책상", "vi": "bàn học"}, {"ko": "의자", "vi": "ghế"}, {"ko": "침대", "vi": "giường"},
    {"ko": "컴퓨터", "vi": "máy vi tính"}, {"ko": "휴대 전화", "vi": "điện thoại di động"},
    {"ko": "시계", "vi": "đồng hồ"}, {"ko": "학교", "vi": "trường học"}, {"ko": "교실", "vi": "phòng học"},
    {"ko": "책", "vi": "sách"}, {"ko": "화장실", "vi": "nhà vệ sinh"},
  ],
  "dialog": {"title": "교실에 뭐가 있어요?", "lines": [
    {"who": "A", "ko": "교실에 책상이 있어요?", "vi": "Trong lớp có bàn học không?"},
    {"who": "B", "ko": "네, 책상하고 의자가 있어요.", "vi": "Có, có bàn học và ghế."},
    {"who": "A", "ko": "컴퓨터도 있어요?", "vi": "Có cả máy vi tính không?"},
    {"who": "B", "ko": "아니요, 컴퓨터는 없어요.", "vi": "Không, không có máy vi tính."},
  ]},
  "mission": {"ko": "내 방에 무엇이 있는지 말해 보세요.",
              "vi": "Hãy nói xem trong phòng của bạn có gì."}},
 {"day": 3, "grammar": "아요/어요 (현재)", "theme": {"ko": "기분과 상태", "vi": "Cảm giác và trạng thái"},
  "words": [
    {"ko": "많다", "vi": "nhiều"}, {"ko": "크다", "vi": "lớn"}, {"ko": "작다", "vi": "nhỏ"},
    {"ko": "맛있다", "vi": "ngon"}, {"ko": "어렵다", "vi": "khó"}, {"ko": "쉽다", "vi": "dễ"},
    {"ko": "춥다", "vi": "lạnh"}, {"ko": "덥다", "vi": "nóng"}, {"ko": "재미있다", "vi": "thú vị"},
    {"ko": "바쁘다", "vi": "bận"},
  ],
  "dialog": {"title": "오늘 날씨", "lines": [
    {"who": "A", "ko": "오늘 날씨가 어때요?", "vi": "Hôm nay thời tiết thế nào?"},
    {"who": "B", "ko": "조금 더워요. 하지만 좋아요.", "vi": "Hơi nóng. Nhưng mà đẹp trời."},
    {"who": "A", "ko": "저도 좋아요.", "vi": "Tôi cũng thích."},
  ]},
  "mission": {"ko": "오늘 기분이 어떤지 형용사로 말해 보세요.",
              "vi": "Hãy dùng tính từ để nói hôm nay bạn cảm thấy thế nào."}},
 {"day": 4, "grammar": "에 가다/오다", "theme": {"ko": "장소", "vi": "Địa điểm"},
  "words": [
    {"ko": "학교", "vi": "trường học"}, {"ko": "편의점", "vi": "cửa hàng tiện lợi"},
    {"ko": "은행", "vi": "ngân hàng"}, {"ko": "집", "vi": "nhà"}, {"ko": "식당", "vi": "nhà hàng"},
    {"ko": "카페", "vi": "quán cà phê"}, {"ko": "병원", "vi": "bệnh viện"}, {"ko": "약국", "vi": "nhà thuốc"},
    {"ko": "시장", "vi": "chợ"}, {"ko": "공원", "vi": "công viên"},
  ],
  "dialog": {"title": "어디에 가요?", "lines": [
    {"who": "A", "ko": "지금 어디에 가요?", "vi": "Bây giờ bạn đi đâu?"},
    {"who": "B", "ko": "저는 시장에 가요.", "vi": "Tôi đi chợ."},
    {"who": "A", "ko": "저는 병원에 가요.", "vi": "Tôi đi bệnh viện."},
  ]},
  "mission": {"ko": "오늘 어디에 가는지 '~에 가요'로 말해 보세요.",
              "vi": "Hãy dùng '~에 가요' để nói hôm nay bạn đi đâu."}},
 {"day": 5, "grammar": "이다 + 날짜", "theme": {"ko": "숫자(한자어)와 날짜", "vi": "Số Hán-Hàn và ngày tháng"},
  "words": [
    {"ko": "일", "vi": "một"}, {"ko": "이", "vi": "hai"}, {"ko": "삼", "vi": "ba"},
    {"ko": "사", "vi": "bốn"}, {"ko": "오", "vi": "năm"}, {"ko": "육", "vi": "sáu"},
    {"ko": "칠", "vi": "bảy"}, {"ko": "팔", "vi": "tám"}, {"ko": "구", "vi": "chín"},
    {"ko": "십", "vi": "mười"},
  ],
  "dialog": {"title": "며칠이에요?", "lines": [
    {"who": "A", "ko": "오늘이 며칠이에요?", "vi": "Hôm nay là ngày mấy?"},
    {"who": "B", "ko": "오늘은 5월 5일이에요.", "vi": "Hôm nay là ngày 5 tháng 5."},
    {"who": "A", "ko": "생일이 며칠이에요?", "vi": "Sinh nhật bạn ngày mấy?"},
    {"who": "B", "ko": "제 생일은 8월 9일이에요.", "vi": "Sinh nhật tôi là ngày 9 tháng 8."},
  ]},
  "mission": {"ko": "내 생일을 한국어 숫자로 말해 보세요.",
              "vi": "Hãy nói sinh nhật của bạn bằng số tiếng Hàn."}},
 {"day": 6, "grammar": "부터 ~까지", "theme": {"ko": "숫자(고유어)와 시간", "vi": "Số thuần Hàn và thời gian"},
  "words": [
    {"ko": "하나", "vi": "một"}, {"ko": "둘", "vi": "hai"}, {"ko": "셋", "vi": "ba"},
    {"ko": "넷", "vi": "bốn"}, {"ko": "다섯", "vi": "năm"}, {"ko": "여섯", "vi": "sáu"},
    {"ko": "일곱", "vi": "bảy"}, {"ko": "여덟", "vi": "tám"}, {"ko": "아홉", "vi": "chín"},
    {"ko": "열", "vi": "mười"},
  ],
  "dialog": {"title": "몇 시부터 몇 시까지", "lines": [
    {"who": "A", "ko": "회사에 언제부터 언제까지 있어요?", "vi": "Bạn ở công ty từ mấy giờ đến mấy giờ?"},
    {"who": "B", "ko": "아홉 시부터 여섯 시까지 있어요.", "vi": "Tôi ở từ 9 giờ đến 6 giờ."},
    {"who": "A", "ko": "점심시간은 언제예요?", "vi": "Giờ ăn trưa là khi nào?"},
    {"who": "B", "ko": "열두 시부터 한 시까지예요.", "vi": "Từ 12 giờ đến 1 giờ."},
  ]},
  "mission": {"ko": "오늘 몇 시부터 몇 시까지 일하는지 말해 보세요.",
              "vi": "Hãy nói hôm nay bạn làm việc từ mấy giờ đến mấy giờ."}},
 {"day": 7, "grammar": "(으)세요 (요청)", "theme": {"ko": "식당에서 주문", "vi": "Gọi món ở nhà hàng"},
  "words": [
    {"ko": "김치찌개", "vi": "canh kimchi"}, {"ko": "비빔밥", "vi": "cơm trộn"},
    {"ko": "불고기", "vi": "thịt nướng"}, {"ko": "삼겹살", "vi": "thịt ba chỉ"},
    {"ko": "라면", "vi": "mì ăn liền"}, {"ko": "김밥", "vi": "cơm cuộn rong biển"},
    {"ko": "반찬", "vi": "món ăn kèm"}, {"ko": "숟가락", "vi": "cái thìa"},
    {"ko": "젓가락", "vi": "đũa"}, {"ko": "메뉴", "vi": "thực đơn"},
  ],
  "dialog": {"title": "주문할게요", "lines": [
    {"who": "A", "ko": "여기 김치찌개 하나 주세요.", "vi": "Cho tôi một canh kimchi."},
    {"who": "B", "ko": "네.", "vi": "Vâng."},
    {"who": "A", "ko": "반찬도 더 주세요.", "vi": "Cho thêm món ăn kèm nữa."},
  ]},
  "mission": {"ko": "식당에서 음식을 주문하는 문장을 만들어 보세요.",
              "vi": "Hãy tạo câu gọi món ở nhà hàng."}},
 {"day": 8, "grammar": "-습니다/ㅂ니다 (격식체)", "theme": {"ko": "회사 물건", "vi": "Đồ dùng công ty"},
  "words": [
    {"ko": "물", "vi": "nước"}, {"ko": "커피", "vi": "cà phê"}, {"ko": "강아지", "vi": "chó con"},
    {"ko": "잡지", "vi": "tạp chí"}, {"ko": "사진", "vi": "bức ảnh"}, {"ko": "노트북", "vi": "máy tính xách tay"},
    {"ko": "녹차", "vi": "trà xanh"}, {"ko": "청소기", "vi": "máy hút bụi"},
    {"ko": "닭고기", "vi": "thịt gà"}, {"ko": "계란", "vi": "trứng gà"},
  ],
  "dialog": {"title": "격식 있게 소개하기", "lines": [
    {"who": "A", "ko": "안녕하십니까? 저는 후엉입니다.", "vi": "Xin chào. Tôi là Hương."},
    {"who": "B", "ko": "반갑습니다. 저는 김민수입니다.", "vi": "Rất vui được gặp. Tôi là Kim Min-su."},
    {"who": "B", "ko": "저는 이 회사에서 일합니다.", "vi": "Tôi làm việc ở công ty này."},
  ]},
  "mission": {"ko": "처음 만난 회사 사람에게 격식체로 인사해 보세요.",
              "vi": "Hãy chào người mới gặp ở công ty bằng thể trang trọng."}},
 {"day": 9, "grammar": "았/었어요 (과거)", "theme": {"ko": "주말 활동", "vi": "Hoạt động cuối tuần"},
  "words": [
    {"ko": "산책하다", "vi": "đi dạo"}, {"ko": "쇼핑하다", "vi": "mua sắm"},
    {"ko": "백화점", "vi": "trung tâm mua sắm"}, {"ko": "즐겁다", "vi": "vui vẻ"},
    {"ko": "걷다", "vi": "đi bộ"}, {"ko": "공원", "vi": "công viên"}, {"ko": "시장", "vi": "chợ"},
  ],
  "dialog": {"title": "주말에 뭐 했어요?", "lines": [
    {"who": "A", "ko": "주말에 뭐 했어요?", "vi": "Cuối tuần bạn đã làm gì?"},
    {"who": "B", "ko": "공원에서 산책했어요. 민수 씨는요?", "vi": "Tôi đi dạo ở công viên. Còn anh Min-su?"},
    {"who": "A", "ko": "저는 백화점에서 쇼핑했어요.", "vi": "Tôi đi mua sắm ở trung tâm mua sắm."},
  ]},
  "mission": {"ko": "지난 주말에 무엇을 했는지 과거형으로 말해 보세요.",
              "vi": "Hãy dùng thì quá khứ để nói bạn đã làm gì cuối tuần trước."}},
 {"day": 10, "grammar": "(으)시- (높임)", "theme": {"ko": "가족", "vi": "Gia đình"},
  "words": [
    {"ko": "할머니", "vi": "bà"}, {"ko": "할아버지", "vi": "ông"}, {"ko": "어머니", "vi": "mẹ"},
    {"ko": "아버지", "vi": "bố"}, {"ko": "언니", "vi": "chị"}, {"ko": "오빠", "vi": "anh"},
    {"ko": "여동생", "vi": "em gái"}, {"ko": "남동생", "vi": "em trai"}, {"ko": "누나", "vi": "chị"},
    {"ko": "부모님", "vi": "bố mẹ"},
  ],
  "dialog": {"title": "부모님은 뭐 하세요?", "lines": [
    {"who": "A", "ko": "아버지는 지금 뭐 하세요?", "vi": "Bố bạn đang làm gì?"},
    {"who": "B", "ko": "아버지는 요리하세요.", "vi": "Bố tôi đang nấu ăn."},
    {"who": "A", "ko": "어머니는 뭐 하세요?", "vi": "Mẹ bạn đang làm gì?"},
    {"who": "B", "ko": "어머니는 텔레비전을 보세요.", "vi": "Mẹ tôi đang xem ti vi."},
  ]},
  "mission": {"ko": "부모님이 지금 무엇을 하시는지 높임말로 말해 보세요.",
              "vi": "Hãy dùng kính ngữ để nói bố mẹ bạn đang làm gì."}},
 {"day": 11, "grammar": "께 / 드리다 (높임)", "theme": {"ko": "선물과 행사", "vi": "Quà tặng và sự kiện"},
  "words": [
    {"ko": "주다", "vi": "cho"}, {"ko": "보내다", "vi": "gửi"}, {"ko": "받다", "vi": "nhận"},
    {"ko": "선물", "vi": "quà"}, {"ko": "초대장", "vi": "thư mời"}, {"ko": "축하하다", "vi": "chúc mừng"},
    {"ko": "케이크", "vi": "bánh kem"}, {"ko": "결혼식", "vi": "lễ cưới"}, {"ko": "졸업식", "vi": "lễ tốt nghiệp"},
    {"ko": "어버이날", "vi": "ngày cha mẹ"},
  ],
  "dialog": {"title": "부모님께 드렸어요", "lines": [
    {"who": "A", "ko": "어버이날에 부모님께 뭘 드렸어요?", "vi": "Ngày cha mẹ bạn đã tặng gì cho bố mẹ?"},
    {"who": "B", "ko": "꽃을 드렸어요. 그리고 편지도 드렸어요.", "vi": "Tôi đã tặng hoa. Và cả thư nữa."},
    {"who": "A", "ko": "저도 부모님께 편지를 드렸어요.", "vi": "Tôi cũng đã viết thư cho bố mẹ."},
  ]},
  "mission": {"ko": "특별한 날에 누구에게 무엇을 드렸는지 말해 보세요.",
              "vi": "Hãy nói bạn đã tặng gì cho ai vào ngày đặc biệt."}},
 {"day": 12, "grammar": "(으)ㄹ 거예요 (미래)", "theme": {"ko": "휴가 계획", "vi": "Kế hoạch nghỉ phép"},
  "words": [
    {"ko": "휴가", "vi": "kỳ nghỉ"}, {"ko": "친척", "vi": "họ hàng"}, {"ko": "화장품", "vi": "mỹ phẩm"},
    {"ko": "빨리", "vi": "nhanh"}, {"ko": "휴일", "vi": "ngày nghỉ"},
  ],
  "dialog": {"title": "휴가에 뭐 할 거예요?", "lines": [
    {"who": "A", "ko": "이번 휴가에 뭐 할 거예요?", "vi": "Kỳ nghỉ này bạn sẽ làm gì?"},
    {"who": "B", "ko": "저는 고향에 갈 거예요. 민수 씨는요?", "vi": "Tôi sẽ về quê. Còn anh Min-su?"},
    {"who": "A", "ko": "저는 집에서 쉴 거예요.", "vi": "Tôi sẽ nghỉ ở nhà."},
  ]},
  "mission": {"ko": "다음 휴가 계획을 '~ㄹ 거예요'로 말해 보세요.",
              "vi": "Hãy dùng '~ㄹ 거예요' để nói kế hoạch kỳ nghỉ tới."}},
 {"day": 13, "grammar": "(으)로 (수단)", "theme": {"ko": "교통수단", "vi": "Phương tiện giao thông"},
  "words": [
    {"ko": "자동차", "vi": "xe ô tô"}, {"ko": "버스", "vi": "xe buýt"}, {"ko": "택시", "vi": "xe taxi"},
    {"ko": "자전거", "vi": "xe đạp"}, {"ko": "지하철", "vi": "tàu điện ngầm"}, {"ko": "오토바이", "vi": "xe máy"},
    {"ko": "공항", "vi": "sân bay"}, {"ko": "비행기", "vi": "máy bay"}, {"ko": "기차", "vi": "tàu hỏa"},
    {"ko": "정류장", "vi": "trạm xe buýt"},
  ],
  "dialog": {"title": "공항에 어떻게 가요?", "lines": [
    {"who": "A", "ko": "공항에 어떻게 가요?", "vi": "Bạn đi sân bay bằng gì?"},
    {"who": "B", "ko": "저는 버스로 가요.", "vi": "Tôi đi bằng xe buýt."},
    {"who": "A", "ko": "저는 지하철로 갈 거예요.", "vi": "Tôi sẽ đi bằng tàu điện ngầm."},
  ]},
  "mission": {"ko": "회사나 학교에 어떤 교통수단으로 가는지 말해 보세요.",
              "vi": "Hãy nói bạn đi công ty hoặc trường học bằng phương tiện gì."}},
 {"day": 14, "grammar": "(으)ㄹ까요? (제안)", "theme": {"ko": "약속 잡기", "vi": "Hẹn gặp"},
  "words": [
    {"ko": "모임", "vi": "cuộc họp"}, {"ko": "약속하다", "vi": "hứa hẹn"}, {"ko": "답장하다", "vi": "hồi đáp"},
    {"ko": "만나다", "vi": "gặp"}, {"ko": "시간", "vi": "thời gian"}, {"ko": "장소", "vi": "địa điểm"},
  ],
  "dialog": {"title": "몇 시에 만날까요?", "lines": [
    {"who": "A", "ko": "저녁 7시에 만날까요?", "vi": "Tối 7 giờ mình gặp nhau nhé?"},
    {"who": "B", "ko": "좋아요. 어디에서 만날까요?", "vi": "Được đấy. Gặp ở đâu nhỉ?"},
    {"who": "A", "ko": "카페에서 만날까요?", "vi": "Gặp ở quán cà phê nhé?"},
    {"who": "B", "ko": "네, 좋아요.", "vi": "Vâng, được đấy."},
  ]},
  "mission": {"ko": "친구에게 '~ㄹ까요?'로 약속을 제안해 보세요.",
              "vi": "Hãy dùng '~ㄹ까요?' để rủ bạn hẹn gặp."}},
 {"day": 15, "grammar": "네요 (감탄)", "theme": {"ko": "날씨와 계절", "vi": "Thời tiết và mùa"},
  "words": [
    {"ko": "날씨", "vi": "thời tiết"}, {"ko": "계절", "vi": "mùa"}, {"ko": "봄", "vi": "mùa xuân"},
    {"ko": "여름", "vi": "mùa hè"}, {"ko": "가을", "vi": "mùa thu"}, {"ko": "겨울", "vi": "mùa đông"},
    {"ko": "따뜻하다", "vi": "ấm áp"}, {"ko": "춥다", "vi": "lạnh"}, {"ko": "맑다", "vi": "trong xanh"},
    {"ko": "흐리다", "vi": "nhiều mây"},
  ],
  "dialog": {"title": "날씨가 덥네요", "lines": [
    {"who": "A", "ko": "오늘 날씨가 정말 덥네요.", "vi": "Hôm nay trời nóng thật đấy."},
    {"who": "B", "ko": "네, 어제보다 더 덥네요.", "vi": "Vâng, nóng hơn hôm qua đấy."},
    {"who": "A", "ko": "저는 봄 날씨를 좋아해요.", "vi": "Tôi thích thời tiết mùa xuân."},
  ]},
  "mission": {"ko": "지금 날씨가 어떤지 '~네요'로 감탄해 보세요.",
              "vi": "Hãy dùng '~네요' để cảm thán về thời tiết bây giờ."}},
 {"day": 16, "grammar": "아/어서 (이유)", "theme": {"ko": "몸과 병원", "vi": "Cơ thể và bệnh viện"},
  "words": [
    {"ko": "눈", "vi": "mắt"}, {"ko": "코", "vi": "mũi"}, {"ko": "귀", "vi": "tai"}, {"ko": "목", "vi": "cổ"},
    {"ko": "팔", "vi": "cánh tay"}, {"ko": "배", "vi": "bụng"}, {"ko": "손", "vi": "bàn tay"},
    {"ko": "다리", "vi": "chân"}, {"ko": "무릎", "vi": "đầu gối"}, {"ko": "발", "vi": "bàn chân"},
  ],
  "dialog": {"title": "왜 병원에 가요?", "lines": [
    {"who": "A", "ko": "왜 병원에 가요?", "vi": "Sao bạn đi bệnh viện?"},
    {"who": "B", "ko": "배가 아파서 병원에 가요.", "vi": "Vì đau bụng nên tôi đi bệnh viện."},
    {"who": "A", "ko": "저는 눈이 아파서 안과에 가요.", "vi": "Vì đau mắt nên tôi đi khoa mắt."},
  ]},
  "mission": {"ko": "아픈 곳을 말하고 '~아서/어서'로 이유를 설명해 보세요.",
              "vi": "Hãy nói chỗ đau và dùng '~아서/어서' để giải thích lý do."}},
 {"day": 17, "grammar": "지 마세요 (금지)", "theme": {"ko": "공공장소 예절", "vi": "Phép tắc nơi công cộng"},
  "words": [
    {"ko": "환전하다", "vi": "đổi tiền"}, {"ko": "주차장", "vi": "bãi đỗ xe"}, {"ko": "주차하다", "vi": "đỗ xe"},
    {"ko": "박물관", "vi": "viện bảo tàng"}, {"ko": "경찰서", "vi": "đồn cảnh sát"}, {"ko": "등록하다", "vi": "đăng ký"},
    {"ko": "오른쪽", "vi": "bên phải"}, {"ko": "왼쪽", "vi": "bên trái"}, {"ko": "동물원", "vi": "sở thú"},
    {"ko": "캠핑", "vi": "cắm trại"},
  ],
  "dialog": {"title": "여기 주차하지 마세요", "lines": [
    {"who": "A", "ko": "여기에 주차하지 마세요.", "vi": "Đừng đỗ xe ở đây."},
    {"who": "B", "ko": "아, 죄송합니다.", "vi": "À, xin lỗi."},
    {"who": "A", "ko": "박물관에서는 사진을 찍지 마세요.", "vi": "Ở viện bảo tàng đừng chụp ảnh."},
  ]},
  "mission": {"ko": "공공장소에서 하지 말아야 할 행동을 '~지 마세요'로 말해 보세요.",
              "vi": "Hãy dùng '~지 마세요' để nói hành động không nên làm ở nơi công cộng."}},
 {"day": 18, "grammar": "는데/(으)ㄴ데 (배경·대조)", "theme": {"ko": "한국 생활 적응", "vi": "Thích nghi cuộc sống Hàn Quốc"},
  "words": [
    {"ko": "편하다", "vi": "thoải mái"}, {"ko": "졸업하다", "vi": "tốt nghiệp"}, {"ko": "입학하다", "vi": "nhập học"},
    {"ko": "점심시간", "vi": "giờ ăn trưa"}, {"ko": "의식주", "vi": "ăn mặc ở"}, {"ko": "결혼하다", "vi": "kết hôn"},
    {"ko": "평일", "vi": "ngày thường"}, {"ko": "익숙하다", "vi": "quen thuộc"}, {"ko": "교통 카드", "vi": "thẻ giao thông"},
    {"ko": "팥빙수", "vi": "chè đậu đỏ đá bào"},
  ],
  "dialog": {"title": "한국 생활이 어때요?", "lines": [
    {"who": "A", "ko": "한국 생활이 어때요?", "vi": "Cuộc sống ở Hàn Quốc thế nào?"},
    {"who": "B", "ko": "조금 힘든데 재미있어요.", "vi": "Hơi vất vả nhưng thú vị."},
    {"who": "A", "ko": "한국어는 어려운데 재미있어요.", "vi": "Tiếng Hàn khó nhưng thú vị."},
  ]},
  "mission": {"ko": "한국 생활이나 한국어 공부에 대해 '~는데'로 느낌을 말해 보세요.",
              "vi": "Hãy dùng '~는데' để nói cảm nghĩ về cuộc sống Hàn Quốc hoặc việc học tiếng Hàn."}},
]

# 뒤에서 배우는 문법 표지가 앞 날짜의 대화에 새는지 훑는다(ko_grammar.py와 같은 원리).
# 열쇠는 **날짜**다 — 문법책에 새 항목을 끼워 넣어 번호가 밀려도 여기는 안 흔들린다.
_MARKERS_AFTER = {
  1: ["가 있어요", "가 없어요", "이 있어요", "이 없어요", "부터", "으세요", "세요", "습니다", "ㅂ니다",
      "았어요", "었어요", "께", "드렸", "거예요", "으로", "까요", "네요", "아서", "어서", "마세요", "는데"],
  2: ["으세요", "세요", "습니다", "ㅂ니다", "았어요", "었어요", "께", "드렸", "거예요", "으로",
      "까요", "네요", "아서", "어서", "마세요", "는데"],
  3: ["부터", "으세요", "세요", "습니다", "ㅂ니다", "았어요", "었어요", "께", "드렸", "거예요",
      "으로", "까요", "네요", "아서", "어서", "마세요", "는데"],
  4: ["부터", "으세요", "세요", "습니다", "ㅂ니다", "았어요", "었어요", "께", "드렸", "거예요",
      "으로", "까요", "네요", "아서", "어서", "마세요", "는데"],
  5: ["으세요", "세요", "습니다", "ㅂ니다", "았어요", "었어요", "께", "드렸", "거예요", "으로",
      "까요", "네요", "아서", "어서", "마세요", "는데"],
  6: ["습니다", "ㅂ니다", "았어요", "었어요", "께", "드렸", "거예요", "으로", "까요", "네요",
      "아서", "어서", "마세요", "는데"],
  7: ["습니다", "ㅂ니다", "았어요", "었어요", "께", "드렸", "거예요", "으로", "까요", "네요",
      "아서", "어서", "마세요", "는데"],
  8: ["았어요", "었어요", "께", "드렸", "거예요", "으로", "까요", "네요", "아서", "어서", "마세요", "는데"],
  9: ["께", "드렸", "거예요", "으로", "까요", "네요", "아서", "어서", "마세요", "는데"],
  10: ["께", "드렸", "거예요", "으로", "까요", "네요", "아서", "어서", "마세요", "는데"],
  11: ["거예요", "으로", "까요", "네요", "아서", "어서", "마세요", "는데"],
  12: ["으로", "까요", "네요", "아서", "어서", "마세요", "는데"],
  13: ["까요", "네요", "아서", "어서", "마세요", "는데"],
  14: ["네요", "아서", "어서", "마세요", "는데"],
  15: ["아서", "어서", "마세요", "는데"],
  16: ["마세요", "는데"],
  17: ["는데"],
  18: [],
}


def scan_forward_ref():
    """대화 줄만 훑는다 — 미션은 학습자에게 거는 말(메타 지시문)이지 따라 배우는
    본문이 아니라서, '~해 보세요' 같은 표현이 늘 쓰인다(문법책 순서와 무관).
    '안녕하세요'는 문법을 분석하기 전에 통짜로 외우는 인사말이라 예외로 둔다
    (어느 한국어 교재도 1과부터 '-으세요' 규칙을 가르친 뒤에야 인사시키지 않는다)."""
    hits = []
    for d in DAYS:
        texts = [(f"L{i}", l["ko"].replace("안녕하세요", "")) for i, l in enumerate(d["dialog"]["lines"])]
        for marker in _MARKERS_AFTER.get(d["day"], []):
            for field, text in texts:
                if marker in text:
                    hits.append((d["day"], d["theme"]["ko"], field, text, marker))
    return hits


if __name__ == "__main__":
    import json, os
    n_words = sum(len(d["words"]) for d in DAYS)
    n_lines = sum(len(d["dialog"]["lines"]) for d in DAYS)
    print(f"날짜 {len(DAYS)}개 · 단어 {n_words}개 · 대화 {n_lines}줄")
    bad = scan_forward_ref()
    if bad:
        print(f"⚠ 순서 위반 의심 {len(bad)}건:")
        for day, theme, field, text, marker in bad:
            print(f"  [Day {day} {theme}] {field}='{text}' ← '{marker}'")
    else:
        print("순서 위반 없음 (자동 검사 기준)")
    out = os.path.join(os.path.dirname(__file__), "..", "data", "ko_days.json")
    json.dump({"note": "1차분: 초급1 18일 — 문법은 ko_grammar.json과 연결, 대화·미션 전부 자체 저작",
               "days": DAYS},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("저장:", out)
