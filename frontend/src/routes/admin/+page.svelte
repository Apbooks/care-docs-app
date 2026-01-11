<script>
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { authStore, isAdmin } from '$lib/stores/auth';
	import { apiRequest } from '$lib/services/api';

	let user = null;
	let userIsAdmin = false;
	let users = [];
	let loading = true;
	let error = '';
	let deleteConfirmUserId = null;

	authStore.subscribe(value => {
		user = value;
	});

	isAdmin.subscribe(value => {
		userIsAdmin = value;
	});

	onMount(async () => {
		// Redirect if not admin
		if (!userIsAdmin) {
			goto('/');
			return;
		}

		await loadUsers();
	});

	async function loadUsers() {
		loading = true;
		error = '';

		try {
			users = await apiRequest('/auth/users');
		} catch (err) {
			error = err.message || 'Failed to load users';
		} finally {
			loading = false;
		}
	}

	async function handleDeleteUser(userId) {
		// Don't allow deleting yourself
		if (userId === user.id) {
			error = 'You cannot delete your own account';
			return;
		}

		try {
			await apiRequest(`/auth/users/${userId}`, {
				method: 'DELETE'
			});

			// Remove from list
			users = users.filter(u => u.id !== userId);
			deleteConfirmUserId = null;
		} catch (err) {
			error = err.message || 'Failed to delete user';
		}
	}

	async function handleToggleActive(userId, currentStatus) {
		// Don't allow deactivating yourself
		if (userId === user.id && currentStatus) {
			error = 'You cannot deactivate your own account';
			return;
		}

		try {
			const updatedUser = await apiRequest(`/auth/users/${userId}`, {
				method: 'PATCH',
				body: JSON.stringify({ is_active: !currentStatus })
			});

			// Update in list
			users = users.map(u => u.id === userId ? updatedUser : u);
		} catch (err) {
			error = err.message || 'Failed to update user';
		}
	}

	function getRoleBadgeColor(role) {
		return role === 'admin' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800';
	}

	function formatDate(dateString) {
		return new Date(dateString).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}
</script>

<svelte:head>
	<title>Admin Panel - Care Documentation</title>
</svelte:head>

<div class="min-h-screen bg-gray-50">
	<!-- Header -->
	<header class="bg-white shadow">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
			<div class="flex justify-between items-center">
				<div>
					<h1 class="text-2xl font-bold text-gray-900">Admin Panel</h1>
					<p class="text-sm text-gray-600 mt-1">Manage users and system settings</p>
				</div>
				<button
					on:click={() => goto('/')}
					class="px-4 py-2 text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
				>
					Back to Dashboard
				</button>
			</div>
		</div>
	</header>

	<!-- Main Content -->
	<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Error Display -->
		{#if error}
			<div class="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
				<p class="text-red-800 text-sm">{error}</p>
			</div>
		{/if}

		<!-- User Management Section -->
		<div class="bg-white rounded-lg shadow">
			<div class="p-6 border-b border-gray-200">
				<div class="flex justify-between items-center">
					<div>
						<h2 class="text-xl font-semibold text-gray-900">User Management</h2>
						<p class="text-sm text-gray-600 mt-1">View and manage user accounts</p>
					</div>
					<button
						on:click={() => goto('/register')}
						class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
					>
						Add New User
					</button>
				</div>
			</div>

			<div class="p-6">
				{#if loading}
					<div class="text-center py-8">
						<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
						<p class="mt-2 text-gray-600">Loading users...</p>
					</div>
				{:else if users.length === 0}
					<div class="text-center py-8">
						<p class="text-gray-600">No users found</p>
					</div>
				{:else}
					<div class="overflow-x-auto">
						<table class="min-w-full divide-y divide-gray-200">
							<thead class="bg-gray-50">
								<tr>
									<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
										User
									</th>
									<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
										Role
									</th>
									<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
										Status
									</th>
									<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
										Created
									</th>
									<th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
										Actions
									</th>
								</tr>
							</thead>
							<tbody class="bg-white divide-y divide-gray-200">
								{#each users as u (u.id)}
									<tr class="hover:bg-gray-50">
										<td class="px-6 py-4 whitespace-nowrap">
											<div class="flex items-center">
												<div class="flex-shrink-0 h-10 w-10 bg-gray-200 rounded-full flex items-center justify-center">
													<span class="text-gray-600 font-medium">
														{u.username.charAt(0).toUpperCase()}
													</span>
												</div>
												<div class="ml-4">
													<div class="text-sm font-medium text-gray-900">{u.username}</div>
													<div class="text-sm text-gray-500">{u.email}</div>
												</div>
											</div>
										</td>
										<td class="px-6 py-4 whitespace-nowrap">
											<span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full {getRoleBadgeColor(u.role)}">
												{u.role}
											</span>
										</td>
										<td class="px-6 py-4 whitespace-nowrap">
											<button
												on:click={() => handleToggleActive(u.id, u.is_active)}
												class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full cursor-pointer {u.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}"
												disabled={u.id === user?.id && u.is_active}
											>
												{u.is_active ? 'Active' : 'Inactive'}
											</button>
										</td>
										<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
											{formatDate(u.created_at)}
										</td>
										<td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
											{#if deleteConfirmUserId === u.id}
												<div class="flex items-center justify-end gap-2">
													<span class="text-gray-600 text-xs">Confirm delete?</span>
													<button
														on:click={() => handleDeleteUser(u.id)}
														class="text-red-600 hover:text-red-900"
													>
														Yes
													</button>
													<button
														on:click={() => deleteConfirmUserId = null}
														class="text-gray-600 hover:text-gray-900"
													>
														No
													</button>
												</div>
											{:else}
												<button
													on:click={() => deleteConfirmUserId = u.id}
													disabled={u.id === user?.id}
													class="text-red-600 hover:text-red-900 disabled:text-gray-400 disabled:cursor-not-allowed"
												>
													Delete
												</button>
											{/if}
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{/if}
			</div>
		</div>

		<!-- System Information -->
		<div class="mt-8 bg-white rounded-lg shadow p-6">
			<h2 class="text-xl font-semibold text-gray-900 mb-4">System Information</h2>
			<dl class="grid grid-cols-1 gap-4 sm:grid-cols-2">
				<div>
					<dt class="text-sm font-medium text-gray-500">Total Users</dt>
					<dd class="mt-1 text-2xl font-semibold text-gray-900">{users.length}</dd>
				</div>
				<div>
					<dt class="text-sm font-medium text-gray-500">Active Users</dt>
					<dd class="mt-1 text-2xl font-semibold text-gray-900">
						{users.filter(u => u.is_active).length}
					</dd>
				</div>
				<div>
					<dt class="text-sm font-medium text-gray-500">Administrators</dt>
					<dd class="mt-1 text-2xl font-semibold text-gray-900">
						{users.filter(u => u.role === 'admin').length}
					</dd>
				</div>
				<div>
					<dt class="text-sm font-medium text-gray-500">Caregivers</dt>
					<dd class="mt-1 text-2xl font-semibold text-gray-900">
						{users.filter(u => u.role === 'caregiver').length}
					</dd>
				</div>
			</dl>
		</div>
	</main>
</div>
