# Media Processor Plugin Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [User Interface](#user-interface)
4. [Processing Configurations](#processing-configurations)
5. [Background Removal Techniques](#background-removal-techniques)
6. [Output Formats](#output-formats)
7. [Batch Processing](#batch-processing)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

## Introduction

The Media Processor Plugin provides comprehensive tools for processing digital media files, with a focus on image processing. Key features include background removal with various techniques, multiple output format configurations, watermarking capabilities, and batch processing support.

The plugin is designed to handle large batches of images efficiently, running processing tasks in the background to maintain application responsiveness.

## Installation

To install the Media Processor Plugin:

1. Place the `media_processor` directory in your Qorzen plugins folder.
2. Restart the application or use the plugin manager to load the plugin.

### Dependencies

The plugin requires the following dependencies:
- Pillow (PIL) for image processing
- PySide6 for UI components

Optional dependencies for enhanced functionality:
- ONNX Runtime for ML-based background removal
- NumPy for advanced image processing

## User Interface

The Media Processor Plugin provides a comprehensive user interface with the following components:

### Main Interface
- **File Selection**: Add individual files or entire folders to process
- **Configuration Selection**: Choose from saved processing configurations
- **Preview Area**: View the original image, background removal preview, or output format preview
- **Output Details**: See information about the projected output files
- **Processing Controls**: Process selected or all files

### Navigation
The plugin can be accessed through:
- The main "Media" menu
- The plugin's main page in the application tab interface

## Processing Configurations

Processing configurations define how media files are processed and can be saved for reuse. Each configuration includes:

1. **General Settings**
   - Name and description
   - Output directory

2. **Background Removal Settings**
   - Removal method and parameters
   - Post-processing options

3. **Output Formats**
   - Multiple format definitions
   - Each with its own settings

4. **Batch Processing Options**
   - Output organization
   - Subfolder templates

### Managing Configurations

- **Create**: Click "New" in the configuration section to create a new configuration
- **Edit**: Select a configuration and click "Edit" to modify it
- **Save**: Save configurations to disk for later use
- **Load**: Load previously saved configurations

## Background Removal Techniques

The plugin offers several background removal techniques, each optimized for different scenarios:

### Chroma Key

Best for images shot against a solid color background (like green screens).

**Settings:**
- **Key Color**: The background color to remove
- **Tolerance**: How much color variation to include in the removal

**Tips:**
- Works best with evenly lit, solid-color backgrounds
- Increase tolerance for uneven lighting or shadows

### Alpha Matting

Uses brightness values to determine foreground/background. Good for high-contrast images.

**Settings:**
- **Foreground Threshold**: Brightness level for definite foreground
- **Background Threshold**: Brightness level for definite background

**Tips:**
- Works well for objects photographed on white/black backgrounds
- Adjust thresholds for optimal separation

### ML Model

Uses machine learning to identify subjects regardless of background complexity.

**Settings:**
- **Model**: Neural network model to use (U2Net, DeepLabV3, etc.)
- **Confidence Threshold**: Minimum confidence level to consider as foreground

**Tips:**
- Most versatile but computationally intensive
- Higher confidence thresholds give cleaner edges but may lose detail

### Smart Selection

Interactive selection tools for complex cases.

**Settings:**
- **Brush Size**: Size of the selection brush
- **Feather Amount**: Edge softening for selections

**Tips:**
- Best for complex or difficult cases requiring manual input
- Use feathering to create natural-looking edges

### Manual Mask

Uses a pre-created binary mask image.

**Settings:**
- **Mask Path**: Path to the mask image file

**Tips:**
- Use for maximum control
- Mask should be a grayscale image where white represents the foreground

### Post-Processing Options

These options can be applied regardless of the removal method:

- **Edge Feathering**: Softens the edges between foreground and background
- **Edge Refinement**: Improves edge definition
- **Denoising**: Reduces noise in the alpha channel

## Output Formats

Each processing configuration can include multiple output formats, allowing you to generate various versions of processed files simultaneously.

### Format Types

Supported output formats include:
- PNG (with transparency)
- JPEG (with quality control)
- TIFF
- BMP
- WEBP
- PDF

### Format Settings

Each format configuration includes:

1. **Basic Settings**
   - Format type
   - Quality setting
   - Image adjustments (brightness, contrast, saturation, sharpness)

2. **Size and Cropping**
   - Resize mode (width, height, exact, maximum, minimum, percentage)
   - Dimensions
   - Aspect ratio control
   - Cropping
   - Padding
   - Rotation

3. **Background**
   - Transparent or solid color
   - Background color selection

4. **Watermark**
   - Text or image watermarks
   - Position, opacity, scale
   - Font settings for text
   - Outlines

5. **File Settings**
   - Prefix and suffix
   - Naming template
   - Subdirectory

## Batch Processing

The plugin provides robust batch processing capabilities to handle multiple files efficiently.

### Starting a Batch Process

1. Add multiple files to the interface
2. Configure processing settings
3. Click "Process All Files"

### Batch Dialog

The batch processing dialog provides:
- Overall progress tracking
- File-by-file status
- Time estimates
- Pause/Resume and Cancel buttons
- Option to minimize while processing continues

### Background Processing

Batch operations run in the background, allowing you to continue using the application. The plugin uses a task queue system to manage concurrent processing and prevent system overload.

## Troubleshooting

### Common Issues

#### Background Removal Problems

- **Problem**: Background not fully removed
  **Solution**: Adjust the thresholds for the removal method or try a different method

- **Problem**: Parts of the subject are transparent
  **Solution**: Decrease tolerance, adjust thresholds, or use edge refinement

#### Output Format Issues

- **Problem**: Unexpected transparency
  **Solution**: Check the "Transparent Background" setting

- **Problem**: Poor quality in compressed formats
  **Solution**: Increase the quality setting

#### Batch Processing Issues

- **Problem**: Processing is slow
  **Solution**: Reduce the number of output formats or simplify background removal method

- **Problem**: Application becomes unresponsive
  **Solution**: Adjust the concurrent jobs setting in the plugin configuration

## Best Practices

### Optimizing Workflow

1. **Create Reusable Configurations**
   - Set up configurations for common scenarios
   - Save them with descriptive names

2. **Start Small for Testing**
   - Test with a few representative images before processing large batches
   - Verify output quality and settings

3. **Organize Output**
   - Use subdirectories and naming templates to keep outputs organized
   - Consider creating separate configurations for different output needs

### Performance Tips

1. **Choose the Right Background Removal Method**
   - Use chroma key or alpha matting when possible (faster)
   - Reserve ML models for complex backgrounds

2. **Optimize Output Formats**
   - Limit the number of output formats per configuration
   - Consider file size vs. quality needs

3. **System Resources**
   - Close other resource-intensive applications during large batch operations
   - Adjust maximum concurrent jobs based on your system's capabilities