// API base URL - prefers Vite build-time env, otherwise infers from hostname.
const API_BASE = (() => {
	const envBase = import.meta.env.VITE_PUBLIC_API_URL;
	if (envBase && envBase !== 'auto') return envBase;
	if (typeof window === 'undefined') return '/api';
	const { protocol, hostname } = window.location;
	if (hostname === 'caredocs.apvinyldesigns.com') {
		return `${protocol}//${hostname}/api`;
	}
	if (
		hostname === 'localhost' ||
		hostname === '127.0.0.1' ||
		hostname.startsWith('192.168.') ||
		hostname.endsWith('.local')
	) {
		return `${protocol}//${hostname}:8000/api`;
	}
	return '/api';
})();

export function getApiBase() {
	return API_BASE;
}

// Import offline stores (lazy loaded to avoid circular deps)
let offlineModule = null;
async function getOfflineModule() {
	if (!offlineModule) {
		offlineModule = await import('../stores/offline.js');
	}
	return offlineModule;
}

function getStoredToken(key) {
	return typeof localStorage !== 'undefined' ? localStorage.getItem(key) : null;
}

function setStoredToken(key, value) {
	if (typeof localStorage === 'undefined') return;
	if (value) {
		localStorage.setItem(key, value);
	} else {
		localStorage.removeItem(key);
	}
}

// Prevent duplicate refresh attempts with a promise lock
let refreshPromise = null;

async function attemptTokenRefresh() {
	// If a refresh is already in progress, wait for it
	if (refreshPromise) {
		return refreshPromise;
	}

	const refreshToken = getStoredToken('refresh_token');
	if (!refreshToken) return null;

	// Create a new refresh promise
	refreshPromise = (async () => {
		try {
			const response = await fetch(`${API_BASE}/auth/refresh`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ refresh_token: refreshToken }),
				credentials: 'include'
			});

			if (!response.ok) {
				return null;
			}

			const data = await response.json();

			// Validate response before storing
			if (!data?.access_token) {
				console.warn('Invalid refresh response: missing access_token');
				return null;
			}

			setStoredToken('access_token', data.access_token);
			if (data.refresh_token) {
				setStoredToken('refresh_token', data.refresh_token);
			}
			return data;
		} finally {
			// Clear the promise lock when done
			refreshPromise = null;
		}
	})();

	return refreshPromise;
}

export async function refreshSession() {
	try {
		return await attemptTokenRefresh();
	} catch (error) {
		console.warn('Token refresh failed:', error);
		return null;
	}
}

/**
 * Check if we're online
 */
function checkOnline() {
	return typeof navigator !== 'undefined' ? navigator.onLine : true;
}

/**
 * Make an API request with proper error handling and offline support
 * @param {string} endpoint - API endpoint (e.g., '/auth/login')
 * @param {object} options - Fetch options
 * @param {boolean} hasRetried - Whether this is a retry after token refresh
 * @param {object} offlineOptions - Options for offline handling
 * @returns {Promise<object>} Response data
 */
export async function apiRequest(endpoint, options = {}, hasRetried = false, offlineOptions = {}) {
	const url = `${API_BASE}${endpoint}`;
	const method = options.method || 'GET';

	// Get access token from localStorage if available
	const token = getStoredToken('access_token');

	const config = {
		...options,
		headers: {
			'Content-Type': 'application/json',
			...(token ? { 'Authorization': `Bearer ${token}` } : {}),
			...options.headers
		},
		credentials: 'include' // Important for cookies
	};

	// Check if we're offline
	if (!checkOnline()) {
		return handleOfflineRequest(endpoint, method, options, offlineOptions);
	}

	try {
		const response = await fetch(url, config);

		if (response.status === 401) {
			const canRefresh = !hasRetried && !endpoint.startsWith('/auth/refresh');
			if (canRefresh) {
				const refreshed = await attemptTokenRefresh();
				if (refreshed?.access_token) {
					return apiRequest(endpoint, options, true, offlineOptions);
				}
			}

			setStoredToken('access_token', null);
			setStoredToken('refresh_token', null);
			if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
				window.location.href = '/login';
			}
			throw new Error('Not authenticated');
		}

		// Handle non-JSON responses
		const contentType = response.headers.get('content-type');
		if (!contentType || !contentType.includes('application/json')) {
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}
			return { success: true };
		}

		const text = await response.text();
		const data = text ? JSON.parse(text) : null;

		if (!response.ok) {
			throw new Error((data && data.detail) || `HTTP ${response.status}`);
		}

		return data ?? { success: true };
	} catch (error) {
		// If network error and we should queue offline
		if (isNetworkError(error) && offlineOptions.queueIfOffline) {
			return handleOfflineRequest(endpoint, method, options, offlineOptions);
		}
		console.error('API request failed:', error);
		throw error;
	}
}

