#!/usr/bin/env python3
"""
Script to aggressively minify frontend code for AI assistant sharing.
Supports Vue, TypeScript, JavaScript, CSS, SCSS, HTML, and JSON files.
"""
from __future__ import annotations

import os
import re
import json
import argparse
from pathlib import Path
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Callable, Protocol, Set


class FileType(Enum):
    """Enumeration of supported file types."""

    VUE = auto()
    TYPESCRIPT = auto()
    JAVASCRIPT = auto()
    CSS = auto()
    SCSS = auto()
    HTML = auto()
    JSON = auto()
    UNKNOWN = auto()


@dataclass
class ProcessingResult:
    """Result of processing a file."""

    original_size: int
    stripped_size: int
    success: bool
    error_message: Optional[str] = None


class MinifierProtocol(Protocol):
    """Protocol for file minifiers."""

    def minify(self, content: str) -> str:
        """Minify content by removing comments, whitespace, etc."""
        ...


class JavaScriptMinifier:
    """Aggressive minifier for JavaScript and TypeScript files."""

    def minify(self, content: str) -> str:
        """Aggressively minify JS/TS content."""
        # Remove single line comments
        content = re.sub(r"//.*?$", "", content, flags=re.MULTILINE)

        # Remove multi-line comments
        content = re.sub(r"/\*[\s\S]*?\*/", "", content)

        # Handle string literals to avoid modifying their contents
        def replace_strings(match: re.Match) -> str:
            """Preserve string literals during minification."""
            return match.group(0)

        # Replace strings temporarily with placeholders
        strings = []

        def collect_strings(match: re.Match) -> str:
            strings.append(match.group(0))
            return f"__STRING_{len(strings) - 1}__"

        # Collect double-quoted strings
        pattern_dq = r'"(?:\\.|[^"\\])*"'
        content = re.sub(pattern_dq, collect_strings, content)

        # Collect single-quoted strings
        pattern_sq = r"'(?:\\.|[^'\\])*'"
        content = re.sub(pattern_sq, collect_strings, content)

        # Collect template literals (backtick strings)
        pattern_tl = r"`(?:\\.|[^`\\])*`"
        content = re.sub(pattern_tl, collect_strings, content)

        # Collapse whitespace (excluding newlines for now)
        content = re.sub(r"[ \t\f\v]+", " ", content)

        # Remove spaces around operators and punctuation
        content = re.sub(r"\s*([=+\-*/%&|^<>!?:;,{}()\[\]])\s*", r"\1", content)

        # Fix double operators that need spaces
        content = re.sub(
            r"([<>!=])=", r"\1=", content
        )  # Ensure operators like <= >= == etc. are preserved

        # Remove unnecessary spaces
        content = re.sub(r"\s+", " ", content)
        content = re.sub(r"^\s+|\s+$", "", content)

        # Remove newlines
        content = re.sub(r"\n", "", content)

        # Restore string literals
        for i, string in enumerate(strings):
            content = content.replace(f"__STRING_{i}__", string)

        return content


class CSSMinifier:
    """Aggressive minifier for CSS and SCSS files."""

    def minify(self, content: str) -> str:
        """Aggressively minify CSS/SCSS content."""
        # Remove CSS comments
        content = re.sub(r"/\*[\s\S]*?\*/", "", content)

        # For SCSS, remove single line comments
        content = re.sub(r"//.*?$", "", content, flags=re.MULTILINE)

        # Preserve content inside strings
        strings = []

        def collect_strings(match: re.Match) -> str:
            strings.append(match.group(0))
            return f"__STRING_{len(strings) - 1}__"

        # Collect double-quoted strings
        pattern_dq = r'"(?:\\.|[^"\\])*"'
        content = re.sub(pattern_dq, collect_strings, content)

        # Collect single-quoted strings
        pattern_sq = r"'(?:\\.|[^'\\])*'"
        content = re.sub(pattern_sq, collect_strings, content)

        # Remove whitespace around selectors, braces, properties, and values
        content = re.sub(r"\s*{\s*", "{", content)
        content = re.sub(r"\s*}\s*", "}", content)
        content = re.sub(r"\s*:\s*", ":", content)
        content = re.sub(r"\s*;\s*", ";", content)
        content = re.sub(r"\s*,\s*", ",", content)
        content = re.sub(r"\s+", " ", content)

        # Remove last semicolons in rule sets
        content = re.sub(r";}", "}", content)

        # Restore string literals
        for i, string in enumerate(strings):
            content = content.replace(f"__STRING_{i}__", string)

        # Remove all newlines and excess spaces
        content = re.sub(r"\s*\n\s*", "", content)
        content = re.sub(r"^\s+|\s+$", "", content)

        return content


