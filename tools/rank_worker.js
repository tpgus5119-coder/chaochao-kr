/* 순위 서버 (Cloudflare Worker + KV) — 나중에 순위를 켤 때 쓴다.
   설정: Worker 하나 더 만들고 이 코드를 붙인 뒤, KV 네임스페이스를 만들어 RANK 라는 이름으로 묶는다.
   앱은 {nick, week, score} 를 보내고 {rank, total, pct, top} 을 받는다.
   개인정보는 별명뿐이고, 등수는 본인에게만 돌려준다(상위 5명만 이름이 공개된다). */
export default {
  async fetch(req, env) {
    const origin = req.headers.get('Origin') || '';
    const allowed = ['https://tpgus5119-coder.github.io', 'http://localhost:8899'].includes(origin);
    const cors = { 'Access-Control-Allow-Origin': allowed ? origin : 'null',
                   'Access-Control-Allow-Methods': 'POST, OPTIONS',
                   'Access-Control-Allow-Headers': 'Content-Type' };
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors });
    if (req.method !== 'POST' || !allowed)
      return new Response('{"error":"blocked"}', { status: 403, headers: cors });

    const { nick, week, score } = await req.json();
    if (!nick || !week || typeof score !== 'number')
      return new Response('{"error":"bad"}', { status: 400, headers: cors });

    const key = 'w:' + week.slice(0, 10);
    const board = JSON.parse((await env.RANK.get(key)) || '{}');
    board[String(nick).slice(0, 10)] = Math.max(0, Math.min(99999, Math.round(score)));
    await env.RANK.put(key, JSON.stringify(board), { expirationTtl: 60 * 60 * 24 * 60 });

    const list = Object.entries(board).sort((a, b) => b[1] - a[1]);
    const rank = list.findIndex(([n]) => n === nick) + 1;
    return new Response(JSON.stringify({
      rank, total: list.length,
      pct: Math.max(1, Math.round(rank * 100 / list.length)),
      top: list.slice(0, 5).map(([n, s]) => ({ nick: n, score: s })),
    }), { headers: { ...cors, 'Content-Type': 'application/json' } });
  },
};
