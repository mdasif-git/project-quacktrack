#!/bin/bash

echo "Checking if GMAIL API password is setup..."
if [ -z "$GMAIL_APP_PASSWORD" ]; then
    echo "Environment variable is not set. Exiting."
    exit 1
fi
echo "Starting setup process..."
echo "Installing required packages..."
pip install -r main/requirements.txt
echo "Setup complete."
