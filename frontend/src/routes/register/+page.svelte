<script>
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { authStore, isAdmin } from '$lib/stores/auth';
	import { registerUser } from '$lib/services/api';

	let username = '';
	let email = '';
	let password = '';
	let confirmPassword = '';
	let role = 'caregiver';
	let error = '';
	let success = '';
	let loading = false;
	let isUserAdmin = false;

	// Subscribe to admin status
	isAdmin.subscribe(value => {
		isUserAdmin = value;
	});

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

<div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 px-4 py-8">
	<div class="max-w-2xl mx-auto">
		<!-- Header -->
		<div class="mb-8">
			<button
				on:click={() => goto('/')}
				class="text-blue-600 hover:text-blue-700 flex items-center gap-2 mb-4"
			>
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
				</svg>
				Back to Dashboard
			</button>
			<h1 class="text-3xl font-bold text-gray-900">Register New User</h1>
			<p class="text-gray-600 mt-2">Create a new caregiver or admin account</p>
		</div>

		<!-- Registration Card -->
		<div class="bg-white rounded-xl shadow-xl p-8">
			{#if error}
				<div class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl">
					<p class="text-red-800 text-base">{error}</p>
				</div>
			{/if}

			{#if success}
				<div class="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl">
					<p class="text-green-800 text-base">{success}</p>
				</div>
			{/if}

			<form on:submit={handleRegister} class="space-y-6">
				<!-- Username -->
				<div>
					<label for="username" class="block text-base font-medium text-gray-700 mb-2">
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
					<label for="email" class="block text-base font-medium text-gray-700 mb-2">
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
					<label for="role" class="block text-base font-medium text-gray-700 mb-2">
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
					<p class="mt-1 text-sm text-gray-500">
						{#if role === 'admin'}
							Administrators can create users and access all features.
						{:else}
							Caregivers can log care activities but cannot create users.
						{/if}
					</p>
				</div>

				<!-- Password -->
				<div>
					<label for="password" class="block text-base font-medium text-gray-700 mb-2">
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
					<label for="confirmPassword" class="block text-base font-medium text-gray-700 mb-2">
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
						class="px-6 py-3 border border-gray-300 rounded-xl font-semibold text-base text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
					>
						Cancel
					</button>
				</div>
			</form>
		</div>
	</div>
</div>
