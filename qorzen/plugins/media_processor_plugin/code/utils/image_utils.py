from __future__ import annotations

from PIL.Image import Resampling

"""
Image processing utilities for the Media Processor Plugin.

This module provides utility functions for image processing
and format conversion for the Media Processor plugin.
"""

import io
import os
import math
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from PIL import Image, ImageOps, ImageFilter
from io import BytesIO


def get_image_info(file_path: str) -> Dict[str, Any]:
    """
    Get information about an image file.

    Args:
        file_path: Path to the image file

    Returns:
        Dictionary with image information

    Raises:
        IOError: If the file cannot be opened or is not a valid image
    """
    try:
        with Image.open(file_path) as img:
            info = {
                "format": img.format,
                "mode": img.mode,
                "width": img.width,
                "height": img.height,
                "size": os.path.getsize(file_path),
                "has_alpha": "A" in img.mode,
                "has_exif": hasattr(img, "_getexif") and img._getexif() is not None,
                "mime_type": f"image/{img.format.lower()}" if img.format else "image/unknown"
            }

            # Add EXIF info if available
            if info["has_exif"]:
                exif = img._getexif()
                if exif:
                    # Extract a few common EXIF tags
                    exif_data = {}
                    TAGS = {
                        271: "Make",
                        272: "Model",
                        306: "DateTime",
                        36867: "DateTimeOriginal",
                        37378: "ApertureValue",
                        37377: "ShutterSpeedValue",
                        34855: "ISOSpeedRatings",
                        37386: "FocalLength"
                    }

                    for tag_id, tag_name in TAGS.items():
                        if tag_id in exif:
                            exif_data[tag_name] = exif[tag_id]

                    info["exif"] = exif_data

            return info
    except Exception as e:
        raise IOError(f"Error reading image file: {str(e)}")


def is_transparent(image: Image.Image) -> bool:
    """
    Check if an image has transparency.

    Args:
        image: PIL Image object

    Returns:
        True if image has transparency, False otherwise
    """
    if image.mode in ('RGBA', 'LA'):
        # Check for transparent pixels
        if image.mode == 'RGBA':
            alpha = image.split()[3]
            return alpha.getextrema()[0] < 255
        else:  # LA mode
            alpha = image.split()[1]
            return alpha.getextrema()[0] < 255

    return False


def convert_to_format(
        image: Image.Image,
        format_name: str,
        quality: int = 90,
        transparent: bool = True
) -> bytes:
    """
    Convert an image to the specified format.

    Args:
        image: PIL Image object
        format_name: Target format name (e.g., "PNG", "JPEG")
        quality: Quality setting (1-100)
        transparent: Whether to preserve transparency

    Returns:
        Image data as bytes
    """
    output = BytesIO()

    # Uppercase format name
    format_name = format_name.upper()

    # Prepare image for output format
    if format_name in ('JPEG', 'JPG'):
        # JPEG doesn't support transparency
        if image.mode == 'RGBA' and not transparent:
            # Create white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode == 'RGBA':
            # Convert to RGB (lose transparency)
            image = image.convert('RGB')

        # Save with quality setting
        image.save(output, format='JPEG', quality=quality)

    elif format_name == 'PNG':
        # PNG supports transparency
        if transparent and image.mode != 'RGBA':
            # Convert to RGBA if needed
            image = image.convert('RGBA')
        elif not transparent and image.mode == 'RGBA':
            # Remove transparency
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background

        # Save with compression
        image.save(output, format='PNG', optimize=True)

    elif format_name == 'WEBP':
        # Save with quality setting and lossless for transparent images
        if transparent and is_transparent(image):
            # WebP supports transparency
            image.save(output, format='WEBP', quality=quality, lossless=True)
        else:
            image.save(output, format='WEBP', quality=quality)

    elif format_name == 'TIFF':
        # Save with compression
        image.save(output, format='TIFF', compression='tiff_lzw')

    elif format_name == 'BMP':
        # BMP doesn't support transparency
        if image.mode == 'RGBA':
            # Convert to RGB (lose transparency)
            image = image.convert('RGB')

        image.save(output, format='BMP')

    else:
        # Default to PNG for unsupported formats
        image.save(output, format='PNG')

    # Get bytes data
    output.seek(0)
    return output.getvalue()


