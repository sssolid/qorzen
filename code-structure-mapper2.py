#!/usr/bin/env python3
"""
Code Structure Mapper - Generate comprehensive code structure representations for AI consumption.

This tool analyzes Python projects and generates detailed structural representations that
include directory structure, modules, classes, methods, functions, and their signatures.
The output can be in various formats suitable for AI analysis, including a directory-based
structure that mirrors the original project for selective sharing.
"""
from __future__ import annotations

import os
import ast
import sys
import json
import argparse
import importlib
import inspect
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable, Literal
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
from datetime import datetime
import re


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("code_structure_mapper")


class OutputFormat(Enum):
    """Supported output formats for the code structure representation."""

    JSON = auto()
    MARKDOWN = auto()
    MERMAID = auto()
    TEXT = auto()
    DIRECTORY = auto()  # New format for directory-based output


@dataclass
class FunctionInfo:
    """Information about a function or method."""

    name: str
    args: List[str] = field(default_factory=list)
    returns: Optional[str] = None
    docstring: Optional[str] = None
    is_async: bool = False
    is_property: bool = False
    decorators: List[str] = field(default_factory=list)
    line_number: int = 0
    source_code: Optional[str] = None
    return_annotation: Optional[str] = None
    arg_annotations: Dict[str, str] = field(default_factory=dict)


@dataclass
class ClassInfo:
    """Information about a class."""

    name: str
    bases: List[str] = field(default_factory=list)
    methods: Dict[str, FunctionInfo] = field(default_factory=dict)
    class_attributes: Dict[str, str] = field(default_factory=dict)
    docstring: Optional[str] = None
    line_number: int = 0
    decorators: List[str] = field(default_factory=list)


@dataclass
class ModuleInfo:
    """Information about a Python module."""

    name: str
    path: Path
    classes: Dict[str, ClassInfo] = field(default_factory=dict)
    functions: Dict[str, FunctionInfo] = field(default_factory=dict)
    imports: List[str] = field(default_factory=list)
    global_variables: Dict[str, str] = field(default_factory=dict)
    docstring: Optional[str] = None


@dataclass
class PackageInfo:
    """Information about a Python package."""

    name: str
    path: Path
    modules: Dict[str, ModuleInfo] = field(default_factory=dict)
    subpackages: Dict[str, "PackageInfo"] = field(default_factory=dict)
    init_module: Optional[ModuleInfo] = None


@dataclass
class ProjectInfo:
    """Information about the entire Python project."""

    name: str
    root_path: Path
    packages: Dict[str, PackageInfo] = field(default_factory=dict)
    modules: Dict[str, ModuleInfo] = field(default_factory=dict)  # Top-level modules
    non_python_files: Dict[str, List[str]] = field(default_factory=dict)


