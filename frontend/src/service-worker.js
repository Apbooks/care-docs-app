/// <reference lib="webworker" />
import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching';
import { clientsClaim } from 'workbox-core';
import { registerRoute, NavigationRoute, Route } from 'workbox-routing';
import { NetworkFirst, NetworkOnly, CacheFirst, StaleWhileRevalidate } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import { CacheableResponsePlugin } from 'workbox-cacheable-response';
import { BackgroundSyncPlugin } from 'workbox-background-sync';

// Self reference for service worker
const sw = /** @type {ServiceWorkerGlobalScope} */ (/** @type {unknown} */ (self));

// Activate updated service worker immediately
sw.skipWaiting();
clientsClaim();

// Precache static assets (injected by workbox)
precacheAndRoute(self.__WB_MANIFEST || []);

// Clean up old caches
cleanupOutdatedCaches();

// Cache names
const CACHE_NAMES = {
	api: 'api-cache-v3',
	images: 'image-cache-v3',
	static: 'static-cache-v3'
};

// Background sync queue for offline event creation
const bgSyncPlugin = new BackgroundSyncPlugin('eventQueue', {
	maxRetentionTime: 24 * 60, // Retry for up to 24 hours (in minutes)
	onSync: async ({ queue }) => {
		let entry;
		while ((entry = await queue.shiftRequest())) {
			try {
				await fetch(entry.request.clone());
				console.log('Background sync successful for:', entry.request.url);
			} catch (error) {
				console.error('Background sync failed for:', entry.request.url, error);
				// Re-add to queue on failure
				await queue.unshiftRequest(entry);
				throw error;
			}
		}
	}
});

// Reminder next-due should not be cached to avoid stale banners
registerRoute(
	({ url }) => url.pathname.startsWith('/api/med-reminders/next'),
	new NetworkOnly(),
	'GET'
);

// API Routes - NetworkFirst for most API calls
registerRoute(
	({ url }) => url.pathname.startsWith('/api/') &&
		!url.pathname.includes('/stream') &&
		!url.pathname.includes('/auth/login') &&
		!url.pathname.includes('/auth/logout') &&
		!url.pathname.includes('/auth/refresh'),
	new NetworkFirst({
		cacheName: CACHE_NAMES.api,
		networkTimeoutSeconds: 10,
		plugins: [
			new CacheableResponsePlugin({
				statuses: [0, 200]
			}),
			new ExpirationPlugin({
				maxEntries: 100,
				maxAgeSeconds: 60 * 60 * 24, // 24 hours
				purgeOnQuotaError: true
			})
		]
	}),
	'GET'
);

// SSE stream should bypass caching and buffering
registerRoute(
	({ url }) => url.pathname.startsWith('/api/stream'),
	new NetworkOnly(),
	'GET'
);

// Event creation/update/delete - use background sync for POST/PATCH/DELETE
registerRoute(
	({ url, request }) =>
		url.pathname.startsWith('/api/events') &&
		['POST', 'PATCH', 'DELETE'].includes(request.method),
	new NetworkFirst({
		cacheName: CACHE_NAMES.api,
		plugins: [bgSyncPlugin]
	}),
	'POST'
);

registerRoute(
	({ url, request }) =>
		url.pathname.startsWith('/api/events') &&
		request.method === 'PATCH',
	new NetworkFirst({
		cacheName: CACHE_NAMES.api,
		plugins: [bgSyncPlugin]
	}),
	'PATCH'
);

registerRoute(
	({ url, request }) =>
		url.pathname.startsWith('/api/events') &&
		request.method === 'DELETE',
	new NetworkFirst({
		cacheName: CACHE_NAMES.api,
		plugins: [bgSyncPlugin]
	}),
	'DELETE'
);

// Continuous feed operations - also use background sync
registerRoute(
	({ url, request }) =>
		url.pathname.startsWith('/api/feeds/continuous') &&
		request.method === 'POST',
	new NetworkFirst({
		cacheName: CACHE_NAMES.api,
		plugins: [bgSyncPlugin]
	}),
	'POST'
);

