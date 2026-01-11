# Raspberry Pi 4B Deployment Guide

## Critical Fixes Applied ✓

All critical bugs have been fixed and pushed to GitHub. You can now safely deploy to your Raspberry Pi.

**Commit**: `2246def` - Fix critical bugs blocking authentication and event operations

---

## Pre-Deployment Checklist on Raspberry Pi

### 1. Pull Latest Changes

```bash
# On your Raspberry Pi
cd /path/to/care-docs-app
git pull origin main
```

### 2. Create Environment File (REQUIRED)

The application will **not start** without a proper `.env` file with a secure JWT secret.

```bash
# Navigate to backend directory
cd backend

# Copy the example file
cp .env.example .env

# Generate a secure JWT secret
openssl rand -hex 32

# Edit the .env file
nano .env
```

**Required .env Configuration:**

```env
# Database Configuration
DB_PASSWORD=your-secure-database-password

# JWT Configuration - REQUIRED! Paste your generated key here
JWT_SECRET_KEY=<paste-your-generated-32-byte-key-here>

# Application Settings
DEBUG=false
ENVIRONMENT=production
CORS_ORIGINS=http://localhost:3000,https://your-domain.com

# Web Push Notifications (optional for initial deployment)
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
VAPID_CLAIM_EMAIL=admin@example.com

# File Upload
MAX_PHOTO_SIZE_MB=10
```

**Important:**
- Replace `<paste-your-generated-32-byte-key-here>` with output from `openssl rand -hex 32`
- Set `ENVIRONMENT=production` for secure HTTPS cookies
- Update `CORS_ORIGINS` if using a custom domain
- Choose a strong `DB_PASSWORD` different from the example

---

## Deployment Steps

### 3. Start Docker Services

```bash
# From the project root directory
cd /path/to/care-docs-app

# Start all services (database, backend, frontend)
docker compose -f docker-compose.prod.yml up -d --build

# Check that all containers are running
docker compose ps
```

Expected output:
```
NAME                   STATUS    PORTS
care-docs-backend      running   0.0.0.0:8000->8000/tcp
care-docs-frontend     running   0.0.0.0:3000->3000/tcp
care-docs-db           running   5432/tcp
```

### 4. Create First Admin User

```bash
# Run the admin creation script inside the backend container
docker compose -f docker-compose.prod.yml exec backend python create_admin.py
```

Follow the interactive prompts:
- Enter username (e.g., `admin`)
- Enter email (e.g., `admin@example.com`)
- Enter password (minimum 6 characters, max 72 bytes)
- Confirm password

You should see:
```
✓ Admin user created successfully!
```

### 5. Verify Deployment

**Test the Backend API:**
```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{"status":"healthy","message":"Care Documentation API is running"}
```

**Test the Frontend:**

Open a browser on your Raspberry Pi or another device on the same network:
- Frontend: `http://<raspberry-pi-ip>:3000`
- Backend API Docs: `http://<raspberry-pi-ip>:8000/docs`

### 6. Test Login

1. Navigate to `http://<raspberry-pi-ip>:3000/login`
2. Enter the admin credentials you created
3. You should be redirected to the dashboard
4. Try creating a test event (medication, feeding, etc.)

---

## Post-Deployment Configuration

### Enable HTTPS (Recommended for Production)

The nginx configuration includes commented-out HTTPS settings. To enable:

1. Obtain SSL certificates (Let's Encrypt recommended)
2. Edit `nginx/nginx.conf`
3. Uncomment the HTTPS server block
4. Update certificate paths
5. Restart nginx: `docker compose restart nginx`

### Automated Backups

The backup script is located at `scripts/backup.sh`. To schedule daily backups:

```bash
# On Raspberry Pi, edit crontab
crontab -e

# Add this line for daily backups at 2 AM
0 2 * * * /path/to/care-docs-app/scripts/backup.sh
```

---

## Troubleshooting

### Application Won't Start

**Error: "SECURITY ERROR: Insecure JWT_SECRET_KEY detected!"**

Solution: You didn't set a valid JWT secret in `.env`. Generate one:
```bash
openssl rand -hex 32
```
Add it to `backend/.env` as `JWT_SECRET_KEY=<your-generated-key>`

**Error: "Connection to database failed"**

Solution: Check that PostgreSQL container is running:
```bash
docker compose ps
docker compose logs db
```

### Authentication Issues

**Error: "Not authenticated" or "Could not validate credentials"**

Solution: Clear browser cookies and try logging in again. The cookie extraction fix should resolve this.

**Error: CORS policy blocking requests**

Solution: Add your domain/IP to `CORS_ORIGINS` in `backend/.env`:
```env
CORS_ORIGINS=http://localhost:3000,http://192.168.1.100:3000,https://yourdomain.com
```
Then restart: `docker compose restart backend`

### Event Operations Failing

**Error: 500 Internal Server Error when viewing/updating events**

Solution: This was the metadata field mismatch bug - it's now fixed in commit `2246def`. Make sure you pulled the latest code.

---

## Monitoring & Logs

### View Application Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

### Check Resource Usage

```bash
# Container stats
docker stats

# System resources
htop
```

### Database Access

```bash
# Connect to PostgreSQL
docker exec -it care-docs-db psql -U careapp -d caredb

# Useful queries
SELECT * FROM users;
SELECT COUNT(*) FROM events;
SELECT type, COUNT(*) FROM events GROUP BY type;
```

---

## Performance Optimization (Raspberry Pi Specific)

The production docker-compose is already optimized for Raspberry Pi 4B:

- PostgreSQL: Limited to 256MB shared_buffers
- Backend: Uvicorn with 2 workers
- Frontend: Pre-built static files served by nginx
- Total memory target: < 600MB

If experiencing performance issues:

1. **Reduce database connections**: Edit `backend/database.py`, set `pool_size=5`
2. **Disable debug logging**: Ensure `DEBUG=false` in `.env`
3. **Monitor memory**: Run `free -h` to check available RAM

---

## Security Best Practices

✅ **Already Implemented:**
- HTTP-only cookies for JWT tokens
- Secure cookie flag enabled in production
- Strong JWT secret requirement (32+ characters)
- Environment-based CORS configuration
- Bcrypt password hashing

🔒 **Recommended Next Steps:**
1. Enable HTTPS with Let's Encrypt
2. Set up firewall rules (ufw or iptables)
3. Implement rate limiting (add to high-priority fixes)
4. Regular automated backups
5. Keep Docker images updated

---

## Updating the Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart containers
docker compose -f docker-compose.prod.yml up -d --build

# Check logs for any errors
docker compose logs -f
```

---

## Quick Reference

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Main application UI |
| Backend API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| Database | localhost:5432 | PostgreSQL (internal only) |

**Default Credentials:** Set during `create_admin.py` step

**Data Location:** Docker volumes (persistent across restarts)
- Database: `care-docs-db-data`
- Photos: `./backend/photos`

---

## Support

If you encounter issues not covered here:

1. Check application logs: `docker compose logs -f backend`
2. Review the commit message for breaking changes
3. Verify all environment variables are set correctly
4. Ensure JWT_SECRET_KEY is 32+ characters and unique

**Critical Files Modified:**
- `backend/config.py` - JWT secret validation
- `backend/routes/auth.py` - Cookie-based authentication
- `backend/routes/events.py` - Metadata field fix
- `backend/main.py` - CORS configuration

All fixes are documented in commit `2246def`.

---

**Last Updated:** 2026-01-10
**Tested On:** Raspberry Pi 4B (4GB RAM)
**Docker Version:** 20.10+
**Docker Compose Version:** 2.0+
