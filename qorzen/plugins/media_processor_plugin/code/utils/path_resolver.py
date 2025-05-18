from __future__ import annotations

"""
Path resolution utilities for media processing.

This module contains functions for resolving output paths, generating 
filenames, and other path-related operations.
"""

import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union, Any

from .exceptions import MediaProcessingError


def generate_filename(
        template: str,
        base_name: str,
        extension: str,
        prefix: Optional[str] = None,
        suffix: Optional[str] = None
) -> str:
    """
    Generate a filename based on a template.

    Args:
        template: Filename template with placeholders
        base_name: Base filename without extension
        extension: File extension (without dot)
        prefix: Optional prefix to add
        suffix: Optional suffix to add

    Returns:
        Generated filename

    Supported template placeholders:
        {name} - Original filename without extension
        {ext} - File extension
        {date} - Current date in YYYY-MM-DD format
        {time} - Current time in HH-MM-SS format
        {timestamp} - Unix timestamp
        {random} - Random 8-character string
        {counter} - Will be replaced with a counter if file exists

    Example:
        "{name}_{date}.{ext}" -> "image_2023-05-17.png"
    """
    # Remove any extension from base_name
    base_name = os.path.splitext(base_name)[0]

    # Add prefix/suffix if provided
    if prefix:
        base_name = f"{prefix}{base_name}"
    if suffix:
        base_name = f"{base_name}{suffix}"

    # Prepare replacements
    now = datetime.now()
    replacements = {
        "{name}": base_name,
        "{ext}": extension,
        "{date}": now.strftime("%Y-%m-%d"),
        "{time}": now.strftime("%H-%M-%S"),
        "{timestamp}": str(int(time.time())),
        "{random}": os.urandom(4).hex(),
        # {counter} is handled separately later
    }

    # Apply replacements
    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)

    # If no extension in result, add it
    if not result.endswith(f".{extension}"):
        result = f"{result}.{extension}"

    return result


def generate_batch_folder_name(template: str) -> str:
    """
    Generate a folder name for batch processing.

    Args:
        template: Folder name template with placeholders

    Returns:
        Generated folder name

    Supported template placeholders:
        {date} - Current date in YYYY-MM-DD format
        {time} - Current time in HH-MM-SS format
        {timestamp} - Unix timestamp
        {random} - Random 8-character string
    """
    # Prepare replacements
    now = datetime.now()
    replacements = {
        "{date}": now.strftime("%Y-%m-%d"),
        "{time}": now.strftime("%H-%M-%S"),
        "{timestamp}": str(int(time.time())),
        "{random}": os.urandom(4).hex(),
    }

    # Apply replacements
    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)

    return result


def resolve_output_path(
        input_path: str,
        output_dir: str,
        format_config: Any,
        file_exists_handler: Optional[callable] = None
) -> str:
    """
    Resolve the output path for a processed file.

    Args:
        input_path: Path to the input file
        output_dir: Base output directory
        format_config: Output format configuration
        file_exists_handler: Optional callback for handling existing files

    Returns:
        Resolved output path
    """
    # Get the input filename
    input_filename = os.path.basename(input_path)
    input_name, input_ext = os.path.splitext(input_filename)
    input_name = input_name.strip()

    # Determine output extension
    output_ext = format_config.format.value

    # Determine output subdirectory
    if format_config.subdir:
        actual_output_dir = os.path.join(output_dir, format_config.subdir)
    else:
        actual_output_dir = output_dir

    # Ensure output directory exists
    os.makedirs(actual_output_dir, exist_ok=True)

    # Generate output filename
    if format_config.naming_template:
        # Use template
        output_filename = generate_filename(
            format_config.naming_template,
            input_name,
            output_ext,
            format_config.prefix,
            format_config.suffix
        )
    else:
        # Use simple naming
        prefix = format_config.prefix or ""
        suffix = format_config.suffix or ""
        output_filename = f"{prefix}{input_name}{suffix}.{output_ext}"

    # Build initial output path
    output_path = os.path.join(actual_output_dir, output_filename)

    # Check if output file already exists
    if os.path.exists(output_path):
        if file_exists_handler:
            # Use handler to resolve conflict
            output_path = file_exists_handler(output_path)
        else:
            # Default behavior: add counter to filename
            counter = 1
            name_part, ext_part = os.path.splitext(output_filename)

            # Check if we already have a counter pattern
            counter_match = re.search(r"_(\d+)$", name_part)
            if counter_match:
                # Extract the counter value and increment
                counter = int(counter_match.group(1)) + 1
                name_part = re.sub(r"_\d+$", f"_{counter}", name_part)
                new_path = os.path.join(actual_output_dir, f"{name_part}{ext_part}")
            else:
                # Add a new counter
                new_path = os.path.join(actual_output_dir, f"{name_part}_{counter}{ext_part}")

            # Check if the new path exists, and increment counter until we find a free one
            while os.path.exists(new_path):
                counter += 1
                if counter_match:
                    name_part = re.sub(r"_\d+$", f"_{counter}", name_part)
                else:
                    name_part = f"{name_part.rstrip('_')}_{counter}"
                new_path = os.path.join(actual_output_dir, f"{name_part}{ext_part}")

            output_path = new_path

    return output_path


def get_unique_output_path(base_path: str) -> str:
    """
    Ensure a path is unique by adding a counter if needed.

    Args:
        base_path: The base file path

    Returns:
        A unique file path
    """
    if not os.path.exists(base_path):
        return base_path

    directory, filename = os.path.split(base_path)
    name, ext = os.path.splitext(filename)

    # Check if filename already ends with _N pattern
    counter_match = re.search(r"_(\d+)$", name)
    if counter_match:
        # Extract the counter value and increment
        counter = int(counter_match.group(1)) + 1
        name = re.sub(r"_\d+$", f"_{counter}", name)
        new_path = os.path.join(directory, f"{name}{ext}")
    else:
        # Add a new counter
        counter = 1
        new_path = os.path.join(directory, f"{name}_{counter}{ext}")

    # Keep incrementing until we find a free path
    while os.path.exists(new_path):
        counter += 1
        if counter_match:
            name = re.sub(r"_\d+$", f"_{counter}", name)
        else:
            name = f"{name.rstrip('_')}_{counter}"
        new_path = os.path.join(directory, f"{name}{ext}")

    return new_path