#!/usr/bin/env python3
"""
Display Client for Bush Display
Lightweight Flask API server that receives uploaded images and displays them on e-ink hardware.
Provides /api/display endpoint that accepts multipart file uploads.
"""

import logging
import os
from io import BytesIO

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from PIL import Image

from epd import EPD

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
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
