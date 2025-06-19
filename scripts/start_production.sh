#!/bin/bash

# Production startup script for Financial Dashboard

set -e

echo "🚀 Starting Financial Dashboard in Production Mode"

# Load production environment
export ENV_FILE=.env.production
if [ -f "$ENV_FILE" ]; then
    export $(cat $ENV_FILE | grep -v '^#' | xargs)
else
    echo "❌ Production environment file not found: $ENV_FILE"
    exit 1
fi

# Check if PostgreSQL is running
echo "✓ Checking PostgreSQL..."
if ! pg_isready -q; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL first."
    exit 1
fi
echo "✅ PostgreSQL is running"

# Check if Redis is running
echo "✓ Checking Redis..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running. Please start Redis first."
    exit 1
fi
echo "✅ Redis is running"

# Run database migrations
echo "✓ Running database migrations..."
alembic upgrade head

# Create necessary directories
mkdir -p logs

# Start services
echo "✓ Starting services..."

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down services..."
    kill $(jobs -p) 2>/dev/null
    exit
}
trap cleanup EXIT

# Start FastAPI backend
echo "  → Starting FastAPI backend..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --env-file $ENV_FILE > logs/backend.log 2>&1 &
sleep 2

# Start Celery worker
echo "  → Starting Celery worker..."
celery -A backend.tasks worker --loglevel=warning > logs/celery.log 2>&1 &
sleep 2

# Start Celery beat
echo "  → Starting Celery beat..."
celery -A backend.tasks beat --loglevel=warning > logs/celery-beat.log 2>&1 &
sleep 2

# Start Streamlit frontend
echo "  → Starting Streamlit frontend..."
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0 > logs/frontend.log 2>&1 &

echo "✅ All services started!"
echo ""
echo "📊 Access the application at:"
echo "   Frontend: http://localhost:8501"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📁 Logs are available in the logs/ directory"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for all background jobs
wait
