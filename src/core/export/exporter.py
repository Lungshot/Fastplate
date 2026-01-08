"""
Exporter
Handles exporting nameplate geometry to various 3D file formats.
"""

import cadquery as cq
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Union


class ExportFormat(Enum):
    """Supported export formats."""
    STL = "stl"
    STEP = "step"
    OBJ = "obj"
    AMF = "amf"
    THREE_MF = "3mf"


@dataclass
class ExportOptions:
    """Options for export."""
    format: ExportFormat = ExportFormat.STL
    
    # STL options
    stl_ascii: bool = False
    stl_tolerance: float = 0.1      # Linear deflection
    stl_angular_tolerance: float = 0.1  # Angular deflection
    
    # Multi-part export
    export_separate_parts: bool = False  # Export base and text separately
    
    # File naming
    base_suffix: str = "_base"
    text_suffix: str = "_text"


class Exporter:
    """
    Exports CadQuery geometry to various 3D file formats.
    """
    
    EXTENSION_MAP = {
        ExportFormat.STL: ".stl",
        ExportFormat.STEP: ".step",
        ExportFormat.OBJ: ".obj",
        ExportFormat.AMF: ".amf",
        ExportFormat.THREE_MF: ".3mf",
    }
    
    def __init__(self, options: Optional[ExportOptions] = None):
        self.options = options or ExportOptions()
    
    def export(self, geometry: cq.Workplane, filepath: Union[str, Path],
               options: Optional[ExportOptions] = None) -> bool:
        """
        Export geometry to file.
        
        Args:
            geometry: CadQuery Workplane to export
            filepath: Output file path
            options: Optional export options override
            
        Returns:
            True if export succeeded, False otherwise.
        """
        opts = options or self.options
        filepath = Path(filepath)
        
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Determine format from extension or options
        ext = filepath.suffix.lower()
        if ext == '.stl':
            return self._export_stl(geometry, filepath, opts)
        elif ext in ['.step', '.stp']:
            return self._export_step(geometry, filepath)
        elif ext == '.obj':
            return self._export_obj(geometry, filepath)
        elif ext == '.amf':
            return self._export_amf(geometry, filepath)
        elif ext == '.3mf':
            return self._export_3mf(geometry, filepath)
        else:
            # Default to STL
            return self._export_stl(geometry, filepath.with_suffix('.stl'), opts)
    
    def export_parts(self, base: cq.Workplane, text: cq.Workplane,
                     filepath: Union[str, Path],
                     options: Optional[ExportOptions] = None) -> bool:
        """
        Export base and text as separate files for multi-color printing.
        
        Args:
            base: Base plate geometry
            text: Text geometry
            filepath: Base output file path (suffixes will be added)
            options: Optional export options override
            
        Returns:
            True if both exports succeeded.
        """
        opts = options or self.options
        filepath = Path(filepath)
        stem = filepath.stem
        ext = filepath.suffix or self.EXTENSION_MAP[opts.format]
        
        base_path = filepath.parent / f"{stem}{opts.base_suffix}{ext}"
        text_path = filepath.parent / f"{stem}{opts.text_suffix}{ext}"
        
        base_ok = self.export(base, base_path, opts)
        text_ok = self.export(text, text_path, opts)
        
        return base_ok and text_ok
    
    def _export_stl(self, geometry: cq.Workplane, filepath: Path,
                    opts: ExportOptions) -> bool:
        """Export to STL format."""
        try:
            cq.exporters.export(
                geometry,
                str(filepath),
                exportType='STL',
                tolerance=opts.stl_tolerance,
                angularTolerance=opts.stl_angular_tolerance
            )
            return True
        except Exception as e:
            print(f"STL export error: {e}")
            return False
    
    def _export_step(self, geometry: cq.Workplane, filepath: Path) -> bool:
        """Export to STEP format."""
        try:
            cq.exporters.export(geometry, str(filepath), exportType='STEP')
            return True
        except Exception as e:
            print(f"STEP export error: {e}")
            return False
    
    def _export_obj(self, geometry: cq.Workplane, filepath: Path) -> bool:
        """Export to OBJ format."""
        try:
            # OBJ export via tessellation
            cq.exporters.export(geometry, str(filepath))
            return True
        except Exception as e:
            print(f"OBJ export error: {e}")
            return False
    
    def _export_amf(self, geometry: cq.Workplane, filepath: Path) -> bool:
        """Export to AMF format."""
        try:
            cq.exporters.export(geometry, str(filepath), exportType='AMF')
            return True
        except Exception as e:
            print(f"AMF export error: {e}")
            return False
    
    def _export_3mf(self, geometry: cq.Workplane, filepath: Path) -> bool:
        """Export to 3MF format."""
        try:
            cq.exporters.export(geometry, str(filepath), exportType='3MF')
            return True
        except Exception as e:
            print(f"3MF export error: {e}")
            return False
    
    @staticmethod
    def get_supported_formats() -> list:
        """Get list of supported export formats."""
        return [
            ("STL Files", "*.stl"),
            ("STEP Files", "*.step *.stp"),
            ("3MF Files", "*.3mf"),
            ("AMF Files", "*.amf"),
        ]
