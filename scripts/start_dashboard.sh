#!/bin/bash

# Financial Dashboard Startup Script
# This script starts the backend API and frontend Streamlit app

echo "🚀 Starting Financial Dashboard..."
echo ""

# Set environment variables if not already set
export BACKEND_URL=${BACKEND_URL:-"http://localhost:8000"}
export DATABASE_URL=${DATABASE_URL:-"postgresql://user:password@localhost:5432/financial_dashboard"}
export REDIS_URL=${REDIS_URL:-"redis://localhost:6379/0"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📊 Financial Dashboard Startup${NC}"
echo "=================================="
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: docker-compose.yml not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Function to check if a service is running
check_service() {
    local service_name=$1
    local port=$2
    
    if curl -s "http://localhost:$port/health" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name is running${NC}"
        return 0
    else
        echo -e "${YELLOW}⏳ $service_name is starting...${NC}"
        return 1
    fi
}

# Start Docker services
echo -e "${BLUE}🐳 Starting Docker services...${NC}"
docker-compose up -d

echo ""
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 10

# Check backend health
echo ""
echo -e "${BLUE}🔍 Checking service health...${NC}"

# Wait for backend to be ready
for i in {1..30}; do
    if check_service "Backend API" 8000; then
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Backend API failed to start${NC}"
        exit 1
    fi
    sleep 2
done

# Check if Redis is accessible
if redis-cli ping >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${YELLOW}⚠️  Redis check failed (may still work via Docker)${NC}"
fi

# Check if Flower is accessible
if curl -s "http://localhost:5555" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Flower UI is running${NC}"
else
    echo -e "${YELLOW}⚠️  Flower UI check failed${NC}"
fi

echo ""
echo -e "${BLUE}📱 Starting Streamlit frontend...${NC}"

# Start Streamlit in the background
cd frontend
streamlit run app.py --server.port 8501 --server.address localhost &
STREAMLIT_PID=$!

# Wait a moment for Streamlit to start
sleep 5

echo ""
echo -e "${GREEN}🎉 Financial Dashboard is ready!${NC}"
echo "=================================="
echo ""
echo -e "${BLUE}🌐 Service URLs:${NC}"
echo "• Frontend Dashboard: http://localhost:8501"
echo "• Backend API: http://localhost:8000"
echo "• API Documentation: http://localhost:8000/docs"
echo "• Task Monitor (Flower): http://localhost:5555"
echo "• Redis: localhost:6379"
echo "• PostgreSQL: localhost:5432"
echo ""
echo -e "${BLUE}📋 Available Pages:${NC}"
echo "• Dashboard: Portfolio overview with real-time data"
echo "• Portfolio: Manage positions and add new investments"
echo "• Tasks: Monitor background tasks and submit new ones"
echo "• Analytics: Performance metrics and risk analysis"
echo "• Settings: Configure data sources and preferences"
echo ""
echo -e "${YELLOW}💡 Quick Actions:${NC}"
echo "• Press Ctrl+C to stop the frontend"
echo "• Run 'docker-compose logs -f' to view backend logs"
echo "• Run 'docker-compose down' to stop all services"
echo ""

# Function to handle cleanup
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down...${NC}"
    
    # Kill Streamlit
    if [ ! -z "$STREAMLIT_PID" ]; then
        kill $STREAMLIT_PID 2>/dev/null
        echo -e "${GREEN}✅ Frontend stopped${NC}"
    fi
    
    # Stop Docker services
    echo -e "${BLUE}🐳 Stopping Docker services...${NC}"
    docker-compose down
    
    echo -e "${GREEN}✅ All services stopped${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for user to stop the application
echo -e "${GREEN}✨ Dashboard is running! Press Ctrl+C to stop.${NC}"
wait $STREAMLIT_PID

cleanup
