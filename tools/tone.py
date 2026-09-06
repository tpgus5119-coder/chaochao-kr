#!/usr/bin/env python3
"""베트남어 글자에서 성조를 자동으로 읽어낸다.
ă â ê ô ơ ư 의 부호(브레베·곡절·뿔)는 성조가 아니므로 걸러낸다."""
import unicodedata as ud

MARKS = {
    '̀': ('huyền', '낮게 내려감',   '＼'),
    '́': ('sắc',   '짧게 올라감',   '／'),
    '̉': ('hỏi',   '내렸다 올림',   '∨'),
    '̃': ('ngã',   '끊었다 올림',   '∿'),
    '̣': ('nặng',  '짧고 무겁게',   '↓'),
}
FLAT = ('ngang', '평평하게 그대로', '—')

def syllable_tone(syl: str):
    for ch in ud.normalize('NFD', syl):
        if ch in MARKS:
            return MARKS[ch]
    return FLAT

def word_tones(vi: str):
    """다음절 단어는 음절마다 성조가 다르다. 전부 돌려준다."""
    out = []
    for syl in vi.split():
        n, ko, shape = syllable_tone(syl)
        out.append({"syl": syl, "name": n, "ko": ko, "shape": shape})
    return out

if __name__ == '__main__':
    for w in ['chào', 'anh', 'cảm ơn', 'tạm biệt', 'mã', 'mạ', 'người', 'tiếng Việt']:
        print(f"{w:12s}", ' + '.join(f"{t['syl']}({t['name']})" for t in word_tones(w)))
