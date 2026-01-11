// API base URL - uses Vite build-time env `VITE_PUBLIC_API_URL` if provided,
// otherwise falls back to same-origin `/api`.
const API_BASE = import.meta.env.VITE_PUBLIC_API_URL || '/api';

/**
 * Make an API request with proper error handling
 * @param {string} endpoint - API endpoint (e.g., '/auth/login')
 * @param {object} options - Fetch options
 * @returns {Promise<object>} Response data
 */
export async function apiRequest(endpoint, options = {}) {
	const url = `${API_BASE}${endpoint}`;

	// Get access token from localStorage if available
	const token = typeof localStorage !== 'undefined' ? localStorage.getItem('access_token') : null;

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

		// Handle non-JSON responses
		const contentType = response.headers.get('content-type');
		if (!contentType || !contentType.includes('application/json')) {
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}
			return { success: true };
		}

		const data = await response.json();

		if (!response.ok) {
			throw new Error(data.detail || `HTTP ${response.status}`);
		}

		return data;
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

// ============================================================================
// QUICK TEMPLATES
// ============================================================================

export async function getQuickMeds(includeInactive = false) {
	const query = includeInactive ? '?include_inactive=true' : '';
	return apiRequest(`/quick-meds${query}`);
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
