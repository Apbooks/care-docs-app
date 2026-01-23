#!/bin/bash

# Database backup script for Care Documentation App
# Schedule with cron: 0 2 * * * /path/to/backup.sh

# Configuration
BACKUP_DIR="/home/pi/care-docs-app/backups"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="caredb_backup_${DATE}.sql"
DAYS_TO_KEEP=30

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup database
echo "Starting backup at $(date)"
docker compose -f /home/pi/care-docs-app/docker-compose.yml exec -T db \
  pg_dump -U careapp caredb > "${BACKUP_DIR}/${BACKUP_FILE}"

# Compress backup
gzip "${BACKUP_DIR}/${BACKUP_FILE}"

# Delete old backups
find "$BACKUP_DIR" -name "caredb_backup_*.sql.gz" -mtime +${DAYS_TO_KEEP} -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
echo "Backup size: $(du -h ${BACKUP_DIR}/${BACKUP_FILE}.gz | cut -f1)"

# Clean up old backups count
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "caredb_backup_*.sql.gz" | wc -l)
echo "Total backups: ${BACKUP_COUNT}"
