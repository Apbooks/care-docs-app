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

	function getEventColor(eventType) {
		const colors = {
			medication: 'blue',
			feeding: 'green',
			diaper: 'yellow',
			demeanor: 'purple',
			observation: 'gray'
		};
		return colors[eventType] || 'gray';
	}

	function formatTime(timestamp) {
		const date = new Date(timestamp);
		const now = new Date();
		const diffMs = now - date;
		const diffMins = Math.floor(diffMs / 60000);
		const diffHours = Math.floor(diffMins / 60);
		const diffDays = Math.floor(diffHours / 24);

		if (diffMins < 1) return 'Just now';
		if (diffMins < 60) return `${diffMins}m ago`;
		if (diffHours < 24) return `${diffHours}h ago`;
		if (diffDays < 7) return `${diffDays}d ago`;

		return date.toLocaleDateString();
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

<div class="space-y-3">
	{#if loading}
		<div class="text-center py-8">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
			<p class="mt-2 text-gray-600">Loading events...</p>
		</div>
	{:else if error}
		<div class="p-4 bg-red-50 border border-red-200 rounded-lg">
			<p class="text-red-800 text-sm">{error}</p>
		</div>
	{:else if events.length === 0}
		<div class="text-center py-8">
			<p class="text-gray-600">No events recorded yet</p>
			<p class="text-sm text-gray-500 mt-1">Tap the + button to create your first entry</p>
		</div>
	{:else}
		{#each events as event (event.id)}
			<div class="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow">
				<div class="flex items-start gap-3">
					<!-- Event Icon -->
					<div class="text-2xl flex-shrink-0">
						{getEventIcon(event.type)}
					</div>

					<!-- Event Details -->
					<div class="flex-1 min-w-0">
						<div class="flex items-start justify-between gap-2">
							<div class="flex-1">
								<h3 class="font-medium text-gray-900 capitalize">
									{event.type.replace('_', ' ')}
								</h3>
								<p class="text-sm text-gray-600 mt-1">
									{formatMetadata(event)}
								</p>
								{#if event.notes && event.type !== 'observation'}
									<p class="text-sm text-gray-500 mt-1 italic">
										{event.notes}
									</p>
								{/if}
							</div>

							<!-- Time Badge -->
							<span class="px-2 py-1 bg-{getEventColor(event.type)}-100 text-{getEventColor(event.type)}-800 text-xs font-medium rounded whitespace-nowrap">
								{formatTime(event.timestamp)}
							</span>
						</div>

						<!-- User Info -->
						<div class="mt-2 flex items-center gap-2 text-xs text-gray-500">
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
