# Care Documentation App - Development Progress

## Project Information
**Start Date:** 2026-01-10
**Purpose:** Progressive Web App for documenting care activities for a child with neurological issues
**Target Deployment:** Raspberry Pi 4B via Docker

---

## Technology Stack
- **Frontend:** SvelteKit + PWA + Tailwind CSS
- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL 15
- **Authentication:** JWT with HTTP-only cookies
- **Deployment:** Docker Compose + Nginx
- **Version Control:** GitHub

---

## Development Log

### 2026-01-10 - Phase 1: Project Setup Complete ✓

#### Completed
- [x] Created project plan with comprehensive architecture
- [x] Initialized git repository
- [x] Created directory structure
- [x] Initialized SvelteKit frontend with:
  - package.json with PWA dependencies (@vite-pwa/sveltekit, localforage)
  - vite.config.js with PWA and Workbox configuration
  - tailwind.config.js for styling
  - svelte.config.js with adapter-node
  - Basic route structure (+layout.svelte, +page.svelte)
  - app.html with PWA meta tags
  - app.css with global styles
- [x] Set up FastAPI backend structure:
  - requirements.txt with all dependencies
  - main.py with CORS and basic endpoints
  - config.py with Pydantic settings
  - database.py with SQLAlchemy setup
  - Directory structure for routes, models, services, middleware
- [x] Created Docker Compose configurations:
  - docker-compose.yml for development
  - docker-compose.prod.yml for Raspberry Pi production
  - Dockerfiles for frontend and backend (dev and prod versions)
  - PostgreSQL optimized for Raspberry Pi 4B
- [x] Created nginx reverse proxy configuration with HTTPS support
- [x] Created .env.example with all required environment variables
- [x] Created .gitignore with comprehensive exclusions
- [x] Wrote comprehensive README.md with:
  - Quick start instructions
  - Project structure documentation
  - Development workflow
  - Raspberry Pi deployment guide
  - Troubleshooting section
- [x] Created utility scripts:
  - scripts/backup.sh for automated database backups
  - scripts/deploy.sh for Raspberry Pi deployment
- [x] Made initial git commit

### 2026-01-10 - Phase 2: Authentication System Complete ✓

#### Completed
- [x] Created User model with SQLAlchemy
  - UUID primary key
  - Fields: username, email, password_hash, role, is_active
  - Timestamps: created_at, updated_at
- [x] Implemented JWT token generation and validation service
  - Access tokens (15 min expiry)
  - Refresh tokens (7 day expiry)
  - Password hashing with bcrypt
  - Token verification and type checking
- [x] Built authentication endpoints (login, logout, register, refresh, /me)
  - Login with HTTP-only cookie support
  - Logout (cookie clearing)
  - Register new users (admin only)
  - Token refresh endpoint
  - Get current user info
- [x] Created authentication middleware
  - Cookie-based token extraction
  - Role-based access control
  - get_current_user dependency
  - get_current_active_admin dependency
- [x] Built login page UI
  - Responsive design with Tailwind CSS
  - Error handling and loading states
  - Redirect to dashboard after login
- [x] Built register page UI
  - Admin-only access
  - Form validation
  - Role selection (admin/caregiver)
  - Success/error feedback
- [x] Implemented auth state management in frontend
  - Svelte stores for auth state
  - LocalStorage persistence
  - Derived stores (isAuthenticated, isAdmin)
  - API service layer
- [x] Created admin initialization script (create_admin.py)
  - Interactive CLI for creating first admin user
  - Password validation
  - Duplicate checking
- [x] Updated dashboard with user info and logout

### 2026-01-10 - Phase 3: Core Event System Partial ✓

#### Completed
- [x] Created Event model with SQLAlchemy
  - UUID primary key
  - Fields: type, timestamp, notes, event_data (JSONB), user_id
  - Relationship to User model
  - Timestamps: created_at, updated_at
- [x] Built event CRUD endpoints
  - POST /events/ - Create new event
  - GET /events/ - List events with filtering
  - GET /events/{id} - Get single event
  - PATCH /events/{id} - Update event
  - DELETE /events/{id} - Delete event
  - GET /events/stats/summary - Event statistics
- [x] Created EventList component for displaying events
- [x] Created EventCard component with color-coded types
- [x] Implemented frontend event service (API layer)
- [x] Built dashboard with event statistics and recent events

#### Completed (Phase 3)
- [x] Create floating + button component
- [x] Build quick entry modal with event type selector
- [x] Implement medication entry form
- [x] Implement feeding entry form
- [x] Implement diaper change form
- [x] Implement demeanor log form
- [x] Implement general observation form

### 2026-01-10 - Critical Bug Fixes & Production Deployment ✓