// Static assets and images - CacheFirst
registerRoute(
	({ request }) =>
		request.destination === 'image' ||
		request.url.match(/\.(png|jpg|jpeg|svg|gif|webp|ico)$/),
	new CacheFirst({
		cacheName: CACHE_NAMES.images,
		plugins: [
			new CacheableResponsePlugin({
				statuses: [0, 200]
			}),
			new ExpirationPlugin({
				maxEntries: 100,
				maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
				purgeOnQuotaError: true
			})
		]
	})
);

// Google Fonts - CacheFirst
registerRoute(
	({ url }) => url.origin === 'https://fonts.googleapis.com' ||
		url.origin === 'https://fonts.gstatic.com',
	new CacheFirst({
		cacheName: 'google-fonts',
		plugins: [
			new CacheableResponsePlugin({
				statuses: [0, 200]
			}),
			new ExpirationPlugin({
				maxEntries: 30,
				maxAgeSeconds: 60 * 60 * 24 * 365 // 1 year
			})
		]
	})
);

// Static JS/CSS assets - StaleWhileRevalidate
registerRoute(
	({ request }) =>
		request.destination === 'script' ||
		request.destination === 'style',
	new StaleWhileRevalidate({
		cacheName: CACHE_NAMES.static,
		plugins: [
			new CacheableResponsePlugin({
				statuses: [0, 200]
			}),
			new ExpirationPlugin({
				maxEntries: 50,
				maxAgeSeconds: 60 * 60 * 24 * 7 // 7 days
			})
		]
	})
);

// Navigation requests - NetworkFirst with offline fallback
const navigationHandler = new NetworkFirst({
	cacheName: 'navigation-cache',
	networkTimeoutSeconds: 5,
	plugins: [
		new CacheableResponsePlugin({
			statuses: [0, 200]
		})
	]
});

// Register navigation route
registerRoute(
	new NavigationRoute(navigationHandler, {
		// Don't cache login page when offline (requires auth)
		denylist: [/\/login/, /\/setup\.html/]
	})
);

// Handle messages from the main thread
sw.addEventListener('message', (event) => {
	if (event.data && event.data.type === 'SKIP_WAITING') {
		sw.skipWaiting();
	}

	if (event.data && event.data.type === 'SYNC_EVENTS') {
		// Trigger background sync manually
		sw.registration.sync.register('eventQueue').catch((err) => {
			console.log('Background sync not supported:', err);
		});
	}

	if (event.data && event.data.type === 'CLEAR_CACHE') {
		// Clear all caches
		caches.keys().then((names) => {
			names.forEach((name) => {
				caches.delete(name);
			});
		});
	}
});

// Handle install event
sw.addEventListener('install', (event) => {
	console.log('Service worker installing...');
	// Force waiting service worker to become active
	sw.skipWaiting();
});

// Handle activate event
sw.addEventListener('activate', (event) => {
	console.log('Service worker activating...');
	// Take control of all pages immediately
	event.waitUntil(sw.clients.claim());
});

// Handle background sync event
sw.addEventListener('sync', (event) => {
	if (event.tag === 'eventQueue') {
		console.log('Background sync triggered for eventQueue');
		// The BackgroundSyncPlugin handles this automatically
	}
});

// Handle push notifications (for future reminder feature)
sw.addEventListener('push', (event) => {
	if (event.data) {
		const data = event.data.json();
		const options = {
			body: data.body || 'Care reminder',
			icon: '/icon.svg',
			badge: '/icon.svg',
			vibrate: [100, 50, 100],
			data: {
				url: data.url || '/'
			},
			actions: [
				{ action: 'open', title: 'Open' },
				{ action: 'dismiss', title: 'Dismiss' }
			]
		};

		event.waitUntil(
			sw.registration.showNotification(data.title || 'Care Docs', options)
		);
	}
});

// Handle notification click
sw.addEventListener('notificationclick', (event) => {
	event.notification.close();

	if (event.action === 'dismiss') {
		return;
	}

	const url = event.notification.data?.url || '/';

	event.waitUntil(
		sw.clients.matchAll({ type: 'window' }).then((clients) => {
			// Check if there's already a window open
			for (const client of clients) {
				if (client.url.includes(url) && 'focus' in client) {
					return client.focus();
				}
			}
			// Open a new window if none found
			if (sw.clients.openWindow) {
				return sw.clients.openWindow(url);
			}
		})
	);
});
