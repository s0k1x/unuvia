/*! Unuvia 2.0 · © 2026 Unuvia (https://unuvia.es). Todos los derechos reservados / All rights reserved. Prohibido copiar, modificar o redistribuir sin autorización escrita: ver LICENSE. */
/* Unuvia · service worker
   - Avisos al móvil.
   - Sin conexión: guarda una copia de la web (red primero; si no hay internet, usa la copia).
     Así siempre ves la última versión cuando hay conexión. */
const CACHE = 'unuvia-v5';
self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(['/', '/manifest.webmanifest', '/icon-192.png', '/badge-96.png']).catch(() => {})));
});
self.addEventListener('activate', e => e.waitUntil((async () => {
  const keys = await caches.keys();
  await Promise.all(keys.filter(k => k.startsWith('unuvia-') && k !== CACHE).map(k => caches.delete(k)));
  await self.clients.claim();
})()));

addEventListener('fetch', e => {
  const r = e.request;
  if (r.method !== 'GET') return;
  const u = new URL(r.url);
  const same = u.origin === self.location.origin, cdn = u.hostname === 'cdn.jsdelivr.net';
  if (!same && !cdn) return;                       // la base de datos y los archivos de Supabase nunca se guardan aquí
  const versioned = same && u.searchParams.has('v') && /\.(?:js|css)$/.test(u.pathname);   // app.js?v=… y styles.css?v=…: cada versión tiene su propia dirección
  const asset = same && /\.(?:png|webp|jpe?g|svg|ico|woff2?)$/.test(u.pathname);
  e.respondWith((async () => {
    const cache = await caches.open(CACHE);
    // Archivos que no cambian bajo la misma dirección: se sirven al instante desde la copia
    if (versioned || asset || cdn) {
      const hit = await cache.match(r);
      const net = fetch(r).then(async res => {
        if (res && res.ok) { await cache.put(r, res.clone()); if (versioned) await prune(cache, u); }
        return res;
      });
      if (hit) { e.waitUntil(net.catch(() => {})); return hit; }   // copia ya; se actualiza por detrás
      return net;
    }
    // La página y el resto: red primero (así siempre ves la última versión) y, sin internet, la copia
    try {
      const res = await fetch(r);
      if (res && res.ok) cache.put(r, res.clone()).catch(() => {});
      return res;
    } catch (err) {
      const hit = await cache.match(r, { ignoreSearch: r.mode === 'navigate' });
      if (hit) return hit;
      if (r.mode === 'navigate') { const home = (await cache.match('/')) || (await cache.match('/index.html')); if (home) return home; }
      throw err;
    }
  })());
});
// Borra las copias antiguas del mismo archivo (otra ?v=) para que no se acumulen
async function prune(cache, u) {
  for (const k of await cache.keys()) {
    const ku = new URL(k.url);
    if (ku.pathname === u.pathname && ku.search !== u.search) await cache.delete(k);
  }
}

self.addEventListener('push', e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (x) { d = { body: e.data ? e.data.text() : '' }; }
  const n = unuviaNotif(d);
  e.waitUntil(self.registration.showNotification(n.title, {
    body: n.body,
    icon: 'icon-192.png',
    badge: 'badge-96.png',
    lang: 'es',
    timestamp: Date.now(),
    vibrate: [70, 40, 70],
    tag: d.tag || undefined,
    renotify: !!d.tag,
    data: { url: d.url || '/' }
  }));
});

/* Diseño del aviso: «Unuvia» primero; debajo, el icono del tipo + la clase, y después el mensaje.
   Funciona con los avisos nuevos (v:2) y con los antiguos (adivina el tipo por el texto). */
const NOTIF_EMO = { anuncio: '📢', trabajo: '📝', evento: '📅', nota: '✅', comentario: '💬', chat: '💬', entrega: '📥', miembro: '👋', rol: '🎖️', recordatorio: '⏰', prueba: '🔔' };
function guessKind(t) {
  t = String(t || '').toLowerCase();
  if (/nuevo evento|evento:|falta de asistencia|retraso/.test(t)) return 'evento';
  if (/anuncio|encuesta|publicó/.test(t)) return 'anuncio';
  if (/nueva tarea|tarea|pregunta|material|entrega:?/.test(t)) return 'trabajo';
  if (/nota|calific|examen corregido|puntos/.test(t)) return 'nota';
  if (/coment/.test(t)) return 'comentario';
  if (/foto|mensaje|nota de voz|escribió/.test(t)) return 'chat';
  if (/se unió|bienvenid/.test(t)) return 'miembro';
  return 'prueba';
}
function unuviaNotif(d) {
  const kind = d.kind || guessKind(d.body);
  const cls = String(d.v === 2 ? (d.cls || '') : (d.title && d.title !== 'Unuvia' ? d.title : '')).trim();
  const msg = String(d.body || '').trim();
  const emo = NOTIF_EMO[kind] || '🔔';
  if (!cls) return { title: 'Unuvia', body: emo + ' ' + msg.slice(0, 180) };
  return { title: 'Unuvia', body: emo + ' ' + cls + (msg ? '\n' + msg.slice(0, 180) : '') };
}

self.addEventListener('notificationclick', e => {
  e.notification.close();
  const url = (e.notification.data && e.notification.data.url) || '/';
  e.waitUntil((async () => {
    const all = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const c of all) {
      if ('focus' in c) { await c.focus(); c.postMessage({ type: 'open', url }); return; }
    }
    if (self.clients.openWindow) return self.clients.openWindow(url);
  })());
});
