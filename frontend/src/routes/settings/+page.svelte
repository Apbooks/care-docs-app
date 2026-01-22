<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { authStore, isAdmin, isReadOnly } from '$lib/stores/auth';
	import {
		updateCurrentUserEmail,
		updateCurrentUserPassword,
		logout as logoutApi,
		getVapidPublicKey,
		subscribePush,
		unsubscribePush
	} from '$lib/services/api';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';
	import LogoMark from '$lib/components/LogoMark.svelte';
	import UserAvatar from '$lib/components/UserAvatar.svelte';

	let user = null;
	let userIsAdmin = false;
	let userIsReadOnly = false;
	let menuOpen = false;

	let email = '';
	let emailPassword = '';
	let emailSaving = false;
	let emailError = '';
	let emailMessage = '';

	let currentPassword = '';
	let newPassword = '';
	let confirmPassword = '';
	let passwordSaving = false;
	let passwordError = '';
	let passwordMessage = '';

	let pushSupported = false;
	let pushPermission = 'default';
	let pushSubscriptionActive = false;
	let pushActionLoading = false;
	let pushActionError = '';

	authStore.subscribe((value) => {
		user = value;
		if (user?.email && !email) {
			email = user.email;
		}
	});

	isAdmin.subscribe((value) => {
		userIsAdmin = value;
	});

	isReadOnly.subscribe((value) => {
		userIsReadOnly = value;
	});

	function toggleMenu() {
		menuOpen = !menuOpen;
	}

	function closeMenu() {
		menuOpen = false;
	}

	async function handleLogout() {
		try {
			await logoutApi();
		} catch (error) {
			// ignore logout errors
		} finally {
			authStore.logout();
			localStorage.removeItem('access_token');
			localStorage.removeItem('refresh_token');
			goto('/login');
		}
	}

	function urlBase64ToUint8Array(base64String) {
		const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
		const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
		const rawData = atob(base64);
		const outputArray = new Uint8Array(rawData.length);
		for (let i = 0; i < rawData.length; i += 1) {
			outputArray[i] = rawData.charCodeAt(i);
		}
		return outputArray;
	}

	async function initializePushState() {
		if (typeof window === 'undefined') return;
		pushSupported = 'serviceWorker' in navigator && 'PushManager' in window;
		pushPermission = typeof Notification !== 'undefined' ? Notification.permission : 'default';
		if (!pushSupported) return;
		try {
			const registration = await navigator.serviceWorker.ready;
			const subscription = await registration.pushManager.getSubscription();
			pushSubscriptionActive = !!subscription;
		} catch (err) {
			pushActionError = err.message || 'Unable to read push subscription status';
		}
	}

	async function handleEnableDevicePush() {
		pushActionError = '';
		pushActionLoading = true;
		try {
			if (!pushSupported) {
				throw new Error('Push notifications are not supported on this device');
			}
			if (typeof Notification === 'undefined') {
				throw new Error('Notification API not available');
			}
			const permission = await Notification.requestPermission();
			pushPermission = permission;
			if (permission !== 'granted') {
				throw new Error('Permission not granted for notifications');
			}
			const { public_key } = await getVapidPublicKey();
			if (!public_key) {
				throw new Error('Missing VAPID public key');
			}
			const registration = await navigator.serviceWorker.ready;
			const subscription = await registration.pushManager.subscribe({
				userVisibleOnly: true,
				applicationServerKey: urlBase64ToUint8Array(public_key)
			});
			await subscribePush(subscription.toJSON());
			pushSubscriptionActive = true;
		} catch (err) {
			pushActionError = err.message || 'Failed to enable push notifications';
		} finally {
			pushActionLoading = false;
		}
	}

	async function handleDisableDevicePush() {
		pushActionError = '';
		pushActionLoading = true;
		try {
			if (!pushSupported) {
				throw new Error('Push notifications are not supported on this device');
			}
			const registration = await navigator.serviceWorker.ready;
			const subscription = await registration.pushManager.getSubscription();
			if (subscription) {
				await unsubscribePush(subscription.toJSON());
				await subscription.unsubscribe();
			}
			pushSubscriptionActive = false;
		} catch (err) {
			pushActionError = err.message || 'Failed to disable push notifications';
		} finally {
			pushActionLoading = false;
		}
	}

	async function handleSaveEmail() {
		emailError = '';
		emailMessage = '';
		emailSaving = true;
		try {
			const updated = await updateCurrentUserEmail({
				email,
				current_password: emailPassword
			});
			await authStore.updateUser(updated);
			emailPassword = '';
			emailMessage = 'Email updated.';
		} catch (err) {
			emailError = err.message || 'Failed to update email';
		} finally {
			emailSaving = false;
		}
	}

	async function handleSavePassword() {
		passwordError = '';
		passwordMessage = '';
		passwordSaving = true;
		try {
			await updateCurrentUserPassword({
				current_password: currentPassword,
				new_password: newPassword,
				confirm_password: confirmPassword
			});
			currentPassword = '';
			newPassword = '';
			confirmPassword = '';
			passwordMessage = 'Password updated.';
		} catch (err) {
			passwordError = err.message || 'Failed to update password';
		} finally {
			passwordSaving = false;
		}
	}

	onMount(() => {
		if (!user) {
			goto('/login');
			return;
		}
		initializePushState();
	});
</script>

