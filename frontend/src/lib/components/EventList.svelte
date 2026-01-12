<script>
	import { onMount } from 'svelte';
	import { getEvents, getEvent, updateEvent, deleteEvent } from '$lib/services/api';
	import { timezone } from '$lib/stores/settings';

	export let limit = 10;
	export let type = null;

	let events = [];
	let loading = true;
	let refreshing = false;
	let error = '';
	let editEvent = null;
	let editLoading = false;
	let editError = '';
	let deleteTargetId = null;

	onMount(() => {
		loadEvents();
	});

	async function loadEvents(options = {}) {
		const { silent = false } = options;
		if (silent && events.length > 0) {
			refreshing = true;
		} else {
			loading = true;
		}
		error = '';

		try {
			const params = { limit };
			if (type) params.type = type;

			events = await getEvents(params);
		} catch (err) {
			error = err.message || 'Failed to load events';
		} finally {
			loading = false;
			refreshing = false;
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
		const options = { timeZone: $timezone };
		const time = date.toLocaleTimeString('en-US', {
			hour: 'numeric',
			minute: '2-digit',
			...($timezone === 'local' ? {} : options)
		});
		const day = date.toLocaleDateString('en-US', {
			year: '2-digit',
			month: 'numeric',
			day: 'numeric',
			...($timezone === 'local' ? {} : options)
		});
		return `${time} ${day}`;
	}

	function formatMetadata(event) {
		const { metadata, type } = event;

		switch (type) {
			case 'medication':
				return `${metadata.med_name} - ${metadata.dosage} (${metadata.route})`;
			case 'feeding':
				if (metadata.mode === 'continuous') {
					const status = metadata.status || (metadata.duration_min ? 'stopped' : 'started');
					if (status === 'stopped') {
						const total = metadata.pump_total_ml ?? metadata.amount_ml;
						const totalLabel = total ? `${total}ml` : 'total pending';
						return `Continuous feed stopped · ${totalLabel}`;
					}
					return 'Continuous feed started';
				}
				if (metadata.mode === 'oral') {
					return metadata.oral_notes || event.notes || 'Oral feeding';
				}
				{
					let parts = [];
					if (metadata.amount_ml) parts.push(`${metadata.amount_ml}ml`);
					if (metadata.formula_type) parts.push(metadata.formula_type);
					return parts.join(' · ') || 'Bolus feeding';
				}
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
		const metadata = JSON.parse(JSON.stringify(event.metadata || {}));
		if (event.type === 'feeding' && !metadata.mode) {
			metadata.mode = 'bolus';
		}
		if (event.type === 'feeding' && metadata.mode === 'continuous' && !metadata.status) {
			metadata.status = metadata.duration_min || metadata.amount_ml ? 'stopped' : 'started';
		}
		editEvent = {
			id: event.id,
			type: event.type,
			timestamp: toDateTimeLocal(event.timestamp),
			notes: event.notes || '',
			metadata
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

	async function handleDelete(eventId) {
		try {
			await deleteEvent(eventId);
			events = events.filter(item => item.id !== eventId);
			deleteTargetId = null;
			closeEdit();
		} catch (err) {
			error = err.message || 'Failed to delete event';
		}
	}

	// Export refresh function so parent can call it
	export function refresh() {
		loadEvents({ silent: true });
	}

	export async function openById(eventId) {
		if (!eventId) return;
		let target = events.find(item => item.id === eventId);
		if (!target) {
			try {
				target = await getEvent(eventId);
			} catch (err) {
				error = err.message || 'Failed to load event details';
				return;
			}
		}
		startEdit(target);
	}
</script>

<div class="space-y-4">
	{#if loading && events.length === 0}
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
			<button
				type="button"
				on:click={() => startEdit(event)}
				class="text-left bg-white dark:bg-slate-900 rounded-xl shadow p-4 sm:p-5 hover:shadow-md transition-shadow w-full"
			>
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
								<p class="text-sm sm:text-base text-gray-600 dark:text-slate-300 mt-1 truncate">
									{formatMetadata(event)}
								</p>
								{#if event.notes && event.type !== 'observation'}
									<p class="text-xs sm:text-sm text-gray-500 dark:text-slate-400 mt-1 italic truncate">
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

					</div>
				</div>
			</button>
		{/each}
	{/if}
</div>

{#if editEvent}
	<div class="fixed inset-0 bg-black/60 z-50" on:click={closeEdit}></div>
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4">
		<div class="w-full max-w-lg max-h-[90vh] bg-white dark:bg-slate-900 rounded-2xl shadow-xl flex flex-col" on:click|stopPropagation>
			<div class="p-6 border-b border-gray-200 dark:border-slate-800">
				<h3 class="text-xl font-semibold text-gray-900 dark:text-slate-100">Event Details</h3>
				<p class="text-sm text-gray-600 dark:text-slate-400 mt-1">Update time, type, and details.</p>
			</div>
			<div class="p-6 space-y-4 overflow-y-auto flex-1">
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
					<div class="space-y-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Feeding Type</label>
							<select
								bind:value={editEvent.metadata.mode}
								class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							>
								<option value="continuous">Continuous</option>
								<option value="bolus">Bolus</option>
								<option value="oral">Oral</option>
							</select>
						</div>

						{#if editEvent.metadata.mode === 'continuous'}
							<div class="grid gap-3 sm:grid-cols-2">
								<div>
									<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Status</label>
									<select
										bind:value={editEvent.metadata.status}
										class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
									>
										<option value="started">Started</option>
										<option value="stopped">Stopped</option>
									</select>
								</div>
								<div>
									<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Rate (ml/hr)</label>
									<input
										type="number"
										min="0"
										bind:value={editEvent.metadata.rate_ml_hr}
										class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
									/>
								</div>
								<div>
									<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Dose (ml)</label>
									<input
										type="number"
										min="0"
										bind:value={editEvent.metadata.dose_ml}
										class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
									/>
								</div>
								<div>
									<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Interval (hr)</label>
									<input
										type="number"
										min="0"
										step="0.1"
										bind:value={editEvent.metadata.interval_hr}
										class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
									/>
								</div>
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
							</div>
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Formula Type</label>
								<input
									type="text"
									bind:value={editEvent.metadata.formula_type}
									class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
								/>
							</div>
						{:else if editEvent.metadata.mode === 'oral'}
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Oral Notes</label>
								<textarea
									rows="3"
									bind:value={editEvent.metadata.oral_notes}
									class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
								></textarea>
							</div>
						{:else}
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
									<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Formula Type</label>
									<input
										type="text"
										bind:value={editEvent.metadata.formula_type}
										class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
									/>
								</div>
							</div>
						{/if}
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
			<div class="flex flex-wrap items-center justify-between gap-3 p-6 border-t border-gray-200 dark:border-slate-800">
				<div class="flex items-center gap-2">
					{#if deleteTargetId === editEvent.id}
						<button
							type="button"
							on:click={() => handleDelete(editEvent.id)}
							class="px-4 py-2 text-sm font-semibold rounded-xl bg-red-600 text-white hover:bg-red-700"
						>
							Confirm Delete
						</button>
						<button
							type="button"
							on:click={() => deleteTargetId = null}
							class="px-4 py-2 text-sm font-semibold rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
						>
							Cancel
						</button>
					{:else}
						<button
							type="button"
							on:click={() => deleteTargetId = editEvent.id}
							class="px-4 py-2 text-sm font-semibold rounded-xl border border-red-200 text-red-600 hover:bg-red-50 dark:border-red-800 dark:text-red-200 dark:hover:bg-red-950"
						>
							Delete
						</button>
					{/if}
				</div>
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
