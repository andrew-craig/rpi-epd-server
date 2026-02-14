# CLAUDE.md

## Project Overview

rpi-epd-server is a lightweight Flask REST API server for Raspberry Pi that receives images via HTTP and displays them on Waveshare e-ink (e-paper) HAT displays. It runs in production behind Gunicorn as a systemd service.

## Tech Stack

- **Python 3** — application language (no build step required)
- **Flask** — web framework
- **Gunicorn** — production WSGI server
- **Pillow (PIL)** — image processing
- **python-dotenv** — environment variable management
- **Waveshare EPD drivers** — hardware interface (downloaded at runtime by `init.sh`, gitignored)

## Project Structure

```
server.py              # Main Flask app, DisplayClient class, API routes
logger.py              # Centralized JSON structured logging
gunicorn_config.py     # Gunicorn production config (1 worker, 120s timeout)
init.sh                # Setup script: downloads EPD drivers, installs deps
rpi-epd-server.service # systemd unit file for production deployment
.example.env           # Example environment configuration
```

EPD driver files (`epd.py`, `epdconfig.py`) are downloaded by `init.sh` from the Waveshare GitHub repo and are gitignored.

## Setup

1. Copy `.example.env` to `.env` and set `EPD_FILE` to your display model
2. Run `bash init.sh` to download drivers and install dependencies

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `EPD_FILE` | Yes | — | Waveshare driver filename (e.g. `epd7in5_V2.py`) |
| `DISPLAY_OFFSET_X` | No | `0` | Horizontal pixel offset for image placement |
| `DISPLAY_OFFSET_Y` | No | `0` | Vertical pixel offset for image placement |
| `FLASK_HOST` | No | `0.0.0.0` | Server bind address |
| `FLASK_PORT` | No | `5000` | Server port |

## API Endpoints

- **POST /api/display** — Upload an image (multipart `image` field) to display on the e-ink screen
- **GET /api/dimension** — Returns display dimensions as `{"width": N, "height": N}`

## Running

```bash
# Development
python3 server.py

# Production
gunicorn -c gunicorn_config.py server:app
```

## Architecture Notes

- **Single worker constraint**: Gunicorn is configured with exactly 1 worker to prevent concurrent hardware access to the e-ink display. Do not increase this.
- **Module-level initialization**: `DisplayClient` is instantiated at module load (`init_client()` at line 233 of `server.py`) for Gunicorn preload compatibility.
- **Image pipeline**: Images are composited onto a white canvas at the display's native resolution, with configurable X/Y offsets. Images rotated 90 degrees are auto-corrected. Oversized images result in a blank white canvas.

## Code Conventions

- PEP 8 style with 4-space indentation
- Google-style docstrings on classes and public methods
- Constants in `UPPER_CASE`, private attributes prefixed with `_`
- JSON structured logging via `logger.py` — use `logging.getLogger(__name__)` in modules
- Error handling: try/except with logging at appropriate levels, re-raise when needed

## Testing

No automated test suite exists. Manual testing via curl:

```bash
curl http://localhost:5000/api/dimension
curl -X POST -F "image=@test.png" http://localhost:5000/api/display
```

## CI/CD

No CI/CD pipeline is configured. No linter or formatter configs exist in the repo.

## Important Constraints

- This runs on Raspberry Pi hardware with GPIO/SPI — EPD driver code requires physical hardware
- Never commit `.env`, `epd.py`, or `epdconfig.py` (all gitignored)
- The 120-second Gunicorn timeout exists because e-ink display refresh operations are slow
- Workers are recycled after 1000 requests (`max_requests`) to prevent memory leaks