class CustomVisitor(ast.NodeVisitor):
    """AST visitor to extract detailed information from Python files."""

    def __init__(self) -> None:
        self.classes: Dict[str, ClassInfo] = {}
        self.functions: Dict[str, FunctionInfo] = {}
        self.global_vars: Dict[str, str] = {}
        self.imports: List[str] = []
        self.current_class: Optional[str] = None
        self.docstring: Optional[str] = None
        self.source_lines: List[str] = []

    def set_source(self, source: str) -> None:
        """Set the source code for reference."""
        self.source_lines = source.splitlines()

    def get_source_segment(self, node: ast.AST) -> Optional[str]:
        """Extract source code for a node."""
        if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
            return None

        start = node.lineno - 1  # Convert to 0-based indexing
        end = getattr(node, "end_lineno", start + 1) - 1

        if (
            start < 0
            or start >= len(self.source_lines)
            or end >= len(self.source_lines)
        ):
            return None

        # Extract the lines
        lines = self.source_lines[start : end + 1]
        return "\n".join(lines)

    def visit_Module(self, node: ast.Module) -> None:
        """Extract module-level docstring."""
        # Extract module docstring if present
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
        ):
            self.docstring = node.body[0].value.value
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Extract class information."""
        # Extract base classes
        bases = [self._get_name_from_node(base) for base in node.bases]

        # Extract class docstring
        docstring = None
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
        ):
            docstring = node.body[0].value.value

        # Extract decorators
        decorators = [self._get_name_from_node(d) for d in node.decorator_list]

        # Create class info
        class_info = ClassInfo(
            name=node.name,
            bases=bases,
            docstring=docstring,
            line_number=node.lineno,
            decorators=decorators,
        )

        self.classes[node.name] = class_info

        # Process class body
        old_class = self.current_class
        self.current_class = node.name

        # We need to do a first pass to identify properties
        property_methods = set()
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if any(
                    d.id == "property"
                    for d in item.decorator_list
                    if isinstance(d, ast.Name)
                ):
                    property_methods.add(item.name)

        # Now process all class items
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        # Add class attributes
                        if isinstance(item.value, ast.Constant):
                            value = repr(item.value.value)
                        else:
                            value = self.get_source_segment(item.value) or "..."
                        class_info.class_attributes[target.id] = value
            else:
                self.visit(item)

        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Extract function or method information."""
        self._process_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Extract async function or method information."""
        self._process_function(node, is_async=True)

    def _process_function(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], is_async: bool
    ) -> None:
        """Process a function definition node."""
        # Extract function arguments
        args = []
        arg_annotations = {}

        # Process positional args
        for arg in node.args.args:
            args.append(arg.arg)
            if arg.annotation:
                arg_annotations[arg.arg] = self._get_name_from_node(arg.annotation)

        # Process keyword args with defaults
        for i, arg in enumerate(node.args.kwonlyargs):
            default_index = i - (len(node.args.args) - len(node.args.defaults))
            if default_index >= 0 and default_index < len(node.args.defaults):
                args.append(
                    f"{arg.arg}={self._get_name_from_node(node.args.defaults[default_index])}"
                )
            else:
                args.append(arg.arg)

            if arg.annotation:
                arg_annotations[arg.arg] = self._get_name_from_node(arg.annotation)

        # Process varargs and kwargs
        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")
            if node.args.vararg.annotation:
                arg_annotations[node.args.vararg.arg] = self._get_name_from_node(
                    node.args.vararg.annotation
                )

        if node.args.kwarg:
            args.append(f"**{node.args.kwarg.arg}")
            if node.args.kwarg.annotation:
                arg_annotations[node.args.kwarg.arg] = self._get_name_from_node(
                    node.args.kwarg.annotation
                )

        # Extract return annotation
        return_annotation = None
        if node.returns:
            return_annotation = self._get_name_from_node(node.returns)

        # Extract docstring
        docstring = None
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
        ):
            docstring = node.body[0].value.value

        # Extract decorators
        decorators = [self._get_name_from_node(d) for d in node.decorator_list]

        # Determine if this is a property
        is_property = any(
            d.id == "property" if isinstance(d, ast.Name) else False
            for d in node.decorator_list
        )

        # Create function info
        func_info = FunctionInfo(
            name=node.name,
            args=args,
            returns=return_annotation,
            docstring=docstring,
            is_async=is_async,
            is_property=is_property,
            decorators=decorators,
            line_number=node.lineno,
            source_code=self.get_source_segment(node),
            return_annotation=return_annotation,
            arg_annotations=arg_annotations,
        )

        # Add to appropriate container
        if self.current_class:
            self.classes[self.current_class].methods[node.name] = func_info
        else:
            self.functions[node.name] = func_info

    def visit_Assign(self, node: ast.Assign) -> None:
        """Extract global variable assignments."""
        if self.current_class is None:  # Only process module-level assignments
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if isinstance(node.value, ast.Constant):
                        self.global_vars[target.id] = repr(node.value.value)
                    else:
                        self.global_vars[target.id] = (
                            self.get_source_segment(node.value) or "..."
                        )
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Extract import statements."""
        for name in node.names:
            if name.asname:
                self.imports.append(f"import {name.name} as {name.asname}")
            else:
                self.imports.append(f"import {name.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Extract from import statements."""
        if node.module:
            names = ", ".join(
                name.name + (f" as {name.asname}" if name.asname else "")
                for name in node.names
            )
            self.imports.append(f"from {node.module} import {names}")
        self.generic_visit(node)

    def _get_name_from_node(self, node: ast.AST) -> str:
        """Extract a name representation from an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name_from_node(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Subscript):
            return f"{self._get_name_from_node(node.value)}[{self._get_name_from_node(node.slice)}]"
        elif isinstance(node, ast.BinOp):
            # Handle simple binary operations like module.attr + other.attr
            return f"{self._get_name_from_node(node.left)} {type(node.op).__name__} {self._get_name_from_node(node.right)}"
        elif isinstance(node, ast.List):
            return f"[{', '.join(self._get_name_from_node(elt) for elt in node.elts)}]"
        elif isinstance(node, ast.Tuple):
            return f"({', '.join(self._get_name_from_node(elt) for elt in node.elts)})"
        elif isinstance(node, ast.Dict):
            if not node.keys:
                return "{}"
            key_values = []
            for i, key in enumerate(node.keys):
                if key is None:  # Handle **unpacked
                    key_values.append(f"**{self._get_name_from_node(node.values[i])}")
                else:
                    key_values.append(
                        f"{self._get_name_from_node(key)}: {self._get_name_from_node(node.values[i])}"
                    )
            return f"{{{', '.join(key_values)}}}"
        elif isinstance(node, ast.Call):
            args = [self._get_name_from_node(arg) for arg in node.args]
            keywords = [
                f"{kw.arg}={self._get_name_from_node(kw.value)}" for kw in node.keywords
            ]
            all_args = args + keywords
            return f"{self._get_name_from_node(node.func)}({', '.join(all_args)})"
        else:
            return str(type(node).__name__)


class CodeStructureMapper:
    """
    Main class to analyze Python projects and generate code structure representations.
    """

    def __init__(
        self,
        root_path: Union[str, Path],
        project_name: Optional[str] = None,
        include_docstrings: bool = True,
        include_source: bool = False,
        include_private: bool = False,
        ignore_patterns: Optional[List[str]] = None,
        preserve_docstring_format: bool = False,
    ) -> None:
        """
        Initialize the code structure mapper.

        Args:
            root_path: Root directory of the project to analyze
            project_name: Name of the project (default: inferred from directory name)
            include_docstrings: Whether to include docstrings in the output
            include_source: Whether to include source code in the output
            include_private: Whether to include private members (prefixed with _)
            ignore_patterns: List of regex patterns for files/dirs to ignore
            preserve_docstring_format: Whether to preserve paragraph format in docstrings
        """
        self.root_path = Path(root_path).resolve()
        self.project_name = project_name or self.root_path.name
        self.include_docstrings = include_docstrings
        self.include_source = include_source
        self.include_private = include_private
        self.ignore_patterns = ignore_patterns or []
        self.ignore_regexes = [re.compile(pattern) for pattern in self.ignore_patterns]
        self.preserve_docstring_format = preserve_docstring_format

        # Add common patterns to ignore if not specified
        default_ignores = [
            r"__pycache__",
            r"\.git",
            r"\.venv",
            r"venv",
            r"\.env",
            r"\.idea",
            r"\.vscode",
            r"\.pytest_cache",
            r"\.tox",
            r"\.eggs",
            r"\.mypy_cache",
            r"build",
            r"dist",
            r"\.coverage",
            r"htmlcov",
        ]

        for pattern in default_ignores:
            if not any(re.search(pattern, ignore) for ignore in self.ignore_patterns):
                self.ignore_regexes.append(re.compile(pattern))

        self.project_info = ProjectInfo(
            name=self.project_name, root_path=self.root_path
        )

    def _should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored based on patterns."""
        str_path = str(path)
        return any(regex.search(str_path) for regex in self.ignore_regexes)

    def analyze_project(self) -> ProjectInfo:
        """
        Analyze the entire project and return the ProjectInfo.

        Returns:
            ProjectInfo object containing the project structure
        """
        logger.info(f"Analyzing project at {self.root_path}")

        # First, identify the structure (packages, modules, other files)
        self._identify_project_structure()

        # Then, analyze each Python file
        self._analyze_python_files()

        return self.project_info

    def _identify_project_structure(self) -> None:
        """
        Identify the project's structure including packages, modules, and other files.
        """
        for item in os.scandir(self.root_path):
            path = Path(item.path)

            if self._should_ignore(path):
                logger.debug(f"Ignoring {path}")
                continue

            if item.is_dir():
                # Check if it's a Python package (has __init__.py)
                init_file = path / "__init__.py"
                if init_file.exists():
                    package_info = self._process_package(path)
                    self.project_info.packages[package_info.name] = package_info
                else:
                    # It's a regular directory, scan it for non-Python files
                    self._scan_for_non_python_files(path)
            elif item.is_file():
                if path.suffix == ".py":
                    # Top-level Python module
                    module_name = path.stem
                    module_info = ModuleInfo(name=module_name, path=path)
                    self.project_info.modules[module_name] = module_info
                else:
                    # Non-Python file
                    rel_dir = str(path.parent.relative_to(self.root_path))
                    if rel_dir == ".":
                        rel_dir = ""

                    if rel_dir not in self.project_info.non_python_files:
                        self.project_info.non_python_files[rel_dir] = []

                    self.project_info.non_python_files[rel_dir].append(path.name)

    def _process_package(self, package_path: Path) -> PackageInfo:
        """
        Process a Python package directory and return information about it.

        Args:
            package_path: Path to the package directory

        Returns:
            PackageInfo object containing package structure
        """
        package_name = package_path.name
        package_info = PackageInfo(name=package_name, path=package_path)

        # Process __init__.py file
        init_file = package_path / "__init__.py"
        if init_file.exists():
            init_module = ModuleInfo(name="__init__", path=init_file)
            package_info.init_module = init_module

        # Process all items in the package
        for item in os.scandir(package_path):
            item_path = Path(item.path)

            if self._should_ignore(item_path):
                continue

            if item.is_dir():
                # Check if it's a subpackage
                subpackage_init = item_path / "__init__.py"
                if subpackage_init.exists():
                    subpackage_info = self._process_package(item_path)
                    package_info.subpackages[subpackage_info.name] = subpackage_info
                else:
                    # Regular directory, scan for non-Python files
                    self._scan_for_non_python_files(item_path)
            elif (
                item.is_file()
                and item_path.suffix == ".py"
                and item_path.name != "__init__.py"
            ):
                # Python module in the package
                module_name = item_path.stem
                module_info = ModuleInfo(name=module_name, path=item_path)
                package_info.modules[module_name] = module_info

        return package_info

    def _scan_for_non_python_files(self, directory: Path) -> None:
        """
        Scan a directory for non-Python files and add them to the project info.

        Args:
            directory: Directory to scan
        """
        for root, _, files in os.walk(directory):
            root_path = Path(root)
            if self._should_ignore(root_path):
                continue

            rel_dir = str(root_path.relative_to(self.root_path))

            python_files = []
            other_files = []

            for file in files:
                file_path = root_path / file
                if self._should_ignore(file_path):
                    continue

                if file_path.suffix == ".py":
                    python_files.append(file)
                else:
                    other_files.append(file)

            if other_files:
                if rel_dir not in self.project_info.non_python_files:
                    self.project_info.non_python_files[rel_dir] = []

                self.project_info.non_python_files[rel_dir].extend(other_files)

    def _analyze_python_files(self) -> None:
        """
        Analyze all Python files identified in the project structure.
        """
        # Analyze top-level modules
        for module_name, module_info in self.project_info.modules.items():
            self._analyze_module(module_info)

        # Analyze packages
        for package_name, package_info in self.project_info.packages.items():
            self._analyze_package(package_info)

    def _analyze_package(self, package_info: PackageInfo) -> None:
        """
        Analyze a Python package recursively.

        Args:
            package_info: PackageInfo object to be analyzed
        """
        # Analyze __init__.py if present
        if package_info.init_module:
            self._analyze_module(package_info.init_module)

        # Analyze modules in the package
        for module_name, module_info in package_info.modules.items():
            self._analyze_module(module_info)

        # Recursively analyze subpackages
        for subpackage_name, subpackage_info in package_info.subpackages.items():
            self._analyze_package(subpackage_info)

    def _analyze_module(self, module_info: ModuleInfo) -> None:
        """
        Analyze a Python module file using AST.

        Args:
            module_info: ModuleInfo object to be analyzed
        """
        try:
            with open(module_info.path, "r", encoding="utf-8") as f:
                source_code = f.read()

            tree = ast.parse(source_code)
            visitor = CustomVisitor()
            visitor.set_source(source_code)
            visitor.visit(tree)

            # Update module info with extracted data
            module_info.classes = visitor.classes
            module_info.functions = visitor.functions
            module_info.global_variables = visitor.global_vars
            module_info.imports = visitor.imports
            module_info.docstring = visitor.docstring

            # Filter out private members if not included
            if not self.include_private:
                self._filter_private_members(module_info)

            # Process docstrings
            if not self.include_docstrings:
                self._remove_docstrings(module_info)
            else:
                self._clean_docstrings(module_info)

            # Remove source code if not included
            if not self.include_source:
                self._remove_source_code(module_info)

        except Exception as e:
            logger.error(f"Error analyzing module {module_info.path}: {str(e)}")

    def _filter_private_members(self, module_info: ModuleInfo) -> None:
        """
        Filter out private members (starting with _) from the module info.

        Args:
            module_info: ModuleInfo object to filter
        """
        # Filter private functions
        module_info.functions = {
            name: info
            for name, info in module_info.functions.items()
            if not name.startswith("_") or name.startswith("__") and name.endswith("__")
        }

        # Filter private classes
        filtered_classes = {}
        for class_name, class_info in module_info.classes.items():
            if class_name.startswith("_") and not (
                class_name.startswith("__") and class_name.endswith("__")
            ):
                continue

            # Filter private methods within classes
            class_info.methods = {
                name: info
                for name, info in class_info.methods.items()
                if not name.startswith("_")
                or name.startswith("__")
                and name.endswith("__")
            }

            # Filter private attributes
            class_info.class_attributes = {
                name: value
                for name, value in class_info.class_attributes.items()
                if not name.startswith("_")
                or name.startswith("__")
                and name.endswith("__")
            }

            filtered_classes[class_name] = class_info

        module_info.classes = filtered_classes

        # Filter private global variables
        module_info.global_variables = {
            name: value
            for name, value in module_info.global_variables.items()
            if not name.startswith("_") or name.startswith("__") and name.endswith("__")
        }

    def _remove_docstrings(self, module_info: ModuleInfo) -> None:
        """
        Remove all docstrings from the module info.

        Args:
            module_info: ModuleInfo object to modify
        """
        module_info.docstring = None

        for class_info in module_info.classes.values():
            class_info.docstring = None

            for method_info in class_info.methods.values():
                method_info.docstring = None

        for func_info in module_info.functions.values():
            func_info.docstring = None

    def _clean_docstrings(self, module_info: ModuleInfo) -> None:
        """
        Clean and normalize docstrings by removing extra whitespace while preserving content.

        Args:
            module_info: ModuleInfo object to modify
        """
        if module_info.docstring:
            module_info.docstring = self._normalize_docstring(module_info.docstring)

        for class_info in module_info.classes.values():
            if class_info.docstring:
                class_info.docstring = self._normalize_docstring(class_info.docstring)

            for method_info in class_info.methods.values():
                if method_info.docstring:
                    method_info.docstring = self._normalize_docstring(
                        method_info.docstring
                    )

        for func_info in module_info.functions.values():
            if func_info.docstring:
                func_info.docstring = self._normalize_docstring(func_info.docstring)

    def _normalize_docstring(self, docstring: str) -> str:
        """
        Normalize a docstring by cleaning whitespace while preserving content.

        Args:
            docstring: The original docstring

        Returns:
            Cleaned docstring with normalized whitespace
        """
        if not docstring:
            return ""

        # If we want to preserve formatting, just clean up indentation
        if self.preserve_docstring_format:
            lines = []
            for line in docstring.splitlines():
                lines.append(line.strip())
            return "\n".join(lines)

        # For normal cleaning mode:
        # Split into lines and strip each line
        lines = [line.strip() for line in docstring.splitlines()]

        # Remove empty lines at the beginning and end
        while lines and not lines[0]:
            lines.pop(0)
        while lines and not lines[-1]:
            lines.pop()

        if not lines:
            return ""

        # For single line docstrings, just return as is
        if len(lines) == 1:
            return lines[0]

        # For multi-line docstrings, join with a space if short
        # or with a newline for longer ones to preserve structure
        joined = " ".join(lines)

        # If the result is short, return as a single line
        if len(joined) < 100:
            return joined

        # For longer docstrings, preserve paragraph structure but clean up spacing
        result = []
        current_paragraph = []

        for line in lines:
            if not line:  # Empty line marks paragraph boundary
                if current_paragraph:
                    result.append(" ".join(current_paragraph))
                    current_paragraph = []
                result.append("")  # Keep paragraph break
            else:
                current_paragraph.append(line)

        # Don't forget the last paragraph
        if current_paragraph:
            result.append(" ".join(current_paragraph))

        return "\n".join(result)

    def _remove_source_code(self, module_info: ModuleInfo) -> None:
        """
        Remove source code snippets from function info.

        Args:
            module_info: ModuleInfo object to modify
        """
        for class_info in module_info.classes.values():
            for method_info in class_info.methods.values():
                method_info.source_code = None

        for func_info in module_info.functions.values():
            func_info.source_code = None

    def export_json(self, output_path: Optional[Path] = None) -> Optional[str]:
        """
        Export the project structure as JSON.

        Args:
            output_path: Path to save the JSON file (optional)

        Returns:
            JSON string if output_path is None, otherwise None
        """
        # Convert the project info to a dictionary
        project_dict = self._project_info_to_dict()

        # Convert to JSON
        json_str = json.dumps(project_dict, indent=2)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json_str)
            logger.info(f"JSON structure written to {output_path}")
            return None
        else:
            return json_str

    def export_markdown(self, output_path: Optional[Path] = None) -> Optional[str]:
        """
        Export the project structure as Markdown.

        Args:
            output_path: Path to save the Markdown file (optional)

        Returns:
            Markdown string if output_path is None, otherwise None
        """
        md_lines = [
            f"# {self.project_name} Project Structure",
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        # Add table of contents
        md_lines.extend(
            [
                "## Table of Contents",
                "1. [Project Overview](#project-overview)",
                "2. [Directory Structure](#directory-structure)",
                "3. [Packages and Modules](#packages-and-modules)",
                "",
            ]
        )

        # Project overview
        md_lines.extend(
            [
                "## Project Overview",
                f"- Project Name: {self.project_name}",
                f"- Root Path: {self.project_info.root_path}",
                f"- Packages: {len(self.project_info.packages)}",
                f"- Top-level Modules: {len(self.project_info.modules)}",
                "",
            ]
        )

        # Directory structure
        md_lines.extend(
            [
                "## Directory Structure",
                "```",
            ]
        )

        # Generate directory tree
        md_lines.extend(self._generate_directory_tree())
        md_lines.append("```")
        md_lines.append("")

        # Packages and modules
        md_lines.append("## Packages and Modules")

        # First, top-level modules
        if self.project_info.modules:
            md_lines.append("### Top-level Modules")
            for module_name, module_info in sorted(self.project_info.modules.items()):
                md_lines.extend(self._module_to_markdown(module_info, 3))
            md_lines.append("")

        # Then, packages
        if self.project_info.packages:
            md_lines.append("### Packages")
            for package_name, package_info in sorted(
                self.project_info.packages.items()
            ):
                md_lines.extend(self._package_to_markdown(package_info, 3))
            md_lines.append("")

        # Join all lines
        markdown_str = "\n".join(md_lines)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_str)
            logger.info(f"Markdown structure written to {output_path}")
            return None
        else:
            return markdown_str

    def export_mermaid(self, output_path: Optional[Path] = None) -> Optional[str]:
        """
        Export the project structure as a Mermaid diagram.

        Args:
            output_path: Path to save the Mermaid file (optional)

        Returns:
            Mermaid string if output_path is None, otherwise None
        """
        mermaid_lines = ["classDiagram"]

        # Generate class definitions and relationships
        class_defs, relationships = self._generate_mermaid_classes()

        mermaid_lines.extend(class_defs)
        mermaid_lines.extend(relationships)

        # Join all lines
        mermaid_str = "\n".join(mermaid_lines)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(mermaid_str)
            logger.info(f"Mermaid diagram written to {output_path}")
            return None
        else:
            return mermaid_str

    def export_text(self, output_path: Optional[Path] = None) -> Optional[str]:
        """
        Export the project structure as plain text.

        Args:
            output_path: Path to save the text file (optional)

        Returns:
            Text string if output_path is None, otherwise None
        """
        lines = [
            f"{self.project_name} Project Structure",
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        # Directory structure
        lines.append("Directory Structure:")
        lines.extend(self._generate_directory_tree())
        lines.append("")

        # Top-level modules
        if self.project_info.modules:
            lines.append("Top-level Modules:")
            for module_name, module_info in sorted(self.project_info.modules.items()):
                lines.extend(self._module_to_text(module_info, 1))
            lines.append("")

        # Packages
        if self.project_info.packages:
            lines.append("Packages:")
            for package_name, package_info in sorted(
                self.project_info.packages.items()
            ):
                lines.extend(self._package_to_text(package_info, 1))
            lines.append("")

        # Join all lines
        text_str = "\n".join(lines)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text_str)
            logger.info(f"Text structure written to {output_path}")
            return None
        else:
            return text_str

    def export_directory(self, output_dir: Path) -> None:
        """
        Export the project structure as separate markdown files in a directory.

        Args:
            output_dir: Directory where the processed project will be created
        """
        logger.info(f"Exporting project structure to directory: {output_dir}")

        # Create the output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create the project index file
        self._create_project_index(output_dir)

        # Create directories for modules
        modules_dir = output_dir / "modules"
        modules_dir.mkdir(exist_ok=True)

        # Export top-level modules
        for module_name, module_info in self.project_info.modules.items():
            module_path = modules_dir / f"{module_name}.md"
            self._export_module_to_file(
                module_info, module_path, relative_path=Path("modules")
            )

        # Export packages
        packages_dir = output_dir / "packages"
        packages_dir.mkdir(exist_ok=True)

        for package_name, package_info in self.project_info.packages.items():
            package_dir = packages_dir / package_name
            package_dir.mkdir(exist_ok=True)
            self._export_package_to_directory(
                package_info, package_dir, relative_path=Path("packages") / package_name
            )

        # Create a metadata file with information about the processing
        self._create_metadata_file(output_dir)

        # Create a tree view of the project structure
        self._create_tree_view_file(output_dir)

        logger.info(f"Project structure exported successfully to {output_dir}")

    def _create_project_index(self, output_dir: Path) -> None:
        """
        Create the main index file for the processed project.

        Args:
            output_dir: The output directory
        """
        index_path = output_dir / "index.md"

        lines = [
            f"# {self.project_name} Project Structure",
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Project Overview",
            f"- **Project Name:** {self.project_name}",
            f"- **Original Path:** {self.project_info.root_path}",
            f"- **Packages:** {len(self.project_info.packages)}",
            f"- **Top-level Modules:** {len(self.project_info.modules)}",
            "",
            "## Navigation",
            "",
            "### Project Structure",
            "- [Tree View](tree_view.md) - Visual representation of the project structure",
            "",
        ]

        # Add top-level modules to the index
        if self.project_info.modules:
            lines.append("### Top-level Modules")
            for module_name in sorted(self.project_info.modules.keys()):
                lines.append(f"- [modules/{module_name}.md](modules/{module_name}.md)")
            lines.append("")

        # Add packages to the index
        if self.project_info.packages:
            lines.append("### Packages")
            for package_name in sorted(self.project_info.packages.keys()):
                lines.append(
                    f"- [packages/{package_name}/index.md](packages/{package_name}/index.md)"
                )
            lines.append("")

        # Add non-Python files section
        if self.project_info.non_python_files:
            lines.append("### Non-Python Files")
            for dir_path, files in sorted(self.project_info.non_python_files.items()):
                if not dir_path:
                    dir_display = "Root Directory"
                else:
                    dir_display = dir_path
                lines.append(f"- **{dir_display}**: {', '.join(sorted(files))}")
            lines.append("")

        # Write the index file
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _export_module_to_file(
        self,
        module_info: ModuleInfo,
        output_path: Path,
        relative_path: Optional[Path] = None,
        package_path: Optional[str] = None,
    ) -> None:
        """
        Export a module's information to a markdown file.

        Args:
            module_info: The module information
            output_path: Path where the markdown file will be saved
            relative_path: Relative path for navigation links
            package_path: Dot-separated package path for the module (if in a package)
        """
        # Get fully qualified module name
        if package_path:
            if module_info.name == "__init__":
                full_module_name = package_path
            else:
                full_module_name = f"{package_path}.{module_info.name}"
        else:
            full_module_name = module_info.name

        # Prepare the markdown content
        lines = [
            f"# Module: {full_module_name}",
            "",
            f"**Path:** `{module_info.path.relative_to(self.project_info.root_path)}`",
            "",
        ]

        # Add navigation link back
        if relative_path:
            back_link = "../" * (len(relative_path.parts))
            lines.append(f"[Back to Project Index]({back_link}index.md)")
            lines.append("")

        # Add module docstring if available
        if module_info.docstring and self.include_docstrings:
            lines.append("## Description")
            lines.append(f"{module_info.docstring}")
            lines.append("")

        # Add imports section
        if module_info.imports:
            lines.append("## Imports")
            lines.append("```python")
            for imp in module_info.imports:
                lines.append(imp)
            lines.append("```")
            lines.append("")

        # Add global variables section
        if module_info.global_variables:
            lines.append("## Global Variables")
            lines.append("```python")
            for var_name, var_value in module_info.global_variables.items():
                lines.append(f"{var_name} = {var_value}")
            lines.append("```")
            lines.append("")

        # Add functions section
        if module_info.functions:
            lines.append("## Functions")
            lines.append("")

            # Add a function summary table
            lines.append("| Function | Description |")
            lines.append("| --- | --- |")

            for func_name, func_info in sorted(module_info.functions.items()):
                brief_desc = ""
                if func_info.docstring:
                    # Extract first sentence from docstring for the summary
                    brief_desc = func_info.docstring.split(".")[0] + "."
                lines.append(f"| `{func_name}` | {brief_desc} |")

            lines.append("")

            # Add detailed function information
            for func_name, func_info in sorted(module_info.functions.items()):
                lines.append(f"### `{func_name}`")

                # Add function signature
                async_prefix = "async " if func_info.is_async else ""
                decorators = [f"@{decorator}" for decorator in func_info.decorators]

                # Add decorators
                if decorators:
                    lines.append("```python")
                    for decorator in decorators:
                        lines.append(decorator)

                    # Add signature
                    signature = (
                        f"{async_prefix}def {func_name}({', '.join(func_info.args)})"
                    )
                    if func_info.return_annotation:
                        signature += f" -> {func_info.return_annotation}"
                    signature += ":"
                    lines.append(signature)
                    lines.append("```")
                else:
                    lines.append("```python")
                    signature = (
                        f"{async_prefix}def {func_name}({', '.join(func_info.args)})"
                    )
                    if func_info.return_annotation:
                        signature += f" -> {func_info.return_annotation}"
                    signature += ":"
                    lines.append(signature)
                    lines.append("```")

                # Add function docstring
                if func_info.docstring and self.include_docstrings:
                    lines.append(f"{func_info.docstring}")

                # Add source code if included
                if func_info.source_code and self.include_source:
                    lines.append("**Source Code:**")
                    lines.append("```python")
                    lines.append(func_info.source_code)
                    lines.append("```")

                lines.append("")

        # Add classes section
        if module_info.classes:
            lines.append("## Classes")
            lines.append("")

            # Add a class summary table
            lines.append("| Class | Description |")
            lines.append("| --- | --- |")

            for class_name, class_info in sorted(module_info.classes.items()):
                brief_desc = ""
                if class_info.docstring:
                    brief_desc = class_info.docstring.split(".")[0] + "."
                lines.append(f"| `{class_name}` | {brief_desc} |")

            lines.append("")

            # Add detailed class information
            for class_name, class_info in sorted(module_info.classes.items()):
                lines.append(f"### Class: `{class_name}`")

                # Add class inheritance
                if class_info.bases:
                    lines.append(f"**Inherits from:** {', '.join(class_info.bases)}")

                # Add class decorators
                if class_info.decorators:
                    lines.append("**Decorators:**")
                    for decorator in class_info.decorators:
                        lines.append(f"- `@{decorator}`")

                # Add class docstring
                if class_info.docstring and self.include_docstrings:
                    lines.append("")
                    lines.append(class_info.docstring)

                lines.append("")

                # Add class attributes
                if class_info.class_attributes:
                    lines.append("#### Attributes")
                    lines.append("")
                    lines.append("| Name | Value |")
                    lines.append("| --- | --- |")
                    for attr_name, attr_value in class_info.class_attributes.items():
                        lines.append(f"| `{attr_name}` | `{attr_value}` |")
                    lines.append("")

                # Add class methods
                if class_info.methods:
                    lines.append("#### Methods")
                    lines.append("")

                    # Add a method summary table
                    lines.append("| Method | Description |")
                    lines.append("| --- | --- |")

                    for method_name, method_info in sorted(class_info.methods.items()):
                        brief_desc = ""
                        if method_info.docstring:
                            brief_desc = method_info.docstring.split(".")[0] + "."
                        prop_tag = " `@property`" if method_info.is_property else ""
                        async_tag = " `async`" if method_info.is_async else ""
                        lines.append(
                            f"| `{method_name}`{prop_tag}{async_tag} | {brief_desc} |"
                        )

                    lines.append("")

                    # Add detailed method information
                    for method_name, method_info in sorted(class_info.methods.items()):
                        lines.append(f"##### `{method_name}`")

                        # Add method signature
                        async_prefix = "async " if method_info.is_async else ""

                        # Add decorators
                        decorator_lines = []
                        if method_info.is_property:
                            decorator_lines.append("@property")

                        other_decorators = [
                            d for d in method_info.decorators if d != "property"
                        ]
                        decorator_lines.extend([f"@{d}" for d in other_decorators])

                        if decorator_lines:
                            lines.append("```python")
                            for dec in decorator_lines:
                                lines.append(dec)

                            # Add signature
                            signature = f"{async_prefix}def {method_name}({', '.join(method_info.args)})"
                            if method_info.return_annotation:
                                signature += f" -> {method_info.return_annotation}"
                            signature += ":"
                            lines.append(signature)
                            lines.append("```")
                        else:
                            lines.append("```python")
                            signature = f"{async_prefix}def {method_name}({', '.join(method_info.args)})"
                            if method_info.return_annotation:
                                signature += f" -> {method_info.return_annotation}"
                            signature += ":"
                            lines.append(signature)
                            lines.append("```")

                        # Add method docstring
                        if method_info.docstring and self.include_docstrings:
                            lines.append(f"{method_info.docstring}")

                        # Add source code if included
                        if method_info.source_code and self.include_source:
                            lines.append("**Source Code:**")
                            lines.append("```python")
                            lines.append(method_info.source_code)
                            lines.append("```")

                        lines.append("")

        # Write the markdown content to the file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _export_package_to_directory(
        self,
        package_info: PackageInfo,
        output_dir: Path,
        relative_path: Path,
        parent_package: Optional[str] = None,
    ) -> None:
        """
        Export a package's information to a directory with markdown files.

        Args:
            package_info: The package information
            output_dir: Directory where the package files will be saved
            relative_path: Relative path for navigation links
            parent_package: Parent package path (dot-separated) if this is a subpackage
        """
        # Create the package directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine the package path
        if parent_package:
            package_path = f"{parent_package}.{package_info.name}"
        else:
            package_path = package_info.name

        # Create the package index file
        index_path = output_dir / "index.md"
        self._create_package_index(
            package_info, index_path, relative_path, package_path
        )

        # Export the __init__.py module if it exists
        if package_info.init_module:
            init_path = output_dir / "init.md"
            self._export_module_to_file(
                package_info.init_module, init_path, relative_path, package_path
            )

        # Export all modules in the package
        for module_name, module_info in package_info.modules.items():
            module_path = output_dir / f"{module_name}.md"
            self._export_module_to_file(
                module_info, module_path, relative_path, package_path
            )

        # Export all subpackages
        for subpackage_name, subpackage_info in package_info.subpackages.items():
            subpackage_dir = output_dir / subpackage_name
            subpackage_rel_path = relative_path / subpackage_name
            self._export_package_to_directory(
                subpackage_info, subpackage_dir, subpackage_rel_path, package_path
            )

    def _create_package_index(
        self,
        package_info: PackageInfo,
        index_path: Path,
        relative_path: Path,
        package_path: str,
    ) -> None:
        """
        Create an index file for a package directory.

        Args:
            package_info: The package information
            index_path: Path where the index file will be saved
            relative_path: Relative path for navigation links
            package_path: Dot-separated package path
        """
        # Prepare the markdown content
        lines = [
            f"# Package: {package_path}",
            "",
            f"**Path:** `{package_info.path.relative_to(self.project_info.root_path)}`",
            "",
        ]

        # Add navigation link back
        back_link = "../" * len(relative_path.parts)
        lines.append(f"[Back to Project Index]({back_link}index.md)")
        if len(relative_path.parts) > 1:
            # Add link to parent package if this is a subpackage
            parent_path = "../index.md"
            parent_name = relative_path.parts[-2]
            lines.append(f"[Back to Parent Package {parent_name}]({parent_path})")
        lines.append("")

        # Add package description from __init__ docstring
        if (
            package_info.init_module
            and package_info.init_module.docstring
            and self.include_docstrings
        ):
            lines.append("## Description")
            lines.append(package_info.init_module.docstring)
            lines.append("")

        # Add __init__ module link
        if package_info.init_module:
            lines.append("## Package Initialization")
            lines.append("- [__init__.py](init.md)")
            lines.append("")

        # Add modules section
        if package_info.modules:
            lines.append("## Modules")
            lines.append("")

            # Add a module summary table
            lines.append("| Module | Description |")
            lines.append("| --- | --- |")

            for module_name, module_info in sorted(package_info.modules.items()):
                brief_desc = ""
                if module_info.docstring:
                    brief_desc = module_info.docstring.split(".")[0] + "."
                lines.append(f"| [`{module_name}`]({module_name}.md) | {brief_desc} |")

            lines.append("")

        # Add subpackages section
        if package_info.subpackages:
            lines.append("## Subpackages")
            lines.append("")

            # Add a subpackage summary table
            lines.append("| Subpackage | Description |")
            lines.append("| --- | --- |")

            for subpackage_name, subpackage_info in sorted(
                package_info.subpackages.items()
            ):
                brief_desc = ""
                if (
                    subpackage_info.init_module
                    and subpackage_info.init_module.docstring
                    and self.include_docstrings
                ):
                    brief_desc = (
                        subpackage_info.init_module.docstring.split(".")[0] + "."
                    )
                lines.append(
                    f"| [`{subpackage_name}`]({subpackage_name}/index.md) | {brief_desc} |"
                )

            lines.append("")

        # Write the markdown content to the file
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _create_metadata_file(self, output_dir: Path) -> None:
        """
        Create a metadata file with information about the processing.

        Args:
            output_dir: The output directory
        """
        metadata_path = output_dir / "metadata.md"

        lines = [
            "# Project Processing Metadata",
            "",
            f"- **Original Project:** {self.project_name}",
            f"- **Original Path:** {self.project_info.root_path}",
            f"- **Processing Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **Include Docstrings:** {self.include_docstrings}",
            f"- **Include Source Code:** {self.include_source}",
            f"- **Include Private Members:** {self.include_private}",
            f"- **Preserve Docstring Format:** {self.preserve_docstring_format}",
            "",
            "## Ignored Patterns",
            "",
        ]

        # Add ignored patterns
        for pattern in self.ignore_patterns:
            lines.append(f"- `{pattern}`")

        # Add default ignored patterns if not explicitly specified
        default_ignores = [
            r"__pycache__",
            r"\.git",
            r"\.venv",
            r"venv",
            r"\.env",
            r"\.idea",
            r"\.vscode",
            r"\.pytest_cache",
            r"\.tox",
            r"\.eggs",
            r"\.mypy_cache",
            r"build",
            r"dist",
            r"\.coverage",
            r"htmlcov",
        ]

        for pattern in default_ignores:
            if not any(re.search(pattern, ignore) for ignore in self.ignore_patterns):
                lines.append(f"- `{pattern}` (default)")

        # Write the metadata file
        with open(metadata_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _create_tree_view_file(self, output_dir: Path) -> None:
        """
        Create a tree view file to visualize the project structure.

        Args:
            output_dir: The output directory
        """
        tree_path = output_dir / "tree_view.md"

        lines = [
            "# Project Structure Tree View",
            "",
            f"Project: {self.project_name}",
            "",
            "```",
        ]

        # Generate directory tree
        lines.extend(self._generate_directory_tree())
        lines.append("```")
        lines.append("")

        # Add navigation link back to index
        lines.append("[Back to Project Index](index.md)")

        # Write the tree view file
        with open(tree_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _project_info_to_dict(self) -> Dict[str, Any]:
        """
        Convert ProjectInfo to a dictionary for JSON serialization.

        Returns:
            Dictionary representation of the project
        """
        project_dict = {
            "name": self.project_info.name,
            "root_path": str(self.project_info.root_path),
            "packages": {},
            "modules": {},
            "non_python_files": self.project_info.non_python_files,
        }

        # Convert top-level modules
        for module_name, module_info in self.project_info.modules.items():
            project_dict["modules"][module_name] = self._module_info_to_dict(
                module_info
            )

        # Convert packages
        for package_name, package_info in self.project_info.packages.items():
            project_dict["packages"][package_name] = self._package_info_to_dict(
                package_info
            )

        return project_dict

    def _package_info_to_dict(self, package_info: PackageInfo) -> Dict[str, Any]:
        """
        Convert PackageInfo to a dictionary for JSON serialization.

        Args:
            package_info: PackageInfo object to convert

        Returns:
            Dictionary representation of the package
        """
        package_dict = {
            "name": package_info.name,
            "path": str(package_info.path),
            "modules": {},
            "subpackages": {},
            "init_module": None,
        }

        # Convert init module if present
        if package_info.init_module:
            package_dict["init_module"] = self._module_info_to_dict(
                package_info.init_module
            )

        # Convert modules
        for module_name, module_info in package_info.modules.items():
            package_dict["modules"][module_name] = self._module_info_to_dict(
                module_info
            )

        # Convert subpackages
        for subpackage_name, subpackage_info in package_info.subpackages.items():
            package_dict["subpackages"][subpackage_name] = self._package_info_to_dict(
                subpackage_info
            )

        return package_dict

    def _module_info_to_dict(self, module_info: ModuleInfo) -> Dict[str, Any]:
        """
        Convert ModuleInfo to a dictionary for JSON serialization.

        Args:
            module_info: ModuleInfo object to convert

        Returns:
            Dictionary representation of the module
        """
        module_dict = {
            "name": module_info.name,
            "path": str(module_info.path),
            "classes": {},
            "functions": {},
            "imports": module_info.imports,
            "global_variables": module_info.global_variables,
            "docstring": module_info.docstring,
        }

        # Convert classes
        for class_name, class_info in module_info.classes.items():
            module_dict["classes"][class_name] = {
                "name": class_info.name,
                "bases": class_info.bases,
                "methods": {},
                "class_attributes": class_info.class_attributes,
                "docstring": class_info.docstring,
                "line_number": class_info.line_number,
                "decorators": class_info.decorators,
            }

            # Convert methods
            for method_name, method_info in class_info.methods.items():
                module_dict["classes"][class_name]["methods"][method_name] = {
                    "name": method_info.name,
                    "args": method_info.args,
                    "returns": method_info.returns,
                    "docstring": method_info.docstring,
                    "is_async": method_info.is_async,
                    "is_property": method_info.is_property,
                    "decorators": method_info.decorators,
                    "line_number": method_info.line_number,
                    "source_code": method_info.source_code,
                    "return_annotation": method_info.return_annotation,
                    "arg_annotations": method_info.arg_annotations,
                }

        # Convert functions
        for func_name, func_info in module_info.functions.items():
            module_dict["functions"][func_name] = {
                "name": func_info.name,
                "args": func_info.args,
                "returns": func_info.returns,
                "docstring": func_info.docstring,
                "is_async": func_info.is_async,
                "is_property": func_info.is_property,
                "decorators": func_info.decorators,
                "line_number": func_info.line_number,
                "source_code": func_info.source_code,
                "return_annotation": func_info.return_annotation,
                "arg_annotations": func_info.arg_annotations,
            }

        return module_dict

    def _generate_directory_tree(self) -> List[str]:
        """
        Generate a text tree representation of the project's directory structure.

        Returns:
            List of lines representing the directory tree
        """
        lines = [f"{self.project_info.root_path.name}/"]

        # Helper function to recursively build the tree
        def build_tree(path: Path, prefix: str = "", is_last: bool = True) -> List[str]:
            tree_lines = []
            items = list(os.scandir(path))

            # Filter out ignored items
            items = [item for item in items if not self._should_ignore(Path(item.path))]

            # Sort items: directories first, then files
            items.sort(key=lambda x: (not x.is_dir(), x.name))

            for i, item in enumerate(items):
                is_last_item = i == len(items) - 1
                item_prefix = prefix + ("└── " if is_last_item else "├── ")
                next_prefix = prefix + ("    " if is_last_item else "│   ")

                tree_lines.append(
                    f"{item_prefix}{item.name}{os.sep if item.is_dir() else ''}"
                )

                if item.is_dir():
                    tree_lines.extend(
                        build_tree(Path(item.path), next_prefix, is_last_item)
                    )

            return tree_lines

        lines.extend(build_tree(self.project_info.root_path))
        return lines

    def _module_to_markdown(
        self, module_info: ModuleInfo, header_level: int
    ) -> List[str]:
        """
        Convert a module to Markdown format.

        Args:
            module_info: ModuleInfo to convert
            header_level: Level for Markdown headers

        Returns:
            List of Markdown lines
        """
        hashes = "#" * header_level
        lines = [f"{hashes} Module: {module_info.name}"]

        if module_info.docstring and self.include_docstrings:
            lines.append(f"*{module_info.docstring.strip().split('.')[0]}.*")

        lines.append(f"Path: `{module_info.path}`")
        lines.append("")

        # Imports
        if module_info.imports:
            lines.append("**Imports:**")
            lines.append("```python")
            for imp in module_info.imports:
                lines.append(imp)
            lines.append("```")
            lines.append("")

        # Global variables
        if module_info.global_variables:
            lines.append("**Global Variables:**")
            lines.append("```python")
            for var_name, var_value in module_info.global_variables.items():
                lines.append(f"{var_name} = {var_value}")
            lines.append("```")
            lines.append("")

        # Functions
        if module_info.functions:
            lines.append("**Functions:**")
            for func_name, func_info in sorted(module_info.functions.items()):
                async_prefix = "async " if func_info.is_async else ""
                decorators = "\n".join(
                    [f"@{decorator}" for decorator in func_info.decorators]
                )
                if decorators:
                    decorators += "\n"

                signature = (
                    f"{async_prefix}def {func_name}({', '.join(func_info.args)})"
                )
                if func_info.return_annotation:
                    signature += f" -> {func_info.return_annotation}"
                signature += ":"

                lines.append("```python")
                lines.append(f"{decorators}{signature}")
                if func_info.docstring and self.include_docstrings:
                    lines.append(f'    """{func_info.docstring}"""')
                lines.append("```")
                lines.append("")

        # Classes
        if module_info.classes:
            lines.append("**Classes:**")
            for class_name, class_info in sorted(module_info.classes.items()):
                bases = ", ".join(class_info.bases) if class_info.bases else "object"
                decorators = "\n".join(
                    [f"@{decorator}" for decorator in class_info.decorators]
                )
                if decorators:
                    decorators += "\n"

                lines.append("```python")
                lines.append(f"{decorators}class {class_name}({bases}):")
                if class_info.docstring and self.include_docstrings:
                    lines.append(f'    """{class_info.docstring}"""')
                lines.append("```")

                # Class attributes
                if class_info.class_attributes:
                    lines.append("*Class attributes:*")
                    lines.append("```python")
                    for attr_name, attr_value in class_info.class_attributes.items():
                        lines.append(f"{attr_name} = {attr_value}")
                    lines.append("```")

                # Methods
                if class_info.methods:
                    lines.append("*Methods:*")
                    for method_name, method_info in sorted(class_info.methods.items()):
                        async_prefix = "async " if method_info.is_async else ""
                        property_prefix = (
                            "@property\n" if method_info.is_property else ""
                        )
                        other_decorators = "\n".join(
                            [
                                f"@{decorator}"
                                for decorator in method_info.decorators
                                if decorator != "property"
                            ]
                        )
                        if other_decorators:
                            other_decorators += "\n"

                        signature = f"{async_prefix}def {method_name}({', '.join(method_info.args)})"
                        if method_info.return_annotation:
                            signature += f" -> {method_info.return_annotation}"
                        signature += ":"

                        lines.append("```python")
                        lines.append(
                            f"{property_prefix}{other_decorators}    {signature}"
                        )
                        if method_info.docstring and self.include_docstrings:
                            lines.append(f'        """{method_info.docstring}"""')
                        lines.append("```")

                lines.append("")

        return lines

    def _package_to_markdown(
        self, package_info: PackageInfo, header_level: int
    ) -> List[str]:
        """
        Convert a package to Markdown format.

        Args:
            package_info: PackageInfo to convert
            header_level: Level for Markdown headers

        Returns:
            List of Markdown lines
        """
        hashes = "#" * header_level
        lines = [f"{hashes} Package: {package_info.name}"]
        lines.append(f"Path: `{package_info.path}`")
        lines.append("")

        # Init module
        if package_info.init_module:
            lines.append("**__init__.py:**")
            init_lines = self._module_to_markdown(
                package_info.init_module, header_level + 1
            )
            # Skip the header line for the init module
            lines.extend(init_lines[1:])

        # Modules
        if package_info.modules:
            for module_name, module_info in sorted(package_info.modules.items()):
                lines.extend(self._module_to_markdown(module_info, header_level + 1))

        # Subpackages
        if package_info.subpackages:
            for subpackage_name, subpackage_info in sorted(
                package_info.subpackages.items()
            ):
                lines.extend(
                    self._package_to_markdown(subpackage_info, header_level + 1)
                )

        return lines

    def _module_to_text(self, module_info: ModuleInfo, indent_level: int) -> List[str]:
        """
        Convert a module to text format.

        Args:
            module_info: ModuleInfo to convert
            indent_level: Indentation level

        Returns:
            List of text lines
        """
        indent = "  " * indent_level
        lines = [
            f"{indent}{module_info.name} ({module_info.path.relative_to(self.project_info.root_path)})"
        ]

        if module_info.docstring and self.include_docstrings:
            docstring_first_line = module_info.docstring.strip().split(".")[0]
            lines.append(f"{indent}  {docstring_first_line}")

        # Global variables
        if module_info.global_variables:
            lines.append(f"{indent}  Global Variables:")
            for var_name, var_value in module_info.global_variables.items():
                lines.append(f"{indent}    {var_name}")

        # Functions
        if module_info.functions:
            lines.append(f"{indent}  Functions:")
            for func_name, func_info in sorted(module_info.functions.items()):
                async_prefix = "async " if func_info.is_async else ""
                signature = (
                    f"{async_prefix}def {func_name}({', '.join(func_info.args)})"
                )
                if func_info.return_annotation:
                    signature += f" -> {func_info.return_annotation}"
                lines.append(f"{indent}    {signature}")

        # Classes
        if module_info.classes:
            lines.append(f"{indent}  Classes:")
            for class_name, class_info in sorted(module_info.classes.items()):
                bases = f" ({', '.join(class_info.bases)})" if class_info.bases else ""
                lines.append(f"{indent}    {class_name}{bases}")

                # Class attributes
                if class_info.class_attributes:
                    lines.append(f"{indent}      Attributes:")
                    for attr_name in class_info.class_attributes:
                        lines.append(f"{indent}        {attr_name}")

                # Methods
                if class_info.methods:
                    lines.append(f"{indent}      Methods:")
                    for method_name, method_info in sorted(class_info.methods.items()):
                        async_prefix = "async " if method_info.is_async else ""
                        property_prefix = (
                            "@property " if method_info.is_property else ""
                        )
                        signature = f"{property_prefix}{async_prefix}def {method_name}({', '.join(method_info.args)})"
                        if method_info.return_annotation:
                            signature += f" -> {method_info.return_annotation}"
                        lines.append(f"{indent}        {signature}")

        return lines

    def _package_to_text(
        self, package_info: PackageInfo, indent_level: int
    ) -> List[str]:
        """
        Convert a package to text format.

        Args:
            package_info: PackageInfo to convert
            indent_level: Indentation level

        Returns:
            List of text lines
        """
        indent = "  " * indent_level
        lines = [
            f"{indent}{package_info.name}/ ({package_info.path.relative_to(self.project_info.root_path)})"
        ]

        # Init module
        if package_info.init_module:
            lines.append(f"{indent}  __init__.py:")
            init_lines = self._module_to_text(
                package_info.init_module, indent_level + 2
            )
            # Skip the first line which has the module name
            lines.extend(init_lines[1:])

        # Modules
        if package_info.modules:
            lines.append(f"{indent}  Modules:")
            for module_name, module_info in sorted(package_info.modules.items()):
                module_lines = self._module_to_text(module_info, indent_level + 2)
                lines.extend(module_lines)

        # Subpackages
        if package_info.subpackages:
            lines.append(f"{indent}  Subpackages:")
            for subpackage_name, subpackage_info in sorted(
                package_info.subpackages.items()
            ):
                subpackage_lines = self._package_to_text(
                    subpackage_info, indent_level + 2
                )
                lines.extend(subpackage_lines)

        return lines

    def _generate_mermaid_classes(self) -> Tuple[List[str], List[str]]:
        """
        Generate Mermaid class diagram content.

        Returns:
            Tuple containing (class definitions, relationships)
        """
        class_defs = []
        relationships = []
        processed_classes = set()

        # Helper function to process a module
        def process_module(module_info: ModuleInfo, package_path: str = "") -> None:
            module_prefix = f"{package_path}." if package_path else ""

            for class_name, class_info in module_info.classes.items():
                full_class_name = f"{module_prefix}{module_info.name}.{class_name}"

                if full_class_name in processed_classes:
                    continue
                processed_classes.add(full_class_name)

                # Add class definition
                class_defs.append(f"  class {full_class_name}")

                # Add attributes
                for attr_name in class_info.class_attributes:
                    visibility = "-" if attr_name.startswith("_") else "+"
                    class_defs.append(f"  {full_class_name} : {visibility}{attr_name}")

                # Add methods
                for method_name, method_info in class_info.methods.items():
                    visibility = "-" if method_name.startswith("_") else "+"
                    args_str = ", ".join(method_info.args)
                    return_str = (
                        f" : {method_info.return_annotation}"
                        if method_info.return_annotation
                        else ""
                    )
                    method_sig = f"{visibility}{method_name}({args_str}){return_str}"

                    if method_info.is_property:
                        method_sig = f"{visibility}{method_name}{return_str} [property]"

                    class_defs.append(f"  {full_class_name} : {method_sig}")

                # Add inheritance relationships
                for base_class in class_info.bases:
                    if "." not in base_class:
                        # Attempt to find the base class in the same module
                        if base_class in module_info.classes:
                            base_full_name = (
                                f"{module_prefix}{module_info.name}.{base_class}"
                            )
                            relationships.append(
                                f"  {base_full_name} <|-- {full_class_name}"
                            )
                    else:
                        # Fully qualified base class
                        relationships.append(f"  {base_class} <|-- {full_class_name}")

        # Process top-level modules
        for module_name, module_info in self.project_info.modules.items():
            process_module(module_info)

        # Helper function to process a package
        def process_package(package_info: PackageInfo, package_path: str = "") -> None:
            current_path = (
                f"{package_path}.{package_info.name}"
                if package_path
                else package_info.name
            )

            # Process init module
            if package_info.init_module:
                process_module(package_info.init_module, current_path)

            # Process modules
            for module_name, module_info in package_info.modules.items():
                process_module(module_info, current_path)

            # Process subpackages
            for subpackage_name, subpackage_info in package_info.subpackages.items():
                process_package(subpackage_info, current_path)

        # Process packages
        for package_name, package_info in self.project_info.packages.items():
            process_package(package_info)

        return class_defs, relationships


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive code structure maps for AI analysis."
    )
    parser.add_argument("input", help="Input directory or file to analyze")
    parser.add_argument(
        "--output", help="Output file or directory (for directory format)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "mermaid", "text", "directory"],
        default="markdown",
        help="Output format (default: markdown; use 'directory' for file-based structure)",
    )
    parser.add_argument("--project-name", help="Project name (default: directory name)")
    parser.add_argument(
        "--include-docstrings",
        action="store_true",
        help="Include docstrings in the output",
    )
    parser.add_argument(
        "--include-source",
        action="store_true",
        help="Include source code in the output",
    )
    parser.add_argument(
        "--include-private",
        action="store_true",
        help="Include private members in the output",
    )
    parser.add_argument("--ignore", help="Comma-separated list of patterns to ignore")
    parser.add_argument(
        "--preserve-docstring-format",
        action="store_true",
        help="Preserve paragraph format in docstrings (default: clean and compact)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean the output directory before exporting (only for directory format)",
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Parse ignore patterns
    ignore_patterns = []
    if args.ignore:
        ignore_patterns = [pattern.strip() for pattern in args.ignore.split(",")]

    # Create the mapper
    mapper = CodeStructureMapper(
        root_path=args.input,
        project_name=args.project_name,
        include_docstrings=args.include_docstrings,
        include_source=args.include_source,
        include_private=args.include_private,
        ignore_patterns=ignore_patterns,
        preserve_docstring_format=args.preserve_docstring_format,
    )

    # Analyze the project
    mapper.analyze_project()

    # Handle output based on format
    if args.format == "directory":
        if args.output:
            output_dir = Path(args.output)
        else:
            output_dir = Path("processed_project")

        # Clean the output directory if requested
        if args.clean and output_dir.exists():
            logger.info(f"Cleaning output directory: {output_dir}")
            shutil.rmtree(output_dir)

        # Export in directory format
        mapper.export_directory(output_dir)
    else:
        # Handle other formats as before
        output_path = Path(args.output) if args.output else None

        if args.format == "json":
            result = mapper.export_json(output_path)
        elif args.format == "markdown":
            result = mapper.export_markdown(output_path)
        elif args.format == "mermaid":
            result = mapper.export_mermaid(output_path)
        elif args.format == "text":
            result = mapper.export_text(output_path)
        else:
            parser.error(f"Unsupported format: {args.format}")
            return

        # Print to stdout if no output file specified
        if result:
            print(result)


if __name__ == "__main__":
    main()
