#!/usr/bin/env python3
"""배포 판번호를 찍는다.
GitHub Pages 가 CSS/JS 를 10분간 브라우저에 캐시시켜서, 고쳐도 바로 안 보인다.
주소 뒤에 ?v=<내용해시> 를 붙여 '내용이 바뀔 때만' 새 주소가 되게 한다."""
import hashlib, pathlib, re

def h8(*paths):
    m = hashlib.sha1()
    for p in paths:
        m.update(pathlib.Path(p).read_bytes())
    # 음성·그림이 바뀌어도 판이 바뀌어야 한다 — 안 그러면 폰 캐시의 옛것이 안 지워진다.
    # 내용 대신 파일 크기 목록만 해시한다(2천 개를 다 읽으면 느리다).
    for p in sorted(pathlib.Path('audio').rglob('*.mp3')):
        m.update(f'{p}:{p.stat().st_size}'.encode())
    # 그림도 같은 이유로 (파일 크기만 본다)
    for p in sorted(pathlib.Path('img').glob('*.webp')):
        m.update(f'{p}:{p.stat().st_size}'.encode())
    return m.hexdigest()[:8]

# 판번호 재료는 **sw.js 가 캐시하는 것 전부**여야 한다.
# 2026-08-31: order.json 이 빠져 있었다 — 발음 4,431곳을 고쳤는데 소리·그림이 그대로면
#   판번호가 안 바뀌고, 서비스 워커가 옛 order.json 을 계속 내준다("고쳤는데 안 바뀐다").
#   sw.js 의 SHELL 목록에서 자동으로 읽어 온다 — 목록이 늘면 여기도 따라 늘게.
_shell = re.findall(r"'\./([^']+)'", pathlib.Path('sw.js').read_text())
ver = h8('style.css', 'app.js', 'pitch.js',
         *[f for f in _shell if f.endswith('.json') and pathlib.Path(f).exists()])

f = pathlib.Path('index.html'); s = f.read_text()
s = re.sub(r'(href="style\.css)(\?v=[^"]*)?"', rf'\1?v={ver}"', s)
s = re.sub(r'(src="app\.js)(\?v=[^"]*)?"', rf'\1?v={ver}"', s)
s = re.sub(r'(src="pitch\.js)(\?v=[^"]*)?"', rf'\1?v={ver}"', s)
f.write_text(s)

w = pathlib.Path('sw.js'); t = w.read_text()
t = re.sub(r"const V = '[^']*';", f"const V = 'vn-{ver}';", t)
w.write_text(t)
def check_uivi():
    """번역 사전에 같은 열쇠가 두 번 있으면 알린다.

    JS 객체는 같은 열쇠가 두 번 있으면 **뒤엣것이 이긴다.** 그래서 앞에 적어 둔 번역이
    조용히 묻힌다 — 화면에는 아무 표시도 안 나서 눈으로는 절대 못 찾는다.
    실제로 26개가 쌓여 있었고, 그중 '나'가 'bạn'(너)으로 잡혀 있었다(순위표의 '나'인데).
    배포 직전마다 여기서 잡는다."""
    import collections, re
    s = pathlib.Path('app.js').read_text(encoding='utf-8')
    i = s.find('const UIVI = {')
    if i < 0:
        return
    seg = s[i:s.find('\n};', i)]
    ks = re.findall(r"'((?:[^'\\]|\\.)*?)':\s*\n?\s*'", seg)
    dup = [k for k, c in collections.Counter(ks).items() if c > 1]
    if dup:
        print(f'  ⚠️ 번역 사전 중복 열쇠 {len(dup)}개 — 앞엣것이 묻힙니다: {dup[:6]}')
    else:
        print(f'  번역 사전 {len(ks)}개 · 중복 없음')


check_uivi()
print('판번호', ver)
