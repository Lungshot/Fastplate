"""
Base Plate Generators
Creates various base plate shapes for nameplates.
"""

import cadquery as cq
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Tuple


class PlateShape(Enum):
    """Available base plate shapes."""
    NONE = "none"  # Text only, no base plate
    RECTANGLE = "rectangle"
    ROUNDED_RECTANGLE = "rounded_rectangle"
    OVAL = "oval"
    CHAMFERED = "chamfered"
    HEXAGON = "hexagon"
    OCTAGON = "octagon"
    SWEEPING = "sweeping"  # Handled by SweepingPlateGenerator


@dataclass
class PlateConfig:
    """Configuration for base plate generation."""
    shape: PlateShape = PlateShape.ROUNDED_RECTANGLE
    width: float = 100.0          # mm
    height: float = 30.0          # mm
    thickness: float = 3.0        # mm
    corner_radius: float = 5.0    # mm (for rounded shapes)
    chamfer_size: float = 3.0     # mm (for chamfered shape)
    
    # Auto-sizing options
    auto_width: bool = False
    auto_height: bool = False
    
    # Padding (when auto-sizing)
    padding_top: float = 5.0
    padding_bottom: float = 5.0
    padding_left: float = 10.0
    padding_right: float = 10.0
    
    def get_total_padding(self) -> Tuple[float, float]:
        """Get total horizontal and vertical padding."""
        return (
            self.padding_left + self.padding_right,
            self.padding_top + self.padding_bottom
        )


class BasePlateGenerator:
    """
    Generates base plate geometry for nameplates.
    """
    
    def __init__(self, config: Optional[PlateConfig] = None):
        self.config = config or PlateConfig()
    
    def generate(self, config: Optional[PlateConfig] = None) -> cq.Workplane:
        """
        Generate a base plate according to configuration.
        
        Args:
            config: Optional config override
            
        Returns:
            CadQuery Workplane with the base plate solid.
        """
        cfg = config or self.config
        
        if cfg.shape == PlateShape.RECTANGLE:
            return self._make_rectangle(cfg)
        elif cfg.shape == PlateShape.ROUNDED_RECTANGLE:
            return self._make_rounded_rectangle(cfg)
        elif cfg.shape == PlateShape.OVAL:
            return self._make_oval(cfg)
        elif cfg.shape == PlateShape.CHAMFERED:
            return self._make_chamfered(cfg)
        elif cfg.shape == PlateShape.HEXAGON:
            return self._make_hexagon(cfg)
        elif cfg.shape == PlateShape.OCTAGON:
            return self._make_octagon(cfg)
        else:
            # Default to rounded rectangle
            return self._make_rounded_rectangle(cfg)
    
    def _make_rectangle(self, cfg: PlateConfig) -> cq.Workplane:
        """Create a simple rectangular plate."""
        return (
            cq.Workplane("XY")
            .box(cfg.width, cfg.height, cfg.thickness)
            .translate((0, 0, cfg.thickness / 2))
        )
    
    def _make_rounded_rectangle(self, cfg: PlateConfig) -> cq.Workplane:
        """Create a rectangle with rounded corners."""
        # Ensure corner radius isn't larger than half the smallest dimension
        max_radius = min(cfg.width, cfg.height) / 2 - 0.1
        radius = min(cfg.corner_radius, max_radius)
        
        if radius <= 0:
            return self._make_rectangle(cfg)
        
        return (
            cq.Workplane("XY")
            .box(cfg.width, cfg.height, cfg.thickness)
            .translate((0, 0, cfg.thickness / 2))
            .edges("|Z")
            .fillet(radius)
        )
    
    def _make_oval(self, cfg: PlateConfig) -> cq.Workplane:
        """Create an oval/ellipse plate."""
        return (
            cq.Workplane("XY")
            .ellipse(cfg.width / 2, cfg.height / 2)
            .extrude(cfg.thickness)
        )
    
    def _make_chamfered(self, cfg: PlateConfig) -> cq.Workplane:
        """Create a rectangle with chamfered corners."""
        # Ensure chamfer isn't too large
        max_chamfer = min(cfg.width, cfg.height) / 2 - 0.1
        chamfer = min(cfg.chamfer_size, max_chamfer)
        
        if chamfer <= 0:
            return self._make_rectangle(cfg)
        
        return (
            cq.Workplane("XY")
            .box(cfg.width, cfg.height, cfg.thickness)
            .translate((0, 0, cfg.thickness / 2))
            .edges("|Z")
            .chamfer(chamfer)
        )
    
    def _make_hexagon(self, cfg: PlateConfig) -> cq.Workplane:
        """Create a hexagonal plate."""
        # Use the smaller dimension to fit the hexagon
        size = min(cfg.width, cfg.height) / 2
        
        return (
            cq.Workplane("XY")
            .polygon(6, size * 2)
            .extrude(cfg.thickness)
        )
    
    def _make_octagon(self, cfg: PlateConfig) -> cq.Workplane:
        """Create an octagonal plate."""
        size = min(cfg.width, cfg.height) / 2
        
        return (
            cq.Workplane("XY")
            .polygon(8, size * 2)
            .extrude(cfg.thickness)
        )
    
    def calculate_auto_size(self, text_bbox: Tuple[float, float, float, float],
                           config: Optional[PlateConfig] = None) -> Tuple[float, float]:
        """
        Calculate automatic plate dimensions based on text bounding box.
        
        Args:
            text_bbox: (min_x, min_y, max_x, max_y) of text
            config: Optional config override
            
        Returns:
            (width, height) for the plate
        """
        cfg = config or self.config
        
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        width = cfg.width
        height = cfg.height
        
        if cfg.auto_width:
            width = text_width + cfg.padding_left + cfg.padding_right
        
        if cfg.auto_height:
            height = text_height + cfg.padding_top + cfg.padding_bottom
        
        return (width, height)
