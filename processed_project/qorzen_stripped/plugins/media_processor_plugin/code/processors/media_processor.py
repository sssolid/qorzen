from __future__ import annotations
import asyncio
import io
from io import BytesIO
from PIL.Image import Resampling
from blib2to3.pygram import initialize
from ..utils.ai_background_remover import AIBackgroundRemover
from ..utils.config_manager import ConfigManager
from ..utils.font_manager import FontManager
'\nMain media processor implementation.\n\nThis module contains the core logic for processing media files,\nincluding background removal and applying output formats.\n'
import os
import pathlib
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, BinaryIO, cast
import PIL
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
import piexif
from qorzen.core.file_manager import FileManager
from qorzen.core.task_manager import TaskManager
from ..models.processing_config import ProcessingConfig, BackgroundRemovalConfig, BackgroundRemovalMethod, OutputFormat, ResizeMode, ImageFormat, WatermarkType, WatermarkPosition
from ..utils.exceptions import MediaProcessingError, ImageProcessingError
from ..utils.path_resolver import resolve_output_path, generate_filename
class MediaProcessor:
    def __init__(self, file_manager: FileManager, task_manager: TaskManager, logger: Any, processing_config: Dict[str, Any], background_removal_config: Dict[str, Any]) -> None:
        self._file_manager = file_manager
        self._task_manager = task_manager
        self._logger = logger
        self._processing_config = processing_config
        self._background_removal_config = background_removal_config
        self._config_manager = ConfigManager(self._file_manager, self._logger)
        self._font_manager = FontManager(self._logger)
        self._ai_background_remover = AIBackgroundRemover(self._file_manager, self._config_manager, self._logger)
        self._default_output_dir = processing_config.get('default_output_dir', 'output')
        self._temp_dir = processing_config.get('temp_dir', 'temp')
        self._initialize_directories()
        self._loaded_configs: Dict[str, ProcessingConfig] = {}
        self._init_pil()
        self._logger.info('Media processor initialized')
    def _init_pil(self) -> None:
        try:
            self._logger.debug(f'PIL version: {PIL.__version__}')
            try:
                default_font = ImageFont.load_default()
                self._logger.debug('Default font loaded successfully')
            except Exception as e:
                self._logger.warning(f'Could not load default font: {e}')
        except Exception as e:
            self._logger.error(f'Error initializing PIL: {e}')
    def _initialize_directories(self) -> None:
        os.makedirs(self._default_output_dir, exist_ok=True)
        os.makedirs(self._temp_dir, exist_ok=True)
        self._logger.debug(f'Directories initialized. Output: {self._default_output_dir}, Temp: {self._temp_dir}')
    async def load_image_from_bytes(self, image_data: bytes) -> Image.Image:
        try:
            return Image.open(io.BytesIO(image_data))
        except Exception as e:
            self._logger.error(f'Failed to load image from bytes: {str(e)}')
            raise MediaProcessingError(f'Failed to load image from bytes: {str(e)}')
    async def load_image(self, image_path: str) -> Image.Image:
        try:
            if image_path.lower().endswith('.psd'):
                return await self._load_psd(image_path)
            if not os.path.isabs(image_path):
                try:
                    image_data = await self._file_manager.read_binary(image_path)
                    return Image.open(io.BytesIO(image_data))
                except Exception as e:
                    self._logger.warning(f'Could not load image via file manager: {e}, trying direct path')
            return Image.open(image_path)
        except PIL.UnidentifiedImageError:
            self._logger.error(f'Unidentified image format: {image_path}')
            raise MediaProcessingError(f'Unidentified image format. Please ensure the file is a valid image.')
        except Exception as e:
            self._logger.error(f'Failed to load image {image_path}: {str(e)}')
            raise MediaProcessingError(f'Failed to load image: {str(e)}')
    async def _load_psd(self, image_path: str) -> Image.Image:
        try:
            try:
                if not os.path.isabs(image_path):
                    try:
                        image_data = await self._file_manager.read_binary(image_path)
                        return Image.open(io.BytesIO(image_data))
                    except Exception:
                        pass
                return Image.open(image_path)
            except Exception as e:
                self._logger.warning(f'Standard PSD loading failed: {e}, trying enhanced method')
            try:
                from psd_tools import PSDImage
                psd = PSDImage.open(image_path)
                return psd.composite()
            except ImportError:
                self._logger.warning('psd-tools not available, falling back to basic PSD support')
                return Image.open(image_path)
        except Exception as e:
            self._logger.error(f'Failed to load PSD {image_path}: {str(e)}')
            raise MediaProcessingError(f'Failed to load PSD file: {str(e)}')
    async def remove_background(self, image: Image.Image, config: BackgroundRemovalConfig) -> Image.Image:
        try:
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            if config.method == BackgroundRemovalMethod.CHROMA_KEY:
                result = await self._remove_background_chroma(image, config)
            elif config.method == BackgroundRemovalMethod.ALPHA_MATTING:
                result = await self._remove_background_alpha_matting(image, config)
            elif config.method == BackgroundRemovalMethod.ML_MODEL:
                result = await self._remove_background_ml(image, config)
            elif config.method == BackgroundRemovalMethod.SMART_SELECTION:
                result = await self._remove_background_smart(image, config)
            elif config.method == BackgroundRemovalMethod.MANUAL_MASK:
                result = await self._remove_background_manual(image, config)
            else:
                raise MediaProcessingError(f'Unsupported background removal method: {config.method}')
            if config.edge_feather > 0:
                result = self._apply_edge_feather(result, config.edge_feather)
            if config.refine_edge:
                result = self._refine_edges(result)
            if config.denoise:
                result = self._denoise_mask(result)
            return result
        except Exception as e:
            self._logger.error(f'Background removal failed: {str(e)}')
            raise MediaProcessingError(f'Background removal failed: {str(e)}')
    async def _remove_background_chroma(self, image: Image.Image, config: BackgroundRemovalConfig) -> Image.Image:
        try:
            if not config.chroma_color:
                raise ValueError('Chroma color not specified')
            chroma_color = config.chroma_color.lstrip('#')
            if len(chroma_color) == 3:
                r, g, b = [int(c * 2, 16) for c in chroma_color]
            else:
                r, g, b = [int(chroma_color[i:i + 2], 16) for i in (0, 2, 4)]
            result = image.copy()
            width, height = result.size
            pixels = result.load()
            for y in range(height):
                for x in range(width):
                    p_r, p_g, p_b, p_a = pixels[x, y]
                    distance = ((p_r - r) ** 2 + (p_g - g) ** 2 + (p_b - b) ** 2) ** 0.5
                    if distance <= config.chroma_tolerance:
                        alpha_factor = distance / config.chroma_tolerance
                        new_alpha = int(alpha_factor * 255)
                        pixels[x, y] = (p_r, p_g, p_b, min(new_alpha, p_a))
            return result
        except Exception as e:
            self._logger.error(f'Chroma key background removal failed: {str(e)}')
            raise MediaProcessingError(f'Chroma key background removal failed: {str(e)}')
    async def _remove_background_alpha_matting(self, image: Image.Image, config: BackgroundRemovalConfig) -> Image.Image:
        try:
            result = image.copy()
            gray = image.convert('L')
            mask = Image.new('L', image.size, 0)
            mask_pixels = mask.load()
            gray_pixels = gray.load()
            width, height = image.size
            for y in range(height):
                for x in range(width):
                    brightness = gray_pixels[x, y]
                    if brightness >= config.alpha_foreground_threshold:
                        mask_pixels[x, y] = 255
                    elif brightness <= config.alpha_background_threshold:
                        mask_pixels[x, y] = 0
                    else:
                        alpha = (brightness - config.alpha_background_threshold) / (config.alpha_foreground_threshold - config.alpha_background_threshold)
                        mask_pixels[x, y] = int(alpha * 255)
            r, g, b, a = result.split()
            result = Image.merge('RGBA', (r, g, b, mask))
            return result
        except Exception as e:
            self._logger.error(f'Alpha matting background removal failed: {str(e)}')
            raise MediaProcessingError(f'Alpha matting background removal failed: {str(e)}')
    async def _remove_background_ml(self, image: Image.Image, config: BackgroundRemovalConfig) -> Image.Image:
        try:
            self._logger.info(f'Using ML model {config.model_name} for background removal')
            width, height = image.size
            mask = Image.new('L', (width, height), 0)
            draw = ImageDraw.Draw(mask)
            center_x, center_y = (width // 2, height // 2)
            max_dist = ((width // 2) ** 2 + (height // 2) ** 2) ** 0.5
            for y in range(height):
                for x in range(width):
                    dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                    alpha = max(0, 1 - dist / max_dist)
                    if alpha > config.confidence_threshold:
                        alpha = 1.0
                    elif alpha < config.confidence_threshold * 0.5:
                        alpha = 0.0
                    mask.putpixel((x, y), int(alpha * 255))
            r, g, b, a = image.split()
            result = Image.merge('RGBA', (r, g, b, mask))
            self._logger.debug('ML-based background removal completed')
            return result
        except Exception as e:
            self._logger.error(f'ML background removal failed: {str(e)}')
            raise MediaProcessingError(f'ML background removal failed: {str(e)}')
    async def _remove_background_smart(self, image: Image.Image, config: BackgroundRemovalConfig) -> Image.Image:
        try:
            width, height = image.size
            mask = Image.new('L', (width, height), 0)
            draw = ImageDraw.Draw(mask)
            center_x, center_y = (width // 2, height // 2)
            radius = min(width, height) // 2 - config.smart_brush_size
            draw.ellipse((center_x - radius, center_y - radius, center_x + radius, center_y + radius), fill=255)
            if config.smart_feather_amount > 0:
                mask = mask.filter(ImageFilter.GaussianBlur(config.smart_feather_amount))
            r, g, b, a = image.split()
            result = Image.merge('RGBA', (r, g, b, mask))
            return result
        except Exception as e:
            self._logger.error(f'Smart selection background removal failed: {str(e)}')
            raise MediaProcessingError(f'Smart selection background removal failed: {str(e)}')
    async def _remove_background_manual(self, image: Image.Image, config: BackgroundRemovalConfig) -> Image.Image:
        try:
            if not config.mask_path:
                raise ValueError('Mask path not specified for manual mask method')
            mask_image = await self.load_image(config.mask_path)
            if mask_image.mode != 'L':
                mask_image = mask_image.convert('L')
            if mask_image.size != image.size:
                mask_image = mask_image.resize(image.size, Resampling.LANCZOS)
            r, g, b, a = image.split()
            result = Image.merge('RGBA', (r, g, b, mask_image))
            return result
        except Exception as e:
            self._logger.error(f'Manual mask background removal failed: {str(e)}')
            raise MediaProcessingError(f'Manual mask background removal failed: {str(e)}')
    def _apply_edge_feather(self, image: Image.Image, feather_amount: int) -> Image.Image:
        if feather_amount <= 0:
            return image
        r, g, b, a = image.split()
        a_feathered = a.filter(ImageFilter.GaussianBlur(feather_amount))
        return Image.merge('RGBA', (r, g, b, a_feathered))
    def _refine_edges(self, image: Image.Image) -> Image.Image:
        r, g, b, a = image.split()
        a_refined = a.filter(ImageFilter.UnsharpMask(radius=1.0, percent=50, threshold=3))
        return Image.merge('RGBA', (r, g, b, a_refined))
    def _denoise_mask(self, image: Image.Image) -> Image.Image:
        r, g, b, a = image.split()
        a_denoised = a.filter(ImageFilter.MedianFilter(size=3))
        return Image.merge('RGBA', (r, g, b, a_denoised))
    async def apply_format(self, image: Image.Image, format_config: OutputFormat) -> Image.Image:
        try:
            result = image.copy()
            if format_config.crop_enabled and all((x is not None for x in [format_config.crop_left, format_config.crop_top, format_config.crop_right, format_config.crop_bottom])):
                left = cast(int, format_config.crop_left)
                top = cast(int, format_config.crop_top)
                right = cast(int, format_config.crop_right)
                bottom = cast(int, format_config.crop_bottom)
                width, height = result.size
                left = max(0, min(left, width - 1))
                top = max(0, min(top, height - 1))
                right = max(left + 1, min(right, width))
                bottom = max(top + 1, min(bottom, height))
                result = result.crop((left, top, right, bottom))
            if format_config.resize_mode != ResizeMode.NONE:
                result = self._resize_image(result, format_config)
            if format_config.rotation_angle != 0:
                result = result.rotate(format_config.rotation_angle, resample=Resampling.BICUBIC, expand=True, fillcolor=(0, 0, 0, 0) if result.mode == 'RGBA' else (255, 255, 255))
            if format_config.padding_enabled:
                result = self._apply_padding(result, format_config)
            if not format_config.transparent_background:
                result = self._apply_background(result, format_config.background_color or '#FFFFFF')
            result = self._apply_adjustments(result, format_config)
            if format_config.watermark.type != WatermarkType.NONE:
                result = await self._apply_watermark(result, format_config.watermark)
            return result
        except Exception as e:
            self._logger.error(f'Format application failed: {str(e)}')
            raise MediaProcessingError(f'Format application failed: {str(e)}')
    def _resize_image(self, image: Image.Image, format_config: OutputFormat) -> Image.Image:
        width, height = image.size
        resize_mode = format_config.resize_mode
        maintain_aspect = format_config.maintain_aspect_ratio
        new_width = width
        new_height = height
        if resize_mode == ResizeMode.WIDTH and format_config.width is not None:
            new_width = format_config.width
            if maintain_aspect:
                new_height = int(height * (new_width / width))
        elif resize_mode == ResizeMode.HEIGHT and format_config.height is not None:
            new_height = format_config.height
            if maintain_aspect:
                new_width = int(width * (new_height / height))
        elif resize_mode == ResizeMode.EXACT:
            if format_config.width is not None and format_config.height is not None:
                new_width = format_config.width
                new_height = format_config.height
        elif resize_mode == ResizeMode.MAX_DIMENSION:
            if format_config.width is not None and format_config.height is not None:
                width_ratio = format_config.width / width
                height_ratio = format_config.height / height
                ratio = min(width_ratio, height_ratio)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
            elif format_config.width is not None:
                if width > format_config.width:
                    new_width = format_config.width
                    if maintain_aspect:
                        new_height = int(height * (new_width / width))
            elif format_config.height is not None:
                if height > format_config.height:
                    new_height = format_config.height
                    if maintain_aspect:
                        new_width = int(width * (new_height / height))
        elif resize_mode == ResizeMode.MIN_DIMENSION:
            if format_config.width is not None and format_config.height is not None:
                width_ratio = format_config.width / width
                height_ratio = format_config.height / height
                ratio = max(width_ratio, height_ratio)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
            elif format_config.width is not None:
                if width < format_config.width:
                    new_width = format_config.width
                    if maintain_aspect:
                        new_height = int(height * (new_width / width))
            elif format_config.height is not None:
                if height < format_config.height:
                    new_height = format_config.height
                    if maintain_aspect:
                        new_width = int(width * (new_height / height))
        elif resize_mode == ResizeMode.PERCENTAGE and format_config.percentage is not None:
            ratio = format_config.percentage / 100.0
            new_width = int(width * ratio)
            new_height = int(height * ratio)
        new_width = max(1, new_width)
        new_height = max(1, new_height)
        if new_width != width or new_height != height:
            return image.resize((new_width, new_height), Resampling.LANCZOS)
        return image
    def _apply_padding(self, image: Image.Image, format_config: OutputFormat) -> Image.Image:
        width, height = image.size
        padding_left = format_config.padding_left
        padding_top = format_config.padding_top
        padding_right = format_config.padding_right
        padding_bottom = format_config.padding_bottom
        if padding_left == 0 and padding_top == 0 and (padding_right == 0) and (padding_bottom == 0):
            return image
        new_width = width + padding_left + padding_right
        new_height = height + padding_top + padding_bottom
        padding_color_str = format_config.padding_color or format_config.background_color or '#FFFFFF'
        padding_color = self._parse_color(padding_color_str)
        if image.mode == 'RGBA':
            new_image = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
        else:
            new_image = Image.new(image.mode, (new_width, new_height), padding_color)
        new_image.paste(image, (padding_left, padding_top))
        return new_image
    def _apply_background(self, image: Image.Image, background_color: str) -> Image.Image:
        if image.mode != 'RGBA':
            return image
        bg_color = self._parse_color(background_color)
        background = Image.new('RGBA', image.size, bg_color)
        return Image.alpha_composite(background, image).convert('RGB')
    def _apply_adjustments(self, image: Image.Image, format_config: OutputFormat) -> Image.Image:
        result = image
        if format_config.brightness != 1.0:
            enhancer = ImageEnhance.Brightness(result)
            result = enhancer.enhance(format_config.brightness)
        if format_config.contrast != 1.0:
            enhancer = ImageEnhance.Contrast(result)
            result = enhancer.enhance(format_config.contrast)
        if format_config.saturation != 1.0:
            enhancer = ImageEnhance.Color(result)
            result = enhancer.enhance(format_config.saturation)
        if format_config.sharpness != 1.0:
            enhancer = ImageEnhance.Sharpness(result)
            result = enhancer.enhance(format_config.sharpness)
        return result
    async def _apply_watermark(self, image: Image.Image, watermark_config: Any) -> Image.Image:
        if watermark_config.type == WatermarkType.NONE:
            return image
        result = image.copy()
        if watermark_config.type == WatermarkType.TEXT:
            return await self._apply_text_watermark(result, watermark_config)
        elif watermark_config.type == WatermarkType.IMAGE:
            return await self._apply_image_watermark(result, watermark_config)
        return result
    async def _apply_text_watermark(self, image: Image.Image, watermark_config: Any) -> Image.Image:
        if not watermark_config.text:
            return image
        result = image.copy()
        width, height = result.size
        overlay = Image.new('RGBA', result.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        try:
            font = ImageFont.truetype(watermark_config.font_name, watermark_config.font_size)
        except IOError:
            self._logger.warning(f'Could not load font {watermark_config.font_name}, using default')
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), watermark_config.text, font=font)
        text_width = int(bbox[2] - bbox[0])
        text_height = int(bbox[3] - bbox[1])
        position = self._calculate_watermark_position(watermark_config.position, width, height, text_width, text_height, watermark_config.margin, watermark_config.custom_position_x, watermark_config.custom_position_y)
        if watermark_config.outline_width > 0 and watermark_config.outline_color:
            outline_color = self._parse_color(watermark_config.outline_color)
            for offset_x in range(-watermark_config.outline_width, watermark_config.outline_width + 1):
                for offset_y in range(-watermark_config.outline_width, watermark_config.outline_width + 1):
                    if offset_x == 0 and offset_y == 0:
                        continue
                    draw.text((position[0] + offset_x, position[1] + offset_y), watermark_config.text, font=font, fill=outline_color)
        text_color = self._parse_color(watermark_config.font_color)
        draw.text(position, watermark_config.text, font=font, fill=text_color)
        if watermark_config.opacity < 1.0:
            mask = overlay.split()[3].point(lambda p: int(p * watermark_config.opacity))
            overlay.putalpha(mask)
        if watermark_config.rotation != 0:
            rotated = overlay.rotate(watermark_config.rotation, center=(position[0] + text_width // 2, position[1] + text_height // 2), resample=Resampling.BICUBIC, expand=False)
            overlay = rotated
        if result.mode == 'RGBA':
            result = Image.alpha_composite(result, overlay)
        else:
            temp = result.convert('RGBA')
            temp = Image.alpha_composite(temp, overlay)
            result = temp.convert(result.mode)
        return result
    async def _apply_image_watermark(self, image: Image.Image, watermark_config: Any) -> Image.Image:
        if not watermark_config.image_path:
            return image
        try:
            watermark_img = await self.load_image(watermark_config.image_path)
            if watermark_img.mode != 'RGBA':
                watermark_img = watermark_img.convert('RGBA')
            if watermark_config.scale != 1.0:
                orig_width, orig_height = watermark_img.size
                target_width = int(image.width * watermark_config.scale)
                target_height = int(orig_height * (target_width / orig_width))
                watermark_img = watermark_img.resize((target_width, target_height), Resampling.LANCZOS)
            if watermark_config.rotation != 0:
                watermark_img = watermark_img.rotate(watermark_config.rotation, resample=Resampling.BICUBIC, expand=True, fillcolor=(0, 0, 0, 0))
            if watermark_config.opacity < 1.0:
                r, g, b, a = watermark_img.split()
                a = a.point(lambda p: int(p * watermark_config.opacity))
                watermark_img = Image.merge('RGBA', (r, g, b, a))
            result = image.copy()
            if watermark_config.position == WatermarkPosition.TILED:
                tiled = Image.new('RGBA', result.size, (0, 0, 0, 0))
                wm_width, wm_height = watermark_img.size
                margin = watermark_config.margin
                step_x = wm_width + margin
                step_y = wm_height + margin
                for y in range(0, result.height, step_y):
                    for x in range(0, result.width, step_x):
                        tiled.paste(watermark_img, (x, y), watermark_img)
                if result.mode == 'RGBA':
                    result = Image.alpha_composite(result, tiled)
                else:
                    temp = result.convert('RGBA')
                    temp = Image.alpha_composite(temp, tiled)
                    result = temp.convert(result.mode)
            else:
                wm_width, wm_height = watermark_img.size
                position = self._calculate_watermark_position(watermark_config.position, result.width, result.height, wm_width, wm_height, watermark_config.margin, watermark_config.custom_position_x, watermark_config.custom_position_y)
                if result.mode == 'RGBA':
                    overlay = Image.new('RGBA', result.size, (0, 0, 0, 0))
                    overlay.paste(watermark_img, position, watermark_img)
                    result = Image.alpha_composite(result, overlay)
                else:
                    temp = result.convert('RGBA')
                    overlay = Image.new('RGBA', temp.size, (0, 0, 0, 0))
                    overlay.paste(watermark_img, position, watermark_img)
                    temp = Image.alpha_composite(temp, overlay)
                    result = temp.convert(result.mode)
            return result
        except Exception as e:
            self._logger.error(f'Error applying image watermark: {e}')
            return image
    def _calculate_watermark_position(self, position: WatermarkPosition, img_width: int, img_height: int, watermark_width: int, watermark_height: int, margin: int, custom_x: Optional[float]=None, custom_y: Optional[float]=None) -> Tuple[int, int]:
        if position == WatermarkPosition.CUSTOM and custom_x is not None and (custom_y is not None):
            x = int(img_width * custom_x - watermark_width / 2)
            y = int(img_height * custom_y - watermark_height / 2)
        elif position == WatermarkPosition.TOP_LEFT:
            x, y = (margin, margin)
        elif position == WatermarkPosition.TOP_CENTER:
            x, y = ((img_width - watermark_width) // 2, margin)
        elif position == WatermarkPosition.TOP_RIGHT:
            x, y = (img_width - watermark_width - margin, margin)
        elif position == WatermarkPosition.MIDDLE_LEFT:
            x, y = (margin, (img_height - watermark_height) // 2)
        elif position == WatermarkPosition.MIDDLE_CENTER:
            x, y = ((img_width - watermark_width) // 2, (img_height - watermark_height) // 2)
        elif position == WatermarkPosition.MIDDLE_RIGHT:
            x, y = (img_width - watermark_width - margin, (img_height - watermark_height) // 2)
        elif position == WatermarkPosition.BOTTOM_LEFT:
            x, y = (margin, img_height - watermark_height - margin)
        elif position == WatermarkPosition.BOTTOM_CENTER:
            x, y = ((img_width - watermark_width) // 2, img_height - watermark_height - margin)
        else:
            x, y = (img_width - watermark_width - margin, img_height - watermark_height - margin)
        return (x, y)
    def _parse_color(self, color_str: str) -> Tuple[int, int, int, int]:
        color_str = color_str.lstrip('#')
        if len(color_str) == 3:
            r = int(color_str[0] + color_str[0], 16)
            g = int(color_str[1] + color_str[1], 16)
            b = int(color_str[2] + color_str[2], 16)
            return (r, g, b, 255)
        elif len(color_str) == 6:
            r = int(color_str[0:2], 16)
            g = int(color_str[2:4], 16)
            b = int(color_str[4:6], 16)
            return (r, g, b, 255)
        elif len(color_str) == 8:
            r = int(color_str[0:2], 16)
            g = int(color_str[2:4], 16)
            b = int(color_str[4:6], 16)
            a = int(color_str[6:8], 16)
            return (r, g, b, a)
        else:
            return (0, 0, 0, 255)
    async def save_image(self, image: Image.Image, output_path: str, format_config: OutputFormat, overwrite: bool=False) -> str:
        try:
            output_format = format_config.format.value.upper()
            if output_format == 'JPEG':
                output_format = 'JPEG'
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            if os.path.exists(output_path) and (not overwrite):
                base_name, ext = os.path.splitext(output_path)
                counter = 1
                new_path = f'{base_name}_{counter}{ext}'
                while os.path.exists(new_path):
                    counter += 1
                    new_path = f'{base_name}_{counter}{ext}'
                output_path = new_path
            save_args: Dict[str, Any] = {}
            if output_format in ('JPEG', 'WEBP'):
                if image.mode == 'RGBA':
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[3])
                    image = background
                save_args['quality'] = format_config.quality
            elif output_format == 'PNG':
                save_args['optimize'] = True
            elif output_format == 'TIFF':
                save_args['compression'] = 'tiff_lzw'
            exif_data = None
            if format_config.preserve_exif and hasattr(image, 'info') and ('exif' in image.info):
                exif_data = image.info['exif']
                if format_config.custom_exif and output_format in ('JPEG', 'TIFF'):
                    try:
                        exif_dict = piexif.load(exif_data)
                        for key, value in format_config.custom_exif.items():
                            if key.lower() == 'artist':
                                exif_dict['0th'][piexif.ImageIFD.Artist] = value.encode('utf-8')
                            elif key.lower() == 'copyright':
                                exif_dict['0th'][piexif.ImageIFD.Copyright] = value.encode('utf-8')
                            elif key.lower() == 'description':
                                exif_dict['0th'][piexif.ImageIFD.ImageDescription] = value.encode('utf-8')
                            elif key.lower() == 'software':
                                exif_dict['0th'][piexif.ImageIFD.Software] = value.encode('utf-8')
                            elif key.lower() == 'datetime':
                                exif_dict['0th'][piexif.ImageIFD.DateTime] = value.encode('utf-8')
                            elif key.lower() == 'comment':
                                exif_dict['Exif'][piexif.ExifIFD.UserComment] = value.encode('utf-8')
                        exif_data = piexif.dump(exif_dict)
                    except Exception as e:
                        self._logger.warning(f'Failed to merge custom EXIF data: {str(e)}')
            elif format_config.custom_exif and output_format in ('JPEG', 'TIFF'):
                try:
                    exif_dict = {'0th': {}, 'Exif': {}, 'GPS': {}, '1st': {}, 'thumbnail': None}
                    for key, value in format_config.custom_exif.items():
                        if key.lower() == 'artist':
                            exif_dict['0th'][piexif.ImageIFD.Artist] = value.encode('utf-8')
                        elif key.lower() == 'copyright':
                            exif_dict['0th'][piexif.ImageIFD.Copyright] = value.encode('utf-8')
                        elif key.lower() == 'description':
                            exif_dict['0th'][piexif.ImageIFD.ImageDescription] = value.encode('utf-8')
                        elif key.lower() == 'software':
                            exif_dict['0th'][piexif.ImageIFD.Software] = value.encode('utf-8')
                        elif key.lower() == 'datetime':
                            exif_dict['0th'][piexif.ImageIFD.DateTime] = value.encode('utf-8')
                        elif key.lower() == 'comment':
                            exif_dict['Exif'][piexif.ExifIFD.UserComment] = value.encode('utf-8')
                    exif_data = piexif.dump(exif_dict)
                except Exception as e:
                    self._logger.warning(f'Failed to create custom EXIF data: {str(e)}')
            if exif_data and output_format in ('JPEG', 'TIFF'):
                save_args['exif'] = exif_data
            image.save(output_path, format=output_format, **save_args)
            self._logger.debug(f'Image saved to {output_path}')
            return output_path
        except Exception as e:
            self._logger.error(f'Error saving image with EXIF: {str(e)}')
            raise MediaProcessingError(f'Error saving image with EXIF: {str(e)}')
    async def load_processing_config(self, config_path: str) -> ProcessingConfig:
        try:
            import json
            if not os.path.isabs(config_path):
                try:
                    config_data = await self._file_manager.read_text(config_path)
                except Exception as e:
                    self._logger.warning(f'Could not load config via file manager: {e}, trying direct path')
                    with open(config_path, 'r') as f:
                        config_data = f.read()
            else:
                with open(config_path, 'r') as f:
                    config_data = f.read()
            config_dict = json.loads(config_data)
            config = ProcessingConfig(**config_dict)
            self._loaded_configs[config.id] = config
            self._logger.debug(f"Loaded processing config '{config.name}' from {config_path}")
            return config
        except Exception as e:
            self._logger.error(f'Error loading processing config: {str(e)}')
            raise MediaProcessingError(f'Error loading processing config: {str(e)}')
    async def save_processing_config(self, config: ProcessingConfig, config_path: str) -> str:
        try:
            import json
            config.updated_at = datetime.now()
            config_dict = config.model_dump()
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            if await self._file_manager.write_text(config_path, json.dumps(config_dict, indent=2, default=str)):
                self._logger.debug(f"Saved processing config '{config.name}' to {config_path}")
                return config_path
            else:
                with open(config_path, 'w') as f:
                    json.dump(config_dict, f, indent=2, default=str)
                self._logger.debug(f"Saved processing config '{config.name}' to {config_path} (direct)")
                return config_path
        except Exception as e:
            self._logger.error(f'Error saving processing config: {str(e)}')
            raise MediaProcessingError(f'Error saving processing config: {str(e)}')
    async def process_image(self, image_path: str, config: ProcessingConfig, output_dir: Optional[str]=None, overwrite: bool=False) -> List[str]:
        try:
            self._logger.info(f'Processing image {image_path}')
            image = await self.load_image(image_path)
            self._logger.debug(f'Loaded image: {image.size[0]}x{image.size[1]} {image.mode}')
            if config.background_removal.method != BackgroundRemovalMethod.NONE:
                self._logger.debug(f'Removing background using {config.background_removal.method}')
                image = await self.remove_background(image, config.background_removal)
            base_output_dir = output_dir or config.output_directory or self._default_output_dir
            os.makedirs(base_output_dir, exist_ok=True)
            output_paths = []
            for format_config in config.output_formats:
                self._logger.debug(f'Applying format: {format_config.name}')
                formatted_image = await self.apply_format(image, format_config)
                filename = os.path.basename(image_path)
                name, ext = os.path.splitext(filename)
                if format_config.naming_template:
                    output_filename = generate_filename(format_config.naming_template, name, format_config.format.value, format_config.prefix, format_config.suffix)
                else:
                    prefix = format_config.prefix or ''
                    suffix = format_config.suffix or ''
                    output_filename = f'{prefix}{name}{suffix}.{format_config.format.value}'
                if format_config.subdir:
                    format_output_dir = os.path.join(base_output_dir, format_config.subdir)
                else:
                    format_output_dir = base_output_dir
                output_path = os.path.join(format_output_dir, output_filename)
                os.makedirs(format_output_dir, exist_ok=True)
                saved_path = await self.save_image(formatted_image, output_path, format_config, overwrite)
                output_paths.append(saved_path)
                self._logger.debug(f'Saved output: {saved_path}')
            self._logger.info(f'Image processing complete, generated {len(output_paths)} outputs')
            return output_paths
        except Exception as e:
            self._logger.error(f'Error processing image: {str(e)}')
            raise MediaProcessingError(f'Error processing image: {str(e)}')
    async def create_preview(self, image_path: str, config: Union[ProcessingConfig, OutputFormat, BackgroundRemovalConfig], size: int=0) -> bytes:
        try:
            image = await self.load_image(image_path)
            if size > 0 and (image.width > size or image.height > size):
                if image.width > image.height:
                    width = size
                    height = int(image.height * (width / image.width))
                else:
                    height = size
                    width = int(image.width * (height / image.height))
                image = image.resize((width, height), Resampling.LANCZOS)
            if isinstance(config, ProcessingConfig):
                if config.background_removal.method != BackgroundRemovalMethod.NONE:
                    image = await self.remove_background(image, config.background_removal)
                if config.output_formats:
                    image = await self.apply_format(image, config.output_formats[0])
            elif isinstance(config, OutputFormat):
                image = await self.apply_format(image, config)
            elif isinstance(config, BackgroundRemovalConfig):
                image = await self.remove_background(image, config)
            from io import BytesIO
            output = BytesIO()
            image.save(output, format='PNG')
            return output.getvalue()
        except Exception as e:
            self._logger.error(f'Error creating preview: {str(e)}')
            raise MediaProcessingError(f'Error creating preview: {str(e)}')
    async def create_preview_from_image(self, image: Image.Image, format_config: OutputFormat, size: int=0) -> bytes:
        try:
            preview_image = image.copy()
            if size > 0 and (preview_image.width > size or preview_image.height > size):
                if preview_image.width > preview_image.height:
                    width = size
                    height = int(preview_image.height * (width / preview_image.width))
                else:
                    height = size
                    width = int(preview_image.width * (height / preview_image.height))
                preview_image = preview_image.resize((width, height), Image.LANCZOS)
            preview_image = await self.apply_format(preview_image, format_config)
            output = io.BytesIO()
            preview_image.save(output, format='PNG')
            return output.getvalue()
        except Exception as e:
            self._logger.error(f'Error creating preview from image: {str(e)}')
            raise MediaProcessingError(f'Error creating preview from image: {str(e)}')