<script>
	import { syncStatus, pendingCount, isOnline, syncStatusText, syncPendingEvents } from '$lib/stores/offline.js';

	// Reactive status for styling
	$: statusClass = getStatusClass($syncStatus, $isOnline);
	$: statusIcon = getStatusIcon($syncStatus, $isOnline);

	function getStatusClass(status, online) {
		if (!online) return 'bg-gray-500';
		switch (status) {
			case 'synced': return 'bg-green-500';
			case 'pending': return 'bg-yellow-500';
			case 'syncing': return 'bg-blue-500 animate-pulse';
			case 'error': return 'bg-red-500';
			default: return 'bg-gray-500';
		}
	}

	function getStatusIcon(status, online) {
		if (!online) return '📴';
		switch (status) {
			case 'synced': return '✓';
			case 'pending': return '⏳';
			case 'syncing': return '🔄';
			case 'error': return '⚠';
			default: return '○';
		}
	}

	function handleClick() {
		if ($isOnline && ($syncStatus === 'pending' || $syncStatus === 'error')) {
			syncPendingEvents();
		}
	}
</script>

<button
	type="button"
	class="flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium text-white transition-all {statusClass}"
	class:cursor-pointer={$isOnline && ($syncStatus === 'pending' || $syncStatus === 'error')}
	class:cursor-default={!$isOnline || $syncStatus === 'synced' || $syncStatus === 'syncing'}
	onclick={handleClick}
	title={$isOnline && ($syncStatus === 'pending' || $syncStatus === 'error') ? 'Click to sync now' : ''}
>
	<span class="text-sm">{statusIcon}</span>
	<span>{$syncStatusText}</span>
	{#if $pendingCount > 0 && $syncStatus !== 'syncing'}
		<span class="bg-white/20 px-1.5 py-0.5 rounded-full text-[10px]">{$pendingCount}</span>
	{/if}
</button>

<style>
	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.7; }
	}
	.animate-pulse {
		animation: pulse 1.5s ease-in-out infinite;
	}
</style>
