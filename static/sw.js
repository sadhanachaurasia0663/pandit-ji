const CACHE = 'pandit-ji-v11';
const ASSETS = [
  '/',
  '/static/styles.css?v=11',
  '/static/app.js?v=10',
  '/static/manifest.webmanifest',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => cache.addAll(ASSETS))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys
          .filter((key) => key.startsWith('pandit-ji-') && key !== CACHE)
          .map((key) => caches.delete(key)),
      ))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (!response.ok) return response;
          return caches.open(CACHE)
            .then((cache) => cache.put(event.request, response.clone()))
            .then(() => response);
        })
        .catch(async () => {
          const cached = await caches.match(event.request);
          return cached || caches.match('/');
        }),
    );
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then((cached) => cached || fetch(event.request)),
  );
});
