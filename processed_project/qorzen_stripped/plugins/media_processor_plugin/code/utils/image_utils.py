from __future__ import annotations
from PIL.Image import Resampling
'\nImage processing utilities for the Media Processor Plugin.\n\nThis module provides utility functions for image processing\nand format conversion for the Media Processor plugin.\n'
import io
import os
import math
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image, ImageOps, ImageFilter
from io import BytesIO
def get_image_info(file_path: str) -> Dict[str, Any]:
    try:
        with Image.open(file_path) as img:
            info = {'format': img.format, 'mode': img.mode, 'width': img.width, 'height': img.height, 'size': os.path.getsize(file_path), 'has_alpha': 'A' in img.mode, 'has_exif': hasattr(img, '_getexif') and img._getexif() is not None, 'mime_type': f'image/{img.format.lower()}' if img.format else 'image/unknown'}
            if info['has_exif']:
                exif = img._getexif()
                if exif:
                    exif_data = {}
                    TAGS = {271: 'Make', 272: 'Model', 306: 'DateTime', 36867: 'DateTimeOriginal', 37378: 'ApertureValue', 37377: 'ShutterSpeedValue', 34855: 'ISOSpeedRatings', 37386: 'FocalLength'}
                    for tag_id, tag_name in TAGS.items():
                        if tag_id in exif:
                            exif_data[tag_name] = exif[tag_id]
                    info['exif'] = exif_data
            return info
    except Exception as e:
        raise IOError(f'Error reading image file: {str(e)}')
def is_transparent(image: Image.Image) -> bool:
    if image.mode in ('RGBA', 'LA'):
        if image.mode == 'RGBA':
            alpha = image.split()[3]
            return alpha.getextrema()[0] < 255
        else:
            alpha = image.split()[1]
            return alpha.getextrema()[0] < 255
    return False
def convert_to_format(image: Image.Image, format_name: str, quality: int=90, transparent: bool=True) -> bytes:
    output = BytesIO()
    format_name = format_name.upper()
    if format_name in ('JPEG', 'JPG'):
        if image.mode == 'RGBA' and (not transparent):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode == 'RGBA':
            image = image.convert('RGB')
        image.save(output, format='JPEG', quality=quality)
    elif format_name == 'PNG':
        if transparent and image.mode != 'RGBA':
            image = image.convert('RGBA')
        elif not transparent and image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        image.save(output, format='PNG', optimize=True)
    elif format_name == 'WEBP':
        if transparent and is_transparent(image):
            image.save(output, format='WEBP', quality=quality, lossless=True)
        else:
            image.save(output, format='WEBP', quality=quality)
    elif format_name == 'TIFF':
        image.save(output, format='TIFF', compression='tiff_lzw')
    elif format_name == 'BMP':
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        image.save(output, format='BMP')
    else:
        image.save(output, format='PNG')
    output.seek(0)
    return output.getvalue()
def fit_image_to_size(image: Image.Image, max_width: int, max_height: int, maintain_aspect: bool=True) -> Image.Image:
    if maintain_aspect:
        width_ratio = max_width / image.width
        height_ratio = max_height / image.height
        ratio = min(width_ratio, height_ratio)
        new_width = int(image.width * ratio)
        new_height = int(image.height * ratio)
        return image.resize((new_width, new_height), Resampling.LANCZOS)
    else:
        return image.resize((max_width, max_height), Resampling.LANCZOS)
def create_gradient_mask(width: int, height: int, center_opacity: float=1.0, edge_opacity: float=0.0, radius_factor: float=0.7) -> Image.Image:
    mask = Image.new('L', (width, height), 0)
    center_x, center_y = (width // 2, height // 2)
    max_dist = math.sqrt((width // 2) ** 2 + (height // 2) ** 2)
    radius = max_dist * radius_factor
    center_value = int(center_opacity * 255)
    edge_value = int(edge_opacity * 255)
    pixels = mask.load()
    for y in range(height):
        for x in range(width):
            dist = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
            if dist >= radius:
                pixels[x, y] = edge_value
            else:
                ratio = dist / radius
                value = int(center_value * (1 - ratio) + edge_value * ratio)
                pixels[x, y] = value
    return mask
def apply_threshold_mask(image: Image.Image, threshold_min: int=10, threshold_max: int=240, feather: int=0) -> Image.Image:
    gray = image.convert('L')
    mask = Image.new('L', image.size, 0)
    mask_pixels = mask.load()
    gray_pixels = gray.load()
    width, height = image.size
    for y in range(height):
        for x in range(width):
            brightness = gray_pixels[x, y]
            if brightness >= threshold_max:
                mask_pixels[x, y] = 255
            elif brightness <= threshold_min:
                mask_pixels[x, y] = 0
            else:
                alpha = (brightness - threshold_min) / (threshold_max - threshold_min)
                mask_pixels[x, y] = int(alpha * 255)
    if feather > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(feather))
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    r, g, b, _ = image.split()
    result = Image.merge('RGBA', (r, g, b, mask))
    return result
def auto_contrast_mask(mask: Image.Image, cutoff: float=0.5) -> Image.Image:
    if mask.mode != 'L':
        mask = mask.convert('L')
    return ImageOps.autocontrast(mask, cutoff)
def generate_thumbnail(image: Image.Image, size: Union[int, Tuple[int, int]]=256, maintain_aspect: bool=True) -> Image.Image:
    thumbnail = image.copy()
    if isinstance(size, int):
        size = (size, size)
    if maintain_aspect:
        thumbnail.thumbnail(size, Resampling.LANCZOS)
        return thumbnail
    else:
        return thumbnail.resize(size, Resampling.LANCZOS)