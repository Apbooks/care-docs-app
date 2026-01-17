<script>
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	// Props
	export let photos = [];
	export let loading = false;
	export let canDelete = true;

	// State
	let lightboxOpen = false;
	let lightboxIndex = 0;
	let confirmDelete = null;
	let deleting = false;

	// Get full image URL
	function getPhotoUrl(photo) {
		const API_BASE = import.meta.env.VITE_PUBLIC_API_URL || '';
		const API_ORIGIN = API_BASE.replace(/\/api\/?$/, '');
		if (photo.url && /^https?:\/\//i.test(photo.url)) return photo.url;
		return `${API_ORIGIN || API_BASE}${photo.url}`;
	}

	// Get thumbnail URL
	function getThumbnailUrl(photo) {
		const API_BASE = import.meta.env.VITE_PUBLIC_API_URL || '';
		const API_ORIGIN = API_BASE.replace(/\/api\/?$/, '');
		const rawUrl = photo.thumbnail_url || photo.url;
		if (rawUrl && /^https?:\/\//i.test(rawUrl)) return rawUrl;
		return `${API_ORIGIN || API_BASE}${rawUrl}`;
	}

	// Open lightbox
	function openLightbox(index) {
		lightboxIndex = index;
		lightboxOpen = true;
	}

	// Close lightbox
	function closeLightbox() {
		lightboxOpen = false;
	}

	// Navigate lightbox
	function nextPhoto() {
		lightboxIndex = (lightboxIndex + 1) % photos.length;
	}

	function prevPhoto() {
		lightboxIndex = (lightboxIndex - 1 + photos.length) % photos.length;
	}

	// Handle keyboard navigation
	function handleKeydown(event) {
		if (!lightboxOpen) return;

		switch (event.key) {
			case 'Escape':
				closeLightbox();
				break;
			case 'ArrowRight':
				nextPhoto();
				break;
			case 'ArrowLeft':
				prevPhoto();
				break;
		}
	}

	// Delete confirmation
	function showDeleteConfirm(photo, index, event) {
		event.stopPropagation();
		confirmDelete = { photo, index };
	}

	function cancelDelete() {
		confirmDelete = null;
	}

	async function confirmDeletePhoto() {
		if (!confirmDelete) return;

		deleting = true;
		try {
			dispatch('delete', { photo: confirmDelete.photo });
		} finally {
			deleting = false;
			confirmDelete = null;
		}
	}

	// Format file size
	function formatSize(bytes) {
		if (bytes < 1024) return bytes + ' B';
		if (bytes < 1024 * 1024) return Math.round(bytes / 1024) + ' KB';
		return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
	}

	// Format date
	function formatDate(dateStr) {
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			hour: 'numeric',
			minute: '2-digit'
		});
	}
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="photo-gallery">
	{#if loading}
		<div class="flex items-center justify-center py-8">
			<div class="animate-spin rounded-full h-6 w-6 border-2 border-blue-600 border-t-transparent"></div>
		</div>
	{:else if photos.length === 0}
		<div class="text-center py-6 text-gray-500 dark:text-slate-400">
			<svg class="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
			</svg>
			<p class="text-sm">No photos attached</p>
		</div>
	{:else}
		<!-- Photo grid -->
		<div class="grid grid-cols-3 gap-2">
			{#each photos as photo, index}
				<div class="relative group">
					<button
						type="button"
						on:click={() => openLightbox(index)}
						class="w-full aspect-square rounded-lg overflow-hidden bg-gray-100 dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
					>
						<img
							src={getThumbnailUrl(photo)}
							alt="Event photo {index + 1}"
							class="w-full h-full object-cover transition-transform group-hover:scale-105"
							loading="lazy"
						/>
					</button>

					{#if canDelete}
						<button
							type="button"
							on:click={(e) => showDeleteConfirm(photo, index, e)}
							class="absolute top-1 right-1 w-6 h-6 bg-red-600 hover:bg-red-700 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow"
							aria-label="Delete photo"
						>
							<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>

<!-- Lightbox -->
{#if lightboxOpen && photos[lightboxIndex]}
	<div class="fixed inset-0 z-50 flex items-center justify-center">
		<button
			type="button"
			class="absolute inset-0 bg-black/95"
			on:click={closeLightbox}
			aria-label="Close lightbox"
		></button>
		<div
			class="relative z-10 flex items-center justify-center w-full h-full"
			role="dialog"
			aria-modal="true"
			tabindex="-1"
		>
		<!-- Close button -->
		<button
			type="button"
			on:click={closeLightbox}
			class="absolute top-4 right-4 w-10 h-10 bg-white/10 hover:bg-white/20 text-white rounded-full flex items-center justify-center z-10"
			aria-label="Close"
		>
			<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
			</svg>
		</button>

		<!-- Navigation arrows -->
		{#if photos.length > 1}
			<button
				type="button"
				on:click|stopPropagation={prevPhoto}
				class="absolute left-4 top-1/2 -translate-y-1/2 w-12 h-12 bg-white/10 hover:bg-white/20 text-white rounded-full flex items-center justify-center z-10"
				aria-label="Previous photo"
			>
				<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
				</svg>
			</button>

			<button
				type="button"
				on:click|stopPropagation={nextPhoto}
				class="absolute right-4 top-1/2 -translate-y-1/2 w-12 h-12 bg-white/10 hover:bg-white/20 text-white rounded-full flex items-center justify-center z-10"
				aria-label="Next photo"
			>
				<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
				</svg>
			</button>
		{/if}

		<!-- Image -->
		<img
			src={getPhotoUrl(photos[lightboxIndex])}
			alt="Event photo {lightboxIndex + 1}"
			class="max-w-full max-h-full object-contain"
		/>

		<!-- Photo info -->
		<div class="absolute bottom-4 left-4 right-4 text-center text-white text-sm">
			<span class="bg-black/50 px-3 py-1 rounded-full">
				{lightboxIndex + 1} / {photos.length}
				{#if photos[lightboxIndex].size_bytes}
					· {formatSize(photos[lightboxIndex].size_bytes)}
				{/if}
			</span>
		</div>
		</div>
	</div>
{/if}

<!-- Delete confirmation modal -->
{#if confirmDelete}
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4">
		<button
			type="button"
			class="absolute inset-0 bg-black/50"
			on:click={cancelDelete}
			aria-label="Close delete confirmation"
		></button>
		<div class="relative z-10 bg-white dark:bg-slate-800 rounded-2xl p-6 max-w-sm w-full shadow-xl">
			<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
				Delete Photo?
			</h3>
			<p class="text-gray-600 dark:text-slate-400 mb-6">
				This action cannot be undone.
			</p>

			<div class="flex gap-3">
				<button
					type="button"
					on:click={cancelDelete}
					disabled={deleting}
					class="flex-1 px-4 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl font-medium transition-colors dark:bg-slate-700 dark:hover:bg-slate-600 dark:text-slate-200 disabled:opacity-50"
				>
					Cancel
				</button>
				<button
					type="button"
					on:click={confirmDeletePhoto}
					disabled={deleting}
					class="flex-1 px-4 py-3 bg-red-600 hover:bg-red-700 text-white rounded-xl font-medium transition-colors disabled:opacity-50"
				>
					{deleting ? 'Deleting...' : 'Delete'}
				</button>
			</div>
		</div>
	</div>
{/if}
