<script>
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { authStore, isAdmin } from '$lib/stores/auth';
	import { logout as logoutApi, getCurrentUser, createEvent } from '$lib/services/api';
	import QuickEntry from '$lib/components/QuickEntry.svelte';
	import EventList from '$lib/components/EventList.svelte';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';

	let user = null;
	let userIsAdmin = false;
	let showQuickEntry = false;
	let eventListComponent;
	let activeContinuousFeed = null;
	let feedActionError = '';
	let feedActionLoading = false;
	const ACTIVE_FEED_KEY = 'active_continuous_feed';

	authStore.subscribe(value => {
		user = value;
	});

	isAdmin.subscribe(value => {
		userIsAdmin = value;
	});

	onMount(() => {
		// If no user in localStorage, redirect to login
		if (!user) {
			goto('/login');
			return;
		}

		loadActiveFeed();
	});

	function loadActiveFeed() {
		if (typeof localStorage === 'undefined') return;
		const stored = localStorage.getItem(ACTIVE_FEED_KEY);
		activeContinuousFeed = stored ? JSON.parse(stored) : null;
	}

	function setActiveFeed(feed) {
		activeContinuousFeed = feed;
		if (typeof localStorage !== 'undefined') {
			if (feed) {
				localStorage.setItem(ACTIVE_FEED_KEY, JSON.stringify(feed));
			} else {
				localStorage.removeItem(ACTIVE_FEED_KEY);
			}
		}
	}

	async function stopContinuousFeed() {
		if (!activeContinuousFeed || feedActionLoading) return;
		feedActionError = '';
		feedActionLoading = true;

		try {
			const stopTime = new Date();
			const startTime = new Date(activeContinuousFeed.started_at);
			const durationMs = stopTime - startTime;
			const durationMinValue = Math.max(0, Math.round(durationMs / 60000));
			const durationHr = durationMs / 3600000;
			const rate = activeContinuousFeed.rate_ml_hr || 0;
			const dose = activeContinuousFeed.dose_ml;
			const intervalHr = activeContinuousFeed.interval_hr;
			let amount = rate * durationHr;

			if (intervalHr && dose && rate) {
				const activeTimeHr = dose / rate;
				const cycles = Math.floor(durationHr / intervalHr);
				const remainderHr = Math.max(0, durationHr - cycles * intervalHr);
				const remainderActiveHr = Math.min(remainderHr, activeTimeHr);
				const remainderAmount = Math.min(dose, rate * remainderActiveHr);
				amount = cycles * dose + remainderAmount;
			} else if (dose) {
				amount = Math.min(amount, dose);
			}

			await createEvent({
				type: 'feeding',
				timestamp: stopTime.toISOString(),
				notes: null,
				metadata: {
					mode: 'continuous',
					status: 'stopped',
					rate_ml_hr: activeContinuousFeed.rate_ml_hr,
					dose_ml: activeContinuousFeed.dose_ml,
					interval_hr: activeContinuousFeed.interval_hr,
					formula_type: activeContinuousFeed.formula_type || null,
					pump_model: activeContinuousFeed.pump_model || null,
					duration_min: durationMinValue,
					amount_ml: Math.round(amount)
				}
			});

			setActiveFeed(null);
			if (eventListComponent) {
				eventListComponent.refresh();
			}
		} catch (error) {
			feedActionError = error.message || 'Failed to stop feed';
		} finally {
			feedActionLoading = false;
		}
	}

	async function handleLogout() {
		try {
			await logoutApi();
			authStore.logout();
			localStorage.removeItem('access_token');
			goto('/login');
		} catch (error) {
			console.error('Logout failed:', error);
			authStore.logout();
			localStorage.removeItem('access_token');
			goto('/login');
		}
	}

	function handleEventCreated() {
		// Refresh the event list when a new event is created
		if (eventListComponent) {
			eventListComponent.refresh();
		}
	}
</script>

<svelte:head>
	<title>Dashboard - Care Documentation App</title>
</svelte:head>

