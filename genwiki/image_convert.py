"""
Created on 2025-03-04

@author: wf
"""

import io
from PIL import Image

class ImageConverter:
    """
    Converter for image formats with DPI and scale handling
    """

    def __init__(self, png_data: bytes, dpi: int):
        """
        Initialize the image converter

        Args:
            png_data: PNG image data as bytes
            dpi: Original DPI of the image
        """
        self.png_data = png_data
        self.dpi = dpi

    def convert_to_jpg(self, target_dpi: int = None, scale: float = None, quality: int = 85) -> bytes:
        """
        Convert PNG to JPG with optional scaling and quality settings to reduce file size/loading time

        Args:
            target_dpi: Target DPI for scaling. If provided, calculates scale based on original DPI.
            scale: Direct scale factor (0.0-1.0). Overrides target_dpi if both are provided.
            quality: JPEG quality (1-100), lower values = smaller file size, faster loading

        Returns:
            JPG image data as bytes
        """
        # Open image from bytes
        img = Image.open(io.BytesIO(self.png_data))

        # Determine scaling factor
        if scale is not None:
            # Use direct scale factor
            scaling_factor = scale
        elif target_dpi is not None and target_dpi < self.dpi:
            # Calculate scale based on DPI
            scaling_factor = target_dpi / self.dpi
        else:
            # No scaling
            scaling_factor = 1.0

        # Apply scaling if needed
        if scaling_factor < 1.0:
            new_width = int(img.width * scaling_factor)
            new_height = int(img.height * scaling_factor)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Convert to JPEG with specified quality
        output = io.BytesIO()
        img.convert("RGB").save(
            output,
            format="JPEG",
            quality=quality,
            optimize=True  # Enable JPEG optimization
        )

        # Get the bytes from the BytesIO object and assign to variable
        jpg_bytes = output.getvalue()

        # Return the bytes
        return jpg_bytes