<svelte:head>
	<title>Settings - Care Documentation App</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-slate-950">
	<header class="bg-white dark:bg-slate-900 shadow sticky top-0 z-30">
		<div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
			<div class="flex items-center justify-between">
				<button
					on:click={toggleMenu}
					class="rounded-full border border-slate-200 p-1 hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
					aria-label="Open menu"
				>
					<UserAvatar user={user} size={40} />
				</button>

				<LogoMark size={48} showLabel={true} href="/" />

				<div class="flex items-center">
					<ThemeToggle />
				</div>
			</div>
		</div>
	</header>

	{#if menuOpen}
		<button
			type="button"
			class="fixed inset-0 z-40 bg-black/40"
			on:click={closeMenu}
			aria-label="Close menu"
		></button>
		<div class="fixed top-0 left-0 z-50 h-full w-64 bg-white dark:bg-slate-900 shadow-xl p-5">
			<div class="flex items-center justify-between mb-6">
				<div>
					<p class="text-sm text-slate-500 dark:text-slate-400">Signed in as</p>
					<p class="text-base font-semibold text-slate-900 dark:text-slate-100">{user?.username || 'User'}</p>
				</div>
				<button
					on:click={closeMenu}
					class="w-10 h-10 flex items-center justify-center rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
					aria-label="Close menu"
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
				<button
					on:click={() => { closeMenu(); goto('/settings'); }}
					class="w-full text-left px-2 py-3 text-base text-slate-700 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800 rounded-lg"
				>
					Settings
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

	<main class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
		<div>
			<h1 class="text-2xl font-bold text-gray-900 dark:text-slate-100">Settings</h1>
			<p class="text-base text-gray-600 dark:text-slate-300 mt-1">Manage your account and notifications.</p>
		</div>

		<div class="bg-white dark:bg-slate-900 rounded-xl shadow p-6 space-y-6">
			<div>
				<h2 class="text-lg font-semibold text-gray-900 dark:text-slate-100 mb-2">Email</h2>
				{#if emailError}
					<p class="text-sm text-red-700 dark:text-red-200 mb-2">{emailError}</p>
				{/if}
				{#if emailMessage}
					<p class="text-sm text-emerald-700 dark:text-emerald-200 mb-2">{emailMessage}</p>
				{/if}
				<div class="grid gap-4 sm:grid-cols-2">
					<div>
						<label for="settings-email" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Email</label>
						<input
							id="settings-email"
							type="email"
							bind:value={email}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="you@example.com"
						/>
					</div>
					<div>
						<label for="settings-email-password" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Current password</label>
						<input
							id="settings-email-password"
							type="password"
							bind:value={emailPassword}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="Confirm your password"
						/>
					</div>
				</div>
				<button
					type="button"
					on:click={handleSaveEmail}
					disabled={emailSaving}
					class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-semibold disabled:opacity-50"
				>
					{emailSaving ? 'Saving...' : 'Update Email'}
				</button>
			</div>

			<div class="border-t border-slate-200 dark:border-slate-800 pt-6">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-slate-100 mb-2">Password</h2>
				{#if passwordError}
					<p class="text-sm text-red-700 dark:text-red-200 mb-2">{passwordError}</p>
				{/if}
				{#if passwordMessage}
					<p class="text-sm text-emerald-700 dark:text-emerald-200 mb-2">{passwordMessage}</p>
				{/if}
				<div class="grid gap-4 sm:grid-cols-2">
					<div>
						<label for="settings-password-current" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Current password</label>
						<input
							id="settings-password-current"
							type="password"
							bind:value={currentPassword}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="Current password"
						/>
					</div>
					<div>
						<label for="settings-password-new" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">New password</label>
						<input
							id="settings-password-new"
							type="password"
							bind:value={newPassword}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="New password"
						/>
					</div>
					<div>
						<label for="settings-password-confirm" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Confirm new password</label>
						<input
							id="settings-password-confirm"
							type="password"
							bind:value={confirmPassword}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="Confirm new password"
						/>
					</div>
				</div>
				<button
					type="button"
					on:click={handleSavePassword}
					disabled={passwordSaving}
					class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-semibold disabled:opacity-50"
				>
					{passwordSaving ? 'Saving...' : 'Update Password'}
				</button>
			</div>
		</div>

		{#if !userIsReadOnly}
			<div class="bg-white dark:bg-slate-900 rounded-xl shadow p-6 space-y-4">
				<div>
					<h2 class="text-lg font-semibold text-gray-900 dark:text-slate-100">Device Push Notifications</h2>
					<p class="text-sm text-gray-600 dark:text-slate-300">Enable push notifications for this device.</p>
				</div>
				<div class="text-sm text-slate-700 dark:text-slate-200 space-y-1">
					<div>Supported: {pushSupported ? 'Yes' : 'No'}</div>
					<div>Permission: {pushPermission}</div>
					<div>Subscribed: {pushSubscriptionActive ? 'Yes' : 'No'}</div>
				</div>
				{#if pushActionError}
					<p class="text-sm text-red-700 dark:text-red-200">{pushActionError}</p>
				{/if}
				<div class="flex flex-wrap gap-3">
					<button
						type="button"
						on:click={handleEnableDevicePush}
						disabled={pushActionLoading || !pushSupported}
						class="px-4 py-2 rounded-xl text-sm font-semibold bg-emerald-600 text-white disabled:opacity-50"
					>
						Enable on this device
					</button>
					<button
						type="button"
						on:click={handleDisableDevicePush}
						disabled={pushActionLoading || !pushSupported}
						class="px-4 py-2 rounded-xl text-sm font-semibold border border-slate-200 dark:border-slate-600 text-slate-700 dark:text-slate-200 disabled:opacity-50"
					>
						Disable on this device
					</button>
				</div>
			</div>
		{/if}
	</main>
</div>
