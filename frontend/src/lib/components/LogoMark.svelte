<script>
	export let size = 48;
	export let showLabel = true;
	export let href = null;
</script>

{#if href}
<a {href} class="flex flex-col items-center">
	<svg
		width={size}
		height={size}
		viewBox="0 0 64 64"
		fill="none"
		xmlns="http://www.w3.org/2000/svg"
		aria-label="Care Docs logo"
		role="img"
		class="drop-shadow"
	>
		<rect x="4" y="4" width="56" height="56" rx="16" class="fill-blue-600 dark:fill-blue-500" />
		<path
			d="M18 20h18c6 0 10 4 10 10v14c0 4-3 6-7 6H18c-4 0-6-2-6-6V26c0-4 2-6 6-6z"
			class="fill-white/95"
		/>
		<path d="M20 28h18M20 34h22M20 40h12" stroke="#2563eb" stroke-width="3" stroke-linecap="round" />
		<circle cx="42" cy="20" r="6" class="fill-emerald-400" />
	</svg>
	{#if showLabel}
		<span class="text-xs tracking-wide text-slate-500 dark:text-slate-300 mt-1">Care Docs</span>
	{/if}
</a>
{:else}
<div class="flex flex-col items-center">
	<svg
		width={size}
		height={size}
		viewBox="0 0 64 64"
		fill="none"
		xmlns="http://www.w3.org/2000/svg"
		aria-label="Care Docs logo"
		role="img"
		class="drop-shadow"
	>
		<rect x="4" y="4" width="56" height="56" rx="16" class="fill-blue-600 dark:fill-blue-500" />
		<path
			d="M18 20h18c6 0 10 4 10 10v14c0 4-3 6-7 6H18c-4 0-6-2-6-6V26c0-4 2-6 6-6z"
			class="fill-white/95"
		/>
		<path d="M20 28h18M20 34h22M20 40h12" stroke="#2563eb" stroke-width="3" stroke-linecap="round" />
		<circle cx="42" cy="20" r="6" class="fill-emerald-400" />
	</svg>
	{#if showLabel}
		<span class="text-xs tracking-wide text-slate-500 dark:text-slate-300 mt-1">Care Docs</span>
	{/if}
</div>
{/if}