#### Completed
- [x] Fixed Event metadata field name mismatch (event.metadata → event.event_data)
- [x] Fixed authentication token extraction (OAuth2PasswordBearer → cookie-based auth)
- [x] Removed insecure default JWT_SECRET_KEY and added validation
- [x] Fixed cookie security flags to be environment-aware (secure=True in production)
- [x] Fixed CORS configuration to use environment variables
- [x] Fixed CORS_ORIGINS parsing error (JSON array → comma-separated string)
- [x] Made .env file optional in Docker containers (uses environment variables)
- [x] Added PUBLIC_API_URL configuration for frontend API connection
- [x] Fixed N+1 query problem in event list (added eager loading)
- [x] Created comprehensive deployment documentation:
  - DEPLOYMENT_GUIDE.md - Full Raspberry Pi deployment guide
  - QUICK_START.md - Quick reference guide
  - TROUBLESHOOTING.md - Common issues and solutions
  - scripts/pi-setup.sh - Automated setup script
- [x] Deployed to Raspberry Pi 4B at 192.168.1.101
- [x] Created web-based setup system for initial admin creation:
  - New /api/setup/initialize endpoint (POST)
  - New /api/setup/status endpoint (GET)
  - setup.html - Browser-based admin creation UI
  - Replaces complex Docker exec workflow
  - Auto-disables after first admin is created (security)

#### Known Issues Fixed
- ✓ Backend field name mismatch causing 500 errors
- ✓ Token authentication cookie extraction failure
- ✓ Hardcoded insecure JWT secret
- ✓ Cookie security flags disabled in production
- ✓ CORS hardcoded to localhost
- ✓ CORS_ORIGINS JSON parsing error
- ✓ Frontend unable to connect to backend API

### 2026-01-11 - Authentication Fixes & Admin Panel ✓

