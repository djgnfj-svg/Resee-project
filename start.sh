#!/bin/bash

# Simple start script for Resee
echo "🚀 Starting Resee..."

# Start all services
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 15

# Run migrations
echo "🔄 Running migrations..."
docker-compose exec -T backend python manage.py migrate

echo "✅ Resee is ready!"
echo "🌐 Main App: http://localhost (nginx)"
echo "📱 Frontend Direct: http://localhost:3000"
echo "🔧 Backend Direct: http://localhost:8000"
echo "📊 RabbitMQ Admin: http://localhost:15672 (resee/resee_password)"

echo ""
echo "📝 Useful commands:"
echo "  Stop: docker-compose down"
echo "  Logs: docker-compose logs -f"
echo "  Status: docker-compose ps"