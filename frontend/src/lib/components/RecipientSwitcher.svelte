<script>
	import { recipients, selectedRecipientId, setSelectedRecipient } from '$lib/stores/recipients';

	export let label = 'Recipient';

	function handleSelect(id) {
		setSelectedRecipient(id);
	}
</script>

{#if $recipients.length > 0}
	<div class="flex flex-col gap-2">
		<span class="text-sm font-medium text-slate-600 dark:text-slate-300">{label}</span>
		<div class="flex gap-2 overflow-x-auto pb-1">
			{#each $recipients as recipient}
				<button
					type="button"
					on:click={() => handleSelect(recipient.id)}
					class={`px-3 py-2 rounded-xl border text-sm font-semibold whitespace-nowrap ${
						$selectedRecipientId === recipient.id
							? 'bg-blue-600 text-white border-blue-600'
							: 'border-slate-200 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800'
					}`}
				>
					{recipient.name}
				</button>
			{/each}
		</div>
	</div>
{:else}
	<p class="text-sm text-slate-500 dark:text-slate-400">No care recipients configured yet.</p>
{/if}
