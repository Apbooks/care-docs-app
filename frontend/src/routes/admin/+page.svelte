<script>
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { authStore, isAdmin } from '$lib/stores/auth';
	import {
		apiRequest,
		getQuickFeedsForRecipient,
		createQuickFeed,
		updateQuickFeed,
		deleteQuickFeed,
		getMedications,
		createMedication,
		updateMedication,
		deleteMedication,
		getMedReminders,
		createMedReminder,
		updateMedReminder,
		getRecipients,
		createRecipient,
		updateRecipient,
		deleteRecipient,
		createInvite,
		listInvites,
		revokeInvite,
		getUserRecipientAccess,
		updateUserRecipientAccess,
		getVapidPublicKey,
		subscribePush,
		unsubscribePush,
		sendTestNotification,
		logout as logoutApi
	} from '$lib/services/api';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';
	import LogoMark from '$lib/components/LogoMark.svelte';
	import { getTimezone, updateTimezone, getNotificationSettings, updateNotificationSettings, updateCurrentUserProfile, uploadAvatar } from '$lib/services/api';
	import { timezone as timezoneStore, setTimezone as setTimezoneStore } from '$lib/stores/settings';
	import RecipientSwitcher from '$lib/components/RecipientSwitcher.svelte';
	import { recipients as recipientsStore, selectedRecipientId, setSelectedRecipient, CARE_CATEGORIES } from '$lib/stores/recipients';
	import UserAvatar from '$lib/components/UserAvatar.svelte';

	let user = null;
	let userIsAdmin = false;
	let menuOpen = false;
	let users = [];
	let loading = true;
	let error = '';
	let deleteConfirmUserId = null;
	let timezoneValue = 'local';
	let timezoneLoading = true;
	let timezoneError = '';
	let profileName = '';
	let profileSaving = false;
	let profileError = '';
	let avatarUploading = false;
	let adminTab = 'meds';
	const roleOptions = [
		{ value: 'admin', label: 'Admin' },
		{ value: 'caregiver', label: 'Caregiver' },
		{ value: 'read_only', label: 'Read Only' }
	];
	const adminTabs = [
		{ id: 'profile', label: 'Profile' },
		{ id: 'recipients', label: 'Recipients' },
		{ id: 'meds', label: 'Medications' },
		{ id: 'feeding', label: 'Feeding' },
		{ id: 'notifications', label: 'Notifications' },
		{ id: 'users', label: 'Users' }
	];
	let notificationsLoading = true;
	let notificationsError = '';
	let notificationsEnablePush = false;
	let notificationsEnableInApp = true;
	let notificationsDueSoonMinutes = '0';
	let notificationsOverdueMinutes = '60';
	let notificationsSnoozeMinutes = '15';
	let pushSupported = false;
	let pushPermission = 'default';
	let pushSubscriptionActive = false;
	let pushActionLoading = false;
	let pushActionError = '';
	let pushTestStatus = '';

	const timezones = [
		'local',
		'America/Chicago',
		'America/New_York',
		'America/Denver',
		'America/Los_Angeles',
		'America/Phoenix',
		'America/Anchorage',
		'Pacific/Honolulu'
	];
	let quickFeeds = [];
	let quickFeedsLoading = true;
	let quickFeedsError = '';
	let medications = [];
	let medicationsLoading = true;
	let medicationsError = '';
	let medReminders = [];
	let medRemindersLoading = true;
	let medRemindersError = '';
	let recipientsList = [];
	let recipientsLoading = true;
	let recipientsError = '';
	let newRecipientName = '';
	let newRecipientActive = true;
	let newRecipientCategories = [...CARE_CATEGORIES];
	let editRecipientId = null;
	let editRecipientName = '';
	let editRecipientActive = true;
	let editRecipientCategories = [...CARE_CATEGORIES];

	let newFeedAmount = '';
	let newFeedDuration = '';
	let newFeedFormula = '';
	let newFeedMode = 'bolus';
	let newFeedRate = '';
	let newFeedDose = '';
	let newFeedInterval = '';
	let newFeedOralNotes = '';
	let editFeedId = null;
	let editFeedAmount = '';
	let editFeedDuration = '';
	let editFeedFormula = '';
	let editFeedMode = 'bolus';
	let editFeedRate = '';
	let editFeedDose = '';
	let editFeedInterval = '';
	let editFeedOralNotes = '';
	let lastTemplateRecipientId = null;

	let newMedicationName = '';
	let newMedicationDose = '';
	let newMedicationUnit = '';
	let newMedicationRoute = '';
	let newMedicationInterval = '4';
	let newMedicationWarning = '15';
	let newMedicationNotes = '';
	let newMedicationActive = true;
	let newMedicationAutoStart = false;
	let newMedicationQuick = false;
	let editMedicationId = null;
	let editMedicationName = '';
	let editMedicationDose = '';
	let editMedicationUnit = '';
	let editMedicationRoute = '';
	let editMedicationInterval = '';
	let editMedicationWarning = '';
	let editMedicationNotes = '';
	let editMedicationActive = true;
	let editMedicationAutoStart = false;
	let editMedicationQuick = false;

	let newReminderMedicationId = '';
	let newReminderStartTime = '';
	let newReminderInterval = '';

	let inviteRole = 'caregiver';
	let inviteRecipientIds = [];
	let inviteExpiresHours = '48';
	let inviteResult = null;
	let inviteError = '';
	let inviteLoading = false;
	let pendingInvites = [];
	let pendingInvitesLoading = false;

	let accessUserId = null;
	let accessUserName = '';
	let accessUserRole = '';
	let accessRecipientIds = [];
	let accessLoading = false;
	let accessSaving = false;
	let accessError = '';

	authStore.subscribe(value => {
		user = value;
	});

	isAdmin.subscribe(value => {
		userIsAdmin = value;
	});

	$: if (user) {
		profileName = user.display_name || user.username || '';
	}

	function toggleMenu() {
		menuOpen = !menuOpen;
	}

	function closeMenu() {
		menuOpen = false;
	}

	function urlBase64ToUint8Array(base64String) {
		const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
		const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
		const rawData = atob(base64);
		const outputArray = new Uint8Array(rawData.length);
		for (let i = 0; i < rawData.length; i += 1) {
			outputArray[i] = rawData.charCodeAt(i);
		}
		return outputArray;
	}

	async function initializePushState() {
		if (typeof window === 'undefined') return;
		pushSupported = 'serviceWorker' in navigator && 'PushManager' in window;
		pushPermission = typeof Notification !== 'undefined' ? Notification.permission : 'default';
		if (!pushSupported) return;
		try {
			const registration = await navigator.serviceWorker.ready;
			const subscription = await registration.pushManager.getSubscription();
			pushSubscriptionActive = !!subscription;
		} catch (err) {
			pushActionError = err.message || 'Unable to read push subscription status';
		}
	}

	async function handleLogout() {
		try {
			await logoutApi();
			authStore.logout();
			localStorage.removeItem('access_token');
			localStorage.removeItem('refresh_token');
			goto('/login');
		} catch (err) {
			authStore.logout();
			localStorage.removeItem('access_token');
			localStorage.removeItem('refresh_token');
			goto('/login');
		}
	}

	async function handleEnableDevicePush() {
		pushActionError = '';
		pushTestStatus = '';
		pushActionLoading = true;
		try {
			if (!pushSupported) {
				throw new Error('Push notifications are not supported on this device');
			}
			if (typeof Notification === 'undefined') {
				throw new Error('Notification API not available');
			}
			const permission = await Notification.requestPermission();
			pushPermission = permission;
			if (permission !== 'granted') {
				throw new Error('Permission not granted for notifications');
			}
			const { public_key } = await getVapidPublicKey();
			if (!public_key) {
				throw new Error('Missing VAPID public key');
			}
			const registration = await navigator.serviceWorker.ready;
			const subscription = await registration.pushManager.subscribe({
				userVisibleOnly: true,
				applicationServerKey: urlBase64ToUint8Array(public_key)
			});
			await subscribePush(subscription.toJSON());
			pushSubscriptionActive = true;
		} catch (err) {
			pushActionError = err.message || 'Failed to enable push notifications';
		} finally {
			pushActionLoading = false;
		}
	}

	async function handleDisableDevicePush() {
		pushActionError = '';
		pushTestStatus = '';
		pushActionLoading = true;
		try {
			if (!pushSupported) {
				throw new Error('Push notifications are not supported on this device');
			}
			const registration = await navigator.serviceWorker.ready;
			const subscription = await registration.pushManager.getSubscription();
			if (subscription) {
				await unsubscribePush(subscription.toJSON());
				await subscription.unsubscribe();
			}
			pushSubscriptionActive = false;
		} catch (err) {
			pushActionError = err.message || 'Failed to disable push notifications';
		} finally {
			pushActionLoading = false;
		}
	}

	async function handleSendTestNotification() {
		pushActionError = '';
		pushTestStatus = '';
		pushActionLoading = true;
		try {
			await sendTestNotification({
				title: 'Care Docs Reminder',
				body: 'This is a test notification from Care Docs.'
			});
			pushTestStatus = 'Test notification sent.';
		} catch (err) {
			pushActionError = err.message || 'Failed to send test notification';
		} finally {
			pushActionLoading = false;
		}
	}

	async function handleProfileSave() {
		if (!user) return;
		profileError = '';
		profileSaving = true;
		try {
			const updated = await updateCurrentUserProfile({ display_name: profileName });
			await authStore.updateUser(updated);
		} catch (err) {
			profileError = err.message || 'Failed to update profile';
		} finally {
			profileSaving = false;
		}
	}

	async function handleAvatarChange(event) {
		const file = event?.target?.files?.[0];
		if (!file) return;
		profileError = '';
		avatarUploading = true;
		try {
			const updated = await uploadAvatar(file);
			await authStore.updateUser(updated);
		} catch (err) {
			profileError = err.message || 'Failed to upload avatar';
		} finally {
			avatarUploading = false;
		}
	}

	onMount(async () => {
		// Check admin status synchronously using get() to avoid race condition
		const auth = get(authStore);
		if (!auth || auth.role !== 'admin') {
			goto('/');
			return;
		}

		await Promise.all([
			loadUsers(),
			loadRecipients(),
			loadQuickFeeds(),
			loadMedications(),
			loadMedReminders(),
			loadTimezone(),
			loadNotificationSettings(),
			loadInvites()
		]);
		await initializePushState();
	});

	$: if ($selectedRecipientId && $selectedRecipientId !== lastTemplateRecipientId) {
		lastTemplateRecipientId = $selectedRecipientId;
		loadQuickFeeds();
		loadMedications();
		loadMedReminders();
	}

	async function loadUsers() {
		loading = true;
		error = '';

		try {
			users = await apiRequest('/auth/users');
		} catch (err) {
			error = err.message || 'Failed to load users';
		} finally {
			loading = false;
		}
	}

	async function loadInvites() {
		pendingInvitesLoading = true;
		try {
			pendingInvites = await listInvites();
		} catch (err) {
			inviteError = err.message || 'Failed to load invites';
		} finally {
			pendingInvitesLoading = false;
		}
	}

	async function loadTimezone() {
		timezoneLoading = true;
		timezoneError = '';

		try {
			const response = await getTimezone();
			timezoneValue = response?.timezone || 'local';
			setTimezoneStore(timezoneValue);
		} catch (err) {
			timezoneError = err.message || 'Failed to load timezone';
		} finally {
			timezoneLoading = false;
		}
	}

	async function loadNotificationSettings() {
		notificationsLoading = true;
		notificationsError = '';

		try {
			const response = await getNotificationSettings();
			notificationsEnablePush = !!response?.enable_push;
			notificationsEnableInApp = response?.enable_in_app !== false;
			notificationsDueSoonMinutes = (response?.due_soon_minutes ?? 0).toString();
			notificationsOverdueMinutes = (response?.overdue_repeat_minutes ?? 60).toString();
			notificationsSnoozeMinutes = (response?.snooze_minutes_default ?? 15).toString();
		} catch (err) {
			notificationsError = err.message || 'Failed to load notification settings';
		} finally {
			notificationsLoading = false;
		}
	}

	async function handleSaveNotificationSettings() {
		notificationsError = '';

		try {
			await updateNotificationSettings({
				enable_push: notificationsEnablePush,
				enable_in_app: notificationsEnableInApp,
				due_soon_minutes: parseInt(notificationsDueSoonMinutes || '0'),
				overdue_repeat_minutes: parseInt(notificationsOverdueMinutes || '60'),
				snooze_minutes_default: parseInt(notificationsSnoozeMinutes || '15')
			});
		} catch (err) {
			notificationsError = err.message || 'Failed to save notification settings';
		}
	}

	async function handleTimezoneSave() {
		timezoneError = '';

		try {
			const response = await updateTimezone(timezoneValue);
			setTimezoneStore(response?.timezone || timezoneValue);
		} catch (err) {
			timezoneError = err.message || 'Failed to update timezone';
		}
	}

	function syncRecipientStore() {
		const activeRecipients = recipientsList.filter((recipient) => recipient.is_active);
		recipientsStore.set(activeRecipients);
		if (!$selectedRecipientId && activeRecipients.length > 0) {
			setSelectedRecipient(activeRecipients[0].id);
		}
	}

	async function loadRecipients() {
		recipientsLoading = true;
		recipientsError = '';

		try {
			recipientsList = await getRecipients(true);
			syncRecipientStore();
		} catch (err) {
			recipientsError = err.message || 'Failed to load recipients';
		} finally {
			recipientsLoading = false;
		}
	}

	async function handleCreateRecipient() {
		recipientsError = '';

		try {
			const created = await createRecipient({
				name: newRecipientName,
				is_active: newRecipientActive,
				enabled_categories: newRecipientCategories
			});
			recipientsList = [...recipientsList, created];
			newRecipientName = '';
			newRecipientActive = true;
			newRecipientCategories = [...CARE_CATEGORIES];
			syncRecipientStore();
		} catch (err) {
			recipientsError = err.message || 'Failed to create recipient';
		}
	}

	function startEditRecipient(recipient) {
		editRecipientId = recipient.id;
		editRecipientName = recipient.name;
		editRecipientActive = recipient.is_active;
		editRecipientCategories = recipient.enabled_categories || [...CARE_CATEGORIES];
	}

	function cancelEditRecipient() {
		editRecipientId = null;
		editRecipientName = '';
		editRecipientActive = true;
		editRecipientCategories = [...CARE_CATEGORIES];
	}

	async function handleSaveRecipient() {
		recipientsError = '';

		try {
			const updated = await updateRecipient(editRecipientId, {
				name: editRecipientName,
				is_active: editRecipientActive,
				enabled_categories: editRecipientCategories
			});
			recipientsList = recipientsList.map((item) => (item.id === updated.id ? updated : item));
			syncRecipientStore();
			cancelEditRecipient();
		} catch (err) {
			recipientsError = err.message || 'Failed to update recipient';
		}
	}

	async function handleDeleteRecipient(recipientId) {
		recipientsError = '';

		try {
			await deleteRecipient(recipientId);
			recipientsList = recipientsList.filter((item) => item.id !== recipientId);
			syncRecipientStore();
			if ($selectedRecipientId === recipientId) {
				const activeRecipients = recipientsList.filter((recipient) => recipient.is_active);
				setSelectedRecipient(activeRecipients[0]?.id || null);
			}
		} catch (err) {
			recipientsError = err.message || 'Failed to delete recipient';
		}
	}

	async function loadQuickFeeds() {
		quickFeedsLoading = true;
		quickFeedsError = '';

		try {
			if (!$selectedRecipientId) {
				quickFeeds = [];
				return;
			}
			quickFeeds = await getQuickFeedsForRecipient($selectedRecipientId, true);
		} catch (err) {
			quickFeedsError = err.message || 'Failed to load quick feeds';
		} finally {
			quickFeedsLoading = false;
		}
	}

	async function loadMedications() {
		medicationsLoading = true;
		medicationsError = '';

		try {
			const params = $selectedRecipientId ? { recipient_id: $selectedRecipientId, include_inactive: true } : { include_inactive: true };
			medications = await getMedications(params);
		} catch (err) {
			medicationsError = err.message || 'Failed to load medications';
		} finally {
			medicationsLoading = false;
		}
	}

	async function loadMedReminders() {
		medRemindersLoading = true;
		medRemindersError = '';

		try {
			if (!$selectedRecipientId) {
				medReminders = [];
				return;
			}
			medReminders = await getMedReminders({ recipient_id: $selectedRecipientId, include_disabled: true });
		} catch (err) {
			medRemindersError = err.message || 'Failed to load reminders';
		} finally {
			medRemindersLoading = false;
		}
	}

	async function handleCreateMedication() {
		medicationsError = '';

		try {
			const created = await createMedication({
				name: newMedicationName,
				default_dose: newMedicationDose || null,
				dose_unit: newMedicationUnit || null,
				default_route: newMedicationRoute || null,
				interval_hours: parseInt(newMedicationInterval || '4'),
				early_warning_minutes: parseInt(newMedicationWarning || '15'),
				notes: newMedicationNotes || null,
				is_active: newMedicationActive,
				auto_start_reminder: newMedicationAutoStart,
				is_quick_med: newMedicationQuick,
				recipient_id: $selectedRecipientId || null
			});
			medications = [created, ...medications];
			newMedicationName = '';
			newMedicationDose = '';
			newMedicationUnit = '';
			newMedicationRoute = '';
			newMedicationInterval = '4';
			newMedicationWarning = '15';
			newMedicationNotes = '';
			newMedicationActive = true;
			newMedicationAutoStart = false;
			newMedicationQuick = false;
		} catch (err) {
			medicationsError = err.message || 'Failed to create medication';
		}
	}

	function startEditMedication(med) {
		editMedicationId = med.id;
		editMedicationName = med.name;
		editMedicationDose = med.default_dose || '';
		editMedicationUnit = med.dose_unit || '';
		editMedicationRoute = med.default_route || '';
		editMedicationInterval = med.interval_hours?.toString() || '';
		editMedicationWarning = med.early_warning_minutes?.toString() || '';
		editMedicationNotes = med.notes || '';
		editMedicationActive = med.is_active;
		editMedicationAutoStart = med.auto_start_reminder || false;
		editMedicationQuick = med.is_quick_med || false;
	}

	function cancelEditMedication() {
		editMedicationId = null;
		editMedicationName = '';
		editMedicationDose = '';
		editMedicationUnit = '';
		editMedicationRoute = '';
		editMedicationInterval = '';
		editMedicationWarning = '';
		editMedicationNotes = '';
		editMedicationActive = true;
		editMedicationAutoStart = false;
		editMedicationQuick = false;
	}

	async function handleSaveMedication() {
		medicationsError = '';

		try {
			const updated = await updateMedication(editMedicationId, {
				name: editMedicationName,
				default_dose: editMedicationDose || null,
				dose_unit: editMedicationUnit || null,
				default_route: editMedicationRoute || null,
				interval_hours: editMedicationInterval ? parseInt(editMedicationInterval) : null,
				early_warning_minutes: editMedicationWarning ? parseInt(editMedicationWarning) : null,
				notes: editMedicationNotes || null,
				is_active: editMedicationActive,
				auto_start_reminder: editMedicationAutoStart,
				is_quick_med: editMedicationQuick,
				recipient_id: $selectedRecipientId || null
			});
			medications = medications.map(item => item.id === updated.id ? updated : item);
			cancelEditMedication();
		} catch (err) {
			medicationsError = err.message || 'Failed to update medication';
		}
	}

	async function handleDeleteMedication(medId) {
		medicationsError = '';

		try {
			await deleteMedication(medId);
			medications = medications.filter(item => item.id !== medId);
		} catch (err) {
			medicationsError = err.message || 'Failed to delete medication';
		}
	}

	async function handleCreateReminder() {
		medRemindersError = '';

		try {
			const created = await createMedReminder({
				recipient_id: $selectedRecipientId,
				medication_id: newReminderMedicationId,
				start_time: newReminderStartTime ? new Date(newReminderStartTime).toISOString() : null,
				interval_hours: newReminderInterval ? parseInt(newReminderInterval) : null,
				enabled: true
			});
			medReminders = [created, ...medReminders];
			newReminderMedicationId = '';
			newReminderStartTime = '';
			newReminderInterval = '';
		} catch (err) {
			medRemindersError = err.message || 'Failed to create reminder';
		}
	}

	async function handleToggleReminder(reminder) {
		medRemindersError = '';

		try {
			const updated = await updateMedReminder(reminder.id, { enabled: !reminder.enabled });
			medReminders = medReminders.map(item => item.id === updated.id ? updated : item);
		} catch (err) {
			medRemindersError = err.message || 'Failed to update reminder';
		}
	}

	async function handleCreateQuickFeed() {
		quickFeedsError = '';

		try {
			const created = await createQuickFeed({
				mode: newFeedMode,
				amount_ml: newFeedAmount ? parseInt(newFeedAmount) : null,
				duration_min: newFeedDuration ? parseInt(newFeedDuration) : null,
				formula_type: newFeedFormula || null,
				rate_ml_hr: newFeedRate ? parseFloat(newFeedRate) : null,
				dose_ml: newFeedDose ? parseFloat(newFeedDose) : null,
				interval_hr: newFeedInterval ? parseFloat(newFeedInterval) : null,
				oral_notes: newFeedOralNotes || null,
				recipient_id: $selectedRecipientId
			});
			quickFeeds = [created, ...quickFeeds];
			newFeedAmount = '';
			newFeedDuration = '';
			newFeedFormula = '';
			newFeedMode = 'bolus';
			newFeedRate = '';
			newFeedDose = '';
			newFeedInterval = '';
			newFeedOralNotes = '';
		} catch (err) {
			quickFeedsError = err.message || 'Failed to create quick feed';
		}
	}

	async function handleToggleQuickFeed(feed) {
		quickFeedsError = '';

		try {
			const updated = await updateQuickFeed(feed.id, { is_active: !feed.is_active });
			quickFeeds = quickFeeds.map(item => item.id === feed.id ? updated : item);
		} catch (err) {
			quickFeedsError = err.message || 'Failed to update quick feed';
		}
	}

	async function handleDeleteQuickFeed(feedId) {
		quickFeedsError = '';

		try {
			await deleteQuickFeed(feedId);
			quickFeeds = quickFeeds.filter(item => item.id !== feedId);
		} catch (err) {
			quickFeedsError = err.message || 'Failed to delete quick feed';
		}
	}

	function startEditQuickFeed(feed) {
		editFeedId = feed.id;
		editFeedAmount = feed.amount_ml ?? '';
		editFeedDuration = feed.duration_min ?? '';
		editFeedFormula = feed.formula_type ?? '';
		editFeedMode = feed.mode || 'bolus';
		editFeedRate = feed.rate_ml_hr ?? '';
		editFeedDose = feed.dose_ml ?? '';
		editFeedInterval = feed.interval_hr ?? '';
		editFeedOralNotes = feed.oral_notes ?? '';
	}

	function cancelEditQuickFeed() {
		editFeedId = null;
		editFeedAmount = '';
		editFeedDuration = '';
		editFeedFormula = '';
		editFeedMode = 'bolus';
		editFeedRate = '';
		editFeedDose = '';
		editFeedInterval = '';
		editFeedOralNotes = '';
	}

	async function handleSaveQuickFeed() {
		quickFeedsError = '';

		try {
			const updated = await updateQuickFeed(editFeedId, {
				mode: editFeedMode,
				amount_ml: editFeedAmount === '' ? null : parseInt(editFeedAmount),
				duration_min: editFeedDuration === '' ? null : parseInt(editFeedDuration),
				formula_type: editFeedFormula || null,
				rate_ml_hr: editFeedRate === '' ? null : parseFloat(editFeedRate),
				dose_ml: editFeedDose === '' ? null : parseFloat(editFeedDose),
				interval_hr: editFeedInterval === '' ? null : parseFloat(editFeedInterval),
				oral_notes: editFeedOralNotes || null
			});
			quickFeeds = quickFeeds.map(item => item.id === updated.id ? updated : item);
			cancelEditQuickFeed();
		} catch (err) {
			quickFeedsError = err.message || 'Failed to update quick feed';
		}
	}

	async function handleCreateInvite() {
		inviteError = '';
		inviteResult = null;

		inviteLoading = true;
		try {
			const result = await createInvite({
				role: inviteRole,
				recipient_ids: inviteRecipientIds,
				expires_in_hours: parseInt(inviteExpiresHours || '48', 10)
			});
			inviteResult = result;
			await loadInvites();
		} catch (err) {
			inviteError = err.message || 'Failed to create invite';
		} finally {
			inviteLoading = false;
		}
	}

	async function handleCopyInvite(url) {
		const inviteUrl = url || inviteResult?.invite_url;
		if (!inviteUrl || typeof navigator === 'undefined') return;
		try {
			await navigator.clipboard.writeText(inviteUrl);
		} catch (err) {
			inviteError = 'Failed to copy invite link';
		}
	}

	async function handleRevokeInvite(token) {
		inviteError = '';
		try {
			await revokeInvite(token);
			pendingInvites = pendingInvites.filter((invite) => invite.token !== token);
		} catch (err) {
			inviteError = err.message || 'Failed to revoke invite';
		}
	}

	async function openAccessEditor(userItem) {
		accessUserId = userItem.id;
		accessUserName = userItem.username;
		accessUserRole = userItem.role;
		accessRecipientIds = [];
		accessError = '';
		accessLoading = true;

		try {
			const response = await getUserRecipientAccess(userItem.id);
			accessRecipientIds = response?.recipient_ids || [];
		} catch (err) {
			accessError = err.message || 'Failed to load recipient access';
		} finally {
			accessLoading = false;
		}
	}

	function closeAccessEditor() {
		accessUserId = null;
		accessUserName = '';
		accessUserRole = '';
		accessRecipientIds = [];
		accessError = '';
		accessLoading = false;
		accessSaving = false;
	}

	async function handleSaveAccess() {
		if (!accessUserId) return;
		accessError = '';
		accessSaving = true;

		try {
			const response = await updateUserRecipientAccess(accessUserId, accessRecipientIds);
			accessRecipientIds = response?.recipient_ids || [];
		} catch (err) {
			accessError = err.message || 'Failed to update recipient access';
		} finally {
			accessSaving = false;
		}
	}

	async function handleRoleChange(userId, role) {
		error = '';
		try {
			const updatedUser = await apiRequest(`/auth/users/${userId}`, {
				method: 'PATCH',
				body: JSON.stringify({ role })
			});
			users = users.map(u => u.id === userId ? updatedUser : u);
			if (accessUserId === userId) {
				accessUserRole = updatedUser.role;
			}
		} catch (err) {
			error = err.message || 'Failed to update user role';
		}
	}

	async function handleDeleteUser(userId) {
		// Don't allow deleting yourself
		if (userId === user.id) {
			error = 'You cannot delete your own account';
			return;
		}

		try {
			await apiRequest(`/auth/users/${userId}`, {
				method: 'DELETE'
			});

			// Remove from list
			users = users.filter(u => u.id !== userId);
			deleteConfirmUserId = null;
		} catch (err) {
			error = err.message || 'Failed to delete user';
		}
	}

	async function handleToggleActive(userId, currentStatus) {
		// Don't allow deactivating yourself
		if (userId === user.id && currentStatus) {
			error = 'You cannot deactivate your own account';
			return;
		}

		try {
			const updatedUser = await apiRequest(`/auth/users/${userId}`, {
				method: 'PATCH',
				body: JSON.stringify({ is_active: !currentStatus })
			});

			// Update in list
			users = users.map(u => u.id === userId ? updatedUser : u);
		} catch (err) {
			error = err.message || 'Failed to update user';
		}
	}

	function getRoleBadgeColor(role) {
		if (role === 'admin') return 'bg-purple-100 text-purple-800';
		if (role === 'read_only') return 'bg-slate-200 text-slate-700';
		return 'bg-blue-100 text-blue-800';
	}

	function formatDate(dateString) {
		return new Date(dateString).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}
