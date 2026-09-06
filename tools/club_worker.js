/* 동아리 + 순위 서버 (Cloudflare Worker + KV) — v2
   설정: Worker 만들기 → 이 코드 붙여넣고 Deploy → Settings → Bindings →
        KV namespace, Variable name: CLUB → 다시 Deploy
   하는 일
   · 동아리 만들기 / 목록 / 가입(자유·승인제) / 승인 / 탈퇴
   · 이번 주 도장(월~일)과 외운 단어 수를 동아리원끼리 공유
   · 주간 순위 — 상위 5명만 이름 공개, 내 등수는 나에게만
   v2: 사람이 다 나간 동아리는 스스로 지워진다 / 바뀐 게 없으면 저장하지 않는다
   v3: 순위는 동아리 안이 아니라 **앱 전체**다 (act:'rank'). 전체 평균과 내 자리도 함께 준다.
       동아리는 이제 '이번 주 출석판'만 맡는다.
   v4: 순위는 별명이 아니라 기기마다 다른 표(uid)로 구분한다 — 같은 별명을 쓰는 두 사람이
       서로의 기록을 덮어쓰지 않게. 남의 등수와 이름은 아무에게도 보내지 않는다
       (누구나 자기 자리만 안다).
   v5: 운영자용 act:'stats' — **이름 없이 숫자만.** 누가 누구인지는 서버도 모른다.
       운영을 하려면 규모와 흐름은 알아야 하는데, 그걸 알기 위해 개인을 알 필요는 없다.
   v6: 폰 알림(웹 푸시). 보내는 것은 '깨워라' 신호뿐 — 대화 내용은 서버를 지나가지 않는다.
       **하루 한 번**, 오늘 아직 공부 안 한 사람에게만. 읽씹이 사흘 이어지면 그 사람은 쉰다
       (그다음 앱을 한 번이라도 열면 다시 0부터 — 돌아온 사람은 다시 챙긴다).
       Settings → Variables and Secrets 에 VAPID_PRIV 와 PUSH_KEY 를 넣어야 돈다.
       재는 것: 몇 명 · 요일별 접속 · **어디까지 갔다 그만두는가(깔때기)** ·
       **얼마나 남아 있는가(코호트)** · **진짜 기억률** · **많은 사람이 틀리는 단어**.
       뒤의 넷이 앱을 어디서 고쳐야 하는지 알려주는 숫자다.
   v7: **사람끼리** — 같은 동아리 안에서만.
       · 사람 목록(uid 로 구분) · 엄지척 하루 한 번 · 쪽지 · 프로필 사진 · 분석 공개 여부
       · 차단하면 그 사람 쪽지는 아예 안 들어온다
       숨기지 않을 것: 쪽지 글과 사진은 **이 서버에 그대로 저장된다**(30일·사진은 바꿀 때까지).
       암호화하지 않으므로 운영자는 마음먹으면 볼 수 있다. 앱 화면에도 그렇게 적어 둔다.
       막는 것은 Origin 허용목록 하나뿐이다 — 비밀 이야기를 할 자리가 아니다.
   v14: 남·북 말씨 확인 설문(act:'dialect'/'dialects') 추가 — giong.html 이 쓴다.
   v15: 설문 **하나로 합침**(act:'giong'/'giongs'). 링크 두 개를 사람에게 부탁하면
        둘째 것은 거의 안 온다 — 한 화면에서 두 가지를 함께 묻는다.
        · 문장마다 '어느 소리가 사람 같은가' **하나만** (nat)
        · 그 문장의 네 소리 **각각** 어느 지방인가 (dia) — 열쇠는 옛 'dialect'와 같은
          '1A'·'5D' 꼴이라 지금까지 모은 표와 그대로 합산된다.
   v14: 목소리 설문에 **응답자 지방(북/중/남)** 을 같이 남긴다. 화면은 처음부터
        물어서 보내고 있었는데 서버가 버리고 있었다. 집계도 지방별로 나눠 준다 —
        '남부 사람은 어느 소리를 골랐나'가 이 설문에서 가장 알고 싶은 것이라서.
   v8: 별명은 먼저 쓴 사람이 임자(act:'nick') · 동아리는 **하나만** 들어간다.
   개인정보는 별명·진도 숫자·본인이 올린 사진·본인이 쓴 쪽지뿐이다. 실명은 받지 않는다. */
const CORS = o => ({
  'Access-Control-Allow-Origin': o, 'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type', 'Content-Type': 'application/json',
});
const OK = ['https://tpgus5119-coder.github.io', 'http://localhost:8899'];
const MAX_CLUBS = 300;
const cut = (s, n) => String(s == null ? '' : s).slice(0, n);
const num = (v, hi) => Math.max(0, Math.min(hi, ~~v));
const week = () => { const d = new Date(); d.setUTCDate(d.getUTCDate() - ((d.getUTCDay() + 6) % 7));
                     return d.toISOString().slice(0, 10); };

/* 웹 푸시 — 내용 없는 신호만 보낸다.
   VAPID 는 '이 서버가 보낸 게 맞다'는 서명이다. 내용을 안 실으므로 암호화는 필요 없다. */
const u8 = b64 => Uint8Array.from(atob(b64.replace(/-/g, '+').replace(/_/g, '/')), c => c.charCodeAt(0));
const b64u = buf => btoa(String.fromCharCode(...new Uint8Array(buf)))
  .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

async function vapidJwt(aud, privB64) {
  const key = await crypto.subtle.importKey('pkcs8', u8(privB64),
    { name: 'ECDSA', namedCurve: 'P-256' }, false, ['sign']);
  const head = b64u(new TextEncoder().encode(JSON.stringify({ typ: 'JWT', alg: 'ES256' })));
  const body = b64u(new TextEncoder().encode(JSON.stringify({
    aud, exp: Math.floor(Date.now() / 1000) + 12 * 3600, sub: 'mailto:chaochao@example.com' })));
  const sig = await crypto.subtle.sign({ name: 'ECDSA', hash: 'SHA-256' }, key,
    new TextEncoder().encode(head + '.' + body));
  return head + '.' + body + '.' + b64u(sig);
}

async function webpush(endpoint, privB64) {
  const aud = new URL(endpoint).origin;
  const jwt = await vapidJwt(aud, privB64);
  const pub = 'BIXezZvZv-VlkJ49y1sGnEtMfqWkENMJOyZPi1XubrE2J6DeCh2ttTDoimW-EO7PR1U-8qNqSyMetpfZMwZEnTQ';
  return fetch(endpoint, {
    method: 'POST',
    headers: { 'TTL': '86400', 'Authorization': `vapid t=${jwt}, k=${pub}` },
  });
}

const today = () => new Date().toISOString().slice(0, 10);

