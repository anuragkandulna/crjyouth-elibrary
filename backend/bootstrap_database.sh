#!/bin/bash

# Load environment variables from .env
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo "❌ .env file not found in backend/. Exiting."
  exit 1
fi

# Check for --dry-run flag
DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
  DRY_RUN=true
  echo "🧪 Running in DRY RUN mode..."
fi

# Verify required variables
if [ -z "$DB_NAME" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ] || [ -z "$DB_HOST" ] || [ -z "$BOOTSTRAP_USER" ]; then
  echo "❌ Missing required environment variables. Please check .env."
  exit 1
fi

# Use fallback database to connect as superuser
export PGDATABASE=postgres

# Check if connection works
if [ "$DRY_RUN" = false ]; then
  psql -U "$BOOTSTRAP_USER" -d postgres -c '\q' 2>/dev/null
  if [ $? -ne 0 ]; then
    echo "❌ Failed to connect as $BOOTSTRAP_USER. Please check your setup."
    exit 1
  fi
fi

# Connect as the superuser
echo "\n🔧 Bootstrapping PostgreSQL database and user..."

# Create user if it doesn't exist
if $DRY_RUN; then
  echo "🔧 DRY RUN: Would create user $DB_USER with password"
else
  psql -U "$BOOTSTRAP_USER" -d postgres -tc "SELECT 1 FROM pg_roles WHERE rolname = '$DB_USER'" | grep -q 1 || \
  psql -U "$BOOTSTRAP_USER" -d postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
fi

# Create database if it doesn't exist
if $DRY_RUN; then
  echo "🔧 DRY RUN: Would create database $DB_NAME owned by $DB_USER"
else
  psql -U "$BOOTSTRAP_USER" -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
  psql -U "$BOOTSTRAP_USER" -d postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
fi

# Grant privileges
if $DRY_RUN; then
  echo "🔧 DRY RUN: Would grant all privileges on $DB_NAME to $DB_USER"
else
  psql -U "$BOOTSTRAP_USER" -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
fi

echo "✅ PostgreSQL user and database setup complete."
