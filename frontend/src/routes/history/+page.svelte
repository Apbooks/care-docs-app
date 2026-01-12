<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { authStore } from '$lib/stores/auth';
	import { getEvents } from '$lib/services/api';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';
	import { timezone } from '$lib/stores/settings';

	let user = null;

	let events = [];
	let loading = true;
	let error = '';

	let typeFilter = 'all';
	let query = '';
	let startDate = '';
	let endDate = '';
	let limit = 200;

	let summary = {
		total: 0,
		medication: 0,
		feeding: 0,
		diaper: 0,
		demeanor: 0,
		observation: 0
	};

	let medRows = [];
	let dailyCounts = [];

	authStore.subscribe(value => {
		user = value;
	});

	onMount(() => {
		if (!user) {
			goto('/login');
			return;
		}
		applyDefaultRange();
		loadHistory();
	});

	function applyDefaultRange() {
		const now = new Date();
		const start = new Date();
		start.setDate(now.getDate() - 7);
		startDate = start.toISOString().slice(0, 10);
		endDate = now.toISOString().slice(0, 10);
	}

	function toISODateBoundary(value, endOfDay = false) {
		if (!value) return null;
		const date = new Date(value);
		if (endOfDay) {
			date.setHours(23, 59, 59, 999);
		} else {
			date.setHours(0, 0, 0, 0);
		}
		return date.toISOString();
	}

	async function loadHistory() {
		loading = true;
		error = '';

		try {
			const params = {
				limit,
				offset: 0
			};
			if (typeFilter !== 'all') {
				params.type = typeFilter;
			}
			if (query.trim()) {
				params.q = query.trim();
			}
			const startIso = toISODateBoundary(startDate);
			const endIso = toISODateBoundary(endDate, true);
			if (startIso) params.start = startIso;
			if (endIso) params.end = endIso;

			events = await getEvents(params);
			buildSummary();
			buildMedRows();
			buildDailyCounts();
		} catch (err) {
			error = err.message || 'Failed to load history';
		} finally {
			loading = false;
		}
	}

	function buildSummary() {
		const next = {
			total: events.length,
			medication: 0,
			feeding: 0,
			diaper: 0,
			demeanor: 0,
			observation: 0
		};
		for (const event of events) {
			if (next[event.type] !== undefined) {
				next[event.type] += 1;
			}
		}
		summary = next;
	}

	function formatTimeStamp(value) {
		const date = new Date(value);
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

	function buildMedRows() {
		medRows = events
			.filter(event => event.type === 'medication')
			.map(event => ({
				id: event.id,
				time: formatTimeStamp(event.timestamp),
				name: event.metadata?.med_name || 'Medication',
				dosage: event.metadata?.dosage || '-',
				route: event.metadata?.route || '-',
				notes: event.notes || ''
			}));
	}

	function buildDailyCounts() {
		const map = new Map();
		for (const event of events) {
			const date = new Date(event.timestamp);
			const key = date.toISOString().slice(0, 10);
			map.set(key, (map.get(key) || 0) + 1);
		}
		const sorted = Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b));
		dailyCounts = sorted.map(([date, count]) => ({ date, count }));
	}

	function exportMedications() {
		const header = ['Time', 'Medication', 'Dosage', 'Route', 'Notes'];
		const rows = medRows.map(row => [row.time, row.name, row.dosage, row.route, row.notes]);
		const csv = [header, ...rows]
			.map(fields => fields.map(field => `"${String(field).replace(/"/g, '""')}"`).join(','))
			.join('\n');

		const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
		const url = URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = url;
		link.download = `medication-log-${startDate || 'all'}-to-${endDate || 'all'}.csv`;
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		URL.revokeObjectURL(url);
	}

	function openEventDetails(event) {
		goto('/?eventId=' + event.id);
	}
</script>

<svelte:head>
	<title>History - Care Documentation</title>
</svelte:head>

