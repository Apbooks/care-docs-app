<script>
	import { onMount } from 'svelte';
	import { getEvents, updateEvent, deleteEvent } from '$lib/services/api';

	export let limit = 10;
	export let type = null;

	let events = [];
	let loading = true;
	let error = '';
	let editEvent = null;
	let editLoading = false;
	let editError = '';
	let deleteTargetId = null;

	onMount(async () => {
		await loadEvents();
	});

	async function loadEvents() {
		loading = true;
		error = '';

		try {
			const params = { limit };
			if (type) params.type = type;

			events = await getEvents(params);
		} catch (err) {
			error = err.message || 'Failed to load events';
		} finally {
			loading = false;
		}
	}

	function getEventIcon(eventType) {
		const icons = {
			medication: '💊',
			feeding: '🍼',
			diaper: '👶',
			demeanor: '😊',
			observation: '📝'
		};
		return icons[eventType] || '📝';
	}

	function getEventBadgeClass(eventType) {
		const classes = {
			medication: 'bg-blue-100 text-blue-800',
			feeding: 'bg-green-100 text-green-800',
			diaper: 'bg-yellow-100 text-yellow-800',
			demeanor: 'bg-purple-100 text-purple-800',
			observation: 'bg-gray-100 text-gray-800'
		};
		return classes[eventType] || 'bg-gray-100 text-gray-800';
	}

	function formatTime(timestamp) {
		const date = new Date(timestamp);
		const time = date.toLocaleTimeString('en-US', {
			hour: 'numeric',
			minute: '2-digit'
		});
		const day = date.toLocaleDateString('en-US', {
			year: '2-digit',
			month: 'numeric',
			day: 'numeric'
		});
		return `${time} ${day}`;
	}

	function formatMetadata(event) {
		const { metadata, type } = event;

		switch (type) {
			case 'medication':
				return `${metadata.med_name} - ${metadata.dosage} (${metadata.route})`;
			case 'feeding':
				let parts = [];
				if (metadata.amount_ml) parts.push(`${metadata.amount_ml}ml`);
				if (metadata.duration_min) parts.push(`${metadata.duration_min} min`);
				if (metadata.formula_type) parts.push(metadata.formula_type);
				return parts.join(', ') || 'Feeding session';
			case 'diaper':
				let desc = `${metadata.condition}`;
				if (metadata.rash) desc += ', rash present';
				return desc.charAt(0).toUpperCase() + desc.slice(1);
			case 'demeanor':
				return `${metadata.mood} - ${metadata.activity_level.replace('_', ' ')}`;
			default:
				return event.notes || 'No details';
		}
	}

	function toDateTimeLocal(value) {
		if (!value) return '';
		const date = new Date(value);
		const offsetMs = date.getTimezoneOffset() * 60000;
		const local = new Date(date.getTime() - offsetMs);
		return local.toISOString().slice(0, 16);
	}

	function startEdit(event) {
		editError = '';
		editEvent = {
			id: event.id,
			type: event.type,
			timestamp: toDateTimeLocal(event.timestamp),
			notes: event.notes || '',
			metadata: JSON.parse(JSON.stringify(event.metadata || {}))
		};
	}

	function closeEdit() {
		editEvent = null;
		editError = '';
	}

	async function saveEdit() {
		if (!editEvent) return;
		editError = '';
		editLoading = true;

		try {
			const payload = {
				type: editEvent.type,
				timestamp: editEvent.timestamp ? new Date(editEvent.timestamp).toISOString() : null,
				notes: editEvent.notes || null,
				metadata: editEvent.metadata || {}
			};

			const updated = await updateEvent(editEvent.id, payload);
			events = events.map(item => item.id === updated.id ? updated : item);
			closeEdit();
		} catch (err) {
			editError = err.message || 'Failed to update event';
		} finally {
			editLoading = false;
		}
	}

	async function confirmDelete(eventId) {
		deleteTargetId = eventId;
	}

	async function handleDelete(eventId) {
		try {
			await deleteEvent(eventId);
			events = events.filter(item => item.id !== eventId);
			deleteTargetId = null;
		} catch (err) {
			error = err.message || 'Failed to delete event';
		}
	}

	// Export refresh function so parent can call it
	export function refresh() {
		loadEvents();
	}
