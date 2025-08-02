#!/bin/bash

# Detect environment
# -------------------------------------------
detect_environment() {
    if [[ "$OSTYPE" == "darwin"* ]] || [[ ! -f /.dockerenv ]]; then
        echo "local"
    else
        echo "test"
    fi
}

# Check if PostgreSQL is available locally
# -------------------------------------------
check_postgres_local() {
    if ! command -v psql >/dev/null 2>&1 && ! command -v pg_ctl >/dev/null 2>&1; then
        echo "❌ PostgreSQL not found on local system."
        echo "   Please install PostgreSQL first: brew install postgresql"
        exit 1
    fi
}

# Start PostgreSQL service based on environment
# -------------------------------------------
start_postgres_service() {
    local env_type=$1

    if [[ "$env_type" == "test" ]]; then
        echo "🚀 Initializing PostgreSQL for testing..."
        sudo service postgresql start
        sleep 3
        echo "✅ PostgreSQL service started"
    else
        echo "🚀 Starting PostgreSQL locally..."
        if command -v brew >/dev/null 2>&1; then
            brew services start postgresql >/dev/null 2>&1 || true
        elif command -v pg_ctl >/dev/null 2>&1; then
            pg_ctl start >/dev/null 2>&1 || true
        fi

        if psql -d postgres -c '\q' >/dev/null 2>&1; then
            echo "✅ PostgreSQL is running locally"
        else
            echo "⚠️  PostgreSQL may not be running. Continuing anyway..."
            echo "   You may need to start it manually if the script fails."
        fi
    fi
}

# Local safety confirmation
# -------------------------------------------
local_safety_prompt() {
    echo ""
    echo "⚠️  WARNING: You're about to run database setup on your LOCAL macOS system!"
    echo ""
    echo "This will:"
    echo "  • Start PostgreSQL service (if not running)"
    echo "  • Create/modify database: $DB_NAME"
    echo "  • Create/modify user: $DB_USER"
    echo "  • Grant database privileges"
    echo ""
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Operation cancelled by user."
        exit 0
    fi

    echo ""
    echo "⏱️  Starting in 5 seconds... Press Ctrl+C to cancel"
    for i in {5..1}; do
        echo "   $i..."
        sleep 1
    done
    echo ""
    echo "🚀 Proceeding with local database setup..."
}

# Main execution
# -------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo "❌ .env file not found at $ENV_FILE. Exiting."
    exit 1
fi

# Validate required environment variables
REQUIRED_VARS=(DB_NAME DB_USER DB_PASSWORD DB_HOST BOOTSTRAP_USER APP_ENV)
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Missing environment variable: $var"
        exit 1
    fi
done

ENV_TYPE=$(detect_environment)

if [[ "$ENV_TYPE" == "local" ]]; then
    check_postgres_local
    local_safety_prompt
    echo "🏠 Running in LOCAL mode using .env configuration"
else
    echo "🐳 Running in TEST mode using .env configuration"
fi

# Check for --dry-run flag
# -------------------------------------------
DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "🧪 Running in DRY RUN mode..."
fi

# Start PostgreSQL service
# -------------------------------------------
start_postgres_service "$ENV_TYPE"

# Use fallback database to connect as superuser
export PGDATABASE=postgres

if [ "$DRY_RUN" = false ]; then
    PGPASSWORD="$DB_PASSWORD" psql -U "$BOOTSTRAP_USER" -d postgres -c '\q' 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "❌ Failed to connect as $BOOTSTRAP_USER. Please check your setup."
        exit 1
    fi
fi

# Connect as the superuser
# -------------------------------------------
echo "🔧 Bootstrapping PostgreSQL database and user..."

# Create user if it doesn't exist
if $DRY_RUN; then
    echo "🔧 DRY RUN: Would create user $DB_USER with password"
else
    PGPASSWORD="$DB_PASSWORD" psql -U "$BOOTSTRAP_USER" -d postgres -tc "SELECT 1 FROM pg_roles WHERE rolname = '$DB_USER'" | grep -q 1 || \
    PGPASSWORD="$DB_PASSWORD" psql -U "$BOOTSTRAP_USER" -d postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
fi

# Create database if it doesn't exist
if $DRY_RUN; then
    echo "🔧 DRY RUN: Would create database $DB_NAME owned by $DB_USER"
else
    PGPASSWORD="$DB_PASSWORD" psql -U "$BOOTSTRAP_USER" -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
    PGPASSWORD="$DB_PASSWORD" psql -U "$BOOTSTRAP_USER" -d postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
fi

# Grant privileges
if $DRY_RUN; then
    echo "🔧 DRY RUN: Would grant all privileges on $DB_NAME to $DB_USER"
else
    PGPASSWORD="$DB_PASSWORD" psql -U "$BOOTSTRAP_USER" -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
fi

echo "✅ PostgreSQL user and database setup complete."
