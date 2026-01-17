<script>
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	// Props
	export let maxSizeKB = 500;
	export let maxDimension = 2048;
	export let disabled = false;

	// State
	let fileInput;
	let cameraInput;
	let selectedFile = null;
	let previewUrl = null;
	let compressing = false;
	let compressionProgress = 0;
	let error = '';

	/**
	 * Compress image using Canvas API
	 */
	async function compressImage(file) {
		return new Promise((resolve, reject) => {
			const img = new Image();
			const canvas = document.createElement('canvas');
			const ctx = canvas.getContext('2d');

			img.onload = () => {
				// Calculate new dimensions
				let width = img.width;
				let height = img.height;

				if (width > maxDimension || height > maxDimension) {
					if (width > height) {
						height = Math.round((height * maxDimension) / width);
						width = maxDimension;
					} else {
						width = Math.round((width * maxDimension) / height);
						height = maxDimension;
					}
				}

				canvas.width = width;
				canvas.height = height;

				// Draw image
				ctx.drawImage(img, 0, 0, width, height);

				// Binary search for optimal quality
				const targetSize = maxSizeKB * 1024;
				let minQuality = 0.1;
				let maxQuality = 0.95;
				let bestBlob = null;

				const tryCompress = (quality) => {
					return new Promise((res) => {
						canvas.toBlob(
							(blob) => res(blob),
							'image/jpeg',
							quality
						);
					});
				};

				const findOptimalQuality = async () => {
					compressionProgress = 20;

					// Start with high quality
					let blob = await tryCompress(maxQuality);
					compressionProgress = 40;

					if (blob.size <= targetSize) {
						return blob;
					}

					// Binary search
					while (maxQuality - minQuality > 0.05) {
						const midQuality = (minQuality + maxQuality) / 2;
						blob = await tryCompress(midQuality);
						compressionProgress = 40 + Math.round((1 - (maxQuality - minQuality)) * 50);

						if (blob.size <= targetSize) {
							bestBlob = blob;
							minQuality = midQuality;
						} else {
							maxQuality = midQuality;
						}
					}

					compressionProgress = 90;
					return bestBlob || blob;
				};

				findOptimalQuality()
					.then((blob) => {
						compressionProgress = 100;
						resolve(blob);
					})
					.catch(reject);
			};

			img.onerror = () => reject(new Error('Failed to load image'));
			img.src = URL.createObjectURL(file);
		});
	}

	/**
	 * Handle file selection
	 */
	async function handleFileSelect(event) {
		const file = event.target.files?.[0];
		if (!file) return;

		error = '';

		// Validate file type
		if (!file.type.startsWith('image/')) {
			error = 'Please select an image file';
			return;
		}

		// Validate file size (10MB max before compression)
		if (file.size > 10 * 1024 * 1024) {
			error = 'File too large. Maximum size is 10MB';
			return;
		}

		try {
			compressing = true;
			compressionProgress = 0;

			// Compress the image
			const compressedBlob = await compressImage(file);

			// Create a File object from the blob
			selectedFile = new File([compressedBlob], file.name.replace(/\.[^.]+$/, '.jpg'), {
				type: 'image/jpeg'
			});

			// Create preview URL
			if (previewUrl) {
				URL.revokeObjectURL(previewUrl);
			}
			previewUrl = URL.createObjectURL(selectedFile);

			// Dispatch event with the compressed file
			dispatch('select', { file: selectedFile, previewUrl });
		} catch (err) {
			error = 'Failed to process image: ' + err.message;
			console.error('Image compression error:', err);
		} finally {
			compressing = false;
			compressionProgress = 0;
		}
	}

	/**
	 * Remove selected photo
	 */
	function removePhoto() {
		if (previewUrl) {
			URL.revokeObjectURL(previewUrl);
		}
		selectedFile = null;
		previewUrl = null;
		error = '';

		// Reset file inputs
		if (fileInput) fileInput.value = '';
		if (cameraInput) cameraInput.value = '';

		dispatch('remove');
	}

	/**
	 * Open camera
	 */
	function openCamera() {
		cameraInput?.click();
	}

	/**
	 * Open file picker
	 */
	function openGallery() {
		fileInput?.click();
	}

	// Cleanup on destroy
	import { onDestroy } from 'svelte';
	onDestroy(() => {
		if (previewUrl) {
			URL.revokeObjectURL(previewUrl);
		}
	});
</script>

<div class="photo-capture">
	<!-- Hidden file inputs -->
	<input
		bind:this={cameraInput}
		type="file"
		accept="image/*"
		capture="environment"
		on:change={handleFileSelect}
		class="hidden"
		{disabled}
	/>
	<input
		bind:this={fileInput}
		type="file"
		accept="image/*"
		on:change={handleFileSelect}
		class="hidden"
		{disabled}
	/>

	{#if !selectedFile && !compressing}
		<!-- Capture buttons -->
		<div class="flex gap-3">
			<button
				type="button"
				on:click={openCamera}
				{disabled}
				class="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-xl border border-blue-200 transition-colors dark:bg-blue-950 dark:hover:bg-blue-900 dark:text-blue-300 dark:border-blue-800 disabled:opacity-50"
			>
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
				</svg>
				<span class="text-base font-medium">Camera</span>
			</button>

			<button
				type="button"
				on:click={openGallery}
				{disabled}
				class="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-gray-50 hover:bg-gray-100 text-gray-700 rounded-xl border border-gray-200 transition-colors dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-300 dark:border-slate-700 disabled:opacity-50"
			>
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
				</svg>
				<span class="text-base font-medium">Gallery</span>
			</button>
		</div>
	{:else if compressing}
		<!-- Compression progress -->
		<div class="p-4 bg-gray-50 rounded-xl dark:bg-slate-800">
			<div class="flex items-center gap-3">
				<div class="animate-spin rounded-full h-5 w-5 border-2 border-blue-600 border-t-transparent"></div>
				<span class="text-sm text-gray-600 dark:text-slate-400">Processing image...</span>
			</div>
			<div class="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden dark:bg-slate-700">
				<div
					class="h-full bg-blue-600 transition-all duration-200"
					style="width: {compressionProgress}%"
				></div>
			</div>
		</div>
	{:else if selectedFile}
		<!-- Preview -->
		<div class="relative">
			<img
				src={previewUrl}
				alt="Selected preview"
				class="w-full h-48 object-cover rounded-xl"
			/>
			<button
				type="button"
				on:click={removePhoto}
				class="absolute top-2 right-2 w-8 h-8 bg-red-600 hover:bg-red-700 text-white rounded-full flex items-center justify-center shadow-lg transition-colors"
				aria-label="Remove photo"
			>
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
			<div class="absolute bottom-2 left-2 px-2 py-1 bg-black/60 text-white text-xs rounded">
				{Math.round(selectedFile.size / 1024)} KB
			</div>
		</div>
	{/if}

	{#if error}
		<p class="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>
	{/if}
</div>

<style>
	.hidden {
		display: none;
	}
</style>
