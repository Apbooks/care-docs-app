# Care Documentation App

A Progressive Web App (PWA) for documenting care activities for individuals with special needs. Track medications, feeding schedules, diaper changes, demeanor, and more with offline support and multi-user access.

## Features

- **Quick Entry Interface**: Fast logging with a floating + button
- **Multi-User Support**: Multiple caregivers can log activities
- **Offline-First**: Works without internet connection, syncs when online
- **Photo Attachments**: Capture and attach photos to entries
- **Historical View**: Filter and search past entries
- **Reminders**: Medication and feeding schedule notifications
- **Export Data**: Export records for doctor appointments
- **Secure**: JWT authentication with HTTP-only cookies
- **Raspberry Pi Ready**: Optimized to run on Raspberry Pi 4B

## Technology Stack

- **Frontend**: SvelteKit + Tailwind CSS + PWA
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL 15
- **Deployment**: Docker Compose + Nginx
- **Offline Storage**: IndexedDB with LocalForage

## Prerequisites

### Development
- Node.js 20+
- Python 3.11+
- Docker and Docker Compose
- 8GB+ RAM
- 10GB disk space

### Raspberry Pi Production
- Raspberry Pi 4B (4GB or 8GB RAM recommended)
- 32GB+ microSD card or USB SSD (SSD strongly recommended)
- Raspbian OS (64-bit)
- Docker and Docker Compose installed

## Quick Start (Production-only on this host)

This host should run **production only**. Nginx Proxy Manager should forward
`caredocs.apvinyldesigns.com` to `http://<host-ip>:8080`.

```bash
cp .env.example .env
# Edit .env (DB_PASSWORD, JWT_SECRET_KEY, PUBLIC_ORIGIN, PUBLIC_API_URL)
docker compose up -d --build
docker compose ps
docker compose logs -f
```

To stop:
```bash
docker compose down
```

Do **not** run the dev stack on this host. Development uses `docker-compose.dev.yml`.

## Quick Start (Development)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/care-docs-app.git
cd care-docs-app
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env with your settings
nano .env
```

**Important**: Generate a secure JWT secret key:

```bash
openssl rand -hex 32
```

### 3. Start Development Environment

```bash
docker compose -f docker-compose.dev.yml up --build
```

This will start:
- PostgreSQL database on port 5432
- FastAPI backend on port 8000
- SvelteKit frontend on port 3000

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Project Structure

```
care-docs-app/
├── backend/                    # FastAPI backend
│   ├── routes/                 # API endpoints
│   ├── models/                 # SQLAlchemy models
│   ├── services/               # Business logic
│   ├── middleware/             # Auth and other middleware
│   ├── main.py                 # FastAPI app entry
│   ├── config.py               # Configuration
│   ├── database.py             # Database setup
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Development Docker image
│   └── Dockerfile.prod         # Production Docker image
├── frontend/                   # SvelteKit frontend
│   ├── src/
│   │   ├── routes/             # SvelteKit routes
│   │   ├── lib/
│   │   │   ├── components/     # Svelte components
│   │   │   ├── stores/         # Svelte stores
│   │   │   └── services/       # Frontend services
│   │   ├── app.html            # HTML template
│   │   └── app.css             # Global styles
│   ├── static/                 # Static assets
│   ├── package.json            # Node dependencies
│   ├── vite.config.js          # Vite + PWA config
│   ├── svelte.config.js        # SvelteKit config
│   ├── tailwind.config.js      # Tailwind CSS config
│   ├── Dockerfile              # Development Docker image
│   └── Dockerfile.prod         # Production Docker image
├── scripts/                    # Deployment scripts
├── docker-compose.yml          # Production configuration (default)
├── docker-compose.dev.yml      # Development configuration
├── nginx.conf                  # Nginx reverse proxy
├── .env.example                # Environment template
├── .gitignore                  # Git exclusions
├── claude.md                   # Development progress
└── README.md                   # This file
```

## Development Workflow

### Backend Development

```bash
# Install dependencies locally (optional, for IDE support)
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run tests
python -m pytest

# Access Python shell with app context
docker compose exec backend python
```

### Frontend Development

```bash
# Install dependencies locally (optional, for IDE support)
cd frontend
npm install

