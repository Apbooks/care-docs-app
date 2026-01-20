<script>
	import { goto } from '$app/navigation';
	import { authStore } from '$lib/stores/auth';
	import { initRecipients } from '$lib/stores/recipients';
	import { login } from '$lib/services/api';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';

	let username = '';
	let password = '';
	let error = '';
	let loading = false;

	async function handleLogin(event) {
		event.preventDefault();
		error = '';
		loading = true;

		try {
			const response = await login(username, password);

			// Store user data AND token in localStorage
			await authStore.setUser(response.user);

			// Store access token in localStorage for cross-origin requests
			if (response.access_token) {
				localStorage.setItem('access_token', response.access_token);
			}
			if (response.refresh_token) {
				localStorage.setItem('refresh_token', response.refresh_token);
			}
			if (response.access_token || response.refresh_token) {
				await authStore.persistTokens(response.access_token, response.refresh_token);
			}

			// Load recipients so dashboard has a default selection
			await initRecipients();

			// Redirect to dashboard
			goto('/');
		} catch (err) {
			error = err.message || 'Login failed. Please check your credentials.';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Login - Care Documentation App</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-slate-950 dark:to-slate-900 flex items-center justify-center px-4">
	<div class="max-w-md w-full">
		<!-- Logo/Title -->
		<div class="text-center mb-8">
			<div class="flex justify-center mb-4">
				<ThemeToggle />
			</div>
			<h1 class="text-4xl font-bold text-gray-900 dark:text-slate-100 mb-2">Care Docs</h1>
			<p class="text-gray-600 dark:text-slate-300">Track care activities with ease</p>
		</div>

		<!-- Login Card -->
		<div class="bg-white dark:bg-slate-900 rounded-xl shadow-xl p-8">
			<h2 class="text-2xl font-semibold text-gray-900 dark:text-slate-100 mb-6">Sign In</h2>

			{#if error}
				<div class="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl dark:bg-red-950 dark:border-red-900">
					<p class="text-red-800 dark:text-red-200 text-base">{error}</p>
				</div>
			{/if}

			<form on:submit={handleLogin} class="space-y-6">
				<!-- Username -->
				<div>
					<label for="username" class="block text-base font-medium text-gray-700 dark:text-slate-300 mb-2">
						Username
					</label>
					<input
						type="text"
						id="username"
						bind:value={username}
						required
						disabled={loading}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
						placeholder="Enter your username"
					/>
				</div>

				<!-- Password -->
				<div>
					<label for="password" class="block text-base font-medium text-gray-700 dark:text-slate-300 mb-2">
						Password
					</label>
					<input
						type="password"
						id="password"
						bind:value={password}
						required
						disabled={loading}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
						placeholder="Enter your password"
					/>
				</div>

				<!-- Login Button -->
				<button
					type="submit"
					disabled={loading}
					class="w-full bg-blue-600 text-white py-3 px-4 rounded-xl font-semibold text-base hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
				>
					{#if loading}
						<span class="flex items-center justify-center">
							<svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
							</svg>
							Signing in...
						</span>
					{:else}
						Sign In
					{/if}
				</button>
			</form>

			<!-- Info -->
			<div class="mt-6 pt-6 border-t border-gray-200 dark:border-slate-800">
				<p class="text-sm text-gray-600 dark:text-slate-400 text-center">
					New user accounts can only be created by administrators.
				</p>
			</div>
		</div>

		<!-- Footer -->
		<p class="text-center text-gray-600 dark:text-slate-400 text-sm mt-8">
			Care Documentation App &copy; 2024
		</p>
	</div>
</div>

<style>
	/* Custom animations */
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>
