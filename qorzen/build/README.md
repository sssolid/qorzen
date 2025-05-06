# Qorzen Build System

The Qorzen Build System is a comprehensive toolset for packaging the Qorzen application as standalone executables for various platforms. It provides both a programmatic API and a command-line interface for building and packaging the application.

## Features

- Cross-platform builds (Windows, macOS, Linux)
- Multiple build types (one-file, one-directory)
- Resource bundling
- Dependency analysis
- Build verification
- Installer creation
- Configuration management

## Installation

The build system is included with the Qorzen application, but requires additional dependencies for building:

```bash
pip install qorzen[build]
```

Or directly install the required dependencies:

```bash
pip install pyinstaller wheel setuptools
```

## Usage

### Command-Line Interface

The build system can be used from the command line via the `qorzen-build` command or by running `python -m qorzen.build.cli`:

```bash
# Basic build with default settings
qorzen-build

# Build for specific platform
qorzen-build --platform windows

# Create a single-file executable
qorzen-build --build-type onefile

# Clean output directory before building
qorzen-build --clean

# Create an installer
qorzen-build --create-installer

# Specify custom output directory
qorzen-build --output-dir dist/myapp

# Include debug information
qorzen-build --debug

# Save build configuration to a file
qorzen-build --save-config build_config.json

# Load build configuration from a file
qorzen-build --config build_config.json
```

You can also use the `qorzen build` command:

```bash
qorzen build --platform windows --type onefile --clean --create-installer
```

### Programmatic API

The build system can also be used programmatically:

```python
from qorzen.build.builder import Builder
from qorzen.build.config import BuildConfig, BuildPlatform, BuildType

# Create build configuration
config = BuildConfig(
    name="MyApp",
    version="1.0.0",
    platform=BuildPlatform.WINDOWS,
    build_type=BuildType.ONEFILE,
    console=False,
    icon_path="path/to/icon.ico",
    output_dir="dist/myapp",
    clean=True,
)

# Create builder
builder = Builder(config)

# Build the application
output_path = builder.build()

print(f"Build completed successfully: {output_path}")
```

## Configuration

The build system is highly configurable. You can specify various options including:

- Target platform (Windows, macOS, Linux)
- Build type (one-file, one-directory)
- Console mode
- Application icon
- Entry point script
- Output directory
- Resource inclusion/exclusion
- Hidden imports
- UPX compression
- Debug options
- Environment variables

Configuration can be provided via command-line arguments, programmatically, or through a JSON configuration file.

### Example Configuration File

```json
{
  "name": "Qorzen",
  "version": "0.1.0",
  "platform": "windows",
  "build_type": "onedir",
  "console": false,
  "icon_path": "resources/icons/qorzen.ico",
  "entry_point": "qorzen/main.py",
  "output_dir": "dist",
  "clean": true,
  "upx": true,
  "debug": false,
  "hidden_imports": [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets"
  ],
  "additional_data": {
    "resources/icons": "icons",
    "resources/templates": "templates"
  }
}
```

## Creating Installers

The build system can create installers for the built application:

- Windows: Inno Setup installers (requires Inno Setup to be installed)
- macOS: DMG files (macOS only)

To create an installer, use the `--create-installer` command-line option or call the `create_installer` function programmatically:

```python
from qorzen.build.utils import create_installer

installer_path = create_installer(output_path, config)
```

## Platform-Specific Considerations

### Windows

- For Windows builds, ensure you have the Microsoft Visual C++ Redistributable installed
- To create installers, install Inno Setup and ensure `iscc` is in your PATH

### macOS

- For macOS builds, ensure you have Xcode Command Line Tools installed
- For code signing, set up appropriate code signing certificates

### Linux

- Install required dependencies for PyInstaller (varies by distribution)
- For AppImage or other Linux package formats, additional tools may be needed

## Troubleshooting

Common build issues and their solutions:

1. **Missing dependencies**: Use the `--hidden-import` option to specify modules that aren't automatically detected
2. **Missing resources**: Use the `additional_data` configuration to include necessary files
3. **UPX errors**: Disable UPX compression with `--no-upx`
4. **Build fails on specific platform**: Ensure all platform-specific dependencies are installed
5. **Large executable size**: Use the `--exclude-path` option to exclude unnecessary modules

If you encounter any other issues, please check the PyInstaller documentation or open an issue on the Qorzen repository.