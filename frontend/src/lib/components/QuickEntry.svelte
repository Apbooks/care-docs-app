<script>
	import { createEventDispatcher } from 'svelte';
	import { createEvent, getQuickMeds, getQuickFeeds, getActiveContinuousFeed, startContinuousFeed, stopContinuousFeed } from '$lib/services/api';
	import { timezone } from '$lib/stores/settings';

	export let show = false;

	const dispatch = createEventDispatcher();

	let step = 'select'; // 'select' or event type
	let loading = false;
	let error = '';

	let quickLoading = false;
	let quickError = '';
	let quickLoaded = false;
	let quickMeds = [];
	let quickFeeds = [];
	let quickNoteEnabled = false;
	let quickNote = '';

	// Event type forms
	let selectedType = '';
	let notes = '';

	// Medication specific
	let medName = '';
	let dosage = '';
	let route = 'oral';

	// Feeding specific
	let feedingMode = 'bolus';
	let amountMl = '';
	let durationMin = '';
	let formulaType = '';
	let feedRate = '';
	let feedDose = '';
	let feedInterval = '';
	let oralNotes = '';
	let pumpTotal = '';
	let activeContinuousFeed = null;

	// Diaper specific
	let condition = 'wet';
	let rash = false;
	let skinNotes = '';

	// Demeanor specific
	let mood = 'neutral';
	let activityLevel = 'moderate';
	let concerns = '';

	const eventTypes = [
		{
			id: 'medication',
			label: 'Medication',
			icon: '💊',
			cardClass: 'border-blue-200 bg-blue-50 hover:border-blue-400 hover:bg-blue-100'
		},
		{
			id: 'feeding',
			label: 'Feeding',
			icon: '🍼',
			cardClass: 'border-green-200 bg-green-50 hover:border-green-400 hover:bg-green-100'
		},
		{
			id: 'diaper',
			label: 'Diaper Change',
			icon: '👶',
			cardClass: 'border-yellow-200 bg-yellow-50 hover:border-yellow-400 hover:bg-yellow-100'
		},
		{
			id: 'demeanor',
			label: 'Demeanor',
			icon: '😊',
			cardClass: 'border-purple-200 bg-purple-50 hover:border-purple-400 hover:bg-purple-100'
		},
		{
			id: 'observation',
			label: 'Observation',
			icon: '📝',
			cardClass: 'border-gray-200 dark:border-slate-800 bg-gray-50 hover:border-gray-400 hover:bg-gray-100'
		}
	];

	$: if (show && !quickLoaded) {
		loadQuickTemplates();
	}
	$: if (show) {
		loadActiveFeed();
	}

	async function loadActiveFeed() {
		try {
			const response = await getActiveContinuousFeed();
			activeContinuousFeed = response?.active_feed || null;
		} catch (err) {
			activeContinuousFeed = null;
		}
	}

	async function loadQuickTemplates() {
		quickLoading = true;
		quickError = '';

		try {
			const [meds, feeds] = await Promise.all([getQuickMeds(), getQuickFeeds()]);
			quickMeds = meds;
			quickFeeds = feeds;
			quickLoaded = true;
		} catch (err) {
			quickError = err.message || 'Failed to load quick templates';
		} finally {
			quickLoading = false;
		}
	}

	function selectType(type) {
		selectedType = type;
		step = type;
	}

	function back() {
		step = 'select';
		error = '';
	}

	function close() {
		show = false;
		reset();
	}

	function resetQuickNote() {
		quickNoteEnabled = false;
		quickNote = '';
	}

	function reset() {
		step = 'select';
		selectedType = '';
		notes = '';
		error = '';
		// Reset type-specific fields
		medName = '';
		dosage = '';
		route = 'oral';
		amountMl = '';
		durationMin = '';
		formulaType = '';
		feedingMode = 'bolus';
		feedRate = '';
		feedDose = '';
		feedInterval = '';
		oralNotes = '';
		pumpTotal = '';
		condition = 'wet';
		rash = false;
		skinNotes = '';
		mood = 'neutral';
		activityLevel = 'moderate';
		concerns = '';
		resetQuickNote();
	}

	function formatRunningTime(value) {
		const date = new Date(value);
		const options = { timeZone: $timezone };
		return date.toLocaleTimeString('en-US', {
			hour: 'numeric',
			minute: '2-digit',
			...($timezone === 'local' ? {} : options)
		});
	}

	function setActiveFeed(feed) {
		activeContinuousFeed = feed;
		if (typeof window !== 'undefined') {
			window.dispatchEvent(new Event('active-feed-changed'));
		}
	}

	async function startContinuousFeedAction() {
		if (loading) return;
		error = '';
		loading = true;

		try {
			const response = await startContinuousFeed({
				rate_ml_hr: feedRate ? parseFloat(feedRate) : null,
				dose_ml: feedDose ? parseFloat(feedDose) : null,
				interval_hr: feedInterval ? parseFloat(feedInterval) : null,
				formula_type: formulaType || null,
				pump_model: 'Moog Infinity',
				notes: notes || null
			});

			setActiveFeed(response?.active_feed || null);
			if (response?.event) {
				dispatch('eventCreated', response.event);
			}
		} catch (err) {
			error = err.message || 'Failed to start feed';
		} finally {
			loading = false;
		}
	}

	async function stopContinuousFeedAction(actualTotal) {
		if (!activeContinuousFeed || loading) return;
		error = '';
		loading = true;

		try {
			const response = await stopContinuousFeed(actualTotal);
			setActiveFeed(null);
			if (response?.event) {
				dispatch('eventCreated', response.event);
			}
			pumpTotal = '';
		} catch (err) {
			error = err.message || 'Failed to stop feed';
		} finally {
			loading = false;
		}
	}

	async function logQuickMedication(template) {
		if (loading) return;
		error = '';
		loading = true;

		try {
			const quickNotes = quickNoteEnabled ? (quickNote.trim() || null) : null;

			const newEvent = await createEvent({
				type: 'medication',
				timestamp: new Date().toISOString(),
				notes: quickNotes,
				metadata: {
					med_name: template.name,
					dosage: template.dosage,
					route: template.route
				}
			});

			dispatch('eventCreated', newEvent);
			close();
		} catch (err) {
			error = err.message || 'Failed to log quick medication';
		} finally {
			loading = false;
		}
	}

	async function logQuickFeed(template) {
		if (loading) return;
		error = '';
		loading = true;

		try {
				if (template.mode === 'continuous') {
					if (activeContinuousFeed) {
						throw new Error('A continuous feed is already running.');
					}

					const response = await startContinuousFeed({
						rate_ml_hr: template.rate_ml_hr,
						dose_ml: template.dose_ml,
						interval_hr: template.interval_hr,
						formula_type: template.formula_type || null,
						pump_model: 'Moog Infinity'
					});

					setActiveFeed(response?.active_feed || null);
					if (response?.event) {
						dispatch('eventCreated', response.event);
					}
					close();
					return;
				}

			const metadata = template.mode === 'oral'
				? { mode: 'oral', oral_notes: template.oral_notes || null }
				: { mode: 'bolus', amount_ml: template.amount_ml, formula_type: template.formula_type || null };

			const newEvent = await createEvent({
				type: 'feeding',
				timestamp: new Date().toISOString(),
				notes: null,
				metadata
			});

			dispatch('eventCreated', newEvent);
			close();
		} catch (err) {
			error = err.message || 'Failed to log quick feed';
		} finally {
			loading = false;
		}
	}

	async function submitEvent() {
		error = '';
		loading = true;

		try {
			let metadata = {};

			// Build metadata based on event type
			switch (selectedType) {
				case 'medication':
					metadata = {
						med_name: medName,
						dosage: dosage,
						route: route
					};
					break;
				case 'feeding':
					if (feedingMode === 'bolus') {
						metadata = {
							mode: 'bolus',
							amount_ml: amountMl ? parseInt(amountMl) : null,
							formula_type: formulaType || null
						};
					} else if (feedingMode === 'oral') {
						metadata = {
							mode: 'oral',
							oral_notes: oralNotes || null
						};
					} else {
						metadata = {
							mode: 'continuous',
							status: 'stopped',
							rate_ml_hr: feedRate ? parseFloat(feedRate) : null,
							dose_ml: feedDose ? parseFloat(feedDose) : null,
							interval_hr: feedInterval ? parseFloat(feedInterval) : null,
							formula_type: formulaType || null
						};
					}
					break;
				case 'diaper':
					metadata = {
						condition: condition,
						rash: rash,
						skin_notes: skinNotes
					};
					break;
				case 'demeanor':
					metadata = {
						mood: mood,
						activity_level: activityLevel,
						concerns: concerns
					};
					break;
				case 'observation':
					// No specific metadata for general observations
					break;
			}

			// Create the event
			const newEvent = await createEvent({
				type: selectedType,
				timestamp: new Date().toISOString(),
				notes: notes || null,
				metadata: metadata
			});

			// Dispatch success event
			dispatch('eventCreated', newEvent);

			// Close and reset
			close();
		} catch (err) {
			error = err.message || 'Failed to create event';
		} finally {
			loading = false;
		}
	}
