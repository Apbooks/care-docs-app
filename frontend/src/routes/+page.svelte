<script>
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { authStore, isAdmin } from '$lib/stores/auth';
	import { logout as logoutApi, getCurrentUser } from '$lib/services/api';
	import QuickEntry from '$lib/components/QuickEntry.svelte';
	import EventList from '$lib/components/EventList.svelte';

	let user = null;
	let userIsAdmin = false;
	let showQuickEntry = false;
	let eventListComponent;

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
	});

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
	<div class="min-h-screen bg-gray-50 pb-20">
		<!-- Header -->
		<header class="bg-white shadow sticky top-0 z-30">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
				<div class="flex justify-between items-center">
					<div>
						<h1 class="text-2xl font-bold text-gray-900">Care Documentation</h1>
						<p class="text-sm text-gray-600 mt-1">Welcome back, {user.username}!</p>
					</div>
					<div class="flex items-center gap-4">
						{#if userIsAdmin}
							<button
								on:click={() => goto('/register')}
								class="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
							>
								Add User
							</button>
						{/if}
						<button
							on:click={handleLogout}
							class="px-4 py-2 text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
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
			<div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
				<div class="flex items-start gap-3">
					<svg class="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
					</svg>
					<div>
						<h3 class="font-semibold text-green-900">Phase 3 Complete!</h3>
						<p class="text-sm text-green-800 mt-1">
							Quick entry system is now active. Use the + button to log medications, feeding, diaper changes, and more.
						</p>
					</div>
				</div>
			</div>

			<!-- Recent Events -->
			<div class="bg-white rounded-lg shadow p-6">
				<h2 class="text-xl font-semibold text-gray-900 mb-4">Recent Events</h2>
				<EventList bind:this={eventListComponent} limit={20} />
			</div>
		</main>

		<!-- Floating Action Button -->
		<button
			on:click={() => showQuickEntry = true}
			class="fixed bottom-6 right-6 w-16 h-16 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 hover:shadow-xl transition-all flex items-center justify-center z-40"
			aria-label="Quick Entry"
		>
			<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
			</svg>
		</button>

		<!-- Quick Entry Modal -->
		<QuickEntry bind:show={showQuickEntry} on:eventCreated={handleEventCreated} />
	</div>
{:else}
	<div class="min-h-screen bg-gray-50 flex items-center justify-center">
		<div class="text-center">
			<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
			<p class="mt-4 text-gray-600">Loading...</p>
		</div>
	</div>
{/if}
