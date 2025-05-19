from __future__ import annotations

"""
AI-based background removal processor using U2Net/ISNet models.

This module provides implementation for advanced background removal
using deep learning models like U2Net and ISNet.
"""

import os
import asyncio
import urllib.request
import zipfile
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Union, cast, Callable
from enum import Enum
import numpy as np
from pathlib import Path
import json

from PIL import Image, ImageFilter
import torch
import torchvision.transforms as transforms

from ..models.processing_config import BackgroundRemovalConfig
from ..utils.exceptions import BackgroundRemovalError


class ModelType(str, Enum):
    """Types of supported segmentation models."""
    U2NET = "u2net"
    U2NETP = "u2netp"
    ISNET = "isnet"
    MODNET = "modnet"


class ModelDetails:
    """Details about available models."""

    MODELS = {
        ModelType.U2NET: {
            "name": "U2Net",
            "description": "Original U2Net model for salient object detection",
            "url": "https://github.com/xuebinqin/U-2-Net/releases/download/U2NetHumanSeg/u2net_human_seg.pth",
            "size": 173475292,  # ~173MB
            "hash": "bc788c85e60baed816ffd6e2b2c6ae8a2b0afa57e335a14cc323cf1edf79abde"
        },
        ModelType.U2NETP: {
            "name": "U2Net-Lite",
            "description": "Lightweight version of U2Net (4.7MB)",
            "url": "https://github.com/xuebinqin/U-2-Net/releases/download/U2NetP/u2netp.pth",
            "size": 4710256,  # ~4.7MB
            "hash": "8cb63ecf8d9a4b62be6abf8e5c8a52d9ebeb7fcb9c64d4a561b5682f2a734af6"
        },
        ModelType.ISNET: {
            "name": "ISNet",
            "description": "ISNet for high-quality human segmentation",
            "url": "https://github.com/xuebinqin/DIS/releases/download/1.1/isnet.pth",
            "size": 176320856,  # ~176MB
            "hash": "a1ca63c02e6c4e371a0a3e6a75223ca2e1b1755caa095f6b334f17f6b4292969"
        },
        ModelType.MODNET: {
            "name": "MODNet",
            "description": "MODNet for real-time portrait matting",
            "url": "https://github.com/ZHKKKe/MODNet/releases/download/v1.0/modnet_photographic_portrait_matting.pth",
            "size": 24002228,  # ~24MB
            "hash": "815b64834ba6942c84c7b1c7ea36ebcbcb80b3e2c88b2d3eb25e7cc3fdb9453c"
        }
    }