class HTMLMinifier:
    """Aggressive minifier for HTML files."""

    def minify(self, content: str) -> str:
        """Aggressively minify HTML content."""
        # Remove HTML comments
        content = re.sub(r"<!--[\s\S]*?-->", "", content)

        # Preserve script and style tags for separate processing
        scripts = []
        styles = []

        def collect_scripts(match: re.Match) -> str:
            scripts.append(match.group(1))
            return f"<script>__SCRIPT_{len(scripts) - 1}__</script>"

        def collect_styles(match: re.Match) -> str:
            styles.append(match.group(1))
            return f"<style>__STYLE_{len(styles) - 1}__</style>"

        # Extract scripts
        content = re.sub(r"<script[^>]*>([\s\S]*?)</script>", collect_scripts, content)

        # Extract styles
        content = re.sub(r"<style[^>]*>([\s\S]*?)</style>", collect_styles, content)

        # Remove whitespace between tags
        content = re.sub(r">\s+<", "><", content)

        # Remove whitespace around attributes
        content = re.sub(r"\s*=\s*", "=", content)

        # Collapse whitespace in text nodes (preserving at least one space)
        content = re.sub(r">[ \t\r\n]+", "> ", content)
        content = re.sub(r"[ \t\r\n]+<", " <", content)

        # Remove unnecessary spaces
        content = re.sub(r"[ \t\r\n]+", " ", content)
        content = re.sub(r"^\s+|\s+$", "", content)

        # Process scripts with JS minifier
        js_minifier = JavaScriptMinifier()
        for i, script in enumerate(scripts):
            minified_script = js_minifier.minify(script)
            content = content.replace(f"__SCRIPT_{i}__", minified_script)

        # Process styles with CSS minifier
        css_minifier = CSSMinifier()
        for i, style in enumerate(styles):
            minified_style = css_minifier.minify(style)
            content = content.replace(f"__STYLE_{i}__", minified_style)

        return content


class JSONMinifier:
    """Minifier for JSON files."""

    def minify(self, content: str) -> str:
        """Minify JSON content to a single line."""
        try:
            # Parse and re-serialize to minify
            parsed = json.loads(content)
            return json.dumps(parsed, separators=(",", ":"))
        except json.JSONDecodeError:
            # If invalid JSON, just return the original content
            return content


class VueMinifier:
    """Minifier for Vue files that handles template, script, and style sections."""

    def __init__(self) -> None:
        """Initialize with appropriate minifiers for each section."""
        self.html_minifier = HTMLMinifier()
        self.js_minifier = JavaScriptMinifier()
        self.css_minifier = CSSMinifier()

    def minify(self, content: str) -> str:
        """Minify Vue file by processing each section separately."""
        # Extract the template, script, and style sections
        template_match = re.search(r"<template>([\s\S]*?)</template>", content)
        script_match = re.search(r"<script[^>]*>([\s\S]*?)</script>", content)
        style_match = re.search(r"<style[^>]*>([\s\S]*?)</style>", content)

        # Process each section if found
        result = content

        if template_match:
            template_content = template_match.group(1)
            minified_template = self.html_minifier.minify(template_content)
            result = result.replace(template_content, minified_template)

        if script_match:
            script_content = script_match.group(1)
            minified_script = self.js_minifier.minify(script_content)
            result = result.replace(script_content, minified_script)

        if style_match:
            style_content = style_match.group(1)
            minified_style = self.css_minifier.minify(style_content)
            result = result.replace(style_content, minified_style)

        # Minify spacing between sections
        result = re.sub(r">\s+<", "><", result)
        result = re.sub(r"\s+", " ", result)
        result = result.strip()

        return result


