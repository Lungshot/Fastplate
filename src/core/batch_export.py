"""
Batch Export
Exports multiple nameplate variations at once.
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import json


@dataclass
class ExportItem:
    """Single item to export."""
    name: str
    config: Dict[str, Any]
    filename: str = ""

    def __post_init__(self):
        if not self.filename:
            # Generate filename from name
            safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in self.name)
            self.filename = f"{safe_name}.stl"


@dataclass
class BatchExportConfig:
    """Configuration for batch export."""
    output_directory: str = ""
    format: str = "stl"              # stl, step, obj
    create_subdirectory: bool = True  # Create subdirectory for batch
    naming_pattern: str = "{index:03d}_{name}"  # Pattern for filenames
    include_preview: bool = False     # Export preview images
    preview_size: tuple = (800, 600)


class BatchExporter:
    """
    Handles batch export of multiple nameplate configurations.
    """

    def __init__(self, generator_func: Callable[[Dict], Any]):
        """
        Initialize the batch exporter.

        Args:
            generator_func: Function that takes a config dict and returns geometry
        """
        self._generator = generator_func
        self._progress_callback: Optional[Callable[[int, int, str], None]] = None
        self._cancel_requested = False

    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """Set callback for progress updates: (current, total, message)."""
        self._progress_callback = callback

    def cancel(self):
        """Request cancellation of the current batch export."""
        self._cancel_requested = True

    def export_batch(self, items: List[ExportItem],
                     config: BatchExportConfig) -> Dict[str, Any]:
        """
        Export a batch of nameplates.

        Args:
            items: List of items to export
            config: Batch export configuration

        Returns:
            Dictionary with results: {
                'success': bool,
                'exported': List[str],
                'failed': List[tuple],  # (name, error)
                'output_dir': str
            }
        """
        self._cancel_requested = False
        results = {
            'success': True,
            'exported': [],
            'failed': [],
            'output_dir': ''
        }

        if not items:
            results['success'] = False
            return results

        # Create output directory
        output_dir = Path(config.output_directory)
        if config.create_subdirectory:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = output_dir / f"batch_{timestamp}"

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            results['output_dir'] = str(output_dir)
        except Exception as e:
            results['success'] = False
            results['failed'].append(("directory", str(e)))
            return results

        # Export each item
        total = len(items)
        for i, item in enumerate(items):
            if self._cancel_requested:
                break

            # Update progress
            if self._progress_callback:
                self._progress_callback(i + 1, total, f"Exporting: {item.name}")

            try:
                # Generate geometry
                geometry = self._generator(item.config)
                if geometry is None:
                    results['failed'].append((item.name, "Failed to generate geometry"))
                    continue

                # Generate filename
                filename = config.naming_pattern.format(
                    index=i + 1,
                    name=item.name,
                    format=config.format
                )
                if not filename.endswith(f".{config.format}"):
                    filename += f".{config.format}"

                # Make filename safe
                filename = "".join(c if c.isalnum() or c in "-_." else "_" for c in filename)
                filepath = output_dir / filename

                # Export based on format
                self._export_geometry(geometry, str(filepath), config.format)
                results['exported'].append(str(filepath))

            except Exception as e:
                results['failed'].append((item.name, str(e)))

        # Save batch manifest
        try:
            manifest = {
                'items': [{'name': item.name, 'filename': item.filename} for item in items],
                'exported': len(results['exported']),
                'failed': len(results['failed']),
                'format': config.format
            }
            manifest_path = output_dir / "batch_manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
        except Exception:
            pass

        results['success'] = len(results['failed']) == 0
        return results

    def _export_geometry(self, geometry, filepath: str, format: str):
        """Export geometry to file."""
        import cadquery as cq

        if format == "stl":
            cq.exporters.export(geometry, filepath, exportType="STL")
        elif format == "step":
            cq.exporters.export(geometry, filepath, exportType="STEP")
        elif format == "obj":
            # OBJ export via STL conversion if needed
            cq.exporters.export(geometry, filepath, exportType="STL")
            # Note: Would need additional processing for true OBJ
        else:
            cq.exporters.export(geometry, filepath, exportType="STL")


class VariationGenerator:
    """
    Generates variations of a base configuration.
    """

    @staticmethod
    def generate_text_variations(base_config: Dict, texts: List[str]) -> List[ExportItem]:
        """
        Generate variations with different text content.

        Args:
            base_config: Base configuration to modify
            texts: List of text strings to use

        Returns:
            List of ExportItems with varied text
        """
        items = []
        for text in texts:
            config = base_config.copy()
            # Update text in config
            if 'text' in config and 'lines' in config['text']:
                if config['text']['lines']:
                    # Update first line's first segment
                    config['text']['lines'][0]['segments'][0]['content'] = text
            items.append(ExportItem(name=text, config=config))
        return items

    @staticmethod
    def generate_size_variations(base_config: Dict,
                                 sizes: List[tuple]) -> List[ExportItem]:
        """
        Generate variations with different plate sizes.

        Args:
            base_config: Base configuration to modify
            sizes: List of (width, height) tuples

        Returns:
            List of ExportItems with varied sizes
        """
        items = []
        for width, height in sizes:
            config = base_config.copy()
            if 'plate' in config:
                config['plate']['width'] = width
                config['plate']['height'] = height
            name = f"{width}x{height}mm"
            items.append(ExportItem(name=name, config=config))
        return items

    @staticmethod
    def generate_color_variations(base_config: Dict,
                                  materials: List[str]) -> List[ExportItem]:
        """
        Generate variations with different material presets.
        (For visualization/organization purposes)

        Args:
            base_config: Base configuration to modify
            materials: List of material preset names

        Returns:
            List of ExportItems
        """
        items = []
        for material in materials:
            config = base_config.copy()
            config['material'] = material
            items.append(ExportItem(name=material, config=config))
        return items
