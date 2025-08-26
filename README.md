# Unified Tissue Extraction Pipeline

A comprehensive Python pipeline that combines SVS conversion, mask generation, and tissue extraction into a single automated workflow.

## 🔬 Overview

This pipeline takes only two inputs:
1. An `.svs` file (whole-slide image)
2. A `.geojson` file (tissue annotations/mask)

And produces a single **RGBA TIFF** file with extracted tissue regions and transparent background.

## 🚀 Pipeline Stages

1. **SVS → Pyramidal TIFF**: Converts the input SVS file to a pyramidal TIFF format
2. **Mask Generation**: Creates a pyramidal binary mask from GeoJSON annotations
3. **Tissue Extraction**: Extracts tissue regions as RGBA with transparent background

## 📦 Installation

### Option 1: Conda (Recommended)

```bash
# Create and activate environment
conda env create -f environment.yml
conda activate tissue-extraction-pipeline
```

### Option 2: Pip

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install libvips-dev openslide-tools

# Install system dependencies (macOS)
brew install vips openslide
```

## 🎯 Usage

### Basic Usage

```bash
python unified_tissue_pipeline.py input.svs annotations.geojson output_tissue.tiff
```

### Advanced Usage

```bash
# Specify temporary directory and compression
python unified_tissue_pipeline.py \
    tissue.svs \
    mask.geojson \
    extracted_tissue.tiff \
    --temp-dir ./temp \
    --compression lzw

# Clean up intermediate files automatically
python unified_tissue_pipeline.py \
    tissue.svs \
    mask.geojson \
    output.tiff \
    --no-keep-intermediates
```

### Command Line Options

- `--temp-dir <path>`: Directory for intermediate files (default: system temp)
- `--no-keep-intermediates`: Delete intermediate files after completion
- `--compression <type>`: Output compression type (default: lzw)

## 📁 Output Files

### Final Output
- **RGBA TIFF**: Pyramidal TIFF with extracted tissue
  - Tissue regions: Opaque (alpha = 255)
  - Background: Transparent (alpha = 0)
  - Preserves original pyramid structure

### Intermediate Files (for debugging)
- `tissue_pyramidal.tiff`: Converted SVS as pyramidal TIFF
- `mask_pyramidal.tiff`: Generated pyramidal mask

## 🎨 Features

- **Progress Tracking**: Real-time progress bars with timing information
- **Rich Console Output**: Beautiful terminal interface with status updates
- **Error Handling**: Comprehensive validation and error reporting
- **Memory Efficient**: Processes large images using pyramidal structures
- **Modular Design**: Clean separation of pipeline stages
- **Debugging Support**: Preserves intermediate files for analysis

## 📊 Performance

The pipeline automatically displays:
- Processing time for each stage
- File size comparisons
- Compression ratios
- Memory usage optimization

## 🔧 Technical Details

### Dependencies
- **pyvips**: High-performance image processing
- **openslide**: Medical image format support
- **opencv**: Computer vision operations
- **shapely**: Geometric operations for masks
- **rich**: Beautiful terminal interface
- **tifffile**: TIFF format handling

### Image Formats
- **Input**: SVS (Aperio), TIFF, other OpenSlide-supported formats
- **Masks**: GeoJSON with polygon/multipolygon geometries
- **Output**: Pyramidal TIFF with RGBA channels

### Memory Management
- Processes images in tiles to handle large files
- Uses pyramidal structures to optimize memory usage
- Configurable cache settings via environment variables

## 🐳 Docker Support

The pipeline is designed to be easily containerized:

```dockerfile
FROM continuumio/miniconda3

# Copy environment file
COPY environment.yml /app/
WORKDIR /app

# Create conda environment
RUN conda env create -f environment.yml

# Copy pipeline script
COPY unified_tissue_pipeline.py /app/

# Activate environment and run
SHELL ["conda", "run", "-n", "tissue-extraction-pipeline", "/bin/bash", "-c"]
ENTRYPOINT ["conda", "run", "-n", "tissue-extraction-pipeline", "python", "unified_tissue_pipeline.py"]
```

## 🔍 Troubleshooting

### Common Issues

1. **Memory errors**: Reduce `VIPS_CONCURRENCY` environment variable
2. **OpenSlide errors**: Ensure system dependencies are installed
3. **GeoJSON format**: Verify GeoJSON contains valid polygon features
4. **File permissions**: Check read/write access to input/output directories

### Environment Variables

```bash
export VIPS_CONCURRENCY=2          # Reduce for low-memory systems
export VIPS_DISC_THRESHOLD=500mb   # Adjust disk cache threshold
export OPENCV_IO_MAX_IMAGE_PIXELS=1073741824  # Max image size
```

## 📝 Example Workflow

```bash
# 1. Prepare your files
ls -la
# input.svs          (whole-slide image)
# annotations.geojson (tissue mask)

# 2. Run the pipeline
python unified_tissue_pipeline.py input.svs annotations.geojson extracted_tissue.tiff

# 3. Check results
ls -la extracted_tissue.tiff
# RGBA TIFF with transparent background and extracted tissue
```

## 🤝 Contributing

This pipeline combines and extends functionality from multiple specialized scripts:
- SVS conversion utilities
- Pyramidal mask generation
- Advanced tissue extraction

When contributing, please maintain the modular structure and comprehensive error handling.

## 📄 License

This project builds upon existing medical imaging tools and follows their respective licensing terms.