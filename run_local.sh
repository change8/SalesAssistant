#!/bin/bash

# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Virtual environment not found at .venv. Please create it first."
    exit 1
fi

# Check dependencies (optional, but good for safety)
# pip install -r backend/requirements.txt

# Set PYTHONPATH
export PYTHONPATH=$DIR

# Run Uvicorn
echo "Starting SalesAssistant Backend..."
echo "Frontend will be available at: http://127.0.0.1:8000/web/"
echo "API Docs available at: http://127.0.0.1:8000/docs"

# Use uvicorn to start the app
# reload flag enables auto-reload on code changes
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
