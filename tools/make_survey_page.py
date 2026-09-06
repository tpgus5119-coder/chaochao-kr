#!/usr/bin/env python3
"""목소리 설문 **한 장**으로 합친다 (giong.html).

전에는 두 장이었다.
  · voice-vi.html — 어느 소리가 더 사람 같은가 (가리고 물었다)
  · giong.html    — 이 소리가 북부냐 남부냐 (이름을 보이고 물었다)
링크 두 개를 부탁하면 둘째 것은 거의 안 온다. 그래서 한 화면에서 둘 다 묻는다.

문장마다 묻는 것 두 가지:
  ① 네 소리 **각각** 어느 지방인가  — Bắc / Trung / Nam / Không rõ
  ② 네 소리 중 **하나만** — 어느 것이 가장 사람 같은가

엔진 이름은 **적지 않는다.** 전 설문은 이름을 보였는데, 그때는 지방만 물었으니
괜찮았다. 이제 '어느 것이 사람 같은가'를 같이 묻는 이상 "우리 앱 목소리"라고
써 두면 그 답이 예의나 반감으로 기울어 못 쓰게 된다. 지방 판단은 이름을 몰라도
잣대 노릇을 한다 — A·C가 북부로 나오는지 우리가 확인하면 되는 것이라서.

자리 차례도 문장마다 돌린다(라틴방진). 먼저 들은 것이 유리한 버릇을 없앤다.
화면에는 Giọng 1~4(자리 번호)로 보이고, 보내는 열쇠는 참이름 A~D다.

색만으로 고른 것을 알리지 않는다(색각 배려) — 굵기와 테두리도 함께 바뀐다.

실행: python3 tools/make_survey_page.py   →  giong.html
"""
import html
import json
import pathlib

R = pathlib.Path(__file__).resolve().parent.parent
LIST = R / "dtest" / "list.json"
OUT = R / "giong.html"

# 자리 차례 — 네 소리가 첫째 자리에 고르게 선다.
ORDER = [("A", "B", "C", "D"), ("B", "D", "A", "C"), ("C", "A", "D", "B"),
         ("D", "C", "B", "A"), ("A", "D", "B", "C")]
PICKS = [("bac", "Bắc"), ("trung", "Trung"), ("nam", "Nam"), ("?", "Không rõ")]

CSS = """
:root{--bg:#fff;--ink:#1a1a1a;--dim:#666;--line:#d8d8d8;--card:#fafafa;
 --dan:#c0392b;--sao:#1d6f42}
@media (prefers-color-scheme:dark){:root{--bg:#161616;--ink:#eee;--dim:#aaa;
 --line:#3a3a3a;--card:#1f1f1f;--dan:#e05c4a;--sao:#4bb377}}
*{box-sizing:border-box}
body{margin:0 auto;padding:18px 14px 90px;background:var(--bg);color:var(--ink);
 font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
 line-height:1.6;max-width:640px}
h1{font-size:22px;margin:0 0 6px;text-wrap:balance}
.note{color:var(--dim);font-size:14px;margin:0 0 16px}
.rg{border:1px solid var(--line);border-radius:10px;padding:14px;margin-bottom:20px;
 background:var(--card)}
.rg p{margin:0 0 10px;font-weight:700}
.row{display:flex;gap:8px;flex-wrap:wrap}
.row button{flex:1 1 22%;padding:10px 6px;border:1px solid var(--line);
 background:var(--bg);color:var(--ink);border-radius:8px;font-size:15px;cursor:pointer}
.row button.on{border:3px solid var(--dan);font-weight:800;
 background:color-mix(in srgb,var(--dan) 12%,transparent)}
.nat button.on{border-color:var(--sao);
 background:color-mix(in srgb,var(--sao) 14%,transparent)}
.q{border:1px solid var(--line);border-radius:10px;padding:14px;margin-bottom:18px}
.sent{font-size:18px;font-weight:700;margin:0 0 12px}
.v{border-top:1px dashed var(--line);padding-top:12px;margin-top:12px}
.v:first-of-type{border-top:0;padding-top:0;margin-top:0}
.vn{font-weight:700;margin-bottom:6px;font-size:15px}
.ask{font-size:13px;color:var(--dim);margin:0 0 6px}
audio{width:100%;height:36px;margin-bottom:8px}
.nat{border-top:2px solid var(--line);margin-top:14px;padding-top:12px}
.nat .ask{font-weight:700;color:var(--ink);font-size:14px}
#send{position:sticky;bottom:14px;width:100%;padding:16px;font-size:17px;font-weight:800;
 border:0;border-radius:10px;background:var(--dan);color:#fff;cursor:pointer;
 box-shadow:0 4px 14px rgba(0,0,0,.25)}
#send:disabled{opacity:.5}
#out{margin-top:14px;white-space:pre-line;font-size:15px}
"""

