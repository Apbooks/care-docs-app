<script>
	import { createEventDispatcher } from 'svelte';
	import { createEvent } from '$lib/services/api';

	export let show = false;

	const dispatch = createEventDispatcher();

	let step = 'select'; // 'select' or event type
	let loading = false;
	let error = '';

	// Event type forms
	let selectedType = '';
	let notes = '';

	// Medication specific
	let medName = '';
	let dosage = '';
	let route = 'oral';

	// Feeding specific
	let amountMl = '';
	let durationMin = '';
	let formulaType = '';

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
			color: 'blue'
		},
		{
			id: 'feeding',
			label: 'Feeding',
			icon: '🍼',
			color: 'green'
		},
		{
			id: 'diaper',
			label: 'Diaper Change',
			icon: '👶',
			color: 'yellow'
		},
		{
			id: 'demeanor',
			label: 'Demeanor',
			icon: '😊',
			color: 'purple'
		},
		{
			id: 'observation',
			label: 'Observation',
			icon: '📝',
			color: 'gray'
		}
	];

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
		condition = 'wet';
		rash = false;
		skinNotes = '';
		mood = 'neutral';
		activityLevel = 'moderate';
		concerns = '';
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
					metadata = {
						amount_ml: amountMl ? parseInt(amountMl) : null,
						duration_min: durationMin ? parseInt(durationMin) : null,
						formula_type: formulaType
					};
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
	<div class="fixed inset-0 flex items-center justify-center z-50 p-4">
		<div class="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
			<!-- Header -->
			<div class="flex justify-between items-center p-6 border-b border-gray-200">
				<h2 class="text-2xl font-bold text-gray-900">
					{#if step === 'select'}
						Quick Entry
					{:else}
						{eventTypes.find(t => t.id === selectedType)?.label}
					{/if}
				</h2>
				<button
					on:click={close}
					class="text-gray-400 hover:text-gray-600 transition-colors"
				>
					<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>

			<!-- Content -->
			<div class="p-6">
				{#if error}
					<div class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
						<p class="text-red-800 text-sm">{error}</p>
					</div>
				{/if}

				{#if step === 'select'}
					<!-- Event Type Selection -->
					<p class="text-gray-600 mb-4">Select the type of event to log:</p>
					<div class="grid grid-cols-2 gap-3">
						{#each eventTypes as type}
							<button
								on:click={() => selectType(type.id)}
								class="p-4 border-2 border-gray-200 rounded-lg hover:border-{type.color}-500 hover:bg-{type.color}-50 transition-all text-center"
							>
								<div class="text-4xl mb-2">{type.icon}</div>
								<div class="font-medium text-gray-900">{type.label}</div>
							</button>
						{/each}
					</div>

				{:else if step === 'medication'}
					<!-- Medication Form -->
					<form on:submit|preventDefault={submitEvent} class="space-y-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">
								Medication Name <span class="text-red-500">*</span>
							</label>
							<input
								type="text"
								bind:value={medName}
								required
								class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
								placeholder="e.g., Tylenol"
							/>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">
								Dosage <span class="text-red-500">*</span>
							</label>
							<input
								type="text"
								bind:value={dosage}
								required
								class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
								placeholder="e.g., 5ml, 100mg"
							/>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">
								Route
							</label>
							<select
								bind:value={route}
								class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
							>
								<option value="oral">Oral</option>
								<option value="tube">Tube Fed</option>
								<option value="topical">Topical</option>
								<option value="injection">Injection</option>
							</select>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">
								Notes (Optional)
							</label>
							<textarea
								bind:value={notes}
								rows="3"
								class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
								placeholder="Any additional notes..."
							></textarea>
						</div>

						<div class="flex gap-3 pt-4">
							<button
								type="button"
								on:click={back}
								class="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
							>
								Back
							</button>
							<button
								type="submit"
								disabled={loading}
								class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-400"
							>
								{loading ? 'Saving...' : 'Save Entry'}
							</button>
						</div>
					</form>

				{:else if step === 'feeding'}
					<!-- Feeding Form -->
					<form on:submit|preventDefault={submitEvent} class="space-y-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">
								Amount (ml)
							</label>
							<input
								type="number"
								bind:value={amountMl}
								min="0"
								class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
								placeholder="e.g., 240"
							/>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">
								Duration (minutes)
							</label>
							<input
								type="number"
								bind:value={durationMin}
								min="0"
								class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
								placeholder="e.g., 20"
							/>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">
								Formula/Food Type
							</label>
							<input
								type="text"
								bind:value={formulaType}
								class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
								placeholder="e.g., Standard formula, Pediasure"
							/>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">
								Notes (Optional)
							</label>
							<textarea
								bind:value={notes}
								rows="3"
								class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
								placeholder="Any additional notes..."
							></textarea>
						</div>

						<div class="flex gap-3 pt-4">
							<button
								type="button"
								on:click={back}
								class="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
							>
								Back
							</button>
							<button
								type="submit"
								disabled={loading}
								class="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-green-400"
							>
								{loading ? 'Saving...' : 'Save Entry'}
							</button>
						</div>
					</form>

				{:else if step === 'diaper'}
					<!-- Diaper Form -->
					<form on:submit|preventDefault={submitEvent} class="space-y-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">
								Condition
							</label>
							<select
								bind:value={condition}
								class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500"
							>
								<option value="wet">Wet</option>
								<option value="dirty">Dirty</option>
								<option value="both">Both</option>
								<option value="dry">Dry (preventive change)</option>
							</select>
						</div>

						<div>
							<label class="flex items-center gap-2">
								<input
									type="checkbox"
									bind:checked={rash}
									class="w-4 h-4 text-yellow-600 border-gray-300 rounded focus:ring-yellow-500"
								/>
								<span class="text-sm font-medium text-gray-700">Rash present</span>
							</label>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">
								Skin Condition Notes
							</label>
							<textarea
								bind:value={skinNotes}
								rows="2"
								class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500"
								placeholder="Describe skin condition..."
							></textarea>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">
								Additional Notes (Optional)
							</label>
							<textarea
								bind:value={notes}
								rows="2"
								class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500"
								placeholder="Any additional notes..."
							></textarea>
						</div>

						<div class="flex gap-3 pt-4">
							<button
								type="button"
								on:click={back}
								class="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
							>
								Back
							</button>
							<button
								type="submit"
								disabled={loading}
								class="flex-1 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:bg-yellow-400"
							>
								{loading ? 'Saving...' : 'Save Entry'}
							</button>
						</div>
					</form>

				{:else if step === 'demeanor'}
					<!-- Demeanor Form -->
					<form on:submit|preventDefault={submitEvent} class="space-y-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">
								Mood
							</label>
							<select
								bind:value={mood}
								class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
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
							<label class="block text-sm font-medium text-gray-700 mb-2">
								Activity Level
							</label>
							<select
								bind:value={activityLevel}
								class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
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
							<label class="block text-sm font-medium text-gray-700 mb-2">
								Concerns
							</label>
							<textarea
								bind:value={concerns}
								rows="2"
								class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
								placeholder="Any concerns or unusual behavior..."
							></textarea>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">
								Additional Notes (Optional)
							</label>
							<textarea
								bind:value={notes}
								rows="2"
								class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
								placeholder="Any additional notes..."
							></textarea>
						</div>

						<div class="flex gap-3 pt-4">
							<button
								type="button"
								on:click={back}
								class="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
							>
								Back
							</button>
							<button
								type="submit"
								disabled={loading}
								class="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-purple-400"
							>
								{loading ? 'Saving...' : 'Save Entry'}
							</button>
						</div>
					</form>

				{:else if step === 'observation'}
					<!-- General Observation Form -->
					<form on:submit|preventDefault={submitEvent} class="space-y-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-2">
								Observation <span class="text-red-500">*</span>
							</label>
							<textarea
								bind:value={notes}
								required
								rows="6"
								class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500"
								placeholder="Describe what you observed..."
							></textarea>
						</div>

						<div class="flex gap-3 pt-4">
							<button
								type="button"
								on:click={back}
								class="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
							>
								Back
							</button>
							<button
								type="submit"
								disabled={loading}
								class="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:bg-gray-400"
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
