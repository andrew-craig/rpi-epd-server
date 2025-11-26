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

# GitHub raw content URLs
GITHUB_BASE="https://raw.githubusercontent.com/waveshareteam/e-Paper/master/RaspberryPi_JetsonNano/python/lib/waveshare_epd"
EPD_URL="${GITHUB_BASE}/${EPD_FILE}"
CONFIG_URL="${GITHUB_BASE}/epdconfig.py"

echo "Downloading epdconfig.py from GitHub..."
if ! curl -fSL "$CONFIG_URL" -o epdconfig.py; then
    echo "Error: Failed to download epdconfig.py"
    echo "URL attempted: ${CONFIG_URL}"
    exit 1
fi
echo "Successfully downloaded epdconfig.py"

echo "Downloading ${EPD_FILE} from GitHub..."
if ! curl -fSL "$EPD_URL" -o "${EPD_FILE}"; then
    echo "Error: Failed to download ${EPD_FILE}"
    echo "URL attempted: ${EPD_URL}"
    exit 1
fi
echo "Successfully downloaded ${EPD_FILE}"

echo "Modifying ${EPD_FILE} to fix imports..."
# Replace the relative import with absolute import
sed -i 's/from \. import epdconfig/import epdconfig/g' "${EPD_FILE}"

# Rename to epd.py for use by server.py
mv "${EPD_FILE}" epd.py
echo "Successfully configured epd.py"


# Install dependencies
echo "Installing dependencies..."
command sudo apt install -y python3-flask python3-gunicorn python3-pil

command python3 -m venv venv

echo "Initialization complete!"
