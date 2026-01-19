-- Idempotent migration for profile fields, recipient categories, and medication fields.

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS display_name VARCHAR(100),
  ADD COLUMN IF NOT EXISTS avatar_filename VARCHAR(255);

ALTER TABLE care_recipients
  ADD COLUMN IF NOT EXISTS enabled_categories JSONB NOT NULL
  DEFAULT '["medication","feeding","diaper","demeanor","observation"]'::jsonb;

ALTER TABLE medications
  ADD COLUMN IF NOT EXISTS default_route VARCHAR(40),
  ADD COLUMN IF NOT EXISTS is_quick_med BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS auto_start_reminder BOOLEAN NOT NULL DEFAULT FALSE;
