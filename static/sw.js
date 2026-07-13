// static/sw.js — KILL SWITCH (tombstone).
//
// Mohtasib is a live, authenticated internal tool — not an offline PWA. A
// service worker here only caused harm: it cached the app shell for "/",
// swallowed the server's  / → /mohtasib  redirect, and served a stale generic
// app after every code change (each version bump lost a round of whack-a-mole
// because the OLD worker handled the very reload that would install the new one).
//
// So there is no worker anymore. This file exists ONLY to evict any previously
// registered worker: the browser revalidates sw.js on navigation independently
// of the old worker's fetch handler, so shipping this tombstone guarantees every
// stale browser (desktop AND iPhone) self-heals on its next visit — it purges all
// caches, unregisters itself, and forces one clean reload straight from the server.
// After that, no worker intercepts anything: redirects and fresh HTML always apply.

self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    try {
      const keys = await caches.keys();
      await Promise.all(keys.map(k => caches.delete(k)));
    } catch (_) {}
    try { await self.clients.claim(); } catch (_) {}
    try { await self.registration.unregister(); } catch (_) {}
    // One-time clean reload so the open page drops worker control and re-fetches
    // from the network — where the server applies auth + the /mohtasib redirect.
    try {
      const clients = await self.clients.matchAll({ type: 'window' });
      for (const c of clients) { try { c.navigate(c.url); } catch (_) {} }
    } catch (_) {}
  })());
});

// No 'fetch' listener on purpose: with none registered, every request goes
// straight to the network. Nothing is intercepted, nothing is cached.
