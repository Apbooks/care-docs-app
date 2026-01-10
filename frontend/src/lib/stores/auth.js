import { writable } from 'svelte/store';
import { browser } from '$app/environment';

// User store with localStorage persistence
function createAuthStore() {
	// Initialize from localStorage if in browser
	const storedUser = browser ? localStorage.getItem('user') : null;
	const initialUser = storedUser ? JSON.parse(storedUser) : null;

	const { subscribe, set, update } = writable(initialUser);

	return {
		subscribe,
		setUser: (user) => {
			if (browser) {
				if (user) {
					localStorage.setItem('user', JSON.stringify(user));
				} else {
					localStorage.removeItem('user');
				}
			}
			set(user);
		},
		logout: () => {
			if (browser) {
				localStorage.removeItem('user');
			}
			set(null);
		},
		updateUser: (userData) => {
			update((user) => {
				const updatedUser = { ...user, ...userData };
				if (browser) {
					localStorage.setItem('user', JSON.stringify(updatedUser));
				}
				return updatedUser;
			});
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