def get_file_type(file_path: str) -> FileType:
    """
    Determine the file type based on extension.

    Args:
        file_path: Path to the file

    Returns:
        FileType enum indicating the detected file type
    """
    extension = Path(file_path).suffix.lower()

    extension_map: Dict[str, FileType] = {
        ".vue": FileType.VUE,
        ".ts": FileType.TYPESCRIPT,
        ".tsx": FileType.TYPESCRIPT,
        ".js": FileType.JAVASCRIPT,
        ".jsx": FileType.JAVASCRIPT,
        ".css": FileType.CSS,
        ".scss": FileType.SCSS,
        ".sass": FileType.SCSS,
        ".less": FileType.CSS,
        ".html": FileType.HTML,
        ".htm": FileType.HTML,
        ".json": FileType.JSON,
    }

    return extension_map.get(extension, FileType.UNKNOWN)


def get_minifier_for_file_type(file_type: FileType) -> Optional[MinifierProtocol]:
    """
    Get the appropriate minifier for a file type.

    Args:
        file_type: The FileType enum

    Returns:
        An instance of a minifier class or None if unsupported
    """
    minifier_map: Dict[FileType, MinifierProtocol] = {
        FileType.VUE: VueMinifier(),
        FileType.TYPESCRIPT: JavaScriptMinifier(),
        FileType.JAVASCRIPT: JavaScriptMinifier(),
        FileType.CSS: CSSMinifier(),
        FileType.SCSS: CSSMinifier(),
        FileType.HTML: HTMLMinifier(),
        FileType.JSON: JSONMinifier(),
    }

    return minifier_map.get(file_type)


def minify_file(file_path: str, output_path: Optional[str] = None) -> ProcessingResult:
    """
    Process a single file, aggressively minifying the content.

    Args:
        file_path: Path to the original file
        output_path: Where to save the minified file

    Returns:
        ProcessingResult with original and minified sizes
    """
    # Default output path if none provided
    if output_path is None:
        file_stem = Path(file_path).stem
        file_suffix = Path(file_path).suffix
        output_path = str(
            Path(file_path).with_name(f"{file_stem}_minified{file_suffix}")
        )

    try:
        # Read the file
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()

        file_type = get_file_type(file_path)
        minifier = get_minifier_for_file_type(file_type)

        if not minifier:
            # File type not supported, just copy the file
            minified_source = source
        else:
            # Minify the content
            minified_source = minifier.minify(source)

        # Write the minified code to the output file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(minified_source)

        return ProcessingResult(
            original_size=len(source), stripped_size=len(minified_source), success=True
        )
    except Exception as e:
        return ProcessingResult(
            original_size=0, stripped_size=0, success=False, error_message=str(e)
        )