</script>

<svelte:head>
	<title>Admin Panel - Care Documentation</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-slate-950">
	<!-- Header -->
	<header class="bg-white dark:bg-slate-900 shadow sticky top-0 z-30">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
			<div class="flex items-center justify-between">
					<button
						on:click={toggleMenu}
						class="rounded-full border border-slate-200 p-1 hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
						aria-label="Open menu"
					>
						<UserAvatar user={user} size={40} />
					</button>

				<LogoMark size={48} showLabel={true} href="/" />

				<div class="flex items-center">
					<ThemeToggle />
				</div>
			</div>
		</div>
	</header>

	{#if menuOpen}
		<button
			type="button"
			class="fixed inset-0 z-40 bg-black/40"
			on:click={closeMenu}
			aria-label="Close menu"
		></button>
		<div class="fixed top-0 left-0 z-50 h-full w-64 bg-white dark:bg-slate-900 shadow-xl p-5">
			<div class="flex items-center justify-between mb-6">
				<div>
					<p class="text-sm text-slate-500 dark:text-slate-400">Signed in as</p>
					<p class="text-base font-semibold text-slate-900 dark:text-slate-100">{user?.username || 'User'}</p>
				</div>
				<button
					on:click={closeMenu}
					class="w-10 h-10 flex items-center justify-center rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
					aria-label="Close menu"
				>
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>

			<div class="space-y-1">
				<button
					on:click={() => { closeMenu(); goto('/'); }}
					class="w-full text-left px-2 py-3 text-base text-slate-700 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800 rounded-lg"
				>
					Dashboard
				</button>
				<button
					on:click={() => { closeMenu(); goto('/history'); }}
					class="w-full text-left px-2 py-3 text-base text-slate-700 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800 rounded-lg"
				>
					History
				</button>
				{#if userIsAdmin}
					<button
						on:click={() => { closeMenu(); goto('/admin'); }}
						class="w-full text-left px-2 py-3 text-base text-slate-700 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800 rounded-lg"
					>
						Admin Panel
					</button>
				{/if}
				<button
					on:click={() => { closeMenu(); handleLogout(); }}
					class="w-full text-left px-2 py-3 text-base text-red-600 hover:bg-red-50 dark:text-red-200 dark:hover:bg-red-950 rounded-lg"
				>
					Logout
				</button>
			</div>
		</div>
	{/if}

	<!-- Main Content -->
	<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Page Title -->
		<div class="mb-6">
			<h1 class="text-2xl font-bold text-gray-900 dark:text-slate-100">Admin Panel</h1>
			<p class="text-base text-gray-600 dark:text-slate-300 mt-1">Manage users and system settings</p>
		</div>

		<div class="mb-6 flex flex-wrap gap-2">
			{#each adminTabs as tab}
				<button
					type="button"
					on:click={() => adminTab = tab.id}
					class={`px-4 py-2 rounded-xl text-sm font-semibold border ${adminTab === tab.id ? 'bg-blue-600 text-white border-blue-600' : 'border-slate-200 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800'}`}
				>
					{tab.label}
				</button>
			{/each}
		</div>

	{#if adminTab === 'profile'}
		<div class="bg-white dark:bg-slate-900 rounded-xl shadow p-6">
			<h2 class="text-xl font-semibold text-gray-900 dark:text-slate-100 mb-2">Profile Settings</h2>
			<p class="text-sm text-gray-600 dark:text-slate-300 mb-4">Update your name, avatar, and theme.</p>
			{#if profileError}
				<div class="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl dark:bg-red-950 dark:border-red-900">
					<p class="text-red-800 dark:text-red-200 text-sm">{profileError}</p>
				</div>
			{/if}
			<div class="grid gap-4 sm:grid-cols-2">
				<div>
					<label for="profile-display-name" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Display Name</label>
					<input
						id="profile-display-name"
						type="text"
						bind:value={profileName}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
						placeholder="Your name"
					/>
				</div>
				<div>
					<label for="profile-avatar" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Avatar</label>
					<input
						id="profile-avatar"
						type="file"
						accept="image/*"
						on:change={handleAvatarChange}
						class="w-full text-sm text-gray-700 dark:text-slate-300"
					/>
					{#if avatarUploading}
						<p class="text-xs text-gray-500 mt-2">Uploading...</p>
					{/if}
				</div>
				<div>
					<p class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Theme</p>
					<ThemeToggle />
				</div>
			</div>
			<div class="mt-4">
				<button
					type="button"
					on:click={handleProfileSave}
					disabled={profileSaving}
					class="px-4 py-3 bg-blue-600 text-white rounded-xl text-base hover:bg-blue-700 disabled:bg-blue-400"
				>
					{profileSaving ? 'Saving...' : 'Save Profile'}
				</button>
			</div>
		</div>
	{/if}

	{#if adminTab === 'users'}
		{#if error}
			<div class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl dark:bg-red-950 dark:border-red-900">
				<p class="text-red-800 dark:text-red-200 text-base">{error}</p>
			</div>
		{/if}

		<div class="grid gap-6">
			<!-- Invite User -->
			<div class="bg-white dark:bg-slate-900 rounded-xl shadow">
				<div class="p-6 border-b border-gray-200 dark:border-slate-800">
					<h2 class="text-xl font-semibold text-gray-900 dark:text-slate-100">Invite User</h2>
					<p class="text-base text-gray-600 dark:text-slate-300 mt-1">Invite link lets the user set their username, email, name, and password.</p>
				</div>
				<div class="p-6 space-y-4">
					{#if inviteError}
						<div class="p-4 bg-red-50 border border-red-200 rounded-xl dark:bg-red-950 dark:border-red-900">
							<p class="text-red-800 dark:text-red-200 text-base">{inviteError}</p>
						</div>
					{/if}
					<form class="grid gap-4 sm:grid-cols-2" on:submit|preventDefault={handleCreateInvite}>
						<div>
							<label for="invite-role" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Role</label>
							<select
								id="invite-role"
								bind:value={inviteRole}
								class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							>
								{#each roleOptions as option}
									<option value={option.value}>{option.label}</option>
								{/each}
							</select>
						</div>
						<div>
							<label for="invite-expires" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Invite expires (hours)</label>
							<input
								id="invite-expires"
								type="number"
								min="1"
								max="720"
								bind:value={inviteExpiresHours}
								class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							/>
						</div>
						<div class="sm:col-span-2">
							<p class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Recipient access</p>
							{#if recipientsList.length === 0}
								<p class="text-sm text-slate-500 dark:text-slate-400">Create recipients first to assign access.</p>
							{:else}
								<div class="flex flex-wrap items-center gap-3 text-sm text-gray-700 dark:text-slate-300">
									{#each recipientsList as recipient}
										<label class="flex items-center gap-2">
											<input
												type="checkbox"
												checked={inviteRecipientIds.includes(recipient.id)}
												on:change={(event) => {
													if (event.target.checked) {
														inviteRecipientIds = [...inviteRecipientIds, recipient.id];
													} else {
														inviteRecipientIds = inviteRecipientIds.filter((item) => item !== recipient.id);
													}
												}}
												class="w-4 h-4 text-blue-600 border-gray-300 rounded"
											/>
											<span>{recipient.name}</span>
										</label>
									{/each}
								</div>
							{/if}
						</div>
						<div class="sm:col-span-2">
							<button
								type="submit"
								disabled={inviteLoading}
								class="px-4 py-3 bg-blue-600 text-white rounded-xl text-base hover:bg-blue-700 disabled:bg-blue-300"
							>
								{inviteLoading ? 'Creating...' : 'Create Invite Link'}
							</button>
						</div>
					</form>

					{#if inviteResult}
						<div class="rounded-xl border border-slate-200 dark:border-slate-800 p-4">
							<p class="text-sm text-slate-600 dark:text-slate-300 mb-2">Invite link</p>
							<div class="flex flex-col gap-3 sm:flex-row sm:items-center">
								<input
									type="text"
									readonly
									value={inviteResult.invite_url}
									class="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm"
								/>
								<button
									type="button"
									on:click={handleCopyInvite}
									class="px-3 py-2 border border-slate-200 rounded-lg text-sm font-semibold"
								>
									Copy Link
								</button>
							</div>
							<p class="text-xs text-slate-500 dark:text-slate-400 mt-2">Expires: {new Date(inviteResult.expires_at).toLocaleString()}</p>
						</div>
					{/if}

					<div class="rounded-xl border border-slate-200 dark:border-slate-800 p-4">
						<p class="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-2">Pending Invites</p>
						{#if pendingInvitesLoading}
							<p class="text-sm text-slate-500 dark:text-slate-400">Loading invites...</p>
						{:else if pendingInvites.length === 0}
							<p class="text-sm text-slate-500 dark:text-slate-400">No pending invites.</p>
						{:else}
							<div class="space-y-3">
								{#each pendingInvites as invite}
									<div class="border border-slate-200 dark:border-slate-800 rounded-lg p-3">
										<div class="flex flex-wrap items-center justify-between gap-2">
											<div>
												<p class="text-sm font-semibold text-slate-900 dark:text-slate-100">Role: {invite.role}</p>
												<p class="text-xs text-slate-500 dark:text-slate-400">Recipients: {(invite.recipient_names || []).join(', ') || 'None selected'}</p>
												<p class="text-xs text-slate-500 dark:text-slate-400">Expires: {new Date(invite.expires_at).toLocaleString()}</p>
											</div>
											<div class="flex items-center gap-2">
												<button
													type="button"
													on:click={() => handleCopyInvite(invite.invite_url)}
													class="px-3 py-2 border border-slate-200 rounded-lg text-xs font-semibold"
												>
													Copy Link
												</button>
												<button
													type="button"
													on:click={() => handleRevokeInvite(invite.token)}
													class="px-3 py-2 border border-red-200 text-red-600 rounded-lg text-xs font-semibold"
												>
													Revoke
												</button>
											</div>
										</div>
									</div>
								{/each}
							</div>
						{/if}
					</div>
				</div>
			</div>

			<!-- User Management Section -->
			<div class="bg-white dark:bg-slate-900 rounded-xl shadow">
				<div class="p-6 border-b border-gray-200 dark:border-slate-800">
					<div class="flex justify-between items-center">
						<div>
							<h2 class="text-xl font-semibold text-gray-900 dark:text-slate-100">User Management</h2>
							<p class="text-base text-gray-600 dark:text-slate-300 mt-1">View and manage user accounts</p>
						</div>
						<button
							on:click={() => goto('/register')}
							class="px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 text-base"
						>
							Add New User
						</button>
					</div>
				</div>

				<div class="p-6">
				{#if loading}
					<div class="text-center py-8">
						<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
						<p class="mt-2 text-gray-600 dark:text-slate-300">Loading users...</p>
					</div>
				{:else if users.length === 0}
					<div class="text-center py-8">
						<p class="text-gray-600 dark:text-slate-300 text-base">No users found</p>
					</div>
				{:else}
				<div class="space-y-4 sm:hidden">
					{#each users as u (u.id)}
						<div class="border border-gray-200 dark:border-slate-800 rounded-xl p-4">
							<div class="flex items-center gap-3">
								<div class="flex-shrink-0 h-12 w-12 bg-gray-200 dark:bg-slate-800 rounded-full flex items-center justify-center">
									<span class="text-gray-600 font-semibold text-lg">
										{u.username.charAt(0).toUpperCase()}
									</span>
								</div>
								<div class="flex-1">
									<div class="text-base font-semibold text-gray-900 dark:text-slate-100">{u.username}</div>
									<div class="text-sm text-gray-500 dark:text-slate-400">{u.email}</div>
								</div>
								<span class={`px-2 py-1 text-xs font-semibold rounded-full ${getRoleBadgeColor(u.role)}`}>
									{u.role}
								</span>
							</div>
							<div class="mt-3 grid gap-2">
								<label for={`user-role-${u.id}`} class="text-xs font-semibold text-slate-500 dark:text-slate-400">Role</label>
								<select
									id={`user-role-${u.id}`}
									class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
									value={u.role}
									on:change={(event) => handleRoleChange(u.id, event.target.value)}
								>
									{#each roleOptions as option}
										<option value={option.value}>{option.label}</option>
									{/each}
								</select>
								<button
									type="button"
									on:click={() => openAccessEditor(u)}
									class="px-3 py-2 border border-slate-200 rounded-lg text-sm font-semibold"
								>
									Manage Access
								</button>
							</div>
							<div class="mt-3 flex flex-wrap items-center gap-3">
								<button
									on:click={() => handleToggleActive(u.id, u.is_active)}
									class={`px-3 py-2 text-xs font-semibold rounded-full ${u.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
									disabled={u.id === user?.id && u.is_active}
								>
									{u.is_active ? 'Active' : 'Inactive'}
								</button>
								<span class="text-xs text-gray-500 dark:text-slate-400">Created {formatDate(u.created_at)}</span>
							</div>
							<div class="mt-3">
								{#if deleteConfirmUserId === u.id}
									<div class="flex items-center gap-3">
										<span class="text-sm text-gray-600 dark:text-slate-300">Confirm delete?</span>
										<button
											type="button"
											on:click={() => handleDeleteUser(u.id)}
											class="text-red-600 font-semibold"
										>
											Yes
										</button>
										<button
											type="button"
											on:click={() => deleteConfirmUserId = null}
											class="text-gray-600 font-semibold"
										>
											No
										</button>
									</div>
								{:else}
										<button
											type="button"
											on:click={() => deleteConfirmUserId = u.id}
											disabled={u.id === user?.id}
											class="text-red-600 font-semibold disabled:text-gray-400 disabled:cursor-not-allowed"
										>
											Delete User
										</button>
								{/if}
							</div>
						</div>
					{/each}
				</div>
				<div class="hidden sm:block overflow-x-auto">
					<table class="min-w-full divide-y divide-gray-200 dark:divide-slate-800">
						<thead class="bg-gray-50 dark:bg-slate-800">
							<tr>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									User
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Role
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Status
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									Created
								</th>
								<th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
									Actions
								</th>
							</tr>
						</thead>
						<tbody class="bg-white dark:bg-slate-900 divide-y divide-gray-200 dark:divide-slate-800">
							{#each users as u (u.id)}
								<tr class="hover:bg-gray-50 dark:hover:bg-slate-800">
									<td class="px-6 py-4 whitespace-nowrap">
										<div class="flex items-center">
											<div class="flex-shrink-0 h-10 w-10 bg-gray-200 dark:bg-slate-800 rounded-full flex items-center justify-center">
												<span class="text-gray-600 dark:text-slate-300 font-medium">
													{u.username.charAt(0).toUpperCase()}
												</span>
											</div>
											<div class="ml-4">
												<div class="text-sm font-medium text-gray-900 dark:text-slate-100">{u.username}</div>
												<div class="text-sm text-gray-500 dark:text-slate-400">{u.email}</div>
											</div>
										</div>
									</td>
									<td class="px-6 py-4 whitespace-nowrap">
										<select
											class="px-2 py-1 border border-slate-200 rounded-lg text-xs"
											value={u.role}
											on:change={(event) => handleRoleChange(u.id, event.target.value)}
										>
											{#each roleOptions as option}
												<option value={option.value}>{option.label}</option>
											{/each}
										</select>
									</td>
									<td class="px-6 py-4 whitespace-nowrap">
										<button
											on:click={() => handleToggleActive(u.id, u.is_active)}
											class={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full cursor-pointer ${u.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
											disabled={u.id === user?.id && u.is_active}
										>
											{u.is_active ? 'Active' : 'Inactive'}
										</button>
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-slate-400">
										{formatDate(u.created_at)}
									</td>
									<td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
										{#if deleteConfirmUserId === u.id}
											<div class="flex items-center justify-end gap-2">
												<span class="text-gray-600 text-xs">Confirm delete?</span>
												<button
													type="button"
													on:click={() => handleDeleteUser(u.id)}
													class="text-red-600 hover:text-red-900"
												>
													Yes
												</button>
												<button
													type="button"
													on:click={() => deleteConfirmUserId = null}
													class="text-gray-600 hover:text-gray-900"
												>
													No
												</button>
											</div>
										{:else}
											<div class="flex items-center justify-end gap-3">
												<button
													type="button"
													on:click={() => openAccessEditor(u)}
													class="text-slate-600 hover:text-slate-900"
												>
													Access
												</button>
												<button
													type="button"
													on:click={() => deleteConfirmUserId = u.id}
													disabled={u.id === user?.id}
													class="text-red-600 hover:text-red-900 disabled:text-gray-400 disabled:cursor-not-allowed"
												>
													Delete
												</button>
											</div>
										{/if}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</div>
	</div>
	{#if accessUserId}
		<div class="bg-white dark:bg-slate-900 rounded-xl shadow">
			<div class="p-6 border-b border-gray-200 dark:border-slate-800">
				<h3 class="text-lg font-semibold text-gray-900 dark:text-slate-100">Recipient Access</h3>
				<p class="text-sm text-gray-600 dark:text-slate-300 mt-1">
					Manage access for <span class="font-semibold">{accessUserName}</span>
				</p>
			</div>
			<div class="p-6 space-y-4">
				{#if accessError}
					<div class="p-4 bg-red-50 border border-red-200 rounded-xl dark:bg-red-950 dark:border-red-900">
						<p class="text-red-800 dark:text-red-200 text-base">{accessError}</p>
					</div>
				{/if}
				{#if accessUserRole === 'admin'}
					<p class="text-sm text-slate-600 dark:text-slate-300">Admins automatically have access to all recipients.</p>
				{/if}
				{#if accessLoading}
					<div class="text-center py-6">
						<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
						<p class="mt-2 text-gray-600 dark:text-slate-300 text-base">Loading access...</p>
					</div>
				{:else}
					{#if recipientsList.length === 0}
						<p class="text-sm text-slate-500 dark:text-slate-400">No recipients available.</p>
					{:else}
						<div class="flex flex-wrap items-center gap-3 text-sm text-gray-700 dark:text-slate-300">
							{#each recipientsList as recipient}
								<label class="flex items-center gap-2">
									<input
										type="checkbox"
										checked={accessRecipientIds.includes(recipient.id)}
										disabled={accessUserRole === 'admin'}
										on:change={(event) => {
											if (event.target.checked) {
												accessRecipientIds = [...accessRecipientIds, recipient.id];
											} else {
												accessRecipientIds = accessRecipientIds.filter((item) => item !== recipient.id);
											}
										}}
										class="w-4 h-4 text-blue-600 border-gray-300 rounded"
									/>
									<span>{recipient.name}</span>
								</label>
							{/each}
						</div>
					{/if}
				{/if}
				<div class="flex flex-wrap items-center gap-3">
					<button
						type="button"
						on:click={handleSaveAccess}
						disabled={accessSaving || accessUserRole === 'admin'}
						class="px-4 py-3 bg-blue-600 text-white rounded-xl text-base hover:bg-blue-700 disabled:bg-blue-300"
					>
						{accessSaving ? 'Saving...' : 'Save Access'}
					</button>
					<button
						type="button"
						on:click={closeAccessEditor}
						class="px-4 py-3 border border-slate-200 rounded-xl text-base"
					>
						Close
					</button>
				</div>
			</div>
		</div>
	{/if}
		</div>
	{/if}

	{#if adminTab === 'recipients'}
	<!-- Care Recipients -->
	<div class="bg-white dark:bg-slate-900 rounded-xl shadow">
		<div class="p-6 border-b border-gray-200 dark:border-slate-800">
			<h2 class="text-xl font-semibold text-gray-900 dark:text-slate-100">Care Recipients</h2>
			<p class="text-base text-gray-600 dark:text-slate-300 mt-1">Manage profiles for each person you track.</p>
		</div>
		<div class="p-6 space-y-6">
			{#if recipientsError}
				<div class="p-4 bg-red-50 border border-red-200 rounded-xl dark:bg-red-950 dark:border-red-900">
					<p class="text-red-800 dark:text-red-200 text-base">{recipientsError}</p>
				</div>
			{/if}

			<form class="grid gap-4 sm:grid-cols-4" on:submit|preventDefault={handleCreateRecipient}>
				<div class="sm:col-span-3">
					<label for="new-recipient-name" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Recipient Name</label>
					<input
						id="new-recipient-name"
						type="text"
						bind:value={newRecipientName}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
						placeholder="e.g., Mason"
						required
					/>
				</div>
				<div class="flex items-end gap-3">
					<label class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-slate-300">
						<input type="checkbox" bind:checked={newRecipientActive} class="w-5 h-5 text-blue-600 border-gray-300 rounded" />
						Active
					</label>
				</div>
				<div class="sm:col-span-4">
					<p class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Enabled categories</p>
					<div class="flex flex-wrap items-center gap-3 text-sm text-gray-700 dark:text-slate-300">
						{#each CARE_CATEGORIES as category}
							<label class="flex items-center gap-2">
								<input
									type="checkbox"
									value={category}
									checked={newRecipientCategories.includes(category)}
									on:change={(event) => {
										if (event.target.checked) {
											newRecipientCategories = [...newRecipientCategories, category];
										} else {
											newRecipientCategories = newRecipientCategories.filter((item) => item !== category);
										}
									}}
									class="w-4 h-4 text-blue-600 border-gray-300 rounded"
								/>
								<span class="capitalize">{category}</span>
							</label>
						{/each}
					</div>
				</div>
				<div class="sm:col-span-4">
					<button
						type="submit"
						class="px-4 py-3 bg-blue-600 text-white rounded-xl text-base hover:bg-blue-700 disabled:bg-blue-300"
						disabled={!newRecipientName}
					>
						Add Recipient
					</button>
				</div>
			</form>

			{#if recipientsLoading}
				<div class="text-center py-6">
					<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
					<p class="mt-2 text-gray-600 dark:text-slate-300 text-base">Loading recipients...</p>
				</div>
			{:else if recipientsList.length === 0}
				<p class="text-gray-600 dark:text-slate-300 text-base">No recipients created yet.</p>
			{:else}
				<div class="grid gap-3 sm:grid-cols-2">
					{#each recipientsList as recipient (recipient.id)}
						<div class="border border-slate-200 dark:border-slate-800 rounded-xl p-4">
							{#if editRecipientId === recipient.id}
								<div class="space-y-3">
									<input
										type="text"
										bind:value={editRecipientName}
										class="w-full px-4 py-2 border border-gray-300 rounded-xl text-base"
									/>
									<label class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-slate-300">
										<input type="checkbox" bind:checked={editRecipientActive} class="w-5 h-5 text-blue-600 border-gray-300 rounded" />
										Active
									</label>
									<div class="flex flex-wrap items-center gap-3 text-sm text-gray-700 dark:text-slate-300">
										<span class="font-medium">Enabled categories:</span>
										{#each CARE_CATEGORIES as category}
											<label class="flex items-center gap-2">
												<input
													type="checkbox"
													value={category}
													checked={editRecipientCategories.includes(category)}
													on:change={(event) => {
														if (event.target.checked) {
															editRecipientCategories = [...editRecipientCategories, category];
														} else {
															editRecipientCategories = editRecipientCategories.filter((item) => item !== category);
														}
													}}
													class="w-4 h-4 text-blue-600 border-gray-300 rounded"
												/>
												<span class="capitalize">{category}</span>
											</label>
										{/each}
									</div>
									<div class="flex items-center gap-2">
										<button on:click={handleSaveRecipient} class="px-3 py-2 bg-blue-600 text-white rounded-lg text-sm">Save</button>
										<button on:click={cancelEditRecipient} class="px-3 py-2 border border-slate-200 rounded-lg text-sm">Cancel</button>
									</div>
								</div>
							{:else}
								<div class="flex items-center justify-between">
									<div>
										<p class="text-base font-semibold text-slate-900 dark:text-slate-100">{recipient.name}</p>
										<p class="text-xs text-slate-500 dark:text-slate-400">
											{recipient.is_active ? 'Active' : 'Inactive'}
										</p>
										<p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
											{(recipient.enabled_categories || []).map((cat) => cat.replace('_', ' ')).join(', ') || 'No categories'}
										</p>
									</div>
									<div class="flex items-center gap-2">
										<button on:click={() => startEditRecipient(recipient)} class="px-3 py-2 border border-slate-200 rounded-lg text-sm">
											Edit
										</button>
										<button on:click={() => handleDeleteRecipient(recipient.id)} class="px-3 py-2 border border-red-200 text-red-600 rounded-lg text-sm">
											Delete
										</button>
									</div>
								</div>
							{/if}
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>
	{/if}

	{#if adminTab === 'meds'}
	<!-- Medication Library -->
	<div class="bg-white dark:bg-slate-900 rounded-xl shadow">
		<div class="p-6 border-b border-gray-200 dark:border-slate-800">
			<h2 class="text-xl font-semibold text-gray-900 dark:text-slate-100">Medication Library</h2>
			<p class="text-base text-gray-600 dark:text-slate-300 mt-1">Define medications with schedules and warnings.</p>
		</div>
		<div class="p-6 space-y-6">
			<RecipientSwitcher label="Medications for" />
			{#if medicationsError}
				<div class="p-4 bg-red-50 border border-red-200 rounded-xl dark:bg-red-950 dark:border-red-900">
					<p class="text-red-800 dark:text-red-200 text-base">{medicationsError}</p>
				</div>
			{/if}

			<form class="grid gap-4 sm:grid-cols-6" on:submit|preventDefault={handleCreateMedication}>
				<div class="sm:col-span-2">
					<label for="new-med-name" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Medication Name</label>
					<input
						id="new-med-name"
						type="text"
						bind:value={newMedicationName}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
						placeholder="e.g., Tylenol"
						required
					/>
				</div>
				<div>
					<label for="new-med-dose" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Dose</label>
					<input
						id="new-med-dose"
						type="text"
						bind:value={newMedicationDose}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
						placeholder="5"
					/>
				</div>
				<div>
					<label for="new-med-unit" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Unit</label>
					<input
						id="new-med-unit"
						type="text"
						bind:value={newMedicationUnit}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
						placeholder="ml"
					/>
				</div>
				<div>
					<label for="new-med-route" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Route</label>
					<select
						id="new-med-route"
						bind:value={newMedicationRoute}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
						required
					>
						<option value="" disabled>Select route</option>
						<option value="oral">Oral</option>
						<option value="tube">Tube Fed</option>
						<option value="topical">Topical</option>
						<option value="injection">Injection</option>
					</select>
				</div>
				<div>
					<label for="new-med-interval" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Interval (hrs)</label>
					<input
						id="new-med-interval"
						type="number"
						min="1"
						bind:value={newMedicationInterval}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
					/>
				</div>
				<div>
					<label for="new-med-warning" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Early Warning (min)</label>
					<input
						id="new-med-warning"
						type="number"
						min="0"
						bind:value={newMedicationWarning}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
					/>
				</div>
				<div class="sm:col-span-6">
					<label for="new-med-notes" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Notes</label>
					<textarea
						id="new-med-notes"
						bind:value={newMedicationNotes}
						rows="2"
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
						placeholder="Optional notes"
					></textarea>
				</div>
				<div class="sm:col-span-6 flex flex-wrap items-center gap-3">
					<label class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-slate-300">
						<input type="checkbox" bind:checked={newMedicationActive} class="w-5 h-5 text-blue-600 border-gray-300 rounded" />
						Active
					</label>
					<label class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-slate-300">
						<input type="checkbox" bind:checked={newMedicationAutoStart} class="w-5 h-5 text-blue-600 border-gray-300 rounded" />
						Start reminder when logged
					</label>
					<label class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-slate-300">
						<input type="checkbox" bind:checked={newMedicationQuick} class="w-5 h-5 text-blue-600 border-gray-300 rounded" />
						Show as quick med
					</label>
					<button
						type="submit"
						class="px-4 py-3 bg-blue-600 text-white rounded-xl text-base hover:bg-blue-700 disabled:bg-blue-300"
						disabled={!newMedicationName || !$selectedRecipientId}
					>
						Add Medication
					</button>
				</div>
			</form>

			{#if medicationsLoading}
				<div class="text-center py-6">
					<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
					<p class="mt-2 text-gray-600 dark:text-slate-300 text-base">Loading medications...</p>
				</div>
			{:else if medications.length === 0}
				<p class="text-gray-600 dark:text-slate-300 text-base">No medications yet.</p>
			{:else}
				<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
					{#each medications as med (med.id)}
						<div class="border border-gray-200 dark:border-slate-800 rounded-xl p-4">
							{#if editMedicationId === med.id}
								<div class="space-y-3">
									<div>
										<label for="edit-med-name" class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Name</label>
										<input
											id="edit-med-name"
											type="text"
											bind:value={editMedicationName}
											class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
										/>
									</div>
									<div class="grid gap-3 sm:grid-cols-2">
										<div>
											<label for="edit-med-dose" class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Dose</label>
											<input
												id="edit-med-dose"
												type="text"
												bind:value={editMedicationDose}
												class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
											/>
										</div>
										<div>
											<label for="edit-med-unit" class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Unit</label>
											<input
												id="edit-med-unit"
												type="text"
												bind:value={editMedicationUnit}
												class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
											/>
										</div>
									</div>
									<div>
										<label for="edit-med-route" class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Route</label>
										<select
											id="edit-med-route"
											bind:value={editMedicationRoute}
											class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
											required
										>
											<option value="" disabled>Select route</option>
											<option value="oral">Oral</option>
											<option value="tube">Tube Fed</option>
											<option value="topical">Topical</option>
											<option value="injection">Injection</option>
										</select>
									</div>
									<div class="grid gap-3 sm:grid-cols-2">
										<div>
											<label for="edit-med-interval" class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Interval (hrs)</label>
											<input
												id="edit-med-interval"
												type="number"
												min="1"
												bind:value={editMedicationInterval}
												class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
											/>
										</div>
										<div>
											<label for="edit-med-warning" class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Early Warning (min)</label>
											<input
												id="edit-med-warning"
												type="number"
												min="0"
												bind:value={editMedicationWarning}
												class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
											/>
										</div>
									</div>
									<div>
										<label for="edit-med-notes" class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Notes</label>
										<textarea
											id="edit-med-notes"
											bind:value={editMedicationNotes}
											rows="2"
											class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
										></textarea>
									</div>
									<label class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-slate-300">
										<input type="checkbox" bind:checked={editMedicationActive} class="w-5 h-5 text-blue-600 border-gray-300 rounded" />
										Active
									</label>
									<label class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-slate-300">
										<input type="checkbox" bind:checked={editMedicationAutoStart} class="w-5 h-5 text-blue-600 border-gray-300 rounded" />
										Start reminder when logged
									</label>
									<label class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-slate-300">
										<input type="checkbox" bind:checked={editMedicationQuick} class="w-5 h-5 text-blue-600 border-gray-300 rounded" />
										Show as quick med
									</label>
									<div class="flex items-center gap-2">
										<button on:click={handleSaveMedication} class="px-3 py-2 bg-blue-600 text-white rounded-lg text-sm">Save</button>
										<button on:click={cancelEditMedication} class="px-3 py-2 border border-slate-200 rounded-lg text-sm">Cancel</button>
									</div>
								</div>
							{:else}
								<div class="flex items-start justify-between gap-3">
									<div>
										<p class="text-base font-semibold text-slate-900 dark:text-slate-100">{med.name}</p>
										<p class="text-sm text-slate-500 dark:text-slate-400">
											{med.default_dose ? `${med.default_dose}${med.dose_unit ? ` ${med.dose_unit}` : ''}` : 'No dose'} · {med.default_route || 'Route not set'} · Every {med.interval_hours} hrs
										</p>
										<p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
											{med.is_active ? 'Active' : 'Inactive'} · Warn {med.early_warning_minutes} min early
											{med.auto_start_reminder ? ' · Auto reminder' : ''}
											{med.is_quick_med ? ' · Quick med' : ''}
										</p>
									</div>
									<div class="flex items-center gap-2">
										<button on:click={() => startEditMedication(med)} class="px-3 py-2 border border-slate-200 rounded-lg text-sm">
											Edit
										</button>
										<button on:click={() => handleDeleteMedication(med.id)} class="px-3 py-2 border border-red-200 text-red-600 rounded-lg text-sm">
											Delete
										</button>
									</div>
								</div>
							{/if}
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>

	<!-- Medication Reminders -->
	<div class="mt-8 bg-white dark:bg-slate-900 rounded-xl shadow">
		<div class="p-6 border-b border-gray-200 dark:border-slate-800">
			<h2 class="text-xl font-semibold text-gray-900 dark:text-slate-100">Medication Reminders</h2>
			<p class="text-base text-gray-600 dark:text-slate-300 mt-1">Set which medications should trigger reminders.</p>
		</div>
		<div class="p-6 space-y-6">
			<RecipientSwitcher label="Reminders for" />
			{#if !$selectedRecipientId}
				<div class="p-4 bg-yellow-50 border border-yellow-200 rounded-xl dark:bg-yellow-950 dark:border-yellow-900">
					<p class="text-yellow-800 dark:text-yellow-200 text-base">Select a recipient to manage reminders.</p>
				</div>
			{/if}
			{#if medRemindersError}
				<div class="p-4 bg-red-50 border border-red-200 rounded-xl dark:bg-red-950 dark:border-red-900">
					<p class="text-red-800 dark:text-red-200 text-base">{medRemindersError}</p>
				</div>
			{/if}

			<form class="grid gap-4 sm:grid-cols-3" on:submit|preventDefault={handleCreateReminder}>
				<div class="sm:col-span-2">
					<label for="new-reminder-medication" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Medication</label>
					<select
						id="new-reminder-medication"
						bind:value={newReminderMedicationId}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
						required
					>
						<option value="" disabled>Select a medication</option>
						{#each medications as med}
							<option value={med.id}>{med.name}</option>
						{/each}
					</select>
				</div>
				<div>
					<label for="new-reminder-interval" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Interval (hrs)</label>
					<input
						id="new-reminder-interval"
						type="number"
						min="1"
						bind:value={newReminderInterval}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
						placeholder="Use med default"
					/>
				</div>
				<div class="sm:col-span-2">
					<label for="new-reminder-start" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Start Time</label>
					<input
						id="new-reminder-start"
						type="datetime-local"
						bind:value={newReminderStartTime}
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
					/>
				</div>
				<div class="sm:col-span-3">
					<button
						type="submit"
						class="px-4 py-3 bg-blue-600 text-white rounded-xl text-base hover:bg-blue-700 disabled:bg-blue-300"
						disabled={!$selectedRecipientId || !newReminderMedicationId}
					>
						Add Reminder
					</button>
				</div>
			</form>

			{#if medRemindersLoading}
				<div class="text-center py-6">
					<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
					<p class="mt-2 text-gray-600 dark:text-slate-300 text-base">Loading reminders...</p>
				</div>
			{:else if medReminders.length === 0}
				<p class="text-gray-600 dark:text-slate-300 text-base">No reminders yet.</p>
			{:else}
				<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
					{#each medReminders as reminder (reminder.id)}
						<div class="border border-gray-200 dark:border-slate-800 rounded-xl p-4">
							<div class="flex items-start justify-between gap-3">
								<div>
									<p class="text-base font-semibold text-slate-900 dark:text-slate-100">{reminder.medication_name}</p>
									<p class="text-sm text-slate-500 dark:text-slate-400">
										Every {reminder.interval_hours} hrs · Warn {reminder.early_warning_minutes} min early
									</p>
									<p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
										{reminder.enabled ? 'Enabled' : 'Disabled'}
									</p>
								</div>
								<button
									type="button"
									on:click={() => handleToggleReminder(reminder)}
									class="px-3 py-2 border border-slate-200 rounded-lg text-sm"
								>
									{reminder.enabled ? 'Disable' : 'Enable'}
								</button>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>
	{/if}

	{#if adminTab === 'feeding'}
	<!-- Quick Feeds -->
	<div class="bg-white dark:bg-slate-900 rounded-xl shadow">
		<div class="p-6 border-b border-gray-200 dark:border-slate-800">
			<h2 class="text-xl font-semibold text-gray-900 dark:text-slate-100">Quick Feeds</h2>
			<p class="text-base text-gray-600 dark:text-slate-300 mt-1">Manage one-tap feeding templates (per recipient).</p>
		</div>
		<div class="p-6 space-y-6">
			<RecipientSwitcher label="Templates for" />
			{#if !$selectedRecipientId}
				<div class="p-4 bg-yellow-50 border border-yellow-200 rounded-xl dark:bg-yellow-950 dark:border-yellow-900">
					<p class="text-yellow-800 dark:text-yellow-200 text-base">Select a recipient to manage templates.</p>
				</div>
			{/if}
			{#if quickFeedsError}
				<div class="p-4 bg-red-50 border border-red-200 rounded-xl dark:bg-red-950 dark:border-red-900">
					<p class="text-red-800 dark:text-red-200 text-base">{quickFeedsError}</p>
				</div>
			{/if}

			<form class="grid gap-4 sm:grid-cols-4" on:submit|preventDefault={handleCreateQuickFeed}>
				<div class="sm:col-span-4">
					<p class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Feeding Type</p>
					<div class="grid grid-cols-3 gap-2">
						<button
							type="button"
							on:click={() => newFeedMode = 'continuous'}
							class={`px-3 py-2 rounded-xl border text-sm font-semibold ${newFeedMode === 'continuous' ? 'bg-green-600 text-white border-green-600' : 'border-gray-300 text-gray-700 dark:text-slate-200'}`}
						>
							Continuous
						</button>
						<button
							type="button"
							on:click={() => newFeedMode = 'bolus'}
							class={`px-3 py-2 rounded-xl border text-sm font-semibold ${newFeedMode === 'bolus' ? 'bg-green-600 text-white border-green-600' : 'border-gray-300 text-gray-700 dark:text-slate-200'}`}
						>
							Bolus
						</button>
						<button
							type="button"
							on:click={() => newFeedMode = 'oral'}
							class={`px-3 py-2 rounded-xl border text-sm font-semibold ${newFeedMode === 'oral' ? 'bg-green-600 text-white border-green-600' : 'border-gray-300 text-gray-700 dark:text-slate-200'}`}
						>
							Oral
						</button>
					</div>
				</div>

				{#if newFeedMode === 'continuous'}
					<div>
						<label for="new-feed-rate" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Rate (ml/hr)</label>
						<input
							id="new-feed-rate"
							type="number"
							min="0"
							bind:value={newFeedRate}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="500"
						/>
					</div>
					<div>
						<label for="new-feed-dose" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Dose (ml)</label>
						<input
							id="new-feed-dose"
							type="number"
							min="0"
							bind:value={newFeedDose}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="95"
						/>
					</div>
					<div>
						<label for="new-feed-interval" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Interval (hr)</label>
						<input
							id="new-feed-interval"
							type="number"
							min="0"
							step="0.1"
							bind:value={newFeedInterval}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="0.5"
						/>
					</div>
					<div>
						<label for="new-feed-formula" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Formula Type</label>
						<input
							id="new-feed-formula"
							type="text"
							bind:value={newFeedFormula}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="Pediasure"
						/>
					</div>
				{:else if newFeedMode === 'oral'}
					<div class="sm:col-span-4">
						<label for="new-feed-oral-notes" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Oral Notes</label>
						<textarea
							id="new-feed-oral-notes"
							rows="2"
							bind:value={newFeedOralNotes}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="Applesauce, puree, water..."
						></textarea>
					</div>
				{:else}
					<div>
						<label for="new-feed-amount" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Amount (ml)</label>
						<input
							id="new-feed-amount"
							type="number"
							min="0"
							bind:value={newFeedAmount}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="95"
						/>
					</div>
					<div class="sm:col-span-3">
						<label for="new-feed-formula" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Formula Type</label>
						<input
							id="new-feed-formula"
							type="text"
							bind:value={newFeedFormula}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
							placeholder="Pediasure"
						/>
					</div>
				{/if}

				<div class="sm:col-span-4">
					<button
						type="submit"
						class="px-4 py-3 bg-green-600 text-white rounded-xl text-base hover:bg-green-700 disabled:bg-green-300"
						disabled={!$selectedRecipientId}
					>
						Add Quick Feed
					</button>
				</div>
			</form>

			{#if quickFeedsLoading}
				<div class="text-center py-6">
					<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto"></div>
					<p class="mt-2 text-gray-600 dark:text-slate-300 text-base">Loading quick feeds...</p>
				</div>
			{:else if quickFeeds.length === 0}
				<p class="text-gray-600 dark:text-slate-300 text-base">No quick feeds yet.</p>
			{:else}
				<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
					{#each quickFeeds as feed (feed.id)}
						<div class="border border-gray-200 dark:border-slate-800 rounded-xl p-4">
							{#if editFeedId === feed.id}
								<div class="space-y-3">
									<div>
										<label for="edit-feed-mode" class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Feeding Type</label>
										<select
											id="edit-feed-mode"
											bind:value={editFeedMode}
											class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
										>
											<option value="continuous">Continuous</option>
											<option value="bolus">Bolus</option>
											<option value="oral">Oral</option>
										</select>
									</div>

									{#if editFeedMode === 'continuous'}
										<div class="grid gap-3 sm:grid-cols-2">
											<div>
												<label for="edit-feed-rate" class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Rate (ml/hr)</label>
												<input
													id="edit-feed-rate"
													type="number"
													min="0"
													bind:value={editFeedRate}
													class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
												/>
											</div>
											<div>
												<label for="edit-feed-dose" class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Dose (ml)</label>
												<input
													id="edit-feed-dose"
													type="number"
													min="0"
													bind:value={editFeedDose}
													class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
												/>
											</div>
											<div>
												<label for="edit-feed-interval" class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Interval (hr)</label>
												<input
													id="edit-feed-interval"
													type="number"
													min="0"
													step="0.1"
													bind:value={editFeedInterval}
													class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
												/>
											</div>
											<div>
												<label for="edit-feed-formula" class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Formula</label>
												<input
													id="edit-feed-formula"
													type="text"
													bind:value={editFeedFormula}
													class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
												/>
											</div>
										</div>
									{:else if editFeedMode === 'oral'}
										<div>
											<label for="edit-feed-oral-notes" class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Oral Notes</label>
											<textarea
												id="edit-feed-oral-notes"
												rows="2"
												bind:value={editFeedOralNotes}
												class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
											></textarea>
										</div>
									{:else}
										<div class="grid gap-3 sm:grid-cols-2">
											<div>
												<label for="edit-feed-amount" class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Amount (ml)</label>
												<input
													id="edit-feed-amount"
													type="number"
													min="0"
													bind:value={editFeedAmount}
													class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
												/>
											</div>
											<div>
												<label for="edit-feed-formula" class="block text-xs font-semibold text-gray-500 dark:text-slate-400 mb-1">Formula</label>
												<input
													id="edit-feed-formula"
													type="text"
													bind:value={editFeedFormula}
													class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
												/>
											</div>
										</div>
									{/if}
									<div class="flex items-center gap-3">
										<button
											on:click={handleSaveQuickFeed}
											class="px-3 py-2 text-xs font-semibold rounded-full bg-green-600 text-white hover:bg-green-700"
										>
											Save
										</button>
										<button
											on:click={cancelEditQuickFeed}
											class="px-3 py-2 text-xs font-semibold rounded-full border border-slate-200 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
										>
											Cancel
										</button>
									</div>
								</div>
							{:else}
								<div class="flex items-start justify-between gap-3">
									<div>
										<div class="text-base font-semibold text-gray-900 dark:text-slate-100 capitalize">
											{feed.mode || 'bolus'}
										</div>
										{#if (feed.mode || 'bolus') === 'continuous'}
											<div class="text-sm text-gray-600 dark:text-slate-300">
												Rate {feed.rate_ml_hr || '-'} ml/hr · Interval {feed.interval_hr || '-'} hr
											</div>
											<div class="text-sm text-gray-600 dark:text-slate-300">
												{#if feed.dose_ml}
													Dose {feed.dose_ml} ml
												{:else}
													Dose infinite
												{/if}
											</div>
										{:else if (feed.mode || 'bolus') === 'oral'}
											<div class="text-sm text-gray-600 dark:text-slate-300">{feed.oral_notes || 'Oral notes'}</div>
										{:else}
											<div class="text-sm text-gray-600 dark:text-slate-300">
												{feed.amount_ml || '-'} ml
												{#if feed.formula_type} · {feed.formula_type}{/if}
											</div>
										{/if}
										{#if feed.created_by_name}
											<div class="text-xs text-gray-500 dark:text-slate-400 mt-1">Added by {feed.created_by_name}</div>
										{/if}
									</div>
									<span class={`px-2 py-1 text-xs font-semibold rounded-full ${feed.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-200 text-gray-700'}`}>
										{feed.is_active ? 'Active' : 'Inactive'}
									</span>
								</div>
								<div class="mt-4 flex items-center gap-3">
									<button
										on:click={() => startEditQuickFeed(feed)}
										class="px-3 py-2 text-xs font-semibold rounded-full border border-slate-200 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
									>
										Edit
									</button>
									<button
										on:click={() => handleToggleQuickFeed(feed)}
										class="px-3 py-2 text-xs font-semibold rounded-full border border-green-200 text-green-700 hover:bg-green-50"
									>
										{feed.is_active ? 'Deactivate' : 'Activate'}
									</button>
									<button
										on:click={() => handleDeleteQuickFeed(feed.id)}
										class="text-red-600 text-xs font-semibold"
									>
										Delete
									</button>
								</div>
							{/if}
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>
	{/if}

	{#if adminTab === 'notifications'}
	<!-- Notification Settings -->
	<div class="bg-white dark:bg-slate-900 rounded-xl shadow">
		<div class="p-6 border-b border-gray-200 dark:border-slate-800">
			<h2 class="text-xl font-semibold text-gray-900 dark:text-slate-100">Notifications</h2>
			<p class="text-base text-gray-600 dark:text-slate-300 mt-1">Adjust reminder and alert behavior.</p>
		</div>
		<div class="p-6 space-y-4">
			{#if notificationsError}
				<div class="p-4 bg-red-50 border border-red-200 rounded-xl dark:bg-red-950 dark:border-red-900">
					<p class="text-red-800 dark:text-red-200 text-base">{notificationsError}</p>
				</div>
			{/if}
			{#if notificationsLoading}
				<p class="text-sm text-gray-600 dark:text-slate-300">Loading notification settings...</p>
			{:else}
				<div class="grid gap-4 sm:grid-cols-2">
					<label class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-slate-300">
						<input type="checkbox" bind:checked={notificationsEnableInApp} class="w-5 h-5 text-blue-600 border-gray-300 rounded" />
						In-app notifications
					</label>
					<label class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-slate-300">
						<input type="checkbox" bind:checked={notificationsEnablePush} class="w-5 h-5 text-blue-600 border-gray-300 rounded" />
						Push notifications
					</label>
					<div>
						<label for="notifications-due-soon" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Due soon window (min)</label>
						<input
							id="notifications-due-soon"
							type="number"
							min="0"
							bind:value={notificationsDueSoonMinutes}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
						/>
					</div>
					<div>
						<label for="notifications-overdue-repeat" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Overdue repeat (min)</label>
						<input
							id="notifications-overdue-repeat"
							type="number"
							min="0"
							bind:value={notificationsOverdueMinutes}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
						/>
					</div>
					<div>
						<label for="notifications-snooze-default" class="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Default snooze (min)</label>
						<input
							id="notifications-snooze-default"
							type="number"
							min="0"
							bind:value={notificationsSnoozeMinutes}
							class="w-full px-4 py-3 border border-gray-300 rounded-xl text-base"
						/>
					</div>
				</div>
				<div class="mt-6 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-4 space-y-3">
					<div>
						<h3 class="text-base font-semibold text-slate-900 dark:text-slate-100">Device push status</h3>
						<p class="text-sm text-slate-600 dark:text-slate-300">Enable push notifications on this device after turning on push in settings.</p>
					</div>
					<div class="text-sm text-slate-700 dark:text-slate-200 space-y-1">
						<div>Supported: {pushSupported ? 'Yes' : 'No'}</div>
						<div>Permission: {pushPermission}</div>
						<div>Subscribed: {pushSubscriptionActive ? 'Yes' : 'No'}</div>
					</div>
					{#if pushActionError}
						<p class="text-sm text-red-700 dark:text-red-200">{pushActionError}</p>
					{/if}
					{#if pushTestStatus}
						<p class="text-sm text-emerald-700 dark:text-emerald-200">{pushTestStatus}</p>
					{/if}
					<div class="flex flex-wrap gap-3">
						<button
							type="button"
							on:click={handleEnableDevicePush}
							disabled={pushActionLoading || !pushSupported}
							class="px-4 py-2 rounded-xl text-sm font-semibold bg-emerald-600 text-white disabled:opacity-50"
						>
							Enable on this device
						</button>
						<button
							type="button"
							on:click={handleDisableDevicePush}
							disabled={pushActionLoading || !pushSupported}
							class="px-4 py-2 rounded-xl text-sm font-semibold border border-slate-200 dark:border-slate-600 text-slate-700 dark:text-slate-200 disabled:opacity-50"
						>
							Disable on this device
						</button>
						<button
							type="button"
							on:click={handleSendTestNotification}
							disabled={pushActionLoading || !pushSubscriptionActive}
							class="px-4 py-2 rounded-xl text-sm font-semibold border border-slate-200 dark:border-slate-600 text-slate-700 dark:text-slate-200 disabled:opacity-50"
						>
							Send test notification
						</button>
					</div>
				</div>
				<div>
					<button
						type="button"
						on:click={handleSaveNotificationSettings}
						class="px-4 py-3 bg-blue-600 text-white rounded-xl text-base hover:bg-blue-700"
					>
						Save Notification Settings
					</button>
				</div>
			{/if}
		</div>
	</div>
	{/if}

	{#if adminTab === 'users'}
	<!-- System Information -->
	<div class="mt-8 bg-white dark:bg-slate-900 rounded-xl shadow p-6">
		<h2 class="text-xl font-semibold text-gray-900 dark:text-slate-100 mb-4">System Information</h2>
		<dl class="grid grid-cols-1 gap-4 sm:grid-cols-2">
			<div>
				<dt class="text-sm font-medium text-gray-500 dark:text-slate-400">Total Users</dt>
				<dd class="mt-1 text-2xl font-semibold text-gray-900 dark:text-slate-100">{users.length}</dd>
			</div>
			<div>
				<dt class="text-sm font-medium text-gray-500 dark:text-slate-400">Active Users</dt>
				<dd class="mt-1 text-2xl font-semibold text-gray-900 dark:text-slate-100">
					{users.filter(u => u.is_active).length}
				</dd>
			</div>
			<div>
				<dt class="text-sm font-medium text-gray-500 dark:text-slate-400">Administrators</dt>
				<dd class="mt-1 text-2xl font-semibold text-gray-900 dark:text-slate-100">
					{users.filter(u => u.role === 'admin').length}
				</dd>
			</div>
			<div>
				<dt class="text-sm font-medium text-gray-500 dark:text-slate-400">Caregivers</dt>
				<dd class="mt-1 text-2xl font-semibold text-gray-900 dark:text-slate-100">
					{users.filter(u => u.role === 'caregiver').length}
				</dd>
			</div>
		</dl>
	</div>

	<!-- Timezone Settings -->
	<div class="mt-8 bg-white dark:bg-slate-900 rounded-xl shadow p-6">
		<h2 class="text-xl font-semibold text-gray-900 dark:text-slate-100 mb-2">Timezone</h2>
		<p class="text-sm text-gray-600 dark:text-slate-300 mb-4">
			Set the timezone used for timestamps throughout the app.
		</p>
		{#if timezoneError}
			<div class="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl dark:bg-red-950 dark:border-red-900">
				<p class="text-red-800 dark:text-red-200 text-sm">{timezoneError}</p>
			</div>
		{/if}
		<div class="flex flex-wrap items-center gap-3">
			<select
				bind:value={timezoneValue}
				disabled={timezoneLoading}
				class="px-4 py-3 border border-gray-300 rounded-xl text-base disabled:bg-gray-100 dark:disabled:bg-slate-800"
			>
				{#each timezones as tz}
					<option value={tz}>{tz}</option>
				{/each}
			</select>
			<button
				type="button"
				on:click={handleTimezoneSave}
				disabled={timezoneLoading}
				class="px-4 py-3 bg-blue-600 text-white rounded-xl text-base hover:bg-blue-700 disabled:bg-blue-400"
			>
				Save Timezone
			</button>
		</div>
	</div>
	{/if}
	</main>
</div>
