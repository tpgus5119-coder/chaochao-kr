# -*- coding: utf-8 -*-
"""나머지 업종 낱말 — 신발·가방 / 자동차·기계 / 건설·플랜트 / 물류·무역 / 식품·화학 / 요식·유통.
   한국인이 실제로 취업하는 자리 기준 (KOTRA 2023: 제조업 1위 > 물류 > 요식 > 건설 > IT).
   신발은 태광비나·창신·화승 같은 나이키 OEM 이 베트남 남부에 몰려 있어 따로 두었다.
   확인한 곳: fttleather.com(đế khâu/đế dán) · zim.vn 신발 용어 · 무역 용어는 tools/trade_words.py 참고."""

SHOE = [
 ("giày", "신발"), ("giày thể thao", "운동화"), ("giày da", "구두"), ("dép", "슬리퍼"),
 ("xăng đan", "샌들"), ("ủng", "장화"), ("túi xách", "가방"), ("ba lô", "배낭"),
 ("ví", "지갑"), ("dây đeo", "끈·스트랩"),
 ("mũ giày", "갑피"), ("đế giày", "밑창"), ("đế ngoài", "아웃솔"), ("đế giữa", "미드솔"),
 ("lót giày", "인솔·깔창"), ("lưỡi gà", "설포"), ("dây giày", "신발끈"), ("lỗ xỏ dây", "끈 구멍"),
 ("gót giày", "뒷굽"), ("mũi giày", "앞코"), ("phom giày", "라스트(신발 골)"),
 ("da thật", "천연가죽"), ("da tổng hợp", "합성피혁"), ("vải lưới", "메시 원단"),
 ("cao su", "고무"), ("nhựa EVA", "EVA 폼"),
 ("ép đế", "밑창 압착"), ("dán đế", "밑창 접착"), ("khâu đế", "밑창 봉합"),
 ("keo dán", "접착제"), ("bôi keo", "본드 칠하기"), ("mài nhám", "표면 거칠게 하기"),
 ("sấy keo", "본드 건조"), ("gò giày", "라스팅"), ("dập khuôn", "금형 성형"),
 ("cắt da", "가죽 재단"), ("may mũ giày", "갑피 봉제"), ("in logo", "로고 인쇄"),
 ("kiểm tra đôi", "짝 검사"), ("lệch đôi", "짝 불일치"), ("bong keo", "본드 벗겨짐"),
 ("hở keo", "본드 들뜸"), ("cỡ giày", "신발 치수"), ("đóng hộp giày", "신발 박스 포장"),
]

MACH = [
 ("khuôn", "금형"), ("khuôn ép", "프레스 금형"), ("máy ép", "프레스"), ("máy tiện", "선반"),
 ("máy phay", "밀링"), ("máy khoan", "드릴링기"), ("máy cắt", "절단기"), ("máy hàn", "용접기"),
 ("hàn hồ quang", "아크 용접"), ("mài", "연마하다"), ("tiện", "선반 가공하다"),
 ("đúc", "주조하다"), ("ép nhựa", "사출 성형"), ("mạ", "도금하다"), ("sơn tĩnh điện", "분체 도장"),
 ("vòng bi", "베어링"), ("động cơ", "모터"), ("bơm", "펌프"), ("van", "밸브"),
 ("xi lanh", "실린더"), ("thủy lực", "유압"), ("khí nén", "공압"), ("dầu bôi trơn", "윤활유"),
 ("dây curoa", "벨트"), ("bánh răng", "기어"), ("trục", "축"), ("ốc vít", "나사"),
 ("bu lông", "볼트"), ("đai ốc", "너트"), ("long đen", "와셔"),
 ("bản vẽ", "도면"), ("dung sai", "공차"), ("thước cặp", "버니어 캘리퍼스"),
 ("thước đo", "자·측정기"), ("cân chỉnh", "정렬하다"), ("siết chặt", "단단히 조이다"),
 ("nới lỏng", "느슨하게 풀다"), ("phụ tùng", "예비 부품"), ("linh kiện thay thế", "교체 부품"),
 ("phụ tùng ô tô", "자동차 부품"), ("dây chuyền lắp ráp", "조립 라인"),
]

