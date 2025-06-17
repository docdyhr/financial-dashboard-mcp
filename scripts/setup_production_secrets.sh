#!/bin/bash
# Script to set up Docker secrets for production deployment

set -e

echo "Setting up Docker secrets for Financial Dashboard production deployment..."

# Function to create a secret if it doesn't exist
create_secret() {
    local secret_name=$1
    local secret_value=$2

    if docker secret inspect "$secret_name" &>/dev/null; then
        echo "Secret '$secret_name' already exists, skipping..."
    else
        echo "$secret_value" | docker secret create "$secret_name" -
        echo "Created secret: $secret_name"
    fi
}

# Generate secure values
SECRET_KEY=$(python3 -c "from backend.core.security import generate_secret_key; print(generate_secret_key(64))")
FLOWER_PASSWORD=$(python3 -c "from backend.core.security import generate_simple_password; print(generate_simple_password(20))")
DB_PASSWORD=$(python3 -c "from backend.core.security import generate_simple_password; print(generate_simple_password(20))")
REDIS_PASSWORD=$(python3 -c "from backend.core.security import generate_simple_password; print(generate_simple_password(20))")

# Database configuration
DB_USER="financial_dashboard"
DB_NAME="financial_dashboard"
DB_HOST="db"
DB_PORT="5432"

# Construct database URL
DB_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

# Create secrets
create_secret "secret_key" "$SECRET_KEY"
create_secret "flower_password" "$FLOWER_PASSWORD"
create_secret "db_url" "$DB_URL"
create_secret "db_user" "$DB_USER"
create_secret "db_password" "$DB_PASSWORD"
create_secret "redis_password" "$REDIS_PASSWORD"

echo ""
echo "Production secrets have been created!"
echo ""
echo "Save these values securely:"
echo "=========================="
echo "Database User: $DB_USER"
echo "Database Password: $DB_PASSWORD"
echo "Flower Password: $FLOWER_PASSWORD"
echo "Redis Password: $REDIS_PASSWORD"
echo ""
echo "To deploy in production, run:"
echo "docker stack deploy -c docker/docker-compose.prod.yml financial-dashboard"
