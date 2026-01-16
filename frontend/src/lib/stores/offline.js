import { writable, derived, get } from 'svelte/store';
import { browser } from '$app/environment';
import localforage from 'localforage';

// Configure LocalForage instances for different data types
const eventsStore = browser ? localforage.createInstance({
	name: 'care-docs',
	storeName: 'events'
}) : null;

const pendingQueueStore = browser ? localforage.createInstance({
	name: 'care-docs',
	storeName: 'pending_queue'
}) : null;

const cacheStore = browser ? localforage.createInstance({
	name: 'care-docs',
	storeName: 'cache'
}) : null;

// Photo queue for offline uploads
const photoQueueStore = browser ? localforage.createInstance({
	name: 'care-docs',
	storeName: 'photo_queue'
}) : null;

// Sync status: 'synced' | 'pending' | 'syncing' | 'error' | 'offline'
export const syncStatus = writable('synced');

// Number of pending items
export const pendingCount = writable(0);

// Online status
export const isOnline = writable(browser ? navigator.onLine : true);

// Last sync timestamp
export const lastSyncTime = writable(null);

// Initialize online/offline listeners
if (browser) {
	window.addEventListener('online', () => {
		isOnline.set(true);
		// Trigger sync when coming back online
		syncPendingEvents();
	});

	window.addEventListener('offline', () => {
		isOnline.set(false);
		syncStatus.set('offline');
	});

	// Initialize pending count on load
	updatePendingCount();
}

/**
 * Update the pending count from the queue
 */
async function updatePendingCount() {
	if (!pendingQueueStore) return;
	try {
		const keys = await pendingQueueStore.keys();
		pendingCount.set(keys.length);

		if (keys.length > 0 && get(isOnline)) {
			syncStatus.set('pending');
		} else if (keys.length === 0) {
			syncStatus.set('synced');
		}
	} catch (error) {
		console.error('Error updating pending count:', error);
	}
}

/**
 * Generate a temporary ID for offline events
 */
