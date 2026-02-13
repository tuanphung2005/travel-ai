#!/bin/bash
# Run script for Travel Backend

# Change to script directory
cd "$(dirname "$0")"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
