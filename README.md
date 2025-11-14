# REST-based Raspberry Pi EPD Display Controller

Lightweight Flask API server that receives images and displays them on a Waveshare e-ink display. This component is designed to run on a Raspberry Pi directly connected to the e-paper display hardware.

## Installation

### 1. Configure
Copy the .example.env file to .env and edit to match your EPD display

Configuration options:

| Variable | Default | Description |
|----------|---------|-------------|
| `DISPLAY_WIDTH` | `800` | Display width in pixels |
| `DISPLAY_HEIGHT` | `480` | Display height in pixels |
| `DISPLAY_OFFSET_X` | `0` | Horizontal offset adjustment (can be negative) |
| `DISPLAY_OFFSET_Y` | `0` | Vertical offset adjustment (can be negative) |
| `FLASK_HOST` | `0.0.0.0` Server address |
| `FLASK_PORT` | `5000` | Server port |

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


### 3. Install Dependencies

Make sure uv is installed for Python package management. Follow the [instructions from astral](https://docs.astral.sh/uv/getting-started/installation/) to install it.

Run the initialisation script
> ./init.sh

### 4. Setup as a Service

The project includes a systemd service file and gunicorn configuration for production deployment.

**Install the service:**

```bash
# Copy the service file to systemd directory
sudo cp rpi-epd-server.service /etc/systemd/system/

# Edit the service file to match your username and paths
sudo nano /etc/systemd/system/rpi-epd-server.service
# Replace 'operator' with your actual username
# Update paths if you installed to a different location

# Ensure your user has access to GPIO/SPI
sudo usermod -a -G gpio,spi $USER
# Log out and back in for group changes to take effect
```

**Start the service:**

```bash
# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable rpi-epd-server.service

# Start service now
sudo systemctl start rpi-epd-server.service

# Check service status
sudo systemctl status rpi-epd-server.service
```

**Configuration:**

The service uses `gunicorn_config.py` for production settings:
- Single worker process (required for e-ink display hardware access)
- 120 second timeout for display operations
- Automatic worker restart after 1000 requests
- Logging to systemd journal

You can modify `gunicorn_config.py` to adjust these settings if needed.


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
sudo python3 display-client.py
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
1. Verify display controller is running: `sudo systemctl status rpi-epd-server.service`
2. Check firewall rules: `sudo ufw status`
3. Test local connectivity: `curl http://localhost:5000/api/display`
4. Verify correct IP address and port in image generator configuration

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