/**
 * Check if an error is a network error
 */
function isNetworkError(error) {
	return error instanceof TypeError && error.message.includes('fetch') ||
		error.message.includes('network') ||
		error.message.includes('Failed to fetch') ||
		error.name === 'NetworkError';
}

/**
 * Handle offline requests by queueing them for later sync
 */
async function handleOfflineRequest(endpoint, method, options, offlineOptions) {
	const offline = await getOfflineModule();

	// For GET requests, try to return cached data
	if (method === 'GET') {
		const cacheKey = offlineOptions.cacheKey || endpoint;
		const cachedData = await offline.getCachedData(cacheKey);
		if (cachedData) {
			return cachedData;
		}
		throw new Error('No cached data available offline');
	}

	// For write operations, queue them for later sync
	if (['POST', 'PATCH', 'DELETE'].includes(method)) {
		const data = options.body ? JSON.parse(options.body) : null;

		// Generate temp ID for new items
		const tempId = offlineOptions.tempId || `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

		const queueItem = await offline.queueOfflineAction({
			type: method === 'POST' ? 'create' : method === 'DELETE' ? 'delete' : 'update',
			endpoint,
			data
		});

		// Return optimistic response for creates
		if (method === 'POST' && data) {
			const optimisticResponse = {
				...data,
				id: tempId,
				_offline: true,
				_queueId: queueItem?.id,
				created_at: new Date().toISOString(),
				updated_at: new Date().toISOString()
			};

			// Cache the optimistic response
			if (offlineOptions.cacheKey) {
				await offline.cacheData(`${offlineOptions.cacheKey}_${tempId}`, optimisticResponse);
			}

			return optimisticResponse;
		}

		// Return success for updates/deletes
		return { success: true, _offline: true, _queueId: queueItem?.id };
	}

	throw new Error('Cannot perform this operation offline');
}

/**
 * Login user
 * @param {string} username
 * @param {string} password
 * @returns {Promise<object>} User data and tokens
 */
export async function login(username, password) {
	return apiRequest('/auth/login', {
		method: 'POST',
		body: JSON.stringify({ username, password })
	});
}

/**
 * Logout user
 * @returns {Promise<object>}
 */
export async function logout() {
	return apiRequest('/auth/logout', {
		method: 'POST'
	});
}

/**
 * Get current user info
 * @returns {Promise<object>} User data
 */
export async function getCurrentUser() {
	return apiRequest('/auth/me');
}

export async function updateCurrentUserProfile(data) {
	return apiRequest('/auth/me', {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

export async function updateCurrentUserEmail(data) {
	return apiRequest('/auth/me/email', {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

export async function updateCurrentUserPassword(data) {
	return apiRequest('/auth/me/password', {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

export async function uploadAvatar(file) {
	const url = `${API_BASE}/auth/me/avatar`;
	const token = getStoredToken('access_token');
	const formData = new FormData();
	formData.append('file', file);

	const response = await fetch(url, {
		method: 'POST',
		headers: {
			...(token ? { 'Authorization': `Bearer ${token}` } : {})
		},
		credentials: 'include',
		body: formData
	});

	if (!response.ok) {
		const data = await response.json().catch(() => ({}));
		throw new Error(data.detail || `HTTP ${response.status}`);
	}

	return response.json();
}

/**
 * Register a new user (admin only)
 * @param {object} userData - { username, email, password, role }
 * @returns {Promise<object>} Created user data
 */
export async function registerUser(userData) {
	return apiRequest('/auth/register', {
		method: 'POST',
		body: JSON.stringify(userData)
	});
}

export async function requestPasswordReset(email) {
	return publicRequest('/auth/password-reset/request', {
		method: 'POST',
		body: JSON.stringify({ email })
	});
}

export async function confirmPasswordReset(payload) {
	return publicRequest('/auth/password-reset/confirm', {
		method: 'POST',
		body: JSON.stringify(payload)
	});
}

// ============================================================================
// INVITES + USER ACCESS (Admin)
// ============================================================================

async function publicRequest(endpoint, options = {}) {
	const url = `${API_BASE}${endpoint}`;
	const response = await fetch(url, {
		...options,
		headers: {
			'Content-Type': 'application/json',
			...options.headers
		},
		credentials: 'include'
	});

	const contentType = response.headers.get('content-type');
	const text = await response.text();
	const data = text && contentType?.includes('application/json') ? JSON.parse(text) : null;

	if (!response.ok) {
		throw new Error((data && data.detail) || `HTTP ${response.status}`);
	}

	return data ?? { success: true };
}

export async function createInvite(data) {
	return apiRequest('/invites', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

export async function getInvite(token) {
	return publicRequest(`/invites/${token}`);
}

export async function acceptInvite(token, data) {
	return publicRequest(`/invites/${token}/accept`, {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

export async function listInvites() {
	return apiRequest('/invites');
}

export async function revokeInvite(token) {
	return apiRequest(`/invites/${token}`, {
		method: 'DELETE'
	});
}

export async function getUserRecipientAccess(userId) {
	return apiRequest(`/auth/users/${userId}/recipients`);
}

export async function updateUserRecipientAccess(userId, recipientIds) {
	return apiRequest(`/auth/users/${userId}/recipients`, {
		method: 'PUT',
		body: JSON.stringify({ recipient_ids: recipientIds })
	});
}

/**
 * Refresh access token
 * @param {string} refreshToken
 * @returns {Promise<object>} New tokens
 */
export async function refreshAccessToken(refreshToken) {
	return apiRequest('/auth/refresh', {
		method: 'POST',
		body: JSON.stringify({ refresh_token: refreshToken })
	});
}

// ============================================================================
// EVENT ENDPOINTS (with offline support)
// ============================================================================

/**
 * Create a new care event (supports offline queueing)
 * @param {object} eventData - { type, timestamp, notes, metadata }
 * @returns {Promise<object>} Created event
 */
export async function createEvent(eventData) {
	const result = await apiRequest('/events/', {
		method: 'POST',
		body: JSON.stringify(eventData)
	}, false, {
		queueIfOffline: true,
		cacheKey: 'events'
	});

	// Cache events after successful online creation
	if (result && !result._offline) {
		try {
			const offline = await getOfflineModule();
			await offline.cacheEvent(result);
		} catch (e) {
			// Caching is best-effort
		}
	}

	return result;
}

/**
 * Get list of events (with offline cache support)
 * @param {object} params - { type, limit, offset }
 * @returns {Promise<array>} Array of events
 */
export async function getEvents(params = {}) {
	const queryParams = new URLSearchParams();

	if (params.type) queryParams.append('type', params.type);
	if (params.limit) queryParams.append('limit', params.limit.toString());
	if (params.offset) queryParams.append('offset', params.offset.toString());
	if (params.start) queryParams.append('start', params.start);
	if (params.end) queryParams.append('end', params.end);
	if (params.q) queryParams.append('q', params.q);
	if (params.recipient_id) queryParams.append('recipient_id', params.recipient_id);

	const query = queryParams.toString();
	const endpoint = `/events/${query ? '?' + query : ''}`;
	const cacheKey = `events_${params.recipient_id || 'all'}`;

	try {
		const result = await apiRequest(endpoint, {}, false, { cacheKey });

		// Cache successful results
		if (Array.isArray(result)) {
			try {
				const offline = await getOfflineModule();
				await offline.cacheEvents(result, params.recipient_id || 'all');
			} catch (e) {
				// Caching is best-effort
			}
		}

		return result;
	} catch (error) {
		// Try to return cached data if offline
		if (!checkOnline() || isNetworkError(error)) {
			try {
				const offline = await getOfflineModule();
				const cached = await offline.getCachedEvents(params.recipient_id || 'all');
				if (cached) {
					return cached;
				}
			} catch (e) {
				// Fall through to throw original error
			}
		}
		throw error;
	}
}

/**
 * Get a specific event by ID
 * @param {string} eventId
 * @returns {Promise<object>} Event data
 */
export async function getEvent(eventId) {
	try {
		return await apiRequest(`/events/${eventId}`);
	} catch (error) {
		// Try cache if offline
		if (!checkOnline() || isNetworkError(error)) {
			try {
				const offline = await getOfflineModule();
				const cached = await offline.getCachedEvent(eventId);
				if (cached) return cached;
			} catch (e) {
				// Fall through
			}
		}
		throw error;
	}
}

/**
 * Update an event (supports offline queueing)
 * @param {string} eventId
 * @param {object} updates - { notes, metadata }
 * @returns {Promise<object>} Updated event
 */
export async function updateEvent(eventId, updates) {
	return apiRequest(`/events/${eventId}`, {
		method: 'PATCH',
		body: JSON.stringify(updates)
	}, false, {
		queueIfOffline: true
	});
}

/**
 * Delete an event (supports offline queueing)
 * @param {string} eventId
 * @returns {Promise<object>}
 */
export async function deleteEvent(eventId) {
	const result = await apiRequest(`/events/${eventId}`, {
		method: 'DELETE'
	}, false, {
		queueIfOffline: true
	});

	// Remove from cache
	try {
		const offline = await getOfflineModule();
		await offline.removeCachedEvent(eventId);
	} catch (e) {
		// Best effort
	}

	return result;
}

/**
 * Get event statistics (with caching)
 * @returns {Promise<object>} Event counts by type
 */
export async function getEventStats() {
	return apiRequest('/events/stats/summary', {}, false, {
		cacheKey: 'event_stats'
	});
}

export async function getEventStatsForRecipient(recipientId) {
	const query = recipientId ? `?recipient_id=${encodeURIComponent(recipientId)}` : '';
	return apiRequest(`/events/stats/summary${query}`, {}, false, {
		cacheKey: `event_stats_${recipientId || 'all'}`
	});
}

// ============================================================================
// QUICK TEMPLATES (with offline caching)
// ============================================================================

export async function getQuickMeds(includeInactive = false) {
	const query = includeInactive ? '?include_inactive=true' : '';
	const cacheKey = `quick_meds_${includeInactive ? 'all' : 'active'}`;

	try {
		const result = await apiRequest(`/quick-meds${query}`);

		// Cache results
		if (Array.isArray(result)) {
			try {
				const offline = await getOfflineModule();
				await offline.cacheData(cacheKey, result);
			} catch (e) {}
		}

		return result;
	} catch (error) {
		if (!checkOnline() || isNetworkError(error)) {
			try {
				const offline = await getOfflineModule();
				const cached = await offline.getCachedData(cacheKey);
				if (cached) return cached;
			} catch (e) {}
		}
		throw error;
	}
}

export async function getQuickMedsForRecipient(recipientId, includeInactive = false) {
	const params = new URLSearchParams();
	if (includeInactive) params.append('include_inactive', 'true');
	if (recipientId) params.append('recipient_id', recipientId);
	params.append('quick_only', 'true');
	const query = params.toString();
	const cacheKey = `quick_meds_${recipientId || 'all'}_${includeInactive ? 'all' : 'active'}`;

	try {
		const result = await apiRequest(`/medications${query ? '?' + query : ''}`);

		if (Array.isArray(result)) {
			try {
				const offline = await getOfflineModule();
				await offline.cacheData(cacheKey, result);
			} catch (e) {}
		}

		return result;
	} catch (error) {
		if (!checkOnline() || isNetworkError(error)) {
			try {
				const offline = await getOfflineModule();
				const cached = await offline.getCachedData(cacheKey);
				if (cached) return cached;
			} catch (e) {}
		}
		throw error;
	}
}

export async function createQuickMed(data) {
	return apiRequest('/quick-meds', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

export async function updateQuickMed(medId, data) {
	return apiRequest(`/quick-meds/${medId}`, {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

export async function deleteQuickMed(medId) {
	return apiRequest(`/quick-meds/${medId}`, {
		method: 'DELETE'
	});
}

export async function getQuickFeeds(includeInactive = false) {
	const query = includeInactive ? '?include_inactive=true' : '';
	const cacheKey = `quick_feeds_${includeInactive ? 'all' : 'active'}`;

	try {
		const result = await apiRequest(`/quick-feeds${query}`);

		if (Array.isArray(result)) {
			try {
				const offline = await getOfflineModule();
				await offline.cacheData(cacheKey, result);
			} catch (e) {}
		}

		return result;
	} catch (error) {
		if (!checkOnline() || isNetworkError(error)) {
			try {
				const offline = await getOfflineModule();
				const cached = await offline.getCachedData(cacheKey);
				if (cached) return cached;
			} catch (e) {}
		}
		throw error;
	}
}

export async function getQuickFeedsForRecipient(recipientId, includeInactive = false) {
	const params = new URLSearchParams();
	if (includeInactive) params.append('include_inactive', 'true');
	if (recipientId) params.append('recipient_id', recipientId);
	const query = params.toString();
	const cacheKey = `quick_feeds_${recipientId || 'all'}_${includeInactive ? 'all' : 'active'}`;

	try {
		const result = await apiRequest(`/quick-feeds${query ? '?' + query : ''}`);

		if (Array.isArray(result)) {
			try {
				const offline = await getOfflineModule();
				await offline.cacheData(cacheKey, result);
			} catch (e) {}
		}

		return result;
	} catch (error) {
		if (!checkOnline() || isNetworkError(error)) {
			try {
				const offline = await getOfflineModule();
				const cached = await offline.getCachedData(cacheKey);
				if (cached) return cached;
			} catch (e) {}
		}
		throw error;
	}
}

export async function createQuickFeed(data) {
	return apiRequest('/quick-feeds', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

export async function updateQuickFeed(feedId, data) {
	return apiRequest(`/quick-feeds/${feedId}`, {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

export async function deleteQuickFeed(feedId) {
	return apiRequest(`/quick-feeds/${feedId}`, {
		method: 'DELETE'
	});
}

// ============================================================================
// SETTINGS
// ============================================================================

export async function getTimezone() {
	return apiRequest('/settings/timezone');
}

export async function updateTimezone(timezone) {
	return apiRequest('/settings/timezone', {
		method: 'PUT',
		body: JSON.stringify({ timezone })
	});
}

export async function getNotificationSettings() {
	return apiRequest('/settings/notifications');
}

export async function updateNotificationSettings(settings) {
	return apiRequest('/settings/notifications', {
		method: 'PUT',
		body: JSON.stringify(settings)
	});
}

// ============================================================================
// PUSH NOTIFICATIONS
// ============================================================================

export async function getVapidPublicKey() {
	return apiRequest('/notifications/vapid-public-key');
}

export async function listPushSubscriptions() {
	return apiRequest('/notifications/subscriptions');
}

export async function subscribePush(subscription) {
	return apiRequest('/notifications/subscribe', {
		method: 'POST',
		body: JSON.stringify(subscription)
	});
}

export async function unsubscribePush(subscription) {
	return apiRequest('/notifications/unsubscribe', {
		method: 'POST',
		body: JSON.stringify(subscription)
	});
}

export async function sendTestNotification(data) {
	return apiRequest('/notifications/test', {
		method: 'POST',
		body: JSON.stringify(data || {})
	});
}

// ============================================================================
// CONTINUOUS FEED
// ============================================================================

export async function getActiveContinuousFeed(recipientId) {
	const query = recipientId ? `?recipient_id=${encodeURIComponent(recipientId)}` : '';
	return apiRequest(`/feeds/continuous/active${query}`);
}

export async function startContinuousFeed(data) {
	return apiRequest('/feeds/continuous/start', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

export async function stopContinuousFeed(recipientId, pumpTotalMl) {
	return apiRequest('/feeds/continuous/stop', {
		method: 'POST',
		body: JSON.stringify({ recipient_id: recipientId, pump_total_ml: pumpTotalMl ?? null })
	});
}

// ============================================================================
// CARE RECIPIENTS (with offline caching)
// ============================================================================

export async function getRecipients(includeInactive = false) {
	const query = includeInactive ? '?include_inactive=true' : '';
	const cacheKey = `recipients_${includeInactive ? 'all' : 'active'}`;

	try {
		const result = await apiRequest(`/recipients${query}`);

		if (Array.isArray(result)) {
			try {
				const offline = await getOfflineModule();
				await offline.cacheData(cacheKey, result);
			} catch (e) {}
		}

		return result;
	} catch (error) {
		if (!checkOnline() || isNetworkError(error)) {
			try {
				const offline = await getOfflineModule();
				const cached = await offline.getCachedData(cacheKey);
				if (cached) return cached;
			} catch (e) {}
		}
		throw error;
	}
}

export async function createRecipient(data) {
	return apiRequest('/recipients', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

export async function updateRecipient(recipientId, data) {
	return apiRequest(`/recipients/${recipientId}`, {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

export async function deleteRecipient(recipientId) {
	return apiRequest(`/recipients/${recipientId}`, {
		method: 'DELETE'
	});
}

// ============================================================================
// PHOTOS
// ============================================================================

/**
 * Upload a photo to an event
 * @param {string} eventId - Event ID to attach photo to
 * @param {File} file - Image file to upload
 * @returns {Promise<object>} Photo metadata
 */
export async function uploadPhoto(eventId, file) {
	const url = `${API_BASE}/photos/`;
	const token = getStoredToken('access_token');

	const formData = new FormData();
	formData.append('file', file);
	formData.append('event_id', eventId);

	const response = await fetch(url, {
		method: 'POST',
		headers: {
			...(token ? { 'Authorization': `Bearer ${token}` } : {})
		},
		credentials: 'include',
		body: formData
	});

	if (!response.ok) {
		const data = await response.json().catch(() => ({}));
		throw new Error(data.detail || `HTTP ${response.status}`);
	}

	return response.json();
}

/**
 * Get photos for an event
 * @param {string} eventId - Event ID
 * @returns {Promise<array>} Array of photo metadata
 */
export async function getEventPhotos(eventId) {
	return apiRequest(`/photos/event/${eventId}`);
}

/**
 * Get photo count for an event (lightweight)
 * @param {string} eventId - Event ID
 * @returns {Promise<object>} { event_id, count }
 */
export async function getPhotoCount(eventId) {
	return apiRequest(`/photos/count/${eventId}`);
}

/**
 * Delete a photo
 * @param {string} photoId - Photo ID to delete
 * @returns {Promise<void>}
 */
export async function deletePhoto(photoId) {
	return apiRequest(`/photos/${photoId}`, {
		method: 'DELETE'
	});
}

// ============================================================================
// MEDICATIONS + REMINDERS
// ============================================================================

export async function getMedications(params = {}) {
	const queryParams = new URLSearchParams();
	if (params.recipient_id) queryParams.append('recipient_id', params.recipient_id);
	if (params.include_inactive) queryParams.append('include_inactive', 'true');
	const query = queryParams.toString();
	return apiRequest(`/medications${query ? '?' + query : ''}`);
}

export async function createMedication(data) {
	return apiRequest('/medications', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

export async function updateMedication(medId, data) {
	return apiRequest(`/medications/${medId}`, {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

export async function deleteMedication(medId) {
	return apiRequest(`/medications/${medId}`, {
		method: 'DELETE'
	});
}

export async function getMedReminders(params = {}) {
	const queryParams = new URLSearchParams();
	if (params.recipient_id) queryParams.append('recipient_id', params.recipient_id);
	if (params.include_disabled) queryParams.append('include_disabled', 'true');
	const query = queryParams.toString();
	return apiRequest(`/med-reminders${query ? '?' + query : ''}`);
}

export async function createMedReminder(data) {
	return apiRequest('/med-reminders', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

export async function updateMedReminder(reminderId, data) {
	return apiRequest(`/med-reminders/${reminderId}`, {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

export async function skipMedReminder(reminderId) {
	return apiRequest(`/med-reminders/${reminderId}/skip`, {
		method: 'POST'
	});
}

export async function logMedReminder(reminderId) {
	return apiRequest(`/med-reminders/${reminderId}/log`, {
		method: 'POST'
	});
}

export async function getNextMedReminders(recipientId, limit = 10) {
	const queryParams = new URLSearchParams();
	queryParams.append('recipient_id', recipientId);
	queryParams.append('limit', limit.toString());
	return apiRequest(`/med-reminders/next?${queryParams.toString()}`);
}

export async function checkMedEarly(data) {
	return apiRequest('/med-reminders/check-early', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}