function generateTempId() {
	return `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Add an event to the offline queue
 * @param {object} action - { type: 'create'|'update'|'delete', data, endpoint }
 */
export async function queueOfflineAction(action) {
	if (!pendingQueueStore) return null;

	const queueItem = {
		id: generateTempId(),
		action: action.type, // 'create', 'update', 'delete'
		endpoint: action.endpoint,
		data: action.data,
		timestamp: new Date().toISOString(),
		retries: 0
	};

	await pendingQueueStore.setItem(queueItem.id, queueItem);
	await updatePendingCount();

	return queueItem;
}

/**
 * Get all pending actions from the queue
 */
export async function getPendingActions() {
	if (!pendingQueueStore) return [];

	const actions = [];
	await pendingQueueStore.iterate((value) => {
		actions.push(value);
	});

	// Sort by timestamp (oldest first)
	return actions.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
}

/**
 * Remove an action from the pending queue
 */
export async function removeFromQueue(id) {
	if (!pendingQueueStore) return;
	await pendingQueueStore.removeItem(id);
	await updatePendingCount();
}

/**
 * Store events locally for offline access
 */
export async function cacheEvents(events, recipientId = 'all') {
	if (!eventsStore) return;

	const cacheKey = `events_${recipientId}`;
	await eventsStore.setItem(cacheKey, {
		data: events,
		timestamp: new Date().toISOString()
	});
}

/**
 * Get cached events
 */
export async function getCachedEvents(recipientId = 'all') {
	if (!eventsStore) return null;

	const cacheKey = `events_${recipientId}`;
	const cached = await eventsStore.getItem(cacheKey);

	if (!cached) return null;

	// Check if cache is stale (older than 1 hour when online)
	const cacheAge = Date.now() - new Date(cached.timestamp).getTime();
	const maxAge = get(isOnline) ? 60 * 60 * 1000 : Infinity; // 1 hour when online, forever when offline

	if (cacheAge > maxAge) {
		return null;
	}

	return cached.data;
}

/**
 * Store a single event locally (for optimistic updates)
 */
export async function cacheEvent(event) {
	if (!eventsStore) return;
	await eventsStore.setItem(`event_${event.id}`, event);
}

/**
 * Get a single cached event
 */
export async function getCachedEvent(eventId) {
	if (!eventsStore) return null;
	return await eventsStore.getItem(`event_${eventId}`);
}

/**
 * Remove a cached event
 */
export async function removeCachedEvent(eventId) {
	if (!eventsStore) return;
	await eventsStore.removeItem(`event_${eventId}`);
}

/**
 * Cache generic data (quick meds, quick feeds, recipients, etc.)
 */
export async function cacheData(key, data) {
	if (!cacheStore) return;
	await cacheStore.setItem(key, {
		data,
		timestamp: new Date().toISOString()
	});
}

/**
 * Get cached generic data
 */
export async function getCachedData(key, maxAgeMs = 60 * 60 * 1000) {
	if (!cacheStore) return null;

	const cached = await cacheStore.getItem(key);
	if (!cached) return null;

	const cacheAge = Date.now() - new Date(cached.timestamp).getTime();
	const effectiveMaxAge = get(isOnline) ? maxAgeMs : Infinity;

	if (cacheAge > effectiveMaxAge) {
		return null;
	}

	return cached.data;
}

/**
 * Clear all cached data
 */
export async function clearCache() {
	if (!eventsStore || !cacheStore) return;
	await eventsStore.clear();
	await cacheStore.clear();
}

/**
 * Clear the pending queue (use with caution)
 */
export async function clearPendingQueue() {
	if (!pendingQueueStore) return;
	await pendingQueueStore.clear();
	await updatePendingCount();
}

/**
 * Sync pending events with the server
 * This is called automatically when coming back online
 */
export async function syncPendingEvents() {
	if (!browser || !get(isOnline)) return;

	const pending = await getPendingActions();
	if (pending.length === 0) {
		syncStatus.set('synced');
		return;
	}

	syncStatus.set('syncing');

	// Import api dynamically to avoid circular dependency
	const { apiRequest } = await import('../services/api.js');

	let successCount = 0;
	let errorCount = 0;

	for (const action of pending) {
		try {
			let method = 'POST';
			if (action.action === 'update') method = 'PATCH';
			if (action.action === 'delete') method = 'DELETE';

			const options = {
				method,
				...(action.data && method !== 'DELETE' ? { body: JSON.stringify(action.data) } : {})
			};

			await apiRequest(action.endpoint, options);
			await removeFromQueue(action.id);
			successCount++;
		} catch (error) {
			console.error('Failed to sync action:', action, error);
			errorCount++;

			// Update retry count
			action.retries = (action.retries || 0) + 1;

			// If too many retries, remove from queue
			if (action.retries >= 5) {
				console.warn('Removing action after 5 failed retries:', action);
				await removeFromQueue(action.id);
			} else {
				// Update the item with new retry count
				await pendingQueueStore.setItem(action.id, action);
			}
		}
	}

	await updatePendingCount();
	lastSyncTime.set(new Date().toISOString());

	// Also sync pending photos after events are synced
	await syncPendingPhotos();

	await updatePendingCount();

	if (errorCount > 0 && successCount === 0) {
		syncStatus.set('error');
	} else if (get(pendingCount) > 0) {
		syncStatus.set('pending');
	} else {
		syncStatus.set('synced');
	}
}

/**
 * Derived store for sync status text
 */
export const syncStatusText = derived(
	[syncStatus, pendingCount, isOnline],
	([$syncStatus, $pendingCount, $isOnline]) => {
		if (!$isOnline) return 'Offline';
		if ($syncStatus === 'syncing') return 'Syncing...';
		if ($syncStatus === 'pending') return `${$pendingCount} pending`;
		if ($syncStatus === 'error') return 'Sync error';
		return 'Synced';
	}
);

// ============================================================================
// PHOTO QUEUE FUNCTIONS
// ============================================================================

/**
 * Queue a photo for upload when online
 * @param {string} eventId - The event ID (can be temp ID for offline events)
 * @param {Blob} blob - The image blob
 * @param {string} filename - Original filename
 * @returns {Promise<string>} Queue item ID
 */
export async function queuePhoto(eventId, blob, filename) {
	if (!photoQueueStore) return null;

	const id = generateTempId();
	const queueItem = {
		id,
		eventId,
		filename,
		blob,
		timestamp: new Date().toISOString(),
		retries: 0
	};

	await photoQueueStore.setItem(id, queueItem);
	await updatePendingCount();

	return id;
}

/**
 * Get all pending photos from the queue
 */
export async function getPendingPhotos() {
	if (!photoQueueStore) return [];

	const photos = [];
	await photoQueueStore.iterate((value) => {
		photos.push(value);
	});

	return photos.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
}

/**
 * Remove a photo from the queue
 */
export async function removePhotoFromQueue(id) {
	if (!photoQueueStore) return;
	await photoQueueStore.removeItem(id);
	await updatePendingCount();
}

/**
 * Update event ID for queued photos (when temp event ID is replaced with real ID)
 */
export async function updatePhotoEventId(tempEventId, realEventId) {
	if (!photoQueueStore) return;

	const photos = await getPendingPhotos();
	for (const photo of photos) {
		if (photo.eventId === tempEventId) {
			photo.eventId = realEventId;
			await photoQueueStore.setItem(photo.id, photo);
		}
	}
}

/**
 * Upload pending photos
 * Called after sync or when coming online
 */
export async function syncPendingPhotos() {
	if (!browser || !get(isOnline)) return;

	const pendingPhotos = await getPendingPhotos();
	if (pendingPhotos.length === 0) return;

	// Import api dynamically
	const { uploadPhoto } = await import('../services/api.js');

	for (const photo of pendingPhotos) {
		// Skip if event ID is still a temp ID (event hasn't synced yet)
		if (photo.eventId.startsWith('temp_')) {
			continue;
		}

		try {
			// Create a File from the blob
			const file = new File([photo.blob], photo.filename, { type: 'image/jpeg' });
			await uploadPhoto(photo.eventId, file);
			await removePhotoFromQueue(photo.id);
		} catch (error) {
			console.error('Failed to upload photo:', photo, error);

			photo.retries = (photo.retries || 0) + 1;
			if (photo.retries >= 5) {
				console.warn('Removing photo after 5 failed retries:', photo);
				await removePhotoFromQueue(photo.id);
			} else {
				await photoQueueStore.setItem(photo.id, photo);
			}
		}
	}
}

/**
 * Get count of pending photos for an event
 */
export async function getPendingPhotoCount(eventId) {
	if (!photoQueueStore) return 0;

	let count = 0;
	await photoQueueStore.iterate((value) => {
		if (value.eventId === eventId) count++;
	});

	return count;
}
