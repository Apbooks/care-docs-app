<script>
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { authStore, isAdmin } from '$lib/stores/auth';
	import {
		apiRequest,
	getQuickMeds,
	createQuickMed,
	updateQuickMed,
	deleteQuickMed,
	getQuickFeeds,
	createQuickFeed,
		updateQuickFeed,
		deleteQuickFeed
	} from '$lib/services/api';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';

	let user = null;
	let userIsAdmin = false;
	let users = [];
	let loading = true;
	let error = '';
	let deleteConfirmUserId = null;
	let quickMeds = [];
	let quickFeeds = [];
	let quickMedsLoading = true;
	let quickFeedsLoading = true;
	let quickMedsError = '';
	let quickFeedsError = '';

	let newMedName = '';
	let newMedDosage = '';
	let newMedRoute = 'oral';
	let editMedId = null;
	let editMedName = '';
	let editMedDosage = '';
	let editMedRoute = 'oral';

	let newFeedAmount = '';
	let newFeedDuration = '';
	let newFeedFormula = '';
	let newFeedMode = 'bolus';
	let newFeedRate = '';
	let newFeedDose = '';
	let newFeedInterval = '';
	let newFeedOralNotes = '';
	let editFeedId = null;
	let editFeedAmount = '';
	let editFeedDuration = '';
	let editFeedFormula = '';
	let editFeedMode = 'bolus';
	let editFeedRate = '';
	let editFeedDose = '';
	let editFeedInterval = '';
	let editFeedOralNotes = '';

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

		await Promise.all([loadUsers(), loadQuickMeds(), loadQuickFeeds()]);
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

	async function loadQuickMeds() {
		quickMedsLoading = true;
		quickMedsError = '';

		try {
			quickMeds = await getQuickMeds(true);
		} catch (err) {
			quickMedsError = err.message || 'Failed to load quick medications';
		} finally {
			quickMedsLoading = false;
		}
	}

	async function loadQuickFeeds() {
		quickFeedsLoading = true;
		quickFeedsError = '';

		try {
			quickFeeds = await getQuickFeeds(true);
		} catch (err) {
			quickFeedsError = err.message || 'Failed to load quick feeds';
		} finally {
			quickFeedsLoading = false;
		}
	}

	async function handleCreateQuickMed() {
		quickMedsError = '';

		try {
			const created = await createQuickMed({
				name: newMedName,
				dosage: newMedDosage,
				route: newMedRoute
			});
			quickMeds = [created, ...quickMeds];
			newMedName = '';
			newMedDosage = '';
			newMedRoute = 'oral';
		} catch (err) {
			quickMedsError = err.message || 'Failed to create quick medication';
		}
	}

	async function handleToggleQuickMed(med) {
		quickMedsError = '';

		try {
			const updated = await updateQuickMed(med.id, { is_active: !med.is_active });
			quickMeds = quickMeds.map(item => item.id === med.id ? updated : item);
		} catch (err) {
			quickMedsError = err.message || 'Failed to update quick medication';
		}
	}

	async function handleDeleteQuickMed(medId) {
		quickMedsError = '';

		try {
			await deleteQuickMed(medId);
			quickMeds = quickMeds.filter(item => item.id !== medId);
		} catch (err) {
			quickMedsError = err.message || 'Failed to delete quick medication';
		}
	}

	function startEditQuickMed(med) {
		editMedId = med.id;
		editMedName = med.name;
		editMedDosage = med.dosage;
		editMedRoute = med.route;
	}

	function cancelEditQuickMed() {
		editMedId = null;
		editMedName = '';
		editMedDosage = '';
		editMedRoute = 'oral';
	}

	async function handleSaveQuickMed() {
		quickMedsError = '';

		try {
			const updated = await updateQuickMed(editMedId, {
				name: editMedName,
				dosage: editMedDosage,
				route: editMedRoute
			});
			quickMeds = quickMeds.map(item => item.id === updated.id ? updated : item);
			cancelEditQuickMed();
		} catch (err) {
			quickMedsError = err.message || 'Failed to update quick medication';
		}
	}

	async function handleCreateQuickFeed() {
		quickFeedsError = '';

		try {
			const created = await createQuickFeed({
				mode: newFeedMode,
				amount_ml: newFeedAmount ? parseInt(newFeedAmount) : null,
				duration_min: newFeedDuration ? parseInt(newFeedDuration) : null,
				formula_type: newFeedFormula || null,
				rate_ml_hr: newFeedRate ? parseFloat(newFeedRate) : null,
				dose_ml: newFeedDose ? parseFloat(newFeedDose) : null,
				interval_hr: newFeedInterval ? parseFloat(newFeedInterval) : null,
				oral_notes: newFeedOralNotes || null
			});
			quickFeeds = [created, ...quickFeeds];
			newFeedAmount = '';
			newFeedDuration = '';
			newFeedFormula = '';
			newFeedMode = 'bolus';
			newFeedRate = '';
			newFeedDose = '';
			newFeedInterval = '';
			newFeedOralNotes = '';
		} catch (err) {
			quickFeedsError = err.message || 'Failed to create quick feed';
		}
	}

	async function handleToggleQuickFeed(feed) {
		quickFeedsError = '';

		try {
			const updated = await updateQuickFeed(feed.id, { is_active: !feed.is_active });
			quickFeeds = quickFeeds.map(item => item.id === feed.id ? updated : item);
		} catch (err) {
			quickFeedsError = err.message || 'Failed to update quick feed';
		}
	}

	async function handleDeleteQuickFeed(feedId) {
		quickFeedsError = '';

		try {
			await deleteQuickFeed(feedId);
			quickFeeds = quickFeeds.filter(item => item.id !== feedId);
		} catch (err) {
			quickFeedsError = err.message || 'Failed to delete quick feed';
		}
	}

	function startEditQuickFeed(feed) {
		editFeedId = feed.id;
		editFeedAmount = feed.amount_ml ?? '';
		editFeedDuration = feed.duration_min ?? '';
		editFeedFormula = feed.formula_type ?? '';
		editFeedMode = feed.mode || 'bolus';
		editFeedRate = feed.rate_ml_hr ?? '';
		editFeedDose = feed.dose_ml ?? '';
		editFeedInterval = feed.interval_hr ?? '';
		editFeedOralNotes = feed.oral_notes ?? '';
	}

	function cancelEditQuickFeed() {
		editFeedId = null;
		editFeedAmount = '';
		editFeedDuration = '';
		editFeedFormula = '';
		editFeedMode = 'bolus';
		editFeedRate = '';
		editFeedDose = '';
		editFeedInterval = '';
		editFeedOralNotes = '';
	}

	async function handleSaveQuickFeed() {
		quickFeedsError = '';

		try {
			const updated = await updateQuickFeed(editFeedId, {
				mode: editFeedMode,
				amount_ml: editFeedAmount === '' ? null : parseInt(editFeedAmount),
				duration_min: editFeedDuration === '' ? null : parseInt(editFeedDuration),
				formula_type: editFeedFormula || null,
				rate_ml_hr: editFeedRate === '' ? null : parseFloat(editFeedRate),
				dose_ml: editFeedDose === '' ? null : parseFloat(editFeedDose),
				interval_hr: editFeedInterval === '' ? null : parseFloat(editFeedInterval),
				oral_notes: editFeedOralNotes || null
			});
			quickFeeds = quickFeeds.map(item => item.id === updated.id ? updated : item);
			cancelEditQuickFeed();
		} catch (err) {
			quickFeedsError = err.message || 'Failed to update quick feed';
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

<div class="min-h-screen bg-gray-50 dark:bg-slate-950">
	<!-- Header -->
	<header class="bg-white dark:bg-slate-900 shadow">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
			<div class="flex justify-between items-center">
				<div>
					<h1 class="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-slate-100">Admin Panel</h1>
					<p class="text-base text-gray-600 dark:text-slate-300 mt-1">Manage users and system settings</p>
				</div>
				<div class="flex items-center gap-3">
					<ThemeToggle />
					<button
						on:click={() => goto('/')}
						class="px-4 py-2 text-base text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-xl dark:text-slate-200 dark:hover:bg-slate-800"
					>
						Back to Dashboard
					</button>
				</div>
			</div>
		</div>
	</header>

	<!-- Main Content -->
	<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Error Display -->
	{#if error}
		<div class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl dark:bg-red-950 dark:border-red-900">
			<p class="text-red-800 dark:text-red-200 text-base">{error}</p>
		</div>
	{/if}

	<!-- User Management Section -->
	<div class="bg-white dark:bg-slate-900 rounded-xl shadow">
		<div class="p-6 border-b border-gray-200 dark:border-slate-800">
			<div class="flex justify-between items-center">
				<div>
					<h2 class="text-xl font-semibold text-gray-900 dark:text-slate-100">User Management</h2>
					<p class="text-base text-gray-600 dark:text-slate-300 mt-1">View and manage user accounts</p>
				</div>
				<button
					on:click={() => goto('/register')}
					class="px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 text-base"
				>
					Add New User
				</button>
			</div>
		</div>

			<div class="p-6">
				{#if loading}
					<div class="text-center py-8">
						<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
						<p class="mt-2 text-gray-600 dark:text-slate-300">Loading users...</p>
					</div>
				{:else if users.length === 0}
					<div class="text-center py-8">
						<p class="text-gray-600 dark:text-slate-300 text-base">No users found</p>
					</div>
				{:else}
				<div class="space-y-4 sm:hidden">
					{#each users as u (u.id)}
						<div class="border border-gray-200 dark:border-slate-800 rounded-xl p-4">
							<div class="flex items-center gap-3">
								<div class="flex-shrink-0 h-12 w-12 bg-gray-200 dark:bg-slate-800 rounded-full flex items-center justify-center">
									<span class="text-gray-600 font-semibold text-lg">
										{u.username.charAt(0).toUpperCase()}
									</span>
								</div>
								<div class="flex-1">
									<div class="text-base font-semibold text-gray-900 dark:text-slate-100">{u.username}</div>
									<div class="text-sm text-gray-500 dark:text-slate-400">{u.email}</div>
								</div>
								<span class={`px-2 py-1 text-xs font-semibold rounded-full ${getRoleBadgeColor(u.role)}`}>
									{u.role}
								</span>
							</div>
							<div class="mt-3 flex flex-wrap items-center gap-3">
								<button
									on:click={() => handleToggleActive(u.id, u.is_active)}
									class={`px-3 py-2 text-xs font-semibold rounded-full ${u.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
									disabled={u.id === user?.id && u.is_active}
								>
									{u.is_active ? 'Active' : 'Inactive'}
								</button>
								<span class="text-xs text-gray-500 dark:text-slate-400">Created {formatDate(u.created_at)}</span>
							</div>
							<div class="mt-3">
								{#if deleteConfirmUserId === u.id}
									<div class="flex items-center gap-3">
										<span class="text-sm text-gray-600 dark:text-slate-300">Confirm delete?</span>
										<button
											on:click={() => handleDeleteUser(u.id)}
											class="text-red-600 font-semibold"
										>
											Yes
										</button>
										<button
											on:click={() => deleteConfirmUserId = null}
											class="text-gray-600 font-semibold"
										>
											No
										</button>
									</div>
								{:else}
									<button
										on:click={() => deleteConfirmUserId = u.id}
										disabled={u.id === user?.id}
										class="text-red-600 font-semibold disabled:text-gray-400 disabled:cursor-not-allowed"
									>
										Delete User
									</button>
								{/if}
							</div>
						</div>
					{/each}
				</div>
				<div class="hidden sm:block overflow-x-auto">
					<table class="min-w-full divide-y divide-gray-200 dark:divide-slate-800">
						<thead class="bg-gray-50 dark:bg-slate-800">
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
						<tbody class="bg-white dark:bg-slate-900 divide-y divide-gray-200 dark:divide-slate-800">
							{#each users as u (u.id)}
								<tr class="hover:bg-gray-50 dark:hover:bg-slate-800">
									<td class="px-6 py-4 whitespace-nowrap">
										<div class="flex items-center">
											<div class="flex-shrink-0 h-10 w-10 bg-gray-200 dark:bg-slate-800 rounded-full flex items-center justify-center">
												<span class="text-gray-600 dark:text-slate-300 font-medium">
													{u.username.charAt(0).toUpperCase()}
												</span>
											</div>
											<div class="ml-4">
												<div class="text-sm font-medium text-gray-900 dark:text-slate-100">{u.username}</div>
												<div class="text-sm text-gray-500 dark:text-slate-400">{u.email}</div>
											</div>
										</div>
									</td>
									<td class="px-6 py-4 whitespace-nowrap">
										<span class={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getRoleBadgeColor(u.role)}`}>
											{u.role}
										</span>
									</td>
									<td class="px-6 py-4 whitespace-nowrap">
										<button
											on:click={() => handleToggleActive(u.id, u.is_active)}
											class={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full cursor-pointer ${u.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
											disabled={u.id === user?.id && u.is_active}
										>
											{u.is_active ? 'Active' : 'Inactive'}
										</button>
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-slate-400">
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

	<!-- Quick Medications -->
	<div class="mt-8 bg-white dark:bg-slate-900 rounded-xl shadow">
		<div class="p-6 border-b border-gray-200 dark:border-slate-800">
			<h2 class="text-xl font-semibold text-gray-900 dark:text-slate-100">Quick Medications</h2>
			<p class="text-base text-gray-600 dark:text-slate-300 mt-1">Manage one-tap medication templates</p>
		</div>
		<div class="p-6 space-y-6">
			{#if quickMedsError}
				<div class="p-4 bg-red-50 border border-red-200 rounded-xl dark:bg-red-950 dark:border-red-900">
					<p class="text-red-800 dark:text-red-200 text-base">{quickMedsError}</p>
				</div>
			{/if}

			<form class="grid gap-4 sm:grid-cols-4" on:submit|preventDefault={handleCreateQuickMed}>
				<div class="sm:col-span-2">
					<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Medication Name</label>
					<input
						type="text"
						bind:value={newMedName}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
						placeholder="e.g., Tylenol"
						required
					/>
				</div>
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Dosage</label>
					<input
						type="text"
						bind:value={newMedDosage}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
						placeholder="5ml"
						required
					/>
				</div>
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Route</label>
					<select
						bind:value={newMedRoute}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
					>
						<option value="oral">Oral</option>
						<option value="tube">Tube Fed</option>
						<option value="topical">Topical</option>
						<option value="injection">Injection</option>
					</select>
				</div>
				<div class="sm:col-span-4">
					<button
						type="submit"
						class="px-4 py-3 bg-blue-600 text-white rounded-xl text-base hover:bg-blue-700 disabled:bg-blue-300"
						disabled={!newMedName || !newMedDosage}
					>
						Add Quick Medication
					</button>
				</div>
			</form>

			{#if quickMedsLoading}
				<div class="text-center py-6">
					<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
					<p class="mt-2 text-gray-600 dark:text-slate-300 text-base">Loading quick medications...</p>
				</div>
			{:else if quickMeds.length === 0}
				<p class="text-gray-600 dark:text-slate-300 text-base">No quick medications yet.</p>
			{:else}
				<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
					{#each quickMeds as med (med.id)}
						<div class="border border-gray-200 dark:border-slate-800 rounded-xl p-4">
							{#if editMedId === med.id}
								<div class="space-y-3">
									<div>
										<label class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Name</label>
										<input
											type="text"
											bind:value={editMedName}
											class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
										/>
									</div>
									<div class="grid gap-3 sm:grid-cols-2">
										<div>
											<label class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Dosage</label>
											<input
												type="text"
												bind:value={editMedDosage}
												class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
											/>
										</div>
										<div>
											<label class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Route</label>
											<select
												bind:value={editMedRoute}
												class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
											>
												<option value="oral">Oral</option>
												<option value="tube">Tube Fed</option>
												<option value="topical">Topical</option>
												<option value="injection">Injection</option>
											</select>
										</div>
									</div>
									<div class="flex items-center gap-3">
										<button
											on:click={handleSaveQuickMed}
											class="px-3 py-2 text-xs font-semibold rounded-full bg-blue-600 text-white hover:bg-blue-700"
										>
											Save
										</button>
										<button
											on:click={cancelEditQuickMed}
											class="px-3 py-2 text-xs font-semibold rounded-full border border-slate-200 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
										>
											Cancel
										</button>
									</div>
								</div>
							{:else}
								<div class="flex items-start justify-between gap-3">
									<div>
										<div class="text-base font-semibold text-gray-900 dark:text-slate-100">{med.name}</div>
										<div class="text-sm text-gray-600 dark:text-slate-300">{med.dosage} · {med.route}</div>
										{#if med.created_by_name}
											<div class="text-xs text-gray-500 dark:text-slate-400 mt-1">Added by {med.created_by_name}</div>
										{/if}
									</div>
									<span class={`px-2 py-1 text-xs font-semibold rounded-full ${med.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-200 text-gray-700'}`}>
										{med.is_active ? 'Active' : 'Inactive'}
									</span>
								</div>
								<div class="mt-4 flex items-center gap-3">
									<button
										on:click={() => startEditQuickMed(med)}
										class="px-3 py-2 text-xs font-semibold rounded-full border border-slate-200 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
									>
										Edit
									</button>
									<button
										on:click={() => handleToggleQuickMed(med)}
										class="px-3 py-2 text-xs font-semibold rounded-full border border-blue-200 text-blue-700 hover:bg-blue-50"
									>
										{med.is_active ? 'Deactivate' : 'Activate'}
									</button>
									<button
										on:click={() => handleDeleteQuickMed(med.id)}
										class="text-red-600 text-xs font-semibold"
									>
										Delete
									</button>
								</div>
							{/if}
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>

	<!-- Quick Feeds -->
	<div class="mt-8 bg-white dark:bg-slate-900 rounded-xl shadow">
		<div class="p-6 border-b border-gray-200 dark:border-slate-800">
			<h2 class="text-xl font-semibold text-gray-900 dark:text-slate-100">Quick Feeds</h2>
			<p class="text-base text-gray-600 dark:text-slate-300 mt-1">Manage one-tap feeding templates</p>
		</div>
		<div class="p-6 space-y-6">
			{#if quickFeedsError}
				<div class="p-4 bg-red-50 border border-red-200 rounded-xl dark:bg-red-950 dark:border-red-900">
					<p class="text-red-800 dark:text-red-200 text-base">{quickFeedsError}</p>
				</div>
			{/if}

			<form class="grid gap-4 sm:grid-cols-4" on:submit|preventDefault={handleCreateQuickFeed}>
				<div class="sm:col-span-4">
					<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Feeding Type</label>
					<div class="grid grid-cols-3 gap-2">
						<button
							type="button"
							on:click={() => newFeedMode = 'continuous'}
							class={`px-3 py-2 rounded-xl border text-sm font-semibold ${newFeedMode === 'continuous' ? 'bg-green-600 text-white border-green-600' : 'border-gray-300 text-gray-700 dark:text-slate-200'}`}
						>
							Continuous
						</button>
						<button
							type="button"
							on:click={() => newFeedMode = 'bolus'}
							class={`px-3 py-2 rounded-xl border text-sm font-semibold ${newFeedMode === 'bolus' ? 'bg-green-600 text-white border-green-600' : 'border-gray-300 text-gray-700 dark:text-slate-200'}`}
						>
							Bolus
						</button>
						<button
							type="button"
							on:click={() => newFeedMode = 'oral'}
							class={`px-3 py-2 rounded-xl border text-sm font-semibold ${newFeedMode === 'oral' ? 'bg-green-600 text-white border-green-600' : 'border-gray-300 text-gray-700 dark:text-slate-200'}`}
						>
							Oral
						</button>
					</div>
				</div>

				{#if newFeedMode === 'continuous'}
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Rate (ml/hr)</label>
						<input
							type="number"
							min="0"
							bind:value={newFeedRate}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="500"
						/>
					</div>
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Dose (ml)</label>
						<input
							type="number"
							min="0"
							bind:value={newFeedDose}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="95"
						/>
					</div>
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Interval (hr)</label>
						<input
							type="number"
							min="0"
							step="0.1"
							bind:value={newFeedInterval}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="0.5"
						/>
					</div>
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Formula Type</label>
						<input
							type="text"
							bind:value={newFeedFormula}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="Pediasure"
						/>
					</div>
				{:else if newFeedMode === 'oral'}
					<div class="sm:col-span-4">
						<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Oral Notes</label>
						<textarea
							rows="2"
							bind:value={newFeedOralNotes}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="Applesauce, puree, water..."
						></textarea>
					</div>
				{:else}
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Amount (ml)</label>
						<input
							type="number"
							min="0"
							bind:value={newFeedAmount}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="95"
						/>
					</div>
					<div class="sm:col-span-3">
						<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Formula Type</label>
						<input
							type="text"
							bind:value={newFeedFormula}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="Pediasure"
						/>
					</div>
				{/if}

				<div class="sm:col-span-4">
					<button
						type="submit"
						class="px-4 py-3 bg-green-600 text-white rounded-xl text-base hover:bg-green-700 disabled:bg-green-300"
					>
						Add Quick Feed
					</button>
				</div>
			</form>

			{#if quickFeedsLoading}
				<div class="text-center py-6">
					<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto"></div>
					<p class="mt-2 text-gray-600 dark:text-slate-300 text-base">Loading quick feeds...</p>
				</div>
			{:else if quickFeeds.length === 0}
				<p class="text-gray-600 dark:text-slate-300 text-base">No quick feeds yet.</p>
			{:else}
				<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
					{#each quickFeeds as feed (feed.id)}
						<div class="border border-gray-200 dark:border-slate-800 rounded-xl p-4">
							{#if editFeedId === feed.id}
								<div class="space-y-3">
									<div>
										<label class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Feeding Type</label>
										<select
											bind:value={editFeedMode}
											class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
										>
											<option value="continuous">Continuous</option>
											<option value="bolus">Bolus</option>
											<option value="oral">Oral</option>
										</select>
									</div>

									{#if editFeedMode === 'continuous'}
										<div class="grid gap-3 sm:grid-cols-2">
											<div>
												<label class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Rate (ml/hr)</label>
												<input
													type="number"
													min="0"
													bind:value={editFeedRate}
													class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
												/>
											</div>
											<div>
												<label class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Dose (ml)</label>
												<input
													type="number"
													min="0"
													bind:value={editFeedDose}
													class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
												/>
											</div>
											<div>
												<label class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Interval (hr)</label>
												<input
													type="number"
													min="0"
													step="0.1"
													bind:value={editFeedInterval}
													class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
												/>
											</div>
											<div>
												<label class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Formula</label>
												<input
													type="text"
													bind:value={editFeedFormula}
													class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
												/>
											</div>
										</div>
									{:else if editFeedMode === 'oral'}
										<div>
											<label class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Oral Notes</label>
											<textarea
												rows="2"
												bind:value={editFeedOralNotes}
												class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
											></textarea>
										</div>
									{:else}
										<div class="grid gap-3 sm:grid-cols-2">
											<div>
												<label class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Amount (ml)</label>
												<input
													type="number"
													min="0"
													bind:value={editFeedAmount}
													class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
												/>
											</div>
											<div>
												<label class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Formula</label>
												<input
													type="text"
													bind:value={editFeedFormula}
													class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
												/>
											</div>
										</div>
									{/if}
									<div class="flex items-center gap-3">
										<button
											on:click={handleSaveQuickFeed}
											class="px-3 py-2 text-xs font-semibold rounded-full bg-green-600 text-white hover:bg-green-700"
										>
											Save
										</button>
										<button
											on:click={cancelEditQuickFeed}
											class="px-3 py-2 text-xs font-semibold rounded-full border border-slate-200 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
										>
											Cancel
										</button>
									</div>
								</div>
							{:else}
								<div class="flex items-start justify-between gap-3">
									<div>
										<div class="text-base font-semibold text-gray-900 dark:text-slate-100 capitalize">
											{feed.mode || 'bolus'}
										</div>
										{#if (feed.mode || 'bolus') === 'continuous'}
											<div class="text-sm text-gray-600 dark:text-slate-300">
												Rate {feed.rate_ml_hr || '-'} ml/hr · Interval {feed.interval_hr || '-'} hr
											</div>
											<div class="text-sm text-gray-600 dark:text-slate-300">
												{#if feed.dose_ml}
													Dose {feed.dose_ml} ml
												{:else}
													Dose infinite
												{/if}
											</div>
										{:else if (feed.mode || 'bolus') === 'oral'}
											<div class="text-sm text-gray-600 dark:text-slate-300">{feed.oral_notes || 'Oral notes'}</div>
										{:else}
											<div class="text-sm text-gray-600 dark:text-slate-300">
												{feed.amount_ml || '-'} ml
												{#if feed.formula_type} · {feed.formula_type}{/if}
											</div>
										{/if}
										{#if feed.created_by_name}
											<div class="text-xs text-gray-500 dark:text-slate-400 mt-1">Added by {feed.created_by_name}</div>
										{/if}
									</div>
									<span class={`px-2 py-1 text-xs font-semibold rounded-full ${feed.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-200 text-gray-700'}`}>
										{feed.is_active ? 'Active' : 'Inactive'}
									</span>
								</div>
								<div class="mt-4 flex items-center gap-3">
									<button
										on:click={() => startEditQuickFeed(feed)}
										class="px-3 py-2 text-xs font-semibold rounded-full border border-slate-200 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
									>
										Edit
									</button>
									<button
										on:click={() => handleToggleQuickFeed(feed)}
										class="px-3 py-2 text-xs font-semibold rounded-full border border-green-200 text-green-700 hover:bg-green-50"
									>
										{feed.is_active ? 'Deactivate' : 'Activate'}
									</button>
									<button
										on:click={() => handleDeleteQuickFeed(feed.id)}
										class="text-red-600 text-xs font-semibold"
									>
										Delete
									</button>
								</div>
							{/if}
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>

	<!-- System Information -->
	<div class="mt-8 bg-white dark:bg-slate-900 rounded-xl shadow p-6">
		<h2 class="text-xl font-semibold text-gray-900 dark:text-slate-100 mb-4">System Information</h2>
		<dl class="grid grid-cols-1 gap-4 sm:grid-cols-2">
			<div>
				<dt class="text-sm font-medium text-gray-500 dark:text-slate-400">Total Users</dt>
				<dd class="mt-1 text-2xl font-semibold text-gray-900 dark:text-slate-100">{users.length}</dd>
			</div>
			<div>
				<dt class="text-sm font-medium text-gray-500 dark:text-slate-400">Active Users</dt>
				<dd class="mt-1 text-2xl font-semibold text-gray-900 dark:text-slate-100">
					{users.filter(u => u.is_active).length}
				</dd>
			</div>
			<div>
				<dt class="text-sm font-medium text-gray-500 dark:text-slate-400">Administrators</dt>
				<dd class="mt-1 text-2xl font-semibold text-gray-900 dark:text-slate-100">
					{users.filter(u => u.role === 'admin').length}
				</dd>
			</div>
			<div>
				<dt class="text-sm font-medium text-gray-500 dark:text-slate-400">Caregivers</dt>
				<dd class="mt-1 text-2xl font-semibold text-gray-900 dark:text-slate-100">
					{users.filter(u => u.role === 'caregiver').length}
				</dd>
			</div>
		</dl>
	</div>
	</main>
</div>