/* 동아리 사람 목록 — 남에게 나가는 것만 골라 담는다.
   분석(정답률·점수)은 **본인이 공개로 켠 사람 것만** 나간다. 사진은 판 번호만 나가고
   그림 자체는 따로 받아 간다(목록이 무거워지지 않게). */
function dirOf(cu, c, me) {
  const people = Object.entries(cu)
    .filter(([u, v]) => v && v.n)
    .map(([u, v]) => {
      const o = { uid: u, nick: v.n, days: v.wk === week() ? (v.w || []) : [],
                  cr: v.wk === week() ? (v.cr || 0) : 0,     // 주가 바뀌면 0 — 월요일 초기화
                  crm: v.crm || 0,                            // 한 달치는 주가 바뀌어도 이어진다
                  memo: v.m || 0, st: v.st || 0, td: v.td || 0,
                  th: v.th || 0, av: v.av || 0, at: v.at || '',
                  thToday: !!(v.tb && v.tb[me] === today()) };
      if (v.op) { o.score = v.s || 0; o.pct = v.p || {}; }
      return o;
    })
    .sort((x, y) => (y.days || []).reduce((a, n) => a + n, 0) - (x.days || []).reduce((a, n) => a + n, 0)
                    || y.memo - x.memo);
  return { name: c.name, owner: c.owner, wait: c.owner === cu[me]?.n ? c.wait : undefined,
           total: people.length, people, members: people.map(p => ({ nick: p.nick, days: p.days, memo: p.memo })),
           block: (cu[me] && cu[me].bl) || [] };
}
async function inboxOf(KV, uid) {
  if (!uid) return {};
  return JSON.parse((await KV.get(`mb:${uid}`)) || '{}');
}