{#if user}
	<div class="min-h-screen bg-gray-50 dark:bg-slate-950 pb-20">
		<!-- Header -->
		<header class="bg-white dark:bg-slate-900 shadow sticky top-0 z-30">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
				<div class="flex justify-between items-center">
					<div>
						<h1 class="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-slate-100">Care Documentation</h1>
						<p class="text-base text-gray-600 dark:text-slate-300 mt-1">Welcome back, {user.username}!</p>
					</div>
					<div class="flex items-center gap-3">
						<ThemeToggle />
						{#if userIsAdmin}
							<button
								on:click={() => goto('/admin')}
								class="px-4 py-2 text-base bg-purple-600 text-white rounded-xl hover:bg-purple-700 flex items-center gap-2"
							>
								<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
								</svg>
								Admin Panel
							</button>
						{/if}
						<button
							on:click={handleLogout}
							class="px-4 py-2 text-base text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-xl dark:text-slate-200 dark:hover:bg-slate-800"
						>
							Logout
						</button>
					</div>
				</div>
			</div>
		</header>

		<!-- Main Content -->
		<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
			<!-- Success Message -->
			<div class="bg-green-50 border border-green-200 rounded-xl p-5 mb-6 dark:bg-emerald-950 dark:border-emerald-800">
				<div class="flex items-start gap-3">
					<svg class="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
					</svg>
					<div>
						<h3 class="font-semibold text-green-900 dark:text-emerald-100">Phase 3 Complete!</h3>
						<p class="text-base text-green-800 dark:text-emerald-200 mt-1">
							Quick entry system is now active. Use the + button to log medications, feeding, diaper changes, and more.
						</p>
					</div>
				</div>
			</div>

			{#if activeContinuousFeed}
				<div class="bg-emerald-50 border border-emerald-200 rounded-xl p-5 mb-6 dark:bg-emerald-950 dark:border-emerald-800">
					<div class="flex flex-wrap items-center justify-between gap-4">
						<div>
							<h3 class="font-semibold text-emerald-900 dark:text-emerald-100">Continuous Feed Running</h3>
							<p class="text-base text-emerald-800 dark:text-emerald-200 mt-1">
								Started {new Date(activeContinuousFeed.started_at).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
								· Rate {activeContinuousFeed.rate_ml_hr || '-'} ml/hr
								· Interval {activeContinuousFeed.interval_hr || '-'} hr
							</p>
						</div>
						<button
							on:click={stopContinuousFeed}
							disabled={feedActionLoading}
							class="px-4 py-2 rounded-xl bg-red-600 text-white text-base font-semibold hover:bg-red-700 disabled:bg-red-400"
						>
							{feedActionLoading ? 'Stopping...' : 'Stop Feed'}
						</button>
					</div>
					{#if feedActionError}
						<p class="mt-3 text-sm text-red-700 dark:text-red-200">{feedActionError}</p>
					{/if}
				</div>
			{/if}

			<!-- Recent Events -->
			<div class="bg-white dark:bg-slate-900 rounded-xl shadow p-6">
				<h2 class="text-xl font-semibold text-gray-900 dark:text-slate-100 mb-4">Recent Events</h2>
				<EventList bind:this={eventListComponent} limit={20} />
			</div>
		</main>

		<!-- Floating Action Button -->
		<button
			on:click={() => showQuickEntry = true}
			class="fixed bottom-6 right-6 w-[72px] h-[72px] bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 hover:shadow-xl transition-all flex items-center justify-center z-40"
			aria-label="Quick Entry"
		>
			<svg class="w-9 h-9" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
			</svg>
		</button>

		<!-- Quick Entry Modal -->
		<QuickEntry bind:show={showQuickEntry} on:eventCreated={handleEventCreated} />
	</div>
{:else}
	<div class="min-h-screen bg-gray-50 dark:bg-slate-950 flex items-center justify-center">
		<div class="text-center">
			<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
			<p class="mt-4 text-gray-600 dark:text-slate-300">Loading...</p>
		</div>
	</div>
{/if}
