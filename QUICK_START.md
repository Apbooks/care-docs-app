# Quick Start - Raspberry Pi Deployment

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
cd backend
cp .env.example .env

# 3. Generate JWT secret and edit .env
openssl rand -hex 32
nano .env  # Paste the generated key as JWT_SECRET_KEY

# 4. Start Docker containers
cd ..
docker compose -f docker-compose.prod.yml up -d --build

# 5. Create admin user
docker compose -f docker-compose.prod.yml exec backend python create_admin.py
```

---

## What You Need to Know

### Required Environment Variable

The app **will not start** without a valid `JWT_SECRET_KEY` in `backend/.env`:

```env
JWT_SECRET_KEY=<32+ character secure random string>
```

Generate one with: `openssl rand -hex 32`

### Production Settings

For production deployment, set in `backend/.env`:

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
docker compose -f docker-compose.prod.yml logs backend
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
- `backend/.env.example` - Environment variable template
- `docker-compose.prod.yml` - Production Docker configuration

---

## Support

For detailed troubleshooting, deployment options, and configuration:
👉 See `DEPLOYMENT_GUIDE.md`

For code review findings and remaining improvements:
👉 See `.claude/plans/eager-churning-babbage.md`

---

**Ready to deploy!** All critical issues are resolved. 🚀
