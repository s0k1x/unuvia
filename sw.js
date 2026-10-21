/*! Unuvia 2.0 · © 2026 Unuvia (https://unuvia.es). Todos los derechos reservados / All rights reserved. Prohibido copiar, modificar o redistribuir sin autorización escrita: ver LICENSE. */
/* Unuvia · service worker
   - Avisos al móvil.
   - Sin conexión: guarda una copia de la web (red primero; si no hay internet, usa la copia).
     Así siempre ves la última versión cuando hay conexión. */
const CACHE = 'unuvia-v9';
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
  if (same && u.pathname === '/version.json') return;   // el aviso de «hay una versión nueva» siempre va directo a la red, sin copia
  const versioned = same && u.searchParams.has('v') && /\.(?:js|css)$/.test(u.pathname);   // app.js?v=… y styles.css?v=…: cada versión tiene su propia dirección
  const asset = same && /\.(?:png|webp|jpe?g|svg|ico|woff2?)$/.test(u.pathname);
  // IMPORTANTE: waitUntil se llama AQUÍ, de forma síncrona. Llamarlo más tarde (dentro de la promesa) lo rechaza Safari en iPhone
  // y rompía la carga del CSS y del código a partir del segundo arranque.
  let release;
  e.waitUntil(new Promise(res => { release = res; }));
  e.respondWith((async () => {
    let background = false;
    try {
      const cache = await caches.open(CACHE);
      // Archivos que no cambian bajo la misma dirección: se sirven al instante desde la copia
      if (versioned || asset || cdn) {
        const hit = await cache.match(r);
        const net = fetch(r).then(async res => {
          if (res && res.ok) {
            try { await cache.put(r, res.clone()); if (versioned) await prune(cache, u); } catch (_) {}   // guardar es un extra: si falla, no pasa nada
          }
          return res;
        });
        if (hit) { background = true; net.then(release, release); return hit; }   // copia ya; se actualiza por detrás
        return await net;
      }
      // La página y el resto: red primero (así siempre ves la última versión) y, sin internet, la copia
      try {
        // Las páginas se piden «revalidando»: GitHub Pages las guarda 10 minutos y así la versión nueva tardaría en llegar
        const res = await fetch(r, r.mode === 'navigate' ? { cache: 'no-cache' } : undefined);
        if (res && res.ok) cache.put(r, res.clone()).catch(() => {});
        return res;
      } catch (err) {
        const hit = await cache.match(r, { ignoreSearch: r.mode === 'navigate' });
        if (hit) return hit;
        if (r.mode === 'navigate') { const home = (await cache.match('/')) || (await cache.match('/index.html')); if (home) return home; }
        throw err;
      }
    } catch (err) {
      // Si el Service Worker falla por lo que sea, la petición va directa a la red: nunca debe impedir que cargue la web
      try { return await fetch(r); } catch (_) { throw err; }
    } finally {
      if (!background) release();
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

// Tema actual (lo avisa la página): el aviso del móvil usa el icono del tema. Cache aparte ('uvmeta') para que no se borre al actualizar.
self.addEventListener('message', e => {
  const d = e.data || {};
  if (d.type === 'theme' && /^[a-z]{3,12}$/.test(d.name || '')) e.waitUntil(caches.open('uvmeta').then(c => c.put('/__theme', new Response(d.name))).catch(() => {}));
  if (d.type === 'prefs') {
    const q = d.quiet || {};
    const clean = { muted: (Array.isArray(d.muted) ? d.muted : []).slice(0, 60).map(x => String(x).slice(0, 60)), quiet: { on: !!q.on, from: /^\d{2}:\d{2}$/.test(q.from) ? q.from : '22:00', to: /^\d{2}:\d{2}$/.test(q.to) ? q.to : '07:00' } };
    e.waitUntil(caches.open('uvmeta').then(c => c.put('/__prefs', new Response(JSON.stringify(clean)))).catch(() => {}));
  }
});
async function themeIcon() {
  try {
    const r = await (await caches.open('uvmeta')).match('/__theme');
    const t = r ? await r.text() : '';
    return t && t !== 'normal' ? 'icons/' + t + '/icon-192.png' : 'icon-192.png';
  } catch (_) { return 'icon-192.png'; }
}

// Preferencias de avisos (la página las guarda aquí): clases silenciadas y horas de silencio
async function uvPrefs() { try { const c = await caches.open('uvmeta'); const r = await c.match('/__prefs'); return r ? await r.json() : null; } catch (_) { return null; } }
function uvMin(s) { const p = String(s).split(':'); return (+p[0] || 0) * 60 + (+p[1] || 0); }
// ¿Este aviso debe llegar en silencio (sin sonido ni vibración)?
function uvSilent(p, cls, now) {
  if (!p) return false;
  const c = String(cls || '').trim().toLowerCase();
  if (c && (Array.isArray(p.muted) ? p.muted : []).some(m => String(m).trim().toLowerCase() === c)) return true;
  const q = p.quiet;
  if (q && q.on && /^\d{2}:\d{2}$/.test(q.from) && /^\d{2}:\d{2}$/.test(q.to)) {
    const m = now.getHours() * 60 + now.getMinutes(), f = uvMin(q.from), t = uvMin(q.to);
    if (f === t) return false;
    return f < t ? (m >= f && m < t) : (m >= f || m < t);
  }
  return false;
}
self.addEventListener('push', e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (x) { d = { body: e.data ? e.data.text() : '' }; }
  const n = unuviaNotif(d);
  const cls = d.v === 2 ? (d.cls || '') : (d.title && d.title !== 'Unuvia' ? d.title : '');
  e.waitUntil(Promise.all([themeIcon(), uvPrefs()]).then(([icon, prefs]) => {
    const quiet = uvSilent(prefs, cls, new Date());
    return self.registration.showNotification(n.title, {
      body: n.body,
      icon,
      badge: 'badge-96.png',
      lang: 'es',
      timestamp: Date.now(),
      ...(quiet ? { silent: true } : { vibrate: [70, 40, 70] }),
      tag: d.tag || undefined,
      renotify: !!d.tag && !quiet,
      data: { url: d.url || '/' }
    });
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

// Los navegadores (sobre todo Chrome en Android y en ordenador) a veces CAMBIAN la suscripción de avisos por su cuenta:
// si no se hace nada, los avisos dejan de llegar sin que nadie lo note. Aquí se renueva sola y se avisa a la app para que la guarde.
self.addEventListener('pushsubscriptionchange', e => {
  e.waitUntil((async () => {
    try {
      const old = e.oldSubscription;
      const key = old && old.options && old.options.applicationServerKey;
      let sub = e.newSubscription;
      if (!sub && key) sub = await self.registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: key });
      const c = await caches.open('uvmeta');
      await c.put('/__resub', new Response(String(Date.now())));
      const all = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
      all.forEach(w => w.postMessage({ type: 'resync' }));
    } catch (_) { /* si falla, la app vuelve a guardarla al abrirse */ }
  })());
});
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
try { self.__uvTest = { uvSilent, unuviaNotif }; } catch (_) {}
