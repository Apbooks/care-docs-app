<script>
	import { onMount } from 'svelte';
	import { getEvents } from '$lib/services/api';

	export let limit = 10;
	export let type = null;

	let events = [];
	let loading = true;
	let error = '';

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
					</div>
				</div>
			</div>
		{/each}
	{/if}
</div>