{#if user}
	<div class="min-h-screen bg-gray-50 dark:bg-slate-950 pb-20">
		<header class="bg-white dark:bg-slate-900 shadow sticky top-0 z-30">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
				<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
					<div>
						<h1 class="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-slate-100">History</h1>
						<p class="text-base text-gray-600 dark:text-slate-300 mt-1">Filter events, see trends, export data.</p>
					</div>
					<div class="flex flex-wrap items-center gap-2">
						<ThemeToggle />
						<button
							on:click={() => goto('/')}
							class="px-4 py-2 text-base text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-xl dark:text-slate-200 dark:hover:bg-slate-800"
						>
							Back
						</button>
					</div>
				</div>
			</div>
		</header>

		<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
			<section class="bg-white dark:bg-slate-900 rounded-2xl shadow p-5 sm:p-6">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-slate-100 mb-4">Filters</h2>
				<div class="grid gap-4 sm:grid-cols-4">
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Type</label>
						<select bind:value={typeFilter} class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base">
							<option value="all">All</option>
							<option value="medication">Medication</option>
							<option value="feeding">Feeding</option>
							<option value="diaper">Diaper</option>
							<option value="demeanor">Demeanor</option>
							<option value="observation">Observation</option>
						</select>
					</div>
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Start</label>
						<input type="date" bind:value={startDate} class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base" />
					</div>
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">End</label>
						<input type="date" bind:value={endDate} class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base" />
					</div>
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Search</label>
						<input type="text" bind:value={query} class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base" placeholder="Notes, meds, formula..." />
					</div>
				</div>
				<div class="mt-4 flex flex-wrap gap-3">
					<button on:click={loadHistory} class="px-4 py-3 bg-blue-600 text-white rounded-xl text-base hover:bg-blue-700">
						Apply Filters
					</button>
					<button on:click={applyDefaultRange} class="px-4 py-3 border border-gray-300 rounded-xl text-base text-gray-700 hover:bg-gray-100 dark:text-slate-200 dark:border-slate-700 dark:hover:bg-slate-800">
						Last 7 Days
					</button>
				</div>
			</section>

			<section class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
				<div class="bg-white dark:bg-slate-900 rounded-2xl shadow p-5">
					<p class="text-sm text-gray-500 dark:text-slate-400">Total Events</p>
					<p class="text-3xl font-semibold text-gray-900 dark:text-slate-100">{summary.total}</p>
				</div>
				<div class="bg-white dark:bg-slate-900 rounded-2xl shadow p-5">
					<p class="text-sm text-gray-500 dark:text-slate-400">Medications</p>
					<p class="text-3xl font-semibold text-gray-900 dark:text-slate-100">{summary.medication}</p>
				</div>
				<div class="bg-white dark:bg-slate-900 rounded-2xl shadow p-5">
					<p class="text-sm text-gray-500 dark:text-slate-400">Feedings</p>
					<p class="text-3xl font-semibold text-gray-900 dark:text-slate-100">{summary.feeding}</p>
				</div>
			</section>

			<section class="bg-white dark:bg-slate-900 rounded-2xl shadow p-5 sm:p-6">
				<div class="flex flex-wrap items-center justify-between gap-3 mb-4">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-slate-100">Daily Activity</h2>
					<p class="text-sm text-gray-500 dark:text-slate-400">Counts per day</p>
				</div>
				{#if dailyCounts.length === 0}
					<p class="text-sm text-gray-600 dark:text-slate-300">No activity yet for this range.</p>
				{:else}
					<div class="space-y-2">
						{#each dailyCounts as row}
							<div class="flex items-center gap-3">
								<div class="w-24 text-xs text-gray-500 dark:text-slate-400">{row.date}</div>
								<div class="flex-1 bg-slate-100 dark:bg-slate-800 rounded-full h-3">
									<div class="bg-blue-600 h-3 rounded-full" style={`width: ${Math.min(100, row.count * 6)}%`}></div>
								</div>
								<div class="w-10 text-xs text-gray-500 dark:text-slate-400">{row.count}</div>
							</div>
						{/each}
					</div>
				{/if}
			</section>

			<section class="bg-white dark:bg-slate-900 rounded-2xl shadow p-5 sm:p-6">
				<div class="flex flex-wrap items-center justify-between gap-3 mb-4">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-slate-100">Medication Log</h2>
					<button on:click={exportMedications} class="px-4 py-2 text-sm font-semibold rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800">
						Export CSV
					</button>
				</div>
				{#if medRows.length === 0}
					<p class="text-sm text-gray-600 dark:text-slate-300">No medication events found.</p>
				{:else}
					<div class="overflow-x-auto">
						<table class="min-w-full text-sm">
							<thead class="text-left text-xs text-gray-500 dark:text-slate-400">
								<tr>
									<th class="py-2">Time</th>
									<th class="py-2">Medication</th>
									<th class="py-2">Dosage</th>
									<th class="py-2">Route</th>
									<th class="py-2">Notes</th>
								</tr>
							</thead>
							<tbody>
								{#each medRows as row}
									<tr class="border-t border-slate-100 dark:border-slate-800">
										<td class="py-2 text-gray-700 dark:text-slate-200">{row.time}</td>
										<td class="py-2 text-gray-700 dark:text-slate-200">{row.name}</td>
										<td class="py-2 text-gray-700 dark:text-slate-200">{row.dosage}</td>
										<td class="py-2 text-gray-700 dark:text-slate-200">{row.route}</td>
										<td class="py-2 text-gray-500 dark:text-slate-400">{row.notes}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{/if}
			</section>

			<section class="bg-white dark:bg-slate-900 rounded-2xl shadow p-5 sm:p-6">
				<div class="flex items-center justify-between gap-3 mb-4">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-slate-100">Recent Activity</h2>
					<p class="text-sm text-gray-500 dark:text-slate-400">Tap for details</p>
				</div>
				{#if loading}
					<p class="text-sm text-gray-600 dark:text-slate-300">Loading events...</p>
				{:else if error}
					<p class="text-sm text-red-600 dark:text-red-300">{error}</p>
				{:else if events.length === 0}
					<p class="text-sm text-gray-600 dark:text-slate-300">No events found.</p>
				{:else}
					<div class="space-y-3">
						{#each events.slice(0, 20) as event}
							<button type="button" on:click={() => openEventDetails(event)} class="w-full text-left border border-slate-100 dark:border-slate-800 rounded-xl p-3 hover:bg-slate-50 dark:hover:bg-slate-800">
								<div class="flex items-center justify-between">
									<div>
										<p class="text-sm font-semibold text-gray-900 dark:text-slate-100 capitalize">{event.type.replace('_', ' ')}</p>
										<p class="text-xs text-gray-500 dark:text-slate-400">{formatTimeStamp(event.timestamp)}</p>
									</div>
									<p class="text-xs text-gray-500 dark:text-slate-400">{event.user_name}</p>
								</div>
							</button>
						{/each}
					</div>
				{/if}
			</section>
		</main>
	</div>
{/if}