def fit_image_to_size(
        image: Image.Image,
        max_width: int,
        max_height: int,
        maintain_aspect: bool = True
) -> Image.Image:
    """
    Resize an image to fit within the specified dimensions.

    Args:
        image: PIL Image object
        max_width: Maximum width
        max_height: Maximum height
        maintain_aspect: Whether to maintain aspect ratio

    Returns:
        Resized image
    """
    if maintain_aspect:
        # Calculate aspect ratios
        width_ratio = max_width / image.width
        height_ratio = max_height / image.height

        # Use the smaller ratio to ensure the image fits within bounds
        ratio = min(width_ratio, height_ratio)

        # Calculate new dimensions
        new_width = int(image.width * ratio)
        new_height = int(image.height * ratio)

        # Resize the image
        return image.resize((new_width, new_height), Resampling.LANCZOS)
    else:
        # Resize to exact dimensions
        return image.resize((max_width, max_height), Resampling.LANCZOS)


def create_gradient_mask(
        width: int,
        height: int,
        center_opacity: float = 1.0,
        edge_opacity: float = 0.0,
        radius_factor: float = 0.7
) -> Image.Image:
    """
    Create a radial gradient mask image.

    Args:
        width: Width of the mask
        height: Height of the mask
        center_opacity: Opacity at the center (0.0-1.0)
        edge_opacity: Opacity at the edges (0.0-1.0)
        radius_factor: Factor to determine gradient radius (0.0-1.0)

    Returns:
        Gradient mask as PIL Image
    """
    mask = Image.new('L', (width, height), 0)

    # Calculate center and maximum distance
    center_x, center_y = width // 2, height // 2
    max_dist = math.sqrt((width // 2) ** 2 + (height // 2) ** 2)
    radius = max_dist * radius_factor

    # Calculate opacity values
    center_value = int(center_opacity * 255)
    edge_value = int(edge_opacity * 255)

    # Fill mask with gradient
    pixels = mask.load()
    for y in range(height):
        for x in range(width):
            # Calculate distance from center
            dist = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)

            # Determine opacity based on distance
            if dist >= radius:
                pixels[x, y] = edge_value
            else:
                # Linear interpolation between center and edge
                ratio = dist / radius
                value = int(center_value * (1 - ratio) + edge_value * ratio)
                pixels[x, y] = value

    return mask


def apply_threshold_mask(
        image: Image.Image,
        threshold_min: int = 10,
        threshold_max: int = 240,
        feather: int = 0
) -> Image.Image:
    """
    Apply a threshold-based alpha mask to an image.

    Args:
        image: PIL Image object
        threshold_min: Minimum brightness threshold (0-255)
        threshold_max: Maximum brightness threshold (0-255)
        feather: Amount of feathering to apply to the mask

    Returns:
        Image with alpha mask applied
    """
    # Convert to grayscale for analysis
    gray = image.convert('L')

    # Create a mask based on brightness thresholds
    mask = Image.new('L', image.size, 0)
    mask_pixels = mask.load()
    gray_pixels = gray.load()
    width, height = image.size

    # Process each pixel
    for y in range(height):
        for x in range(width):
            brightness = gray_pixels[x, y]

            # Apply thresholds
            if brightness >= threshold_max:
                # Definite foreground
                mask_pixels[x, y] = 255
            elif brightness <= threshold_min:
                # Definite background
                mask_pixels[x, y] = 0
            else:
                # In-between area, apply linear interpolation
                alpha = (brightness - threshold_min) / (threshold_max - threshold_min)
                mask_pixels[x, y] = int(alpha * 255)

    # Apply feathering if requested
    if feather > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(feather))

    # Apply the mask to the image
    if image.mode != 'RGBA':
        image = image.convert('RGBA')

    r, g, b, _ = image.split()
    result = Image.merge('RGBA', (r, g, b, mask))

    return result


def auto_contrast_mask(mask: Image.Image, cutoff: float = 0.5) -> Image.Image:
    """
    Apply auto contrast to a mask to improve edge definition.

    Args:
        mask: PIL Image mask (L mode)
        cutoff: Percentage to cut off from histogram (0.0-1.0)

    Returns:
        Enhanced mask
    """
    # Ensure mask is in L mode
    if mask.mode != 'L':
        mask = mask.convert('L')

    # Apply auto contrast
    return ImageOps.autocontrast(mask, cutoff)


def generate_thumbnail(
        image: Image.Image,
        size: Union[int, Tuple[int, int]] = 256,
        maintain_aspect: bool = True
) -> Image.Image:
    """
    Generate a thumbnail from an image.

    Args:
        image: PIL Image object
        size: Maximum size as single value or (width, height) tuple
        maintain_aspect: Whether to maintain aspect ratio

    Returns:
        Thumbnail image
    """
    # Make a copy of the image
    thumbnail = image.copy()

    # Convert size to tuple if needed
    if isinstance(size, int):
        size = (size, size)

    if maintain_aspect:
        # Use PIL's thumbnail method which preserves aspect ratio
        thumbnail.thumbnail(size, Resampling.LANCZOS)
        return thumbnail
    else:
        # Resize to exact dimensions
        return thumbnail.resize(size, Resampling.LANCZOS)