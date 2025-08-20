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

# Check if SQLite is available
# -------------------------------------------
check_sqlite() {
    if ! command -v sqlite3 >/dev/null 2>&1; then
        echo "❌ SQLite not found on system."
        echo "   Please install SQLite first: brew install sqlite"
        exit 1
    fi
}

# Create data directory if it doesn't exist
# -------------------------------------------
create_data_directory() {
    local data_dir="$SCRIPT_DIR/data"
    
    if [ ! -d "$data_dir" ]; then
        echo "📁 Creating data directory: $data_dir"
        mkdir -p "$data_dir"
    fi
    
    echo "✅ Data directory ready: $data_dir"
}

# Local safety confirmation
# -------------------------------------------
local_safety_prompt() {
    echo ""
    echo "⚠️  WARNING: You're about to run database setup on your LOCAL macOS system!"
    echo ""
    echo "This will:"
    echo "  • Create SQLite database: $DB_NAME"
    echo "  • Store database in: $SCRIPT_DIR/data/"
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

# Validate required environment variables (SQLite only needs DB_NAME)
REQUIRED_VARS=(DB_NAME APP_ENV)
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Missing environment variable: $var"
        exit 1
    fi
done

ENV_TYPE=$(detect_environment)

if [[ "$ENV_TYPE" == "local" ]]; then
    check_sqlite
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

# Create data directory
# -------------------------------------------
create_data_directory

# Set database file path
DB_FILE="$SCRIPT_DIR/data/$DB_NAME.db"

# Bootstrap SQLite database
# -------------------------------------------
echo "🔧 Bootstrapping SQLite database..."

if $DRY_RUN; then
    echo "🔧 DRY RUN: Would create SQLite database at $DB_FILE"
else
    if [ ! -f "$DB_FILE" ]; then
        echo "📄 Creating new SQLite database: $DB_FILE"
        sqlite3 "$DB_FILE" "SELECT 1;" >/dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo "✅ SQLite database created successfully"
        else
            echo "❌ Failed to create SQLite database"
            exit 1
        fi
    else
        echo "✅ SQLite database already exists: $DB_FILE"
    fi
fi

echo "✅ SQLite database setup complete."
echo "📍 Database location: $DB_FILE"
