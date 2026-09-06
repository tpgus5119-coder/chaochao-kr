/* 설문이 서버에 **실제로 닿는지** 스스로 시험한다.  실행: node tools/survey_selftest.mjs
 *
 * 왜 있나: giong.html 을 만들어 놓고 한 번도 답을 흘려보지 않은 채 사람들에게
 * 링크를 줬다. 서버는 그 이름을 몰라 답을 통째로 버렸고, 페이스북에서 답해 준
 * 사람들의 표가 사라졌다. 코드를 눈으로 읽어서는 안 보이는 종류였다.
 *
 * 진짜 워커 코드를 그대로 불러다 가짜 KV 에 물려 돌린다. 통신도, 실제 저장소도
 * 건드리지 않으므로 **진짜 표를 더럽히지 않는다.**
 * 보내는 쪽 셈은 giong.html 에서 **그 줄을 뽑아 와서** 쓴다 — 베낀 사본을
 * 시험하면 사본만 맞고 정작 페이지는 틀릴 수 있다.
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const R = join(dirname(fileURLToPath(import.meta.url)), '..');
const ORIGIN = 'https://tpgus5119-coder.github.io';

/* ── 가짜 KV — 워커가 쓰는 만큼만 ───────────────────────── */
const store = new Map();
const KV = {
  async put(k, v) { store.set(k, v); },
  async get(k) { return store.has(k) ? store.get(k) : null; },
  async delete(k) { store.delete(k); },
  async list({ prefix = '' } = {}) {
    return { keys: [...store.keys()].filter(k => k.startsWith(prefix)).map(name => ({ name })),
             list_complete: true };
  },
};

const worker = (await import(join(R, 'tools/club_worker.js'))).default;
const call = async body => {
  const res = await worker.fetch(new Request('https://x/', {
    method: 'POST', headers: { 'Content-Type': 'application/json', Origin: ORIGIN },
    body: JSON.stringify(body),
  }), { CLUB: KV });
  return res.json();
};

/* ── 보내는 쪽 셈을 giong.html 에서 뽑아 온다 ────────────── */
const page = readFileSync(join(R, 'giong.html'), 'utf8');
const lines = page.split('\n').filter(l =>
  l.includes('const old=Object.assign') || l.includes("old['1'+n+v]"));
if (lines.length !== 2) throw new Error(`giong.html 의 셈하는 줄을 못 찾았다 (${lines.length}줄)`);
const encode = new Function('dia', 'nat', `${lines.join('\n')}\nreturn old;`);

/* ── 한 사람이 낸 답(문장 5개 × 소리 4개 + 고른 것 5개) ──── */
const V = ['A', 'B', 'C', 'D'];
const dia = {}, nat = {};
for (let n = 1; n <= 5; n++) {
  V.forEach(v => { dia[`${n}${v}`] = v === 'D' ? 'nam' : 'bac'; });
  nat[n] = 'C';                                   // 다섯 문장 모두 C 를 골랐다 치고
}

let bad = 0;
const eq = (name, got, want) => {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  if (!ok) bad++;
  console.log(`  ${ok ? '통과' : '실패'}  ${name}` + (ok ? '' : `\n        받음 ${JSON.stringify(got)}\n        바람 ${JSON.stringify(want)}`));
};

console.log('■ 새 칸(act:giong) — 워커를 v15 로 올린 뒤의 길');
eq('보내면 받아 준다', (await call({ act: 'giong', rg: 'nam', dia, nat })).ok, true);
let g = await call({ act: 'giongs' });
eq('사람 수 1', g.n, 1);
eq('문장1의 D 를 남부라 함', g.dia['1D'], { nam: 1 });
eq('문장1에서 고른 소리 C', g.nat['1'], { C: 1 });

console.log('\n■ 옛 칸(act:dialect) — 지금 올라가 있는 서버에서 가는 길');
const old = encode(dia, nat);
eq('칸 수 25 (지방 20 + 고른 것 5)', Object.keys(old).length, 25);
eq('보내면 받아 준다', (await call({ act: 'dialect', rg: 'nam', picks: old })).ok, true);

/* survey_read.py 가 되돌리는 규칙과 같은 셈으로 읽어 본다 */
g = await call({ act: 'giongs' });
const dia2 = {}, nat2 = {};
for (const [k, cnt] of Object.entries(g.dia)) {
  if (k.length === 2) dia2[k] = cnt;
  else if (k.length === 3 && k[0] === '1')
    (nat2[k[1]] = nat2[k[1]] || {})[k[2]] = Object.values(cnt).reduce((a, b) => a + b, 0);
}
eq('옛 칸 것까지 세면 2명', g.n + g.nOld, 2);
eq('되돌린 지방 표 — 문장1의 D 는 남부 2', dia2['1D'], { nam: 2 });
eq('되돌린 고른 소리 — 문장1은 C 1표(옛 칸 몫)', nat2['1'], { C: 1 });

console.log(bad ? `\n✗ 실패 ${bad}개` : '\n✓ 모두 통과 — 두 길 다 답이 남는다');
process.exit(bad ? 1 : 0);