CONS = [
 ("công trường", "공사 현장"), ("công trình", "공사·건축물"), ("thi công", "시공하다"),
 ("thiết kế", "설계하다"), ("bản vẽ thiết kế", "설계도"), ("giám sát", "감리하다"),
 ("nghiệm thu", "준공 검사"), ("thầu phụ", "하도급"), ("nhà thầu", "시공사"),
 ("chủ đầu tư", "발주처"), ("tiến độ", "공정률"), ("hồ sơ thi công", "시공 서류"),
 ("bê tông", "콘크리트"), ("cốt thép", "철근"), ("xi măng", "시멘트"), ("gạch", "벽돌"),
 ("cát", "모래"), ("sỏi", "자갈"), ("giàn giáo", "비계"), ("cẩu", "크레인"),
 ("máy xúc", "굴착기"), ("máy trộn", "믹서"), ("đổ bê tông", "콘크리트 타설"),
 ("đào móng", "기초 굴착"), ("san lấp", "성토·정지"), ("lắp dựng", "설치·조립"),
 ("đường ống", "배관"), ("hệ thống điện", "전기 설비"), ("hệ thống nước", "급배수"),
 ("thông gió", "환기"), ("cách nhiệt", "단열"), ("chống thấm", "방수"),
 ("mũ bảo hộ", "안전모"), ("dây an toàn", "안전벨트"), ("lưới an toàn", "안전망"),
 ("biển cảnh báo", "경고 표지판"), ("khu vực nguy hiểm", "위험 구역"),
]

LOGI = [
 ("kho hàng", "창고"), ("nhập kho", "입고하다"), ("xuất kho", "출고하다"),
 ("kiểm kê", "재고 조사"), ("tồn kho", "재고"), ("phiếu xuất kho", "출고 전표"),
 ("phiếu nhập kho", "입고 전표"), ("xe nâng", "지게차"), ("pa lét", "팔레트"),
 ("thùng carton", "골판지 상자"), ("băng keo", "포장 테이프"), ("màng quấn", "랩 필름"),
 ("bốc xếp", "상하차"), ("chất hàng", "적재하다"), ("dỡ hàng", "하역하다"),
 ("xe tải", "트럭"), ("xe container", "컨테이너 차"), ("tàu biển", "선박"),
 ("máy bay chở hàng", "화물기"), ("cảng biển", "항구"), ("sân bay hàng hoá", "화물 공항"),
 ("giao hàng", "납품하다"), ("nhận hàng", "인수하다"), ("giao đúng hạn", "납기 준수"),
 ("trễ hàng", "납기 지연"), ("thiếu hàng", "물량 부족"), ("hàng lỗi trả về", "반품"),
 ("vận chuyển nội địa", "내륙 운송"), ("phí vận chuyển", "운송비"), ("bảo hiểm hàng hoá", "화물 보험"),
]

FOOD = [
 ("nguyên liệu thực phẩm", "식품 원료"), ("phụ gia", "첨가물"), ("bảo quản lạnh", "냉장 보관"),
 ("cấp đông", "급속 냉동"), ("rã đông", "해동하다"), ("tiệt trùng", "살균하다"),
 ("lên men", "발효하다"), ("trộn", "배합하다"), ("nhào bột", "반죽하다"), ("sấy khô", "건조하다"),
 ("đóng gói chân không", "진공 포장"), ("hạn sử dụng", "유통기한"), ("nhãn dinh dưỡng", "영양 표시"),
 ("vệ sinh an toàn thực phẩm", "식품 위생"), ("khử trùng", "소독하다"),
]

# 화학·플라스틱 — 식품과는 다른 업종이다 (효성·LG화학·롯데케미칼)
CHEM = [
 ("hoá chất","화학 약품"),("dung dịch","용액"),("nồng độ","농도"),("pha loãng","희석하다"),
 ("trung hoà","중화하다"),("nước thải","폐수"),("khí thải","배기가스"),("chất độc hại","유해물질"),
 ("bình chứa","저장 탱크"),("van an toàn","안전 밸브"),("nhựa nguyên sinh","신재 수지"),
 ("hạt nhựa","플라스틱 펠릿"),("ép phun","사출 성형"),("đùn nhựa","압출"),("khuôn nhựa","사출 금형"),
 ("nhiệt độ nóng chảy","용융 온도"),("áp suất phun","사출 압력"),("thời gian làm nguội","냉각 시간"),
 ("chất phụ gia","첨가제"),("chất tạo màu","착색제"),("xúc tác","촉매"),("lò phản ứng","반응기"),
 ("chưng cất","증류"),("tinh chế","정제"),("độ nhớt","점도"),("đóng rắn","경화"),
 ("bồn chứa","저장조"),("đường ống dẫn","배관"),("bơm hoá chất","약품 펌프"),
 ("phòng thí nghiệm hoá","화학 실험실"),("mẫu phân tích","분석 시료"),("khu vực nguy hiểm cháy","화기 위험 구역"),
]

