/* AI 중계 서버 (Cloudflare Worker에 붙여넣는 코드) — v4 「열쇠 하나로 버티기」
   하는 일: 앱의 요청을 받아 → 금고에 든 열쇠를 붙여 → AI 회사로 전달.
   열쇠는 이 서버 밖으로 절대 안 나간다. 우리 앱에서 온 요청만 받는다.

   v4에서 바뀐 것 (대표님 지시: 쓸 수 있는 열쇠가 하나뿐이다)
     ① 모델 이름을 **적어 두지 않는다.** 구글에 "이 열쇠로 쓸 수 있는 걸 다 대라"고
        물어서 받아 쓴다. 내가 짐작으로 적은 이름 때문에 헛걸음하던 것을 없앴다.
        무료 몫은 **모델마다 따로** 걸리므로, 열쇠가 하나여도 모델이 열이면 열 몫이다.
     ② 구글이 다 막히면 **다른 회사**로 넘어간다. 공짜로 쓸 수 있는 곳만 골랐다.
     ③ 소리(발음 채점)는 대체 경로에서도 산다 — 받아 적은 뒤 글 모델에게 채점시킨다.

   금고(Settings → Variables and Secrets)에 넣는 것
     GEMINI_KEY     — 필수. 구글 열쇠. 여러 개면 **쉼표든 줄바꿈이든** 상관없다.
                      (사고 이력: 화면에 `AIza...uMQA` 로 가려진 글자를 그대로 복사해 넣어
                       열한 글자짜리 다섯 개가 들어갔다. 그래서 모양 검사에서 그것부터 본다.)
     GROQ_KEY       — 선택. https://console.groq.com  (공짜, 카드 안 걸어도 됨)
     OPENROUTER_KEY — 선택. https://openrouter.ai     (공짜 모델만 쓴다)
   바인딩(Settings → Bindings → Add → Workers AI, 이름 AI)
     AI             — 선택. 이 서버가 도는 그 계정이다. 가입도 카드도 필요 없다. */

/* ── 구글 모델 목록: 물어서 받는다 ────────────────────────────────────────
   왜 물어보나: 이름을 손으로 적어 두면 구글이 새 모델을 내거나 옛 모델을 없앨 때
   따라가지 못한다. 실제로 내가 적어 둔 여섯 개 중 몇이 실재하는지도 확인 못 했었다.
   목록 조회는 **생성 몫을 한 개도 안 쓴다**(공짜). 30분에 한 번만 새로 묻는다. */
let CACHE = { at: 0, list: [] };
const TTL = 30 * 60 * 1000;

/* 말을 주고받는 모델만 남긴다.
   실제 목록(36개)을 받아 보고 정한 것이다 — 짐작이 아니다. 걸러 내는 것들:
     -image · nano-banana · lyria  → 그림·음악을 만드는 모델. 글을 못 준다.
     transcribe                    → 받아 적기만 한다. 채점 지시를 안 따른다.
     deep-research · antigravity   → 오래 걸리는 조사용. 채점 한 줄에 쓸 것이 아니다.
     computer-use · robotics       → 화면·로봇 조종용.
     customtools                   → 도구 호출 전용 변종.
   gemma 는 남긴다 — 같은 열쇠로 공짜고 하루 몫이 **따로** 걸린다(글 작업에 큰 보탬).
   대신 귀가 없어서 소리를 보내면 400 을 뱉는데, BUSY 에 400 이 있으니 알아서 넘어간다. */
const SKIP = /embedding|aqa|imagen|veo|tts|image|lyria|nano-banana|deep-research|computer-use|robotics|antigravity|transcribe|customtools/i;
/* 한 번 부를 때 최대 몇 모델까지 훑나. 목록이 18개인데 다 훑으면 앱이 기다리다 지친다.
   막힌 모델은 빨리 답하므로(429·400) 열둘이면 몫 큰 lite 까지 닿는다. 그 뒤는 예비가 받는다. */
const MAX_TRY = 12;
/* 차례: 좋은 것 먼저. 앞엣것이 붐빌 때만 뒤로 밀린다.
   점수가 낮을수록 먼저 간다.
     · flash → flash-lite → 나머지 → gemma → pro
     · 같은 등급이면 판 번호가 높은 것 먼저 (3.5 > 3.1 > 2.5)
   preview·exp 도 버리지 않는다 — 몫이 **따로** 걸리므로 그만큼 하루가 늘어난다. */