</script>

{#if show}
	<!-- Modal Backdrop -->
	<div
		class="fixed inset-0 bg-black bg-opacity-50 z-40"
		on:click={close}
		on:keydown={(e) => e.key === 'Escape' && close()}
	></div>

	<!-- Modal -->
	<div class="fixed inset-0 flex items-end sm:items-center justify-center z-50">
		<div class="bg-white dark:bg-slate-900 w-full sm:max-w-lg max-h-[90vh] sm:max-h-[85vh] rounded-t-2xl sm:rounded-2xl shadow-xl flex flex-col">
			<!-- Header -->
			<div class="flex justify-between items-center p-5 sm:p-6 border-b border-gray-200 dark:border-slate-800 dark:border-slate-800">
				<h2 class="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-slate-100 dark:text-slate-100">
					{#if step === 'select'}
						Quick Entry
					{:else}
						{eventTypes.find(t => t.id === selectedType)?.label}
					{/if}
				</h2>
				<button
					on:click={close}
					class="text-gray-400 hover:text-gray-600 dark:text-slate-300 dark:text-slate-400 dark:hover:text-slate-200 transition-colors"
					aria-label="Close"
				>
					<svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>

			<!-- Content -->
			<div class="p-5 sm:p-6 overflow-y-auto flex-1">
				{#if error}
					<div class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg dark:bg-red-950 dark:border-red-900">
						<p class="text-red-800 dark:text-red-200 text-base">{error}</p>
					</div>
				{/if}

				{#if quickLoading && step !== 'select'}
					<div class="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700">
						Loading quick templates...
					</div>
				{:else if quickError && step !== 'select'}
					<div class="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
						{quickError}
					</div>
				{/if}

				{#if step === 'select'}
					<!-- Event Type Selection -->
					<p class="text-gray-600 dark:text-slate-300 text-base mb-4">Select the type of event to log:</p>
					<div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
						{#each eventTypes as type}
							<button
								on:click={() => selectType(type.id)}
								class={`p-4 min-h-[88px] border-2 rounded-xl transition-all text-center text-gray-900 dark:text-slate-100 dark:bg-slate-800 dark:border-slate-700 dark:hover:bg-slate-700 ${type.cardClass}`}
							>
								<div class="text-4xl mb-2">{type.icon}</div>
								<div class="font-semibold text-base">{type.label}</div>
							</button>
						{/each}
					</div>

				{:else if step === 'medication'}
					{#if quickMeds.length > 0}
						<div class="mb-6">
							<div class="flex flex-wrap items-center justify-between gap-3 mb-3">
								<h3 class="text-lg font-semibold text-gray-900 dark:text-slate-100">Quick Medications</h3>
								<label class="flex items-center gap-3 text-sm font-medium text-gray-700 dark:text-slate-300">
									<input
										type="checkbox"
										bind:checked={quickNoteEnabled}
										class="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
									/>
									Add note
								</label>
							</div>
							{#if quickNoteEnabled}
								<textarea
									bind:value={quickNote}
									rows="3"
									class="w-full px-4 py-3 border border-blue-200 rounded-xl focus:ring-2 focus:ring-blue-500 text-base"
									placeholder="Add a quick note (fever, before bed, etc.)"
								></textarea>
							{/if}
							<div class="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-3">
								{#each quickMeds as med}
									<button
										on:click={() => logQuickMedication(med)}
										class="p-3 min-h-[72px] rounded-xl border-2 border-blue-200 bg-blue-50 hover:bg-blue-100 text-left text-gray-900 dark:text-slate-100 dark:bg-slate-800 dark:border-slate-700 dark:hover:bg-slate-700"
										disabled={loading}
									>
										<div class="font-semibold text-gray-900 dark:text-slate-100 text-sm">{med.name}</div>
										<div class="text-xs text-gray-700 mt-1">{med.dosage}</div>
										<div class="text-xs text-gray-500 dark:text-slate-400 capitalize">{med.route}</div>
									</button>
								{/each}
							</div>
						</div>
					{/if}

					<!-- Medication Form -->
					<form on:submit|preventDefault={submitEvent} class="space-y-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Medication Name <span class="text-red-500">*</span>
							</label>
							<input
								type="text"
								bind:value={medName}
								required
								class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 text-base"
								placeholder="e.g., Tylenol"
							/>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Dosage <span class="text-red-500">*</span>
							</label>
							<input
								type="text"
								bind:value={dosage}
								required
								class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 text-base"
								placeholder="e.g., 5ml, 100mg"
							/>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Route
							</label>
							<select
								bind:value={route}
								class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 text-base"
							>
								<option value="oral">Oral</option>
								<option value="tube">Tube Fed</option>
								<option value="topical">Topical</option>
								<option value="injection">Injection</option>
							</select>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Notes (Optional)
							</label>
							<textarea
								bind:value={notes}
								rows="3"
								class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 text-base"
								placeholder="Any additional notes..."
							></textarea>
						</div>

						<div class="flex gap-3 pt-4">
							<button
								type="button"
								on:click={back}
								class="flex-1 px-4 py-3 border border-gray-300 rounded-xl text-gray-700 text-base hover:bg-gray-50"
							>
								Back
							</button>
							<button
								type="submit"
								disabled={loading}
								class="flex-1 px-4 py-3 bg-blue-600 text-white rounded-xl text-base hover:bg-blue-700 disabled:bg-blue-400"
							>
								{loading ? 'Saving...' : 'Save Entry'}
							</button>
						</div>
					</form>

				{:else if step === 'feeding'}
					{#if quickFeeds.length > 0}
						<div class="mb-6">
							<h3 class="text-lg font-semibold text-gray-900 dark:text-slate-100 mb-3">Quick Feeds</h3>
							<div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
								{#each quickFeeds as feed}
									<button
										on:click={() => logQuickFeed(feed)}
										class="p-3 min-h-[72px] rounded-xl border-2 border-green-200 bg-green-50 hover:bg-green-100 text-left text-gray-900 dark:text-slate-100 dark:bg-slate-800 dark:border-slate-700 dark:hover:bg-slate-700"
										disabled={loading}
									>
										<div class="font-semibold text-gray-900 dark:text-slate-100 text-sm capitalize">
											{feed.mode || 'bolus'}
										</div>
										{#if (feed.mode || 'bolus') === 'continuous'}
											<div class="text-xs text-gray-700 dark:text-slate-300 mt-1">{feed.rate_ml_hr || '-'} ml/hr · {feed.interval_hr || '-'} hr</div>
											{#if feed.dose_ml}
												<div class="text-xs text-gray-600 dark:text-slate-400 mt-1">Dose {feed.dose_ml} ml</div>
											{/if}
										{:else if (feed.mode || 'bolus') === 'oral'}
											<div class="text-xs text-gray-700 dark:text-slate-300 mt-1 truncate">{feed.oral_notes || 'Oral notes'}</div>
										{:else}
											<div class="text-xs text-gray-700 dark:text-slate-300 mt-1">{feed.amount_ml || '-'} ml</div>
										{/if}
										{#if feed.formula_type}
											<div class="text-xs text-gray-600 dark:text-slate-400 mt-1">{feed.formula_type}</div>
										{/if}
									</button>
								{/each}
							</div>
						</div>
					{/if}

					<!-- Feeding Form -->
					<form on:submit|preventDefault={submitEvent} class="space-y-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Feeding Type
							</label>
							<div class="grid grid-cols-3 gap-2">
								<button
									type="button"
									on:click={() => feedingMode = 'continuous'}
									class={`px-3 py-2 rounded-xl border text-sm font-semibold ${feedingMode === 'continuous' ? 'bg-green-600 text-white border-green-600' : 'border-gray-300 text-gray-700 dark:text-slate-200'}`}
								>
									Continuous
								</button>
								<button
									type="button"
									on:click={() => feedingMode = 'bolus'}
									class={`px-3 py-2 rounded-xl border text-sm font-semibold ${feedingMode === 'bolus' ? 'bg-green-600 text-white border-green-600' : 'border-gray-300 text-gray-700 dark:text-slate-200'}`}
								>
									Bolus
								</button>
								<button
									type="button"
									on:click={() => feedingMode = 'oral'}
									class={`px-3 py-2 rounded-xl border text-sm font-semibold ${feedingMode === 'oral' ? 'bg-green-600 text-white border-green-600' : 'border-gray-300 text-gray-700 dark:text-slate-200'}`}
								>
									Oral
								</button>
							</div>
						</div>

						{#if feedingMode === 'continuous'}
							{#if activeContinuousFeed}
								<div class="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950 border border-emerald-200 dark:border-emerald-800">
									<p class="text-sm font-semibold text-emerald-800 dark:text-emerald-200">
										Feed running since {formatRunningTime(activeContinuousFeed.started_at)}
									</p>
									<p class="text-sm text-emerald-700 dark:text-emerald-300 mt-1">
										Rate {activeContinuousFeed.rate_ml_hr || '-'} ml/hr · Interval {activeContinuousFeed.interval_hr || '-'} hr
									</p>
								</div>
							{/if}

							<div class="grid gap-3 sm:grid-cols-2">
								<div>
									<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
										Feed Rate (ml/hr)
									</label>
									<input
										type="number"
										min="0"
										bind:value={feedRate}
										class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 text-base"
										placeholder="500"
									/>
								</div>
								<div>
									<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
										Dose (ml) - leave blank for infinite
									</label>
									<input
										type="number"
										min="0"
										bind:value={feedDose}
										class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 text-base"
										placeholder="95"
									/>
								</div>
								<div>
									<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
										Feed Interval (hr)
									</label>
									<input
										type="number"
										min="0"
										step="0.1"
										bind:value={feedInterval}
										class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 text-base"
										placeholder="0.5"
									/>
								</div>
								<div>
									<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
										Formula Type
									</label>
									<input
										type="text"
										bind:value={formulaType}
										class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 text-base"
										placeholder="Pediasure"
									/>
								</div>
							</div>

							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
									Notes (Optional)
								</label>
								<textarea
									bind:value={notes}
									rows="2"
									class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 text-base"
									placeholder="Any additional notes..."
								></textarea>
							</div>
							{#if activeContinuousFeed}
								<div>
									<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
										Pump Total (ml)
									</label>
									<input
										type="number"
										min="0"
										bind:value={pumpTotal}
										class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 text-base"
										placeholder="Actual pump total"
									/>
								</div>
							{/if}
						{:else if feedingMode === 'bolus'}
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
									Amount (ml)
								</label>
								<input
									type="number"
									bind:value={amountMl}
									min="0"
									class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 text-base"
									placeholder="95"
								/>
							</div>

							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
									Formula Type
								</label>
								<input
									type="text"
									bind:value={formulaType}
									class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 text-base"
									placeholder="Pediasure"
								/>
							</div>
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
									Notes (Optional)
								</label>
								<textarea
									bind:value={notes}
									rows="2"
									class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 text-base"
									placeholder="Any additional notes..."
								></textarea>
							</div>
						{:else}
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
									Oral Feeding Notes
								</label>
								<textarea
									bind:value={oralNotes}
									rows="3"
									class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 text-base"
									placeholder="e.g., applesauce, water, puree..."
								></textarea>
							</div>
						{/if}

						<div class="flex gap-3 pt-4">
							<button
								type="button"
								on:click={back}
								class="flex-1 px-4 py-3 border border-gray-300 rounded-xl text-gray-700 text-base hover:bg-gray-50"
							>
								Back
							</button>
							{#if feedingMode === 'continuous'}
								{#if activeContinuousFeed}
									<button
										type="button"
										on:click={() => stopContinuousFeedAction(pumpTotal)}
										disabled={loading}
										class="flex-1 px-4 py-3 bg-red-600 text-white rounded-xl text-base hover:bg-red-700 disabled:bg-red-400"
									>
										{loading ? 'Stopping...' : 'Stop Feed'}
									</button>
							{:else}
								<button
									type="button"
									on:click={startContinuousFeedAction}
									disabled={loading}
									class="flex-1 px-4 py-3 bg-green-600 text-white rounded-xl text-base hover:bg-green-700 disabled:bg-green-400"
								>
										{loading ? 'Starting...' : 'Start Feed'}
									</button>
								{/if}
							{:else}
								<button
									type="submit"
									disabled={loading}
									class="flex-1 px-4 py-3 bg-green-600 text-white rounded-xl text-base hover:bg-green-700 disabled:bg-green-400"
								>
									{loading ? 'Saving...' : 'Save Entry'}
								</button>
							{/if}
						</div>
					</form>

				{:else if step === 'diaper'}
					<!-- Diaper Form -->
					<form on:submit|preventDefault={submitEvent} class="space-y-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Condition
							</label>
							<select
								bind:value={condition}
								class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-500 text-base"
							>
								<option value="wet">Wet</option>
								<option value="dirty">Dirty</option>
								<option value="both">Both</option>
								<option value="dry">Dry (preventive change)</option>
							</select>
						</div>

						<div>
							<label class="flex items-center gap-3">
								<input
									type="checkbox"
									bind:checked={rash}
									class="w-6 h-6 text-yellow-600 border-gray-300 rounded focus:ring-yellow-500"
								/>
								<span class="text-sm font-medium text-gray-700 dark:text-slate-300">Rash present</span>
							</label>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Skin Condition Notes
							</label>
							<textarea
								bind:value={skinNotes}
								rows="2"
								class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-500 text-base"
								placeholder="Describe skin condition..."
							></textarea>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Additional Notes (Optional)
							</label>
							<textarea
								bind:value={notes}
								rows="2"
								class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-500 text-base"
								placeholder="Any additional notes..."
							></textarea>
						</div>

						<div class="flex gap-3 pt-4">
							<button
								type="button"
								on:click={back}
								class="flex-1 px-4 py-3 border border-gray-300 rounded-xl text-gray-700 text-base hover:bg-gray-50"
							>
								Back
							</button>
							<button
								type="submit"
								disabled={loading}
								class="flex-1 px-4 py-3 bg-yellow-600 text-white rounded-xl text-base hover:bg-yellow-700 disabled:bg-yellow-400"
							>
								{loading ? 'Saving...' : 'Save Entry'}
							</button>
						</div>
					</form>

				{:else if step === 'demeanor'}
					<!-- Demeanor Form -->
					<form on:submit|preventDefault={submitEvent} class="space-y-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Mood
							</label>
							<select
								bind:value={mood}
								class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 text-base"
							>
								<option value="happy">Happy</option>
								<option value="content">Content</option>
								<option value="neutral">Neutral</option>
								<option value="fussy">Fussy</option>
								<option value="irritable">Irritable</option>
								<option value="distressed">Distressed</option>
							</select>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Activity Level
							</label>
							<select
								bind:value={activityLevel}
								class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 text-base"
							>
								<option value="very_active">Very Active</option>
								<option value="active">Active</option>
								<option value="moderate">Moderate</option>
								<option value="calm">Calm</option>
								<option value="lethargic">Lethargic</option>
								<option value="sleeping">Sleeping</option>
							</select>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Concerns
							</label>
							<textarea
								bind:value={concerns}
								rows="2"
								class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 text-base"
								placeholder="Any concerns or unusual behavior..."
							></textarea>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Additional Notes (Optional)
							</label>
							<textarea
								bind:value={notes}
								rows="2"
								class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 text-base"
								placeholder="Any additional notes..."
							></textarea>
						</div>

						<div class="flex gap-3 pt-4">
							<button
								type="button"
								on:click={back}
								class="flex-1 px-4 py-3 border border-gray-300 rounded-xl text-gray-700 text-base hover:bg-gray-50"
							>
								Back
							</button>
							<button
								type="submit"
								disabled={loading}
								class="flex-1 px-4 py-3 bg-purple-600 text-white rounded-xl text-base hover:bg-purple-700 disabled:bg-purple-400"
							>
								{loading ? 'Saving...' : 'Save Entry'}
							</button>
						</div>
					</form>

				{:else if step === 'observation'}
					<!-- General Observation Form -->
					<form on:submit|preventDefault={submitEvent} class="space-y-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Observation <span class="text-red-500">*</span>
							</label>
							<textarea
								bind:value={notes}
								required
								rows="6"
								class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-gray-500 text-base"
								placeholder="Describe what you observed..."
							></textarea>
						</div>

						<div class="flex gap-3 pt-4">
							<button
								type="button"
								on:click={back}
								class="flex-1 px-4 py-3 border border-gray-300 rounded-xl text-gray-700 text-base hover:bg-gray-50"
							>
								Back
							</button>
							<button
								type="submit"
								disabled={loading}
								class="flex-1 px-4 py-3 bg-gray-700 text-white rounded-xl text-base hover:bg-gray-800 disabled:bg-gray-400"
							>
								{loading ? 'Saving...' : 'Save Entry'}
							</button>
						</div>
					</form>
				{/if}
			</div>
		</div>
	</div>
{/if}
