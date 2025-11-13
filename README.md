# Display Controller

Lightweight Flask API server that receives images and displays them on a Waveshare 7.5" e-ink display. This component is designed to run on an ARM device (Raspberry Pi) directly connected to the e-paper display hardware.

## Overview

The Display Controller is part of the Bush Display project's distributed architecture:
- **Image Generator Service** (Docker container): Generates dashboard images
- **Display Controller** (this component): Receives and displays images on e-ink hardware

This separation allows the heavy image generation to run on any platform while keeping the display control minimal and hardware-focused.

## Hardware Requirements

- **ARM Device**: Raspberry Pi (3, 4, or Zero W recommended)
- **E-Paper Display**: Waveshare 7.5" V2 e-ink display (800x480 resolution)
- **Connection**: SPI interface (default GPIO pins)
- **Power**: 5V power supply for Raspberry Pi

### Waveshare 7.5" Display Pinout

The display connects to the Raspberry Pi GPIO pins via SPI:
- VCC → 3.3V
- GND → Ground
- DIN → GPIO 10 (MOSI)
- CLK → GPIO 11 (SCLK)
- CS → GPIO 8 (CE0)
- DC → GPIO 25
- RST → GPIO 17
- BUSY → GPIO 24

## Installation

### 1. System Requirements

Ensure your Raspberry Pi is running a recent version of Raspberry Pi OS (Bullseye or newer):

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Enable SPI Interface

The e-ink display requires SPI to be enabled:

```bash
sudo raspi-config
```

Navigate to: **Interface Options** → **SPI** → **Enable**

Reboot if prompted:

```bash
sudo reboot
```

### 3. Install Python Dependencies

Clone this repository or copy the `display-controller` directory to your Raspberry Pi, then install dependencies:

```bash
cd display-controller
pip install .
```

Or install in editable mode for development:

```bash
pip install -e .
```

Or install system-wide (may require sudo):

```bash
sudo pip3 install .
```

## Configuration

The display controller uses environment variables for configuration. Copy the example environment file:

```bash
cp .example.env .env
```

Edit `.env` to configure your display:

```bash
# Display dimensions (width x height in pixels)
DISPLAY_WIDTH=480
DISPLAY_HEIGHT=800

# Display offset adjustments (in pixels)
# Use these to correct for screen alignment issues
DISPLAY_OFFSET_X=-6
DISPLAY_OFFSET_Y=3

# Flask API server settings (optional)
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `DISPLAY_WIDTH` | `800` | Display width in pixels |
| `DISPLAY_HEIGHT` | `480` | Display height in pixels |
| `DISPLAY_OFFSET_X` | `0` | Horizontal offset adjustment (can be negative) |
| `DISPLAY_OFFSET_Y` | `0` | Vertical offset adjustment (can be negative) |
| `FLASK_HOST` | `0.0.0.0` | Flask API host (0.0.0.0 = all interfaces) |
| `FLASK_PORT` | `5000` | Flask API port |

**Note**: The example `.env` shows `DISPLAY_WIDTH=480` and `DISPLAY_HEIGHT=800` for portrait orientation, but the physical display is 800x480. Adjust based on your image generator's output format.

## Running the Application

### Manual Start

Load environment variables and run the display client:

```bash
# Load environment variables
export $(cat .env | xargs)

# Run the display client
python3 display-client.py
```

The server will start and listen for incoming display requests:

```
INFO - Starting Flask API server on 0.0.0.0:5000
```

### Testing with curl

You can test the display controller by sending an image file:

```bash
curl -X POST http://localhost:5000/api/display \
  -F "image=@/path/to/test-image.png"
```

Expected response:

```json
{
  "success": true,
  "message": "Display updated successfully"
}
```

## Systemd Service Setup

To automatically start the display controller on boot, create a systemd service:

### 1. Create Service File

Create `/etc/systemd/system/display-controller.service`:

```ini
[Unit]
Description=Bush Display Controller
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/display-controller
EnvironmentFile=/home/pi/display-controller/.env
ExecStart=/usr/bin/python3 /home/pi/display-controller/display-client.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Note**: Adjust paths (`/home/pi/display-controller`) to match your installation location.

### 2. Enable and Start Service

```bash
# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable display-controller.service

# Start service now
sudo systemctl start display-controller.service

# Check service status
sudo systemctl status display-controller.service
```

### 3. View Logs

```bash
# View recent logs
sudo journalctl -u display-controller.service -n 50

# Follow logs in real-time
sudo journalctl -u display-controller.service -f
```

### 4. Service Management

```bash
# Stop service
sudo systemctl stop display-controller.service

# Restart service
sudo systemctl restart display-controller.service

# Disable auto-start
sudo systemctl disable display-controller.service
```

## API Documentation

### POST /api/display

