import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import localforage from 'localforage';

// Configure a dedicated store for auth data (more reliable than localStorage for PWA)
const authStorage = browser ? localforage.createInstance({
	name: 'care-docs',
	storeName: 'auth'
}) : null;

// User store with dual persistence (localStorage for sync access, IndexedDB for reliability)
function createAuthStore() {
	// Initialize from localStorage if in browser (synchronous for immediate access)
	const storedUser = browser ? localStorage.getItem('user') : null;
	const initialUser = storedUser ? JSON.parse(storedUser) : null;

	const { subscribe, set, update } = writable(initialUser);

	// Also try to load from IndexedDB (async, will update if different)
	if (browser && authStorage) {
		authStorage.getItem('user').then((idbUser) => {
			if (idbUser && !initialUser) {
				// IndexedDB has user but localStorage doesn't - restore
				localStorage.setItem('user', JSON.stringify(idbUser));
				set(idbUser);
			}
		}).catch(() => {
			// Ignore errors on initial load
		});
	}

	return {
		subscribe,
		setUser: async (user) => {
			if (browser) {
				if (user) {
					localStorage.setItem('user', JSON.stringify(user));
					// Also persist to IndexedDB for offline reliability
					if (authStorage) {
						try {
							await authStorage.setItem('user', user);
						} catch (e) {
							console.warn('Failed to persist user to IndexedDB:', e);
						}
					}
				} else {
					localStorage.removeItem('user');
					if (authStorage) {
						try {
							await authStorage.removeItem('user');
						} catch (e) {}
					}
				}
			}
			set(user);
		},
		logout: async () => {
			if (browser) {
				localStorage.removeItem('user');
				localStorage.removeItem('access_token');
				localStorage.removeItem('refresh_token');
				if (authStorage) {
					try {
						await authStorage.removeItem('user');
						await authStorage.removeItem('tokens');
					} catch (e) {}
				}
			}
			set(null);
		},
		updateUser: async (userData) => {
			update((user) => {
				const updatedUser = { ...user, ...userData };
				if (browser) {
					localStorage.setItem('user', JSON.stringify(updatedUser));
					if (authStorage) {
						authStorage.setItem('user', updatedUser).catch(() => {});
					}
				}
				return updatedUser;
			});
		},
		// Check if user can work offline (has valid cached credentials)
		canWorkOffline: async () => {
			if (!browser || !authStorage) return false;
			try {
				const user = await authStorage.getItem('user');
				const tokens = await authStorage.getItem('tokens');
				return !!(user && tokens?.refresh_token);
			} catch {
				return false;
			}
		},
		// Persist tokens to IndexedDB for offline access
		persistTokens: async (accessToken, refreshToken) => {
			if (!browser || !authStorage) return;
			try {
				await authStorage.setItem('tokens', {
					access_token: accessToken,
					refresh_token: refreshToken,
					persisted_at: new Date().toISOString()
				});
			} catch (e) {
				console.warn('Failed to persist tokens:', e);
			}
		},
		// Get persisted tokens
		getPersistedTokens: async () => {
			if (!browser || !authStorage) return null;
			try {
				return await authStorage.getItem('tokens');
			} catch {
				return null;
			}
		}
	};
}

export const authStore = createAuthStore();

// Derived store for checking if user is authenticated
export const isAuthenticated = {
	subscribe: (callback) => {
		return authStore.subscribe((user) => {
			callback(!!user);
		});
	}
};

// Derived store for checking if user is admin
export const isAdmin = {
	subscribe: (callback) => {
		return authStore.subscribe((user) => {
			callback(user?.role === 'admin');
		});
	}
};
