# REST-based Raspberry Pi EPD Display Controller

Lightweight Flask API server that receives images and displays them on a Waveshare e-ink display. This component is designed to run on a Raspberry Pi directly connected to the e-paper display hardware.

## Features

- REST API endpoint for uploading and displaying images on e-ink displays
- Support for all Waveshare e-Paper HAT displays
- Automatic image positioning with configurable offsets
- Production-ready systemd service configuration
- Gunicorn-based deployment for reliability
- Display dimension query endpoint

## Prerequisites

- Raspberry Pi (any model with GPIO pins)
- Waveshare e-Paper HAT display
- Raspberry Pi OS (tested on Raspberry Pi OS Lite)
- Python 3 (pre-installed on Raspberry Pi OS)
- Internet connection for downloading dependencies

## Installation

### 1. Clone the Repository

```bash
cd ~
git clone https://github.com/yourusername/rpi-epd-server.git
cd rpi-epd-server
```

### 2. Configure Your Display

Copy the example environment file and edit it to match your display:

```bash
cp .example.env .env
nano .env
```

Configuration options:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `EPD_FILE` | **Yes** | `epd7in5_V2.py` | Waveshare driver filename for your display model |
| `DISPLAY_OFFSET_X` | No | `0` | Horizontal offset adjustment in pixels (can be negative) |
| `DISPLAY_OFFSET_Y` | No | `0` | Vertical offset adjustment in pixels (can be negative) |
| `FLASK_HOST` | No | `0.0.0.0` | Server bind address |
| `FLASK_PORT` | No | `5000` | Server port |

