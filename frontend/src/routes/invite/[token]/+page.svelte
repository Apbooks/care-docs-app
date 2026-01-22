<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { getInvite, acceptInvite } from '$lib/services/api';

	let token = '';
	let loading = true;
	let error = '';
	let invite = null;
	let password = '';
	let confirmPassword = '';
	let username = '';
	let email = '';
	let displayName = '';
	let submitLoading = false;
	let submitError = '';
	let submitSuccess = '';

	$: token = $page.params.token;

	function validatePassword(passwordValue) {
		const errors = [];
		if (!/[a-z]/.test(passwordValue)) {
			errors.push('Include a lowercase letter.');
		}
		if (!/[A-Z]/.test(passwordValue)) {
			errors.push('Include an uppercase letter.');
		}
		if (!/[0-9]/.test(passwordValue)) {
			errors.push('Include a number.');
		}
		return errors;
	}

	onMount(async () => {
		if (!token) {
			error = 'Invite token is missing.';
			loading = false;
			return;
		}

		try {
			invite = await getInvite(token);
			username = invite?.username || '';
			email = invite?.email || '';
		} catch (err) {
			error = err.message || 'Invite not found or expired.';
		} finally {
			loading = false;
		}
	});

	async function handleSubmit(event) {
		event.preventDefault();
		submitError = '';
		submitSuccess = '';

		if (!username || !email || !password || !confirmPassword) {
			submitError = 'Please fill in username, email, and password.';
			return;
		}
		if (password !== confirmPassword) {
			submitError = 'Passwords do not match.';
			return;
		}
		const passwordIssues = validatePassword(password);
		if (passwordIssues.length > 0) {
			submitError = passwordIssues.join(' ');
			return;
		}

		submitLoading = true;
		try {
			await acceptInvite(token, {
				username,
				email,
				display_name: displayName || null,
				password
			});
			submitSuccess = 'Password set. You can now log in.';
			setTimeout(() => {
				goto('/login');
			}, 1500);
		} catch (err) {
			submitError = err.message || 'Failed to accept invite.';
		} finally {
			submitLoading = false;
		}
	}
</script>

<svelte:head>
	<title>Accept Invite - Care Docs</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-slate-950 flex items-center justify-center px-4 py-10">
	<div class="w-full max-w-lg bg-white dark:bg-slate-900 rounded-2xl shadow-xl p-8">
		<h1 class="text-2xl font-bold text-gray-900 dark:text-slate-100">Accept Invite</h1>
		<p class="text-base text-gray-600 dark:text-slate-300 mt-2">Set your password to finish account setup.</p>

		{#if loading}
			<div class="text-center py-10">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
				<p class="mt-2 text-gray-600 dark:text-slate-300">Loading invite...</p>
			</div>
		{:else if error}
			<div class="mt-6 p-4 bg-red-50 border border-red-200 rounded-xl dark:bg-red-950 dark:border-red-900">
				<p class="text-red-800 dark:text-red-200 text-base">{error}</p>
			</div>
		{:else if invite}
			<div class="mt-6 space-y-4">
				<div class="rounded-xl border border-slate-200 dark:border-slate-800 p-4">
					<p class="text-sm text-slate-500 dark:text-slate-400">Account</p>
					<p class="text-base font-semibold text-slate-900 dark:text-slate-100">{invite.username || 'Set your username'}</p>
					<p class="text-sm text-slate-500 dark:text-slate-400">{invite.email || 'Set your email'}</p>
					<p class="text-xs text-slate-500 dark:text-slate-400 mt-2">Role: {invite.role}</p>
					{#if invite.recipient_names?.length}
						<p class="text-xs text-slate-500 dark:text-slate-400 mt-2">Recipients: {invite.recipient_names.join(', ')}</p>
					{/if}
					<p class="text-xs text-slate-500 dark:text-slate-400 mt-2">Expires: {new Date(invite.expires_at).toLocaleString()}</p>
				</div>

				{#if submitError}
					<div class="p-4 bg-red-50 border border-red-200 rounded-xl dark:bg-red-950 dark:border-red-900">
						<p class="text-red-800 dark:text-red-200 text-base">{submitError}</p>
					</div>
				{/if}
				{#if submitSuccess}
					<div class="p-4 bg-green-50 border border-green-200 rounded-xl dark:bg-emerald-950 dark:border-emerald-800">
						<p class="text-emerald-800 dark:text-emerald-200 text-base">{submitSuccess}</p>
					</div>
				{/if}

				<form class="space-y-4" on:submit={handleSubmit}>
					<div>
						<label for="invite-username" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Username</label>
						<input
							id="invite-username"
							type="text"
							bind:value={username}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="Your username"
							required
						/>
					</div>
					<div>
						<label for="invite-email" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Email</label>
						<input
							id="invite-email"
							type="email"
							bind:value={email}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="you@example.com"
							required
						/>
					</div>
					<div>
						<label for="invite-display-name" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Name</label>
						<input
							id="invite-display-name"
							type="text"
							bind:value={displayName}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="Display name"
						/>
					</div>
					<div>
						<label for="invite-password" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Password</label>
						<input
							id="invite-password"
							type="password"
							bind:value={password}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="Upper, lower, and a number"
							required
						/>
						<p class="mt-1 text-xs text-gray-500 dark:text-slate-400">Password must include uppercase, lowercase, and a number.</p>
					</div>
					<div>
						<label for="invite-confirm-password" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Confirm Password</label>
						<input
							id="invite-confirm-password"
							type="password"
							bind:value={confirmPassword}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							required
						/>
					</div>
					<button
						type="submit"
						disabled={submitLoading}
						class="w-full px-4 py-3 bg-blue-600 text-white rounded-xl text-base font-semibold hover:bg-blue-700 disabled:bg-blue-300"
					>
						{submitLoading ? 'Setting password...' : 'Set Password'}
					</button>
				</form>
			</div>
		{/if}
	</div>
</div>
