<script>
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { authStore, isAdmin } from '$lib/stores/auth';
	import { registerUser, logout as logoutApi } from '$lib/services/api';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';
	import LogoMark from '$lib/components/LogoMark.svelte';

	let user = null;
	let username = '';
	let email = '';
	let password = '';
	let confirmPassword = '';
	let role = 'caregiver';
	let error = '';
	let success = '';
	let loading = false;
	let isUserAdmin = false;
	let menuOpen = false;

	authStore.subscribe(value => {
		user = value;
	});

	// Subscribe to admin status
	isAdmin.subscribe(value => {
		isUserAdmin = value;
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
			authStore.logout();
			localStorage.removeItem('access_token');
			localStorage.removeItem('refresh_token');
			goto('/login');
		} catch (err) {
			authStore.logout();
			localStorage.removeItem('access_token');
			localStorage.removeItem('refresh_token');
			goto('/login');
		}
	}

	onMount(() => {
		// Redirect if not admin
		if (!isUserAdmin) {
			goto('/');
		}
	});

	async function handleRegister(event) {
		event.preventDefault();
		error = '';
		success = '';

		// Validate passwords match
		if (password !== confirmPassword) {
			error = 'Passwords do not match';
			return;
		}

		// Validate password length
		if (password.length < 6) {
			error = 'Password must be at least 6 characters';
			return;
		}

		loading = true;

		try {
			await registerUser({
				username,
				email,
				password,
				role
			});

			success = `User ${username} created successfully!`;

			// Clear form
			username = '';
			email = '';
			password = '';
			confirmPassword = '';
			role = 'caregiver';

			// Redirect to dashboard after 2 seconds
			setTimeout(() => {
				goto('/');
			}, 2000);
		} catch (err) {
			error = err.message || 'Registration failed. Please try again.';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Register User - Care Documentation App</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-slate-950">
	<!-- Header -->
	<header class="bg-white dark:bg-slate-900 shadow sticky top-0 z-30">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
			<div class="flex items-center justify-between">
				<button
					on:click={toggleMenu}
					class="w-12 h-12 flex items-center justify-center rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
					aria-label="Open menu"
				>
					<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
					</svg>
				</button>

				<LogoMark size={48} showLabel={true} href="/" />

				<div class="flex items-center">
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
					<p class="text-base font-semibold text-slate-900 dark:text-slate-100">{user?.username || 'User'}</p>
				</div>
				<button
					on:click={closeMenu}
					class="w-10 h-10 flex items-center justify-center rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
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
				{#if isUserAdmin}
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
	<main class="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Page Title -->
		<div class="mb-6">
			<h1 class="text-2xl font-bold text-gray-900 dark:text-slate-100">Register New User</h1>
			<p class="text-gray-600 dark:text-slate-300 mt-1">Create a new caregiver or admin account</p>
		</div>

		<!-- Registration Card -->
		<div class="bg-white dark:bg-slate-900 rounded-xl shadow-xl p-8">
			{#if error}
				<div class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl dark:bg-red-950 dark:border-red-900">
					<p class="text-red-800 dark:text-red-200 text-base">{error}</p>
				</div>
			{/if}

			{#if success}
				<div class="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl dark:bg-emerald-950 dark:border-emerald-800">
					<p class="text-green-800 dark:text-emerald-200 text-base">{success}</p>
				</div>
			{/if}

			<form on:submit={handleRegister} class="space-y-6">
				<!-- Username -->
				<div>
					<label for="username" class="block text-base font-medium text-gray-700 dark:text-slate-300 mb-2">
						Username <span class="text-red-500">*</span>
					</label>
					<input
						type="text"
						id="username"
						bind:value={username}
						required
						disabled={loading}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
						placeholder="johndoe"
					/>
				</div>

				<!-- Email -->
				<div>
					<label for="email" class="block text-base font-medium text-gray-700 dark:text-slate-300 mb-2">
						Email <span class="text-red-500">*</span>
					</label>
					<input
						type="email"
						id="email"
						bind:value={email}
						required
						disabled={loading}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
						placeholder="john@example.com"
					/>
				</div>

				<!-- Role -->
				<div>
					<label for="role" class="block text-base font-medium text-gray-700 dark:text-slate-300 mb-2">
						Role <span class="text-red-500">*</span>
					</label>
					<select
						id="role"
						bind:value={role}
						disabled={loading}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
					>
						<option value="caregiver">Caregiver</option>
						<option value="admin">Administrator</option>
					</select>
					<p class="mt-1 text-sm text-gray-500 dark:text-slate-400">
						{#if role === 'admin'}
							Administrators can create users and access all features.
						{:else}
							Caregivers can log care activities but cannot create users.
						{/if}
					</p>
				</div>

				<!-- Password -->
				<div>
					<label for="password" class="block text-base font-medium text-gray-700 dark:text-slate-300 mb-2">
						Password <span class="text-red-500">*</span>
					</label>
					<input
						type="password"
						id="password"
						bind:value={password}
						required
						minlength="6"
						disabled={loading}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
						placeholder="Minimum 6 characters"
					/>
				</div>

				<!-- Confirm Password -->
				<div>
					<label for="confirmPassword" class="block text-base font-medium text-gray-700 dark:text-slate-300 mb-2">
						Confirm Password <span class="text-red-500">*</span>
					</label>
					<input
						type="password"
						id="confirmPassword"
						bind:value={confirmPassword}
						required
						minlength="6"
						disabled={loading}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
						placeholder="Re-enter password"
					/>
				</div>

				<!-- Submit Button -->
				<div class="flex gap-4 pt-4">
					<button
						type="submit"
						disabled={loading}
						class="flex-1 bg-blue-600 text-white py-3 px-4 rounded-xl font-semibold text-base hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
					>
						{#if loading}
							Creating User...
						{:else}
							Create User
						{/if}
					</button>

					<button
						type="button"
						on:click={() => goto('/')}
						disabled={loading}
						class="px-6 py-3 border border-gray-300 rounded-xl font-semibold text-base text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors dark:text-slate-200 dark:border-slate-700 dark:hover:bg-slate-800"
					>
						Cancel
					</button>
				</div>
			</form>
		</div>
	</main>
</div>