**Important:** Set `EPD_FILE` to match your specific e-Paper display model. Find your model's driver filename from [Waveshare's e-Paper repository](https://github.com/waveshareteam/e-Paper/tree/master/RaspberryPi_JetsonNano/python/lib/waveshare_epd). Common examples:

- 7.5" V2: `epd7in5_V2.py`
- 4.2" V2: `epd4in2_V2.py`
- 2.13" V2: `epd2in13_V2.py`

### 3. Enable SPI Interface

The e-ink display communicates via SPI, which must be enabled:

```bash
sudo raspi-config
```

Navigate to: **Interface Options** → **SPI** → **Enable**

Reboot to apply changes:

```bash
sudo reboot
```

### 4. Run the Initialization Script

The initialization script will:
- Download the appropriate EPD driver files from Waveshare's GitHub
- Install required system packages (Flask, Gunicorn, PIL, python-dotenv)
- Configure the EPD driver for your project

```bash
cd ~/rpi-epd-server
chmod +x init.sh
./init.sh
```

### 5. Test the Server

Start the server manually to verify everything works:

```bash
python3 server.py
```

The server should start on port 5000. Test it from another machine:

```bash
curl http://raspberrypi.local:5000/api/dimension
```

You should see a response with your display dimensions:
```json
{"width": 800, "height": 480}
```

Press Ctrl+C to stop the test server.

### 6. Setup as a Systemd Service (Recommended)

For production use, run the server as a systemd service so it starts automatically on boot.

**Step 1: Add your user to required groups**

```bash
sudo usermod -a -G gpio,spi $USER
```

**Important:** Log out and back in (or reboot) for group changes to take effect.

**Step 2: Edit the service file**

Update the service file with your username and installation path:

```bash
nano rpi-epd-server.service
```

Replace `operator` with your actual username in these lines:
- `User=operator`
- `Group=operator`
- `WorkingDirectory=/home/operator/rpi-epd-server`
- `EnvironmentFile=/home/operator/rpi-epd-server/.env`
- `ExecStart` path

**Step 3: Install and start the service**

```bash
# Copy the service file to systemd directory
sudo cp rpi-epd-server.service /etc/systemd/system/

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable rpi-epd-server.service

# Start service now
sudo systemctl start rpi-epd-server.service

# Check service status
sudo systemctl status rpi-epd-server.service
```

If the service is running correctly, you should see "active (running)" in green.

**Production Configuration:**

The service uses `gunicorn_config.py` with these production-optimized settings:
- Single worker process (prevents concurrent display access issues)
- 120 second timeout for slow display operations
- Automatic worker restart after 1000 requests (prevents memory leaks)
- Logging to systemd journal
- Preloaded application for faster response times

You can modify `gunicorn_config.py` if you need to adjust these settings.


## API Documentation

The server provides two REST API endpoints:

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

**Image Requirements:**
- Image dimensions should match or be smaller than the display dimensions
- Images larger than the display will result in a blank screen
- The server automatically centers the image on the display canvas
- Use `DISPLAY_OFFSET_X` and `DISPLAY_OFFSET_Y` environment variables to fine-tune positioning

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

### GET /api/dimension

Returns the configured display dimensions.

**Request:**
- Method: `GET`
- No parameters required

**Response (Success):**
```json
{
  "width": 800,
  "height": 480
}
```

**Response (Error):**
```json
{
  "error": "EPD not initialized"
}
```

**Status Codes:**
- `200`: Success
- `500`: Server error (display not initialized)

**Example:**
```bash
curl http://raspberrypi.local:5000/api/dimension
```

This endpoint is useful for image generators to dynamically determine the correct image size to generate.

## How It Works

1. **Initialization**: On startup, the server downloads the appropriate EPD driver from Waveshare's GitHub repository based on your `EPD_FILE` configuration
2. **Image Reception**: When an image is uploaded via the `/api/display` endpoint, the server receives it as multipart form data
3. **Image Preparation**: The image is composited onto a blank canvas matching the display dimensions, with optional offset adjustments
4. **Display Update**: The EPD driver initializes the display hardware, sends the image data via SPI, and then puts the display to sleep to conserve power
5. **Response**: The server returns a JSON response indicating success or failure

The server uses a single Gunicorn worker to prevent concurrent access to the display hardware, which could cause corruption.

## Hardware Setup

### Display Connection

Waveshare e-Paper HATs connect directly to the Raspberry Pi's 40-pin GPIO header. The HAT includes all necessary circuitry and requires:

1. Physical connection to GPIO pins (HAT sits on top of Raspberry Pi)
2. SPI interface enabled in Raspberry Pi configuration
3. Appropriate driver file for your specific display model

### Pin Mapping (for reference)

The e-Paper HAT uses these GPIO pins for SPI communication:
- **VCC** → 3.3V power
- **GND** → Ground
- **DIN** → GPIO 10 (MOSI - data input)
- **CLK** → GPIO 11 (SCLK - clock)
- **CS** → GPIO 8 (CE0 - chip select)
- **DC** → GPIO 25 (data/command selection)
- **RST** → GPIO 17 (reset)
- **BUSY** → GPIO 24 (busy status)

Most Waveshare HATs use these standard pins, but verify with your display's documentation.

## Troubleshooting

### View Logs

```bash
# View recent logs
sudo journalctl -u rpi-epd-server.service -n 50

# Follow logs in real-time
sudo journalctl -u rpi-epd-server.service -f
```

### Manage Service

```bash
# Stop service
sudo systemctl stop rpi-epd-server.service

# Restart service
sudo systemctl restart rpi-epd-server.service

# Disable auto-start
sudo systemctl disable rpi-epd-server.service
```

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
sudo python3 server.py
```

### Display Not Updating

**Symptoms**: API returns success but display doesn't change

**Solutions**:
1. Check wiring connections between display and Raspberry Pi
2. Verify display power supply
3. Check logs for hardware errors: `journalctl -u rpi-epd-server.service -n 100`
4. Test display with Waveshare example code to verify hardware

### Image Too Large Warning

**Warning**: `Image too large (WxH) for display (800x480), returning blank canvas`

**Solution**: Ensure the image generator produces images matching your display dimensions. Query the `/api/dimension` endpoint to get the correct dimensions, or check the EPD specifications for your display model. The display controller expects images to fit within the display dimensions.

### Port Already in Use

**Error**: `OSError: [Errno 98] Address already in use`

**Solution**: Another process is using port 5000. Either:
- Stop the other process
- Change `FLASK_PORT` in `.env` to a different port
- Find and kill the process: `sudo lsof -ti:5000 | xargs kill -9`

### Network Connection Refused

**Error**: Image generator cannot connect to display controller

**Solutions**:
1. Verify display controller is running: `sudo systemctl status rpi-epd-server.service`
2. Check firewall rules: `sudo ufw status`
3. Test local connectivity: `curl http://localhost:5000/api/dimension`
4. Verify correct IP address and port in image generator configuration

### Init Script Fails

**Error**: Failed to download EPD driver files from GitHub

**Solutions**:
1. Verify `EPD_FILE` is set correctly in `.env` file
2. Check your internet connection
3. Verify the EPD file exists in [Waveshare's repository](https://github.com/waveshareteam/e-Paper/tree/master/RaspberryPi_JetsonNano/python/lib/waveshare_epd)
4. Check if GitHub is accessible from your network

## Project Structure

```
rpi-epd-server/
├── server.py              # Main Flask application
├── epd.py                 # EPD driver (downloaded by init.sh)
├── epdconfig.py           # EPD configuration (downloaded by init.sh)
├── init.sh                # Initialization script
├── gunicorn_config.py     # Production server configuration
├── rpi-epd-server.service # Systemd service file
├── .env                   # Environment configuration (user-created)
└── .example.env           # Example environment configuration
```

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is provided as-is for use with Waveshare e-Paper displays.
