import { writable } from 'svelte/store';
import { getTimezone } from '$lib/services/api';

const TIMEZONE_KEY = 'app_timezone';

function loadStoredTimezone() {
	if (typeof localStorage === 'undefined') return 'local';
	const stored = localStorage.getItem(TIMEZONE_KEY);
	return stored || 'local';
}

export const timezone = writable(loadStoredTimezone());

export async function initSettings() {
	try {
		const response = await getTimezone();
		const value = response?.timezone || 'local';
		timezone.set(value);
		if (typeof localStorage !== 'undefined') {
			localStorage.setItem(TIMEZONE_KEY, value);
		}
	} catch (error) {
		// Ignore when unauthenticated.
	}
}

export function setTimezone(value) {
	timezone.set(value);
	if (typeof localStorage !== 'undefined') {
		localStorage.setItem(TIMEZONE_KEY, value);
	}
}
