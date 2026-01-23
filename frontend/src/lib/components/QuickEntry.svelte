<script>
	import { createEventDispatcher } from 'svelte';
	import {
		createEvent,
		getQuickMedsForRecipient,
		getQuickFeedsForRecipient,
		getMedications,
		getMedRoutes,
		getActiveContinuousFeed,
		startContinuousFeed,
		stopContinuousFeed,
		uploadPhoto,
		checkMedEarly
	} from '$lib/services/api';
	import { timezone } from '$lib/stores/settings';
import { selectedRecipientId, selectedRecipient, CARE_CATEGORIES } from '$lib/stores/recipients';
	import { isOnline, queuePhoto } from '$lib/stores/offline';
	import PhotoCapture from './PhotoCapture.svelte';

	export let show = false;

	const dispatch = createEventDispatcher();

	let step = 'select'; // 'select' or event type
	let loading = false;
	let error = '';
	let earlyWarning = null;
	let pendingMedicationAction = null;

	// Photo state
	let selectedPhoto = null;
	let photoPreviewUrl = null;
	let uploadingPhoto = false;

	let quickLoading = false;
	let quickError = '';
	let quickLoaded = false;
	let quickLoadedFor = null;
	let quickMeds = [];
	let quickFeeds = [];
	let medLibrary = [];
	let medRoutes = [];
	let medLibraryLoading = false;
	let quickNoteEnabled = false;
	let quickNote = '';

	// Event type forms
	let selectedType = '';
	let notes = '';
	let enabledCategories = CARE_CATEGORIES;

	// Medication specific
	let medName = '';
	let dosage = '';
	let route = '';
	let selectedMedicationId = '';

	// Feeding specific
	let feedingMode = 'bolus';
	let amountMl = '';
	let durationMin = '';
	let formulaType = '';
	let feedName = '';
	let feedRate = '';
	let feedDose = '';
	let feedInterval = '';
	let oralNotes = '';
	let pumpTotal = '';
	let activeContinuousFeed = null;

	// Diaper specific
	let condition = '';
	let rash = false;
	let skinNotes = '';
	let diaperSize = '';
	let wetSize = '';
	let dirtySize = '';
	let diaperConsistency = '';

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

	$: enabledCategories = $selectedRecipient?.enabled_categories || CARE_CATEGORIES;
	$: if (selectedType && !enabledCategories.includes(selectedType)) {
		selectedType = '';
		step = 'select';
	}

	$: if (show && $selectedRecipientId && quickLoadedFor !== $selectedRecipientId) {
		quickLoadedFor = $selectedRecipientId;
		loadQuickTemplates();
	}
	$: if (show && $selectedRecipientId) {
		loadActiveFeed();
	}

	async function loadActiveFeed() {
		if (!$selectedRecipientId) {
			activeContinuousFeed = null;
			return;
		}
		try {
			const response = await getActiveContinuousFeed($selectedRecipientId);
			activeContinuousFeed = response?.active_feed || null;
		} catch (err) {
			activeContinuousFeed = null;
		}
	}

	async function loadQuickTemplates() {
		quickLoading = true;
		quickError = '';

		try {
			const [meds, feeds, medList, routes] = await Promise.all([
				getQuickMedsForRecipient($selectedRecipientId),
				getQuickFeedsForRecipient($selectedRecipientId),
				getMedications({ recipient_id: $selectedRecipientId }),
				getMedRoutes({ recipient_id: $selectedRecipientId })
			]);
			quickMeds = meds;
			quickFeeds = feeds;
			medLibrary = medList;
			medRoutes = routes;
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

	function resetPhoto() {
		selectedPhoto = null;
		photoPreviewUrl = null;
		uploadingPhoto = false;
	}

	function handlePhotoSelect(event) {
		selectedPhoto = event.detail.file;
		photoPreviewUrl = event.detail.previewUrl;
	}

	function handlePhotoRemove() {
		resetPhoto();
	}

	function reset() {
		step = 'select';
		selectedType = '';
		notes = '';
		error = '';
		// Reset type-specific fields
		medName = '';
		dosage = '';
		route = '';
		selectedMedicationId = '';
		amountMl = '';
		durationMin = '';
		formulaType = '';
		feedName = '';
		feedingMode = 'bolus';
		feedRate = '';
		feedDose = '';
		feedInterval = '';
		oralNotes = '';
		pumpTotal = '';
		condition = '';
		rash = false;
		skinNotes = '';
		diaperSize = '';
		wetSize = '';
		dirtySize = '';
		diaperConsistency = '';
		mood = 'neutral';
		activityLevel = 'moderate';
		concerns = '';
		resetQuickNote();
		resetPhoto();
	}

	function applyMedicationSelection(medication) {
		if (!medication) return;
		selectedMedicationId = medication.id;
		medName = medication.name || '';
		const dose = medication.default_dose || '';
		const unit = medication.dose_unit ? ` ${medication.dose_unit}` : '';
		dosage = `${dose}${unit}`.trim();
		const availableRoutes = getAvailableRoutes(medication);
		route = medication.default_route || availableRoutes[0] || '';
	}

	function getAvailableRoutes(medication) {
		const medRouteNames = medication?.routes?.map((item) => item.name) || [];
		if (medRoutes.length) {
			const activeNames = new Set(medRoutes.map((item) => item.name));
			const filtered = medRouteNames.filter((name) => activeNames.has(name));
			if (filtered.length) return filtered;
			if (medication?.default_route && activeNames.has(medication.default_route)) {
				return [medication.default_route];
			}
			return medRoutes.map((item) => item.name);
		}
		if (medRouteNames.length) return medRouteNames;
		if (medication?.default_route) return [medication.default_route];
		return [];
	}

	function getRouteOptionsForSelect() {
		if (selectedMedicationId && selectedMedicationId !== 'other') {
			const med = medLibrary.find((item) => item.id === selectedMedicationId);
			if (med) return getAvailableRoutes(med);
		}
		return medRoutes.map((item) => item.name);
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
		if (loading || !$selectedRecipientId) return;
		error = '';
		loading = true;

		try {
			const response = await startContinuousFeed({
				recipient_id: $selectedRecipientId,
				name: feedName || null,
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
		if (!activeContinuousFeed || loading || !$selectedRecipientId) return;
		error = '';
		loading = true;

		try {
			const response = await stopContinuousFeed($selectedRecipientId, actualTotal);
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

	async function logQuickMedication(template, overrideEarlyCheck = false) {
		if (loading || !$selectedRecipientId) return;
		error = '';
		loading = true;

		try {
			if (!template.default_route) {
				throw new Error('Set a default route in the medication library to use quick add.');
			}
			const dose = template.default_dose || '';
			const unit = template.dose_unit ? ` ${template.dose_unit}` : '';
			const medDose = `${dose}${unit}`.trim();
			const quickNotes = quickNoteEnabled ? (quickNote.trim() || null) : null;

			if (!overrideEarlyCheck) {
				const ok = await handleMedicationEarlyCheck(template.name, () => logQuickMedication(template, true));
				if (!ok) {
					loading = false;
					return;
				}
			}

			const newEvent = await createEvent({
				type: 'medication',
				timestamp: new Date().toISOString(),
				recipient_id: $selectedRecipientId,
				notes: quickNotes,
				metadata: {
					med_name: template.name,
					dosage: medDose,
					route: template.default_route
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
		if (loading || !$selectedRecipientId) return;
		error = '';
		loading = true;

		try {
				if (template.mode === 'continuous') {
					if (activeContinuousFeed) {
						throw new Error('A continuous feed is already running.');
					}

					const response = await startContinuousFeed({
						recipient_id: $selectedRecipientId,
						name: template.name || null,
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
				recipient_id: $selectedRecipientId,
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

	async function submitEvent(arg) {
		const overrideEarlyCheck = arg === true;
		if (!$selectedRecipientId) {
			error = 'Select a care recipient first.';
			return;
		}
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
					if (condition === 'both') {
						metadata = {
							condition: condition,
							wet_size: wetSize || null,
							dirty_size: dirtySize || null,
							consistency: diaperConsistency || null,
							rash: rash,
							skin_notes: skinNotes
						};
					} else {
						metadata = {
							condition: condition,
							size: diaperSize || null,
							consistency: diaperConsistency || null,
							rash: rash,
							skin_notes: skinNotes
						};
					}
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

			if (selectedType === 'medication' && !overrideEarlyCheck) {
				const ok = await handleMedicationEarlyCheck(medName, submitEventWithOverride);
				if (!ok) {
					loading = false;
					return;
				}
			}

			// Create the event
			const newEvent = await createEvent({
				type: selectedType,
				timestamp: new Date().toISOString(),
				recipient_id: $selectedRecipientId,
				notes: notes || null,
				metadata: metadata
			});

			// Upload photo if one was selected
			if (selectedPhoto && newEvent?.id) {
				uploadingPhoto = true;
				try {
					if ($isOnline && !newEvent._offline) {
						// Online: upload directly
						await uploadPhoto(newEvent.id, selectedPhoto);
					} else {
						// Offline: queue for later
						await queuePhoto(newEvent.id, selectedPhoto, selectedPhoto.name);
					}
				} catch (photoErr) {
					console.error('Photo upload failed:', photoErr);
					// Don't fail the whole operation for photo upload failure
					// The event was already created
				} finally {
					uploadingPhoto = false;
				}
			}

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

	async function submitEventWithOverride() {
		if (loading) return;
		await submitEvent(true);
	}

	async function handleMedicationEarlyCheck(medNameValue, continueAction) {
		if (!medNameValue || !$selectedRecipientId) {
			return true;
		}
		try {
			const result = await checkMedEarly({
				recipient_id: $selectedRecipientId,
				med_name: medNameValue,
				timestamp: new Date().toISOString()
			});
			if (result?.status === 'early') {
				earlyWarning = {
					medName: medNameValue,
					minutesUntilDue: result.minutes_until_due,
					warningLevel: result.warning_level,
					nextDue: result.next_due
				};
				pendingMedicationAction = continueAction;
				return false;
			}
		} catch (err) {
			// If check fails, allow the event to proceed.
		}
		return true;
	}

	function confirmEarlyWarning() {
		if (!pendingMedicationAction) return;
		const action = pendingMedicationAction;
		pendingMedicationAction = null;
		earlyWarning = null;
		action();
	}

	function cancelEarlyWarning() {
		earlyWarning = null;
		pendingMedicationAction = null;
	}
</script>

{#if show}
	<!-- Modal Backdrop -->
	<button
		type="button"
		class="fixed inset-0 bg-black bg-opacity-50 z-40"
		on:click={close}
		aria-label="Close quick entry"
	></button>

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
				{#if earlyWarning}
					<div class="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-lg dark:bg-amber-950 dark:border-amber-900">
						<p class="text-amber-900 dark:text-amber-100 text-base font-semibold">Medication due soon</p>
						<p class="text-amber-800 dark:text-amber-200 text-sm mt-1">
							{earlyWarning.medName} is due in {earlyWarning.minutesUntilDue} minutes.
						</p>
						<div class="mt-3 flex flex-wrap gap-2">
							<button
								type="button"
								on:click={confirmEarlyWarning}
								class="px-4 py-2 rounded-lg bg-amber-600 text-white text-sm font-semibold hover:bg-amber-700"
							>
								Log anyway
							</button>
							<button
								type="button"
								on:click={cancelEarlyWarning}
								class="px-4 py-2 rounded-lg bg-white text-amber-800 border border-amber-300 text-sm font-semibold hover:bg-amber-100"
							>
								Cancel
							</button>
						</div>
					</div>
				{/if}
				{#if !$selectedRecipientId}
					<div class="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg dark:bg-yellow-950 dark:border-yellow-900">
						<p class="text-yellow-800 dark:text-yellow-200 text-base">
							Select a care recipient before logging an entry.
						</p>
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
						{#each eventTypes.filter((type) => enabledCategories.includes(type.id)) as type}
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
										<div class="text-xs text-gray-700 dark:text-slate-200 mt-1">
											{med.default_dose ? `${med.default_dose}${med.dose_unit ? ` ${med.dose_unit}` : ''}` : 'Select dose'}
										</div>
									</button>
								{/each}
							</div>
						</div>
					{/if}

					<!-- Medication Form -->
					<form on:submit|preventDefault={submitEvent} class="space-y-4">
						<div>
							<label for="quick-medication-select" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Medication <span class="text-red-500">*</span>
							</label>
							<select
								id="quick-medication-select"
								bind:value={selectedMedicationId}
								on:change={() => {
									const med = medLibrary.find(item => item.id === selectedMedicationId);
									if (med) {
										applyMedicationSelection(med);
									} else {
										medName = '';
										dosage = '';
										route = '';
									}
								}}
								class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 text-base"
								required
							>
								<option value="" disabled>Select a medication</option>
								{#each medLibrary as med}
									<option value={med.id}>{med.name}</option>
								{/each}
								<option value="other">Other</option>
							</select>
						</div>

						{#if selectedMedicationId === 'other' || !selectedMedicationId}
							<div>
								<label for="quick-medication-name" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
									Medication Name <span class="text-red-500">*</span>
								</label>
								<input
									id="quick-medication-name"
									type="text"
									bind:value={medName}
									required
									class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 text-base"
									placeholder="e.g., Tylenol"
								/>
							</div>
						{/if}

						<div>
							<label for="quick-medication-dosage" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Dosage <span class="text-red-500">*</span>
							</label>
							<input
								id="quick-medication-dosage"
								type="text"
								bind:value={dosage}
								required
								class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 text-base"
								placeholder="e.g., 5ml, 100mg"
							/>
						</div>

						<div>
							<label for="quick-medication-route" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Route
							</label>
							{#if getRouteOptionsForSelect().length > 0}
								<select
									id="quick-medication-route"
									bind:value={route}
									required
									class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 text-base"
								>
									<option value="" disabled>Select route</option>
									{#each getRouteOptionsForSelect() as routeOption}
										<option value={routeOption}>{routeOption}</option>
									{/each}
								</select>
							{:else}
								<input
									id="quick-medication-route"
									type="text"
									bind:value={route}
									class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 text-base"
									placeholder="Route"
								/>
							{/if}
						</div>

						<div>
							<label for="quick-medication-notes" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Notes (Optional)
							</label>
							<textarea
								id="quick-medication-notes"
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
											{feed.name || feed.mode || 'bolus'}
										</div>
										{#if feed.name}
											<div class="text-xs text-gray-500 dark:text-slate-300 mt-0.5 capitalize">{feed.mode || 'bolus'}</div>
										{/if}
										{#if (feed.mode || 'bolus') === 'continuous'}
											<div class="text-xs text-gray-700 dark:text-slate-200 mt-1">{feed.rate_ml_hr || '-'} ml/hr · {feed.interval_hr || '-'} hr</div>
											{#if feed.dose_ml}
												<div class="text-xs text-gray-600 dark:text-slate-200 mt-1">Dose {feed.dose_ml} ml</div>
											{/if}
										{:else if (feed.mode || 'bolus') === 'oral'}
											<div class="text-xs text-gray-700 dark:text-slate-200 mt-1 truncate">{feed.oral_notes || 'Oral notes'}</div>
										{:else}
											<div class="text-xs text-gray-700 dark:text-slate-200 mt-1">{feed.amount_ml || '-'} ml</div>
										{/if}
										{#if feed.formula_type}
											<div class="text-xs text-gray-600 dark:text-slate-300 mt-1">{feed.formula_type}</div>
										{/if}
									</button>
								{/each}
							</div>
						</div>
					{/if}

					<!-- Feeding Form -->
					<form on:submit|preventDefault={submitEvent} class="space-y-4">
						<div>
							<p class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Feeding Type
							</p>
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
										{#if activeContinuousFeed.name}
											{activeContinuousFeed.name} ·
										{/if}
										Rate {activeContinuousFeed.rate_ml_hr || '-'} ml/hr · Dose {activeContinuousFeed.dose_ml || '-'} ml · Interval {activeContinuousFeed.interval_hr || '-'} hr
									</p>
								</div>
							{/if}

							<div class="grid gap-3 sm:grid-cols-2">
								<div class="sm:col-span-2">
									<label for="quick-feed-name" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
										Feed Name (optional)
									</label>
									<input
										id="quick-feed-name"
										type="text"
										bind:value={feedName}
										class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 text-base"
										placeholder="Overnight"
									/>
								</div>
								<div>
									<label for="quick-feed-rate" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
										Feed Rate (ml/hr)
									</label>
									<input
										id="quick-feed-rate"
										type="number"
										min="0"
										bind:value={feedRate}
										class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 text-base"
										placeholder="500"
									/>
								</div>
								<div>
									<label for="quick-feed-dose" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
										Dose (ml) - leave blank for infinite
									</label>
									<input
										id="quick-feed-dose"
										type="number"
										min="0"
										bind:value={feedDose}
										class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 text-base"
										placeholder="95"
									/>
								</div>
								<div>
									<label for="quick-feed-interval" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
										Feed Interval (hr)
									</label>
									<input
										id="quick-feed-interval"
										type="number"
										min="0"
										step="0.1"
										bind:value={feedInterval}
										class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 text-base"
										placeholder="0.5"
									/>
								</div>
								<div>
									<label for="quick-feed-formula" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
										Formula Type
									</label>
									<input
										id="quick-feed-formula"
										type="text"
										bind:value={formulaType}
										class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 text-base"
										placeholder="Pediasure"
									/>
								</div>
							</div>

							<div>
								<label for="quick-feed-notes" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
									Notes (Optional)
								</label>
								<textarea
									id="quick-feed-notes"
									bind:value={notes}
									rows="2"
									class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 text-base"
									placeholder="Any additional notes..."
								></textarea>
							</div>
							{#if activeContinuousFeed}
								<div>
									<label for="quick-feed-pump-total" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
										Pump Total (ml)
									</label>
									<input
										id="quick-feed-pump-total"
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
								<label for="quick-feed-amount" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
									Amount (ml)
								</label>
								<input
									id="quick-feed-amount"
									type="number"
									bind:value={amountMl}
									min="0"
									class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 text-base"
									placeholder="95"
								/>
							</div>

							<div>
								<label for="quick-feed-formula" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
									Formula Type
								</label>
								<input
									id="quick-feed-formula"
									type="text"
									bind:value={formulaType}
									class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 text-base"
									placeholder="Pediasure"
								/>
							</div>
							<div>
								<label for="quick-feed-notes" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
									Notes (Optional)
								</label>
								<textarea
									id="quick-feed-notes"
									bind:value={notes}
									rows="2"
									class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 text-base"
									placeholder="Any additional notes..."
								></textarea>
							</div>
						{:else}
							<div>
								<label for="quick-feed-oral-notes" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
									Oral Feeding Notes
								</label>
								<textarea
									id="quick-feed-oral-notes"
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
						<!-- Type Selection - Buttons -->
						<div>
							<p class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Type
							</p>
							<div class="grid grid-cols-3 gap-2">
								{#each [
									{ value: 'wet', label: 'Wet', icon: '💧' },
									{ value: 'dirty', label: 'Dirty', icon: '💩' },
									{ value: 'both', label: 'Both', icon: '💧💩' }
								] as opt}
									<button
										type="button"
										on:click={() => {
											const prevCondition = condition;
											condition = opt.value;
											if (opt.value === 'wet') {
												diaperConsistency = '';
											}
											// Clear size fields when switching between both and wet/dirty
											if (opt.value === 'both' && prevCondition !== 'both') {
												wetSize = '';
												dirtySize = '';
												diaperSize = '';
											} else if (opt.value !== 'both' && prevCondition === 'both') {
												diaperSize = '';
												wetSize = '';
												dirtySize = '';
											}
										}}
										class="px-4 py-3 rounded-xl text-base font-medium transition-all
											{condition === opt.value
												? 'bg-yellow-500 text-white ring-2 ring-yellow-600'
												: 'bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-600'}"
									>
										{opt.icon} {opt.label}
									</button>
								{/each}
							</div>
						</div>

						<!-- Size Selection - Show for wet or dirty (single size) -->
						{#if condition === 'wet' || condition === 'dirty'}
							<div>
								<p class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
									Size
								</p>
								<div class="grid grid-cols-3 gap-2">
									{#each ['small', 'medium', 'large'] as size}
										<button
											type="button"
											on:click={() => diaperSize = size}
											class="px-4 py-3 rounded-xl text-base font-medium capitalize transition-all
												{diaperSize === size
													? 'bg-yellow-500 text-white ring-2 ring-yellow-600'
													: 'bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-600'}"
										>
											{size}
										</button>
									{/each}
								</div>
							</div>
						{/if}

						<!-- Separate Wet and Dirty Size Selection - Show for both -->
						{#if condition === 'both'}
							<div>
								<p class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
									💧 Wet Size
								</p>
								<div class="grid grid-cols-3 gap-2">
									{#each ['small', 'medium', 'large'] as size}
										<button
											type="button"
											on:click={() => wetSize = size}
											class="px-4 py-3 rounded-xl text-base font-medium capitalize transition-all
												{wetSize === size
													? 'bg-blue-500 text-white ring-2 ring-blue-600'
													: 'bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-600'}"
										>
											{size}
										</button>
									{/each}
								</div>
							</div>
							<div>
								<p class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
									💩 Dirty Size
								</p>
								<div class="grid grid-cols-3 gap-2">
									{#each ['small', 'medium', 'large'] as size}
										<button
											type="button"
											on:click={() => dirtySize = size}
											class="px-4 py-3 rounded-xl text-base font-medium capitalize transition-all
												{dirtySize === size
													? 'bg-amber-600 text-white ring-2 ring-amber-700'
													: 'bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-600'}"
										>
											{size}
										</button>
									{/each}
								</div>
							</div>
						{/if}

						<!-- Consistency Selection - Show only for dirty or both -->
						{#if condition === 'dirty' || condition === 'both'}
							<div>
								<p class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
									Consistency
								</p>
								<div class="grid grid-cols-2 gap-2">
									{#each [
										{ value: 'loose', label: 'Loose' },
										{ value: 'semi-firm', label: 'Semi-firm' },
										{ value: 'firm', label: 'Firm' },
										{ value: 'good', label: 'Good' }
									] as opt}
										<button
											type="button"
											on:click={() => diaperConsistency = opt.value}
											class="px-4 py-3 rounded-xl text-base font-medium transition-all
												{diaperConsistency === opt.value
													? 'bg-yellow-500 text-white ring-2 ring-yellow-600'
													: 'bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-600'}"
										>
											{opt.label}
										</button>
									{/each}
								</div>
							</div>
						{/if}

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
							<label for="diaper-skin-notes" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Skin Condition Notes
							</label>
							<textarea
								id="diaper-skin-notes"
								bind:value={skinNotes}
								rows="2"
								class="w-full px-4 py-3 border border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 rounded-xl focus:ring-2 focus:ring-yellow-500 text-base"
								placeholder="Describe skin condition..."
							></textarea>
						</div>

						<div>
							<label for="diaper-notes" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Additional Notes (Optional)
							</label>
							<textarea
								id="diaper-notes"
								bind:value={notes}
								rows="2"
								class="w-full px-4 py-3 border border-gray-300 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 rounded-xl focus:ring-2 focus:ring-yellow-500 text-base"
								placeholder="Any additional notes..."
							></textarea>
						</div>

						<!-- Photo Capture - useful for documenting rashes -->
						<div>
							<p class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Add Photo (Optional)
							</p>
							<PhotoCapture
								on:select={handlePhotoSelect}
								on:remove={handlePhotoRemove}
								disabled={loading}
							/>
						</div>

						<div class="flex gap-3 pt-4">
							<button
								type="button"
								on:click={back}
								class="flex-1 px-4 py-3 border border-gray-300 dark:border-slate-600 rounded-xl text-gray-700 dark:text-slate-300 text-base hover:bg-gray-50 dark:hover:bg-slate-700"
							>
								Back
							</button>
							<button
								type="submit"
								disabled={loading || !condition}
								class="flex-1 px-4 py-3 bg-yellow-600 text-white rounded-xl text-base hover:bg-yellow-700 disabled:bg-yellow-400 disabled:cursor-not-allowed"
							>
								{loading ? 'Saving...' : 'Save Entry'}
							</button>
						</div>
					</form>

				{:else if step === 'demeanor'}
					<!-- Demeanor Form -->
					<form on:submit|preventDefault={submitEvent} class="space-y-4">
						<div>
							<label for="demeanor-mood" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Mood
							</label>
							<select
								id="demeanor-mood"
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
							<label for="demeanor-activity" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Activity Level
							</label>
							<select
								id="demeanor-activity"
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
							<label for="demeanor-concerns" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Concerns
							</label>
							<textarea
								id="demeanor-concerns"
								bind:value={concerns}
								rows="2"
								class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 text-base"
								placeholder="Any concerns or unusual behavior..."
							></textarea>
						</div>

						<div>
							<label for="demeanor-notes" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Additional Notes (Optional)
							</label>
							<textarea
								id="demeanor-notes"
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
							<label for="observation-notes" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Observation <span class="text-red-500">*</span>
							</label>
							<textarea
								id="observation-notes"
								bind:value={notes}
								required
								rows="6"
								class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-gray-500 text-base"
								placeholder="Describe what you observed..."
							></textarea>
						</div>

						<!-- Photo Capture -->
						<div>
							<p class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
								Add Photo (Optional)
							</p>
							<PhotoCapture
								on:select={handlePhotoSelect}
								on:remove={handlePhotoRemove}
								disabled={loading}
							/>
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