JS = """
const API='https://viet-club.chaochao-app.workers.dev';
const N=%d;
let RG='';
const dia={},nat={};
const mark=(b,store,key)=>{store[key]=b.dataset.v;
  b.parentNode.querySelectorAll('button').forEach(x=>x.classList.remove('on'));
  b.classList.add('on');left();};
document.querySelectorAll('.rg button').forEach(b=>b.onclick=()=>{
  RG=b.dataset.v;
  b.parentNode.querySelectorAll('button').forEach(x=>x.classList.remove('on'));
  b.classList.add('on');left();});
document.querySelectorAll('.dq button').forEach(b=>b.onclick=()=>mark(b,dia,b.dataset.k));
document.querySelectorAll('.nat button').forEach(b=>b.onclick=()=>mark(b,nat,b.dataset.k));
// 남은 개수를 단추에 적는다 — 어디까지 했는지 보여야 끝까지 한다.
function left(){
  const need=N*4+N+1, got=Object.keys(dia).length+Object.keys(nat).length+(RG?1:0);
  document.getElementById('send').textContent=
    got>=need?'Gửi kết quả ✓':`Gửi kết quả (còn ${need-got} mục)`;
}
left();
document.getElementById('send').onclick=async()=>{
  if(!RG){alert('Hãy chọn vùng giọng của bạn trước.');scrollTo(0,0);return;}
  if(!Object.keys(dia).length&&!Object.keys(nat).length){
    alert('Bạn chưa chọn mục nào.');return;}
  const btn=document.getElementById('send');btn.disabled=true;
  const post=b=>fetch(API,{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify(b)}).then(r=>r.json()).catch(()=>({}));
  let msg='⚠️ Không gửi được — nhưng vẫn cảm ơn bạn!';
  /* 서버가 옛 판이면 'giong'을 모르고 답을 통째로 버린다 — 실제로 그랬고,
     페이스북에서 답해 준 사람들의 표가 그렇게 사라졌다. 그래서 **옛 판에서도
     두 답이 다 남게** 한다. 옛 'dialect' 칸은 열쇠가 '숫자1~2 + A~D',
     값이 bac/trung/nam/? 라야 통과한다. 그 틀 안에서:
       · 지방 표  = '3C'  (문장3의 소리C)        — 본디 쓰임 그대로
       · 사람 같다 = '13D' (앞의 1은 표시, 문장3에서 D를 골랐다). 값은 안 쓴다.
     한 번에 보내니 한 사람의 두 답이 갈라져 반만 남는 일이 없다.
     읽는 쪽은 tools/survey_read.py 하나뿐이고 거기서 되돌린다.
     ※ 문장이 9개를 넘으면 이 표시가 겹친다. 그때는 짜임을 바꿔야 한다. */
  const old=Object.assign({},dia);
  for(const[n,v]of Object.entries(nat)) old['1'+n+v]='?';
  if((await post({act:'giong',rg:RG,dia,nat})).ok
   ||(await post({act:'dialect',rg:RG,picks:old})).ok)
    msg='✅ Đã gửi. Cảm ơn bạn rất nhiều! 🙏';
  document.getElementById('out').textContent=
    `Vùng: ${RG} · Đã đánh dấu ${Object.keys(dia).length} + ${Object.keys(nat).length} mục.\\n${msg}`;
};
"""


def main():
    items = json.loads(LIST.read_text(encoding="utf-8"))
    p = ['<!doctype html><html lang="vi"><head><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1">',
         "<title>Giọng máy đọc tiếng Việt — nghe giúp mình nhé</title>",
         f"<style>{CSS}</style></head><body>",
         "<h1>🎧 Giọng nào nghe giống người thật? Và là giọng vùng nào?</h1>",
         '<p class="note">Mỗi câu có <b>4 giọng máy đọc</b>. Nghe xong, bạn giúp mình '
         '<b>2 việc</b>:<br>'
         '① Với <b>từng giọng</b>, đánh dấu đó là giọng <b>Bắc / Trung / Nam</b> '
         '(không chắc thì chọn <b>Không rõ</b> — đừng đoán bừa).<br>'
         '② Trong 4 giọng, chọn <b>một giọng duy nhất</b> nghe <b>giống người thật nhất</b>.'
         '<br><br>Mình đang làm một ứng dụng học tiếng Hàn – tiếng Việt '
         '<b>miễn phí</b>, và cần chọn giọng đọc cho đúng. '
         'Khảo sát <b>không hỏi tên, không hỏi tuổi</b>, mất khoảng 4 phút. Cảm ơn bạn! 🙏</p>',
         '<div class="rg"><p>Trước tiên: bạn nói giọng vùng nào?</p><div class="row">']
    for v, lab in [("bac", "Miền Bắc"), ("trung", "Miền Trung"), ("nam", "Miền Nam")]:
        p.append(f'<button type="button" data-v="{v}">{lab}</button>')
    p.append('</div></div>')

    for it in items:
        n = it["n"]
        p.append('<div class="q">')
        p.append(f'<p class="sent">Câu {n}. {html.escape(it["text"])}</p>')
        seats = []
        for seat, tag in enumerate(ORDER[(n - 1) % len(ORDER)], 1):
            f = it["files"].get(tag)
            if not f:
                continue
            seats.append((seat, tag))
            p.append('<div class="v">')
            p.append(f'<div class="vn">Giọng {seat}</div>')
            p.append(f'<audio controls preload="none" src="dtest/{f}"></audio>')
            p.append('<p class="ask">Giọng này là giọng vùng nào?</p>')
            p.append('<div class="row dq">')
            for v, lab in PICKS:
                p.append(f'<button type="button" data-k="{n}{tag}" data-v="{v}">{lab}</button>')
            p.append("</div></div>")
        p.append('<div class="nat"><p class="ask">'
                 '★ Trong 4 giọng trên, giọng nào nghe <u>giống người thật nhất</u>? '
                 '(chọn 1)</p><div class="row">')
        for seat, tag in seats:
            p.append(f'<button type="button" data-k="{n}" data-v="{tag}">Giọng {seat}</button>')
        p.append("</div></div></div>")

    p.append('<button id="send">Gửi kết quả</button><div id="out"></div>')
    p.append(f"<script>{JS % len(items)}</script></body></html>")
    OUT.write_text("\n".join(p), encoding="utf-8")
    print(f"{OUT.name} 만듦 — 문장 {len(items)}개 · 물음 {len(items)*5+1}개 · "
          f"{OUT.stat().st_size//1024}KB")


if __name__ == "__main__":
    main()
