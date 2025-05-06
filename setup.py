"""Setup script for the Qorzen application.

This script installs the Qorzen application and its dependencies.
"""

from __future__ import annotations

import os
import pathlib
import setuptools

# Read the long description from README.md
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

# Read version from __version__.py
version = {}
with open("qorzen/__version__.py", "r", encoding="utf-8") as f:
    exec(f.read(), version)

# Dependencies
install_requires = [
    "pydantic>=2.0.0",
    "PySide6>=6.5.0",
    "pyyaml>=6.0",
    "sqlalchemy>=2.0.0",
    "structlog>=22.1.0",
    "httpx>=0.24.0",
    "jwt>=1.3.1",
    "passlib>=1.7.4",
    "psutil>=5.9.0",
    "prometheus_client>=0.16.0",
    "tenacity>=8.2.0",
    "python-json-logger>=2.0.4",
]

# Development dependencies
dev_requires = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.1.0",
    "isort>=5.12.0",
    "mypy>=1.0.0",
    "types-pyyaml",
    "types-requests",
    "pyinstaller>=5.9.0",
]

# Build dependencies
build_requires = [
    "pyinstaller>=5.9.0",
    "wheel>=0.38.0",
    "setuptools>=65.5.0",
]

setuptools.setup(
    name="qorzen",
    version=version.get("__version__", "0.1.0"),
    author="Qorzen Team",
    author_email="contact@qorzen.com",
    description="A modular, extensible platform for the automotive aftermarket industry",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://qorzen.com",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=install_requires,
    extras_require={
        "dev": dev_requires,
        "build": build_requires,
        "all": dev_requires + build_requires,
    },
    entry_points={
        "console_scripts": [
            "qorzen=qorzen.main:main",
            "qorzen-build=qorzen.build.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "qorzen": ["**/*.png", "**/*.ico", "**/*.json", "**/*.yaml", "**/*.yml"],
    },
)