<script>
	import '../app.css';
	import { onMount } from 'svelte';
	import { initTheme } from '$lib/stores/theme';
	import { initSettings } from '$lib/stores/settings';
	import { refreshSession } from '$lib/services/api';
	import { initRecipients } from '$lib/stores/recipients';

	onMount(() => {
		initTheme();
		initSettings();
		initRecipients();
		refreshSession();

		const intervalId = setInterval(() => {
			refreshSession();
		}, 10 * 60 * 1000);

		const handleVisibility = () => {
			if (document.visibilityState === 'visible') {
				refreshSession();
			}
		};
		document.addEventListener('visibilitychange', handleVisibility);

		return () => {
			clearInterval(intervalId);
			document.removeEventListener('visibilitychange', handleVisibility);
		};
	});
</script>

<div class="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
	<slot />
</div>
