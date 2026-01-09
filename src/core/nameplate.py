"""
Nameplate Builder
Main class that combines all geometry components to create complete nameplates.
"""

import cadquery as cq
from dataclasses import dataclass, field
from typing import Optional, Tuple, List
from pathlib import Path

from .geometry.base_plates import BasePlateGenerator, PlateConfig, PlateShape
from .geometry.text_builder import TextBuilder, TextConfig, TextStyle, TextLineConfig
from .geometry.borders import BorderGenerator, BorderConfig, BorderStyle
from .geometry.mounts import MountGenerator, MountConfig, MountType
from .geometry.sweeping import SweepingPlateGenerator, SweepingConfig
from .geometry.svg_importer import SVGImporter, SVGElement
from .export.exporter import Exporter, ExportOptions, ExportFormat


@dataclass
class NameplateConfig:
    """Complete configuration for a nameplate."""
    # Plate settings
    plate: PlateConfig = field(default_factory=PlateConfig)
    
    # Sweeping settings (used when plate.shape == SWEEPING)
    sweeping: SweepingConfig = field(default_factory=SweepingConfig)
    
    # Text settings
    text: TextConfig = field(default_factory=TextConfig)
    
    # Border settings
    border: BorderConfig = field(default_factory=BorderConfig)
    
    # Mount settings
    mount: MountConfig = field(default_factory=MountConfig)
    
    # Icons (Nerd Fonts)
    icons: List[dict] = field(default_factory=list)  # List of icon configs

    # SVG elements
    svg_elements: List[SVGElement] = field(default_factory=list)

    # Metadata
    name: str = "Untitled"
    
    def to_dict(self) -> dict:
        """Convert config to dictionary for serialization."""
        return {
            'name': self.name,
            'plate': {
                'shape': self.plate.shape.value,
                'width': self.plate.width,
                'height': self.plate.height,
                'thickness': self.plate.thickness,
                'corner_radius': self.plate.corner_radius,
                'auto_width': self.plate.auto_width,
                'auto_height': self.plate.auto_height,
                'padding_top': self.plate.padding_top,
                'padding_bottom': self.plate.padding_bottom,
                'padding_left': self.plate.padding_left,
                'padding_right': self.plate.padding_right,
            },
            'sweeping': {
                'width': self.sweeping.width,
                'height': self.sweeping.height,
                'thickness': self.sweeping.thickness,
                'curve_angle': self.sweeping.curve_angle,
                'curve_radius': self.sweeping.curve_radius,
                'base_type': self.sweeping.base_type,
            },
            'text': {
                'lines': [
                    {
                        'content': line.content,
                        'font_family': line.font_family,
                        'font_style': line.font_style,
                        'font_size': line.font_size,
                    }
                    for line in self.text.lines
                ],
                'style': self.text.style.value,
                'depth': self.text.depth,
                'halign': self.text.halign.value,
                'valign': self.text.valign.value,
                'line_spacing': self.text.line_spacing,
            },
            'border': {
                'enabled': self.border.enabled,
                'style': self.border.style.value,
                'width': self.border.width,
                'height': self.border.height,
            },
            'mount': {
                'type': self.mount.mount_type.value,
                'stand_angle': self.mount.stand_angle,
            },
            'icons': self.icons,
            'svg_elements': [
                {
                    'name': elem.name,
                    'paths': elem.paths,
                    'viewbox': elem.viewbox,
                    'width': elem.width,
                    'height': elem.height,
                    'position_x': elem.position_x,
                    'position_y': elem.position_y,
                    'rotation': elem.rotation,
                    'scale_x': elem.scale_x,
                    'scale_y': elem.scale_y,
                    'depth': elem.depth,
                    'style': elem.style,
                    'target_size': getattr(elem, 'target_size', 20.0),
                }
                for elem in self.svg_elements
            ],
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'NameplateConfig':
        """Create config from dictionary."""
        config = cls()
        
        if 'name' in data:
            config.name = data['name']
        
        if 'plate' in data:
            p = data['plate']
            config.plate.shape = PlateShape(p.get('shape', 'rounded_rectangle'))
            config.plate.width = p.get('width', 100.0)
            config.plate.height = p.get('height', 30.0)
            config.plate.thickness = p.get('thickness', 3.0)
            config.plate.corner_radius = p.get('corner_radius', 5.0)
            config.plate.auto_width = p.get('auto_width', False)
            config.plate.auto_height = p.get('auto_height', False)
            config.plate.padding_top = p.get('padding_top', 5.0)
            config.plate.padding_bottom = p.get('padding_bottom', 5.0)
            config.plate.padding_left = p.get('padding_left', 10.0)
            config.plate.padding_right = p.get('padding_right', 10.0)
        
        if 'sweeping' in data:
            s = data['sweeping']
            config.sweeping.width = s.get('width', 100.0)
            config.sweeping.height = s.get('height', 30.0)
            config.sweeping.thickness = s.get('thickness', 3.0)
            config.sweeping.curve_angle = s.get('curve_angle', 45.0)
            config.sweeping.curve_radius = s.get('curve_radius', 80.0)
            config.sweeping.base_type = s.get('base_type', 'pedestal')
        
        if 'text' in data:
            t = data['text']
            config.text.lines = []
            for line_data in t.get('lines', []):
                line = TextLineConfig(
                    content=line_data.get('content', ''),
                    font_family=line_data.get('font_family', 'Arial'),
                    font_style=line_data.get('font_style', 'Regular'),
                    font_size=line_data.get('font_size', 12.0),
                )
                config.text.lines.append(line)
            config.text.style = TextStyle(t.get('style', 'raised'))
            config.text.depth = t.get('depth', 2.0)
            config.text.line_spacing = t.get('line_spacing', 1.2)
        
        if 'border' in data:
            b = data['border']
            config.border.enabled = b.get('enabled', False)
            config.border.style = BorderStyle(b.get('style', 'raised'))
            config.border.width = b.get('width', 3.0)
            config.border.height = b.get('height', 1.5)
        
        if 'mount' in data:
            m = data['mount']
            config.mount.mount_type = MountType(m.get('type', 'none'))
            config.mount.stand_angle = m.get('stand_angle', 25.0)
        
        if 'icons' in data:
            config.icons = data['icons']

        if 'svg_elements' in data:
            config.svg_elements = []
            for elem_data in data['svg_elements']:
                elem = SVGElement(
                    name=elem_data.get('name', 'SVG Element'),
                    paths=elem_data.get('paths', []),
                    viewbox=tuple(elem_data.get('viewbox', (0, 0, 100, 100))),
                    width=elem_data.get('width', 0),
                    height=elem_data.get('height', 0),
                    position_x=elem_data.get('position_x', 0),
                    position_y=elem_data.get('position_y', 0),
                    rotation=elem_data.get('rotation', 0),
                    scale_x=elem_data.get('scale_x', 1.0),
                    scale_y=elem_data.get('scale_y', 1.0),
                    depth=elem_data.get('depth', 2.0),
                    style=elem_data.get('style', 'raised'),
                )
                elem.target_size = elem_data.get('target_size', 20.0)
                config.svg_elements.append(elem)

        return config


class NameplateBuilder:
    """
    Main builder class that creates complete nameplate geometry.
    """
    
    def __init__(self, config: Optional[NameplateConfig] = None):
        self.config = config or NameplateConfig()
        
        # Component generators
        self._plate_gen = BasePlateGenerator()
        self._sweeping_gen = SweepingPlateGenerator()
        self._text_gen = TextBuilder()
        self._border_gen = BorderGenerator()
        self._mount_gen = MountGenerator()
        self._svg_importer = SVGImporter()
        self._exporter = Exporter()
        
        # Generated geometry cache
        self._base_geometry: Optional[cq.Workplane] = None
        self._text_geometry: Optional[cq.Workplane] = None
        self._combined_geometry: Optional[cq.Workplane] = None
        self._needs_rebuild = True
    
    def set_config(self, config: NameplateConfig) -> None:
        """Set the configuration and mark for rebuild."""
        self.config = config
        self._needs_rebuild = True
    
    def build(self, config: Optional[NameplateConfig] = None) -> cq.Workplane:
        """
        Build the complete nameplate geometry.
        
        Args:
            config: Optional config override
            
        Returns:
            CadQuery Workplane with the complete nameplate.
        """
        cfg = config or self.config

        # Generate text first (needed for auto-sizing and text-only mode)
        self._text_geometry, text_bbox = self._text_gen.generate(cfg.text)

        # Handle "none" plate shape (text only)
        if cfg.plate.shape == PlateShape.NONE:
            # Just return the text geometry
            if self._text_geometry is not None:
                self._combined_geometry = self._text_geometry
            else:
                # Empty workplane if no text
                self._combined_geometry = cq.Workplane("XY")
            self._base_geometry = None
            self._needs_rebuild = False
            return self._combined_geometry

        # Generate base plate
        if cfg.plate.shape == PlateShape.SWEEPING:
            self._base_geometry = self._sweeping_gen.generate(cfg.sweeping)
            plate_width = cfg.sweeping.width
            plate_height = cfg.sweeping.height
            plate_thickness = cfg.sweeping.thickness
        else:
            self._base_geometry = self._plate_gen.generate(cfg.plate)
            plate_width = cfg.plate.width
            plate_height = cfg.plate.height
            plate_thickness = cfg.plate.thickness
        
        # Handle auto-sizing
        if cfg.plate.auto_width or cfg.plate.auto_height:
            new_width, new_height = self._plate_gen.calculate_auto_size(
                text_bbox, cfg.plate
            )
            if cfg.plate.auto_width:
                cfg.plate.width = new_width
                plate_width = new_width
            if cfg.plate.auto_height:
                cfg.plate.height = new_height
                plate_height = new_height
            
            # Regenerate base with new size
            if cfg.plate.shape != PlateShape.SWEEPING:
                self._base_geometry = self._plate_gen.generate(cfg.plate)
        
        # Generate border
        border_geometry = self._border_gen.generate(
            plate_width, plate_height, plate_thickness, cfg.border
        )
        
        # Generate mounting features
        mount_add, mount_subtract = self._mount_gen.generate(
            plate_width, plate_height, plate_thickness, cfg.mount
        )
        
        # Combine everything
        result = self._base_geometry
        
        # Add border
        if border_geometry is not None:
            if cfg.border.style == BorderStyle.INSET:
                result = result.cut(border_geometry)
            else:
                result = result.union(border_geometry)
        
        # Handle text based on style
        if self._text_geometry is not None:
            # For sweeping plates, position text at the center of the curved surface
            if cfg.plate.shape == PlateShape.SWEEPING:
                import math
                # The center of the sweeping plate is at Y=0, Z=thickness
                # But the curve means text should be positioned slightly differently
                text_z = plate_thickness
                text_y = 0
            else:
                text_z = plate_thickness
                text_y = 0

            if cfg.text.style == TextStyle.RAISED:
                # Position text on plate surface and union
                text_positioned = self._text_geometry.translate((0, text_y, text_z))
                result = result.union(text_positioned)
            elif cfg.text.style == TextStyle.ENGRAVED:
                # Engrave into top of plate - need text geometry that cuts down from top
                # Regenerate text with appropriate depth for engraving
                from .geometry.text_builder import TextBuilder
                engrave_cfg = cfg.text
                engrave_text, _ = TextBuilder().generate(engrave_cfg)
                if engrave_text is not None:
                    # Position so text cuts down from top surface
                    text_engraved = engrave_text.translate((0, 0, plate_thickness - cfg.text.depth))
                    result = result.cut(text_engraved)
                # Clear text geometry - it's now part of the combined geometry (cut into plate)
                self._text_geometry = None
            elif cfg.text.style == TextStyle.CUTOUT:
                # Cut completely through plate - need text as tall as plate thickness
                from .geometry.text_builder import TextBuilder, TextConfig
                cutout_cfg = TextConfig()
                cutout_cfg.lines = cfg.text.lines
                cutout_cfg.halign = cfg.text.halign
                cutout_cfg.valign = cfg.text.valign
                cutout_cfg.line_spacing = cfg.text.line_spacing
                cutout_cfg.orientation = cfg.text.orientation
                cutout_cfg.depth = plate_thickness + 1  # Extra to ensure clean cut
                cutout_text, _ = TextBuilder().generate(cutout_cfg)
                if cutout_text is not None:
                    # Position to cut through entire plate
                    text_cutout = cutout_text.translate((0, 0, -0.5))
                    result = result.cut(text_cutout)
                # Clear text geometry - it's now part of the combined geometry (cut through plate)
                self._text_geometry = None
        
        # Add mount features
        if mount_add is not None:
            result = result.union(mount_add)
        if mount_subtract is not None:
            result = result.cut(mount_subtract)

        # Add SVG elements
        for svg_elem in cfg.svg_elements:
            svg_geometry = self._svg_importer.create_geometry(
                svg_elem,
                target_size=getattr(svg_elem, 'target_size', 20.0)
            )
            if svg_geometry is not None:
                # Apply position
                svg_positioned = svg_geometry.translate((
                    svg_elem.position_x,
                    svg_elem.position_y,
                    0
                ))

                # Apply rotation
                if svg_elem.rotation != 0:
                    svg_positioned = svg_positioned.rotate(
                        (0, 0, 0), (0, 0, 1), svg_elem.rotation
                    )

                # Handle style (raised/engraved/cutout)
                if svg_elem.style == "raised":
                    svg_final = svg_positioned.translate((0, 0, plate_thickness))
                    result = result.union(svg_final)
                elif svg_elem.style == "engraved":
                    svg_final = svg_positioned.translate((0, 0, plate_thickness - svg_elem.depth))
                    result = result.cut(svg_final)
                elif svg_elem.style == "cutout":
                    # Extend through the plate
                    svg_cutout = self._svg_importer.create_geometry(
                        svg_elem,
                        target_size=getattr(svg_elem, 'target_size', 20.0),
                        depth=plate_thickness + 1
                    )
                    if svg_cutout is not None:
                        svg_cutout = svg_cutout.translate((
                            svg_elem.position_x,
                            svg_elem.position_y,
                            -0.5
                        ))
                        if svg_elem.rotation != 0:
                            svg_cutout = svg_cutout.rotate(
                                (0, 0, 0), (0, 0, 1), svg_elem.rotation
                            )
                        result = result.cut(svg_cutout)

        self._combined_geometry = result
        self._needs_rebuild = False

        return result
    
    def get_geometry(self) -> Optional[cq.Workplane]:
        """Get the current combined geometry, building if necessary."""
        if self._needs_rebuild or self._combined_geometry is None:
            return self.build()
        return self._combined_geometry
    
    def get_base_geometry(self) -> Optional[cq.Workplane]:
        """Get just the base plate geometry."""
        if self._needs_rebuild:
            self.build()
        return self._base_geometry
    
    def get_text_geometry(self) -> Optional[cq.Workplane]:
        """Get just the text geometry."""
        if self._needs_rebuild:
            self.build()
        return self._text_geometry
    
    def export(self, filepath: str, options: Optional[ExportOptions] = None) -> bool:
        """
        Export the nameplate to file.
        
        Args:
            filepath: Output file path
            options: Optional export options
            
        Returns:
            True if export succeeded.
        """
        geometry = self.get_geometry()
        if geometry is None:
            return False
        
        return self._exporter.export(geometry, filepath, options)
    
    def export_separate(self, filepath: str, 
                        options: Optional[ExportOptions] = None) -> bool:
        """
        Export base and text as separate files.
        
        Args:
            filepath: Base output file path
            options: Optional export options
            
        Returns:
            True if both exports succeeded.
        """
        if self._needs_rebuild:
            self.build()
        
        if self._base_geometry is None or self._text_geometry is None:
            return False
        
        return self._exporter.export_parts(
            self._base_geometry,
            self._text_geometry,
            filepath,
            options
        )
    
    def invalidate(self) -> None:
        """Mark the geometry cache as invalid, forcing rebuild."""
        self._needs_rebuild = True
        self._combined_geometry = None


def create_default_nameplate() -> NameplateBuilder:
    """Create a nameplate builder with sensible defaults."""
    config = NameplateConfig()
    config.plate.shape = PlateShape.ROUNDED_RECTANGLE
    config.plate.width = 120.0
    config.plate.height = 35.0
    config.plate.thickness = 4.0
    config.plate.corner_radius = 5.0
    
    config.text.lines = [TextLineConfig(content="Your Name", font_size=14.0)]
    config.text.style = TextStyle.RAISED
    config.text.depth = 2.0
    
    return NameplateBuilder(config)
