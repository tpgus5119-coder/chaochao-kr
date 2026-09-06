#!/usr/bin/env python3
"""단어에 붙일 그림(지금은 이모지).

근거: 그림은 구체적인 것에만 붙일 때 도움이 된다. 추상어·문법어에 붙이면
인지부하만 올려서 오히려 해롭다(중복 정보 효과). 그래서 아래 목록에 없는
단어에는 아무것도 붙이지 않는다 — 빈칸이 정상이다.

kind: 'thing' 정지 그림으로 충분 / 'action' 나중에 짧은 영상으로 바꾸면 더 좋다
      (동작·절차는 영상이 정지 그림보다 크게 낫다, d=1.06)
"""

V = {
 # --- 사람·인사 ---
 "chào":("👋","action"), "anh":("👨","thing"), "chị":("👩","thing"),
 "em":("🧒","thing"), "bạn":("👫","thing"), "người":("🧍","thing"),
 "gặp":("🤝","action"), "vui":("😊","thing"), "cảm ơn":("🙏","action"),
 "xin lỗi":("🙇","action"), "tạm biệt":("👋","action"),
 # --- 상태 ---
 "khỏe":("💪","thing"), "mệt":("😩","thing"), "ốm":("🤒","thing"),
 # --- 나라 ---
 "nước":("🌏","thing"), "Hàn Quốc":("🇰🇷","thing"), "Việt Nam":("🇻🇳","thing"),
 "tiếng Hàn":("🇰🇷","thing"), "tiếng Việt":("🇻🇳","thing"),
 # --- 장소·이동 ---
 "sống":("🏡","thing"), "nhà":("🏠","thing"), "đây":("📍","thing"),
 "đi":("🚶","action"), "về":("🔙","action"), "mang":("📤","action"),
 # --- 말하기·듣기 ---
 "nói":("🗣️","action"), "nghe":("👂","action"), "hiểu":("💡","thing"),
 "từ từ":("🐢","action"), "lại":("🔁","action"), "hỏi":("🙋","action"),
 # --- 숫자 ---
 "một":("1️⃣","thing"), "hai":("2️⃣","thing"), "ba":("3️⃣","thing"),
 "bốn":("4️⃣","thing"), "năm":("5️⃣","thing"), "sáu":("6️⃣","thing"),
 "bảy":("7️⃣","thing"), "tám":("8️⃣","thing"), "chín":("9️⃣","thing"),
 "mười":("🔟","thing"), "tuổi":("🎂","thing"), "cái":("📦","thing"),
 # --- 시간 ---
 "giờ":("🕐","thing"), "bây giờ":("⏰","thing"), "sáng":("🌅","thing"),
 "chiều":("🌇","thing"), "mai":("📆","thing"), "hôm nay":("📅","thing"),
 "chủ nhật":("🛌","thing"), "tuần":("🗓️","thing"),
 # --- 일 ---
 "làm":("🔨","action"), "việc":("💼","thing"),
 # --- 음식 ---
 "ăn":("🍽️","action"), "cơm":("🍚","thing"),
 "uống":("🥤","action"), "ngon":("😋","thing"),
 # --- 돈 ---
 "tiền":("💵","thing"), "đắt":("💸","thing"), "rẻ":("🏷️","thing"), "mua":("🛒","action"),
 # --- 부탁·약속 ---
 "giúp":("🆘","action"), "nhớ":("🧠","thing"), "quên":("💨","action"),
 "đừng":("🚫","thing"), "hứa":("🤞","action"),

 # --- 2차 추가 (단어 200개 확장분) ---
 "thành phố":("🏙️","thing"), "chợ":("🏪","thing"), "đường":("🛣️","thing"),
 "nhà vệ sinh":("🚻","thing"), "bệnh viện":("🏥","thing"), "thuốc":("💊","thing"),
 "phở":("🍜","thing"), "cà phê":("☕","thing"), "đói":("😣","thing"), "no":("😌","thing"),
 "thích":("❤️","thing"), "muốn":("💭","thing"),
 "gia đình":("👨‍👩‍👧","thing"), "bố":("👨","thing"), "mẹ":("👩","thing"),
 "con trai":("👦","thing"), "em gái":("👧","thing"), "vợ":("👰","thing"), "chồng":("🤵","thing"),
 "tay":("🤚","thing"), "chân":("🦵","thing"), "đầu":("🤯","thing"), "đau":("🤕","thing"),
 "bị":("💥","thing"), "cảm":("🤧","thing"),
 "trên":("⬆️","thing"), "dưới":("⬇️","thing"), "trong":("📥","thing"), "ngoài":("📤","thing"),
 "bên cạnh":("↔️","thing"), "gần":("🔍","thing"), "xa":("🔭","thing"),
 "mở":("🔓","action"), "đóng":("🔒","action"), "đợi":("⏳","action"),
 "tốt":("👍","thing"), "xấu":("👎","thing"), "đẹp":("✨","thing"), "hay":("🎉","thing"),
 "khó":("🧗","thing"), "dễ":("🛝","thing"), "mới":("🆕","thing"), "cũ":("🕰️","thing"),
 "nhiều":("🗄️","thing"), "ít":("🤏","thing"),
 "dậy":("⏰","action"), "nghỉ":("😴","action"), "muộn":("🐌","thing"),
 "bắt đầu":("▶️","action"), "kết thúc":("⏹️","action"),
 "phút":("⏱️","thing"), "rưỡi":("🕧","thing"), "tối":("🌙","thing"), "hôm qua":("⏪","thing"),
 "bán":("🏷️","action"), "nghìn":("🔢","thing"), "đồng":("💴","thing"),
 "hộp":("🎁","thing"), "thùng":("📦","thing"), "chiếc":("🚲","thing"), "con":("🐕","thing"),
 "thứ hai":("1️⃣","thing"), "chủ nhật":("🛌","thing"),
 "xong":("✅","action"), "chưa":("⏳","thing"), "cùng":("🤝","action"),
 "quan trọng":("❗","thing"), "chắc chắn":("✔️","thing"),
}

# 3차 추가 (직무·확장 과정 구체어 432개) — 손으로 안 쓰고 imgnew.json에서 읽는다
import json as _json, pathlib as _pl
_extra = _pl.Path(__file__).parent / 'imgnew.json'
if _extra.exists():
    for _vi, _e in _json.loads(_extra.read_text()).items():
        V.setdefault(_vi, (_e['emoji'], _e['kind']))

def attach(word):
    hit = V.get(word["vi"])
    if hit:
        word["emoji"], word["vkind"] = hit
    return word

if __name__ == '__main__':
    import json
    d = json.load(open('data/days.json'))
    ws = [w for x in d['days'] for w in x['words']]
    have = [w for w in ws if w['vi'] in V]
    act = [w['vi'] for w in have if V[w['vi']][1] == 'action']
    print(f"단어 {len(ws)}개 중 그림 붙는 것 {len(have)}개 ({len(have)*100//len(ws)}%)")
    print(f"그중 나중에 영상으로 바꾸면 좋은 것 {len(act)}개:")
    print("  " + ", ".join(act))
    print(f"\n아무것도 안 붙는 추상어 {len(ws)-len(have)}개 — 의도한 것이다")
