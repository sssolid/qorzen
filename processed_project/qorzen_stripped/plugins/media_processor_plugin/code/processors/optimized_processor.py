from __future__ import annotations
'\nProcessing optimization with intermediate images.\n\nThis module implements the ability to use a formatted intermediate image as the\nbase for subsequent format processing, improving performance for shared operations.\n'
import os
import tempfile
from typing import Dict, List, Optional, Set, Tuple, Any, Union, cast
from pathlib import Path
import asyncio
from PIL import Image
from ..models.processing_config import ProcessingConfig, BackgroundRemovalConfig, OutputFormat
from ..utils.exceptions import MediaProcessingError
class OptimizedProcessor:
    def __init__(self, media_processor: Any, logger: Any, use_intermediate: bool=True) -> None:
        self._media_processor = media_processor
        self._logger = logger
        self._use_intermediate = use_intermediate
        self._temp_dir = tempfile.mkdtemp(prefix='media_processor_')
        self._temp_files: List[str] = []
        self._logger.info(f'Optimized processor initialized with intermediate images: {use_intermediate}')
    def enable_intermediate_images(self, enabled: bool) -> None:
        self._use_intermediate = enabled
        self._logger.debug(f"Intermediate images {('enabled' if enabled else 'disabled')}")
    async def process_image(self, image_path: str, config: ProcessingConfig, output_dir: Optional[str]=None, overwrite: bool=False) -> List[str]:
        try:
            if not self._use_intermediate or len(config.output_formats) <= 1:
                return await self._media_processor.process_image(image_path, config, output_dir, overwrite)
            self._logger.info(f'Processing {image_path} with intermediate images')
            image = await self._media_processor.load_image(image_path)
            self._logger.debug(f'Loaded image: {image.size[0]}x{image.size[1]} {image.mode}')
            if config.background_removal.method.value != 'none':
                self._logger.debug(f'Removing background using {config.background_removal.method}')
                image = await self._media_processor.remove_background(image, config.background_removal)
                self._logger.debug('Background removal complete')
            intermediate_path = self._create_temp_file('intermediate.png')
            image.save(intermediate_path, format='PNG')
            self._logger.debug(f'Saved intermediate image to {intermediate_path}')
            base_output_dir = output_dir or config.output_directory or self._media_processor._default_output_dir
            os.makedirs(base_output_dir, exist_ok=True)
            output_paths = []
            for format_config in config.output_formats:
                self._logger.debug(f'Applying format: {format_config.name}')
                format_image = Image.open(intermediate_path)
                formatted_image = await self._media_processor.apply_format(format_image, format_config)
                filename = os.path.basename(image_path)
                name, ext = os.path.splitext(filename)
                if format_config.naming_template:
                    from ..utils.path_resolver import generate_filename
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
                saved_path = await self._media_processor.save_image(formatted_image, output_path, format_config, overwrite)
                output_paths.append(saved_path)
                self._logger.debug(f'Saved output: {saved_path}')
            self._logger.info(f'Image processing complete, generated {len(output_paths)} outputs')
            return output_paths
        except Exception as e:
            self._logger.error(f'Error in optimized processing: {str(e)}')
            raise MediaProcessingError(f'Optimized processing failed: {str(e)}')
        finally:
            self._cleanup_temp_files()
    async def batch_process_images(self, image_paths: List[str], config: ProcessingConfig, output_dir: Optional[str]=None, overwrite: bool=False, progress_callback: Optional[callable]=None) -> Dict[str, List[str]]:
        results: Dict[str, List[str]] = {}
        for i, image_path in enumerate(image_paths):
            try:
                if progress_callback:
                    progress = int(i / len(image_paths) * 100)
                    file_name = os.path.basename(image_path)
                    progress_callback(progress, f'Processing {file_name}...')
                output_paths = await self.process_image(image_path, config, output_dir, overwrite)
                results[image_path] = output_paths
            except Exception as e:
                self._logger.error(f'Error processing {image_path}: {str(e)}')
                results[image_path] = []
        if progress_callback:
            progress_callback(100, 'Processing complete')
        return results
    def _create_temp_file(self, suffix: str) -> str:
        temp_file = os.path.join(self._temp_dir, f'temp_{len(self._temp_files)}_{suffix}')
        self._temp_files.append(temp_file)
        return temp_file
    def _cleanup_temp_files(self) -> None:
        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                self._logger.warning(f'Error removing temp file {temp_file}: {str(e)}')
        self._temp_files = []
class ProcessingOptimizer:
    def __init__(self, logger: Any) -> None:
        self._logger = logger
    def should_use_intermediate(self, config: ProcessingConfig) -> bool:
        if len(config.output_formats) <= 1:
            return False
        if config.background_removal.method.value != 'none':
            return True
        common_operations = self._identify_common_operations(config.output_formats)
        return len(common_operations) > 0
    def _identify_common_operations(self, formats: List[OutputFormat]) -> Set[str]:
        operations = set()
        resize_modes = [f.resize_mode for f in formats]
        if len(set(resize_modes)) == 1 and formats[0].resize_mode.value != 'none':
            width_match = all((f.width == formats[0].width for f in formats))
            height_match = all((f.height == formats[0].height for f in formats))
            percentage_match = all((f.percentage == formats[0].percentage for f in formats))
            if width_match and height_match and percentage_match:
                operations.add('resize')
        watermark_types = [f.watermark.type for f in formats]
        if len(set(watermark_types)) == 1 and formats[0].watermark.type.value != 'none':
            if all((f.watermark.image_path == formats[0].watermark.image_path for f in formats)):
                operations.add('watermark')
        if len(set((f.rotation_angle for f in formats))) == 1 and formats[0].rotation_angle != 0:
            operations.add('rotation')
        if len(set((f.brightness for f in formats))) == 1 and formats[0].brightness != 1.0 or (len(set((f.contrast for f in formats))) == 1 and formats[0].contrast != 1.0) or (len(set((f.saturation for f in formats))) == 1 and formats[0].saturation != 1.0) or (len(set((f.sharpness for f in formats))) == 1 and formats[0].sharpness != 1.0):
            operations.add('adjustments')
        return operations