# Run linter
npm run check

# Build for production
npm run build
```

### Database Management

```bash
# Access PostgreSQL
docker compose exec db psql -U careapp -d caredb

# View database logs
docker compose logs db

# Backup database
docker compose exec db pg_dump -U careapp caredb > backup.sql

# Restore database
docker compose exec -T db psql -U careapp caredb < backup.sql
```

## Deployment to Raspberry Pi

### 1. Prepare Raspberry Pi

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin

# Enable swap (2GB)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # Set CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### 2. Clone and Configure

```bash
cd ~
git clone https://github.com/yourusername/care-docs-app.git
cd care-docs-app

# Copy and edit environment variables
cp .env.example .env
nano .env
```

### 3. Generate VAPID Keys for Push Notifications

```bash
# Install web-push globally (on your development machine)
npm install -g web-push

# Generate VAPID keys
web-push generate-vapid-keys

# Copy the keys to your .env file
```

### 4. Build and Start

```bash
docker compose up -d --build
```

### 5. Set Up HTTPS (Optional but Recommended)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Stop containers temporarily
docker compose down

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
sudo mkdir -p ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/

# Edit nginx.conf to uncomment HTTPS server block
nano nginx.conf

# Restart containers
docker compose up -d
```

### 6. Create First Admin User

Once the backend is running, you'll need to create an admin user to access the application. Instructions for this will be added in Phase 2 when authentication is implemented.

## Maintenance

### View Logs

```bash
# All containers
docker compose logs -f

# Specific service
docker compose logs -f backend
```

### Update Application

```bash
cd ~/care-docs-app
git pull origin main
docker compose up -d --build
```

### Automated Backups

Create a backup script that runs daily via cron (instructions in `/scripts/backup.sh` - to be created).

### Monitor Resource Usage

```bash
# Docker stats
docker stats

# System resources
htop
```

## Event Types

The app supports tracking these care activities:

1. **Medication**: Track medication name, dosage, route (oral/tube), and time
2. **Feeding**: Log amount (ml), duration, formula type, and notes
3. **Diaper Change**: Record wet/dry/both, rash presence, skin condition
4. **Demeanor**: Document mood, activity level, and any concerns
5. **General Observation**: Free-form notes with optional photos

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation (Swagger UI).

## Troubleshooting

### Container won't start

```bash
# Check logs
docker compose logs [service-name]

# Rebuild without cache
docker compose up --build --force-recreate
```

### Database connection errors

```bash
# Check database is healthy
docker compose ps

# Check database logs
docker compose logs db

# Verify environment variables
cat .env
```

### Frontend can't reach backend

```bash
# Check network
docker network ls
docker network inspect care-docs-app_default

# Verify backend is running
curl http://localhost:8000/api/health
```

### Out of memory on Raspberry Pi

```bash
# Check memory usage
free -h

# Verify swap is enabled
sudo swapon --show

# Reduce Docker memory limits in docker-compose.yml
```

## Development Progress

See [claude.md](claude.md) for detailed development progress and implementation notes.

## Security Considerations

- All medical data transmitted over HTTPS in production
- JWT tokens stored in HTTP-only cookies (XSS protection)
- SQL injection protection via SQLAlchemy ORM
- EXIF data stripped from uploaded photos
- Regular automated backups
- Rate limiting on authentication endpoints (to be implemented)

## Performance Targets (Raspberry Pi 4B)

- Load time: < 3 seconds
- Memory usage: < 600MB total
- Photo upload: < 10 seconds
- Offline sync: < 5 seconds for 10 events
- Notification delivery: < 1 minute
- Concurrent users: 3+

## Future Enhancements

- Voice entry via Web Speech API
- Medication inventory tracking
- Doctor appointment scheduling
- Vital signs tracking
- Chart generation for medical reports
- Multi-language support
- Dark mode
- Barcode scanning for medications

## Contributing

This is a personal project, but suggestions and improvements are welcome via issues.

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please open a GitHub issue.

## Acknowledgments

Built with love for caregivers everywhere who dedicate themselves to caring for those with special needs.
