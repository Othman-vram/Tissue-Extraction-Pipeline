#!/usr/bin/env python3
import os
import sys
import json
import time
import tempfile
import platform
from pathlib import Path
from typing import Tuple, Optional

try:
    import numpy as np
    import cv2
    import pyvips
    import openslide
    from PIL import Image
    import tifffile
    from shapely.geometry import shape
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich import print as rprint
    from tqdm import tqdm
except ImportError as e:
    print(f"Required library not found: {e}")
    print("Please install required packages with: conda env create -f environment.yml")
    sys.exit(1)

# Enable pyvips cache tracing for debugging
# pyvips.cache_set_trace(True)  # Disabled for clean output

class UnifiedTissueExtractionPipeline:
    """Unified pipeline for tissue extraction from SVS files"""
    
    def __init__(self, keep_intermediates: bool = True, compression: str = 'lzw'):
        self.keep_intermediates = keep_intermediates
        self.compression = compression
        
        # Detect if we can use colors
        self.use_colors = self._can_use_colors()
        self.console = Console(force_terminal=True, color_system="auto" if self.use_colors else None)
    
    def _can_use_colors(self) -> bool:
        """Detect if terminal supports colors"""
        # Check if we're on Windows and in basic cmd
        if platform.system() == "Windows":
            # Check if Windows Terminal or modern terminal
            if os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM"):
                return True
            # Basic cmd.exe usually doesn't support colors well
            return False
        return True
    
    def print_header(self):
        """Print pipeline header with fallback for no colors"""
        if self.use_colors:
            self.console.print(Panel.fit(
                Text("🔬 Unified Tissue Extraction Pipeline", style="bold blue"),
                border_style="blue"
            ))
        else:
            print("=" * 60)
            print("🔬 UNIFIED TISSUE EXTRACTION PIPELINE")
            print("=" * 60)
    
    def print_level_selection(self, tissue_levels: int, mask_levels: int, max_levels: int):
        """Print level selection with fallback for no colors"""
        if self.use_colors:
            level_info = f"""[bold]Available Pyramid Levels:[/bold]
• Tissue levels: {tissue_levels}
• Mask levels: {mask_levels}  
• Maximum processable: {max_levels}
• Level indices: 0 to {max_levels-1}

[bold]Selection Options:[/bold]
• Single level: '0' or '2'
• Multiple levels: '0,1,2' or '1,3,5'  
• Range: '0-3' or '2-5'
• All levels: press Enter (default)"""
            
            self.console.print(Panel(level_info, title="🔍 Level Selection", border_style="cyan"))
        else:
            print("\n" + "─" * 50)
            print("🔍 LEVEL SELECTION")
            print("─" * 50)
            print(f"Available Pyramid Levels:")
            print(f"• Tissue levels: {tissue_levels}")
            print(f"• Mask levels: {mask_levels}")
            print(f"• Maximum processable: {max_levels}")
            print(f"• Level indices: 0 to {max_levels-1}")
            print(f"\nSelection Options:")
            print(f"• Single level: '0' or '2'")
            print(f"• Multiple levels: '0,1,2' or '1,3,5'")
            print(f"• Range: '0-3' or '2-5'")
            print(f"• All levels: press Enter (default)")
            print("─" * 50)
    
    def print_summary(self, total_time: float, svs_size: float, output_size: float, 
                     output_path: str, tissue_tiff_path: str, mask_tiff_path: str):
        """Print final summary with fallback for no colors"""
        if self.use_colors:
            self.console.print(Panel.fit(
                f"""[green]✓ Pipeline completed successfully![/green]

📊 [bold]Results:[/bold]
• Total processing time: {total_time:.1f} seconds
• Input SVS size: {svs_size:.1f} MB
• Output RGBA size: {output_size:.1f} MB
• Compression ratio: {output_size/svs_size:.2f}x

📁 [bold]Files:[/bold]
• Final output: {output_path}
• Tissue TIFF: {tissue_tiff_path}
• Mask TIFF: {mask_tiff_path}

🎨 [bold]Output format:[/bold]
• RGBA pyramidal TIFF
• Transparent background
• Opaque tissue regions
• Preserved pyramid structure""",
                title="Pipeline Summary",
                border_style="green"
            ))
        else:
            print("\n" + "=" * 60)
            print("✓ PIPELINE COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print(f"📊 RESULTS:")
            print(f"• Total processing time: {total_time:.1f} seconds")
            print(f"• Input SVS size: {svs_size:.1f} MB")
            print(f"• Output RGBA size: {output_size:.1f} MB")
            print(f"• Compression ratio: {output_size/svs_size:.2f}x")
            print(f"\n📁 FILES:")
            print(f"• Final output: {output_path}")
            print(f"• Tissue TIFF: {tissue_tiff_path}")
            print(f"• Mask TIFF: {mask_tiff_path}")
            print(f"\n🎨 OUTPUT FORMAT:")
            print(f"• RGBA pyramidal TIFF")
            print(f"• Transparent background")
            print(f"• Opaque tissue regions")
            print(f"• Preserved pyramid structure")
            print("=" * 60)
        
    def log_info(self, message: str):
        """Log info message with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        if self.use_colors:
            self.console.print(f"[blue][{timestamp}][/blue] {message}")
        else:
            print(f"[{timestamp}] {message}")
    
    def log_success(self, message: str):
        """Log success message"""
        if self.use_colors:
            self.console.print(f"[green]✓[/green] {message}")
        else:
            print(f"✓ {message}")
    
    def log_warning(self, message: str):
        """Log warning message"""
        if self.use_colors:
            self.console.print(f"[yellow]⚠[/yellow] {message}")
        else:
            print(f"⚠ {message}")
    
    def log_error(self, message: str):
        """Log error message"""
        if self.use_colors:
            self.console.print(f"[red]✗[/red] {message}")
        else:
            print(f"✗ {message}")

    def validate_inputs(self, svs_path: str, geojson_path: str) -> None:
        """Validate input files exist and are accessible"""
        if not os.path.exists(svs_path):
            raise FileNotFoundError(f"SVS file not found: {svs_path}")
        
        if not os.path.exists(geojson_path):
            raise FileNotFoundError(f"GeoJSON file not found: {geojson_path}")
        
        # Test if SVS can be opened
        try:
            wsi = openslide.OpenSlide(svs_path)
            wsi.close()
        except Exception as e:
            raise ValueError(f"Cannot open SVS file: {e}")
        
        # Test if GeoJSON is valid
        try:
            with open(geojson_path, "r") as f:
                geojson_data = json.load(f)
            if "features" not in geojson_data:
                raise ValueError("Invalid GeoJSON: missing 'features' key")
        except Exception as e:
            raise ValueError(f"Cannot parse GeoJSON file: {e}")

    def convert_svs_to_tiff(self, svs_path: str, output_tiff_path: str, 
                           progress: Progress, task_id) -> Tuple[int, int]:
        """
        Convert SVS file to pyramidal TIFF using your exact working code
        """
        progress.update(task_id, description="Loading SVS file...")
        
        # Your exact working code
        img = pyvips.Image.new_from_file(svs_path, access="sequential")
        
        progress.update(task_id, advance=50, description="Converting to pyramidal TIFF...")
        
        img.tiffsave(
            output_tiff_path,
            tile=True,
            pyramid=True,
            compression="jpeg",
            bigtiff=True
        )
        
        progress.update(task_id, completed=100, description="SVS conversion completed")
        
        return img.width, img.height

    def generate_pyramidal_mask(self, svs_path: str, geojson_path: str, 
                               output_mask_path: str, progress: Progress, task_id) -> None:
        """
        Generate pyramidal mask - your exact pyramidal_mask.py code
        """
        progress.update(task_id, description="Opening WSI for dimensions...")
        
        # === 1. Open the WSI to extract dimensions (your exact code)
        wsi = openslide.OpenSlide(svs_path)
        base_width, base_height = wsi.dimensions
        tile_size = wsi.properties.get("openslide.tile-width", 512)
        wsi.close()
        
        progress.update(task_id, advance=20, description="Loading GeoJSON annotations...")
        
        # === 2. Load and transform GeoJSON to match full res (your exact code)
        with open(geojson_path, "r") as f:
            geojson = json.load(f)

        geoms = [shape(f["geometry"]) for f in geojson["features"]]
        
        progress.update(task_id, advance=20, description="Creating full-resolution mask...")
        
        # === 3. Create full-resolution binary mask (your exact code)
        mask = np.zeros((base_height, base_width), dtype=np.uint8)
        mask_value = 255

        for geom in geoms:
            if geom.geom_type == "Polygon":
                polygons = [np.array(geom.exterior.coords, np.int32)]
            elif geom.geom_type == "MultiPolygon":
                polygons = [np.array(p.exterior.coords, np.int32) for p in geom.geoms]
            else:
                continue

            for poly in polygons:
                cv2.fillPoly(mask, [poly], mask_value)
        
        progress.update(task_id, advance=30, description="Converting to pyvips format...")
        
        # === 4. Convert to pyvips (your exact code)
        vips_img = pyvips.Image.new_from_memory(
            mask.tobytes(), base_width, base_height, 1, format="uchar"
        )
        
        progress.update(task_id, advance=20, description="Saving pyramidal mask...")
        
        # === 5. Save pyramidal TIFF with same pyramid logic (your exact code)
        vips_img.tiffsave(
            output_mask_path,
            bigtiff=True,
            compression="deflate",
            tile=True,
            tile_width=int(tile_size),
            tile_height=int(tile_size),
            pyramid=True,
        )
        
        progress.update(task_id, completed=100, description="Mask generation completed")

    def convert_to_rgba(self, tissue_img: np.ndarray, mask_binary: np.ndarray) -> np.ndarray:
        """
        Convert tissue image to RGBA with transparent background
        (Your exact advanced_tissue_extractor.py code)
        """
        height, width = tissue_img.shape[:2]
        
        # Handle different input formats
        if len(tissue_img.shape) == 2:
            # Grayscale input - convert to RGB
            rgb_img = np.stack([tissue_img, tissue_img, tissue_img], axis=2)
        elif tissue_img.shape[2] == 3:
            # RGB input
            rgb_img = tissue_img.copy()
        elif tissue_img.shape[2] == 4:
            # Already RGBA - use RGB channels
            rgb_img = tissue_img[:, :, :3]
        else:
            raise ValueError(f"Unsupported image format: {tissue_img.shape}")
        
        # Create RGBA image
        rgba_img = np.zeros((height, width, 4), dtype=tissue_img.dtype)
        
        # Copy RGB channels
        rgba_img[:, :, :3] = rgb_img
        
        # Set alpha channel based on mask
        # Where mask is 1 (tissue), alpha = 255 (opaque)
        # Where mask is 0 (background), alpha = 0 (transparent)
        if tissue_img.dtype == np.uint8:
            rgba_img[:, :, 3] = mask_binary * 255
        elif tissue_img.dtype == np.uint16:
            rgba_img[:, :, 3] = mask_binary * 65535
        else:
            rgba_img[:, :, 3] = mask_binary.astype(tissue_img.dtype)
        
        return rgba_img

    def parse_level_selection(self, levels_str: str, max_levels: int) -> list:
        """
        Parse level selection string into list of level indices
        (Your exact advanced_tissue_extractor.py code)
        """
        selected = []
        
        for part in levels_str.split(','):
            part = part.strip()
            
            if '-' in part:
                # Range specification (e.g., "0-3")
                start, end = map(int, part.split('-'))
                selected.extend(range(start, min(end + 1, max_levels)))
            else:
                # Single level (e.g., "0")
                level = int(part)
                if level < max_levels:
                    selected.append(level)
        
        # Remove duplicates and sort
        return sorted(list(set(selected)))

    def extract_tissue_rgba(self, tissue_path: str, mask_path: str, output_path: str,
                           mask_threshold: int = 128) -> None:
        """
        Extract tissue using mask and output as RGBA with transparency
        (Your exact advanced_tissue_extractor.py code with interactive level selection)
        """
        self.log_info("Starting RGBA tissue extraction...")
        
        # Use pyvips to read pyramid levels since it created the files
        try:
            tissue_img = pyvips.Image.new_from_file(tissue_path)
            tissue_levels = tissue_img.get('n-pages') if tissue_img.get_typeof('n-pages') != 0 else 1
            tissue_shape = (tissue_img.height, tissue_img.width)
        except Exception as e:
            raise ValueError(f"Invalid tissue TIFF file: {e}")
        
        try:
            mask_img = pyvips.Image.new_from_file(mask_path)
            mask_levels = mask_img.get('n-pages') if mask_img.get_typeof('n-pages') != 0 else 1
            mask_shape = (mask_img.height, mask_img.width)
        except Exception as e:
            raise ValueError(f"Invalid mask TIFF file: {e}")
        
        self.log_info(f"Available levels - Tissue: {tissue_levels}, Mask: {mask_levels}")
        
        if tissue_levels != mask_levels:
            self.log_warning(f"Different pyramid levels (tissue: {tissue_levels}, mask: {mask_levels})")
            max_levels = min(tissue_levels, mask_levels)
        else:
            max_levels = tissue_levels
        
        # Display level selection
        self.print_level_selection(tissue_levels, mask_levels, max_levels)
        
        try:
            levels_input = input("\nEnter pyramid levels to process (default: all): ").strip()
        except (EOFError, KeyboardInterrupt):
            self.log_warning("User interrupted level selection, using all levels")
            levels_input = ""
        
        if not levels_input:
            # Default: process all levels
            selected_levels = list(range(max_levels))
            self.log_info(f"Using all {max_levels} levels: {selected_levels}")
        else:
            # Parse user input
            selected_levels = self.parse_level_selection(levels_input, max_levels)
            self.log_info(f"Selected levels: {selected_levels}")
        
        self.log_info(f"Processing {len(selected_levels)} pyramid levels: {selected_levels}")
        
        # Create output directory
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        # Use pyvips to read pyramid levels and tifffile to write
        with tifffile.TiffWriter(output_path, bigtiff=True) as writer:
            
            # Use rich progress bar instead of tqdm for consistency
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=self.console
            ) as progress:
                
                task = progress.add_task("Processing pyramid levels...", total=len(selected_levels))
            
                for i, level in enumerate(selected_levels):
                    progress.update(task, description=f"Processing level {level}...")
                    
                    # Read images at current level using pyvips
                    tissue_vips = pyvips.Image.new_from_file(tissue_path, page=level)
                    mask_vips = pyvips.Image.new_from_file(mask_path, page=level)
                    
                    # Convert to numpy arrays
                    tissue_img = np.ndarray(buffer=tissue_vips.write_to_memory(),
                                          dtype=np.uint8,
                                          shape=[tissue_vips.height, tissue_vips.width, tissue_vips.bands])
                    
                    mask_img = np.ndarray(buffer=mask_vips.write_to_memory(),
                                        dtype=np.uint8,
                                        shape=[mask_vips.height, mask_vips.width, mask_vips.bands])
                    
                    # Process mask
                    if len(mask_img.shape) == 3:
                        mask_img = mask_img[:, :, 0]  # Use first channel
                    
                    # Resize mask if dimensions don't match
                    if mask_img.shape[:2] != tissue_img.shape[:2]:
                        try:
                            mask_img = cv2.resize(
                                mask_img, 
                                (tissue_img.shape[1], tissue_img.shape[0]),
                                interpolation=cv2.INTER_NEAREST
                            )
                        except:
                            mask_img = np.array(Image.fromarray(mask_img).resize(
                                (tissue_img.shape[1], tissue_img.shape[0]),
                                Image.NEAREST
                            ))
                    
                    # Create binary mask (1 for tissue, 0 for background)
                    mask_binary = (mask_img > mask_threshold).astype(np.uint8)
                    
                    # Convert to RGBA with transparent background
                    rgba_extracted = self.convert_to_rgba(tissue_img, mask_binary)
                    
                    # Write level to output with RGBA photometric interpretation
                    writer.write(
                        rgba_extracted,
                        subfiletype=1 if level > 0 or level != selected_levels[0] else 0,
                        compression=self.compression,
                        photometric='rgb',
                        extrasamples=[1]    # 1 = associated alpha (transparency)
                    )
                    
                    progress.update(task, advance=1)
                
                progress.update(task, completed=len(selected_levels), description="Tissue extraction completed")

    def run_pipeline(self, svs_path: str, geojson_path: str, output_path: str,
                    temp_dir: Optional[str] = None) -> None:
        """
        Run the complete tissue extraction pipeline
        """
        
        # Display pipeline header
        self.print_header()
        
        start_time = time.time()
        
        # Validate inputs
        self.log_info("Validating input files...")
        try:
            self.validate_inputs(svs_path, geojson_path)
            self.log_success("Input validation passed")
        except Exception as e:
            self.log_error(f"Input validation failed: {e}")
            return
        
        # Setup temporary directory
        if temp_dir is None:
            temp_dir = tempfile.mkdtemp(prefix="tissue_pipeline_")
        else:
            os.makedirs(temp_dir, exist_ok=True)
        
        # Define intermediate file paths
        tissue_tiff_path = os.path.join(temp_dir, "tissue_pyramidal.tiff")
        mask_tiff_path = os.path.join(temp_dir, "mask_pyramidal.tiff")
        
        self.log_info(f"Working directory: {temp_dir}")
        self.log_info(f"Input SVS: {svs_path}")
        self.log_info(f"Input GeoJSON: {geojson_path}")
        self.log_info(f"Final output: {output_path}")
        
        # Create progress tracker for first two stages
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            # Stage 1: Convert SVS to pyramidal TIFF
            task1 = progress.add_task("Converting SVS to TIFF...", total=100)
            try:
                width, height = self.convert_svs_to_tiff(
                    svs_path, tissue_tiff_path, progress, task1
                )
                self.log_success(f"SVS converted to TIFF ({width}x{height})")
                self.log_info(f"Tissue TIFF: {tissue_tiff_path}")
            except Exception as e:
                self.log_error(f"SVS conversion failed: {e}")
                return
            
            # Stage 2: Generate pyramidal mask
            task2 = progress.add_task("Generating pyramidal mask...", total=100)
            try:
                self.generate_pyramidal_mask(
                    svs_path, geojson_path, mask_tiff_path, progress, task2
                )
                self.log_success("Pyramidal mask generated")
                self.log_info(f"Mask TIFF: {mask_tiff_path}")
            except Exception as e:
                self.log_error(f"Mask generation failed: {e}")
                return
        
        # Stage 3: Extract tissue with RGBA transparency (your exact code)
        self.log_info("Starting tissue extraction phase...")
        try:
            self.extract_tissue_rgba(
                tissue_tiff_path, mask_tiff_path, output_path
            )
            self.log_success("Tissue extraction completed")
        except Exception as e:
            self.log_error(f"Tissue extraction failed: {e}")
            return
        
        # Calculate timing and file sizes
        total_time = time.time() - start_time
        
        # File size information
        svs_size = os.path.getsize(svs_path) / (1024 * 1024)  # MB
        output_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        
        # Display results
        self.print_summary(total_time, svs_size, output_size, output_path, tissue_tiff_path, mask_tiff_path)
        
        # Cleanup intermediate files if requested
        if not self.keep_intermediates:
            try:
                os.remove(tissue_tiff_path)
                os.remove(mask_tiff_path)
                os.rmdir(temp_dir)
                self.log_info("Intermediate files cleaned up")
            except Exception as e:
                self.log_warning(f"Could not clean up intermediate files: {e}")
        else:
            self.log_info("Intermediate files preserved for debugging")

def main():
    """Main function with command line interface"""
    
    if len(sys.argv) < 4:
        print("Usage: python unified_tissue_pipeline.py <svs_file> <geojson_file> <output_rgba_tiff> [options]")
        print("\nOptions:")
        print("  --temp-dir <path>           Directory for intermediate files")
        print("  --no-keep-intermediates     Delete intermediate files after completion")
        print("  --compression <type>        Output compression (default: lzw)")
        print("\nExample:")
        print("python unified_tissue_pipeline.py tissue.svs annotations.geojson extracted_tissue.tiff")
        print("python unified_tissue_pipeline.py tissue.svs mask.geojson output.tiff --temp-dir ./temp")
        print("\nPipeline stages:")
        print("1. Convert SVS → Pyramidal TIFF")
        print("2. Generate pyramidal mask from GeoJSON")
        print("3. Extract tissue → RGBA TIFF with transparency")
        print("\nNote: During tissue extraction, you'll be prompted to select which pyramid levels to process.")
        sys.exit(1)
    
    svs_path = sys.argv[1]
    geojson_path = sys.argv[2]
    output_path = sys.argv[3]
    
    # Parse optional arguments
    temp_dir = None
    keep_intermediates = True
    compression = 'lzw'
    
    i = 4
    while i < len(sys.argv):
        if sys.argv[i] == '--temp-dir' and i + 1 < len(sys.argv):
            temp_dir = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--no-keep-intermediates':
            keep_intermediates = False
            i += 1
        elif sys.argv[i] == '--compression' and i + 1 < len(sys.argv):
            compression = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    try:
        pipeline = UnifiedTissueExtractionPipeline(
            keep_intermediates=keep_intermediates,
            compression=compression
        )
        pipeline.run_pipeline(svs_path, geojson_path, output_path, temp_dir)
    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()