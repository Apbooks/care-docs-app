# Troubleshooting - Container Name Issue

## Problem: "No such container: care-docs-backend"

This happens because Docker Compose generates container names based on the directory name.

### Solution

**Find the actual container name:**

```bash
docker ps
```

Look for the container running the backend image. The name will be something like:
- `care-docs-app-backend-1`
- `care-docs-app_backend_1`
- `docker-backend-1`

### Create Admin User with Correct Name

Once you find the backend container name from `docker ps`, use it:

```bash
# Replace <container-name> with the actual name from docker ps
docker exec -it <container-name> python create_admin.py
```

**Examples:**
```bash
# If the container is named care-docs-app-backend-1
docker exec -it care-docs-app-backend-1 python create_admin.py

# If the container is named docker-backend-1
docker exec -it docker-backend-1 python create_admin.py

# If the container is named care-docs-app_backend_1
docker exec -it care-docs-app_backend_1 python create_admin.py
```

### Alternative: Use Docker Compose Exec

This automatically finds the correct container:

```bash
docker compose -f docker-compose.prod.yml exec backend python create_admin.py
```

This is the **recommended method** as it doesn't require knowing the exact container name.

---

## Quick Commands Reference

### Check Running Containers
```bash
docker ps
```

### View Logs
```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Just backend
docker compose -f docker-compose.prod.yml logs -f backend
```

### Restart Services
```bash
docker compose -f docker-compose.prod.yml restart
```

### Stop Services
```bash
docker compose -f docker-compose.prod.yml down
```

### Rebuild and Restart
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

---

## Other Common Issues

### Port Already in Use

**Error:** `Bind for 0.0.0.0:3000 failed: port is already allocated`

**Solution:**
```bash
# Find what's using the port
sudo lsof -i :3000

# Stop the conflicting service or change ports in docker-compose.prod.yml
```

### Database Connection Failed

**Check if database container is running:**
```bash
docker ps | grep db
```

**View database logs:**
```bash
docker compose -f docker-compose.prod.yml logs db
```

### API Not Responding

**Check backend logs:**
```bash
docker compose -f docker-compose.prod.yml logs backend
```

**Common causes:**
- Missing or invalid JWT_SECRET_KEY in backend/.env
- Database not ready when backend started
- CORS configuration issues

**Solution:** Check logs and restart backend:
```bash
docker compose -f docker-compose.prod.yml restart backend
```

---

## Getting Help

1. **Check container status:** `docker ps -a`
2. **View logs:** `docker compose -f docker-compose.prod.yml logs`
3. **Verify .env file:** `cat backend/.env` (check JWT_SECRET_KEY is set)
4. **Test API health:** `curl http://localhost:8000/api/health`

If issues persist, include the output of these commands when asking for help.
