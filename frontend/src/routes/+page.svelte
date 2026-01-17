<script>
	import { goto } from '$app/navigation';
	import { onMount, tick } from 'svelte';
	import { get } from 'svelte/store';
	import { page } from '$app/stores';
	import { authStore, isAdmin } from '$lib/stores/auth';
import { logout as logoutApi, getCurrentUser, getActiveContinuousFeed, stopContinuousFeed, refreshSession, getNextMedReminders, skipMedReminder, createEvent, checkMedEarly } from '$lib/services/api';
	import QuickEntry from '$lib/components/QuickEntry.svelte';
	import EventList from '$lib/components/EventList.svelte';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';
	import { timezone } from '$lib/stores/settings';
	import LogoMark from '$lib/components/LogoMark.svelte';
	import RecipientSwitcher from '$lib/components/RecipientSwitcher.svelte';
	import { selectedRecipientId, selectedRecipient, CARE_CATEGORIES } from '$lib/stores/recipients';
	import SyncStatus from '$lib/components/SyncStatus.svelte';
	import { isOnline } from '$lib/stores/offline';
	import UserAvatar from '$lib/components/UserAvatar.svelte';

	let user = null;
	let userIsAdmin = false;
	let showQuickEntry = false;
	let eventListComponent;
	let activeContinuousFeed = null;
	let feedActionError = '';
	let feedActionLoading = false;
	let medReminders = [];
	let medRemindersLoading = false;
	let medRemindersError = '';
	let medRemindersExpanded = false;
	let stream;
	let menuOpen = false;
	let lastRecipientId = null;
	let reconnectAttempts = 0;
	let reconnectTimeout = null;
	let enabledCategories = CARE_CATEGORIES;

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
		loadMedReminders();
		const eventId = get(page).url.searchParams.get('eventId');
		if (eventId) {
			tick().then(() => {
				if (eventListComponent) {
					eventListComponent.openById(eventId);
				}
			});
		}

		const handleActiveFeedChanged = () => loadActiveFeed();
		window.addEventListener('active-feed-changed', handleActiveFeedChanged);

		const API_BASE = import.meta.env.VITE_PUBLIC_API_URL || '/api';

		async function connectStream() {
			try {
				await refreshSession();
			} catch (error) {
				// Token refresh is best-effort; stream can still connect without it.
			}
			const token = typeof localStorage !== 'undefined' ? localStorage.getItem('access_token') : null;
			const streamUrl = token ? `${API_BASE}/stream?token=${encodeURIComponent(token)}` : `${API_BASE}/stream`;

			stream = new EventSource(streamUrl);

			stream.onopen = () => {
				reconnectAttempts = 0; // Reset on successful connection
			};

			stream.onmessage = (event) => {
				try {
					const data = JSON.parse(event.data);
					const recipientMatch = !data.recipient_id || data.recipient_id === $selectedRecipientId;
					if (data.type?.startsWith('event.') && recipientMatch) {
						if (eventListComponent) {
							eventListComponent.refresh();
						}
						loadActiveFeed();
						loadMedReminders();
					}
					if (data.type?.startsWith('feed.') && recipientMatch) {
						loadActiveFeed();
						if (eventListComponent) {
							eventListComponent.refresh();
						}
					}
					if (data.type?.startsWith('med.') && recipientMatch) {
						loadMedReminders();
					}
				} catch (error) {
					console.error('Stream parse error:', error);
				}
			};

			stream.onerror = () => {
				stream.close();
				// Exponential backoff: 1s, 2s, 4s, 8s, 16s, max 30s
				const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
				reconnectAttempts++;
				reconnectTimeout = setTimeout(connectStream, delay);
			};
		}

		connectStream();

		return () => {
			window.removeEventListener('active-feed-changed', handleActiveFeedChanged);
			if (reconnectTimeout) {
				clearTimeout(reconnectTimeout);
			}
			if (stream) {
				stream.close();
			}
		};
	});

	$: if ($selectedRecipientId !== lastRecipientId) {
		lastRecipientId = $selectedRecipientId;
		loadActiveFeed();
		loadMedReminders();
		if (eventListComponent) {
			eventListComponent.refresh();
		}
	}

	$: enabledCategories = $selectedRecipient?.enabled_categories || CARE_CATEGORIES;

	async function loadMedReminders() {
		if (!$selectedRecipientId || !enabledCategories.includes('medication')) {
			medReminders = [];
			return;
		}
		medRemindersLoading = true;
		medRemindersError = '';
		try {
			medReminders = await getNextMedReminders($selectedRecipientId, 10);
		} catch (err) {
			medRemindersError = err.message || 'Failed to load medication reminders';
		} finally {
			medRemindersLoading = false;
		}
	}

	function formatDueTime(value) {
		if (!value) return 'No schedule';
		const date = new Date(value);
		const options = { timeZone: $timezone };
		return date.toLocaleTimeString('en-US', {
			hour: 'numeric',
			minute: '2-digit',
			...($timezone === 'local' ? {} : options)
		});
	}

	async function handleSkipReminder(reminderId) {
		try {
			await skipMedReminder(reminderId);
			loadMedReminders();
		} catch (err) {
			medRemindersError = err.message || 'Failed to skip reminder';
		}
	}

	async function handleLogMedNow(reminder) {
		if (!$selectedRecipientId) return;
		try {
			const earlyCheck = await checkMedEarly({
				recipient_id: $selectedRecipientId,
				med_name: reminder.medication_name,
				timestamp: new Date().toISOString()
			});
			if (earlyCheck?.status === 'early') {
				const minutes = earlyCheck.minutes_until_due ?? 0;
				const confirmEarly = confirm(`${reminder.medication_name} is due in ${minutes} minutes. Log anyway?`);
				if (!confirmEarly) {
					return;
				}
			}
			await createEvent({
				type: 'medication',
				timestamp: new Date().toISOString(),
				recipient_id: $selectedRecipientId,
				notes: null,
				metadata: {
					med_name: reminder.medication_name,
					dosage: reminder.default_dose ? `${reminder.default_dose}${reminder.dose_unit ? ` ${reminder.dose_unit}` : ''}` : null,
					route: 'oral'
				}
			});
			loadMedReminders();
			if (eventListComponent) {
				eventListComponent.refresh();
			}
		} catch (err) {
			medRemindersError = err.message || 'Failed to log medication';
		}
	}

	async function loadActiveFeed() {
		if (!$selectedRecipientId) {
			activeContinuousFeed = null;
			return;
		}
		try {
			const response = await getActiveContinuousFeed($selectedRecipientId);
			activeContinuousFeed = response?.active_feed || null;
		} catch (error) {
			activeContinuousFeed = null;
		}
	}

	function formatBannerTime(value) {
		const date = new Date(value);
		const options = { timeZone: $timezone };
		return date.toLocaleTimeString('en-US', {
			hour: 'numeric',
			minute: '2-digit',
			...($timezone === 'local' ? {} : options)
		});
	}

	async function stopContinuousFeedAction() {
		if (!activeContinuousFeed || feedActionLoading || !$selectedRecipientId) return;
		feedActionError = '';
		feedActionLoading = true;

		try {
			await stopContinuousFeed($selectedRecipientId);
			activeContinuousFeed = null;
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
			localStorage.removeItem('refresh_token');
			goto('/login');
		} catch (error) {
			console.error('Logout failed:', error);
			authStore.logout();
			localStorage.removeItem('access_token');
			localStorage.removeItem('refresh_token');
			goto('/login');
		}
	}

	function handleEventCreated() {
		// Refresh the event list when a new event is created
		if (eventListComponent) {
			eventListComponent.refresh();
		}
		loadMedReminders();
	}

	function toggleMenu() {
		menuOpen = !menuOpen;
	}

	function closeMenu() {
		menuOpen = false;
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
				<div class="flex items-center justify-between">
					<button
						on:click={toggleMenu}
						class="rounded-full border border-slate-200 p-1 hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
						aria-label="Open menu"
					>
						<UserAvatar user={user} size={40} />
					</button>

					<LogoMark size={48} showLabel={true} href="/" />

					<div class="flex items-center gap-2">
						<SyncStatus />
						<ThemeToggle />
					</div>
				</div>
			</div>
		</header>

		{#if menuOpen}
			<div class="fixed inset-0 z-40 bg-black/40" on:click={closeMenu}></div>
			<div class="fixed top-0 left-0 z-50 h-full w-64 bg-white dark:bg-slate-900 shadow-xl p-5">
				<div class="flex items-center justify-between mb-6">
					<div>
						<p class="text-sm text-slate-500 dark:text-slate-400">Signed in as</p>
						<p class="text-base font-semibold text-slate-900 dark:text-slate-100">{user.username}</p>
					</div>
					<button
						on:click={closeMenu}
						class="w-10 h-10 rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>

				<div class="space-y-1">
					<button
						on:click={() => { closeMenu(); goto('/'); }}
						class="w-full text-left px-2 py-3 text-base text-slate-700 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800 rounded-lg"
					>
						Dashboard
					</button>
					<button
						on:click={() => { closeMenu(); goto('/history'); }}
						class="w-full text-left px-2 py-3 text-base text-slate-700 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800 rounded-lg"
					>
						History
					</button>
					{#if userIsAdmin}
						<button
							on:click={() => { closeMenu(); goto('/admin'); }}
							class="w-full text-left px-2 py-3 text-base text-slate-700 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800 rounded-lg"
						>
							Admin Panel
						</button>
					{/if}
					<button
						on:click={() => { closeMenu(); handleLogout(); }}
						class="w-full text-left px-2 py-3 text-base text-red-600 hover:bg-red-50 dark:text-red-200 dark:hover:bg-red-950 rounded-lg"
					>
						Logout
					</button>
				</div>
			</div>
		{/if}

		<!-- Main Content -->
		<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
			{#if !$isOnline}
				<div class="mb-4 p-3 bg-gray-100 border border-gray-300 rounded-xl dark:bg-gray-800 dark:border-gray-700">
					<p class="text-gray-700 dark:text-gray-300 text-sm flex items-center gap-2">
						<span>📴</span>
						<span>You're offline. Events will be saved locally and synced when back online.</span>
					</p>
				</div>
			{/if}
			<div class="mb-6">
				<RecipientSwitcher />
			</div>
			{#if !$selectedRecipientId}
				<div class="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-xl dark:bg-yellow-950 dark:border-yellow-900">
					<p class="text-yellow-800 dark:text-yellow-200 text-base">
						Select a care recipient to view and log events.
					</p>
				</div>
			{/if}
			{#if activeContinuousFeed && enabledCategories.includes('feeding')}
				<div class="bg-emerald-50 border border-emerald-200 rounded-xl p-5 mb-6 dark:bg-emerald-950 dark:border-emerald-800">
					<div class="flex flex-wrap items-center justify-between gap-4">
						<div>
							<h3 class="font-semibold text-emerald-900 dark:text-emerald-100">Continuous Feed Running</h3>
							<p class="text-base text-emerald-800 dark:text-emerald-200 mt-1">
								Started {formatBannerTime(activeContinuousFeed.started_at)}
								· Rate {activeContinuousFeed.rate_ml_hr || '-'} ml/hr
								· Interval {activeContinuousFeed.interval_hr || '-'} hr
							</p>
						</div>
						<button
							on:click={stopContinuousFeedAction}
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

			{#if $selectedRecipientId && enabledCategories.includes('medication')}
				<div class="bg-white dark:bg-slate-900 rounded-xl shadow p-6 mb-6">
					<div class="flex items-start justify-between gap-4">
						<div>
							<h2 class="text-lg font-semibold text-gray-900 dark:text-slate-100">Medication reminders</h2>
							<p class="text-sm text-gray-600 dark:text-slate-400">Next doses due</p>
						</div>
						{#if medReminders.length > 3}
							<button
								type="button"
								on:click={() => { medRemindersExpanded = !medRemindersExpanded; }}
								class="text-sm font-semibold text-blue-600 hover:text-blue-700"
							>
								{medRemindersExpanded ? 'Show less' : 'Show more'}
							</button>
						{/if}
					</div>

					{#if medRemindersLoading}
						<p class="text-sm text-gray-500 dark:text-slate-400 mt-4">Loading reminders...</p>
					{:else if medRemindersError}
						<p class="text-sm text-red-600 dark:text-red-400 mt-4">{medRemindersError}</p>
					{:else if medReminders.length === 0}
						<p class="text-sm text-gray-500 dark:text-slate-400 mt-4">No active reminders.</p>
					{:else}
						<div class="mt-4 space-y-3">
							{#each (medRemindersExpanded ? medReminders : medReminders.slice(0, 3)) as reminder}
								<div class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 dark:border-slate-800 px-4 py-3">
									<div>
										<p class="text-base font-semibold text-slate-900 dark:text-slate-100">{reminder.medication_name}</p>
										<p class="text-sm text-slate-600 dark:text-slate-400">
											{reminder.minutes_until_due <= 0 ? 'Due now' : `Due at ${formatDueTime(reminder.next_due)}`}
										</p>
									</div>
									<div class="flex flex-wrap items-center gap-2">
										<button
											type="button"
											on:click={() => handleLogMedNow(reminder)}
											class="px-3 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700"
										>
											Log dose now
										</button>
										<button
											type="button"
											on:click={() => handleSkipReminder(reminder.id)}
											class="px-3 py-2 rounded-lg border border-slate-300 text-slate-700 text-sm font-semibold hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
										>
											Skip this med
										</button>
									</div>
								</div>
							{/each}
						</div>
					{/if}
				</div>
			{/if}

			<!-- Recent Events -->
			<div class="bg-white dark:bg-slate-900 rounded-xl shadow p-6">
				<h2 class="text-xl font-semibold text-gray-900 dark:text-slate-100 mb-4">Recent Events</h2>
				<EventList bind:this={eventListComponent} limit={20} recipientId={$selectedRecipientId} allowedTypes={enabledCategories} />
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
