/* ==========================================================
   VeriNews AI — PWA Service Worker (Offline Support)
   ========================================================== */

const CACHE_NAME = "verinews-cache-v1";
const STATIC_ASSETS = [
  "./",
  "./index.html",
  "./style.css",
  "./script.js",
  "./manifest.json",
  "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap",
  "https://unpkg.com/lucide@latest",
  "https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js",
  "https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"
];

// Install Event: Cache Core Static Shell
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("[ServiceWorker] Pre-caching offline assets");
      return cache.addAll(STATIC_ASSETS.map(url => new Request(url, { cache: "reload" }))).catch(err => {
        console.warn("[ServiceWorker] Non-critical cache warning:", err);
      });
    })
  );
  self.skipWaiting();
});

// Activate Event: Clean up stale caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(
        keyList.map((key) => {
          if (key !== CACHE_NAME) {
            console.log("[ServiceWorker] Removing old cache:", key);
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch Event: Network-first for API, Cache-first with stale-while-revalidate for static assets
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Skip non-GET requests and browser extensions
  if (event.request.method !== "GET" || url.protocol.startsWith("chrome-extension")) {
    return;
  }

  // Network-First for API verification routes
  if (url.pathname.startsWith("/api") || url.pathname.startsWith("/search") || url.pathname.startsWith("/stream_summary")) {
    event.respondWith(
      fetch(event.request).catch(() => {
        return new Response(
          JSON.stringify({
            claim: "Offline Query",
            verdict: "UNVERIFIED",
            confidence: 0,
            summary: "You are currently offline. Connect to the internet for live real-time web verification.",
            cached: false
          }),
          { headers: { "Content-Type": "application/json" } }
        );
      })
    );
    return;
  }

  // Stale-While-Revalidate for app assets
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      const fetchPromise = fetch(event.request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const responseClone = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return networkResponse;
      }).catch(() => cachedResponse);

      return cachedResponse || fetchPromise;
    })
  );
});
