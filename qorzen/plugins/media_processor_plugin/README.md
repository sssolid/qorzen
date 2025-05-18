# Media Processor Plugin

A powerful plugin for processing digital media files with advanced background removal and multiple output formats.

## Features

### Background Removal
- Multiple background removal techniques:
  - Chroma key (green screen)
  - Alpha matting
  - ML-based segmentation
  - Smart selection
  - Manual masking
- Configurable edge refinement
- Feathering and denoising options

### Output Formats
- Support for multiple output formats per processing task
- Format options include:
  - PNG, JPEG, TIFF, BMP, WEBP, PDF
  - Transparent backgrounds (for supported formats)
  - Custom background colors
  - Quality settings
  - EXIF data preservation/customization

### Image Transformations
- Resizing with multiple options:
  - Fixed width/height
  - Percentage scaling
  - Maximum/minimum dimensions
  - Aspect ratio preservation
- Cropping
- Padding with custom colors
- Rotation
- Image adjustments (brightness, contrast, saturation, sharpness)

### Watermarking
- Text watermarks with:
  - Font selection
  - Size and color options
  - Optional outlines
  - Rotation and opacity
- Image watermarks with:
  - Custom positioning
  - Scaling and opacity
  - Rotation

### File Naming and Organization
- Custom naming templates with variables:
  - {name} - Original filename
  - {ext} - File extension
  - {date} - Current date
  - {time} - Current time
  - {timestamp} - Unix timestamp
  - {random} - Random string
  - {counter} - Incremental counter (for duplicates)
- Custom prefixes and suffixes
- Subdirectory options

### Batch Processing
- Process multiple files at once
- Progress tracking
- Pause, resume, and cancel options
- Custom batch output organization
- Background processing

## Usage

### Processing Single Files
1. Add files using the "Add Files" button or drag and drop
2. Select or create a processing configuration
3. Preview the results with different output formats
4. Click "Process Selected" to process the file

### Batch Processing
1. Add multiple files
2. Configure processing settings
3. Click "Process All Files"
4. Monitor progress in the batch dialog

### Managing Configurations
- Create, edit, and save processing configurations
- Each configuration can include:
  - Background removal settings
  - Multiple output formats
  - Batch processing options

## Technical Details

### Supported Input Formats
- JPEG (.jpg, .jpeg)
- PNG (.png)
- TIFF (.tiff, .tif)
- BMP (.bmp)
- WEBP (.webp)
- PSD (.psd) - Photoshop documents
- GIF (.gif)

### Supported Output Formats
- JPEG (.jpg, .jpeg)
- PNG (.png)
- TIFF (.tiff, .tif)
- BMP (.bmp)
- WEBP (.webp)
- PDF (.pdf)

### System Requirements
- The plugin runs in the background and is designed to handle large batches
- For best performance with ML-based background removal:
  - 8GB+ RAM recommended
  - GPU support (when enabled)

## License

MIT License

## Acknowledgements

This plugin uses components from:
- Pillow for image processing
- U2Net/DeepLabV3 for ML-based segmentation (when enabled)