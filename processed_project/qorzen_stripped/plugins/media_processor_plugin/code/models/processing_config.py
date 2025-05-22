from __future__ import annotations
'\nData models for media processing configurations.\n\nThis module contains the Pydantic models for processing configurations, \nbackground removal settings, and output format configurations.\n'
import uuid
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field, model_validator, field_validator
class BackgroundRemovalMethod(str, Enum):
    CHROMA_KEY = 'chroma_key'
    ALPHA_MATTING = 'alpha_matting'
    ML_MODEL = 'ml_model'
    SMART_SELECTION = 'smart_selection'
    MANUAL_MASK = 'manual_mask'
    NONE = 'none'
class BackgroundRemovalConfig(BaseModel):
    method: BackgroundRemovalMethod = Field(default=BackgroundRemovalMethod.ALPHA_MATTING, description='Method used for background removal')
    chroma_color: Optional[str] = Field(default='#00FF00', description='Color key to remove (for chroma key method)')
    chroma_tolerance: int = Field(default=30, description='Tolerance for color matching (0-255)', ge=0, le=255)
    alpha_foreground_threshold: int = Field(default=240, description='Threshold for foreground in alpha matting (0-255)', ge=0, le=255)
    alpha_background_threshold: int = Field(default=10, description='Threshold for background in alpha matting (0-255)', ge=0, le=255)
    model_name: str = Field(default='u2net', description='Name of ML model to use')
    confidence_threshold: float = Field(default=0.5, description='Confidence threshold for ML prediction (0.0-1.0)', ge=0.0, le=1.0)
    smart_brush_size: int = Field(default=20, description='Brush size for smart selection', ge=1)
    smart_feather_amount: int = Field(default=2, description='Feather amount for smart selection edges', ge=0)
    mask_path: Optional[str] = Field(default=None, description='Path to manual mask file')
    edge_feather: int = Field(default=2, description='Edge feathering amount to apply after removal', ge=0)
    refine_edge: bool = Field(default=True, description='Whether to apply edge refinement')
    denoise: bool = Field(default=False, description='Apply denoising to mask')
    @field_validator('chroma_color')
    def validate_chroma_color(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not (v.startswith('#') and len(v) in (4, 7)):
            raise ValueError("Chroma color must be a valid hex color (e.g., '#00FF00')")
        return v
    @property
    def as_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)
class WatermarkType(str, Enum):
    NONE = 'none'
    TEXT = 'text'
    IMAGE = 'image'
class WatermarkPosition(str, Enum):
    TOP_LEFT = 'top_left'
    TOP_CENTER = 'top_center'
    TOP_RIGHT = 'top_right'
    MIDDLE_LEFT = 'middle_left'
    MIDDLE_CENTER = 'middle_center'
    MIDDLE_RIGHT = 'middle_right'
    BOTTOM_LEFT = 'bottom_left'
    BOTTOM_CENTER = 'bottom_center'
    BOTTOM_RIGHT = 'bottom_right'
    TILED = 'tiled'
    CUSTOM = 'custom'