SHOP = [
 ("cửa hàng", "매장"), ("siêu thị", "마트"), ("cửa hàng tiện lợi", "편의점"),
 ("quầy thu ngân", "계산대"), ("kệ hàng", "진열대"), ("trưng bày", "진열하다"),
 ("khuyến mãi", "판촉·할인 행사"), ("giảm giá", "할인하다"), ("hoá đơn bán hàng", "판매 영수증"),
 ("khách quen", "단골"), ("phục vụ khách", "고객 응대"), ("khiếu nại", "고객 불만"),
 ("đổi trả", "교환·반품"), ("doanh số", "매출액"), ("kiểm hàng", "상품 점검"),
 ("nhà bếp", "주방"), ("đầu bếp", "요리사"), ("phục vụ bàn", "홀 서빙"),
 ("thực đơn", "메뉴판"), ("gọi món", "주문하다"), ("mang đi", "포장 판매"),
 ("giao đồ ăn", "음식 배달"), ("đặt bàn", "자리 예약"), ("hoá đơn", "계산서"),
 ("tiền tip", "팁"), ("vệ sinh bếp", "주방 위생"),
]



# ── 더 채운 것 (2026-08-30) — 갈래마다 900을 채우려면 이만큼은 있어야 한다
SHOE += [
 ("nhà máy giày","신발 공장"),("chuyền may mũ","갑피 봉제 라인"),("chuyền gò","라스팅 라인"),
 ("chuyền đế","밑창 라인"),("kho phom","라스트 창고"),("mẫu giày","신발 견본"),
 ("bảng màu","컬러 차트"),("cỡ mẫu","기준 사이즈"),("bộ cỡ","사이즈 세트"),("nhảy cỡ","사이즈 그레이딩"),
 ("cắt bằng dao chặt","재단 칼 절단"),("cắt tự động","자동 재단"),("bồi vải","원단 합포"),
 ("in chuyển nhiệt","열전사 인쇄"),("thêu logo","로고 자수"),("đục lỗ","타공"),
 ("tán khuy","아일릿 박기"),("may lộn","뒤집어 박기"),("may diễu","눌러 박기"),
 ("xử lý nhiệt","열처리"),("làm nguội","냉각"),("kiểm tra keo","접착 검사"),
 ("thử độ bám","접착력 시험"),("thử độ mài mòn","마모 시험"),("thử uốn gập","굴곡 시험"),
 ("giày lỗi","불량 신발"),("bẩn keo","본드 오염"),("lệch logo","로고 삐뚤어짐"),
 ("nhăn mũ giày","갑피 주름"),("hộp giày","신발 상자"),("giấy nhồi","충전지"),
 ("túi hút ẩm","방습제"),("đôi giày","신발 한 켤레"),("chiếc giày","신발 한 짝"),
 ("trái phải","좌우"),("dán mã cỡ","사이즈 라벨 부착"),
]
MACH += [
 ("gia công cơ khí","기계 가공"),("gia công chính xác","정밀 가공"),("máy CNC","CNC 기계"),
 ("chương trình gia công","가공 프로그램"),("dao cắt","절삭 공구"),("mũi khoan","드릴 비트"),
 ("tốc độ quay","회전 속도"),("bước tiến","이송 속도"),("dung dịch làm mát","절삭유"),
 ("phoi","칩·절삭 부스러기"),("bavia","버(거스러미)"),("gọt bavia","버 제거"),
 ("độ nhám bề mặt","표면 거칠기"),("độ cứng","경도"),("nhiệt luyện","열처리"),
 ("tôi thép","담금질"),("ram","뜨임"),("kiểm tra không phá huỷ","비파괴 검사"),
 ("thép không gỉ","스테인리스"),("nhôm","알루미늄"),("đồng","구리"),("tôn","철판"),
 ("hàn TIG","티그 용접"),("hàn MIG","미그 용접"),("que hàn","용접봉"),("mối hàn đẹp","용접 비드"),
 ("biến dạng","변형"),("cong vênh","휨"),("lắp lẫn","호환 조립"),("kẹp chặt","클램핑"),
 ("đồ gá","지그"),("bàn máp","정반"),("đồng hồ so","다이얼 게이지"),("panme","마이크로미터"),
]
CONS += [
 ("giấy phép xây dựng","건축 허가"),("mặt bằng thi công","현장 배치도"),("tiến độ thi công","공정표"),
 ("nhật ký công trình","공사 일지"),("biên bản nghiệm thu","검사 조서"),("bàn giao công trình","준공 인계"),
 ("bảo hành công trình","하자 보수"),("phát sinh","추가 공사"),("dự toán","공사비 산출"),
 ("khối lượng thi công","시공 물량"),("vật liệu xây dựng","건설 자재"),("thép hình","형강"),
 ("ván khuôn","거푸집"),("cột","기둥"),("dầm","보"),("sàn","슬래브"),("móng","기초"),
 ("tường","벽체"),("mái","지붕"),("trát vữa","미장"),("ốp lát","타일 시공"),("sơn nước","도장"),
 ("hàn kết cấu","철골 용접"),("lắp cốp pha","거푸집 설치"),("tháo cốp pha","거푸집 해체"),
 ("đầm bê tông","콘크리트 다짐"),("bảo dưỡng bê tông","콘크리트 양생"),("máy phát điện","발전기"),
 ("máy nén khí","컴프레서"),("xe ben","덤프트럭"),("xe trộn bê tông","레미콘"),
]
LOGI += [
 ("vận đơn đường biển","해상 선하증권"),("vận đơn hàng không","항공 운송장"),("tờ khai xuất","수출 신고"),
 ("tờ khai nhập","수입 신고"),("kiểm hoá","세관 검사"),("thông quan điện tử","전자 통관"),
 ("mã HS hàng hoá","품목 HS 코드"),("xuất xứ hàng hoá","물품 원산지"),("giấy phép nhập khẩu","수입 허가"),
 ("hàng mẫu","견본품"),("hàng phi mậu dịch","비무역 물품"),("kho ngoại quan","보세창고"),
 ("hàng quá cảnh","통과 화물"),("đóng container","컨테이너 적입"),("niêm phong","실링·봉인"),
 ("cân hàng","화물 계량"),("trọng lượng tịnh","순중량"),("trọng lượng cả bì","총중량"),
 ("kích thước kiện","포장 치수"),("số kiện","포장 개수"),("lịch tàu","선박 스케줄"),
 ("đặt chỗ tàu","선복 예약"),("hàng về cảng","항구 도착"),("lấy hàng","화물 반출"),
 ("phí lưu kho","보관료"),("phí lưu container","컨테이너 체선료"),("giao hàng tận nơi","문전 배송"),
 ("theo dõi đơn hàng","배송 추적"),("bảng kê hàng hoá","포장 명세서"),
]
FOOD += [
 ("dây chuyền chế biến","가공 라인"),("phòng chế biến","가공실"),("nguyên liệu tươi","신선 원료"),
 ("rửa nguyên liệu","원료 세척"),("sơ chế","전처리"),("cắt gọt","절단·손질"),("gia nhiệt","가열"),
 ("làm nguội nhanh","급속 냉각"),("kho lạnh","냉동 창고"),("nhiệt độ bảo quản","보관 온도"),
 ("giám sát nhiệt độ","온도 관리"),("HACCP","해썹(식품안전관리)"),("truy xuất lô","로트 추적"),
 ("dị vật","이물"),("kim loại lẫn","금속 혼입"),("máy dò kim loại","금속 검출기"),
 ("cân định lượng","정량 계량"),("bao bì thực phẩm","식품 포장재"),("in hạn dùng","유통기한 인쇄"),
 ("kiểm nghiệm","시험 분석"),("phòng thí nghiệm","시험실"),("mẫu lưu","보관 시료"),
 ("găng tay dùng một lần","일회용 장갑"),("khẩu trang","마스크"),("ủng cao su","고무 장화"),
]
SHOP += [
 ("nhập hàng về","상품 입고"),("kiểm hàng nhập","입고 검수"),("dán giá","가격표 부착"),
 ("thay giá","가격 변경"),("hàng cận hạn","유통기한 임박 상품"),("hàng hết hạn","기한 만료 상품"),
 ("kiểm kê hàng","재고 실사"),("hao hụt hàng","상품 로스"),("mất cắp","도난"),
 ("camera an ninh","보안 카메라"),("máy quét mã","바코드 스캐너"),("máy POS","포스 단말기"),
 ("thanh toán thẻ","카드 결제"),("thanh toán QR","QR 결제"),("tiền lẻ","잔돈"),
 ("mở ca","오픈 준비"),("đóng ca","마감"),("kết ca","시재 정산"),("báo cáo doanh thu","매출 보고"),
 ("khu vực ăn uống","식음 구역"),("bàn ghế","테이블과 의자"),("dụng cụ bếp","주방 도구"),
 ("nguyên liệu nấu","조리 재료"),("chuẩn bị nguyên liệu","재료 준비"),("nêm nếm","간 맞추기"),
 ("trình bày món","플레이팅"),("thời gian chờ món","대기 시간"),("phản hồi khách","고객 피드백"),
]

# 요식과 유통도 다른 업종이다 — 갈라 둔다
REST = [w for w in SHOP if any(k in w[1] for k in
        ("주방","요리사","서빙","메뉴","주문","포장 판매","배달","자리 예약","계산서","팁",
         "식음","테이블","조리","재료","간 맞추","플레이팅","대기 시간","피드백"))]
RETAIL = [w for w in SHOP if w not in REST]

TRACKS = [("전자·반도체", None), ("섬유·봉제·신발", SHOE), ("기계·금속·자동차", MACH),
          ("건설", CONS), ("물류·무역", LOGI), ("식품", FOOD), ("화학·플라스틱", CHEM),
          ("요식", REST), ("유통·판매", RETAIL)]
