<script>
	import { onMount } from 'svelte';
	import { getEvents, getEvent, updateEvent, deleteEvent, getEventPhotos, deletePhoto } from '$lib/services/api';
	import { timezone } from '$lib/stores/settings';
	import { recipients } from '$lib/stores/recipients';
	import PhotoGallery from './PhotoGallery.svelte';

	export let limit = 10;
	export let type = null;
	export let recipientId = null;

	let events = [];
	let loading = true;
	let refreshing = false;
	let error = '';
	let editEvent = null;
	let editLoading = false;
	let editError = '';
	let deleteTargetId = null;
	let lastRecipientId = null;
	let hasMore = true;
	let loadingMore = false;

	// Photo state
	let eventPhotos = [];
	let loadingPhotos = false;
	let photosError = '';

	onMount(() => {
		loadEvents();
	});

	$: if (recipientId !== lastRecipientId) {
		lastRecipientId = recipientId;
		loadEvents();
	}

	async function loadEvents(options = {}) {
		const { silent = false } = options;
		if (silent && events.length > 0) {
			refreshing = true;
		} else {
			loading = true;
		}
		error = '';

		try {
			if (recipientId === null || recipientId === undefined || recipientId === '') {
				events = [];
				hasMore = false;
				return;
			}
			const params = { limit, offset: 0 };
			if (type) params.type = type;
			if (recipientId) params.recipient_id = recipientId;

			const result = await getEvents(params);
			events = result;
			hasMore = result.length === limit;
		} catch (err) {
			error = err.message || 'Failed to load events';
		} finally {
			loading = false;
			refreshing = false;
		}
	}

	async function loadMore() {
		if (loadingMore || !hasMore) return;
		loadingMore = true;

		try {
			const newOffset = events.length;
			const params = { limit, offset: newOffset };
			if (type) params.type = type;
			if (recipientId) params.recipient_id = recipientId;

			const moreEvents = await getEvents(params);
			events = [...events, ...moreEvents];
			hasMore = moreEvents.length === limit;
		} catch (err) {
			error = err.message || 'Failed to load more events';
		} finally {
			loadingMore = false;
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
		const { metadata = {}, type } = event;

		switch (type) {
			case 'medication':
				return `${metadata?.med_name || 'Medication'} - ${metadata?.dosage || '-'} (${metadata?.route || '-'})`;
			case 'feeding':
				if (metadata?.mode === 'continuous') {
					const status = metadata?.status || (metadata?.duration_min ? 'stopped' : 'started');
					if (status === 'stopped') {
						const total = metadata?.pump_total_ml ?? metadata?.amount_ml;
						const totalLabel = total ? `${total}ml` : 'total pending';
						return `Continuous feed stopped · ${totalLabel}`;
					}
					return 'Continuous feed started';
				}
				if (metadata?.mode === 'oral') {
					return metadata?.oral_notes || event.notes || 'Oral feeding';
				}
				{
					let parts = [];
					if (metadata?.amount_ml) parts.push(`${metadata.amount_ml}ml`);
					if (metadata?.formula_type) parts.push(metadata.formula_type);
					return parts.join(' · ') || 'Bolus feeding';
				}
			case 'diaper':
				let diaperParts = [];
				if (metadata?.condition) diaperParts.push(metadata.condition);
				if (metadata?.condition === 'both') {
					if (metadata?.wet_size) diaperParts.push(`wet: ${metadata.wet_size}`);
					if (metadata?.dirty_size) diaperParts.push(`dirty: ${metadata.dirty_size}`);
				} else {
					if (metadata?.size) diaperParts.push(metadata.size);
				}
				if (metadata?.consistency) diaperParts.push(metadata.consistency);
				if (metadata?.rash) diaperParts.push('rash present');
				let diaperDesc = diaperParts.join(', ') || 'Unknown';
				return diaperDesc.charAt(0).toUpperCase() + diaperDesc.slice(1);
			case 'demeanor':
				const mood = metadata?.mood || 'Unknown';
				const activity = metadata?.activity_level?.replace('_', ' ') || 'unknown';
				return `${mood} - ${activity}`;
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

	async function startEdit(event) {
		editError = '';
		photosError = '';
		eventPhotos = [];
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
			recipient_id: event.recipient_id || null,
			metadata
		};

		// Load photos for this event
		loadEventPhotos(event.id);
	}

	async function loadEventPhotos(eventId) {
		if (!eventId || eventId.startsWith('temp_')) return;
		loadingPhotos = true;
		photosError = '';
		try {
			eventPhotos = await getEventPhotos(eventId);
		} catch (err) {
			photosError = err.message || 'Failed to load photos';
			eventPhotos = [];
		} finally {
			loadingPhotos = false;
		}
	}

	async function handlePhotoDelete(event) {
		const photo = event.detail;
		try {
			await deletePhoto(photo.id);
			eventPhotos = eventPhotos.filter(p => p.id !== photo.id);
		} catch (err) {
			photosError = err.message || 'Failed to delete photo';
		}
	}

	function closeEdit() {
		editEvent = null;
		editError = '';
		eventPhotos = [];
		photosError = '';
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
				metadata: editEvent.metadata || {},
				recipient_id: editEvent.recipient_id || null
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

		{#if hasMore}
			<button
				type="button"
				on:click={loadMore}
				disabled={loadingMore}
				class="w-full py-4 text-center text-blue-600 dark:text-blue-400 font-medium
					   bg-white dark:bg-slate-900 rounded-xl shadow hover:bg-gray-50
					   dark:hover:bg-slate-800 transition-colors disabled:opacity-50"
			>
				{#if loadingMore}
					<span class="inline-flex items-center gap-2">
						<svg class="animate-spin h-4 w-4" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
						</svg>
						Loading...
					</span>
				{:else}
					Show More
				{/if}
			</button>
		{/if}
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
				{#if $recipients.length > 0}
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Recipient</label>
						<select
							bind:value={editEvent.recipient_id}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
						>
							{#each $recipients as recipient}
								<option value={recipient.id}>{recipient.name}</option>
							{/each}
						</select>
					</div>
				{/if}

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
					<div class="space-y-4">
						<!-- Condition Buttons -->
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Type</label>
							<div class="grid grid-cols-3 gap-2">
								{#each [
									{ value: 'wet', label: '💧 Wet' },
									{ value: 'dirty', label: '💩 Dirty' },
									{ value: 'both', label: '💧💩 Both' }
								] as opt}
									<button
										type="button"
										on:click={() => {
											const prevCondition = editEvent.metadata.condition;
											editEvent.metadata.condition = opt.value;
											if (opt.value === 'wet') {
												editEvent.metadata.consistency = null;
											}
											// Clear size fields when switching between both and wet/dirty
											if (opt.value === 'both' && prevCondition !== 'both') {
												editEvent.metadata.wet_size = null;
												editEvent.metadata.dirty_size = null;
												editEvent.metadata.size = null;
											} else if (opt.value !== 'both' && prevCondition === 'both') {
												editEvent.metadata.size = null;
												editEvent.metadata.wet_size = null;
												editEvent.metadata.dirty_size = null;
											}
										}}
										class="px-3 py-2 rounded-lg text-sm font-medium transition-all
											{editEvent.metadata.condition === opt.value
												? 'bg-yellow-500 text-white'
												: 'bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-600'}"
									>
										{opt.label}
									</button>
								{/each}
							</div>
						</div>

						<!-- Size Buttons - show for wet or dirty (single size) -->
						{#if ['wet', 'dirty'].includes(editEvent.metadata.condition)}
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Size</label>
								<div class="grid grid-cols-3 gap-2">
									{#each ['small', 'medium', 'large'] as size}
										<button
											type="button"
											on:click={() => editEvent.metadata.size = size}
											class="px-3 py-2 rounded-lg text-sm font-medium capitalize transition-all
												{editEvent.metadata.size === size
													? 'bg-yellow-500 text-white'
													: 'bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-600'}"
										>
											{size}
										</button>
									{/each}
								</div>
							</div>
						{/if}

						<!-- Separate Wet and Dirty Size - show for both -->
						{#if editEvent.metadata.condition === 'both'}
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">💧 Wet Size</label>
								<div class="grid grid-cols-3 gap-2">
									{#each ['small', 'medium', 'large'] as size}
										<button
											type="button"
											on:click={() => editEvent.metadata.wet_size = size}
											class="px-3 py-2 rounded-lg text-sm font-medium capitalize transition-all
												{editEvent.metadata.wet_size === size
													? 'bg-blue-500 text-white'
													: 'bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-600'}"
										>
											{size}
										</button>
									{/each}
								</div>
							</div>
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">💩 Dirty Size</label>
								<div class="grid grid-cols-3 gap-2">
									{#each ['small', 'medium', 'large'] as size}
										<button
											type="button"
											on:click={() => editEvent.metadata.dirty_size = size}
											class="px-3 py-2 rounded-lg text-sm font-medium capitalize transition-all
												{editEvent.metadata.dirty_size === size
													? 'bg-amber-600 text-white'
													: 'bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-600'}"
										>
											{size}
										</button>
									{/each}
								</div>
							</div>
						{/if}

						<!-- Consistency Buttons - show for dirty, both -->
						{#if ['dirty', 'both'].includes(editEvent.metadata.condition)}
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Consistency</label>
								<div class="grid grid-cols-2 gap-2">
									{#each [
										{ value: 'loose', label: 'Loose' },
										{ value: 'semi-firm', label: 'Semi-firm' },
										{ value: 'firm', label: 'Firm' },
										{ value: 'good', label: 'Good' }
									] as opt}
										<button
											type="button"
											on:click={() => editEvent.metadata.consistency = opt.value}
											class="px-3 py-2 rounded-lg text-sm font-medium transition-all
												{editEvent.metadata.consistency === opt.value
													? 'bg-yellow-500 text-white'
													: 'bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-600'}"
										>
											{opt.label}
										</button>
									{/each}
								</div>
							</div>
						{/if}

						<!-- Rash and Skin Notes -->
						<div class="flex items-center gap-3">
							<input
								type="checkbox"
								bind:checked={editEvent.metadata.rash}
								class="w-6 h-6 text-yellow-600 border-gray-300 rounded"
							/>
							<label class="text-sm font-medium text-gray-700 dark:text-slate-300">Rash present</label>
						</div>
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Skin Notes</label>
							<input
								type="text"
								bind:value={editEvent.metadata.skin_notes}
								class="w-full px-4 py-3 border border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 rounded-xl text-base"
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

				<!-- Photos Section -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Photos</label>
					{#if loadingPhotos}
						<div class="flex items-center justify-center py-4">
							<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
						</div>
					{:else if photosError}
						<p class="text-sm text-red-600 dark:text-red-400">{photosError}</p>
					{:else if eventPhotos.length > 0}
						<PhotoGallery photos={eventPhotos} on:delete={handlePhotoDelete} />
					{:else}
						<p class="text-sm text-gray-500 dark:text-slate-400 italic">No photos attached</p>
					{/if}
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