class WatermarkConfig(BaseModel):
    type: WatermarkType = Field(default=WatermarkType.NONE, description='Type of watermark to apply')
    text: Optional[str] = Field(default=None, description='Text for text watermark')
    font_name: str = Field(default='Arial', description='Font name for text watermark')
    font_size: int = Field(default=24, description='Font size for text watermark', ge=1)
    font_color: str = Field(default='#000000', description='Font color for text watermark')
    outline_color: Optional[str] = Field(default=None, description='Outline color for text watermark')
    outline_width: int = Field(default=0, description='Outline width for text watermark', ge=0)
    image_path: Optional[str] = Field(default=None, description='Path to image for image watermark')
    position: WatermarkPosition = Field(default=WatermarkPosition.BOTTOM_RIGHT, description='Position for watermark placement')
    opacity: float = Field(default=0.5, description='Opacity of watermark (0.0-1.0)', ge=0.0, le=1.0)
    scale: float = Field(default=0.2, description='Scale of watermark relative to image size', gt=0.0, le=1.0)
    margin: int = Field(default=10, description='Margin from edge of image (pixels)', ge=0)
    rotation: float = Field(default=0.0, description='Rotation angle in degrees', ge=-360.0, le=360.0)
    custom_position_x: Optional[float] = Field(default=None, description='Custom X position as percentage of image width', ge=0.0, le=1.0)
    custom_position_y: Optional[float] = Field(default=None, description='Custom Y position as percentage of image height', ge=0.0, le=1.0)
    @model_validator(mode='before')
    def check_watermark_type_requirements(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        watermark_type = values.get('type')
        if watermark_type == WatermarkType.TEXT:
            if not values.get('text'):
                raise ValueError('Text must be provided for text watermark')
        elif watermark_type == WatermarkType.IMAGE:
            if not values.get('image_path'):
                raise ValueError('Image path must be provided for image watermark')
        position = values.get('position')
        if position == WatermarkPosition.CUSTOM:
            if values.get('custom_position_x') is None or values.get('custom_position_y') is None:
                raise ValueError('Custom position requires both x and y coordinates')
        return values
class ResizeMode(str, Enum):
    NONE = 'none'
    WIDTH = 'width'
    HEIGHT = 'height'
    EXACT = 'exact'
    MAX_DIMENSION = 'max_dimension'
    MIN_DIMENSION = 'min_dimension'
    PERCENTAGE = 'percentage'
class ImageFormat(str, Enum):
    JPEG = 'jpeg'
    PNG = 'png'
    TIFF = 'tiff'
    BMP = 'bmp'
    WEBP = 'webp'
    PSD = 'psd'
    PDF = 'pdf'
class OutputFormat(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description='Unique identifier for this format')
    name: str = Field(description='User-friendly name for this format')
    format: ImageFormat = Field(default=ImageFormat.PNG, description='Output file format')
    suffix: Optional[str] = Field(default=None, description='Suffix to add to filename')
    prefix: Optional[str] = Field(default=None, description='Prefix to add to filename')
    naming_template: Optional[str] = Field(default=None, description='Template for output filenames')
    subdir: Optional[str] = Field(default=None, description='Subdirectory to save files in')
    transparent_background: bool = Field(default=False, description='Whether to use transparent background')
    background_color: Optional[str] = Field(default='#FFFFFF', description='Background color when not transparent')
    resize_mode: ResizeMode = Field(default=ResizeMode.NONE, description='Method to use for resizing')
    width: Optional[int] = Field(default=None, description='Target width in pixels', gt=0)
    height: Optional[int] = Field(default=None, description='Target height in pixels', gt=0)
    percentage: Optional[float] = Field(default=None, description='Resize percentage', gt=0)
    maintain_aspect_ratio: bool = Field(default=True, description='Whether to maintain aspect ratio during resize')
    crop_enabled: bool = Field(default=False, description='Whether to apply cropping')
    crop_left: Optional[int] = Field(default=None, description='Left crop position', ge=0)
    crop_top: Optional[int] = Field(default=None, description='Top crop position', ge=0)
    crop_right: Optional[int] = Field(default=None, description='Right crop position', ge=0)
    crop_bottom: Optional[int] = Field(default=None, description='Bottom crop position', ge=0)
    padding_enabled: bool = Field(default=False, description='Whether to apply padding')
    padding_left: int = Field(default=0, description='Left padding in pixels', ge=0)
    padding_top: int = Field(default=0, description='Top padding in pixels', ge=0)
    padding_right: int = Field(default=0, description='Right padding in pixels', ge=0)
    padding_bottom: int = Field(default=0, description='Bottom padding in pixels', ge=0)
    padding_color: Optional[str] = Field(default=None, description='Padding color (uses background_color if None)')
    rotation_angle: float = Field(default=0.0, description='Rotation angle in degrees', ge=-360.0, le=360.0)
    brightness: float = Field(default=1.0, description='Brightness adjustment factor', ge=0.0, le=2.0)
    contrast: float = Field(default=1.0, description='Contrast adjustment factor', ge=0.0, le=2.0)
    saturation: float = Field(default=1.0, description='Saturation adjustment factor', ge=0.0, le=2.0)
    sharpness: float = Field(default=1.0, description='Sharpness adjustment factor', ge=0.0, le=2.0)
    watermark: WatermarkConfig = Field(default_factory=WatermarkConfig, description='Watermark configuration')
    quality: int = Field(default=90, description='Output quality (0-100)', ge=1, le=100)
    preserve_exif: bool = Field(default=True, description='Whether to preserve original EXIF data')
    custom_exif: Dict[str, str] = Field(default_factory=dict, description='Custom EXIF data to add')
    @model_validator(mode='before')
    def validate_resize_mode_requirements(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        resize_mode = values.get('resize_mode', ResizeMode.NONE)
        if resize_mode == ResizeMode.WIDTH and values.get('width') is None:
            raise ValueError('Width must be specified for WIDTH resize mode')
        if resize_mode == ResizeMode.HEIGHT and values.get('height') is None:
            raise ValueError('Height must be specified for HEIGHT resize mode')
        if resize_mode == ResizeMode.EXACT:
            if values.get('width') is None or values.get('height') is None:
                raise ValueError('Both width and height must be specified for EXACT resize mode')
        if resize_mode == ResizeMode.MAX_DIMENSION or resize_mode == ResizeMode.MIN_DIMENSION:
            if values.get('width') is None and values.get('height') is None:
                raise ValueError(f'Either width or height must be specified for {resize_mode} resize mode')
        if resize_mode == ResizeMode.PERCENTAGE and values.get('percentage') is None:
            raise ValueError('Percentage must be specified for PERCENTAGE resize mode')
        return values
    @field_validator('background_color', 'padding_color')
    def validate_colors(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not (v.startswith('#') and len(v) in (4, 7)):
            raise ValueError("Color must be a valid hex color (e.g., '#FFFFFF')")
        return v
    @property
    def as_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)
class ProcessingConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description='Unique identifier for this configuration')
    name: str = Field(description='User-friendly name for this configuration')
    description: Optional[str] = Field(default=None, description='Detailed description of this configuration')
    created_at: datetime = Field(default_factory=datetime.now, description='When this configuration was created')
    updated_at: datetime = Field(default_factory=datetime.now, description='When this configuration was last updated')
    background_removal: BackgroundRemovalConfig = Field(default_factory=BackgroundRemovalConfig, description='Background removal configuration')
    output_formats: List[OutputFormat] = Field(default_factory=list, description='List of output formats to generate')
    output_directory: Optional[str] = Field(default=None, description='Base directory for output files')
    create_subfolder_for_batch: bool = Field(default=True, description='Create a subfolder for batch output')
    batch_subfolder_template: str = Field(default='batch_{timestamp}', description='Template for batch subfolder name')
    @model_validator(mode='before')
    def set_updated_time(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        values['updated_at'] = datetime.now()
        return values
    @field_validator('output_formats')
    def validate_output_formats(cls, v: List[OutputFormat]) -> List[OutputFormat]:
        if not v:
            raise ValueError('At least one output format must be specified')
        return v
    @property
    def as_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)