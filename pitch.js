'use strict';
/* 성조 판정기.
   음성인식(무슨 말인지 알아내기)이 아니라 **음높이(F0) 곡선**만 뽑는다.
   성조는 "소리가 오르내리는 모양"이므로, 무슨 단어인지 몰라도 모양은 잴 수 있다.
   이게 음성인식보다 훨씬 정확하고 가볍다.

   방법: YIN 알고리즘(차이함수 + 누적평균정규화). 반옥타브 오류가 적다.
   화자마다 목소리 높이가 다르므로 **각자의 중앙값 기준 반음(semitone) 차이**로 바꿔
   남녀·고저 차이를 없앤다. 그래야 원어민과 내 소리를 겹쳐 볼 수 있다. */

const PITCH = (() => {
  const FMIN = 60, FMAX = 500;

  /* 한 조각에서 기본주파수 하나 */
  function yin(buf, rate, thr = 0.12) {
    const tauMin = Math.floor(rate / FMAX), tauMax = Math.floor(rate / FMIN);
    const n = buf.length, half = Math.min(tauMax, n >> 1);
    const d = new Float32Array(half + 1);
    for (let tau = 1; tau <= half; tau++) {
      let s = 0;
      for (let i = 0; i < n - tau; i++) { const x = buf[i] - buf[i + tau]; s += x * x; }
      d[tau] = s;
    }
    // 누적평균정규화
    const cmnd = new Float32Array(half + 1);
    cmnd[0] = 1; let run = 0;
    for (let tau = 1; tau <= half; tau++) {
      run += d[tau];
      cmnd[tau] = run ? d[tau] * tau / run : 1;
    }
    let tau = -1;
    for (let t = tauMin; t <= half; t++) {
      if (cmnd[t] < thr) {
        while (t + 1 <= half && cmnd[t + 1] < cmnd[t]) t++;
        tau = t; break;
      }
    }
    if (tau < 0) {                       // 임계값을 못 넘으면 최솟값
      let best = tauMin, bv = cmnd[tauMin] ?? 1;
      for (let t = tauMin; t <= half; t++) if (cmnd[t] < bv) { bv = cmnd[t]; best = t; }
      if (bv > 0.55) return 0;           // 너무 흐리면 무성음으로 본다
      tau = best;
    }
    // 포물선 보간으로 소수점까지
    const a = cmnd[tau - 1] ?? cmnd[tau], b = cmnd[tau], c = cmnd[tau + 1] ?? cmnd[tau];
    const shift = (a + c - 2 * b) ? (a - c) / (2 * (a + c - 2 * b)) : 0;
    return rate / (tau + shift);
  }

  /* 소리 전체의 음높이 곡선. 무성음·소리 없는 구간은 null */
  function contour(samples, rate) {
    const win = Math.round(rate * 0.045);      // 45ms 창
    const hop = Math.round(rate * 0.010);      // 10ms 간격
    const out = [];
    let peak = 0;
    for (let i = 0; i < samples.length; i++) { const a = Math.abs(samples[i]); if (a > peak) peak = a; }
    const floor = Math.max(0.012, peak * 0.10);
    for (let s = 0; s + win < samples.length; s += hop) {
      const seg = samples.subarray(s, s + win);
      let rms = 0;
      for (let i = 0; i < seg.length; i++) rms += seg[i] * seg[i];
      rms = Math.sqrt(rms / seg.length);
      out.push(rms < floor ? null : (yin(seg, rate) || null));
    }
    return out;
  }

  /* 중앙값 기준 반음으로 바꾼다 → 목소리 높낮이 차이를 없앤다 */
  function normalize(hz) {
    const v = hz.filter(x => x && x > FMIN && x < FMAX).sort((a, b) => a - b);
    if (v.length < 4) return null;
    const med = v[v.length >> 1];
    return hz.map(x => (x && x > FMIN && x < FMAX) ? 12 * Math.log2(x / med) : null);
  }

  /* 앞뒤 무성 구간을 잘라내고 튀는 값을 다듬는다 */
  function clean(st) {
    if (!st) return null;
    let a = st.findIndex(x => x !== null);
    let b = st.length - 1; while (b >= 0 && st[b] === null) b--;
    if (a < 0 || b <= a) return null;
    const cut = st.slice(a, b + 1);
    // 옥타브 튐 제거: 이웃과 10반음 넘게 차이 나면 버린다
    for (let i = 1; i < cut.length - 1; i++) {
      if (cut[i] === null) continue;
      const p = cut[i - 1], q = cut[i + 1];
      if (p !== null && q !== null && Math.abs(cut[i] - p) > 10 && Math.abs(cut[i] - q) > 10) cut[i] = (p + q) / 2;
    }
    // 3점 평균
    const sm = cut.slice();
    for (let i = 1; i < cut.length - 1; i++) {
      const w = [cut[i - 1], cut[i], cut[i + 1]].filter(x => x !== null);
      if (w.length) sm[i] = w.reduce((s, x) => s + x, 0) / w.length;
    }
    return sm;
  }

  /* 길이를 맞춰 겹쳐볼 수 있게 한다 (0~1 구간 20점) */
  function resample(st, n = 20) {
    if (!st) return null;
    const pts = st.map((v, i) => [i / (st.length - 1), v]).filter(p => p[1] !== null);
    if (pts.length < 4) return null;
    const out = [];
    for (let k = 0; k < n; k++) {
      const t = k / (n - 1);
      let j = 0; while (j < pts.length - 1 && pts[j + 1][0] < t) j++;
      const [t0, v0] = pts[j], [t1, v1] = pts[Math.min(j + 1, pts.length - 1)];
      out.push(t1 === t0 ? v0 : v0 + (v1 - v0) * (t - t0) / (t1 - t0));
    }
    return out;
  }


  /* 허밍·잡음 거르기.
     음높이만 보면 '아~' 하고 흥얼거려도 곡선이 맞아버린다.
     말소리에는 있고 허밍에는 없는 것 — 에너지가 오르내리고, 자음 때문에
     무성 구간이 섞이고, 길이가 한 음절 범위 안이다 — 로 걸러낸다. */
  function speechLike(samples, rate, hz) {
    const win = Math.round(rate * 0.02);
    const env = [];
    for (let s = 0; s + win < samples.length; s += win) {
      let e = 0;
      for (let i = s; i < s + win; i++) e += samples[i] * samples[i];
      env.push(Math.sqrt(e / win));
    }
    const peak = Math.max(...env, 1e-9);
    const loud = env.filter(v => v > peak * 0.25);
    const sec = loud.length * 0.02;
    const voiced = hz.filter(x => x).length / Math.max(1, hz.filter((x, i) => {
      return true;
    }).length);
    // 에너지 변동폭 — 허밍은 평평하다
    const m = env.reduce((a, b) => a + b, 0) / env.length;
    const sd = Math.sqrt(env.reduce((a, b) => a + (b - m) ** 2, 0) / env.length);
    const flux = m ? sd / m : 0;
    if (sec < 0.12) return { ok: false, why: '너무 짧습니다. 한 음절을 또박또박 말해 보세요.' };
    if (sec > 2.5) return { ok: false, why: '너무 깁니다. 한 단어만 말해 보세요.' };
    if (voiced > 0.97 && flux < 0.45) return { ok: false, why: '허밍처럼 들립니다. 입을 열고 또박또박 말해 보세요.' };
    if (peak < 0.02) return { ok: false, why: '소리가 너무 작습니다. 조금 크게 말해 보세요.' };
    return { ok: true, sec };
  }

  /* 소리가 실제로 난 길이(초). nặng 처럼 '짧고 뚝 끊기는' 성조는
     높낮이 모양만으로는 huyền 과 구별이 안 된다. 길이가 그 차이를 잡아준다. */
  function voicedSec(hz, rate, hop) {
    const n = hz.filter(x => x).length;
    return n * hop / rate;
  }

  /* 에너지 곡선 — 소리가 난 구간만, 로그 뒤 표준화해서 20점.
     연구 권고대로 로그 변환 + 평균·편차 정규화를 쓴다(목소리 크기 차이를 없앤다). */
  function energy(samples, rate, hz) {
    const win = Math.round(rate * 0.045), hop = Math.round(rate * 0.010);
    let a = hz.findIndex(x => x), b = hz.length - 1;
    while (b >= 0 && !hz[b]) b--;
    if (a < 0 || b <= a) return null;
    const raw = [];
    for (let i = a; i <= b; i++) {
      const s0 = i * hop;
      if (s0 + win >= samples.length) break;
      let e = 0;
      for (let k = s0; k < s0 + win; k++) e += samples[k] * samples[k];
      raw.push(Math.log(Math.sqrt(e / win) + 1e-9));
    }
    if (raw.length < 4) return null;
    const m = raw.reduce((s, v) => s + v, 0) / raw.length;
    const sd = Math.sqrt(raw.reduce((s, v) => s + (v - m) ** 2, 0) / raw.length) || 1;
    const z = raw.map(v => (v - m) / sd);
    const out = [];
    for (let k = 0; k < 20; k++) {
      const t = k / 19 * (z.length - 1), j = Math.floor(t), f = t - j;
      out.push(z[j] + (z[Math.min(j + 1, z.length - 1)] - z[j]) * f);
    }
    return out;
  }

  async function analyze(arrayBuffer, ctx, checkSpeech) {
    const buf = await ctx.decodeAudioData(arrayBuffer.slice(0));
    const ch = buf.getChannelData(0);
    const rate = buf.sampleRate;
    const hz = contour(ch, rate);
    if (checkSpeech) {
      const g = speechLike(ch, rate, hz);
      if (!g.ok) return { reject: g.why };
    }
    const curve = resample(clean(normalize(hz)));
    if (!curve) return null;
    return { curve, en: energy(ch, rate, hz), sec: voicedSec(hz, rate, Math.round(rate * 0.010)) };
  }

  /* 두 곡선의 '모양'이 얼마나 닮았나 (0~100).
     앞서 기울기(차이값)로 재봤더니 잡음이 심해 같은 성조끼리도 낮게 나왔다.
     곡선 값 자체를 각자 표준화한 뒤 상관을 보는 쪽이 훨씬 안정적이다. */
  function zscore(a) {
    const m = a.reduce((s, v) => s + v, 0) / a.length;
    const sd = Math.sqrt(a.reduce((s, v) => s + (v - m) ** 2, 0) / a.length);
    return sd < 0.25 ? a.map(() => 0) : a.map(v => (v - m) / sd);
  }

  /* ── 성조 본보기와 판정 ────────────────────────────────────
     원어민 음성 **1,151개**(한 음절 낱말, 북부 남녀)를 이 파일과 같은 방법으로 재서 뽑았다
     (tools/tone_corpus.py · tools/tone_feat.py).

     조사해서 알게 된 것 — 베트남어 성조는 **F0만으로는 안 된다.**
     하노이 말은 성조와 발성이 붙어 있어 ngã·nặng 은 삐걱거리고(creaky) hỏi 는 성문이 조인다.
     연구들은 "높이보다 삐걱거림·숨소리가 주된 지각 단서"라고 한다.
     그래서 삐걱거림(F0 흔들림)도 재 봤는데 **우리 기준 음성이 TTS 라 삐걱거림이 거의 없었다** —
     넣으니 오히려 나빠졌다(86.5%→83.9%). 그래서 안 쓴다. 에너지 곡선은 조금 도움이 됐다(86.8%).

     여섯 성조를 그대로 가르면 58%뿐이다. 소리로 실제 갈리는 **세 무리**로 묶으면 87%다.
       flat 내려감(ngang·huyền·nặng) · rise 올라감(sắc) · dip 내렸다 올라감(hỏi·ngã)

     **가장 크게 좋아진 것은 특징을 늘린 것이 아니라 '모르면 모른다'고 한 것이다.**
     원어민 녹음은 전부 제대로 낸 것이므로 거기서 나오는 X 는 곧 잘못된 지적이다. 실측:
       바로 가장 가까운 것을 고르면 → 제대로 낸 것의 13.2% 를 틀렸다고 한다
       아래 문턱을 두면       → 1.9% 로 줄고, 틀린 것은 60% 를 잡고 28% 는 '다시 하라'고 한다
     사람을 잘못 판정하지 않는 쪽을 택했다. */
  const TPL = {"flat": {"c": [1.522, 1.269, 1.039, 0.895, 0.797, 0.683, 0.544, 0.401, 0.251, 0.098, -0.071, -0.246, -0.409, -0.551, -0.675, -0.786, -0.886, -1.021, -1.198, -1.423], "e": [-1.69, -0.534, 0.165, 0.602, 0.838, 0.923, 0.93, 0.88, 0.8, 0.688, 0.574, 0.45, 0.309, 0.144, -0.03, -0.23, -0.5, -0.888, -1.443, -2.23], "s": 0.219}, "rise": {"c": [-0.528, -0.751, -0.923, -0.977, -0.979, -0.923, -0.847, -0.729, -0.573, -0.364, -0.106, 0.208, 0.569, 0.963, 1.375, 1.779, 2.153, 2.479, 2.733, 2.915], "e": [-1.665, -0.583, 0.109, 0.542, 0.775, 0.847, 0.833, 0.765, 0.685, 0.607, 0.55, 0.5, 0.442, 0.356, 0.204, -0.03, -0.37, -0.818, -1.416, -2.18], "s": 0.186}, "dip": {"c": [2.129, 1.541, 1.083, 0.73, 0.479, 0.167, -0.23, -0.66, -0.996, -1.252, -1.395, -1.37, -1.162, -0.774, -0.247, 0.412, 1.073, 1.715, 2.201, 2.476], "e": [-1.608, -0.172, 0.617, 1.001, 1.087, 1.019, 0.868, 0.695, 0.516, 0.314, 0.108, -0.047, -0.13, -0.151, -0.146, -0.171, -0.309, -0.64, -1.253, -2.234], "s": 0.253}};
  const FAM = { 'ngang': 'flat', 'huyền': 'flat', 'nặng': 'flat',
                'sắc': 'rise', 'hỏi': 'dip', 'ngã': 'dip' };
  const FAMKO = { flat: '내려감', rise: '올라감', dip: '내렸다 올라감' };
  /* 두 문턱은 실측으로 골랐다. 문턱을 아주 높이면 잘못된 지적은 1.9%까지 줄지만
     **진짜 틀린 것의 40%를 맞다고 하게 된다** — 그것도 잘못된 판정이다. 둘을 함께 보고 골랐다.
       O<0.35 · X≥0.80  →  잘못된 지적 3.9% · 틀린 것 79% 잡음 · 나머지는 '다시 한 번'
     그리고 X 라고 해도 '틀렸다'가 아니라 **'다르게 들린다'**고 말한다 — 잰 것을 말할 뿐이다. */
  const SURE = 0.35, WRONG = 0.80;

  /* 길이를 얼마나 볼 것인가 — **상한을 둔다**. 이게 없으면 천천히 말하는 사람이 손해를 본다.
     실측: 말을 두 배 느리게 하면 길이 가중치 ×4 에서 정확도가 86.8%→84.8% 로 떨어지고
     판정이 한쪽(내려감)으로 쏠렸다. 가중치를 ×8 로 올리면 이 코퍼스에서는 88.1% 로 제일 좋지만
     느린 사람에게는 84.6% 로 제일 나빠진다 — **기준 음성이 TTS 라 길이가 고른 탓에 생기는 착시**다.
     상한 0.05초를 두면 보통 속도 86.5% · 두 배 느려도 85.9% 로 속도에 흔들리지 않는다. */
  const SECCAP = 0.05;
  function dist(A, k) {
    const t = TPL[k], a = A.curve;
    let s = 0;
    for (let i = 0; i < 20; i++) { const v = a[i] - t.c[i]; s += v * v; }
    let d = Math.sqrt(s / 20);
    if (A.sec) d += Math.min(Math.abs(A.sec - t.s), SECCAP) * 4;
    if (A.en) {
      let e = 0;
      for (let i = 0; i < 20; i++) { const v = A.en[i] - t.e[i]; e += v * v; }
      d += Math.sqrt(e / 20) * 0.5;
    }
    return d;
  }

  /* 어느 무리에 가장 가까운가 (설명용). */
  function classify(A) {
    if (!A || !A.curve || A.curve.length !== 20) return null;
    let best = null, bd = 1e9;
    for (const k in TPL) { const d = dist(A, k); if (d < bd) { bd = d; best = k; } }
    return { fam: best, ko: FAMKO[best], dist: bd };
  }

  /* **목표 성조를 아는 상태에서** 맞았는지 본다. 셋 중 하나로만 답한다.
       ok    목표가 가장 가깝다 (또는 거의)          → O
       miss  목표가 뚜렷하게 멀다                    → X + 무엇이 다른지
       unsure 그 사이 — 못 가리겠다                  → 다시 한 번
     '모르겠다'를 말할 수 있어야 잘못된 지적이 줄어든다. */
  /* hỏi·ngã(내렸다 올라감)도 **채점한다.** 다만 문턱을 조금 높이고 안내를 붙인다.
     처음에는 아예 채점을 안 하려 했는데, 다시 재보니 그럴 이유가 없었다:
       '52%' 는 여섯 성조를 그대로 가를 때의 숫자이고,
       **목표를 아는 채점**으로 보면 판정한 것 중 89.2% 가 맞는다 —
       내려감 88.3% · 올라감 93.9% 와 거의 같다.
     다만 제대로 낸 것에 X 를 주는 비율이 문턱 0.80 에서 17.8% 로 다른 성조(0.8%·3.3%)보다 높다.
     문턱을 1.00 으로 올리면 정확도는 88.6% 로 거의 그대로인데 잘못된 지적이 10.6% 로 준다.
     그래서 이 무리만 문턱을 1.00 으로 두고, 화면에 **남부·중부는 이 둘을 하나로 합쳐 쓴다**는
     사실을 함께 알려 준다 (북부는 또렷이 가른다 — '현지인이 다 못 한다'는 말은 사실이 아니다). */
  const HARD = { dip: 1.00 };

  function judge(A, wantFam) {
    if (!A || !A.curve || !TPL[wantFam]) return null;
    const ds = {};
    let bd = 1e9, best = null;
    for (const k in TPL) { const d = dist(A, k); ds[k] = d; if (d < bd) { bd = d; best = k; } }
    const gap = ds[wantFam] - bd;
    if (gap < SURE) return { v: 'ok', fam: wantFam, ko: FAMKO[wantFam] };
    const out = { fam: best, ko: FAMKO[best], want: wantFam, wantKo: FAMKO[wantFam],
                  note: !!HARD[wantFam] };
    if (gap >= (HARD[wantFam] || WRONG)) return Object.assign(out, { v: 'miss' });
    return Object.assign(out, { v: 'unsure' });
  }

  /* 곡선의 '방향'만 뽑는다 (그림 밑 설명용). */
  function direction(A) {
    const a = A && (A.curve || A);
    if (!a) return null;
    const n = a.length, third = Math.floor(n / 3);
    const head = a.slice(0, third).reduce((s, v) => s + v, 0) / third;
    const tail = a.slice(n - third).reduce((s, v) => s + v, 0) / third;
    const mid = a.slice(third, n - third);
    const midMin = Math.min(...mid);
    const net = tail - head;
    const dip = Math.min(head, tail) - midMin;
    if (dip > 1.6 && net > -1.0) return 'dip';    // 내렸다 올림
    if (net > 1.2) return 'up';
    if (net < -1.2) return 'down';
    return 'flat';
  }

  function similarity(A, B) {
    const a = A && (A.curve || A), b = B && (B.curve || B);
    if (!a || !b || a.length !== b.length) return null;
    const za = zscore(a), zb = zscore(b);
    let num = 0, sa = 0, sb = 0;
    for (let i = 0; i < za.length; i++) { num += za[i] * zb[i]; sa += za[i] ** 2; sb += zb[i] ** 2; }
    const r = (sa && sb) ? num / Math.sqrt(sa * sb) : 0;
    // 전체 오르내림 폭도 본다 — 방향은 같은데 밋밋하면 성조가 아니다
    const span = x => Math.max(...x) - Math.min(...x);
    const dv = Math.abs(span(a) - span(b));
    let sc = (r + 1) / 2 * 100 - dv * 2.5;
    // 길이 차이도 반영한다 (한쪽이 두 배 이상 길면 다른 성조로 본다)
    if (A && B && A.sec && B.sec) {
      const ratio = Math.max(A.sec, B.sec) / Math.min(A.sec, B.sec);
      if (ratio > 1.35) sc -= Math.min(45, (ratio - 1.35) * 60);
    }
    return Math.max(0, Math.min(100, Math.round(sc)));
  }

  /* 녹음 중에 실시간으로 쓰려고 밖에 내놓는다 (한 조각에서 음높이 하나) */
  return { analyze, similarity, direction, classify, judge, yin, FAM, FAMKO };
})();
