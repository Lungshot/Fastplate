"""
Sweeping Plate Generator
Creates curved/sweeping base plates for nameplates.
"""

import cadquery as cq
import math
from dataclasses import dataclass
from typing import Optional, Tuple, List


@dataclass
class SweepingConfig:
    """Configuration for sweeping/curved plates."""
    width: float = 100.0          # mm - plate width
    height: float = 30.0          # mm - plate height  
    thickness: float = 3.0        # mm - plate thickness
    
    # Curve parameters
    curve_angle: float = 45.0     # degrees - total sweep angle
    curve_radius: float = 80.0    # mm - radius of curvature
    eccentricity: float = 0.0     # -1 to 1 - shifts curve center
    
    # Base type
    base_type: str = "pedestal"   # pedestal, flat, minimal
    
    # Corner options
    corner_radius: float = 3.0    # mm - rounded corners
    
    # Pedestal options
    pedestal_height: float = 5.0  # mm - height of pedestal base
    pedestal_width: float = 20.0  # mm - width of pedestal

    def to_dict(self) -> dict:
        """Serialize SweepingConfig to a dictionary."""
        return {
            'width': self.width,
            'height': self.height,
            'thickness': self.thickness,
            'curve_angle': self.curve_angle,
            'curve_radius': self.curve_radius,
            'eccentricity': self.eccentricity,
            'base_type': self.base_type,
            'corner_radius': self.corner_radius,
            'pedestal_height': self.pedestal_height,
            'pedestal_width': self.pedestal_width,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SweepingConfig':
        """Deserialize SweepingConfig from a dictionary."""
        return cls(
            width=data.get('width', 100.0),
            height=data.get('height', 30.0),
            thickness=data.get('thickness', 3.0),
            curve_angle=data.get('curve_angle', 45.0),
            curve_radius=data.get('curve_radius', 80.0),
            eccentricity=data.get('eccentricity', 0.0),
            base_type=data.get('base_type', 'pedestal'),
            corner_radius=data.get('corner_radius', 3.0),
            pedestal_height=data.get('pedestal_height', 5.0),
            pedestal_width=data.get('pedestal_width', 20.0),
        )


class SweepingPlateGenerator:
    """
    Generates curved/sweeping nameplate geometry.
    Creates plates that curve in an arc, similar to popular desk nameplates.
    """
    
    def __init__(self, config: Optional[SweepingConfig] = None):
        self.config = config or SweepingConfig()
    
    def generate(self, config: Optional[SweepingConfig] = None) -> cq.Workplane:
        """
        Generate a sweeping curved plate.
        
        Args:
            config: Optional config override
            
        Returns:
            CadQuery Workplane with the curved plate.
        """
        cfg = config or self.config
        
        if cfg.curve_angle <= 0:
            # No curve, return flat plate
            return self._make_flat_plate(cfg)
        
        # Generate the curved plate
        curved_plate = self._make_curved_plate(cfg)
        
        # Add base/pedestal if needed
        if cfg.base_type == "pedestal":
            base = self._make_pedestal_base(cfg)
            curved_plate = curved_plate.union(base)
        elif cfg.base_type == "minimal":
            base = self._make_minimal_base(cfg)
            curved_plate = curved_plate.union(base)
        
        return curved_plate
    
    def _make_flat_plate(self, cfg: SweepingConfig) -> cq.Workplane:
        """Create a flat (non-curved) plate."""
        plate = (
            cq.Workplane("XY")
            .box(cfg.width, cfg.height, cfg.thickness)
            .translate((0, 0, cfg.thickness / 2))
        )
        
        if cfg.corner_radius > 0:
            try:
                plate = plate.edges("|Z").fillet(cfg.corner_radius)
            except:
                pass
        
        return plate
    
    def _make_curved_plate(self, cfg: SweepingConfig) -> cq.Workplane:
        """Create the main curved plate using sweep along an arc."""
        angle_rad = math.radians(cfg.curve_angle)
        
        # Create the cross-section profile (rectangle)
        profile = (
            cq.Workplane("XZ")
            .rect(cfg.width, cfg.thickness)
        )
        
        # Create the sweep path - an arc
        # Arc center is below the plate
        arc_center_y = -cfg.curve_radius
        
        # Adjust for eccentricity
        eccentricity_offset = cfg.eccentricity * cfg.curve_radius * 0.5
        
        # Calculate arc points
        start_angle = math.pi/2 - angle_rad/2
        end_angle = math.pi/2 + angle_rad/2
        
        # Create arc path using three points
        arc_start = (
            0,
            cfg.curve_radius * math.sin(start_angle) + arc_center_y,
            cfg.curve_radius * math.cos(start_angle) + eccentricity_offset
        )
        arc_mid = (
            0,
            cfg.curve_radius + arc_center_y,
            eccentricity_offset
        )
        arc_end = (
            0,
            cfg.curve_radius * math.sin(end_angle) + arc_center_y,
            cfg.curve_radius * math.cos(end_angle) + eccentricity_offset
        )
        
        # Create the curved plate by extruding along the curve
        # Using a different approach: create the curve as a lofted solid
        
        # Alternative: create by revolving a profile
        # This creates a section of a cylinder
        try:
            # Method 1: Use a series of sections to approximate the curve
            curved_plate = self._create_curved_surface_loft(cfg)
        except:
            # Fallback: simple bent plate approximation
            curved_plate = self._create_curved_surface_segments(cfg)
        
        return curved_plate
    
    def _create_curved_surface_loft(self, cfg: SweepingConfig) -> cq.Workplane:
        """Create curved surface using revolution of a cross-section profile."""
        angle_rad = math.radians(cfg.curve_angle)

        # Create a cross-section profile (rectangular with optional rounded corners)
        # The profile is in the XZ plane, and we'll revolve around an axis parallel to X
        half_height = cfg.height / 2

        # Create the profile shape
        profile = (
            cq.Workplane("XZ")
            .moveTo(-cfg.width/2, 0)
            .lineTo(-cfg.width/2, cfg.thickness)
            .lineTo(cfg.width/2, cfg.thickness)
            .lineTo(cfg.width/2, 0)
            .close()
        )

        # Use sweep along an arc path for more control
        # Create path as an arc in the YZ plane
        num_segments = max(16, int(cfg.curve_angle / 3))
        segment_angle = angle_rad / num_segments
        segment_arc_length = cfg.curve_radius * segment_angle

        result = None

        for i in range(num_segments):
            current_angle = -angle_rad/2 + (i + 0.5) * segment_angle

            # Position on the arc
            y_pos = cfg.curve_radius * math.sin(current_angle)
            z_pos = cfg.curve_radius * (1 - math.cos(current_angle))

            # Create segment - a flat box that follows the curve
            segment = (
                cq.Workplane("XY")
                .box(cfg.width, segment_arc_length * 1.05, cfg.thickness)
            )

            # Rotate to follow curve tangent (rotate around X axis)
            segment = segment.rotate((0,0,0), (1,0,0), math.degrees(current_angle))

            # Position on curve
            segment = segment.translate((0, y_pos, z_pos + cfg.thickness/2))

            if result is None:
                result = segment
            else:
                try:
                    result = result.union(segment)
                except:
                    pass

        # Apply corner radius to the side edges if possible
        if cfg.corner_radius > 0 and result is not None:
            try:
                # Fillet the vertical edges
                result = result.edges("|X").fillet(min(cfg.corner_radius, cfg.thickness * 0.4))
            except:
                pass

        return result if result else cq.Workplane("XY")
    
    def _create_curved_surface_segments(self, cfg: SweepingConfig) -> cq.Workplane:
        """Fallback: create curved surface using discrete segments."""
        angle_rad = math.radians(cfg.curve_angle)
        num_segments = max(12, int(cfg.curve_angle / 3))
        
        result = None
        segment_angle = angle_rad / num_segments
        segment_arc_length = cfg.curve_radius * segment_angle
        
        for i in range(num_segments):
            current_angle = -angle_rad/2 + (i + 0.5) * segment_angle
            
            # Position on the arc
            y_pos = cfg.curve_radius * math.sin(current_angle)
            z_pos = cfg.curve_radius * (1 - math.cos(current_angle))
            
            # Create segment box
            segment = (
                cq.Workplane("XY")
                .box(cfg.width, segment_arc_length, cfg.thickness)
            )
            
            # Rotate to follow curve tangent
            segment = segment.rotate((0,0,0), (1,0,0), math.degrees(current_angle))
            
            # Position on curve
            segment = segment.translate((0, y_pos, z_pos))
            
            if result is None:
                result = segment
            else:
                try:
                    result = result.union(segment)
                except:
                    pass
        
        return result if result else cq.Workplane("XY")
    
    def _make_pedestal_base(self, cfg: SweepingConfig) -> cq.Workplane:
        """Create a pedestal base for the curved plate to sit on."""
        angle_rad = math.radians(cfg.curve_angle)
        
        # Calculate where the plate ends touch down
        end_y = cfg.curve_radius * math.sin(angle_rad/2)
        end_z = cfg.curve_radius * (1 - math.cos(angle_rad/2))
        
        # Create pedestal that supports the front edge
        pedestal_depth = end_y + cfg.pedestal_width
        
        pedestal = (
            cq.Workplane("XY")
            .box(cfg.width * 0.9, pedestal_depth, cfg.pedestal_height)
            .translate((0, -pedestal_depth/2 + end_y, cfg.pedestal_height/2 - end_z))
        )
        
        # Round the front edge
        try:
            pedestal = pedestal.edges(">Y").fillet(cfg.pedestal_height * 0.3)
        except:
            pass
        
        return pedestal
    
    def _make_minimal_base(self, cfg: SweepingConfig) -> cq.Workplane:
        """Create minimal support feet."""
        angle_rad = math.radians(cfg.curve_angle)
        
        end_y = cfg.curve_radius * math.sin(angle_rad/2)
        end_z = cfg.curve_radius * (1 - math.cos(angle_rad/2))
        
        foot_size = 10.0
        foot_height = end_z + cfg.thickness/2
        
        # Create two feet at the front
        left_foot = (
            cq.Workplane("XY")
            .box(foot_size, foot_size, foot_height)
            .translate((-cfg.width/3, end_y - foot_size/2, foot_height/2 - end_z))
        )
        
        right_foot = (
            cq.Workplane("XY")
            .box(foot_size, foot_size, foot_height)
            .translate((cfg.width/3, end_y - foot_size/2, foot_height/2 - end_z))
        )
        
        return left_foot.union(right_foot)
    
    def get_text_surface_center(self, config: Optional[SweepingConfig] = None) -> Tuple[float, float, float]:
        """
        Get the center point of the curved surface for text placement.
        
        Returns:
            (x, y, z) coordinates of the surface center.
        """
        cfg = config or self.config
        
        # At angle = 0, the surface center is at the top of the curve
        z = cfg.curve_radius - cfg.curve_radius + cfg.thickness/2
        
        return (0, 0, z + cfg.thickness)
    
    def get_text_surface_normal(self, config: Optional[SweepingConfig] = None) -> Tuple[float, float, float]:
        """
        Get the normal vector at the center of the curved surface.
        
        Returns:
            (nx, ny, nz) normal vector.
        """
        # At center (angle=0), normal points straight up in Z
        return (0, 0, 1)