class AIBackgroundRemover:
    """
    Background removal implementation using deep learning models.

    This class handles downloading, loading, and applying AI models for
    background removal tasks.
    """

    def __init__(
            self,
            file_manager: Any,
            config_manager: Any,
            logger: Any
    ):
        """
        Initialize the AI background remover.

        Args:
            file_manager: File manager instance
            config_manager: Configuration manager instance
            logger: Logger instance
        """
        self._file_manager = file_manager
        self._config_manager = config_manager
        self._logger = logger

        # Check if we're running in a CUDA environment
        self._has_cuda = torch.cuda.is_available()
        self._device = torch.device("cuda" if self._has_cuda else "cpu")

        # Model storage details
        self._models_dir: Optional[str] = None
        self._loaded_models: Dict[str, Any] = {}

        self._logger.info(f"AI Background Remover initialized with device: {self._device}")

    async def initialize(self) -> bool:
        """
        Initialize the background remover. Sets up model directory and checks
        for downloaded models.

        Returns:
            bool: True if initialization was successful
        """
        try:
            # Create models directory
            if self._config_manager and hasattr(self._config_manager, "_config_dir"):
                models_dir = os.path.join(self._config_manager._config_dir, "models")
            else:
                # Fallback to a default location
                models_dir = os.path.join("plugin_data", "media_processor", "models")

            # Ensure directory exists
            if hasattr(self._file_manager, "ensure_directory"):
                self._models_dir = await self._file_manager.ensure_directory(models_dir)
            else:
                os.makedirs(models_dir, exist_ok=True)
                self._models_dir = models_dir

            self._logger.info(f"AI models directory: {self._models_dir}")

            # Check for existing models
            downloaded_models = await self._get_downloaded_models()
            self._logger.info(f"Found {len(downloaded_models)} downloaded models")

            return True

        except Exception as e:
            self._logger.error(f"Error initializing AI background remover: {str(e)}")
            return False

    async def _get_downloaded_models(self) -> List[str]:
        """
        Get list of already downloaded models.

        Returns:
            List[str]: List of model identifiers
        """
        if not self._models_dir:
            return []

        downloaded = []
        try:
            for model_id, model_info in ModelDetails.MODELS.items():
                model_path = os.path.join(self._models_dir, f"{model_id}.pth")
                if await self._file_manager.file_exists(model_path):
                    # Verify file size as basic check
                    size = await self._file_manager.get_file_size(model_path)
                    if size > 0:  # Simple check, could compare with expected size
                        downloaded.append(model_id)

            return downloaded

        except Exception as e:
            self._logger.error(f"Error checking downloaded models: {str(e)}")
            return []

    async def is_model_downloaded(self, model_id: str) -> bool:
        """
        Check if a specific model is downloaded.

        Args:
            model_id: The model identifier

        Returns:
            bool: True if the model is downloaded
        """
        if not self._models_dir:
            return False

        model_path = os.path.join(self._models_dir, f"{model_id}.pth")
        return await self._file_manager.file_exists(model_path)

    async def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """
        Get information about a model.

        Args:
            model_id: The model identifier

        Returns:
            Dict[str, Any]: Model information
        """
        if model_id not in ModelDetails.MODELS:
            return {
                "name": "Unknown Model",
                "description": "Unknown model type",
                "downloaded": False,
                "size": 0
            }

        model_info = ModelDetails.MODELS[model_id].copy()
        model_info["downloaded"] = await self.is_model_downloaded(model_id)

        return model_info

    async def download_model(self, model_id: str,
                             progress_callback: Optional[Callable[[int, str], None]] = None) -> bool:
        """
        Download a model file.

        Args:
            model_id: The model identifier
            progress_callback: Optional callback for progress updates

        Returns:
            bool: True if download was successful
        """
        if not self._models_dir:
            raise BackgroundRemovalError("Models directory not initialized")

        if model_id not in ModelDetails.MODELS:
            raise BackgroundRemovalError(f"Unknown model: {model_id}")

        model_info = ModelDetails.MODELS[model_id]
        model_path = os.path.join(self._models_dir, f"{model_id}.pth")
        temp_path = os.path.join(self._models_dir, f"{model_id}.tmp")

        if progress_callback:
            await self._call_progress_on_main_thread(progress_callback, 0, "Starting download...")

        try:
            # Create download directory
            os.makedirs(os.path.dirname(model_path), exist_ok=True)

            # Callback for download progress
            def _download_progress(count, block_size, total_size):
                percent = int(count * block_size * 100 / total_size)
                if progress_callback:
                    message = f"Downloading {model_info['name']}... {percent}%"
                    asyncio.run_coroutine_threadsafe(
                        self._call_progress_on_main_thread(progress_callback, percent, message),
                        asyncio.get_event_loop()
                    )

            # Download the file
            urllib.request.urlretrieve(
                model_info["url"],
                temp_path,
                _download_progress
            )

            # Verify download with hash
            if progress_callback:
                await self._call_progress_on_main_thread(
                    progress_callback, 95, "Verifying download..."
                )

            file_hash = self._compute_sha256(temp_path)
            if file_hash != model_info["hash"]:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise BackgroundRemovalError(
                    f"Downloaded file checksum mismatch: {file_hash} != {model_info['hash']}"
                )

            # Move to final location
            if os.path.exists(model_path):
                os.remove(model_path)
            os.rename(temp_path, model_path)

            if progress_callback:
                await self._call_progress_on_main_thread(
                    progress_callback, 100, "Download complete"
                )

            self._logger.info(f"Successfully downloaded model: {model_id}")
            return True

        except Exception as e:
            self._logger.error(f"Error downloading model {model_id}: {str(e)}")
            if os.path.exists(temp_path):
                os.remove(temp_path)

            if progress_callback:
                await self._call_progress_on_main_thread(
                    progress_callback, 0, f"Error: {str(e)}"
                )

            raise BackgroundRemovalError(f"Model download failed: {str(e)}")

    async def _call_progress_on_main_thread(
            self,
            callback: Callable[[int, str], None],
            percent: int,
            message: str
    ) -> None:
        """
        Call progress callback on the main thread.

        Args:
            callback: The progress callback
            percent: Percentage complete
            message: Progress message
        """
        if hasattr(self, "_concurrency_manager"):
            await self._concurrency_manager.run_on_main_thread(
                lambda: callback(percent, message)
            )
        else:
            callback(percent, message)

    def _compute_sha256(self, file_path: str) -> str:
        """
        Compute SHA-256 hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            str: Hexadecimal hash
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256.update(byte_block)
        return sha256.hexdigest()

    async def remove_background(
            self,
            image: Image.Image,
            config: BackgroundRemovalConfig
    ) -> Image.Image:
        """
        Remove background from an image using AI models.

        Args:
            image: Input image
            config: Background removal configuration

        Returns:
            Image.Image: Image with background removed
        """
        if config.model_name not in ModelDetails.MODELS:
            raise BackgroundRemovalError(
                f"Unknown model: {config.model_name}, supported models: {list(ModelDetails.MODELS.keys())}"
            )

        # Check if model is downloaded
        if not await self.is_model_downloaded(config.model_name):
            raise BackgroundRemovalError(
                f"Model {config.model_name} is not downloaded. Please download it first."
            )

        try:
            # Load the model
            model = await self._load_model(config.model_name)

            # Process image
            if config.model_name in [ModelType.U2NET, ModelType.U2NETP]:
                return await self._process_with_u2net(image, model, config)
            elif config.model_name == ModelType.ISNET:
                return await self._process_with_isnet(image, model, config)
            elif config.model_name == ModelType.MODNET:
                return await self._process_with_modnet(image, model, config)
            else:
                raise BackgroundRemovalError(f"Unsupported model type: {config.model_name}")

        except Exception as e:
            self._logger.error(f"Error in AI background removal: {str(e)}")
            raise BackgroundRemovalError(f"AI background removal failed: {str(e)}")

    async def _load_model(self, model_id: str) -> Any:
        """
        Load a model from disk if not already loaded.

        Args:
            model_id: The model identifier

        Returns:
            Any: The loaded model
        """
        # Check if already loaded
        if model_id in self._loaded_models:
            return self._loaded_models[model_id]

        if not self._models_dir:
            raise BackgroundRemovalError("Models directory not initialized")

        model_path = os.path.join(self._models_dir, f"{model_id}.pth")

        try:
            if model_id in [ModelType.U2NET, ModelType.U2NETP]:
                from ..models.u2net_model import U2NET, U2NETP

                # Create the appropriate model architecture
                if model_id == ModelType.U2NET:
                    model = U2NET()
                else:  # U2NETP
                    model = U2NETP()

                # Load the weights
                model.load_state_dict(torch.load(model_path, map_location=self._device))
                model.to(self._device)
                model.eval()

            elif model_id == ModelType.ISNET:
                from ..models.isnet_model import ISNetDIS

                model = ISNetDIS()
                model.load_state_dict(torch.load(model_path, map_location=self._device))
                model.to(self._device)
                model.eval()

            elif model_id == ModelType.MODNET:
                from ..models.modnet_model import MODNet

                model = MODNet()
                model.load_state_dict(torch.load(model_path, map_location=self._device))
                model.to(self._device)
                model.eval()

            else:
                raise BackgroundRemovalError(f"Unsupported model type: {model_id}")

            # Cache the loaded model
            self._loaded_models[model_id] = model

            self._logger.info(f"Successfully loaded model: {model_id}")
            return model

        except Exception as e:
            self._logger.error(f"Error loading model {model_id}: {str(e)}")
            raise BackgroundRemovalError(f"Failed to load model: {str(e)}")

    async def _process_with_u2net(
            self,
            image: Image.Image,
            model: Any,
            config: BackgroundRemovalConfig
    ) -> Image.Image:
        """
        Process image with U2Net model.

        Args:
            image: Input image
            model: Loaded model
            config: Background removal configuration

        Returns:
            Image.Image: Processed image
        """
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Preprocess
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        input_tensor = transform(image).unsqueeze(0).to(self._device)

        # Process
        with torch.no_grad():
            output = model(input_tensor)
            if isinstance(output, tuple):
                output = output[0]  # U2Net returns multiple outputs, use the first one

            # Normalize output
            output = torch.sigmoid(output)
            output = output.data.cpu().numpy().squeeze()

            # Apply threshold
            if config.confidence_threshold > 0:
                output = (output > config.confidence_threshold).astype(np.float32)

            # Resize to original size
            output = Image.fromarray((output * 255).astype(np.uint8))
            output = output.resize(image.size, Image.LANCZOS)

        # Apply edge refinement if needed
        if config.refine_edge:
            output = output.filter(ImageFilter.UnsharpMask(radius=1.0, percent=150, threshold=3))

        # Create RGBA output
        result = image.copy().convert("RGBA")
        r, g, b, a = result.split()
        result.putalpha(output)

        return result

    async def _process_with_isnet(
            self,
            image: Image.Image,
            model: Any,
            config: BackgroundRemovalConfig
    ) -> Image.Image:
        """
        Process image with ISNet model.

        Args:
            image: Input image
            model: Loaded model
            config: Background removal configuration

        Returns:
            Image.Image: Processed image
        """
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Get optimal size (multiple of 32)
        h, w = image.height, image.width
        new_h = ((h + 31) // 32) * 32
        new_w = ((w + 31) // 32) * 32

        # Resize for processing
        image_resized = image.resize((new_w, new_h), Image.LANCZOS)

        # Preprocess
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        input_tensor = transform(image_resized).unsqueeze(0).to(self._device)

        # Process
        with torch.no_grad():
            output = model(input_tensor)

            # Normalize output
            output = torch.sigmoid(output[0][0])
            output = output.data.cpu().numpy().squeeze()

            # Apply threshold
            if config.confidence_threshold > 0:
                output = (output > config.confidence_threshold).astype(np.float32)

            # Resize to original size
            output = Image.fromarray((output * 255).astype(np.uint8))
            output = output.resize((w, h), Image.LANCZOS)

        # Apply edge refinement if needed
        if config.refine_edge:
            output = output.filter(ImageFilter.UnsharpMask(radius=1.0, percent=150, threshold=3))

        # Create RGBA output
        result = image.copy().convert("RGBA")
        r, g, b, a = result.split()
        result.putalpha(output)

        return result

    async def _process_with_modnet(
            self,
            image: Image.Image,
            model: Any,
            config: BackgroundRemovalConfig
    ) -> Image.Image:
        """
        Process image with MODNet model.

        Args:
            image: Input image
            model: Loaded model
            config: Background removal configuration

        Returns:
            Image.Image: Processed image
        """
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Preprocess
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])

        input_tensor = transform(image).unsqueeze(0).to(self._device)

        # Process
        with torch.no_grad():
            _, _, matte = model(input_tensor, True)

            # Get alpha matte
            matte = matte.data.cpu().numpy().squeeze()

            # Apply threshold
            if config.confidence_threshold > 0:
                matte = np.where(matte > config.confidence_threshold, matte, 0)

            # Resize to original size
            matte = Image.fromarray((matte * 255).astype(np.uint8))
            matte = matte.resize(image.size, Image.LANCZOS)

        # Apply edge refinement if needed
        if config.refine_edge:
            matte = matte.filter(ImageFilter.UnsharpMask(radius=1.0, percent=150, threshold=3))

        # Create RGBA output
        result = image.copy().convert("RGBA")
        r, g, b, a = result.split()
        result.putalpha(matte)

        return result