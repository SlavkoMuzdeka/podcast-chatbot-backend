#!/usr/bin/env bash
set -euo pipefail

echo "🗄️  Setting up PostgreSQL database for Podcast Chatbot..."

# 1. Ensure psql is available
if ! command -v psql &>/dev/null; then
  echo "❌ PostgreSQL client (psql) is not installed. Install via brew or apt."
  exit 1
fi

# 2. Load environment variables from .env
if [[ -f .env ]]; then
  set -o allexport
  source .env
  set +o allexport
else
  echo "❌ .env file not found. Please create and configure it."
  exit 1
fi

# 3. Expect DATABASE_URL in format postgresql://user:pass@host:port/dbname
if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "❌ DATABASE_URL not set in .env."
  exit 1
fi

# Parse components of DATABASE_URL using grep -oP
DB_USER=$(echo "$DATABASE_URL" | grep -oP '(?<=postgresql://)[^:]+')
DB_PASS=$(echo "$DATABASE_URL" | grep -oP '(?<=postgresql://[^:]+:)[^@]+')
DB_HOST=$(echo "$DATABASE_URL" | grep -oP '(?<=@)[^:]+')
DB_PORT=$(echo "$DATABASE_URL" | grep -oP '(?<=:)[0-9]+(?=/)')
DB_NAME=$(echo "$DATABASE_URL" | grep -oP '(?<=/)[^/?]+$')

echo "📊 Database configuration:"
echo "   Host:     $DB_HOST"
echo "   Port:     $DB_PORT"
echo "   Database: $DB_NAME"
echo "   User:     $DB_USER"

# 4. Initialize tables using python3 (if present)
echo "📋 Initializing database tables..."
if command -v python3 &>/dev/null; then
  python3 migrations/init_db.py
else
  echo "❌ python3 not found. Please install Python 3 to run migrations."
  exit 1
fi

echo "✅ Database setup completed successfully!"
echo ""
echo "🚀 Start the app with:"
echo "   python3 run.py"
echo ""
echo "📡 Connection string (from .env):"
echo "   $DATABASE_URL"
