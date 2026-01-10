<script>
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { authStore, isAdmin } from '$lib/stores/auth';
	import { logout as logoutApi } from '$lib/services/api';

	let user = null;
	let userIsAdmin = false;

	// Subscribe to auth store
	authStore.subscribe(value => {
		user = value;
	});

	isAdmin.subscribe(value => {
		userIsAdmin = value;
	});

	onMount(() => {
		// Redirect to login if not authenticated
		if (!user) {
			goto('/login');
		}
	});

	async function handleLogout() {
		try {
			await logoutApi();
			authStore.logout();
			goto('/login');
		} catch (error) {
			console.error('Logout failed:', error);
			// Logout locally anyway
			authStore.logout();
			goto('/login');
		}
	}
</script>

<svelte:head>
	<title>Dashboard - Care Documentation App</title>
</svelte:head>

{#if user}
	<div class="min-h-screen bg-gray-50">
		<!-- Header -->
		<header class="bg-white shadow">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
				<div class="flex justify-between items-center">
					<div>
						<h1 class="text-2xl font-bold text-gray-900">Care Documentation</h1>
						<p class="text-sm text-gray-600 mt-1">Welcome back, {user.username}!</p>
					</div>
					<div class="flex items-center gap-4">
						<span class="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
							{user.role === 'admin' ? 'Administrator' : 'Caregiver'}
						</span>
						<button
							on:click={handleLogout}
							class="px-4 py-2 text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
						>
							Logout
						</button>
					</div>
				</div>
			</div>
		</header>

		<!-- Main Content -->
		<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
			<!-- Status Message -->
			<div class="bg-green-50 border border-green-200 rounded-lg p-6 mb-8">
				<div class="flex items-start gap-3">
					<svg class="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
					</svg>
					<div>
						<h3 class="text-lg font-semibold text-green-900 mb-1">Authentication Working!</h3>
						<p class="text-green-800">
							Phase 2 Complete: You're successfully logged in. The quick entry interface and event tracking features will be available in Phase 3.
						</p>
					</div>
				</div>
			</div>

			<!-- Admin Actions -->
			{#if userIsAdmin}
				<div class="bg-white rounded-lg shadow p-6 mb-8">
					<h2 class="text-xl font-semibold text-gray-900 mb-4">Admin Actions</h2>
					<div class="flex gap-4">
						<button
							on:click={() => goto('/register')}
							class="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
						>
							Register New User
						</button>
					</div>
				</div>
			{/if}

			<!-- Coming Soon Features -->
			<div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
				<!-- Quick Entry -->
				<div class="bg-white rounded-lg shadow p-6">
					<div class="flex items-center gap-3 mb-4">
						<div class="p-2 bg-blue-100 rounded-lg">
							<svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
							</svg>
						</div>
						<h3 class="text-lg font-semibold text-gray-900">Quick Entry</h3>
					</div>
					<p class="text-gray-600 text-sm">
						Fast logging with + button for medications, feeding, diaper changes, and more.
					</p>
					<span class="inline-block mt-4 px-3 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded-full">
						Phase 3
					</span>
				</div>

				<!-- Historical View -->
				<div class="bg-white rounded-lg shadow p-6">
					<div class="flex items-center gap-3 mb-4">
						<div class="p-2 bg-purple-100 rounded-lg">
							<svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
							</svg>
						</div>
						<h3 class="text-lg font-semibold text-gray-900">Historical View</h3>
					</div>
					<p class="text-gray-600 text-sm">
						Timeline view with filtering, search, and export capabilities.
					</p>
					<span class="inline-block mt-4 px-3 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded-full">
						Phase 6
					</span>
				</div>

				<!-- Photo Attachments -->
				<div class="bg-white rounded-lg shadow p-6">
					<div class="flex items-center gap-3 mb-4">
						<div class="p-2 bg-green-100 rounded-lg">
							<svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
							</svg>
						</div>
						<h3 class="text-lg font-semibold text-gray-900">Photo Attachments</h3>
					</div>
					<p class="text-gray-600 text-sm">
						Camera integration with offline support and automatic compression.
					</p>
					<span class="inline-block mt-4 px-3 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded-full">
						Phase 5
					</span>
				</div>

				<!-- Reminders -->
				<div class="bg-white rounded-lg shadow p-6">
					<div class="flex items-center gap-3 mb-4">
						<div class="p-2 bg-red-100 rounded-lg">
							<svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
							</svg>
						</div>
						<h3 class="text-lg font-semibold text-gray-900">Reminders</h3>
					</div>
					<p class="text-gray-600 text-sm">
						Push notifications for medication and feeding schedules.
					</p>
					<span class="inline-block mt-4 px-3 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded-full">
						Phase 7
					</span>
				</div>

				<!-- Offline Support -->
				<div class="bg-white rounded-lg shadow p-6">
					<div class="flex items-center gap-3 mb-4">
						<div class="p-2 bg-orange-100 rounded-lg">
							<svg class="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
							</svg>
						</div>
						<h3 class="text-lg font-semibold text-gray-900">Offline Support</h3>
					</div>
					<p class="text-gray-600 text-sm">
						Works without internet, syncs automatically when back online.
					</p>
					<span class="inline-block mt-4 px-3 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded-full">
						Phase 4
					</span>
				</div>

				<!-- PWA Install -->
				<div class="bg-white rounded-lg shadow p-6">
					<div class="flex items-center gap-3 mb-4">
						<div class="p-2 bg-indigo-100 rounded-lg">
							<svg class="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
							</svg>
						</div>
						<h3 class="text-lg font-semibold text-gray-900">Install as App</h3>
					</div>
					<p class="text-gray-600 text-sm">
						Add to your phone's home screen for quick access like a native app.
					</p>
					<span class="inline-block mt-4 px-3 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded-full">
						Phase 4
					</span>
				</div>
			</div>

			<!-- User Info Card -->
			<div class="mt-8 bg-white rounded-lg shadow p-6">
				<h2 class="text-xl font-semibold text-gray-900 mb-4">Your Account</h2>
				<dl class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<div>
						<dt class="text-sm font-medium text-gray-500">Username</dt>
						<dd class="mt-1 text-sm text-gray-900">{user.username}</dd>
					</div>
					<div>
						<dt class="text-sm font-medium text-gray-500">Email</dt>
						<dd class="mt-1 text-sm text-gray-900">{user.email}</dd>
					</div>
					<div>
						<dt class="text-sm font-medium text-gray-500">Role</dt>
						<dd class="mt-1 text-sm text-gray-900 capitalize">{user.role}</dd>
					</div>
					<div>
						<dt class="text-sm font-medium text-gray-500">Account Created</dt>
						<dd class="mt-1 text-sm text-gray-900">
							{new Date(user.created_at).toLocaleDateString()}
						</dd>
					</div>
				</dl>
			</div>
		</main>
	</div>
{:else}
	<div class="min-h-screen bg-gray-50 flex items-center justify-center">
		<div class="text-center">
			<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
			<p class="mt-4 text-gray-600">Loading...</p>
		</div>
	</div>
{/if}
