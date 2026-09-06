#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""목소리 블라인드 설문 페이지 두 장을 굽는다 — voice-vi.html(베트남인용) · voice-ko.html(한국인용).

소리는 vtest/ 의 파일을 쓴다: {키}_A.mp3(Edge 현행) · {키}_B.m4a(Supertonic).
나중에 Chirp가 오면 {키}_C.mp3 를 넣고 VOICES 에 'C' 를 추가해 다시 구우면 3자 비교가 된다.

완료를 누르면 동아리 서버(act:'vote')로 결과가 날아가 풀별(vi/ko)로 쌓인다.
집계 보기: 서버에 {act:'votes'} — 이름 없는 숫자만.
실행: python3 tools/mk_votetest.py
"""
import json, pathlib, random

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLUBURL = 'https://viet-club.chaochao-app.workers.dev'
VOICES = ['A', 'B', 'C']        # A=Edge(현행) B=Supertonic C=Chirp3 HD
EXT = {'A': 'mp3', 'B': 'm4a', 'C': 'mp3'}
NAME = {'A': 'Edge (현행)', 'B': 'Supertonic', 'C': 'Chirp 3 HD'}

VI = {
 "v1": "Xin chào, tôi là nhân viên mới.", "v2": "Hôm nay trời mưa nên đường rất trơn.",
 "v3": "Xin hãy đội mũ bảo hộ trước khi vào xưởng.", "v4": "Cái này bao nhiêu tiền một cân?",
 "v5": "Tôi muốn đổi tiền Việt sang tiền Hàn.", "v6": "Máy này bị hỏng rồi, đừng chạm vào.",
 "v7": "Cuối tuần chúng ta đi ăn phở nhé.", "v8": "Kiểm tra chất lượng xong thì đóng gói ngay.",
}
KO = {
 "k1": "안전모를 쓰고 작업장에 들어가세요.", "k2": "이 기계는 고장 났으니 만지지 마세요.",
 "k3": "내일 아침 여덟 시까지 출근해야 합니다.", "k4": "물건을 옮길 때는 허리를 조심하세요.",
}

CSS = """
:root{--bg:#f5f6f4;--card:#fff;--ink:#16181c;--dim:#5c6470;--line:#dde1dd;--dan:#0e6f62;--soft:#e4efec}
@media(prefers-color-scheme:dark){:root{--bg:#101316;--card:#171b1f;--ink:#e9ecea;--dim:#98a2ae;--line:#2a3138;--dan:#4fbfa8;--soft:#12312c}}
*{box-sizing:border-box}
body{font-family:-apple-system,'Apple SD Gothic Neo','Segoe UI',Roboto,sans-serif;max-width:640px;margin:0 auto;
 padding:24px 16px 80px;background:var(--bg);color:var(--ink);line-height:1.6}
h1{font-size:21px}.note{color:var(--dim);font-size:14px}
.q{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px 16px;margin:14px 0}
.sent{font-weight:600;margin:0 0 10px}
label{display:flex;flex-direction:column;gap:6px;margin:10px 0;padding:10px;border:1px solid var(--line);border-radius:6px}
audio{width:100%}span{font-size:14px}
#done{width:100%;padding:14px;font-size:17px;font-weight:700;background:var(--dan);color:#fff;border:0;border-radius:8px;margin-top:18px;cursor:pointer}
#done:disabled{opacity:.55}
#result{display:none;background:var(--soft);border:1px solid var(--dan);border-radius:8px;padding:16px;margin-top:16px;white-space:pre-line;font-size:15px}
"""

def page(pool, sents, ui, seed):
    rnd = random.Random(seed)
    rows = []
    for i, (k, txt) in enumerate(sents.items()):
        order = VOICES[:]
        rnd.shuffle(order)
        opts = "".join(
            f'<label><audio controls preload="none" src="vtest/{k}_{v}.{EXT[v]}"></audio>'
            f'<span><input type="radio" name="q{i}" value="{v}"> {ui["pick"].format(n=j+1)}</span></label>'
            for j, v in enumerate(order))
        rows.append(f'<div class="q" data-k="{k}"><p class="sent">{i+1}. {txt}</p>{opts}</div>')
    names = json.dumps(NAME, ensure_ascii=False)
    return f"""<!doctype html><html lang="{pool}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>{ui['title']}</title><style>{CSS}</style></head><body>
<h1>🎧 {ui['title']}</h1>
<p class="note">{ui['intro']}</p>
{''.join(rows)}
<button id="done">{ui['btn']}</button>
<div id="result"></div>
<script>
const NAME = {names};
document.getElementById('done').onclick = async () => {{
  const picks = {{}}; let skip = 0;
  document.querySelectorAll('.q').forEach(q => {{
    const s = q.querySelector('input:checked');
    if (!s) {{ skip++; return; }}
    picks[q.dataset.k] = s.value;
  }});
  if (!Object.keys(picks).length) {{ alert('{ui['none']}'); return; }}
  const btn = document.getElementById('done'); btn.disabled = true;
  const tally = {{}};
  Object.values(picks).forEach(v => tally[v] = (tally[v] || 0) + 1);
  let sent = '{ui['sendfail']}';
  if (!localStorage.getItem('voted_{pool}')) {{
    try {{
      const r = await fetch('{CLUBURL}', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ act: 'vote', pool: '{pool}', test: 'ab1', picks }}) }});
      if ((await r.json()).ok) {{ sent = '{ui['sentok']}'; localStorage.setItem('voted_{pool}', '1'); }}
    }} catch (e) {{}}
  }} else sent = '{ui['dup']}';
  const lines = Object.entries(tally).map(([v, n]) => `${{NAME[v] || v}}: ${{n}}`).join('\\n');
  const r = document.getElementById('result');
  r.style.display = 'block';
  r.textContent = `{ui['yours']}\\n\\n${{lines}}` + (skip ? `\\n{ui['skip']}: ${{skip}}` : '') + `\\n\\n${{sent}}`;
}};
</script></body></html>"""

UI_VI = dict(
  title="Giọng nào nghe giống người thật hơn?",
  intro="Nghe 3 giọng đọc cho mỗi câu rồi chọn giọng tự nhiên hơn (8 câu, ~3 phút). "
        "Khảo sát cho một ứng dụng học tiếng Hàn – tiếng Việt miễn phí. Cảm ơn bạn! 🙏",
  pick="Giọng {n} nghe thật hơn", btn="Xong — Gửi kết quả", none="Bạn chưa chọn câu nào.",
  yours="Kết quả của bạn:", skip="Bỏ qua", sentok="✅ Đã gửi kết quả. Cảm ơn bạn rất nhiều!",
  sendfail="⚠️ Không gửi được — vẫn cảm ơn bạn đã tham gia!", dup="(Đã gửi trước đó — không gửi lại)")
UI_KO = dict(
  title="어느 쪽이 더 사람 같나요?",
  intro="문장마다 세 소리를 듣고 더 자연스러운 쪽을 고르세요 (베트남어 8 + 한국어 4문장, 약 4분). "
        "무료 한–베 학습앱의 목소리 선정 설문입니다. 감사합니다! 🙏",
  pick="소리 {n}이 더 사람 같다", btn="다 골랐어요 — 결과 보내기", none="아직 고른 문장이 없습니다.",
  yours="당신의 선택:", skip="건너뜀", sentok="✅ 결과가 전송됐습니다. 감사합니다!",
  sendfail="⚠️ 전송은 실패했지만 참여 감사합니다!", dup="(이미 전송된 기기 — 다시 보내지 않았습니다)")

(ROOT / "voice-vi.html").write_text(page("vi", VI, UI_VI, seed=11))
(ROOT / "voice-ko.html").write_text(page("ko", {**VI, **KO}, UI_KO, seed=7))
print("voice-vi.html · voice-ko.html 생성 (소리:", len(VOICES), "종 —", " vs ".join(NAME[v] for v in VOICES), ")")
