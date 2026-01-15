// API base URL - uses Vite build-time env `VITE_PUBLIC_API_URL` if provided,
// otherwise falls back to same-origin `/api`.
const API_BASE = import.meta.env.VITE_PUBLIC_API_URL || '/api';

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
 * Make an API request with proper error handling
 * @param {string} endpoint - API endpoint (e.g., '/auth/login')
 * @param {object} options - Fetch options
 * @returns {Promise<object>} Response data
 */
export async function apiRequest(endpoint, options = {}, hasRetried = false) {
	const url = `${API_BASE}${endpoint}`;

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

	try {
		const response = await fetch(url, config);

		if (response.status === 401) {
			const canRefresh = !hasRetried && !endpoint.startsWith('/auth/refresh');
			if (canRefresh) {
				const refreshed = await attemptTokenRefresh();
				if (refreshed?.access_token) {
					return apiRequest(endpoint, options, true);
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
		console.error('API request failed:', error);
		throw error;
	}
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
// EVENT ENDPOINTS
// ============================================================================

/**
 * Create a new care event
 * @param {object} eventData - { type, timestamp, notes, metadata }
 * @returns {Promise<object>} Created event
 */
export async function createEvent(eventData) {
	return apiRequest('/events/', {
		method: 'POST',
		body: JSON.stringify(eventData)
	});
}

/**
 * Get list of events
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
	return apiRequest(`/events/${query ? '?' + query : ''}`);
}

/**
 * Get a specific event by ID
 * @param {string} eventId
 * @returns {Promise<object>} Event data
 */
export async function getEvent(eventId) {
	return apiRequest(`/events/${eventId}`);
}

/**
 * Update an event
 * @param {string} eventId
 * @param {object} updates - { notes, metadata }
 * @returns {Promise<object>} Updated event
 */
export async function updateEvent(eventId, updates) {
	return apiRequest(`/events/${eventId}`, {
		method: 'PATCH',
		body: JSON.stringify(updates)
	});
}

/**
 * Delete an event
 * @param {string} eventId
 * @returns {Promise<object>}
 */
export async function deleteEvent(eventId) {
	return apiRequest(`/events/${eventId}`, {
		method: 'DELETE'
	});
}

/**
 * Get event statistics
 * @returns {Promise<object>} Event counts by type
 */
export async function getEventStats() {
	return apiRequest('/events/stats/summary');
}

export async function getEventStatsForRecipient(recipientId) {
	const query = recipientId ? `?recipient_id=${encodeURIComponent(recipientId)}` : '';
	return apiRequest(`/events/stats/summary${query}`);
}

// ============================================================================
// QUICK TEMPLATES
// ============================================================================

export async function getQuickMeds(includeInactive = false) {
	const query = includeInactive ? '?include_inactive=true' : '';
	return apiRequest(`/quick-meds${query}`);
}

export async function getQuickMedsForRecipient(recipientId, includeInactive = false) {
	const params = new URLSearchParams();
	if (includeInactive) params.append('include_inactive', 'true');
	if (recipientId) params.append('recipient_id', recipientId);
	const query = params.toString();
	return apiRequest(`/quick-meds${query ? '?' + query : ''}`);
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
	return apiRequest(`/quick-feeds${query}`);
}

export async function getQuickFeedsForRecipient(recipientId, includeInactive = false) {
	const params = new URLSearchParams();
	if (includeInactive) params.append('include_inactive', 'true');
	if (recipientId) params.append('recipient_id', recipientId);
	const query = params.toString();
	return apiRequest(`/quick-feeds${query ? '?' + query : ''}`);
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
// CARE RECIPIENTS
// ============================================================================

export async function getRecipients(includeInactive = false) {
	const query = includeInactive ? '?include_inactive=true' : '';
	return apiRequest(`/recipients${query}`);
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
