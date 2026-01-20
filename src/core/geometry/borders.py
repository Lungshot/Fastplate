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
    ROPE = "rope"           # Twisted rope pattern
    DOTS = "dots"           # Dotted border
    DASHES = "dashes"       # Dashed border
    ORNATE = "ornate"       # Decorative with corner pieces


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

    # For pattern borders (rope, dots, dashes)
    pattern_size: float = 3.0    # mm - size of pattern elements
    pattern_spacing: float = 2.0 # mm - spacing between elements

    def to_dict(self) -> dict:
        """Serialize BorderConfig to a dictionary."""
        return {
            'enabled': self.enabled,
            'style': self.style.value,
            'width': self.width,
            'height': self.height,
            'offset': self.offset,
            'corner_style': self.corner_style,
            'corner_radius': self.corner_radius,
            'double_gap': self.double_gap,
            'double_inner_width': self.double_inner_width,
            'pattern_size': self.pattern_size,
            'pattern_spacing': self.pattern_spacing,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BorderConfig':
        """Deserialize BorderConfig from a dictionary."""
        style = data.get('style', 'raised')
        if isinstance(style, str):
            style = BorderStyle(style)

        return cls(
            enabled=data.get('enabled', False),
            style=style,
            width=data.get('width', 3.0),
            height=data.get('height', 1.5),
            offset=data.get('offset', 2.0),
            corner_style=data.get('corner_style', 'rounded'),
            corner_radius=data.get('corner_radius', 3.0),
            double_gap=data.get('double_gap', 2.0),
            double_inner_width=data.get('double_inner_width', 1.5),
            pattern_size=data.get('pattern_size', 3.0),
            pattern_spacing=data.get('pattern_spacing', 2.0),
        )


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
        elif cfg.style == BorderStyle.ROPE:
            return self._make_rope_border(plate_width, plate_height, plate_thickness, cfg)
        elif cfg.style == BorderStyle.DOTS:
            return self._make_dots_border(plate_width, plate_height, plate_thickness, cfg)
        elif cfg.style == BorderStyle.DASHES:
            return self._make_dashes_border(plate_width, plate_height, plate_thickness, cfg)
        elif cfg.style == BorderStyle.ORNATE:
            return self._make_ornate_border(plate_width, plate_height, plate_thickness, cfg)

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

    def _make_rope_border(self, plate_width: float, plate_height: float,
                          plate_thickness: float, cfg: BorderConfig) -> cq.Workplane:
        """Create a twisted rope pattern border."""
        try:
            result = None
            inner_w = plate_width - cfg.offset * 2
            inner_h = plate_height - cfg.offset * 2

            rope_radius = cfg.width / 2
            spacing = cfg.pattern_spacing + cfg.pattern_size
            z_pos = plate_thickness - 0.1

            # Create rope segments along each edge
            # Top edge
            x = -inner_w / 2 + spacing / 2
            while x <= inner_w / 2 - spacing / 2:
                twist = self._create_rope_segment(rope_radius, cfg.height, cfg.pattern_size)
                if twist:
                    twist = twist.translate((x, inner_h / 2, z_pos))
                    result = twist if result is None else result.union(twist)
                x += spacing

            # Bottom edge
            x = -inner_w / 2 + spacing / 2
            while x <= inner_w / 2 - spacing / 2:
                twist = self._create_rope_segment(rope_radius, cfg.height, cfg.pattern_size)
                if twist:
                    twist = twist.translate((x, -inner_h / 2, z_pos))
                    result = result.union(twist) if result else twist
                x += spacing

            # Left edge
            y = -inner_h / 2 + spacing / 2
            while y <= inner_h / 2 - spacing / 2:
                twist = self._create_rope_segment(rope_radius, cfg.height, cfg.pattern_size)
                if twist:
                    twist = twist.rotate((0, 0, 0), (0, 0, 1), 90)
                    twist = twist.translate((-inner_w / 2, y, z_pos))
                    result = result.union(twist) if result else twist
                y += spacing

            # Right edge
            y = -inner_h / 2 + spacing / 2
            while y <= inner_h / 2 - spacing / 2:
                twist = self._create_rope_segment(rope_radius, cfg.height, cfg.pattern_size)
                if twist:
                    twist = twist.rotate((0, 0, 0), (0, 0, 1), 90)
                    twist = twist.translate((inner_w / 2, y, z_pos))
                    result = result.union(twist) if result else twist
                y += spacing

            return result
        except Exception as e:
            print(f"Error creating rope border: {e}")
            return None

    def _create_rope_segment(self, radius: float, height: float, length: float) -> Optional[cq.Workplane]:
        """Create a single rope twist segment."""
        try:
            # Simplified rope segment - two overlapping cylinders at angle
            seg1 = (
                cq.Workplane("XY")
                .cylinder(length, radius)
                .rotate((0, 0, 0), (0, 1, 0), 90)
                .rotate((0, 0, 0), (0, 0, 1), 20)
            )
            seg2 = (
                cq.Workplane("XY")
                .cylinder(length, radius)
                .rotate((0, 0, 0), (0, 1, 0), 90)
                .rotate((0, 0, 0), (0, 0, 1), -20)
            )
            return seg1.union(seg2)
        except Exception as e:
            print(f"Error creating rope segment: {e}")
            return None

    def _make_dots_border(self, plate_width: float, plate_height: float,
                          plate_thickness: float, cfg: BorderConfig) -> cq.Workplane:
        """Create a dotted border."""
        try:
            result = None
            inner_w = plate_width - cfg.offset * 2
            inner_h = plate_height - cfg.offset * 2

            dot_radius = cfg.pattern_size / 2
            spacing = cfg.pattern_size + cfg.pattern_spacing
            z_pos = plate_thickness - 0.1

            # Top edge
            x = -inner_w / 2 + spacing / 2
            while x <= inner_w / 2 - spacing / 2:
                dot = (
                    cq.Workplane("XY")
                    .circle(dot_radius)
                    .extrude(cfg.height)
                    .translate((x, inner_h / 2, z_pos))
                )
                result = dot if result is None else result.union(dot)
                x += spacing

            # Bottom edge
            x = -inner_w / 2 + spacing / 2
            while x <= inner_w / 2 - spacing / 2:
                dot = (
                    cq.Workplane("XY")
                    .circle(dot_radius)
                    .extrude(cfg.height)
                    .translate((x, -inner_h / 2, z_pos))
                )
                result = result.union(dot)
                x += spacing

            # Left edge (avoid corners)
            y = -inner_h / 2 + spacing
            while y <= inner_h / 2 - spacing:
                dot = (
                    cq.Workplane("XY")
                    .circle(dot_radius)
                    .extrude(cfg.height)
                    .translate((-inner_w / 2, y, z_pos))
                )
                result = result.union(dot)
                y += spacing

            # Right edge (avoid corners)
            y = -inner_h / 2 + spacing
            while y <= inner_h / 2 - spacing:
                dot = (
                    cq.Workplane("XY")
                    .circle(dot_radius)
                    .extrude(cfg.height)
                    .translate((inner_w / 2, y, z_pos))
                )
                result = result.union(dot)
                y += spacing

            return result
        except Exception as e:
            print(f"Error creating dots border: {e}")
            return None

    def _make_dashes_border(self, plate_width: float, plate_height: float,
                            plate_thickness: float, cfg: BorderConfig) -> cq.Workplane:
        """Create a dashed border."""
        try:
            result = None
            inner_w = plate_width - cfg.offset * 2
            inner_h = plate_height - cfg.offset * 2

            dash_length = cfg.pattern_size
            spacing = dash_length + cfg.pattern_spacing
            z_pos = plate_thickness - 0.1

            # Top edge (horizontal dashes)
            x = -inner_w / 2 + spacing / 2
            while x <= inner_w / 2 - spacing / 2:
                dash = (
                    cq.Workplane("XY")
                    .rect(dash_length, cfg.width)
                    .extrude(cfg.height)
                    .translate((x, inner_h / 2, z_pos))
                )
                result = dash if result is None else result.union(dash)
                x += spacing

            # Bottom edge
            x = -inner_w / 2 + spacing / 2
            while x <= inner_w / 2 - spacing / 2:
                dash = (
                    cq.Workplane("XY")
                    .rect(dash_length, cfg.width)
                    .extrude(cfg.height)
                    .translate((x, -inner_h / 2, z_pos))
                )
                result = result.union(dash)
                x += spacing

            # Left edge (vertical dashes)
            y = -inner_h / 2 + spacing / 2
            while y <= inner_h / 2 - spacing / 2:
                dash = (
                    cq.Workplane("XY")
                    .rect(cfg.width, dash_length)
                    .extrude(cfg.height)
                    .translate((-inner_w / 2, y, z_pos))
                )
                result = result.union(dash)
                y += spacing

            # Right edge
            y = -inner_h / 2 + spacing / 2
            while y <= inner_h / 2 - spacing / 2:
                dash = (
                    cq.Workplane("XY")
                    .rect(cfg.width, dash_length)
                    .extrude(cfg.height)
                    .translate((inner_w / 2, y, z_pos))
                )
                result = result.union(dash)
                y += spacing

            return result
        except Exception as e:
            print(f"Error creating dashes border: {e}")
            return None

    def _make_ornate_border(self, plate_width: float, plate_height: float,
                            plate_thickness: float, cfg: BorderConfig) -> cq.Workplane:
        """Create an ornate border with decorative corner pieces."""
        try:
            # Start with simple raised border
            border = self._make_raised_border(plate_width, plate_height, plate_thickness, cfg)
            if not border:
                return None

            # Add corner ornaments
            inner_w = plate_width - cfg.offset * 2
            inner_h = plate_height - cfg.offset * 2
            ornament_size = cfg.pattern_size * 2
            z_pos = plate_thickness - 0.1

            corners = [
                (-inner_w / 2, inner_h / 2, 0),      # Top-left
                (inner_w / 2, inner_h / 2, 90),     # Top-right
                (inner_w / 2, -inner_h / 2, 180),   # Bottom-right
                (-inner_w / 2, -inner_h / 2, 270),  # Bottom-left
            ]

            for x, y, angle in corners:
                ornament = self._create_corner_ornament(ornament_size, cfg.height)
                if ornament:
                    ornament = ornament.rotate((0, 0, 0), (0, 0, 1), angle)
                    ornament = ornament.translate((x, y, z_pos))
                    border = border.union(ornament)

            return border
        except Exception as e:
            print(f"Error creating ornate border: {e}")
            return None

    def _create_corner_ornament(self, size: float, height: float) -> Optional[cq.Workplane]:
        """Create a decorative corner ornament."""
        try:
            # Simple fleur-de-lis style ornament
            diamond = (
                cq.Workplane("XY")
                .polygon(4, size * 0.7)
                .extrude(height)
                .rotate((0, 0, 0), (0, 0, 1), 45)
            )
            circle1 = (
                cq.Workplane("XY")
                .circle(size * 0.2)
                .extrude(height)
                .translate((size * 0.3, size * 0.3, 0))
            )
            return diamond.union(circle1)
        except Exception as e:
            print(f"Error creating corner ornament: {e}")
            return None

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
