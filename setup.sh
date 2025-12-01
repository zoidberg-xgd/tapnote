#!/bin/bash

echo "🚀 Starting TapNote Local Deployment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# 1) Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating default .env file..."
    cp example.env .env
    echo "DEBUG=True" >> .env
    echo "SECRET_KEY=django-insecure-local-setup-key" >> .env
    echo "ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0" >> .env
    echo "PORT=9009" >> .env
fi

# 2) Create necessary directories
echo "fyp Creating directories..."
mkdir -p prototype/helpers
touch prototype/__init__.py
touch prototype/helpers/__init__.py

# 3) Move helper if it exists in root (legacy support)
if [ -f "openai_helper.py" ]; then
    mv openai_helper.py prototype/helpers/
fi

# 4) Build & Run
echo "🏗️  Building Docker container..."
docker-compose build

echo "🚀 Starting container..."
docker-compose up -d

echo ""
echo "✅ Deployment Complete!"
echo "----------------------------------------"
echo "🌍 App is running at: http://localhost:9009"
echo "----------------------------------------"
echo "To view logs: docker-compose logs -f"
echo "To stop:      docker-compose down"
