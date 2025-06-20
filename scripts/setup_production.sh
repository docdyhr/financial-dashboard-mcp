#!/bin/bash

# Production Setup Script for Financial Dashboard
# This script helps set up a secure production environment
#
# SECURITY NOTICE:
# - Never commit the generated .env file to version control
# - Store all generated credentials securely
# - Use a proper secret management service in production

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Financial Dashboard - Production Setup${NC}"
echo "======================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
   echo -e "${RED}ERROR: Please do not run this script as root!${NC}"
   exit 1
fi

# Function to generate secure random strings
generate_secret() {
    local length=${1:-32}
    python3 -c "import secrets; print(secrets.token_urlsafe($length))"
}

# Function to prompt for input with masking for passwords
read_secret() {
    local prompt="$1"
    local var_name="$2"

    echo -n "$prompt"
    read -s -r value
    echo ""
    eval "$var_name='$value'"
}

# Check if .env already exists
if [ -f .env ]; then
    echo -e "${YELLOW}WARNING: .env file already exists!${NC}"
    echo -n "Do you want to backup and create a new one? (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        backup_file=".env.backup.$(date +%Y%m%d_%H%M%S)"
        mv .env "$backup_file"
        echo -e "${GREEN}Existing .env backed up to: $backup_file${NC}"
    else
        echo "Exiting without changes."
        exit 0
    fi
fi

echo -e "${YELLOW}Generating secure production configuration...${NC}"
echo ""

# Database Configuration
echo "=== Database Configuration ==="
echo -n "PostgreSQL Username [financial_user]: "
read -r POSTGRES_USER
POSTGRES_USER=${POSTGRES_USER:-financial_user}

read_secret "PostgreSQL Password (leave empty to auto-generate): " POSTGRES_PASSWORD
if [ -z "$POSTGRES_PASSWORD" ]; then
    POSTGRES_PASSWORD=$(generate_secret 32)
    echo -e "${GREEN}Generated PostgreSQL password${NC}"
fi

echo -n "PostgreSQL Database Name [financial_dashboard]: "
read -r POSTGRES_DB
POSTGRES_DB=${POSTGRES_DB:-financial_dashboard}

echo -n "PostgreSQL Host [localhost]: "
read -r POSTGRES_HOST
POSTGRES_HOST=${POSTGRES_HOST:-localhost}

echo -n "PostgreSQL Port [5432]: "
read -r POSTGRES_PORT
POSTGRES_PORT=${POSTGRES_PORT:-5432}

# Generate secure secrets
echo ""
echo -e "${YELLOW}Generating secure secrets...${NC}"
SECRET_KEY=$(generate_secret 64)
echo -e "${GREEN}✓ Generated SECRET_KEY (64 characters)${NC}"

MCP_AUTH_TOKEN=$(generate_secret 32)
echo -e "${GREEN}✓ Generated MCP_AUTH_TOKEN (32 characters)${NC}"

# Flower Monitoring
echo ""
echo "=== Flower Monitoring Configuration ==="
echo -n "Flower Username [admin]: "
read -r FLOWER_USERNAME
FLOWER_USERNAME=${FLOWER_USERNAME:-admin}

read_secret "Flower Password (leave empty to auto-generate): " FLOWER_PASSWORD
if [ -z "$FLOWER_PASSWORD" ]; then
    FLOWER_PASSWORD=$(generate_secret 32)
    echo -e "${GREEN}Generated Flower password${NC}"
fi

# Market Data Providers
echo ""
echo "=== Market Data Provider API Keys ==="
echo -e "${YELLOW}Register for free API keys at:${NC}"
echo "- Alpha Vantage: https://www.alphavantage.co/support/#api-key"
echo "- Finnhub: https://finnhub.io/register"
echo ""

read_secret "Alpha Vantage API Key (optional): " ALPHA_VANTAGE_API_KEY
read_secret "Finnhub API Key (optional): " FINNHUB_API_KEY

# Create .env file
cat > .env << EOF
# Production Configuration - Financial Dashboard
# Generated on: $(date)
#
# SECURITY NOTICE:
# - This file contains sensitive credentials
# - NEVER commit this file to version control
# - Store a secure backup of these credentials
# - Consider using a secret management service

# Database Configuration
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
DATABASE_ECHO=False

# PostgreSQL Docker Configuration
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=${POSTGRES_DB}

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=False

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Security
SECRET_KEY=${SECRET_KEY}
ACCESS_TOKEN_EXPIRE_MINUTES=1440
MCP_AUTH_TOKEN=${MCP_AUTH_TOKEN}

# Market Data Providers
ALPHA_VANTAGE_API_KEY=${ALPHA_VANTAGE_API_KEY}
FINNHUB_API_KEY=${FINNHUB_API_KEY}
YFINANCE_START_DATE=2020-01-01

# MCP Server Configuration
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8502

# Environment
ENVIRONMENT=production
DEBUG=False

# Logging
LOG_LEVEL=WARNING
LOG_FILE=logs/production.log

# CORS - Update with your actual domain
CORS_ORIGINS=["https://yourdomain.com"]

# Flower Monitoring
FLOWER_USERNAME=${FLOWER_USERNAME}
FLOWER_PASSWORD=${FLOWER_PASSWORD}

# Celery Beat Schedule (in seconds)
MARKET_DATA_UPDATE_INTERVAL=300
PORTFOLIO_SNAPSHOT_INTERVAL=3600
EOF

# Set secure permissions
chmod 600 .env

echo ""
echo -e "${GREEN}✓ Production configuration created successfully!${NC}"
echo ""
echo "=== Important Security Information ==="
echo ""
echo -e "${YELLOW}Database Credentials:${NC}"
echo "Username: ${POSTGRES_USER}"
echo "Database: ${POSTGRES_DB}"
echo -e "${RED}Password: [HIDDEN - Check .env file]${NC}"
echo ""
echo -e "${YELLOW}Admin Credentials:${NC}"
echo "Flower Username: ${FLOWER_USERNAME}"
echo -e "${RED}Flower Password: [HIDDEN - Check .env file]${NC}"
echo ""
echo -e "${YELLOW}Generated Secrets:${NC}"
echo -e "${RED}SECRET_KEY: [HIDDEN - Check .env file]${NC}"
echo -e "${RED}MCP_AUTH_TOKEN: [HIDDEN - Check .env file]${NC}"
echo ""
echo "=== Next Steps ==="
echo "1. Review the generated .env file"
echo "2. Update CORS_ORIGINS with your actual domain"
echo "3. Store these credentials securely"
echo "4. Set up SSL/TLS certificates"
echo "5. Configure your firewall rules"
echo "6. Set up monitoring and alerting"
echo "7. Run: docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo -e "${GREEN}Remember: NEVER commit the .env file to version control!${NC}"
