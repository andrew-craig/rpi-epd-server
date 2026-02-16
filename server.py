#!/usr/bin/env python3
"""
Display Client for Bush Display
Lightweight Flask API server that receives uploaded images and displays them on e-ink hardware.
Provides /api/display endpoint that accepts multipart file uploads.
"""

import logging
import os
import time
from io import BytesIO

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from PIL import Image, ImageDraw, ImageFont

from epd import EPD
from logger import setup_logging

# Load environment variables from .env file
load_dotenv()

# Configure JSON logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Global client instance - initialized at module level for Gunicorn compatibility
client = None


class DisplayClient:
    """Manages e-ink display updates from generated images."""

    def __init__(self):
        """Initialize display client."""
        self._DISPLAY_OFFSET_X = int(os.environ.get("DISPLAY_OFFSET_X", 0))
        self._DISPLAY_OFFSET_Y = int(os.environ.get("DISPLAY_OFFSET_Y", 0))
        self._BACKGROUND_COLOUR = (255, 255, 255)
        self.epd = EPD()

        logger.info(f"Display client initialized with dimensions {self.epd.width}x{self.epd.height}")

    def prepare_image(self, uploaded_image):
        """
        Prepare uploaded image for display by compositing it onto canvas with offset.

        Args:
            uploaded_image: PIL.Image to prepare

        Returns:
            PIL.Image ready for display
        """
        # Create a blank canvas
        img = Image.new(
            "RGB", (self.epd.width, self.epd.height), self._BACKGROUND_COLOUR
        )

        # Get dimensions of uploaded image
        fetched_width, fetched_height = uploaded_image.size
        logger.info(f"Uploaded image dimensions: {fetched_width}x{fetched_height}")

        # Check if image fits within display dimensions
        if (
            fetched_width <= self.epd.width
            and fetched_height <= self.epd.height
        ):
            # Paste the image into the canvas
            img.paste(
                uploaded_image,
                (0 + self._DISPLAY_OFFSET_X, 0 + self._DISPLAY_OFFSET_Y),
            )
            logger.info(
                f"Image pasted at offset ({self._DISPLAY_OFFSET_X}, {self._DISPLAY_OFFSET_Y})"
            )
        elif ( 
            fetched_width <= self.epd.height
            and fetched_height <= self.epd.width
        ):
            # If image is rotated, rotate it back to fit display dimensions
            uploaded_image = uploaded_image.rotate(90, expand=True)
            img.paste(
                uploaded_image,
                (0 + self._DISPLAY_OFFSET_X, 0 + self._DISPLAY_OFFSET_Y),
            )
            logger.info(
                f"Rotated and pasted image at offset ({self._DISPLAY_OFFSET_X}, {self._DISPLAY_OFFSET_Y})"
            )

        else:
            logger.warning(
                f"Image too large ({fetched_width}x{fetched_height}) for display "
                f"({self.epd.width}x{self.epd.height}), returning blank canvas"
            )

        return img

    def display_image(self, image):
        """
        Display image on e-ink screen.

        Args:
            image: PIL.Image to display
        """
        try:
            logger.info("Initializing e-ink display")
            self.epd.init()

            logger.info("Displaying image")
            self.epd.display(self.epd.getbuffer(image))

            logger.info("Putting display to sleep")
            self.epd.sleep()

        except Exception as e:
            logger.error(f"Error displaying image: {e}")
            raise

    def display(self, uploaded_image):
        """
        Prepare and display an uploaded image.

        Args:
            uploaded_image: PIL.Image to display
        """
        logger.info("Processing image for display")

        try:
            # Prepare image with offset
            prepared_image = self.prepare_image(uploaded_image)

            # Display the image
            self.display_image(prepared_image)
            logger.info("Display updated successfully")

        except Exception as e:
            logger.error(f"Error displaying image: {e}")
            raise


def init_client():
    """Initialize the display client if not already initialized."""
    global client
    if client is None:
        logger.info("Initializing display client")
        client = DisplayClient()
    return client


@app.route("/api/display", methods=["POST"])
def api_display():
    """
    API endpoint to trigger display update.
    Expects multipart/form-data with 'image' file field.
    """
    try:
        # Check if file is present in request
        if "image" not in request.files:
            return jsonify({"error": "No image file provided"}), 400

        file = request.files["image"]

        # Check if file is empty
        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400

        logger.info(f"Received display request with image file: {file.filename}")

        # Read image from uploaded file
        image_data = file.read()
        uploaded_image = Image.open(BytesIO(image_data))
        logger.info("Successfully read image")

        # Call client.display with the uploaded image
        global client
        if client is None:
            logger.info("Display not initialized. Displaying image failed.")

            return jsonify({"error": "Display client not initialized"}), 500

        client.display(uploaded_image)

        return jsonify(
            {"success": True, "message": "Display updated successfully"}
        ), 200

    except Exception as e:
        logger.error(f"Error in /api/display endpoint: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/dimension", methods=["GET"])