</script>

<div class="space-y-4">
	{#if loading}
		<div class="text-center py-10">
			<div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto"></div>
			<p class="mt-3 text-gray-600 dark:text-slate-300 text-base">Loading events...</p>
		</div>
	{:else if error}
		<div class="p-4 bg-red-50 border border-red-200 rounded-lg dark:bg-red-950 dark:border-red-900">
			<p class="text-red-800 dark:text-red-200 text-base">{error}</p>
		</div>
	{:else if events.length === 0}
		<div class="text-center py-10">
			<p class="text-gray-600 dark:text-slate-300 text-base">No events recorded yet</p>
			<p class="text-sm text-gray-500 dark:text-slate-400 mt-1">Tap the + button to create your first entry</p>
		</div>
	{:else}
		{#each events as event (event.id)}
			<div class="bg-white dark:bg-slate-900 rounded-xl shadow p-5 hover:shadow-md transition-shadow">
				<div class="flex items-start gap-3">
					<!-- Event Icon -->
					<div class="text-3xl flex-shrink-0">
						{getEventIcon(event.type)}
					</div>

					<!-- Event Details -->
					<div class="flex-1 min-w-0">
						<div class="flex items-start justify-between gap-2">
							<div class="flex-1">
								<h3 class="font-semibold text-gray-900 dark:text-slate-100 capitalize text-base">
									{event.type.replace('_', ' ')}
								</h3>
								<p class="text-base text-gray-600 dark:text-slate-300 mt-1">
									{formatMetadata(event)}
								</p>
								{#if event.notes && event.type !== 'observation'}
									<p class="text-sm text-gray-500 dark:text-slate-400 mt-1 italic">
										{event.notes}
									</p>
								{/if}
							</div>

							<!-- Time Badge -->
							<span class={`px-3 py-1.5 text-xs font-semibold rounded-full whitespace-nowrap ${getEventBadgeClass(event.type)}`}>
								{formatTime(event.timestamp)}
							</span>
						</div>

						<!-- User Info -->
						<div class="mt-3 flex items-center gap-2 text-xs text-gray-500 dark:text-slate-400">
							<svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
								<path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd" />
							</svg>
							<span>{event.user_name}</span>
						</div>

						<!-- Actions -->
						<div class="mt-4 flex items-center gap-3">
							<button
								on:click={() => startEdit(event)}
								class="px-3 py-2 text-xs font-semibold rounded-full border border-slate-200 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
							>
								Edit
							</button>
							{#if deleteTargetId === event.id}
								<button
									on:click={() => handleDelete(event.id)}
									class="px-3 py-2 text-xs font-semibold rounded-full bg-red-600 text-white hover:bg-red-700"
								>
									Confirm Delete
								</button>
								<button
									on:click={() => deleteTargetId = null}
									class="px-3 py-2 text-xs font-semibold rounded-full border border-slate-200 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
								>
									Cancel
								</button>
							{:else}
								<button
									on:click={() => confirmDelete(event.id)}
									class="px-3 py-2 text-xs font-semibold rounded-full border border-red-200 text-red-600 hover:bg-red-50 dark:border-red-800 dark:text-red-200 dark:hover:bg-red-950"
								>
									Delete
								</button>
							{/if}
						</div>
					</div>
				</div>
			</div>
		{/each}
	{/if}
</div>

{#if editEvent}
	<div class="fixed inset-0 bg-black/60 z-50" on:click={closeEdit}></div>
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4">
		<div class="w-full max-w-lg bg-white dark:bg-slate-900 rounded-2xl shadow-xl" on:click|stopPropagation>
			<div class="p-6 border-b border-gray-200 dark:border-slate-800">
				<h3 class="text-xl font-semibold text-gray-900 dark:text-slate-100">Edit Event</h3>
				<p class="text-sm text-gray-600 dark:text-slate-400 mt-1">Update time, type, and details.</p>
			</div>
			<div class="p-6 space-y-4">
				{#if editError}
					<div class="p-3 bg-red-50 border border-red-200 rounded-xl dark:bg-red-950 dark:border-red-900">
						<p class="text-red-800 dark:text-red-200 text-sm">{editError}</p>
					</div>
				{/if}

				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Event Type</label>
					<select
						bind:value={editEvent.type}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
					>
						<option value="medication">Medication</option>
						<option value="feeding">Feeding</option>
						<option value="diaper">Diaper</option>
						<option value="demeanor">Demeanor</option>
						<option value="observation">Observation</option>
					</select>
				</div>

				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Time</label>
					<input
						type="datetime-local"
						bind:value={editEvent.timestamp}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
					/>
				</div>

				{#if editEvent.type === 'medication'}
					<div class="grid gap-3 sm:grid-cols-2">
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Medication</label>
							<input
								type="text"
								bind:value={editEvent.metadata.med_name}
								class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							/>
						</div>
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Dosage</label>
							<input
								type="text"
								bind:value={editEvent.metadata.dosage}
								class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							/>
						</div>
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Route</label>
							<input
								type="text"
								bind:value={editEvent.metadata.route}
								class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							/>
						</div>
					</div>
				{:else if editEvent.type === 'feeding'}
					<div class="grid gap-3 sm:grid-cols-2">
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Amount (ml)</label>
							<input
								type="number"
								min="0"
								bind:value={editEvent.metadata.amount_ml}
								class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							/>
						</div>
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Duration (min)</label>
							<input
								type="number"
								min="0"
								bind:value={editEvent.metadata.duration_min}
								class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							/>
						</div>
						<div class="sm:col-span-2">
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Formula Type</label>
							<input
								type="text"
								bind:value={editEvent.metadata.formula_type}
								class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							/>
						</div>
					</div>
				{:else if editEvent.type === 'diaper'}
					<div class="grid gap-3 sm:grid-cols-2">
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Condition</label>
							<input
								type="text"
								bind:value={editEvent.metadata.condition}
								class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							/>
						</div>
						<div class="flex items-center gap-3">
							<input
								type="checkbox"
								bind:checked={editEvent.metadata.rash}
								class="w-6 h-6 text-yellow-600 border-gray-300 rounded"
							/>
							<label class="text-sm font-medium text-gray-700 dark:text-slate-300">Rash present</label>
						</div>
						<div class="sm:col-span-2">
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Skin Notes</label>
							<input
								type="text"
								bind:value={editEvent.metadata.skin_notes}
								class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							/>
						</div>
					</div>
				{:else if editEvent.type === 'demeanor'}
					<div class="grid gap-3 sm:grid-cols-2">
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Mood</label>
							<input
								type="text"
								bind:value={editEvent.metadata.mood}
								class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							/>
						</div>
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Activity Level</label>
							<input
								type="text"
								bind:value={editEvent.metadata.activity_level}
								class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							/>
						</div>
						<div class="sm:col-span-2">
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Concerns</label>
							<input
								type="text"
								bind:value={editEvent.metadata.concerns}
								class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							/>
						</div>
					</div>
				{/if}

				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Notes</label>
					<textarea
						rows="3"
						bind:value={editEvent.notes}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
					></textarea>
				</div>
			</div>
			<div class="flex items-center justify-end gap-3 p-6 border-t border-gray-200 dark:border-slate-800">
				<button
					type="button"
					on:click={closeEdit}
					class="px-4 py-2 text-sm font-semibold rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
				>
					Cancel
				</button>
				<button
					type="button"
					on:click={saveEdit}
					disabled={editLoading}
					class="px-4 py-2 text-sm font-semibold rounded-xl bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-400"
				>
					{editLoading ? 'Saving...' : 'Save Changes'}
				</button>
			</div>
		</div>
	</div>
{/if}
