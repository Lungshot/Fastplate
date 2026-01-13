"""
Border Generator
Creates border/frame geometry for nameplates.
"""

import cadquery as cq
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple


class BorderStyle(Enum):
    """Available border styles."""
    NONE = "none"
    RAISED = "raised"       # Border protrudes above base
    INSET = "inset"         # Border is recessed into base
    DOUBLE = "double"       # Double-line border
    GROOVE = "groove"       # V-groove border


@dataclass
class BorderConfig:
    """Configuration for border generation."""
    enabled: bool = False
    style: BorderStyle = BorderStyle.RAISED
    width: float = 3.0           # mm - border thickness
    height: float = 1.5          # mm - how much it protrudes/recesses
    offset: float = 2.0          # mm - distance from plate edge
    corner_style: str = "rounded"  # rounded, square, chamfered
    corner_radius: float = 3.0   # mm - for rounded corners
    
    # For double border
    double_gap: float = 2.0      # mm - gap between lines
    double_inner_width: float = 1.5  # mm - inner line width


class BorderGenerator:
    """
    Generates border/frame geometry for nameplates.
    """
    
    def __init__(self, config: Optional[BorderConfig] = None):
        self.config = config or BorderConfig()
    
    def generate(self, plate_width: float, plate_height: float, 
                 plate_thickness: float,
                 config: Optional[BorderConfig] = None) -> Optional[cq.Workplane]:
        """
        Generate border geometry.
        
        Args:
            plate_width: Width of the base plate
            plate_height: Height of the base plate
            plate_thickness: Thickness of the base plate
            config: Optional config override
            
        Returns:
            CadQuery Workplane with border geometry, or None if disabled.
        """
        cfg = config or self.config
        
        if not cfg.enabled or cfg.style == BorderStyle.NONE:
            return None
        
        if cfg.style == BorderStyle.RAISED:
            return self._make_raised_border(plate_width, plate_height, plate_thickness, cfg)
        elif cfg.style == BorderStyle.INSET:
            return self._make_inset_border(plate_width, plate_height, plate_thickness, cfg)
        elif cfg.style == BorderStyle.DOUBLE:
            return self._make_double_border(plate_width, plate_height, plate_thickness, cfg)
        elif cfg.style == BorderStyle.GROOVE:
            return self._make_groove_border(plate_width, plate_height, plate_thickness, cfg)
        
        return None
    
    def _make_raised_border(self, plate_width: float, plate_height: float,
                            plate_thickness: float, cfg: BorderConfig) -> cq.Workplane:
        """Create a raised border frame."""
        # Outer dimensions
        outer_w = plate_width - cfg.offset * 2
        outer_h = plate_height - cfg.offset * 2
        
        # Inner dimensions (cutout)
        inner_w = outer_w - cfg.width * 2
        inner_h = outer_h - cfg.width * 2
        
        # Create outer rectangle
        border = cq.Workplane("XY").rect(outer_w, outer_h)
        
        # Create inner cutout
        border = border.rect(inner_w, inner_h, forConstruction=False)
        
        # Extrude as a frame (difference between outer and inner)
        border = (
            cq.Workplane("XY")
            .rect(outer_w, outer_h)
            .extrude(cfg.height)
            .faces(">Z")
            .workplane()
            .rect(inner_w, inner_h)
            .cutThruAll()
        )
        
        # Apply corner style
        if cfg.corner_style == "rounded" and cfg.corner_radius > 0:
            try:
                border = border.edges("|Z").fillet(min(cfg.corner_radius, cfg.width * 0.9))
            except:
                pass  # Fillet may fail on complex geometry
        elif cfg.corner_style == "chamfered":
            try:
                border = border.edges("|Z").chamfer(min(cfg.corner_radius, cfg.width * 0.9))
            except:
                pass
        
        # Position on top of plate with 0.1mm overlap for reliable union with raised text
        border = border.translate((0, 0, plate_thickness - 0.1))

        return border

    def _make_inset_border(self, plate_width: float, plate_height: float,
                           plate_thickness: float, cfg: BorderConfig) -> cq.Workplane:
        """Create an inset (recessed) border groove."""
        # This returns a shape to be subtracted from the plate
        outer_w = plate_width - cfg.offset * 2
        outer_h = plate_height - cfg.offset * 2
        inner_w = outer_w - cfg.width * 2
        inner_h = outer_h - cfg.width * 2
        
        # Create groove shape
        groove = (
            cq.Workplane("XY")
            .rect(outer_w, outer_h)
            .extrude(cfg.height)
            .faces(">Z")
            .workplane()
            .rect(inner_w, inner_h)
            .cutThruAll()
        )
        
        # Position to cut into top of plate
        groove = groove.translate((0, 0, plate_thickness - cfg.height))
        
        return groove
    
    def _make_double_border(self, plate_width: float, plate_height: float,
                            plate_thickness: float, cfg: BorderConfig) -> cq.Workplane:
        """Create a double-line border."""
        # Outer border
        outer_w1 = plate_width - cfg.offset * 2
        outer_h1 = plate_height - cfg.offset * 2
        inner_w1 = outer_w1 - cfg.width * 2
        inner_h1 = outer_h1 - cfg.width * 2
        
        # Inner border
        outer_w2 = inner_w1 - cfg.double_gap * 2
        outer_h2 = inner_h1 - cfg.double_gap * 2
        inner_w2 = outer_w2 - cfg.double_inner_width * 2
        inner_h2 = outer_h2 - cfg.double_inner_width * 2
        
        # Create outer frame
        outer_frame = (
            cq.Workplane("XY")
            .rect(outer_w1, outer_h1)
            .extrude(cfg.height)
            .faces(">Z")
            .workplane()
            .rect(inner_w1, inner_h1)
            .cutThruAll()
        )
        
        # Create inner frame
        inner_frame = (
            cq.Workplane("XY")
            .rect(outer_w2, outer_h2)
            .extrude(cfg.height)
            .faces(">Z")
            .workplane()
            .rect(inner_w2, inner_h2)
            .cutThruAll()
        )
        
        # Combine frames
        combined = outer_frame.union(inner_frame)

        # Position on plate with 0.1mm overlap for reliable union with raised text
        combined = combined.translate((0, 0, plate_thickness - 0.1))

        return combined
    
    def _make_groove_border(self, plate_width: float, plate_height: float,
                            plate_thickness: float, cfg: BorderConfig) -> cq.Workplane:
        """Create a V-groove border (to be subtracted from plate)."""
        # Create a simple groove for now - V-groove would require more complex lofting
        return self._make_inset_border(plate_width, plate_height, plate_thickness, cfg)
    
    def get_inset_area(self, plate_width: float, plate_height: float,
                       config: Optional[BorderConfig] = None) -> Tuple[float, float]:
        """
        Get the usable area inside the border.
        
        Returns:
            (width, height) of the area inside the border
        """
        cfg = config or self.config
        
        if not cfg.enabled or cfg.style == BorderStyle.NONE:
            return (plate_width, plate_height)
        
        inset = cfg.offset + cfg.width
        
        if cfg.style == BorderStyle.DOUBLE:
            inset += cfg.double_gap + cfg.double_inner_width
        
        return (
            plate_width - inset * 2,
            plate_height - inset * 2
        )
