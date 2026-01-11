<script>
	import { theme, toggleTheme } from '$lib/stores/theme';
</script>

<button
	type="button"
	on:click={toggleTheme}
	class="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-gray-200 text-sm font-semibold text-gray-700 hover:bg-gray-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
	aria-label="Toggle dark mode"
>
	{#if $theme === 'dark'}
		<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
			<path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4.22 2.22a1 1 0 011.42 0l.7.7a1 1 0 01-1.42 1.42l-.7-.7a1 1 0 010-1.42zM17 9a1 1 0 110 2h-1a1 1 0 110-2h1zM5 10a5 5 0 118 4.9 1 1 0 11-1-1.73A3 3 0 1010 7a1 1 0 110-2 5 5 0 01-5 5zm-1-8a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm-2.34 3.64a1 1 0 010 1.42l-.7.7A1 1 0 012.54 6.34l.7-.7a1 1 0 011.42 0zM4 10a1 1 0 110 2H3a1 1 0 110-2h1zm1.36 5.36a1 1 0 010 1.42l-.7.7a1 1 0 11-1.42-1.42l.7-.7a1 1 0 011.42 0zM10 16a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zm6.36-1.64a1 1 0 010 1.42l-.7.7a1 1 0 01-1.42-1.42l.7-.7a1 1 0 011.42 0z" />
		</svg>
		<span>Light</span>
	{:else}
		<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
			<path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
		</svg>
		<span>Dark</span>
	{/if}
</button>