Receives an image file and displays it on the e-ink screen.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Form data with `image` field containing image file

**Supported Image Formats:**
- PNG (recommended)
- JPEG
- BMP
- Any format supported by Pillow

**Response (Success):**
```json
{
  "success": true,
  "message": "Display updated successfully"
}
```

**Response (Error):**
```json
{
  "error": "Error description"
}
```

**Status Codes:**
- `200`: Success
- `400`: Bad request (missing image file or empty filename)
- `500`: Server error (display initialization failure, etc.)

**Example:**
```bash
curl -X POST http://raspberrypi.local:5000/api/display \
  -F "image=@dashboard.png"
```

## Troubleshooting

### SPI Not Enabled

**Error**: `FileNotFoundError: [Errno 2] No such file or directory: '/dev/spidev0.0'`

**Solution**: Enable SPI interface via `raspi-config` and reboot.

### Permission Denied (SPI/GPIO)

**Error**: `PermissionError: [Errno 13] Permission denied: '/dev/spidev0.0'`

**Solution**: Add your user to the `spi` and `gpio` groups:

```bash
sudo usermod -a -G spi,gpio $USER
# Log out and back in for changes to take effect
```

Or run with sudo (not recommended for production):

```bash
sudo python3 display-client.py
```

### Display Not Updating

**Symptoms**: API returns success but display doesn't change

**Solutions**:
1. Check wiring connections between display and Raspberry Pi
2. Verify display power supply
3. Check logs for hardware errors: `journalctl -u display-controller.service -n 100`
4. Test display with Waveshare example code to verify hardware

### Image Too Large Warning

**Warning**: `Image too large (WxH) for display (800x480), returning blank canvas`

**Solution**: Ensure the image generator produces images matching your `DISPLAY_WIDTH` and `DISPLAY_HEIGHT` settings. The display controller expects images to fit within the configured dimensions.

### Port Already in Use

**Error**: `OSError: [Errno 98] Address already in use`

**Solution**: Another process is using port 5000. Either:
- Stop the other process
- Change `FLASK_PORT` in `.env` to a different port
- Find and kill the process: `sudo lsof -ti:5000 | xargs kill -9`

### Network Connection Refused

**Error**: Image generator cannot connect to display controller

**Solutions**:
1. Verify display controller is running: `sudo systemctl status display-controller.service`
2. Check firewall rules: `sudo ufw status`
3. Test local connectivity: `curl http://localhost:5000/api/display`
4. Verify correct IP address and port in image generator configuration

## Development and Testing

### Testing Without Hardware

The `epd7in5_V2.py` driver includes an `EPDTest` class for development without physical hardware. To use it, modify `display-client.py` to import `EPDTest` instead of `EPD`:

```python
from epd7in5_V2 import EPDTest as EPD
```

This will display images in a window instead of sending to the e-paper display.

### Debug Mode

For more verbose logging, you can modify the logging level in `display-client.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

## Architecture

### Image Flow

1. **Image Generator** (Docker container) generates dashboard image
2. **HTTP POST** sends image to display controller via `/api/display` endpoint
3. **Display Client** receives multipart file upload
4. **Image Preparation** applies offset adjustments and composites onto canvas
5. **EPD Driver** initializes display, sends image data via SPI, puts display to sleep

### File Structure

```
display-controller/
├── display-client.py      # Flask API server and display logic
├── epd7in5_V2.py          # Waveshare e-paper display driver
├── pyproject.toml         # Project metadata and dependencies
├── .example.env           # Example environment configuration
├── .env                   # Your environment configuration (not in git)
└── README.md              # This file
```

## Performance

- **Display Update Time**: ~15-20 seconds (e-ink refresh limitation)
- **API Response Time**: <100ms (returns immediately, display updates in background)
- **Memory Usage**: ~50-100MB (minimal Python process)
- **CPU Usage**: <5% idle, ~20% during display update

## Best Practices

1. **Update Frequency**: E-ink displays have limited refresh cycles (~1 million). Avoid updating more frequently than necessary. The recommended update interval is 60 seconds minimum.

2. **Power Management**: The display controller automatically puts the display to sleep after each update to reduce power consumption and prevent burn-in.

3. **Network Reliability**: Use systemd service with `Restart=always` to ensure the display controller recovers from network failures or crashes.

4. **Image Format**: PNG is recommended for best quality and compatibility. Ensure images are exactly the right dimensions to avoid scaling.

5. **Monitoring**: Regularly check logs for errors or warnings that might indicate hardware issues.

## Related Components

- **Image Generator Service**: See `../image-generator/README.md` for the Docker-based image generation service
- **Deployment Guide**: See `../DEPLOYMENT.md` for complete system setup instructions
- **Project Overview**: See `../README.md` for overall architecture

## License

This component is part of the Bush Display project. See the root directory for license information.