def process_directory(
    input_dir: str,
    output_dir: str,
    extensions: Optional[List[str]] = None,
    exclude_dirs: Optional[Set[str]] = None,
) -> Tuple[int, int, int, int]:
    """
    Process all files in a directory, minifying them.

    Args:
        input_dir: Directory containing original files
        output_dir: Directory where minified files will be saved
        extensions: List of file extensions to process
        exclude_dirs: Set of directory names to exclude

    Returns:
        Tuple of (processed_files, total_original_size, total_minified_size, error_files)
    """
    # Default extensions if none specified
    if extensions is None:
        extensions = [
            ".vue",
            ".ts",
            ".js",
            ".css",
            ".scss",
            ".html",
            ".json",
            ".tsx",
            ".jsx",
        ]

    # Default exclude dirs
    if exclude_dirs is None:
        exclude_dirs = {
            "node_modules",
            "dist",
            ".git",
            ".github",
            ".vscode",
            ".idea",
            "coverage",
            "build",
        }

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    total_original_size = 0
    total_minified_size = 0
    processed_files = 0
    error_files = 0

    # Walk through the directory tree
    for root, dirs, files in os.walk(input_dir):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        # Create corresponding directory in output_dir
        rel_path = os.path.relpath(root, input_dir)
        if rel_path == ".":
            current_output_dir = output_dir
        else:
            current_output_dir = os.path.join(output_dir, rel_path)
        os.makedirs(current_output_dir, exist_ok=True)

        # Process each file
        for file in files:
            file_ext = os.path.splitext(file)[1]
            if file_ext in extensions:
                input_file = os.path.join(root, file)
                output_file = os.path.join(current_output_dir, file)

                result = minify_file(input_file, output_file)

                if result.success:
                    processed_files += 1
                    total_original_size += result.original_size
                    total_minified_size += result.stripped_size

                    if result.original_size > 0:
                        reduction = (
                            1 - result.stripped_size / result.original_size
                        ) * 100
                        print(f"Processed {input_file} -> {output_file}")
                        print(
                            f"  Size reduced: {result.original_size} -> {result.stripped_size} bytes ({reduction:.1f}% reduction)"
                        )
                else:
                    error_files += 1
                    print(f"Error processing {input_file}: {result.error_message}")

    return processed_files, total_original_size, total_minified_size, error_files


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Aggressively minify frontend code files for AI assistant sharing"
    )
    parser.add_argument("input", help="Input file or directory")
    parser.add_argument(
        "--output", help="Output file or directory (defaults to inputname_minified)"
    )
    parser.add_argument(
        "--extensions",
        default=".vue,.ts,.js,.css,.scss,.html,.json,.tsx,.jsx",
        help="Comma-separated list of file extensions to process",
    )
    parser.add_argument(
        "--exclude-dirs",
        default="node_modules,dist,.git,.github,.vscode,.idea,coverage,build",
        help="Comma-separated list of directories to exclude",
    )

    args = parser.parse_args()

    input_path = args.input
    output_path = args.output
    extensions = args.extensions.split(",")
    exclude_dirs = set(args.exclude_dirs.split(","))

    if os.path.isfile(input_path):
        # Process a single file
        if output_path is None:
            file_stem = Path(input_path).stem
            file_suffix = Path(input_path).suffix
            output_path = str(
                Path(input_path).with_name(f"{file_stem}_minified{file_suffix}")
            )

        result = minify_file(input_path, output_path)
        if result.success:
            if result.original_size > 0:
                reduction = (1 - result.stripped_size / result.original_size) * 100
                print(
                    f"Size reduced: {result.original_size} -> {result.stripped_size} bytes ({reduction:.1f}% reduction)"
                )
        else:
            print(f"Error processing {input_path}: {result.error_message}")
    elif os.path.isdir(input_path):
        # Process a directory
        if output_path is None:
            output_path = input_path + "_minified"

        processed_files, total_original_size, total_minified_size, error_files = (
            process_directory(input_path, output_path, extensions, exclude_dirs)
        )

        # Print summary
        if processed_files > 0:
            overall_reduction = (1 - total_minified_size / total_original_size) * 100
            print("\nSummary:")
            print(f"  Processed {processed_files} files successfully")
            if error_files > 0:
                print(f"  Failed to process {error_files} files")
            print(
                f"  Total size reduced: {total_original_size} -> {total_minified_size} bytes"
            )
            print(f"  Overall reduction: {overall_reduction:.1f}%")
    else:
        print(f"Input path {input_path} does not exist")


if __name__ == "__main__":
    main()
