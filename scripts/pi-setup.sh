#!/bin/bash
# Quick setup script for Raspberry Pi 4B deployment
# Run this after pulling the latest code

set -e  # Exit on error

echo "=========================================="
echo "Care Docs App - Raspberry Pi Setup"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "Error: docker-compose.prod.yml not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed!"
    echo "Install with: curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not available!"
    echo "Docker Compose v2 should be included with Docker."
    exit 1
fi

echo "✓ Docker is installed"
echo ""

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  No .env file found in backend/"
    echo ""
    echo "Creating .env from template..."
    cp backend/.env.example backend/.env

    echo ""
    echo "Generating secure JWT secret..."
    JWT_SECRET=$(openssl rand -hex 32)

    # Update the .env file with generated secret
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" backend/.env
    else
        # Linux (Raspberry Pi)
        sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" backend/.env
    fi

    # Set production environment
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/DEBUG=.*/DEBUG=false/" backend/.env
        sed -i '' "s/ENVIRONMENT=.*/ENVIRONMENT=production/" backend/.env
    else
        sed -i "s/DEBUG=.*/DEBUG=false/" backend/.env
        sed -i "s/ENVIRONMENT=.*/ENVIRONMENT=production/" backend/.env
    fi

    echo "✓ .env file created with secure JWT secret"
    echo ""
    echo "IMPORTANT: Review backend/.env and update:"
    echo "  - DB_PASSWORD (set a strong password)"
    echo "  - CORS_ORIGINS (add your domain/IP)"
    echo ""
    read -p "Press Enter to continue after reviewing .env file..."
else
    echo "✓ .env file exists"
    echo ""

    # Validate JWT secret
    JWT_SECRET=$(grep "^JWT_SECRET_KEY=" backend/.env | cut -d '=' -f2)
    if [ -z "$JWT_SECRET" ] || [ ${#JWT_SECRET} -lt 32 ]; then
        echo "⚠️  WARNING: JWT_SECRET_KEY in .env is missing or too short!"
        echo ""
        read -p "Generate a new secure JWT secret? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            JWT_SECRET=$(openssl rand -hex 32)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" backend/.env
            else
                sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" backend/.env
            fi
            echo "✓ New JWT secret generated and saved"
        fi
    else
        echo "✓ JWT_SECRET_KEY is configured"
    fi
fi

echo ""
echo "=========================================="
echo "Building and starting Docker containers..."
echo "=========================================="
echo ""

# Stop any running containers
docker compose -f docker-compose.prod.yml down 2>/dev/null || true

# Build and start containers
docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo "Waiting for services to start..."
sleep 10

# Check container status
echo ""
echo "Container Status:"
docker compose -f docker-compose.prod.yml ps

echo ""
echo "=========================================="
echo "Testing API connectivity..."
echo "=========================================="
echo ""

# Wait for API to be ready
max_attempts=30
attempt=0
until curl -s http://localhost:8000/api/health > /dev/null 2>&1 || [ $attempt -eq $max_attempts ]; do
    attempt=$((attempt + 1))
    echo "Waiting for API... (attempt $attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ API failed to start. Check logs with: docker compose logs backend"
    exit 1
fi

echo "✓ API is running!"
echo ""

# Test API health
HEALTH_RESPONSE=$(curl -s http://localhost:8000/api/health)
echo "Health check response: $HEALTH_RESPONSE"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Services are running:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "Next Steps:"
echo ""
echo "1. Create an admin user:"
echo "   docker exec -it care-docs-backend python create_admin.py"
echo ""
echo "2. Access the application:"
echo "   http://localhost:3000/login"
echo ""
echo "3. View logs (if needed):"
echo "   docker compose -f docker-compose.prod.yml logs -f"
echo ""
echo "4. Stop the application:"
echo "   docker compose -f docker-compose.prod.yml down"
echo ""

# Offer to create admin user now
echo ""
read -p "Create admin user now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    docker exec -it care-docs-backend python create_admin.py
    echo ""
    echo "=========================================="
    echo "You can now log in at: http://localhost:3000/login"
    echo "=========================================="
fi

echo ""
echo "For detailed deployment information, see DEPLOYMENT_GUIDE.md"
echo ""
