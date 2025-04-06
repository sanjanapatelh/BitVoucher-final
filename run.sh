#!/bin/bash
# run.sh - Start the Bitcoin subsidy application

# Ensure script fails on any error
set -e

# Directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Print startup message
echo " Starting Application "

# Set default environment variables if not already set
export LNBITS_URL="${LNBITS_URL:-http://localhost:5001}"
export ADMIN_KEY="${ADMIN_KEY:-9bca41d2b0f540f08393cde5dd13b178}"  
export SECRET_KEY="${SECRET_KEY:-$(openssl rand -hex 32)}"
export DEBUG="${DEBUG:-False}"
export PORT="${PORT:-8080}"
export HOST="${HOST:-0.0.0.0}"

# Logging configuration
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export LOG_FILE="${LOG_FILE:-subsidy_app.log}"
export DEFAULT_DAILY_LIMIT="${DEFAULT_DAILY_LIMIT:-10000}"
export ALLOWED_CATEGORIES="${ALLOWED_CATEGORIES:-food,medicine}"

# Ensure Python environment is set up
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing/upgrading dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Start the application
echo "Starting application on ${HOST}:${PORT}"
echo "LNBits URL: ${LNBITS_URL}"
echo "Debug Mode: ${DEBUG}"

# Run the application
python3 app.py

# Deactivate virtual environment when done
deactivate