def api_dimension():
    """
    API endpoint to get EPD dimensions.
    Returns the width and height of the currently initialized EPD.
    """
    try:
        global client
        if client is None or client.epd is None:
            logger.warning("EPD not initialized for dimension request")
            return jsonify({"error": "EPD not initialized"}), 500

        width = client.epd.width
        height = client.epd.height

        logger.info(f"Returning EPD dimensions: {width}x{height}")
        return jsonify({"width": width, "height": height}), 200

    except Exception as e:
        logger.error(f"Error in /api/dimension endpoint: {e}")
        return jsonify({"error": str(e)}), 500


def _draw_calibration_frame(width, height, offset):
    """
    Draw a calibration frame with outward-pointing corner arrows and centered offset number.

    Args:
        width: Display width in pixels.
        height: Display height in pixels.
        offset: Current calibration offset (arrows move inward by this many pixels).

    Returns:
        PIL.Image with the calibration pattern.
    """
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    line_width = 2
    wing = 10
    shaft = 7

    # Top-left: arrow tip at (offset, offset), wings along top and left edges
    tl = (offset, offset)
    draw.line([tl, (offset + wing, offset)], fill=0, width=line_width)
    draw.line([tl, (offset, offset + wing)], fill=0, width=line_width)
    draw.line([(offset + shaft, offset + shaft), tl], fill=0, width=line_width)

    # Top-right: arrow tip at (width-1-offset, offset)
    tr = (width - 1 - offset, offset)
    draw.line([tr, (tr[0] - wing, offset)], fill=0, width=line_width)
    draw.line([tr, (tr[0], offset + wing)], fill=0, width=line_width)
    draw.line([(tr[0] - shaft, offset + shaft), tr], fill=0, width=line_width)

    # Bottom-left: arrow tip at (offset, height-1-offset)
    bl = (offset, height - 1 - offset)
    draw.line([bl, (offset + wing, bl[1])], fill=0, width=line_width)
    draw.line([bl, (offset, bl[1] - wing)], fill=0, width=line_width)
    draw.line([(offset + shaft, bl[1] - shaft), bl], fill=0, width=line_width)

    # Bottom-right: arrow tip at (width-1-offset, height-1-offset)
    br = (width - 1 - offset, height - 1 - offset)
    draw.line([br, (br[0] - wing, br[1])], fill=0, width=line_width)
    draw.line([br, (br[0], br[1] - wing)], fill=0, width=line_width)
    draw.line([(br[0] - shaft, br[1] - shaft), br], fill=0, width=line_width)

    # Draw centered offset number
    font = ImageFont.load_default()
    text = str(offset)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(
        ((width - text_w) // 2, (height - text_h) // 2),
        text,
        fill=0,
        font=font,
    )

    return img


def _calibrate(display_client, iterations=20, interval=10):
    """
    Run a blocking calibration sequence on the e-ink display.

    Args:
        display_client: DisplayClient instance.
        iterations: Number of frames to display.
        interval: Seconds between refreshes.
    """
    width = display_client.epd.width
    height = display_client.epd.height

    for i in range(iterations):
        logger.info(f"Calibration iteration {i}/{iterations - 1}")
        frame = _draw_calibration_frame(width, height, i)
        display_client.display_image(frame)
        if i < iterations - 1:
            time.sleep(interval)


@app.route("/api/calibrate", methods=["POST"])
def api_calibrate():
    """
    API endpoint to run display calibration.
    Displays 20 frames with corner arrows moving inward, 10 seconds apart.
    """
    try:
        global client
        if client is None:
            logger.warning("Display not initialized for calibration request")
            return jsonify({"error": "Display client not initialized"}), 500

        logger.info("Starting display calibration")
        _calibrate(client)
        logger.info("Display calibration complete")

        return jsonify({
            "success": True,
            "message": "Calibration complete",
            "iterations": 20,
        }), 200

    except Exception as e:
        logger.error(f"Error in /api/calibrate endpoint: {e}")
        return jsonify({"error": str(e)}), 500


def main():
    """Entry point for display client."""

    # Ensure client is initialized (already done at module level, but safe to call again)
    init_client()

    # Get configuration from environment
    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_PORT", 5000))

    logger.info(f"Starting Flask API server on {host}:{port}")

    # Start Flask server
    app.run(host=host, port=port, debug=False)


# Initialize client when module is loaded (for Gunicorn compatibility)
init_client()

if __name__ == "__main__":
    main()
