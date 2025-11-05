#!/bin/bash

# Load API key from .key file
if [ -f ".key" ]; then
    API_KEY=$(cat .key | tr -d '\n\r')
else
    echo "Error: .key file not found!"
    echo "Please create a .key file with your API key."
    echo "Example: echo 'your-secret-api-key' > .key"
    exit 1
fi

# Run mcpo with the API key
uvx mcpo --port 8000 --api-key "$API_KEY" -- uv run python weather.py