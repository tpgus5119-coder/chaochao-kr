#!/usr/bin/env python3
"""그림 생성 프롬프트 문서(docs/image-prompts.md)를 만든다.
파일명은 days.json 의 img 값과 1:1 — 어긋나면 앱이 그림을 못 찾으므로 여기서 검증한다."""
import json, sys

STYLE = "simple flat illustration, soft pastel colors, thick outlines, plain white background, no text, no letters"

# 파일명(.webp 뺀 것) → 그릴 것. 구체어에만 그림이 붙는다.
EN = {
 # Day 1 인사와 호칭
 "d01-scene":"two coworkers waving hello to each other in a hallway",
 "d01-chao":"a smiling person waving hello",
 "d01-anh":"a young man",
 "d01-chi":"a young woman",
 "d01-em":"a younger person, small and cheerful",
 "d01-ban":"two friends of the same age standing side by side",
 "d01-cam-on":"a person bowing slightly with both hands together in thanks",
 # Day 2 이름
 "d02-scene":"two people introducing themselves, both wearing blank name tags",
 "d02-nguoi":"a single standing person",
 "d02-xin-loi":"a person bowing deeply in apology",
 "d02-vui":"a happy person jumping with joy",
 # Day 3 나라·사는 곳
 "d03-scene":"two people talking in front of a large globe",
 "d03-nuoc":"a globe showing continents",
 "d03-han-quoc":"the flag of South Korea on a flagpole",
 "d03-viet-nam":"the flag of Vietnam on a flagpole",
 "d03-song":"a cozy house with a person standing at the door",
 "d03-day":"a red map pin marking a spot on the ground",
 "d03-thanh-pho":"a city skyline with tall buildings",
 # Day 4 안부
 "d04-scene":"two people meeting and shaking hands warmly",
 "d04-gap":"two people shaking hands",
 "d04-khoe":"a strong arm flexing its biceps",
 "d04-met":"a tired person slumped over with drooping shoulders",
 "d04-hom-nay":"a desk calendar with today circled in red",
 # Day 5 못 알아들음
 "d05-scene":"one person confused with question marks above the head, the other speaking slowly",
 "d05-hieu":"a bright lightbulb glowing above a person's head",
 "d05-noi":"a person speaking with a speech bubble",
 "d05-nghe":"a person cupping a hand behind the ear to listen",
 "d05-lai":"a circular repeat arrow going around",
 "d05-tu-tu":"a turtle walking slowly",
 "d05-tieng-viet":"a speech bubble colored like the Vietnamese flag",
 "d05-tieng-han":"a speech bubble colored like the South Korean flag",
 # Day 6 작별
 "d06-scene":"two people waving goodbye at a doorway in the evening",
 "d06-tam-biet":"a person waving goodbye with a big arm wave",
 "d06-mai":"a calendar page with a rising sun, meaning tomorrow",
 "d06-di":"a person walking away",
 "d06-ve":"a person walking back toward a house, arrow pointing home",
 "d06-nha":"a simple house with a red roof",
 # Day 7 숫자 1~10
 "d07-scene":"two people counting red apples on a table",
 "d07-mot":"one red apple",
 "d07-hai":"two red apples in a row",
 "d07-ba":"three red apples in a row",
 "d07-bon":"four red apples in a row",
 "d07-nam":"five red apples in a row",
 "d07-sau":"six red apples in two rows of three",
 "d07-bay":"seven red apples in two rows",
 "d07-tam":"eight red apples in two rows of four",
 "d07-chin":"nine red apples in three rows of three",
 "d07-muoi":"ten red apples in two rows of five",
 # Day 8 개수 세기
 "d08-scene":"two warehouse workers counting cardboard boxes",
 "d08-cai":"one simple cup on a table",
 "d08-chiec":"one motorbike",
 "d08-con":"one small dog",
 "d08-hop":"a small carton box",
 "d08-thung":"a large cardboard box",
 # Day 9 나이·시간
 "d09-scene":"one person pointing at a wall clock, the other holding a birthday cake",
 "d09-tuoi":"a birthday cake with lit candles",
 "d09-gio":"a round wall clock",
 "d09-phut":"a stopwatch",
 "d09-bay-gio":"an alarm clock ringing right now",
 "d09-ruoi":"a clock showing half past nine",
 "d09-sang":"a sunrise over hills",
 "d09-chieu":"an afternoon sun low in the sky",
 "d09-toi":"a night sky with moon and stars",
 # Day 10 요일
 "d10-scene":"two people looking at a big wall calendar together",
 "d10-thu-hai":"a weekly calendar with the first weekday circled",
 "d10-chu-nhat":"a weekly calendar with the red sunday column circled",
 "d10-hom-qua":"a calendar with an arrow pointing back one day",
 "d10-tuan":"a strip of seven calendar days in a row",
 # Day 11 하루 일과
 "d11-scene":"one person stretching awake in bed, a clock and sunrise outside the window",
 "d11-day":"a person stretching arms wide, waking up in bed",
 "d11-bat-dau":"a runner crouched at a starting line",
 "d11-ket-thuc":"a runner crossing a finish line with a checkered flag",
 "d11-lam":"a person hammering at a workbench",
 "d11-viec":"a desk with documents and a laptop",
 "d11-nghi":"a person resting on a sofa with a cup of tea",
 "d11-muon":"a person running in a hurry, a big clock behind",
 # Day 12 먹고 마시기
 "d12-scene":"two people happily eating noodle soup together at a restaurant table",
 "d12-an":"a person eating a bowl of rice with chopsticks",
 "d12-uong":"a person drinking a glass of water",
 "d12-com":"a bowl of steamed white rice",
 "d12-pho":"a bowl of vietnamese pho noodle soup with chopsticks lifting noodles",
 "d12-muon":"a person gazing at a dream in a thought bubble with a star inside",
 "d12-ca-phe":"a glass of vietnamese iced coffee with a metal drip filter on top",
 "d12-ngon":"a person delighted by a steaming delicious dish with sparkles",
 "d12-doi":"a hungry person holding an empty plate, stomach growling",
 "d12-no":"a person patting a full belly, satisfied",
 "d12-thich":"a person hugging a big heart",
 # Day 13 사고 팔기
 "d13-scene":"a buyer and a market vendor bargaining over fruit at a stall",
 "d13-tien":"banknotes and coins",
 "d13-dat":"a diamond with a big price tag and an arrow pointing up",
 "d13-re":"a discount price tag with an arrow pointing down",
 "d13-mua":"a person handing money and receiving a shopping bag",
 "d13-ban":"a vendor handing goods over a counter",
 "d13-nghin":"a tall pile of gold coins",
 "d13-dong":"a single shiny copper coin",
 # Day 14 위치
 "d14-scene":"one person asking directions, the other pointing down the road",
 "d14-tren":"a cat sitting on top of a box",
 "d14-duoi":"a cat sitting under a table",
 "d14-trong":"a cat inside an open box",
 "d14-ngoai":"a cat standing outside next to a closed box",
 "d14-ben-canh":"a cat sitting right beside a box",
 "d14-gan":"two houses standing very close together",
 "d14-xa":"two tiny houses far apart on distant hills",
 "d14-duong":"a road stretching toward the horizon",
 "d14-cho":"an open-air market stall full of fruit",
 "d14-nha-ve-sinh":"a restroom door with a toilet visible inside",
 # Day 15 가족
 "d15-scene":"a person showing a framed family photo to a friend",
 "d15-gia-dinh":"a family of four holding hands",
 "d15-bo":"a kind father figure",
 "d15-me":"a kind mother figure",
 "d15-con-trai":"a little boy",
 "d15-vo":"a wife showing a wedding ring",
 "d15-chong":"a husband showing a wedding ring",
 "d15-em-gai":"a little girl",
 # Day 16 아플 때
 "d16-scene":"a friend handing medicine to a sick person lying in bed",
 "d16-bi":"a person standing under a small personal rain cloud",
 "d16-dau":"a person wincing and holding an aching arm, pain marks around it",
 "d16-om":"a sick person in bed with a thermometer in the mouth",
 "d16-benh-vien":"a hospital building with a red cross sign",
 "d16-thuoc":"a medicine bottle and a few pills",
 "d16-dau2":"a simple human head",
 "d16-tay":"an open hand and arm",
 "d16-chan":"a leg and foot",
 "d16-cam":"a person sneezing into a tissue, catching a cold",
 # Day 17 부탁
 "d17-scene":"one person reaching out a helping hand to another who asks for help",
 "d17-giup":"a helping hand pulling someone up",
 "d17-hoi":"a person raising a hand with a question mark above",
 "d17-dung":"a red prohibition circle with a slash",
 "d17-mo":"a hand opening a door",
 "d17-dong":"a hand closing a door shut",
 "d17-doi":"a person sitting on a bench waiting, looking at a watch",
 # Day 18 평가
 "d18-scene":"two people chatting happily, both giving a thumbs up",
 "d18-tot":"a big thumbs up",
 "d18-xau":"a big thumbs down",
 "d18-dep":"a beautiful blooming flower with sparkles",
 "d18-hay":"a person laughing and clapping with delight",
 "d18-kho":"a person straining to push a huge boulder",
 "d18-de":"a person easily lifting a single feather with one finger",
 "d18-moi":"a brand-new sparkling sneaker",
 "d18-cu":"an old worn-out patched shoe",
 "d18-nhieu":"a huge pile of many apples",
 "d18-it":"just two apples alone on a big empty table",
 # Day 19 시제
 "d19-scene":"one person still eating a meal while the other points at a wristwatch",
 "d19-chua":"an hourglass still running, sand halfway",
 "d19-xong":"a big green check mark",
 "d19-cung":"two people walking together side by side",
 # Day 20 약속
 "d20-scene":"two people making a pinky promise",
 "d20-nho":"a person with a photo of a friend inside a thought bubble",
 "d20-quen":"a person scratching the head, an empty thought bubble with a question mark",
 "d20-hua":"two hands making a pinky promise",
 "d20-chac-chan":"a shield with a check mark",
 "d20-quan-trong":"a gold star with a red exclamation mark",
 # 직무 파트 (Day 21~30) — 장면만 (단어 그림은 추후)
 "d21-scene":"a new worker greeting colleagues at a garment factory entrance",
 "d22-scene":"a sewing workshop table with fabric, thread, needles and scissors",
 "d23-scene":"two workers examining parts of a shirt on a table",
 "d24-scene":"a worker sewing at a sewing machine while another irons a shirt",
 "d25-scene":"a quality inspector checking a garment and pointing at a stitch",
 "d26-scene":"workers counting stacked boxes of clothes in a warehouse",
 "d27-scene":"a supervisor showing safety gloves and a mask to a worker",
 "d28-scene":"a senior worker demonstrating a task while a trainee watches",
 "d29-scene":"a worker looking at a stopped conveyor machine with warning light",
 "d30-scene":"a worker politely talking to a team leader at an office desk",
 "d31-scene":"a worker examining uneven stitches on fabric under a lamp",
 "d32-scene":"workers spreading fabric layers on a long cutting table",
 "d33-scene":"boxes of labels, zippers and sewing accessories on shelves",
 "d34-scene":"an inspector marking defects on a garment with red tags",
 "d35-scene":"a worker counting boxes and writing numbers on a clipboard",
 "d36-scene":"workers folding shirts and packing them into plastic bags",
 "d37-scene":"workers eating lunch together at a factory canteen",
 "d38-scene":"a person receiving a pay envelope and smiling at a bank book",
 "d39-scene":"a worker pointing directions in a factory corridor",
 "d40-scene":"a worker talking on the phone while noting a message",
 "d61-scene":"a worker in uniform with id badge checking a rules board",
 "d62-scene":"two coworkers helping each other carry a box, smiling",
 "d63-scene":"coworkers toasting glasses at a company dinner party",
 "d64-scene":"a worker politely asking a manager while holding a calendar",
 "d65-scene":"a worker bowing slightly in apology, supervisor waving it off kindly",
 "d66-scene":"two people reviewing a contract document with a pen",
 "d67-scene":"a person reading a payslip with a calculator",
 "d68-scene":"a person at an immigration counter with passport and photos",
 "d69-scene":"a nurse guiding a worker at a company clinic",
 "d70-scene":"a person reporting a lost wallet at a police desk",
 "d71-scene":"two coworkers chatting about hometowns over a map of vietnam",
 "d73-scene":"friends cheering at a football match on tv with vietnam flags",
 "d74-scene":"two people chatting happily on monday morning at lockers",
 "d75-scene":"coworkers clapping and giving thumbs up to a shy colleague",
 "d76-scene":"a vietnamese cafe with iced milk coffee and tea glasses",
 "d77-scene":"a steaming bowl of pho with herbs, lime and chili on the side",
 "d78-scene":"a phone shop clerk handing a sim card to a customer",
 "d80-scene":"a delivery rider checking an address in a narrow alley",
 "d81-scene":"a team leader explaining steps one by one to a worker",
 "d82-scene":"a manager checking progress on a clipboard beside a line",
 "d83-scene":"a manager talking privately and kindly with one worker aside",
 "d84-scene":"a manager praising a smiling worker in front of the team",
 "d85-scene":"a short morning meeting with raised hands and a whiteboard",
 "d88-scene":"sorted garment piles with green pass and red fail tags",
 "d89-scene":"a worker unpicking stitches and replacing a button",
 "d90-scene":"a worker reading an illustrated work-standard sheet",
 "d91-scene":"a worker soldering a chip on a circuit board with smoke wisps",
 "d92-scene":"an inspection machine booting up with data on screen",
 "d93-scene":"a cracked phone screen with an error code displayed",
 "d94-scene":"a thermometer and hygrometer on a cleanroom wall",
 "d95-scene":"sealed boxes on a pallet being checked against a list",
 "d96-scene":"a forklift reversing with warning light while workers step aside",
 "d97-scene":"warehouse shelves with labeled bins and a receiving slip",
 "d100-scene":"a courier and receiver signing a delivery report over a damaged box",
 # 일상 확장 + 전자·사무 — 장면만
 "d41-scene":"two people talking about weather, one holding an umbrella, rain outside",
 "d42-scene":"a person waiting at a bus stop, motorbikes passing by",
 "d43-scene":"two workers choosing fabric colors from colorful rolls",
 "d44-scene":"a coworker comforting a homesick friend on a bench",
 "d45-scene":"friends playing football in a park on a sunny day",
 "d46-scene":"a person doing laundry and cleaning a small room",
 "d47-scene":"a pharmacist handing medicine to a person with a scarf",
 "d48-scene":"friends toasting with drinks at a small restaurant table",
 "d49-scene":"people celebrating with gifts and red envelopes at Tet",
 "d50-scene":"a newcomer with a passport and suitcase in a vietnamese street",
 "d51-scene":"a worker examining electronic parts on a workbench",
 "d52-scene":"a worker assembling a device with a screwdriver on a line",
 "d53-scene":"workers in cleanroom suits and caps entering a clean room",
 "d55-scene":"a supervisor pointing at a production dashboard beside a conveyor",
 "d56-scene":"an office desk with a computer, printer and documents",
 "d57-scene":"a staff member serving a customer at a shop counter",
 "d59-scene":"a traveler with a suitcase at an airport departure board",
 "d60-scene":"a person exchanging money at a bank counter",
 "d101-scene":"two coworkers chatting, one pointing at a factory and the other at an office building",
 "d102-scene":"a shopper and a vendor counting banknotes and coins at a market stall",
 "d104-scene":"a fruit stall with bananas, mangoes and watermelons on display, a vendor weighing fruit",
 "d106-scene":"a shopper with a basket choosing vegetables at a busy market stall",
}

