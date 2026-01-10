#!/bin/bash

# Deployment script for Care Documentation App on Raspberry Pi
# Run this script on your Raspberry Pi to deploy the application

set -e

echo "====================================="
echo "Care Documentation App - Deployment"
echo "====================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and configure it."
    exit 1
fi

# Pull latest changes
echo "Pulling latest changes from git..."
git pull origin main

# Stop existing containers
echo "Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

# Build and start containers
echo "Building and starting containers..."
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check if services are running
echo "Checking service status..."
docker-compose -f docker-compose.prod.yml ps

# Show logs
echo ""
echo "Deployment complete!"
echo ""
echo "View logs with: docker-compose -f docker-compose.prod.yml logs -f"
echo "Access application at: http://$(hostname -I | awk '{print $1}')"
echo ""