#### Critical Authentication Fixes
- [x] Fixed cross-origin authentication (HTTP-only cookies don't work across ports)
  - Solution: Hybrid approach using localStorage + Authorization header
  - Frontend stores access_token in localStorage after login
  - All API requests include Authorization: Bearer header
  - Backend accepts tokens from EITHER header OR cookie
- [x] Fixed cookie path settings (added path="/" to all cookies)
- [x] Fixed get_token_from_request to check Authorization header
- [x] Fixed register endpoint response validation (UUID/datetime to string conversion)
- [x] Fixed missing List import causing backend startup crash

#### Admin Panel Implementation
- [x] Created comprehensive admin panel at /admin route
- [x] User management table with search and filters
- [x] Toggle user active/inactive status
- [x] Delete users with confirmation (prevents self-deletion)
- [x] System information dashboard (user counts by role/status)
- [x] Backend endpoints:
  - GET /auth/users - List all users (admin only)
  - PATCH /auth/users/{id} - Update user (admin only)
  - DELETE /auth/users/{id} - Delete user (admin only)
- [x] Admin Panel button in main dashboard (purple, with icon)
- [x] Role-based access control (admin-only routes)

#### Testing & Deployment
- [x] Verified login/logout flow works correctly
- [x] Verified medication/event entry works
- [x] Verified user registration works
- [x] Verified admin panel user management works
- [x] Deployed to Raspberry Pi successfully
- [x] All systems operational

#### Current Status (2026-01-11) - FULLY OPERATIONAL ✓
- Backend: Running on Raspberry Pi at http://192.168.1.101:8000
- Frontend: Running at http://192.168.1.101:3000
- Database: PostgreSQL 15 running with optimized settings for Pi
- Admin account: Created and working
- Authentication: WORKING - localStorage + Authorization header approach
- Admin Panel: WORKING - full user management capabilities
- Event System: WORKING - medications, feeding, diaper, demeanor, observations
- All critical bugs: RESOLVED

### 2026-01-11 - Phase 4: Quick Actions + Touch-Friendly UI (In Progress)

#### Completed
- [x] Added quick medication and quick feed templates (database tables + API)
- [x] Built admin management UI for quick meds/feeds with activate/deactivate
- [x] Added inline editing for quick meds/feeds (does not affect historical events)
- [x] Implemented quick action buttons in Quick Entry modal (single-tap logging)
- [x] Added optional quick medication note toggle for fast context entry
- [x] Updated Quick Entry modal to a touch-friendly bottom sheet layout
- [x] Increased touch target sizes across dashboard, admin panel, login, and register
- [x] Added dark mode with system default + manual toggle
- [x] Added event edit/delete controls in recent activity (timestamp + metadata)
- [x] Added feeding modes (continuous/bolus/oral) with start/stop tracking and metadata
- [x] Added admin-configurable timezone setting
- [x] Added real-time updates via SSE for events and feed status
- [x] Added hamburger menu header with centered logo for mobile-friendly navigation
- [x] Fixed quick medication buttons styling in dark mode
- [x] Added custom Care Docs logo mark for header
- [x] Added pump actual total entry when stopping continuous feeds
- [x] Added feeding totals summary to history view
- [x] Added automatic token refresh to keep sessions alive
- [x] Increased token lifetimes to reduce logouts
- [x] Care recipients (per-person profiles) with recipient selector and per-recipient templates
- [x] Sync active continuous feed start time when editing feed start event
- [x] Refresh active feed banner on event updates

---

### 2026-01-12 - Phase 5: Med Reminders + Recipient Customization (In Progress)

#### Completed
- [x] Added medication library enhancements (default route, quick med flag, auto-start reminder)
- [x] Added medication reminders (API, next due lookup, early warning checks, skip reminders)
- [x] Unified quick meds with the medication library and auto-log quick meds
- [x] Added per-recipient enabled categories and filtering across dashboard/history/quick entry
- [x] Added admin controls for recipient categories and notification settings
- [x] Added user profile updates (display name) and avatar upload storage served from /avatars
- [x] Replaced hamburger navigation with a user avatar button in headers
- [x] Fixed SSE pub/sub publishing errors for live updates

#### Pending
- [x] Run migrations for new columns: users.display_name, users.avatar_filename, care_recipients.enabled_categories, medications.default_route, medications.is_quick_med, medications.auto_start_reminder

### 2026-01-19 - Status Check (No code changes)

#### Current Focus
- Pending migrations for new columns (see list above)
- Web Push notifications and reminder UI still not implemented (Phase 6 "Reminders & Notifications")

### 2026-01-19 - Next Steps Identified (No code changes)

#### Next Up
- Implement Reminders & Notifications (Web Push API setup, permission flow, reminder management UI, notification service, APScheduler integration)
- Add testing infrastructure (pytest, Vitest) and cover core auth/event/reminder flows
- Address deployment gaps: HTTPS, automated backups, performance optimization

### 2026-01-19 - Reminder Scheduler + Notification Endpoints (Backend Complete)

#### Completed
- [x] Added APScheduler-based reminder scanner with SSE/pubsub broadcasts for due reminders
- [x] Added push subscription model + API endpoints (subscribe/unsubscribe/list/test)
- [x] Added reminder last_notified_at tracking to prevent duplicate alerts
- [x] Added notification service wrapper for Web Push delivery
- [x] Added scheduler configuration settings (SCHEDULER_ENABLED, REMINDER_SCAN_INTERVAL_SECONDS)

### 2026-01-19 - Push Subscription UI + VAPID Endpoint (Complete)

#### Completed
- [x] Added VAPID public key endpoint for frontend subscription flow
- [x] Added device push enable/disable + test controls in Admin Notifications tab
- [x] Switched PWA build to injectManifest to ensure custom service worker handles push events
- [x] Added frontend API helpers for push subscription management
- [x] Applied DB migrations for push_subscriptions + medication_reminders.last_notified_at
- [x] Generated VAPID keys and updated environment configuration
- [x] Updated production env to use tunnel domain for CORS, PUBLIC_API_URL, and frontend ORIGIN
- [x] Enabled proxy headers in production backend to preserve HTTPS in redirects behind Cloudflare
- [x] Fixed login redirect race by awaiting auth store persistence
- [x] Switched to simple split-hostname setup (frontend on caredocs.*, API on api.caredocs.*)
- [x] Simplified deployment to single hostname via nginx reverse proxy on port 8080
- [x] Added auto API base selection to support both local and public access
- [x] Fixed SSE stream base URL to use auto API base (prevents /api/stream 404 locally)
- [x] Added HEAD handler for /api/health and disabled slash redirects for medications

### 2026-01-20 - Invite-Based User Onboarding + Recipient Access (In Progress)

#### Completed
- [x] Added invite system with expiring tokens and copyable links
- [x] Added user-recipient access mapping and access control helpers
- [x] Enforced recipient access + read-only restrictions across event, feed, reminder, photo, stream, and template endpoints
- [x] Updated admin UI to create invites, edit roles (admin/caregiver/read_only), and manage recipient access
- [x] Added invite acceptance page with username/email/name + password strength validation
- [x] Added pending invite list + revoke support in admin UI
- [x] Enforced case-insensitive usernames in login/register/invites/admin scripts
- [x] Applied DB tables for invites/access and rebuilt production containers
- [x] Disabled auth refresh on invite route to avoid redirect to login
- [x] Fixed user delete to clear recipient access first (prevents FK 500)

## Architecture Decisions

### Why SvelteKit?
- 30% faster load times than React/Vue
- Smaller bundle sizes (critical for Raspberry Pi)
- Native PWA support via @vite-pwa/sveltekit
- No virtual DOM overhead

### Why FastAPI?
- 5-10x faster than Flask
- Async support for I/O operations (photos, database)
- Lower memory footprint (~150MB)
- ARM64 Docker images available
- Type safety with Pydantic

### Why PostgreSQL over SQLite?
- Multi-user concurrent access required
- Better transaction safety for medical data
- Robust backup/restore capabilities
- JSON support for flexible event metadata

---

## Feature Implementation Tracker

### Core Features Status

#### 1. Quick Entry Interface
- [x] Floating + button component
- [x] Event type selector
- [x] Medication entry form
- [x] Feeding entry form
- [x] Diaper change form
- [x] Demeanor log form
- [x] General observation form
- [x] Timestamp auto-generation
- [x] User tagging

#### 2. Multi-User Authentication ✓
- [x] JWT token generation
- [x] HTTP-only cookie handling
- [x] Login page
- [x] Logout functionality
- [x] User registration (admin only)
- [x] Protected routes
- [x] Session management
- [ ] Offline auth persistence (Phase 4)

#### 3. Offline-First Architecture ✓
- [x] Service worker setup
- [x] IndexedDB configuration
- [x] LocalForage integration
- [x] Workbox caching strategies
- [x] Background sync
- [x] Conflict resolution
- [x] Sync status indicator

#### 4. Photo Attachments ✓
- [x] Camera access
- [x] Client-side compression
- [x] IndexedDB blob storage
- [x] Upload endpoint
- [x] Server-side thumbnail generation
- [x] Photo gallery component
- [x] Lazy loading
- [x] Offline photo queue

#### 5. Historical View & Reports
- [x] Timeline view (history list)
- [x] Event filtering
- [x] Date range picker
- [x] Search functionality
- [x] Event detail modal
- [x] Edit/delete events
- [x] Export to CSV
- [x] Data visualization (daily activity bars)
- [x] Feeding totals summary (daily + range)

#### 6. Reminders & Notifications
- [x] Web Push API setup
- [x] Permission request
- [ ] Reminder management UI
- [x] Notification service
- [x] APScheduler integration
- [ ] Snooze/dismiss
- [ ] Notification clicks
- [x] Backend scheduler + push subscription endpoints

---

## Database Schema

### Tables Created
- [x] users (id, username, email, password_hash, role, is_active, created_at, updated_at)
- [x] events
- [x] quick_medications
- [x] quick_feeds
- [x] care_recipients
- [x] photos
- [ ] reminders
- [x] push_subscriptions
- [x] user_invites
- [x] user_recipient_access

---

## Testing Checklist

### Unit Tests
- [ ] Backend API endpoints
- [ ] Authentication service
- [ ] Event creation/retrieval
- [ ] Photo upload/download

### Integration Tests
- [ ] Offline sync flow
- [ ] Multi-user concurrent access
- [ ] Photo attachment workflow
- [ ] Notification delivery

### E2E Tests
- [ ] User registration and login
- [ ] Create all event types
- [ ] Offline mode
- [ ] PWA installation
- [ ] Photo capture and upload
- [ ] Historical filtering
- [ ] Reminder creation and notification

---

## Performance Metrics

### Target Metrics (Raspberry Pi 4B)
- Load time: < 3 seconds
- Memory usage: < 600MB total
- Photo upload: < 10 seconds
- Offline sync: < 5 seconds for 10 events
- Notification delivery: < 1 minute
- Concurrent users: 3+

### Actual Metrics
_To be measured after deployment_

---

## Deployment History

### Development Environment
- [ ] Local development setup complete
- [ ] Docker Compose development config working
- [ ] Hot reload configured

### Raspberry Pi 4B
- [x] Initial deployment (2026-01-10)
- [x] Docker Compose production configuration
- [x] Backend running on port 8000
- [x] Frontend running on port 3000
- [x] PostgreSQL optimized for Pi hardware
- [x] Admin user created
- [x] Authentication fully working (2026-01-11)
- [x] Admin panel deployed and operational (2026-01-11)
- [x] Event entry system working (2026-01-11)
- [ ] HTTPS configured (pending domain/SSL certificate)
- [ ] Automated backups setup
- [ ] Performance optimization complete

---

## Known Issues

### All Critical Issues: RESOLVED ✓
- ✓ Cross-origin authentication (localStorage + Authorization header)
- ✓ Cookie path settings
- ✓ Register endpoint validation
- ✓ Backend startup crashes
- ✓ User management capabilities

### To Address (Non-Critical)
- ✓ PWA icons (now using SVG - icon.svg, favicon.svg)
- No testing infrastructure (pytest, Vitest)
- No rate limiting on authentication endpoints
- Alembic added; need baseline revision and plan to disable create_all in production
- Insufficient logging configuration
- Dynamic Tailwind classes causing bundle bloat
- No input validation length limits on text fields

---

## Phase 4: Quick Actions & Touch-Friendly UI (In Progress - 2026-01-11)

### Quick Actions System Requirements
**Goal:** Make event entry faster with predefined templates for common medications and feeds

#### Quick Medications Feature
- [x] Admin panel section to manage quick medication templates
- [x] Database table: `quick_medications` (id, name, dosage, route, is_active, created_by_user_id, created_at)
- [x] API endpoints:
  - GET /api/quick-meds - List all active quick medications
  - POST /api/quick-meds - Create new quick medication (admin only)
  - PATCH /api/quick-meds/{id} - Update quick medication (admin only)
  - DELETE /api/quick-meds/{id} - Delete quick medication (admin only)
- [x] Touch-friendly button grid in QuickEntry modal (above manual form)
- [x] Single tap logs medication with predefined values
- [x] Optional "Add Note" toggle:
  - Default: OFF (log without notes)
  - When ON: Show textarea for context (fever, pain, before bed, etc.)
  - Checkbox should be large and touch-friendly
- [x] Manual entry form remains available for non-standard doses

#### Quick Feeds Feature
- [x] Admin panel section to manage quick feed templates
- [x] Database table: `quick_feeds` (id, amount_ml, duration_min, formula_type, is_active, created_by_user_id, created_at)
- [x] API endpoints:
  - GET /api/quick-feeds - List all active quick feeds
  - POST /api/quick-feeds - Create new quick feed (admin only)
  - PATCH /api/quick-feeds/{id} - Update quick feed (admin only)
  - DELETE /api/quick-feeds/{id} - Delete quick feed (admin only)
- [x] Touch-friendly button grid in QuickEntry modal
- [x] Single tap logs feed with predefined values
- [x] Manual entry form for custom amounts/types

### Touch-Friendly UI Overhaul
**Goal:** Optimize entire app for phone/tablet touch interaction

#### Design Principles
- Minimum 48px touch targets (larger than Apple HIG 44px for easier use)
- Generous spacing between interactive elements (16px minimum)
- Bottom-aligned primary actions (easier thumb reach on phones)
- Larger text sizes:
  - Body text: 16px minimum (no more 14px)
  - Buttons: 18px minimum
  - Headers: Scale up by 20%
- Higher contrast for outdoor visibility
- Sticky headers for context while scrolling
- Large, obvious cancel/back buttons

#### Components to Update
- [x] **QuickEntry Modal**
  - Bottom-sheet style on mobile (slide up from bottom)
  - Larger event type buttons (min 80px height)
  - Grid layout: 2 columns on mobile, 3 on tablet
  - Bigger form inputs (min 48px height)
  - Bottom-aligned submit button

- [x] **Event Type Selector**
  - Card grid instead of buttons
  - Larger icons (48px instead of 24px)
  - More visual feedback on tap

- [x] **Dashboard**
  - Larger + button (72px instead of 64px)
  - Bottom-right positioning with more padding
  - Touch-friendly event cards (no tiny buttons)

- [x] **Admin Panel**
  - Card-based layout on mobile (instead of table)
  - Larger action buttons
  - Confirm dialogs with bigger touch targets

- [x] **Forms**
  - Larger inputs (min 48px height)
  - Bigger checkboxes/radio buttons (24px)
  - More padding in text areas
  - Native mobile date/time pickers (pending)

- [ ] **Navigation**
  - Consider bottom nav bar for mobile
  - Larger header buttons
  - More spacing in dropdown menus

---

## Phase 5: Care Recipients (Complete - 2026-01-12) ✓

**Goal:** Support multiple care recipients with per-recipient templates and reports.

#### Completed
- [x] Add CareRecipient model + CRUD endpoints
- [x] Add recipient_id to events, quick meds, quick feeds
- [x] Recipient selector on dashboard + history
- [x] Admin management for recipients
- [x] Per-recipient templates (quick meds/feeds)
- [x] Per-recipient active continuous feed tracking

---

## Phase 6: Offline-First Architecture (Complete - 2026-01-16) ✓

**Goal:** Enable full offline functionality with automatic sync when connection is restored.

#### Implementation Details

**Offline Store (src/lib/stores/offline.js)**
- LocalForage instances for events, pending queue, and cache
- Sync status tracking: synced | pending | syncing | error | offline
- Online/offline event listeners with auto-sync on reconnection
- Temporary ID generation for offline-created events
- Cache management with configurable max age

**Service Worker (src/service-worker.js)**
- Workbox-based with injectManifest strategy
- NetworkFirst for API calls with 10s timeout
- CacheFirst for images and static assets
- StaleWhileRevalidate for JS/CSS
- Background sync via Workbox BackgroundSyncPlugin
- Push notification support (ready for Phase 7)

**API Service Enhancements (src/lib/services/api.js)**
- Offline detection and automatic queueing
- Optimistic responses for creates
- Cache-first reads when offline
- Automatic cache population on successful fetches
- Network error detection and fallback

**Sync Status Component (src/lib/components/SyncStatus.svelte)**
- Visual indicator: green (synced), yellow (pending), blue (syncing), red (error), gray (offline)
- Shows pending count
- Click to manually trigger sync
- Integrated into dashboard header

**Auth Persistence (src/lib/stores/auth.js)**
- Dual storage: localStorage (sync) + IndexedDB (reliable)
- Token persistence for offline session restoration
- Automatic recovery from IndexedDB if localStorage cleared

**PWA Icons**
- SVG-based icons for crisp display at any size
- icon.svg (512x512) and favicon.svg (32x32)

#### Completed
- [x] Create offline store with IndexedDB via LocalForage
- [x] Implement custom service worker with caching strategies
- [x] Create offline event queue for background sync
- [x] Add sync status indicator component
- [x] Implement conflict resolution for offline changes
- [x] Update API service to use offline-first pattern
- [x] Add offline auth persistence
- [x] Create PWA icons (SVG-based)
- [x] Integrate SyncStatus into dashboard

---

## Future Enhancements

### Post-MVP Features
- Voice entry via Web Speech API
- Medication inventory tracking
- Doctor appointment scheduling
- Vital signs tracking
- Chart generation for medical reports
- Multi-language support
- Barcode scanning for medications
- Swipe gestures for common actions
- Haptic feedback (PWA vibration API)

---

## Resources & Documentation

### Official Documentation
- [SvelteKit Docs](https://kit.svelte.dev/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [PWA Guide](https://web.dev/learn/pwa/)
- [Workbox Docs](https://developer.chrome.com/docs/workbox)

### Project Links
- GitHub Repository: https://github.com/Apbooks/care-docs-app
- Production URL: http://192.168.1.101:3000 (Raspberry Pi - local network)
- Backend API: http://192.168.1.101:8000 (Raspberry Pi - local network)
- API Documentation: http://192.168.1.101:8000/docs

---

## Notes

- **Security**: All medical data must be transmitted over HTTPS
- **Backup**: Daily automated backups at 2:00 AM
- **Privacy**: EXIF data stripped from all photos
- **Reliability**: PostgreSQL provides ACID compliance for data integrity

---

**Last Updated:** 2026-01-20 (Invites + access control)

---

## Development Guidelines

**IMPORTANT:** Always keep this `claude.md` file updated when making changes to the project. This includes:
- Logging new features and bug fixes with dates
- Updating the Feature Implementation Tracker
- Documenting architecture decisions
- Recording deployment changes
- Noting any known issues

After completing work, always commit changes and push to the remote repository.

---

## Migration Notes (manual SQL)

### Alembic (schema tracking)

```bash
# Create a new migration (run from /app inside the backend container)
alembic -c /app/alembic.ini revision --autogenerate -m "describe change"

# Apply latest migrations
alembic -c /app/alembic.ini upgrade head
```

### Medication Library + Quick Meds

```sql
ALTER TABLE medications ADD COLUMN auto_start_reminder BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE medications ADD COLUMN is_quick_med BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE medications ADD COLUMN default_route VARCHAR(40);
```

### Recipient Categories + User Profile

```sql
ALTER TABLE care_recipients ADD COLUMN enabled_categories JSONB NOT NULL DEFAULT '["medication","feeding","diaper","demeanor","observation"]';
ALTER TABLE users ADD COLUMN display_name VARCHAR(100);
ALTER TABLE users ADD COLUMN avatar_filename VARCHAR(255);
```

### Reminder Notifications (Backend)

```sql
ALTER TABLE medication_reminders ADD COLUMN last_notified_at timestamp;

CREATE TABLE IF NOT EXISTS push_subscriptions (
  id uuid PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES users(id),
  endpoint varchar(2048) NOT NULL UNIQUE,
  p256dh varchar(255) NOT NULL,
  auth varchar(255) NOT NULL,
  expiration_time timestamp NULL,
  created_at timestamp NOT NULL DEFAULT now(),
  updated_at timestamp NOT NULL DEFAULT now()
);
```

### User Invites + Recipient Access

```sql
CREATE TABLE IF NOT EXISTS user_invites (
  id uuid PRIMARY KEY,
  token varchar(128) NOT NULL UNIQUE,
  email varchar(255),
  username varchar(50),
  role varchar(20) NOT NULL DEFAULT 'caregiver',
  recipient_ids jsonb NOT NULL DEFAULT '[]',
  expires_at timestamp NOT NULL,
  used_at timestamp NULL,
  created_by_user_id uuid NOT NULL REFERENCES users(id),
  created_at timestamp NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_recipient_access (
  id uuid PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES users(id),
  recipient_id uuid NOT NULL REFERENCES care_recipients(id),
  CONSTRAINT uniq_user_recipient UNIQUE (user_id, recipient_id)
);
```

### Quick Feeds Name (optional)

```sql
ALTER TABLE quick_feeds ADD COLUMN name varchar(120);
```

Quick meds migration (one-time):

```bash
docker compose -f docker-compose.prod.yml exec backend \
  sh -lc "PYTHONPATH=/app python /app/scripts/migrate_quick_meds_to_medications.py"
```

When adding care recipients:

```sql
CREATE TABLE IF NOT EXISTS care_recipients (
  id uuid PRIMARY KEY,
  name varchar(100) NOT NULL,
  is_active boolean NOT NULL DEFAULT true,
  created_by_user_id uuid NOT NULL REFERENCES users(id),
  created_at timestamp NOT NULL DEFAULT now(),
  updated_at timestamp NOT NULL DEFAULT now()
);

ALTER TABLE events ADD COLUMN IF NOT EXISTS recipient_id uuid REFERENCES care_recipients(id);
ALTER TABLE quick_medications ADD COLUMN IF NOT EXISTS recipient_id uuid REFERENCES care_recipients(id);
ALTER TABLE quick_feeds ADD COLUMN IF NOT EXISTS recipient_id uuid REFERENCES care_recipients(id);
```

If you already have events/templates, create at least one recipient and backfill:

```sql
-- Replace with the recipient you want as default
UPDATE events SET recipient_id = '<recipient-id>' WHERE recipient_id IS NULL;
UPDATE quick_medications SET recipient_id = '<recipient-id>' WHERE recipient_id IS NULL;
UPDATE quick_feeds SET recipient_id = '<recipient-id>' WHERE recipient_id IS NULL;
```

---

### 2026-01-16 - Phase 6: Offline-First Architecture Complete ✓

#### Offline-First Implementation
- [x] Created offline store with LocalForage (IndexedDB) for events, queue, and cache
- [x] Implemented custom service worker with Workbox strategies:
  - NetworkFirst for API calls with background sync
  - CacheFirst for images
  - StaleWhileRevalidate for static assets
- [x] Built sync status indicator component with visual feedback
- [x] Updated all API functions to support offline caching and queueing
- [x] Enhanced auth store with dual persistence (localStorage + IndexedDB)
- [x] Added offline detection and banner in dashboard
- [x] Created SVG-based PWA icons (icon.svg, favicon.svg)

#### Files Added/Modified
- `frontend/src/lib/stores/offline.js` - New offline state management
- `frontend/src/service-worker.js` - Custom Workbox service worker
- `frontend/src/lib/components/SyncStatus.svelte` - Sync status indicator
- `frontend/src/lib/services/api.js` - Offline-first API patterns
- `frontend/src/lib/stores/auth.js` - Enhanced auth persistence
- `frontend/src/routes/+page.svelte` - Added SyncStatus and offline banner
- `frontend/vite.config.js` - Updated PWA config for injectManifest
- `frontend/package.json` - Added workbox dependencies
- `frontend/static/icon.svg` - PWA icon
- `frontend/static/favicon.svg` - Favicon
- `frontend/src/app.html` - Updated icon references

---

### 2026-01-16 - Phase 7: Photo Attachments Complete ✓

#### Photo Attachments Implementation
- [x] Created Photo model with UUID, event relationship, and metadata
- [x] Built image processing service with:
  - EXIF GPS stripping for privacy
  - Automatic image compression (target 500KB)
  - Thumbnail generation (200x200)
  - MIME type validation
  - Orientation correction from EXIF data
- [x] Created photo API endpoints:
  - POST /api/photos/ - Upload photo with multipart form
  - GET /api/photos/event/{event_id} - List photos for event
  - GET /api/photos/{photo_id} - Get single photo
  - DELETE /api/photos/{photo_id} - Delete photo
  - GET /api/photos/count/{event_id} - Get photo count for event
- [x] Built PhotoCapture component with:
  - Camera capture via native input
  - Gallery picker for existing photos
  - Client-side compression using Canvas API
  - Preview with file size display
  - Progress indicator during compression
- [x] Built PhotoGallery component with:
  - Thumbnail grid display
  - Lightbox for full-size viewing
  - Keyboard navigation (arrow keys, escape)
  - Delete with confirmation
- [x] Integrated photo capture into QuickEntry (observation and diaper forms)
- [x] Integrated photo gallery into EventList edit modal
- [x] Added offline photo queue:
  - Queue photos for upload when offline
  - Auto-sync when connection restored
  - Handle temp event ID mapping after event sync

#### Files Added
- `backend/models/photo.py` - Photo SQLAlchemy model
- `backend/routes/photos.py` - Photo CRUD endpoints
- `backend/services/image_service.py` - Image processing service
- `frontend/src/lib/components/PhotoCapture.svelte` - Camera/file capture UI
- `frontend/src/lib/components/PhotoGallery.svelte` - Photo display grid

#### Files Modified
- `backend/models/__init__.py` - Added Photo export
- `backend/main.py` - Registered photos router
- `frontend/src/lib/stores/offline.js` - Added photo queue functions
- `frontend/src/lib/services/api.js` - Added photo API functions
- `frontend/src/lib/components/QuickEntry.svelte` - Added PhotoCapture integration
- `frontend/src/lib/components/EventList.svelte` - Added PhotoGallery integration

---

### 2026-01-17 - Phase 8: Medication Reminders + Library (In Progress)

#### Medication Library + Reminders
- [x] Added Medication library model + admin UI (dose/unit/route, interval, early warning)
- [x] Added Medication Reminder model + API endpoints
- [x] Added dashboard reminder banner (top 3 with show more, log now, skip)
- [x] Early-dose warning (±15 min window) in Quick Entry and reminder banner
- [x] Auto-start reminder when a med is logged (optional toggle in Medication Library)
- [x] Unified quick meds with Medication Library (quick-med flag)
- [x] Quick med tap auto-logs event using med defaults + route
- [x] Reminder cleanup on med deletion and event deletion
- [x] Real-time reminder refresh on med deletion (SSE broadcast)

#### Files Added
- `backend/models/medication.py` - Medication library model
- `backend/models/med_reminder.py` - Medication reminder model
- `backend/routes/medications.py` - Medication library CRUD
- `backend/routes/med_reminders.py` - Reminder CRUD + early check + next due
- `backend/services/med_reminder_service.py` - Reminder calculations + updates
- `backend/scripts/migrate_quick_meds_to_medications.py` - One-time migration

#### Files Modified
- `backend/routes/events.py` - Update reminders on med create/delete
- `backend/main.py` - Registered medication routes
- `frontend/src/routes/admin/+page.svelte` - Medication library + reminder UI
- `frontend/src/routes/+page.svelte` - Reminder banner + early check
- `frontend/src/lib/components/QuickEntry.svelte` - Med dropdown, quick med auto-log, early warning
- `frontend/src/lib/services/api.js` - Medication/reminder API helpers

### 2026-01-19 - Bug Fix: Reminder Disable Respected

#### Fixed
- [x] Stop re-enabling disabled medication reminders when logging meds
- [x] Stop flipping reminder enabled state during event delete reconciliation
- [x] Disabling "Start reminder when logged" turns off existing reminders for that medication
- [x] Auto-start off now always disables reminders (even if previously off)
- [x] Prevent caching `/api/med-reminders/next` to avoid stale reminder banners
- [x] Bump service worker cache versions to force refresh
- [x] Applied pending DB migrations for profile/recipient/med fields

### 2026-01-19 - Alembic Migrations Added

#### Completed
- [x] Added Alembic configuration in `backend/alembic` and `backend/alembic.ini`
- [x] Added Alembic dependency to backend requirements
- [x] Created baseline Alembic revision and stamped DB head

### 2026-01-20 - Admin Invite UX Fixes

#### Fixed
- [x] Copy invite link now ignores click events and copies the actual URL
- [x] Added copy feedback indicator for invite link
- [x] Copy button now changes to "Copied" for the specific invite link
- [x] Added invitee name field to invite creation and pending invite list

### 2026-01-20 - Dashboard Mobile Formatting

#### Updated
- [x] Shortened dashboard event timestamp format and allowed wrapping on small screens

### 2026-01-21 - User Settings + Password Reset (In Progress)

#### Added
- [x] User settings page (email + password updates)
- [x] Device push enable/disable controls for caregivers/admins
- [x] Forgot password + reset password frontend routes
- [x] Backend endpoints for email/password updates and reset token flow
- [x] SMTP configuration placeholders in .env.example

### 2026-01-21 - Production Access Fix

#### Fixed
- [x] Resolved Vite host allowlist block for caredocs.apvinyldesigns.com by adding it to `server.allowedHosts` in `frontend/vite.config.js`
- [x] Rebuilt production containers to apply the change (nginx reverse proxy preserved)

### 2026-01-22 - Continuous Feed Naming + Quick Feed Templates (In Progress)

#### Added
- [x] Optional continuous feed name captured on start and stored in event metadata
- [x] Dashboard banner + recent events now show feed name, rate, dose, and interval
- [x] Quick feed templates support an optional name (UI + API)
- [x] Dark mode quick template text contrast improved for rate/dose details

### 2026-01-16 - Consistent Navigation Across All Pages

#### Navigation Updates
- [x] Added `href` prop to LogoMark.svelte for clickable logo linking to dashboard
- [x] Updated Dashboard page to include "Dashboard" menu item and clickable logo
- [x] Updated History page with hamburger menu navigation (replaced "Back" button)
- [x] Updated Admin page with hamburger menu navigation (replaced "Back to Dashboard" button)
- [x] Updated Register page with hamburger menu navigation (replaced inline back link)

#### Navigation Pattern (all authenticated pages)
- Hamburger menu (left) - opens slide-out menu with Dashboard, History, Admin Panel (if admin), Logout
- Logo (center) - clickable, links to dashboard (serves as refresh in PWA)
- Theme toggle (right) - dark/light mode switch

---

### 2026-01-15 - Bug Fixes & Diaper Form Enhancements

#### Bug Fixes
- [x] Removed `mem_reservation` from docker-compose.prod.yml (not supported on Raspberry Pi kernel)
- [x] Fixed datetime comparison bug in continuous feed stop endpoint (timezone-aware vs naive datetime)
  - Added check to ensure `started_at` is UTC-aware before comparison with `stop_time`

#### Diaper Change Form Enhancements
- [x] Changed diaper type from dropdown to button-based selection (Wet/Dirty/Both)
- [x] Added conditional size buttons (Small/Medium/Large) - shown for wet, dirty, or both
- [x] Added conditional consistency buttons (Loose/Semi-firm/Firm/Good) - shown only for dirty or both
- [x] Updated EventList display to show size and consistency in event summary
- [x] Updated edit modal with button-based editing matching QuickEntry form

---

## Quick Setup Guide

### Raspberry Pi Production Deployment

```bash
# 1. Clone and navigate to project
cd ~/Docker/care-docs-app
git pull origin main

# 2. Configure environment
cd .
nano .env  # Set JWT_SECRET_KEY, DB_PASSWORD, PUBLIC_API_URL, CORS_ORIGINS

# 3. Start services
docker compose -f docker-compose.prod.yml up -d --build

# 4. Create admin user via web browser
# Open: http://192.168.1.101:8000/setup.html
# Fill in admin credentials and submit

# 5. Access the application
# Frontend: http://192.168.1.101:3000
# Backend API: http://192.168.1.101:8000/docs
```

### Development Environment (Local)

```bash
cd /Users/jackhenryinvestments/Documents/Code/care-docs-app

# Start all services
docker compose up --build

# Create first admin user via browser
# Open: http://localhost:8000/setup.html

# OR use CLI method:
docker compose exec backend python create_admin.py

# Access the app
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

### Stopping the Environment

```bash
# Stop all containers
docker compose down

# Stop and remove all data (database will be reset)
docker compose down -v
```
