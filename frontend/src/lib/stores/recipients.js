import { writable } from 'svelte/store';
import { getRecipients } from '$lib/services/api';

const RECIPIENT_KEY = 'selected_recipient_id';

function loadStoredRecipient() {
	if (typeof localStorage === 'undefined') return null;
	return localStorage.getItem(RECIPIENT_KEY);
}

export const recipients = writable([]);
export const selectedRecipientId = writable(loadStoredRecipient());

export function setSelectedRecipient(id) {
	selectedRecipientId.set(id);
	if (typeof localStorage !== 'undefined') {
		if (id) {
			localStorage.setItem(RECIPIENT_KEY, id);
		} else {
			localStorage.removeItem(RECIPIENT_KEY);
		}
	}
}

export async function initRecipients() {
	try {
		const list = await getRecipients();
		recipients.set(list);
		const active = list.filter((recipient) => recipient.is_active);
		const stored = loadStoredRecipient();
		const storedRecipient = list.find((recipient) => recipient.id === stored);
		if (storedRecipient) {
			setSelectedRecipient(storedRecipient.id);
		} else if (active.length > 0) {
			setSelectedRecipient(active[0].id);
		} else {
			setSelectedRecipient(null);
		}
	} catch (error) {
		// Only log non-401 errors (401 means user is not authenticated yet)
		if (error?.message !== 'Not authenticated') {
			console.warn('Failed to load recipients:', error);
		}
	}
}
