<script>
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { confirmPasswordReset } from '$lib/services/api';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';

	let newPassword = '';
	let confirmPassword = '';
	let loading = false;
	let error = '';
	let message = '';

	$: token = $page.url.searchParams.get('token') || '';

	async function handleSubmit(event) {
		event.preventDefault();
		error = '';
		message = '';
		loading = true;
		try {
			await confirmPasswordReset({
				token,
				new_password: newPassword,
				confirm_password: confirmPassword
			});
			message = 'Password reset. You can now log in.';
		} catch (err) {
			error = err.message || 'Failed to reset password.';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Reset Password - Care Documentation App</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-slate-950 dark:to-slate-900 flex items-center justify-center px-4">
	<div class="max-w-md w-full">
		<div class="text-center mb-8">
			<div class="flex justify-center mb-4">
				<ThemeToggle />
			</div>
			<h1 class="text-3xl font-bold text-gray-900 dark:text-slate-100 mb-2">Set a New Password</h1>
			<p class="text-gray-600 dark:text-slate-300">Choose a strong password to continue.</p>
		</div>

		<div class="bg-white dark:bg-slate-900 rounded-xl shadow-xl p-8">
			{#if !token}
				<div class="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl dark:bg-red-950 dark:border-red-900">
					<p class="text-red-800 dark:text-red-200 text-base">Reset link is missing or invalid.</p>
				</div>
			{:else}
				{#if error}
					<div class="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl dark:bg-red-950 dark:border-red-900">
						<p class="text-red-800 dark:text-red-200 text-base">{error}</p>
					</div>
				{/if}
				{#if message}
					<div class="mb-4 p-4 bg-emerald-50 border border-emerald-200 rounded-xl dark:bg-emerald-950 dark:border-emerald-900">
						<p class="text-emerald-800 dark:text-emerald-200 text-base">{message}</p>
					</div>
				{/if}

				<form on:submit={handleSubmit} class="space-y-6">
					<div>
						<label for="new-password" class="block text-base font-medium text-gray-700 dark:text-slate-300 mb-2">
							New password
						</label>
						<input
							type="password"
							id="new-password"
							bind:value={newPassword}
							required
							disabled={loading}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
							placeholder="New password"
						/>
					</div>
					<div>
						<label for="confirm-password" class="block text-base font-medium text-gray-700 dark:text-slate-300 mb-2">
							Confirm password
						</label>
						<input
							type="password"
							id="confirm-password"
							bind:value={confirmPassword}
							required
							disabled={loading}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
							placeholder="Confirm password"
						/>
					</div>

					<button
						type="submit"
						disabled={loading}
						class="w-full bg-blue-600 text-white py-3 px-4 rounded-xl font-semibold text-base hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
					>
						{loading ? 'Saving...' : 'Reset Password'}
					</button>
				</form>
			{/if}

			<div class="mt-6 pt-6 border-t border-gray-200 dark:border-slate-800 text-center">
				<button
					type="button"
					on:click={() => goto('/login')}
					class="text-sm text-blue-600 hover:text-blue-700"
				>
					Back to login
				</button>
			</div>
		</div>
	</div>
</div>
