#!/bin/bash

# Financial Dashboard Task Queue Startup Script

set -e

echo "🚀 Starting Financial Dashboard Task Queue Components..."

# Check if Redis is running
if ! command -v redis-cli &> /dev/null; then
    echo "❌ Redis CLI not found. Please install Redis."
    exit 1
fi

if ! redis-cli ping &> /dev/null; then
    echo "❌ Redis is not running. Please start Redis first."
    echo "   macOS (Homebrew): brew services start redis"
    echo "   Linux: sudo systemctl start redis"
    echo "   Docker: docker run -d -p 6379:6379 redis:7-alpine"
    exit 1
fi

echo "✅ Redis is running"

# Set up environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export CELERY_BROKER_URL="${CELERY_BROKER_URL:-redis://localhost:6379/0}"
export CELERY_RESULT_BACKEND="${CELERY_RESULT_BACKEND:-redis://localhost:6379/0}"

# Create logs directory
mkdir -p logs

echo "📋 Starting task queue components..."

# Function to kill background processes on exit
cleanup() {
    echo "🛑 Stopping task queue components..."
    jobs -p | xargs -r kill
    wait
    echo "✅ All components stopped"
}

trap cleanup EXIT

# Start Celery worker
echo "🔧 Starting Celery worker..."
celery -A backend.tasks worker --loglevel=info --logfile=logs/celery_worker.log &
WORKER_PID=$!

# Start Celery beat scheduler
echo "⏰ Starting Celery beat scheduler..."
celery -A backend.tasks beat --loglevel=info --logfile=logs/celery_beat.log &
BEAT_PID=$!

# Start Flower monitoring (optional)
if command -v flower &> /dev/null; then
    echo "🌸 Starting Flower monitoring on http://localhost:5555..."
    celery -A backend.tasks flower --port=5555 --logfile=logs/flower.log &
    FLOWER_PID=$!
else
    echo "⚠️  Flower not available. Install with: pip install flower"
fi

echo ""
echo "🎉 Task queue components started successfully!"
echo ""
echo "📊 Monitoring URLs:"
echo "   - Flower (if available): http://localhost:5555"
echo ""
echo "📝 Log files:"
echo "   - Worker logs: logs/celery_worker.log"
echo "   - Beat logs: logs/celery_beat.log"
echo "   - Flower logs: logs/flower.log"
echo ""
echo "🔧 Management commands:"
echo "   - List active tasks: python backend/tasks/cli.py list-active"
echo "   - Worker stats: python backend/tasks/cli.py worker-stats"
echo "   - Update prices: python backend/tasks/cli.py update-prices"
echo "   - Fetch market data: python backend/tasks/cli.py fetch-market-data -s AAPL -s GOOGL"
echo ""
echo "Press Ctrl+C to stop all components..."

# Wait for any background process to exit
wait
