#!/bin/bash
# Start script for AI Sandbox

echo "Starting AI Sandbox Backend..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Ensure API keys are set (they should be exported in your terminal or in a .env file)
if [ -z "$GEMINI_API_KEY" ]; then
    echo "Warning: GEMINI_API_KEY is not set."
fi

# Run the API
PYTHONPATH=. python3 -m app.main api --port 8001
