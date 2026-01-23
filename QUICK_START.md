# Quick Start - Raspberry Pi Deployment

## Production-Only (Recommended on this host)

This host should run **production only**. The reverse proxy (Nginx Proxy Manager) points to
`http://localhost:8080`, which is the nginx container in `docker-compose.yml`.

### Start / Stop / Status
```bash
docker compose up -d --build
docker compose ps
docker compose logs -f
docker compose down
```

### One-time checks
- Ensure `.env` exists at repo root and includes `DB_PASSWORD`, `JWT_SECRET_KEY`, `PUBLIC_ORIGIN`, `PUBLIC_API_URL`.
- NPM should proxy `caredocs.apvinyldesigns.com` → `http://<host-ip>:8080`

### Do not run dev on this host
The dev stack (`docker-compose.dev.yml`) uses ports 3000/8000 and will collide with production.
Run it on a different machine if needed.

## What Was Fixed

All critical bugs blocking the application have been fixed and pushed to GitHub:

✅ **Metadata field mismatch** - Events API now works correctly
✅ **Authentication broken** - Cookie-based auth now functional
✅ **Insecure JWT secret** - Now requires secure 32+ character key
✅ **Cookie security** - Enabled for production HTTPS
✅ **CORS hardcoded** - Now configurable via environment

**Commits pushed:**
- `2246def` - Critical bug fixes
- `43401d3` - Deployment guide
- `9c5793b` - Automated setup script

---

## Deploy to Raspberry Pi (Simple Method)

### On Your Raspberry Pi:

```bash
# 1. Pull latest code
cd /path/to/care-docs-app
git pull origin main

# 2. Run automated setup script
./scripts/pi-setup.sh
```

The script will:
- Check Docker installation
- Create and configure `.env` file with secure JWT secret
- Build and start all containers
- Test API connectivity
- Guide you through admin user creation

**That's it!** 🎉

Access your app at: `http://<raspberry-pi-ip>:3000`

---

## Deploy to Raspberry Pi (Manual Method)

If you prefer manual control:

```bash
# 1. Pull latest code
git pull origin main

# 2. Create .env file
cp .env.example .env

# 3. Generate JWT secret and edit .env
openssl rand -hex 32
nano .env  # Paste the generated key as JWT_SECRET_KEY

# 4. Start Docker containers
docker compose up -d --build

# 5. Create admin user
docker compose exec backend python create_admin.py
```

---

## What You Need to Know

### Required Environment Variable

The app **will not start** without a valid `JWT_SECRET_KEY` in `.env`:

```env
JWT_SECRET_KEY=<32+ character secure random string>
```

Generate one with: `openssl rand -hex 32`

### Production Settings

For production deployment, set in `.env`:

```env
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=http://localhost:3000,https://your-domain.com
```

### Accessing the App

Once deployed:
- **Frontend**: http://\<raspberry-pi-ip\>:3000
- **Backend API**: http://\<raspberry-pi-ip\>:8000
- **API Docs**: http://\<raspberry-pi-ip\>:8000/docs

---

## Troubleshooting

### "SECURITY ERROR: Insecure JWT_SECRET_KEY detected!"

You need to set a valid JWT secret:
```bash
openssl rand -hex 32
# Add the output to backend/.env as JWT_SECRET_KEY=<output>
```

### "Not authenticated" errors

Clear browser cookies and log in again. The authentication fix resolves cookie extraction.

### CORS errors

Add your IP/domain to `CORS_ORIGINS` in `backend/.env`:
```env
CORS_ORIGINS=http://192.168.1.100:3000,https://mydomain.com
```

### Container won't start

Check logs:
```bash
docker compose logs backend
```

---

## Next Steps After Deployment

1. **Create additional users**: Admin can register caregivers at `/register`
2. **Set up HTTPS**: See `DEPLOYMENT_GUIDE.md` for SSL configuration
3. **Enable backups**: Configure automated daily backups with `scripts/backup.sh`
4. **Monitor performance**: Use `docker stats` to check resource usage

---

## Important Files

- `DEPLOYMENT_GUIDE.md` - Comprehensive deployment documentation
- `scripts/pi-setup.sh` - Automated setup script
- `.env.example` - Environment variable template
- `docker-compose.yml` - Production Docker configuration (default)
- `docker-compose.dev.yml` - Development Docker configuration

---

## Support

For detailed troubleshooting, deployment options, and configuration:
👉 See `DEPLOYMENT_GUIDE.md`

For code review findings and remaining improvements:
👉 See `.claude/plans/eager-churning-babbage.md`

---

**Ready to deploy!** All critical issues are resolved. 🚀
