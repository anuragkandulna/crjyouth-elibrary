#!/bin/bash
set -e

echo "🔧 Configuring PostgreSQL authentication..."

# Configure PostgreSQL for md5 authentication
sed -i 's/local   all             postgres                                peer/local   all             postgres                                md5/' /etc/postgresql/14/main/pg_hba.conf
sed -i 's/local   all             all                                     peer/local   all             all                                     md5/' /etc/postgresql/14/main/pg_hba.conf

# Temporarily revert to peer auth to set password
sed -i 's/local   all             postgres                                md5/local   all             postgres                                peer/' /etc/postgresql/14/main/pg_hba.conf

# Start PostgreSQL
service postgresql start
sleep 3

# Set postgres user password
su - postgres -c "psql -c \"ALTER USER postgres PASSWORD 'postgres';\""

# Restore md5 authentication
sed -i 's/local   all             postgres                                peer/local   all             postgres                                md5/' /etc/postgresql/14/main/pg_hba.conf

# Reload PostgreSQL configuration
su - postgres -c "psql -c \"SELECT pg_reload_conf();\""

# Test connection works
PGPASSWORD=postgres psql -U postgres -d postgres -c "SELECT 'PostgreSQL setup complete' as status;" > /dev/null

# Stop PostgreSQL
service postgresql stop

echo "✅ PostgreSQL configuration completed successfully" 