export default {
  async fetch(req, env) {
    const origin = req.headers.get('Origin') || '';
    const cors = CORS(OK.includes(origin) ? origin : 'null');
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors });
    if (req.method !== 'POST' || !OK.includes(origin))
      return new Response('{"error":"blocked"}', { status: 403, headers: cors });

    const KV = env.CLUB;
    const send = o => new Response(JSON.stringify(o), { headers: cors });
    if (!KV) return send({ error: 'KV 저장소가 연결되지 않았습니다 (Bindings: CLUB)' });

    const b = await req.json().catch(() => ({}));
    const act = cut(b.act, 20), nick = cut(b.nick, 10);

    /* ── 목소리 블라인드 설문 (v13) ────────────────────
       표 하나 = KV 글 하나(동시 제출이 서로를 덮어쓸 일이 없다). 90일 보관.
       개인정보 없음 — 어느 소리를 골랐는지 뿐. 풀은 둘: vi(베트남인) / ko(한국인). */
    if (act === 'vote') {
      const pool = b.pool === 'vi' ? 'vi' : 'ko';
      const clean = {};
      for (const [k, v] of Object.entries(b.picks || {}).slice(0, 30))
        if (/^[a-z]\d{1,2}$/.test(k) && /^[A-C]$/.test(String(v))) clean[k] = String(v);
      if (!Object.keys(clean).length) return send({ error: 'empty' });
      /* v14: **응답자 지방(rg)도 남긴다.**
         설문 화면은 처음부터 '당신은 어느 지방 말씨입니까(북/중/남)'를 묻고 보내 왔는데,
         서버가 그 칸을 그냥 버리고 있었다. 그래서 "남부 사람은 어느 소리를 골랐나"를
         물을 수가 없었다 — 목소리 고르기에서 가장 알고 싶은 것이 그건데도.
         지방은 개인을 가리키지 않는다(셋 중 하나). */
      const rg = ['bac', 'trung', 'nam'].includes(b.rg) ? b.rg : '';
      await KV.put(`sv:${pool}:${Date.now()}:${Math.random().toString(36).slice(2, 8)}`,
        JSON.stringify({ p: clean, r: rg, t: cut(b.test, 12) }),
        { expirationTtl: 60 * 60 * 24 * 90 });
      return send({ ok: true });
    }
    /* ── 남·북 말씨 확인 (v14) ─────────────────────
       블라인드 설문과 다른 것이다. 저것은 '어느 쪽이 더 사람 같은가',
       이것은 '이 목소리가 어느 지방 말씨인가'를 이름을 보여 주고 묻는다.
       열쇠는 '1A'·'5D' 꼴(문장번호 + 목소리), 값은 bac/trung/nam/?. */
    if (act === 'dialect') {
      const rg = ['bac', 'trung', 'nam'].includes(b.rg) ? b.rg : '';
      const clean = {};
      for (const [k, v] of Object.entries(b.picks || {}).slice(0, 40))
        if (/^\d{1,2}[A-D]$/.test(k) && /^(bac|trung|nam|\?)$/.test(String(v)))
          clean[k] = String(v);
      if (!Object.keys(clean).length) return send({ error: 'empty' });
      await KV.put(`dl:${Date.now()}:${Math.random().toString(36).slice(2, 8)}`,
        JSON.stringify({ p: clean, r: rg }), { expirationTtl: 60 * 60 * 24 * 90 });
      return send({ ok: true });
    }
    /* ── 합친 설문 (v15) ──────────────────────────
       한 사람이 한 번에 두 가지를 답한다. 표 하나 = KV 글 하나.
       dia 열쇠는 'dialect'와 같은 꼴이라 옛 표와 같이 셀 수 있고,
       nat 열쇠는 문장 번호, 값은 그 사람이 고른 소리 하나(A~D)다. */
    if (act === 'giong') {
      const rg = ['bac', 'trung', 'nam'].includes(b.rg) ? b.rg : '';
      const dia = {}, nat = {};
      for (const [k, v] of Object.entries(b.dia || {}).slice(0, 40))
        if (/^\d{1,2}[A-D]$/.test(k) && /^(bac|trung|nam|\?)$/.test(String(v)))
          dia[k] = String(v);
      for (const [k, v] of Object.entries(b.nat || {}).slice(0, 20))
        if (/^\d{1,2}$/.test(k) && /^[A-D]$/.test(String(v))) nat[k] = String(v);
      if (!Object.keys(dia).length && !Object.keys(nat).length)
        return send({ error: 'empty' });
      await KV.put(`gs:${Date.now()}:${Math.random().toString(36).slice(2, 8)}`,
        JSON.stringify({ d: dia, v: nat, r: rg }), { expirationTtl: 60 * 60 * 24 * 90 });
      return send({ ok: true });
    }
    if (act === 'giongs') {                      // 집계 — 이름 없는 숫자만
      /* 지방(dia)은 옛 'dl:' 표까지 함께 센다. 같은 열쇠 꼴이라 합쳐도 된다. */
      const dia = {}, nat = {}, byrg = {}; let n = 0, nOld = 0, cursor;
      const add = (m, q, c) => { (m[q] = m[q] || {})[c] = (m[q][c] || 0) + 1; };
      for (const [pre, isNew] of [['gs:', true], ['dl:', false]]) {
        cursor = undefined;
        do {
          const l = await KV.list({ prefix: pre, cursor });
          for (const k of l.keys) {
            const v = JSON.parse((await KV.get(k.name)) || 'null');
            if (!v) continue;
            isNew ? n++ : nOld++;
            const rg = v.r || '', m = rg ? (byrg[rg] = byrg[rg] || { n: 0, dia: {}, nat: {} }) : null;
            if (m) m.n++;
            for (const [q, c] of Object.entries(v.d || v.p || {})) {
              add(dia, q, c); if (m) add(m.dia, q, c);
            }
            for (const [q, c] of Object.entries(v.v || {})) {
              add(nat, q, c); if (m) add(m.nat, q, c);
            }
          }
          cursor = l.list_complete ? undefined : l.cursor;
        } while (cursor);
      }
      return send({ n, nOld, dia, nat, byrg });
    }
    if (act === 'dialects') {                    // 집계 — 이름 없는 숫자만
      const agg = {}, byrg = {}; let n = 0, cursor;
      do {
        const l = await KV.list({ prefix: 'dl:', cursor });
        for (const k of l.keys) {
          const v = JSON.parse((await KV.get(k.name)) || 'null');
          if (!v) continue;
          n++;
          for (const [q, c] of Object.entries(v.p || {})) {
            (agg[q] = agg[q] || {})[c] = (agg[q][c] || 0) + 1;
            if (!v.r) continue;
            const m = byrg[v.r] = byrg[v.r] || {};
            (m[q] = m[q] || {})[c] = (m[q][c] || 0) + 1;
          }
        }
        cursor = l.list_complete ? undefined : l.cursor;
      } while (cursor);
      return send({ n, agg, byrg });
    }
    if (act === 'votes') {                                   // 집계 — 이름 없는 숫자만
      const out = {};
      for (const pool of ['vi', 'ko']) {
        const agg = {}, byrg = {}; let n = 0, norg = 0, cursor;
        do {
          const l = await KV.list({ prefix: `sv:${pool}:`, cursor });
          for (const k of l.keys) {
            const v = JSON.parse((await KV.get(k.name)) || 'null');
            if (!v) continue;
            n++;
            for (const [q, c] of Object.entries(v.p || {}))
              (agg[q] = agg[q] || {})[c] = (agg[q][c] || 0) + 1;
            // 지방별 집계. v13 이전 표에는 지방이 없다 — 그 수는 norg 로 따로 알린다.
            const rg = v.r || '';
            if (!rg) { norg++; continue; }
            const m = byrg[rg] = byrg[rg] || { n: 0, agg: {} };
            m.n++;
            for (const [q, c] of Object.entries(v.p || {}))
              (m.agg[q] = m.agg[q] || {})[c] = (m.agg[q][c] || 0) + 1;
          }
          cursor = l.list_complete ? undefined : l.cursor;
        } while (cursor);
        out[pool] = { n, norg, agg, byrg };
      }
      return send(out);
    }

    const clubs = JSON.parse((await KV.get('clubs')) || '{}');
    /* CKEY 가 **정의되어 있지 않았다** — quit(계정 탈퇴)이 동아리에서 뺄 때
       KV.put(CKEY, …) 를 부르므로, 동아리에 든 사람은 탈퇴가 실패했다 (2026-08-30 검수) */
    const CKEY = 'clubs';
    const save = () => KV.put(CKEY, JSON.stringify(clubs));

    /* ── 별명 자리 잡기 ─────────────────────────────────
       같은 별명이 둘이면 동아리 출석판에서 누가 누구인지 알 수 없다.
       그래서 먼저 쓴 사람이 임자다. 기기표(uid)가 같으면 자기 것이니 그냥 통과. */
    const NKEY = 'nicks';
    if (act === 'nick') {
      const uid = cut(b.uid, 16);
      if (!nick || !uid) return send({ error: '별명과 기기 표가 있어야 합니다' });
      const nicks = JSON.parse((await KV.get(NKEY)) || '{}');
      const low = nick.toLowerCase();
      if (nicks[low] && nicks[low] !== uid) return send({ error: '이미 쓰는 사람이 있습니다' });
      for (const k of Object.keys(nicks)) if (nicks[k] === uid && k !== low) delete nicks[k];
      if (nicks[low] !== uid) { nicks[low] = uid; await KV.put(NKEY, JSON.stringify(nicks)); }
      // 별명을 바꿨는데 동아리 명단은 옛 이름 그대로면, 다음 접속에 '너는 회원이 아니다'가 되어
      // 앱이 동아리를 지워 버린다. 실제로 그 사고가 났다 — 이름을 바꿀 때 명단도 같이 고친다.
      let moved = false;
      for (const c of Object.values(clubs)) {
        const was = (c.uids || {})[uid];
        if (!was || was === nick) continue;
        c.uids[uid] = nick;
        c.members = c.members.map(x => (x === was ? nick : x));
        c.wait = (c.wait || []).map(x => (x === was ? nick : x));
        if (c.owner === was) c.owner = nick;
        moved = true;
      }
      if (moved) await save();
      return send({ ok: true });
    }

    /* ── 관리자 도구 ──────────────────────────────────
       대표님이 아이디를 둘 쓰시던 때(로그인 붙기 전)의 자취를 정리하려면
       **하나씩 골라** 보고 지울 수 있어야 한다. wipe 는 전부 지워서 못 쓴다.
       열쇠는 PUSH_KEY 하나를 그대로 쓴다 (2026-08-30).
       ※ 지우기 전에 반드시 look 으로 **누가 들어 있는지** 보고 판단한다. */
    const admin = () => env.PUSH_KEY && cut(b.key, 64) === env.PUSH_KEY;

    if (act === 'look') {                                    // 동아리 하나를 들여다본다
      if (!admin()) return send({ error: 'no' });
      const id = cut(b.id, 24);
      const c = clubs[id];
      if (!c) return send({ error: '없는 동아리입니다' });
      const cu = JSON.parse((await KV.get(`cu:${id}`)) || '{}');
      return send({ id, name: c.name, owner: c.owner,
                    members: c.members || [], wait: c.wait || [],
                    uids: Object.entries(c.uids || {}).map(([u, n]) => ({ uid: u, nick: n })),
                    last: Object.entries(cu).map(([u, v]) => ({ uid: u, nick: v.nick || '',
                      days: (v.days || []).filter(Boolean).length, at: v.at || 0 })) });
    }

    if (act === 'delclub') {                                 // 동아리 하나만 지운다
      if (!admin()) return send({ error: 'no' });
      const id = cut(b.id, 24);
      const c = clubs[id];
      if (!c) return send({ error: '없는 동아리입니다' });
      const n = (c.members || []).length;
      delete clubs[id];
      await KV.put(CKEY, JSON.stringify(clubs));
      await KV.delete(`cu:${id}`);
      return send({ ok: true, name: c.name, members: n });
    }

    if (act === 'delacct') {                                 // 계정 하나만 지운다 (비밀번호 없이)
      if (!admin()) return send({ error: 'no' });
      const id = cut(b.id, 20).toLowerCase().trim();
      const AK = 'acct:' + id;
      const acct = JSON.parse((await KV.get(AK)) || 'null');
      if (!acct) return send({ error: '없는 아이디입니다' });
      const nicks = JSON.parse((await KV.get(NKEY)) || '{}');
      let nick = '';
      for (const [k, v] of Object.entries(nicks)) if (v === acct.u) { nick = k; delete nicks[k]; }
      await KV.put(NKEY, JSON.stringify(nicks));
      let touched = false;
      for (const cc of Object.values(clubs)) {
        if (cc.uids && cc.uids[acct.u]) {
          const nk = cc.uids[acct.u];
          delete cc.uids[acct.u];
          cc.members = (cc.members || []).filter(m => m !== nk);
          touched = true;
        }
      }
      if (touched) await KV.put(CKEY, JSON.stringify(clubs));
      await KV.delete('prog:' + id);
      await KV.delete(AK);
      return send({ ok: true, id, nick });
    }

    if (act === 'accts') {                                   // 아이디 목록 (누가 있는지 본다)
      if (!admin()) return send({ error: 'no' });
      const nicks = JSON.parse((await KV.get(NKEY)) || '{}');
      return send({ nicks: Object.entries(nicks).map(([n, u]) => ({ nick: n, uid: u })) });
    }

    if (act === 'wipe') {                                    // 관리자만 — 동아리를 전부 비운다
      if (!env.PUSH_KEY || cut(b.key, 64) !== env.PUSH_KEY) return send({ error: 'no' });
      const ids = Object.keys(clubs);
      for (const id of ids) await KV.delete(`cu:${id}`);
      await KV.put('clubs', '{}');
      return send({ ok: true, wiped: ids.length });
    }

    /* ── 계정 ─────────────────────────────────────────
       아이디+비밀번호로 어느 기기서든 같은 별명·같은 기록(동아리·엄지·사진)이 따라온다.
       비밀번호는 소금을 쳐서 으깬 값(해시)만 저장한다 — 원문은 어디에도 안 남는다.
       이메일이 없으므로 비밀번호를 잊으면 되찾을 길이 없다(가입 화면에 밝힌다). */
    const hashPw = async (salt, pw) => {
      const d = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(salt + '\u0001' + pw));
      return [...new Uint8Array(d)].map(x => x.toString(16).padStart(2, '0')).join('');
    };
    if (act === 'signup' || act === 'login') {
      const id = cut(b.id, 20).toLowerCase().trim();
      const pw = String(b.pw || '').slice(0, 64);
      if (!/^[a-z0-9_]{4,20}$/.test(id)) return send({ error: '아이디는 영문·숫자 4~20자입니다' });
      // 비밀번호 규칙은 NIST 지침을 따른다: 길이 8자 이상, 특수문자 강제는 하지 않는다
      // (강제 규칙은 오히려 뻔한 변형을 만든다는 것이 지침의 근거다). 기존 가입자는 그대로 들어온다.
      if (act === 'signup' && pw.length < 8) return send({ error: '비밀번호는 8자 이상입니다' });
      if (pw.length < 4) return send({ error: '비밀번호가 너무 짧습니다' });
      const AK = 'acct:' + id;
      const acct = JSON.parse((await KV.get(AK)) || 'null');
      if (act === 'signup') {
        if (acct) return send({ error: '이미 있는 아이디입니다' });
        const uid = cut(b.uid, 16);
        if (!nick || !uid) return send({ error: '별명을 먼저 정해 주세요' });
        const salt = Math.random().toString(36).slice(2, 12);
        // ui = 화면에 나올 말. 국적으로 짐작하지 않고 가입할 때 고른 것을 그대로 받는다
        const prof = { nat: cut(b.nat, 4), learn: cut(b.learn, 4), reg: cut(b.reg, 2),
                       ui: cut(b.ui, 4) };
        // 증표(token): 로그인한 사람만 자기 진도를 읽고 쓸 수 있게 하는 문패.
        // 비밀번호를 매번 보내지 않으려고 따로 둔다.
        const tok = [...crypto.getRandomValues(new Uint8Array(16))].map(x => x.toString(16).padStart(2, '0')).join('');
        await KV.put(AK, JSON.stringify({ s: salt, h: await hashPw(salt, pw), u: uid, p: prof, t: tok }));
        return send({ ok: true, uid, nick, prof, tok });
      }
      if (!acct) return send({ error: '없는 아이디입니다' });
      if (await hashPw(acct.s, pw) !== acct.h) return send({ error: '비밀번호가 다릅니다' });
      // 이 계정(uid)의 지금 별명을 찾아 준다
      const nicks = JSON.parse((await KV.get(NKEY)) || '{}');
      let myNick = '';
      for (const [k, v] of Object.entries(nicks)) if (v === acct.u) { myNick = k; break; }
      // 이 uid 가 들어 있는 동아리도 알려 준다 (기기를 바꿔도 동아리가 따라온다)
      let myClub = null;
      for (const [cid, cc] of Object.entries(clubs))
        if (cc.uids && cc.uids[acct.u]) { myClub = { id: cid, name: cc.name, nick: cc.uids[acct.u] }; break; }
      if (!acct.t) {                                        // 옛 가입자에게도 증표를 만들어 준다
        acct.t = [...crypto.getRandomValues(new Uint8Array(16))].map(x => x.toString(16).padStart(2, '0')).join('');
        await KV.put(AK, JSON.stringify(acct));
      }
      const hasProg = !!(await KV.get('prog:' + id, { type: 'text' }));
      return send({ ok: true, uid: acct.u, nick: myNick || (myClub && myClub.nick) || '',
                    club: myClub, prof: acct.p || null, tok: acct.t, hasProg });
    }

    /* ── 탈퇴 ────────────────────────────────────────
       비밀번호를 한 번 더 받고, **계정·진도·별명·동아리 자리를 모두 지운다.**
       떠나는 까닭은 이름 없이 세기만 한다 — 누가 왜 나갔는지가 아니라
       '무엇 때문에 나가는가'만 알면 고칠 수 있다. */
    if (act === 'quit') {
      const id = cut(b.id, 20).toLowerCase().trim();
      const pw = String(b.pw || '').slice(0, 64);
      const AK = 'acct:' + id;
      const acct = JSON.parse((await KV.get(AK)) || 'null');
      if (!acct) return send({ error: '없는 아이디입니다' });
      if (await hashPw(acct.s, pw) !== acct.h) return send({ error: '비밀번호가 다릅니다' });

      // 까닭 세기 — 이름도 아이디도 남기지 않는다
      const WHY = ['hard', 'easy', 'busy', 'bug', 'need', 'other'];
      const why = WHY.includes(b.why) ? b.why : '';
      if (why || b.memo) {
        const q = JSON.parse((await KV.get('quitwhy')) || '{"n":{},"memo":[]}');
        if (why) q.n[why] = (q.n[why] || 0) + 1;
        const memo = cut(b.memo, 200);
        if (memo) { q.memo.unshift({ w: why, m: memo, at: Date.now() }); q.memo = q.memo.slice(0, 200); }
        await KV.put('quitwhy', JSON.stringify(q));
      }

      // 별명 자리를 비운다 (다른 사람이 그 별명을 쓸 수 있게)
      const nicks = JSON.parse((await KV.get(NKEY)) || '{}');
      for (const [k, v] of Object.entries(nicks)) if (v === acct.u) delete nicks[k];
      await KV.put(NKEY, JSON.stringify(nicks));
      // 동아리에서 뺀다
      let touched = false;
      for (const cc of Object.values(clubs)) {
        if (cc.uids && cc.uids[acct.u]) {
          const nk = cc.uids[acct.u];
          delete cc.uids[acct.u];
          cc.members = (cc.members || []).filter(m => m !== nk);
          touched = true;
        }
      }
      if (touched) await KV.put(CKEY, JSON.stringify(clubs));
      // 전체 순위판에서도 지운다
      const g = JSON.parse((await KV.get(GKEY)) || '{}');
      if (g[acct.u]) { delete g[acct.u]; await KV.put(GKEY, JSON.stringify(g), TTL); }
      await KV.delete('prog:' + id);
      await KV.delete(AK);
      return send({ ok: true });
    }

    /* ── 동아리 순위 ─────────────────────────────────
       **구성원 개인 점수를 다 더한 값**이다 (사용자 지시).
       한 사람 평균은 내보내지 않는다 — 잣대가 둘이면 어느 쪽이 진짜 순위인지 알 수 없다.
       개인 점수는 전체 순위판(GKEY)에 uid 로 쌓여 있으므로, 동아리의 uid 목록으로 더한다. */
    if (act === 'ranks') {
      const g = JSON.parse((await KV.get(GKEY)) || '{}');
      const out = [];
      for (const [cid, cc] of Object.entries(clubs)) {
        const uids = Object.keys(cc.uids || {});
        let wk = 0, mo = 0;
        for (const u of uids) {
          const m = g[u];
          if (!m) continue;
          wk += num(m.s, 999999);                    // 이번 주 점수
          mo += num(m.mo, 999999) || num(m.s, 999999);
        }
        out.push({ id: cid, name: cc.name, n: uids.length || (cc.members || []).length,
                   city: cc.city || '', wk, mo });
      }
      out.sort((x, y) => y.wk - x.wk);
      return send({ clubs: out.slice(0, 50) });
    }

    /* ── 진도 서버 저장 ──────────────────────────────
       로그인한 사람만. 하루 한두 번 쓰기라 20~100명 규모는 무료 한도(쓰기 1,000/일) 안이다.
       더 커지면 D1 로 옮긴다 — 그때까지의 다리다. */
    if (act === 'save' || act === 'load') {
      const id = cut(b.id, 20).toLowerCase().trim();
      const acct = JSON.parse((await KV.get('acct:' + id)) || 'null');
      if (!acct || !acct.t || cut(b.tok, 40) !== acct.t) return send({ error: '로그인이 필요합니다' });
      const PK = 'prog:' + id;
      if (act === 'load') {
        const raw = await KV.get(PK, { type: 'text' });
        return send(raw ? JSON.parse(raw) : { data: null });
      }
      const body2 = JSON.stringify({ data: b.data || null, at: Date.now() });
      if (body2.length > 400000) return send({ error: '진도가 너무 큽니다' });
      await KV.put(PK, body2);
      return send({ ok: true, at: Date.now() });
    }

    if (act === 'clubs')                                     // 목록 (사람 많은 순)
      return send({ clubs: Object.entries(clubs)
        .map(([id, c]) => ({ id, name: c.name, n: c.members.length, approve: !!c.approve,
                             desc: c.desc || '', cat: c.cat || '', city: c.city || '' }))
        .sort((x, y) => y.n - x.n) });

    if (act === 'create') {                                  // 만들기
      if (!nick) return send({ error: '별명을 먼저 정해 주세요' });
      if (Object.keys(clubs).length >= MAX_CLUBS) return send({ error: '동아리가 너무 많습니다' });
      const name = cut(b.name, 20).trim();
      if (!name) return send({ error: '이름을 적어 주세요' });
      if (Object.values(clubs).some(c => c.name === name)) return send({ error: '같은 이름이 이미 있습니다' });
      const id = Math.random().toString(36).slice(2, 8);
      clubs[id] = { name, owner: nick, approve: !!b.approve, members: [nick], wait: [],
                    desc: cut(b.desc, 60).trim(),            // 한 줄 소개 (60자)
                    cat: cut(b.cat, 10),                     // 갈래 (앱이 정한 목록 중 하나)
                    city: cut(b.city, 6),                    // 만나는 도시 — 갈래보다 이게 먼저다
                    uids: cut(b.uid, 16) ? { [cut(b.uid, 16)]: nick } : {} };
      await save();
      return send({ id, name });
    }

    const GKEY = `r:${week()}`, TTL = { expirationTtl: 60 * 60 * 24 * 30 };
    const FIELDS = ['say', 'ear', 'read', 'spell', 'memo'];

    /* ── 폰 알림 ─────────────────────────────────────────────
       알림 주소(endpoint)만 들고 있는다. 그것으로는 누구인지 알 수 없다.
       내용 없는 신호만 보내므로 암호화 짐이 없다 — 무슨 말이 왔는지는 앱을 열어야 본다. */
    const SUBK = 'push:subs';
    if (act === 'sub') {
      const uid = cut(b.uid, 16);
      if (!uid || !b.sub || !b.sub.endpoint) return send({ error: 'bad sub' });
      const subs = JSON.parse((await KV.get(SUBK)) || '{}');
      subs[uid] = { e: cut(b.sub.endpoint, 512), t: 0 };     // t = 마지막으로 보낸 날
      await KV.put(SUBK, JSON.stringify(subs));
      return send({ ok: true });
    }
    if (act === 'unsub') {
      const uid = cut(b.uid, 16);
      const subs = JSON.parse((await KV.get(SUBK)) || '{}');
      if (subs[uid]) { delete subs[uid]; await KV.put(SUBK, JSON.stringify(subs)); }
      return send({ ok: true });
    }
    if (act === 'push') {                                    // 로봇만 부른다 (PUSH_KEY 필요)
      if (!env.PUSH_KEY || cut(b.key, 64) !== env.PUSH_KEY) return send({ error: 'no' });
      if (!env.VAPID_PRIV) return send({ error: 'VAPID_PRIV 없음' });
      const subs = JSON.parse((await KV.get(SUBK)) || '{}');
      const g = JSON.parse((await KV.get(GKEY)) || '{}');
      const today = new Date().toISOString().slice(0, 10);
      const DAY = 86400000, now = Date.now();
      let sent = 0, gone = 0, skipped = 0;
      for (const [uid, v] of Object.entries(subs)) {
        if (v.t === today) { skipped++; continue; }           // 하루 한 번까지만
        const me = g[uid];
        const idle = me && me.l ? Math.floor((now - Date.parse(me.l + 'T00:00:00Z')) / DAY) : 99;
        if (idle < 1) { skipped++; continue; }                // 오늘 이미 공부한 사람은 안 부른다
        if ((v.miss || 0) >= 3) { skipped++; continue; }      // 세 번 내리 안 읽으면 그 사람은 쉰다
        try {
          const r = await webpush(v.e, env.VAPID_PRIV);
          if (r.status === 404 || r.status === 410) { delete subs[uid]; gone++; continue; }
          v.t = today; v.miss = (v.miss || 0) + 1; sent++;    // 앱을 열면 sub 이 다시 와서 0으로 돌아간다
        } catch (e) { }
      }
      await KV.put(SUBK, JSON.stringify(subs));
      return send({ sent, gone, skipped, total: Object.keys(subs).length });
    }

    if (act === 'stats') {                                   // 운영 현황 — 숫자만, 이름 없음
      const g = JSON.parse((await KV.get(GKEY)) || '{}');
      const list = Object.values(g);
      const byDay = [0, 0, 0, 0, 0, 0, 0];
      list.forEach(v => (v.w || []).forEach((x, i) => { if (x) byDay[i]++; }));
      const s2 = list.map(v => v.s).sort((a, b) => a - b);
      const mid = s2.length ? s2[Math.floor(s2.length / 2)] : 0;
      const clubs2 = Object.values(clubs);

      // 깔때기 — 끝낸 세트가 몇 개인 사람이 몇 명인가. 사람들이 어디서 멈추는지 보인다.
      const FB = [0, 1, 3, 6, 11, 21];
      const funnel = [0, 0, 0, 0, 0, 0];
      list.forEach(v => {
        const n = v.st || 0;
        let i = 0; while (i + 1 < FB.length && n >= FB[i + 1]) i++;
        funnel[i]++;
      });

      // 코호트 — 시작한 지 N일 지난 사람 중 최근 사흘 안에 공부한 사람
      const DAY = 86400000, now = Date.now();
      const MARK = [1, 3, 7, 14, 30];
      const cohort = [0, 0, 0, 0, 0], alive = [0, 0, 0, 0, 0];
      list.forEach(v => {
        if (!v.f) return;
        const age = Math.floor((now - Date.parse(v.f + 'T00:00:00Z')) / DAY);
        const idle = v.l ? Math.floor((now - Date.parse(v.l + 'T00:00:00Z')) / DAY) : 999;
        MARK.forEach((m, i) => { if (age >= m) { cohort[i]++; if (idle <= 3) alive[i]++; } });
      });

      // 진짜 기억률 — 다시 볼 때가 된 카드를 첫 시도에 맞힌 비율 (간격 반복의 핵심 지표)
      const tr = list.reduce((a, v) => v.tr ? [a[0] + v.tr[0], a[1] + v.tr[1]] : a, [0, 0]);

      // 많은 사람이 틀리는 단어 — 커리큘럼을 고칠 직접 근거 (누가 틀렸는지는 안 남는다)
      const hard = {};
      list.forEach(v => (v.ms || []).forEach(w => { hard[w] = (hard[w] || 0) + 1; }));
      const hardWords = Object.entries(hard).filter(([, n]) => n >= 2)
        .sort((a, b) => b[1] - a[1]).slice(0, 15);
      return send({
        week: week(), people: list.length, byDay,
        active: list.filter(v => (v.w || []).reduce((a, x) => a + x, 0) > 0).length,
        started: list.filter(v => v.m > 0).length,          // 단어를 하나라도 외운 사람
        avgScore: s2.length ? Math.round(s2.reduce((a, x) => a + x, 0) / s2.length) : 0,
        midScore: mid,
        avgMemo: list.length ? Math.round(list.reduce((a, v) => a + v.m, 0) / list.length) : 0,
        clubs: clubs2.length, clubMembers: clubs2.reduce((a, c) => a + c.members.length, 0),
        funnel, cohort, alive, hardWords,
        trueRet: tr[1] ? Math.round(tr[0] * 100 / tr[1]) : 0, trueN: tr[1],
      });
    }

    if (act === 'rank') {                                    // 앱 전체 순위 + 전체 평균
      const uid = cut(b.uid, 16);
      if (!nick || !uid) return send({ error: '별명을 먼저 정해 주세요' });
      const g = JSON.parse((await KV.get(GKEY)) || '{}');
      const p = b.pct && typeof b.pct === 'object' ? b.pct : {};
      const mine = { n: nick, s: num(b.score, 999999), m: num(b.memo, 99999), p: {},
                     /* 앱 전체 순위의 재료 — 이번 주 점수와 한 달 점수.
                        전에는 실력 점수(s)로만 줄을 세웠다. 그건 '얼마나 잘하나'지
                        '얼마나 했나'가 아니다. 순위는 노력으로 매긴다(대표님 지시). */
                     cr: num(b.cr, 9999999), crm: num(b.crm, 9999999) };
      for (const k of FIELDS) if (typeof p[k] === 'number') mine.p[k] = num(p[k], 100);
      mine.w = (Array.isArray(b.days) ? b.days : []).slice(0, 7).map(x => x ? 1 : 0);
      mine.f = cut(b.f, 10); mine.l = cut(b.l, 10);          // 첫날 · 마지막 날
      mine.dd = num(b.dd, 9999); mine.st = num(b.st, 9999);  // 공부한 날 · 끝낸 세트
      if (Array.isArray(b.tr)) mine.tr = [num(b.tr[0], 99999), num(b.tr[1], 99999)];
      mine.ms = (Array.isArray(b.ms) ? b.ms : []).slice(0, 8).map(x => cut(x, 24));
      const was = g[uid];
      if (was && was.w) for (let i = 0; i < 7; i++) mine.w[i] = mine.w[i] || was.w[i] || 0;
      if (!was || was.n !== mine.n || was.s !== mine.s || was.m !== mine.m
          || was.cr !== mine.cr || was.crm !== mine.crm
          || String(was.w) !== String(mine.w)
          || JSON.stringify(was.p) !== JSON.stringify(mine.p)) {   // 바뀐 게 없으면 저장하지 않는다
        g[uid] = mine;
        let ent = Object.entries(g);
        if (ent.length > 2000) {                             // 너무 커지면 점수 낮은 쪽부터 잘라낸다
          ent = ent.sort((x, y) => y[1].s - x[1].s).slice(0, 2000);
          for (const k of Object.keys(g)) delete g[k];
          for (const [k, v] of ent) g[k] = v;
          g[uid] = mine;
        }
        await KV.put(GKEY, JSON.stringify(g), TTL);
      }
      const list = Object.entries(g).sort((x, y) => y[1].s - x[1].s);
      const rank = list.findIndex(([k]) => k === uid) + 1;
      /* 앱 전체에서 점수로 줄 세운다 — 이번 주와 한 달, 따로.
         내보내는 것은 **맨 위 셋의 별명·점수**와 **내 자리**뿐이다.
         4등 아래는 이름도 등수도 내보내지 않는다 — 자기 등수는 자기만 본다. */
      const board = f => {
        const L = Object.entries(g).filter(([, x]) => typeof x[f] === 'number' && x[f] > 0)
                        .sort((x, y) => y[1][f] - x[1][f]);
        const at = L.findIndex(([k]) => k === uid);
        return { top: L.slice(0, 3).map(([, x]) => ({ n: x.n, v: x[f] })),
                 rank: at < 0 ? 0 : at + 1, total: L.length,
                 mine: (g[uid] || {})[f] || 0 };
      };
      const avg = {};
      for (const k of FIELDS) {
        const v = list.map(([, x]) => x.p[k]).filter(x => typeof x === 'number');
        if (v.length >= 3) avg[k] = Math.round(v.reduce((a, x) => a + x, 0) / v.length);
      }
      const scores = list.map(([, x]) => x.s);
      // 남의 등수도 이름도 내보내지 않는다 — 나가는 것은 내 자리와 전체 평균뿐이다
      return send({
        rank, total: list.length,
        pct: list.length >= 3 ? Math.max(1, Math.round(rank * 100 / list.length)) : 0,
        avgScore: scores.length ? Math.round(scores.reduce((a, x) => a + x, 0) / scores.length) : 0,
        avgMemo: list.length ? Math.round(list.reduce((a, [, x]) => a + x.m, 0) / list.length) : 0,
        avg, myScore: mine.s, myMemo: mine.m, myPct: mine.p,
        week: board('cr'), month: board('crm'),        // 앱 전체 점수 순위
      });
    }

    /* ── 프로필 사진 ──────────────────────────────────────
       작게 줄여 온 것만 받는다(글자 16000개 ≒ 12KB). 사람마다 키 하나. */
    if (act === 'setface') {
      const img = cut(b.img, 16000), uid = cut(b.uid, 16);
      if (!uid) return send({ error: 'no uid' });
      if (!img) { await KV.delete(`av:${uid}`); return send({ ok: true }); }
      if (!img.startsWith('data:image/')) return send({ error: '사진이 아닙니다' });
      await KV.put(`av:${uid}`, img);
      return send({ ok: true });
    }
    if (act === 'face') {                                    // 남의 사진 받아 오기 (한 번에 여럿)
      const want = (Array.isArray(b.uids) ? b.uids : []).slice(0, 30).map(x => cut(x, 16));
      const out = {};
      for (const u of want) out[u] = (await KV.get(`av:${u}`)) || '';
      return send({ face: out });
    }

    const id = cut(b.id, 12), c = clubs[id];
    if (!c) return send({ error: 'gone' });                  // 정말로 사라진 동아리 (이때만 'gone')
    c.wait = c.wait || [];
    c.uids = c.uids || {};
    /* 사람을 붙드는 것은 **기기 표(uid)** 다. 별명은 얼굴 이름일 뿐이라 바뀐다.
       명단에 옛 이름이 남아 있으면 여기서 조용히 고쳐 준다. */
    const myUid = cut(b.uid, 16);
    if (myUid && c.uids[myUid] && c.uids[myUid] !== nick && nick) {
      const was = c.uids[myUid];
      c.uids[myUid] = nick;
      c.members = c.members.map(x => (x === was ? nick : x));
      c.wait = c.wait.map(x => (x === was ? nick : x));
      if (c.owner === was) c.owner = nick;
      await save();
    }

    if (act === 'join') {
      if (c.members.includes(nick)) return send({ ok: true, state: 'member' });
      // 여러 동아리에 겹쳐 들어갈 수 있다 (사용자 지시로 하나 제한을 풀었다)
      if (c.members.length >= 100) return send({ error: '정원이 찼습니다 (100명)' });
      if (myUid) c.uids[myUid] = nick;
      if (c.approve) { if (!c.wait.includes(nick)) { c.wait.push(nick); } await save(); }
      else { c.members.push(nick); await save(); }
      return send({ ok: true, state: c.approve ? 'wait' : 'member' });
    }

    if (act === 'accept' && c.owner === nick) {              // 개설자가 승인
      const who = cut(b.who, 10);
      c.wait = c.wait.filter(x => x !== who);
      if (!c.members.includes(who)) c.members.push(who);
      await save();
      return send({ ok: true });
    }

    /* ── 오늘 한 줄 (동아리 담벼락) ─────────────────────
       쪽지(1:1)보다 커뮤니티를 만드는 것은 담벼락이다. 최근 50개, 30일 뒤 삭제.
       글 하나 = KV 쓰기 1번이라 무료 한도 안에서 넉넉하다. */
    const FDK = 'fd:' + id, FTTL = { expirationTtl: 60 * 60 * 24 * 30 };
    if (act === 'feed') {
      if (!c.members.includes(nick)) return send({ error: 'notmember' });
      return send({ posts: JSON.parse((await KV.get(FDK)) || '[]') });
    }
    if (act === 'post') {
      if (!c.members.includes(nick)) return send({ error: 'notmember' });
      const x = cut(b.x, 200).trim();
      if (!x) return send({ error: '내용이 없습니다' });
      const posts = JSON.parse((await KV.get(FDK)) || '[]');
      posts.push({ f: cut(b.uid, 16), n: nick, x, t: Date.now() });
      await KV.put(FDK, JSON.stringify(posts.slice(-50)), FTTL);
      return send({ ok: true, posts: posts.slice(-50) });
    }

    if (act === 'leave') {
      if (myUid) delete c.uids[myUid];
      c.members = c.members.filter(x => x !== nick);
      c.wait = c.wait.filter(x => x !== nick);
      if (!c.members.length) delete clubs[id];               // 아무도 없으면 동아리를 지운다
      else if (c.owner === nick) c.owner = c.members[0];     // 방장이 나가면 다음 사람에게
      await save();
      return send({ ok: true });
    }

    /* ── 동아리 사람들 ────────────────────────────────────
       예전에는 별명으로 줄을 세웠는데, 별명은 바뀌고 겹친다.
       이제 사람은 uid(기기마다 다른 표)로 구분하고 별명은 얼굴 이름일 뿐이다.
       한 동아리의 사람들을 **키 하나**에 모아 둔다 — KV 는 하루 쓰기 1000번뿐이라
       사람마다 키를 따로 두면 금방 바닥난다. */
    const CUK = `cu:${id}`, CTTL = { expirationTtl: 60 * 60 * 24 * 90 };
    const readCu = async () => JSON.parse((await KV.get(CUK)) || '{}');
    const uid = cut(b.uid, 16);

    if (act === 'report') {                                  // 내 현황 올리고 사람 목록 받기
      // 기기 표가 명단에 있으면 회원이다. 이름이 어긋난 것만으로 내보내지 않는다.
      if (!c.members.includes(nick)) {
        if (myUid && c.uids[myUid]) { c.members.push(nick); c.uids[myUid] = nick; await save(); }
        else return send({ error: 'notmember' });            // 'gone' 이 아니다 — 동아리는 살아 있다
      }
      if (!uid) return send({ error: 'no uid' });
      const cu = await readCu();
      const was = cu[uid] || {};
      const mine = {
        n: nick,
        w: (Array.isArray(b.days) ? b.days : []).slice(0, 7).map(x => x ? 1 : 0),
        wk: week(),                                          // 지난주 도장은 저절로 지워진다
        m: num(b.memo, 99999), s: num(b.score, 999999),
        /* 점수를 저장한다. 앱은 진작부터 보내고 있었는데 여기서 버리고 있었다 —
           그래서 순위가 점수가 아니라 '이번 주 출석 도장'으로 매겨졌고,
           한 달 순위는 재료가 없어 아예 안 나왔다 (대표님 지적, 2026-08-29). */
        cr: num(b.cr, 9999999), crm: num(b.crm, 9999999),
        st: num(b.st, 9999), td: num(b.td, 99999),           // 연속으로 온 날 · 온 날 모두
        op: b.op ? 1 : 0,                                    // 분석을 남에게 보일지
        av: num(b.av, 9999),                                 // 사진 판 번호 (남이 다시 받을지 판단)
        th: was.th || 0, tb: was.tb || {},                   // 받은 엄지 · 누가 언제 눌렀나
        bl: (Array.isArray(b.bl) ? b.bl : (was.bl || [])).slice(0, 50).map(x => cut(x, 16)),
        at: today(),
      };
      const p = b.pct && typeof b.pct === 'object' ? b.pct : {};
      mine.p = {};
      for (const k of FIELDS) if (typeof p[k] === 'number') mine.p[k] = num(p[k], 100);
      cu[uid] = mine;
      // 같은 사람이 폰·컴퓨터 두 대로 들어오면 기기표(uid)가 둘이라 명단에 두 번 떴다.
      // 별명이 같으면 같은 사람이다 — 방금 온 기기만 남긴다.
      for (const k of Object.keys(cu)) if (k !== uid && cu[k].n === nick) delete cu[k];
      for (const k of Object.keys(cu)) if (!c.members.includes(cu[k].n)) delete cu[k];
      // 바뀐 게 없으면 저장하지 않는다 (하루 쓰기 1000번을 아낀다)
      if (JSON.stringify(was) !== JSON.stringify(mine)) await KV.put(CUK, JSON.stringify(cu), CTTL);
      return send(Object.assign(dirOf(cu, c, uid), { inbox: await inboxOf(KV, uid) }));
    }

    if (act === 'dir') {                                     // 목록만 다시 받기 (안 쓰고 읽기만)
      const cu = await readCu();
      return send(Object.assign(dirOf(cu, c, uid), { inbox: await inboxOf(KV, uid) }));
    }

    if (act === 'thumb') {                                   // 엄지척 — 한 사람에게 하루 한 번
      const to = cut(b.to, 16);
      const cu = await readCu();
      if (!cu[uid] || !cu[to] || to === uid) return send({ error: '없는 사람입니다' });
      cu[to].tb = cu[to].tb || {};
      if (cu[to].tb[uid] === today()) return send({ error: '오늘은 이미 눌렀습니다', th: cu[to].th || 0 });
      cu[to].tb[uid] = today();
      cu[to].th = (cu[to].th || 0) + 1;
      await KV.put(CUK, JSON.stringify(cu), CTTL);
      return send({ ok: true, th: cu[to].th });
    }

    /* ── 쪽지 ────────────────────────────────────────────
       같은 동아리 사람끼리만. 한 짝의 대화가 키 하나이고 최근 60줄만 남는다.
       받는 쪽에게는 '누구한테 뭔가 왔다'는 표시만 따로 적어 둔다(mb:) —
       그래야 방을 안 열어 봐도 빨간 표가 뜬다. */
    const pairKey = (x, y) => 'dm:' + [x, y].sort().join('~');
    if (act === 'dm') {
      const to = cut(b.to, 16);
      const list = JSON.parse((await KV.get(pairKey(uid, to))) || '[]');
      return send({ msgs: list });
    }
    if (act === 'say') {
      const to = cut(b.to, 16), x = cut(b.x, 300).trim();
      if (!x) return send({ error: '빈 쪽지' });
      const cu = await readCu();
      if (!cu[uid] || !cu[to]) return send({ error: '같은 동아리 사람에게만 보낼 수 있습니다' });
      if ((cu[to].bl || []).includes(uid)) return send({ error: '이 사람에게는 보낼 수 없습니다' });
      const k = pairKey(uid, to);
      const list = JSON.parse((await KV.get(k)) || '[]');
      list.push({ f: uid, t: Date.now(), x });
      await KV.put(k, JSON.stringify(list.slice(-60)), { expirationTtl: 60 * 60 * 24 * 30 });
      const mb = JSON.parse((await KV.get(`mb:${to}`)) || '{}');
      mb[uid] = Date.now();
      await KV.put(`mb:${to}`, JSON.stringify(mb), { expirationTtl: 60 * 60 * 24 * 30 });
      return send({ ok: true, msgs: list.slice(-60) });
    }

    return send({ error: 'bad act' });
  },
};
