/* 오프라인 캐시.
   앱 껍데기와 커리큘럼은 처음 열 때 통째로 받아두고,
   음성은 22MB나 되므로 한 번 재생한 것만 캐시에 남긴다 (데이터 요금 배려). */
const V = 'vn-9663fa6e';
const SHELL = ['./', './index.html', './app.js', './pitch.js', './style.css',
               './manifest.json', './icon.png',
               // 새 짜임(일곱 권)의 알맹이 — 이것이 없으면 비행기 모드에서 과정이 안 열린다
               './data/days.json', './data/audio_index.json',
               './data/order.json', './data/grammar.json', './data/know.json',
               './data/exgloss.json'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(V).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin) return;

  // 음성·그림: 캐시에 있으면 캐시, 없으면 받아서 캐시에 넣는다.
  // (판번호가 바뀌면 캐시를 통째로 버리므로 옛 파일이 남을 일은 없다)
  if (url.pathname.endsWith('.mp3') || url.pathname.endsWith('.webp')) {
    e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(r => {
      if (r.ok) { const cp = r.clone(); caches.open(V).then(c => c.put(e.request, cp)); }
      return r;
    })));
    return;
  }

  // 나머지: 서버에 항상 다시 물어본다(ETag 로 확인만 하므로 가볍다). 실패하면 캐시.
  // 이렇게 안 하면 Pages 의 10분 캐시 때문에 고친 내용이 바로 안 보인다.
  e.respondWith(fetch(e.request, { cache: 'no-cache' }).then(r => {
    if (r.ok) { const cp = r.clone(); caches.open(V).then(c => c.put(e.request, cp)); }
    return r;
  }).catch(() => caches.match(e.request)));
});

/* ---------- 폰 알림 ----------
   서버가 '깨워라'만 보낸다(내용 없음). 무슨 말이 왔는지는 앱을 열어야 본다 —
   대화 내용을 서버에 보내지 않기 위해서다. */
self.addEventListener('push', e => {
  e.waitUntil(self.registration.showNotification('짜오짜오', {
    body: '베트남 친구가 메시지를 보냈어요',
    icon: './icon.png', badge: './icon-180.png', tag: 'chaochao-msg',
  }));
});
self.addEventListener('notificationclick', e => {
  e.notification.close();
  e.waitUntil(clients.matchAll({ type: 'window', includeUncontrolled: true }).then(ws => {
    for (const w of ws) if (w.url.includes('/chaochao') && 'focus' in w) return w.focus();
    return clients.openWindow('./index.html');
  }));
});