function rank(n) {
  const ver = parseFloat((n.match(/[\d.]+/) || ['0'])[0]) || 0;
  let tier = 3;
  if (/pro/.test(n)) tier = 9;          // pro 는 무료 몫이 가장 작다 — 맨 뒤
  else if (/gemma/.test(n)) tier = 5;   // 몫은 크지만 글솜씨가 아래다 — pro 앞
  else if (/flash-lite/.test(n)) tier = 1;
  else if (/flash/.test(n)) tier = 0;
  const raw = /preview|exp/.test(n) ? 5 : 0;       // 정식판을 앞에, 미리보기는 그 뒤
  return tier * 100 + raw - ver;
}
async function models(key) {
  if (CACHE.list.length && Date.now() - CACHE.at < TTL) return CACHE.list;
  try {
    const r = await fetch(
      'https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000&key=' + key);
    if (r.ok) {
      const list = ((await r.json()).models || [])
        .filter(m => (m.supportedGenerationMethods || []).includes('generateContent'))
        .map(m => m.name.replace('models/', ''))
        .filter(n => !SKIP.test(n))
        .sort((a, b) => rank(a) - rank(b));
      if (list.length) { CACHE = { at: Date.now(), list }; return list; }
    }
  } catch (e) { /* 못 물어봤으면 아래 최소 목록으로 간다 */ }
  // 구글에 못 물어봤을 때의 최소한. 계기판에서 실제로 돈 것이 확인된 이름만 둔다.
  return CACHE.list.length ? CACHE.list : ['gemini-2.5-flash', 'gemini-2.5-flash-lite'];
}

/* ── 구글이 막혔을 때 갈 곳 ──────────────────────────────────────────────
   OpenAI 꼴로 말하는 곳들이라 한 가지 코드로 다 된다.
   공짜 조건이 확실한 것만 넣었다. 열쇠가 없으면 그 줄은 통째로 건너뛴다. */
