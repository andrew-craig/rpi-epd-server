#!/bin/bash

# Exit on error
set -e

echo "Initializing rpi-epd-server project..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    exit 1
fi

# Read EPD_FILE value from .env
EPD_FILE=$(grep -E "^EPD_FILE=" .env | cut -d '=' -f2)

if [ -z "$EPD_FILE" ]; then
    echo "Error: EPD_FILE not found in .env"
    exit 1
fi

echo "Found EPD_FILE: $EPD_FILE"

# GitHub raw content URL
GITHUB_URL="https://raw.githubusercontent.com/waveshareteam/e-Paper/master/RaspberryPi_JetsonNano/python/lib/waveshare_epd/${EPD_FILE}"

echo "Downloading ${EPD_FILE} from GitHub..."

# Download the file
if ! curl -fSL "$GITHUB_URL" -o epd.py; then
    echo "Error: Failed to download ${EPD_FILE}"
    echo "URL attempted: ${GITHUB_URL}"
    exit 1
fi

echo "Successfully downloaded and renamed to epd.py"

CONFIG_URL="https://raw.githubusercontent.com/waveshareteam/e-Paper/master/RaspberryPi_JetsonNano/python/lib/waveshare_epd/epdconfig.py"

echo "Downloading config file from GitHub..."

# Download the file
if ! curl -fSL "$CONFIG_URL" -o epd.py; then
    echo "Error: Failed to download epdconfig.py"
    echo "URL attempted: ${CONFIG_URL}"
    exit 1
fi


# Install dependencies
echo "Installing dependencies..."
command sudo apt install -y python3-flask python3-gunicorn python3-pil

command python3 -m venv venv

echo "Initialization complete!"