d = json.load(open('data/days.json'))
EXTRA = {}                             # 워크플로로 저작한 확장분 (vi 키로 합류, imgrest는 p에 화풍 꼬리 포함)
for _f in ('tools/imgnew.json', 'tools/imgrest.json'):
    try: EXTRA.update(json.load(open(_f)))
    except FileNotFoundError: pass
for day in d['days']:
    for w in day['words']:
        e = EXTRA.get(w.get('vi'))
        if 'img' in w and e:
            p = e.get('en') or e.get('p', '')
            if p:
                EN.setdefault(w['img'][:-5], p.split(', simple flat')[0])

need, rows = [], []
for day in d['days']:
    items = [(day['dialog']['img'], '오늘의 대화 — ' + day['dialog']['title'])]
    items += [(w['img'], f"{w['ko']} ({w['vi']})") for w in day['words'] if 'img' in w]
    rows.append((day['day'], day['theme'], items))
    need += [f[:-5] for f, _ in items]

miss = [k for k in need if k not in EN]
extra = [k for k in EN if k not in need]
if miss or extra:
    print("어긋남! 없음:", miss, "/ 남음:", extra); sys.exit(1)

out = [f"# 그림 생성 프롬프트 (전체 {len(need)}장)", "",
 "**만드는 법** — 무료 이미지 AI(빙 이미지 크리에이터 copilot.microsoft.com/images, 캔바 등)에 아래 한 줄을 통째로 붙여넣는다.",
 "마음에 드는 것을 골라 저장하고, **저장한 파일 이름을 왼쪽 이름으로** 바꾼다 (확장자는 png/jpg 아무거나 — 변환은 내가 한다).",
 "만든 그림을 채팅으로 보내주면 내가 앱에 넣는다. 한 번에 다 할 필요 없다 — **Day 하나(7~11장)씩** 하면 된다.",
 "", "모든 프롬프트에 같은 화풍 지시가 붙어 있어서 어느 날 만들어도 그림체가 비슷하게 나온다.", ""]
for day, theme, items in rows:
    out.append(f"## Day {day} — {theme}")
    out.append("")
    for f, label in items:
        out.append(f"**{f}** · {label}")
        out.append(f"> {EN[f[:-5]]}, {STYLE}")
        out.append("")
open('docs/image-prompts.md', 'w').write('\n'.join(out))
scenes = sum(1 for k in need if k.endswith('-scene'))
print(f"docs/image-prompts.md 기록 — {len(need)}장 (장면 {scenes} + 단어 {len(need) - scenes})")