const ALT = [
  { env: 'GROQ_KEY', url: 'https://api.groq.com/openai/v1/chat/completions',
    ms: ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant'] },
  { env: 'OPENROUTER_KEY', url: 'https://openrouter.ai/api/v1/chat/completions',
    ms: ['meta-llama/llama-3.3-70b-instruct:free', 'google/gemma-2-9b-it:free'] },
];
/* 마지막 자리 — 이 서버가 도는 그 계정. 가입도 카드도 필요 없다.
   **작은 것을 앞에 둔다.** 여기가 하는 일은 잘 채점하는 게 아니라 앱이 안 죽게 하는 것이다.
   하루 몫(뉴런)이 하나로 묶여 있어서, 큰 모델을 앞에 두면 같은 몫으로 받는 사람이 확 준다.
   8b 로 하루 약 2,700번(들어감 400·나옴 150 토큰 기준). 큰 모델은 그보다 훨씬 적다. */
const CF = ['@cf/meta/llama-3.1-8b-instruct', '@cf/meta/llama-3.3-70b-instruct-fp8-fast'];

/* '이 모델로는 안 된다' 는 신호 — 전부 '다음으로' 가 정답이다.
     429·5xx = 붐빔   404 = 없는 모델   403 = 이 열쇠로는 못 씀
     400     = 그 모델이 우리 요청을 안 받는다(예: 소리를 못 듣는 모델)
   400 을 뺐다가 사고가 났다: 붐벼서 밀린 요청이 400 을 맞고 그 자리에서 죽었다. */
const BUSY = [400, 403, 404, 429, 500, 502, 503, 504];

const J = (o, s, h) => new Response(JSON.stringify(o, null, 1),
  { status: s || 200, headers: { ...(h || {}), 'Content-Type': 'application/json; charset=utf-8' } });

/* ── 소리를 글로 옮긴다 ──────────────────────────────────────────────────
   왜 필요한가: 대체 모델들은 귀가 없다. 글만 읽는다. 그런데 우리 앱에서 AI를 가장
   많이 쓰는 곳이 **발음 채점**이다. 그래서 소리는 먼저 받아 적고, 받아 적은 글을
   원래 채점 지시와 함께 글 모델에게 넘긴다. 채점 지시는 손대지 않는다. */
async function hear(b64, env) {
  const bin = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  if (env.GROQ_KEY) {
    try {
      const fd = new FormData();
      fd.append('file', new File([bin], 'a.wav', { type: 'audio/wav' }));
      fd.append('model', 'whisper-large-v3-turbo');
      fd.append('language', 'vi');
      const r = await fetch('https://api.groq.com/openai/v1/audio/transcriptions',
        { method: 'POST', headers: { Authorization: 'Bearer ' + env.GROQ_KEY.trim() }, body: fd });
      if (r.ok) { const t = (await r.json()).text; if (t) return t.trim(); }
    } catch (e) { /* 다음 곳으로 */ }
  }
  if (env.AI) {
    try {
      const o = await env.AI.run('@cf/openai/whisper', { audio: [...bin] });
      if (o && o.text) return o.text.trim();
    } catch (e) { /* 포기 */ }
  }
  return '';
}

/* 구글 꼴 요청을 OpenAI 꼴 대화로 옮긴다. 소리는 위에서 받아 적어 글로 끼워 넣는다.
   사진은 옮기지 않는다 — 손글씨 비교는 대체 모델의 눈으로는 못 한다(솔직히 못 한다). */
async function toChat(body, env) {
  const j = JSON.parse(body);
  const parts = (j.contents || []).flatMap(c => c.parts || []);
  let text = '';
  for (const p of parts) {
    const d = p.inline_data || p.inlineData;
    if (!d) { text += (p.text || '') + '\n'; continue; }
    const mime = d.mime_type || d.mimeType || '';
    if (!mime.startsWith('audio')) return null;                  // 사진 → 대체 불가
    const heard = await hear(d.data, env);
    if (!heard) return null;
    text += `\n(학습자가 말한 것을 받아 적으면: "${heard}")\n`;
  }
  text = text.trim();
  if (!text) return null;
  return { messages: [{ role: 'user', content: text }],
           max_tokens: (j.generationConfig || {}).maxOutputTokens || 400 };
}

// 구글이 주는 답 모양으로 되돌린다 — 앱은 이 모양만 읽을 줄 안다.
const asGoogle = (txt, by) =>
  ({ candidates: [{ content: { parts: [{ text: txt }] }, finishReason: 'STOP' }], _by: by });

export default {
  async fetch(req, env) {
    const origin = req.headers.get('Origin') || '';
    const allowed = [
      'https://tpgus5119-coder.github.io',   // 배포된 앱
      'http://localhost:8899',               // 개발 확인용
    ].includes(origin);
    const cors = {
      'Access-Control-Allow-Origin': allowed ? origin : 'null',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors });

    const keys = (env.GEMINI_KEY || '').split(/[,\s]+/).map(k => k.trim()).filter(Boolean);
    const q = new URL(req.url).searchParams;

    /* ?health=1 — **찔러 보지 말고 물어본다.**
       열쇠가 살았는지, 이 열쇠로 쓸 수 있는 모델이 몇인지, 대체 경로가 걸렸는지.
       생성 몫을 한 개도 안 쓴다. 열쇠도 그 조각도 내보내지 않는다.
       주소: https://viet-ai.chaochao-app.workers.dev/?health=1 */
    if (q.get('health') === '1') {
      const rows = [];
      let live = [];
      for (let i = 0; i < keys.length; i++) {
        const k = keys[i];
        let st = 0, n = 0, why = '';
        try {
          const r = await fetch(
            'https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000&key=' + k);
          st = r.status;
          if (r.ok) {
            const ms = ((await r.json()).models || [])
              .filter(m => (m.supportedGenerationMethods || []).includes('generateContent'))
              .map(m => m.name.replace('models/', '')).filter(x => !SKIP.test(x));
            n = ms.length;
            if (ms.length > live.length) live = ms.sort((a, b) => rank(a) - rank(b));
          } else why = (((await r.json()) || {}).error || {}).message || '';
        } catch (e) { why = String(e); }
        rows.push({ 열쇠: i + 1, 살았나: st === 200, 상태: st,
                    글자수: k.length,
                    모양: k.includes('...') ? '가림표를 복사하셨습니다 — 복사 아이콘(⧉)을 쓰세요'
                        : k.length < 20 ? '너무 짧습니다 — 잘려서 붙은 것 같습니다' : '길이는 괜찮습니다',
                    쓸수있는모델: n, 까닭: why.slice(0, 140) });
      }
      return J({
        열쇠: rows,
        살아있는열쇠: rows.filter(r => r.살았나).length + '/' + keys.length,
        쓸수있는_구글모델_차례대로: live,
        구글모델수: live.length,
        예비: { groq: !!env.GROQ_KEY, openrouter: !!env.OPENROUTER_KEY, cloudflare: !!env.AI },
        읽는법: '상태 200이면 열쇠가 살아 있다. 구글모델수가 하루 몫의 배수다 '
              + '(몫은 모델마다 따로 걸린다). 예비가 전부 false면 구글이 막히는 순간 앱도 멈춘다.',
      });
    }

    /* ?ping=1 — 대체 경로가 **진짜로** 답하는지 한 번 시켜 본다.
       health 는 물어보기만 하지만 이건 실제로 한 마디 시킨다(아주 짧게).
       주소: https://viet-ai.chaochao-app.workers.dev/?ping=1 */
    if (q.get('ping') === '1') {
      const out = {};
      const ask = { messages: [{ role: 'user', content: 'Reply with the single word: ok' }], max_tokens: 5 };
      for (const a of ALT) {
        if (!env[a.env]) { out[a.env] = '열쇠 없음'; continue; }
        try {
          const r = await fetch(a.url, {
            method: 'POST',
            headers: { Authorization: 'Bearer ' + env[a.env].trim(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: a.ms[0], ...ask }) });
          const t = await r.text();
          out[a.env] = r.ok ? '됨: ' + t.slice(0, 80) : r.status + ' ' + t.slice(0, 140);
        } catch (e) { out[a.env] = String(e).slice(0, 140); }
      }
      if (!env.AI) out.cloudflare = '바인딩 없음';
      else try {
        const o = await env.AI.run(CF[0], ask);
        out.cloudflare = '됨: ' + String((o || {}).response || '').slice(0, 80);
      } catch (e) { out.cloudflare = String(e).slice(0, 140); }
      return J(out);
    }

    if (req.method !== 'POST' || !allowed)
      return new Response('{"error":"blocked"}', { status: 403, headers: cors });

    const body = await req.text();
    if (body.length > 1_000_000)             // 녹음·사진 포함 최대 1MB
      return new Response('{"error":"too big"}', { status: 413, headers: cors });
    if (!keys.length) return J({ error: 'no key' }, 500, cors);

    /* ① 구글 — 열쇠로 쓸 수 있는 모델을 좋은 것부터 훑는다.
       한 바퀴만 돈다. 앱도 세 번 재시도하므로 여기서 더 돌면 몫이 순식간에 바닥난다. */
    const list = (await models(keys[0])).slice(0, MAX_TRY);
    let r = null, first = null;
    for (const model of list) {
      for (let k = 0; k < keys.length; k++) {
        r = await fetch(
          `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=`
            + keys[k],
          { method: 'POST', headers: { 'Content-Type': 'application/json' }, body });
        if (!r.ok && !first) first = { status: r.status, text: await r.clone().text() };
        if (!BUSY.includes(r.status)) break;
      }
      if (!BUSY.includes(r.status)) break;
    }
    if (r && r.ok)
      return new Response(await r.text(),
        { status: 200, headers: { ...cors, 'Content-Type': 'application/json' } });

    /* ② 구글이 다 막혔다 — 다른 회사로. 소리는 받아 적어서 글로 바꿔 넘긴다.
       사진(손글씨 비교)은 넘기지 않는다. 대체 모델의 눈으로는 제대로 못 본다. */
    let chat = null;
    try { chat = await toChat(body, env); } catch (e) { chat = null; }
    if (chat) {
      for (const a of ALT) {
        if (!env[a.env]) continue;
        for (const m of a.ms) {
          try {
            const rr = await fetch(a.url, {
              method: 'POST',
              headers: { Authorization: 'Bearer ' + env[a.env].trim(), 'Content-Type': 'application/json' },
              body: JSON.stringify({ model: m, ...chat }) });
            if (!rr.ok) continue;
            const t = (((await rr.json()).choices || [])[0] || {}).message;
            if (t && t.content)
              return J(asGoogle(t.content, a.env.replace('_KEY', '').toLowerCase()), 200, cors);
          } catch (e) { /* 다음 모델 */ }
        }
      }
      if (env.AI) for (const m of CF) {
        try {
          const o = await env.AI.run(m, chat);
          const t = o && (o.response || o.result);
          if (t) return J(asGoogle(String(t), 'cloudflare'), 200, cors);
        } catch (e) { /* 다음 모델 */ }
      }
    }

    // 끝내 실패했으면 **맨 처음** 에러를 돌려준다.
    // 마지막 예비가 뱉은 엉뚱한 말보다 첫 모델의 답이 원인에 가깝다.
    return new Response(first ? first.text : (r ? await r.text() : '{"error":"failed"}'), {
      status: first ? first.status : (r ? r.status : 500),
      headers: { ...cors, 'Content-Type': 'application/json' },
    });
  },
};
