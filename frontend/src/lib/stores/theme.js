import { writable } from 'svelte/store';

const THEME_KEY = 'theme';

function getInitialTheme() {
	if (typeof localStorage === 'undefined') {
		return 'light';
	}

	const stored = localStorage.getItem(THEME_KEY);
	if (stored === 'light' || stored === 'dark') {
		return stored;
	}

	if (typeof window !== 'undefined' && window.matchMedia) {
		return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
	}

	return 'light';
}

function applyTheme(value) {
	if (typeof document !== 'undefined') {
		document.documentElement.classList.toggle('dark', value === 'dark');
	}

	if (typeof localStorage !== 'undefined') {
		localStorage.setItem(THEME_KEY, value);
	}
}

export const theme = writable('light');

export function initTheme() {
	const value = getInitialTheme();
	theme.set(value);
	applyTheme(value);
}

export function toggleTheme() {
	theme.update((current) => {
		const next = current === 'dark' ? 'light' : 'dark';
		applyTheme(next);
		return next;
	});
}
