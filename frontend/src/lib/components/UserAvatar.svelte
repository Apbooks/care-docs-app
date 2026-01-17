<script>
	export let user = null;
	export let size = 40;

	const defaultInitials = (value) => {
		if (!value) return '?';
		const parts = value.trim().split(/\s+/);
		const initials = parts.slice(0, 2).map((part) => part[0]).join('');
		return initials.toUpperCase();
	};
</script>

<div
	class="rounded-full overflow-hidden bg-slate-200 text-slate-700 flex items-center justify-center font-semibold"
	style={`width: ${size}px; height: ${size}px;`}
>
	{#if user?.avatar_url}
		<img src={user.avatar_url} alt="User avatar" class="w-full h-full object-cover" />
	{:else}
		<span class="text-sm">{defaultInitials(user?.display_name || user?.username)}</span>
	{/if}
</div>
