"""
Divider Line Generator
Creates horizontal divider lines between text lines on nameplates.
"""

import cadquery as cq
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class DividerStyle(Enum):
    """Available divider line styles."""
    NONE = "none"
    SOLID = "solid"           # Simple solid line
    DOUBLE = "double"         # Two parallel lines
    DASHED = "dashed"         # Dashed line
    DOTTED = "dotted"         # Dotted line
    ORNAMENTAL = "ornamental" # Line with center ornament


@dataclass
class DividerConfig:
    """Configuration for divider lines."""
    enabled: bool = False
    style: DividerStyle = DividerStyle.SOLID
    width_percent: float = 80.0   # Percentage of plate width
    thickness: float = 1.0        # mm - line thickness
    height: float = 0.5           # mm - height (raised) or depth (engraved)
    is_raised: bool = True        # True = raised, False = engraved
    # Pattern options
    dash_length: float = 4.0      # mm - for dashed style
    dash_gap: float = 2.0         # mm - gap between dashes
    dot_diameter: float = 1.5     # mm - for dotted style
    dot_spacing: float = 3.0      # mm - spacing between dots
    # Double line options
    double_gap: float = 2.0       # mm - gap between double lines


class DividerGenerator:
    """Generates divider line geometry."""

    def generate(self, config: DividerConfig, plate_width: float,
                 y_position: float, plate_thickness: float) -> Optional[cq.Workplane]:
        """
        Generate a divider line at the specified Y position.

        Args:
            config: Divider configuration
            plate_width: Width of the plate
            y_position: Y position for the divider (center of line)
            plate_thickness: Thickness of the plate (for Z positioning)

        Returns:
            CadQuery Workplane with divider geometry
        """
        if not config.enabled or config.style == DividerStyle.NONE:
            return None

        line_width = plate_width * (config.width_percent / 100.0)
        z_pos = plate_thickness if config.is_raised else plate_thickness - config.height

        generators = {
            DividerStyle.SOLID: self._make_solid_line,
            DividerStyle.DOUBLE: self._make_double_line,
            DividerStyle.DASHED: self._make_dashed_line,
            DividerStyle.DOTTED: self._make_dotted_line,
            DividerStyle.ORNAMENTAL: self._make_ornamental_line,
        }

        generator = generators.get(config.style)
        if generator:
            return generator(config, line_width, y_position, z_pos)

        return None

    def generate_between_lines(self, config: DividerConfig, plate_width: float,
                               line_y_positions: List[float], plate_thickness: float) -> Optional[cq.Workplane]:
        """
        Generate divider lines between all text line positions.

        Args:
            config: Divider configuration
            plate_width: Width of the plate
            line_y_positions: Y positions of text lines (sorted top to bottom)
            plate_thickness: Thickness of the plate

        Returns:
            CadQuery Workplane with all divider geometry combined
        """
        if not config.enabled or len(line_y_positions) < 2:
            return None

        result = None

        # Create dividers between adjacent lines
        for i in range(len(line_y_positions) - 1):
            y1 = line_y_positions[i]
            y2 = line_y_positions[i + 1]
            divider_y = (y1 + y2) / 2  # Midpoint between lines

            divider = self.generate(config, plate_width, divider_y, plate_thickness)
            if divider:
                if result is None:
                    result = divider
                else:
                    result = result.union(divider)

        return result

    def _make_solid_line(self, config: DividerConfig, width: float,
                         y_pos: float, z_pos: float) -> Optional[cq.Workplane]:
        """Create a simple solid line."""
        try:
            return (
                cq.Workplane("XY")
                .rect(width, config.thickness)
                .extrude(config.height)
                .translate((0, y_pos, z_pos))
            )
        except Exception as e:
            print(f"Error creating solid divider: {e}")
            return None

    def _make_double_line(self, config: DividerConfig, width: float,
                          y_pos: float, z_pos: float) -> Optional[cq.Workplane]:
        """Create two parallel lines."""
        try:
            offset = (config.thickness + config.double_gap) / 2

            line1 = (
                cq.Workplane("XY")
                .rect(width, config.thickness)
                .extrude(config.height)
                .translate((0, y_pos + offset, z_pos))
            )

            line2 = (
                cq.Workplane("XY")
                .rect(width, config.thickness)
                .extrude(config.height)
                .translate((0, y_pos - offset, z_pos))
            )

            return line1.union(line2)
        except Exception as e:
            print(f"Error creating double divider: {e}")
            return None

    def _make_dashed_line(self, config: DividerConfig, width: float,
                          y_pos: float, z_pos: float) -> Optional[cq.Workplane]:
        """Create a dashed line."""
        try:
            result = None
            spacing = config.dash_length + config.dash_gap
            x = -width / 2 + config.dash_length / 2

            while x <= width / 2 - config.dash_length / 2:
                dash = (
                    cq.Workplane("XY")
                    .rect(config.dash_length, config.thickness)
                    .extrude(config.height)
                    .translate((x, y_pos, z_pos))
                )
                if result is None:
                    result = dash
                else:
                    result = result.union(dash)
                x += spacing

            return result
        except Exception as e:
            print(f"Error creating dashed divider: {e}")
            return None

    def _make_dotted_line(self, config: DividerConfig, width: float,
                          y_pos: float, z_pos: float) -> Optional[cq.Workplane]:
        """Create a dotted line."""
        try:
            result = None
            spacing = config.dot_spacing
            radius = config.dot_diameter / 2
            x = -width / 2 + spacing / 2

            while x <= width / 2 - spacing / 2:
                dot = (
                    cq.Workplane("XY")
                    .circle(radius)
                    .extrude(config.height)
                    .translate((x, y_pos, z_pos))
                )
                if result is None:
                    result = dot
                else:
                    result = result.union(dot)
                x += spacing

            return result
        except Exception as e:
            print(f"Error creating dotted divider: {e}")
            return None

    def _make_ornamental_line(self, config: DividerConfig, width: float,
                              y_pos: float, z_pos: float) -> Optional[cq.Workplane]:
        """Create a line with center ornament (diamond shape)."""
        try:
            # Create two lines with a gap in the middle
            ornament_size = config.thickness * 3
            gap = ornament_size + 2
            half_line_width = (width - gap) / 2

            # Left line
            left_line = (
                cq.Workplane("XY")
                .rect(half_line_width, config.thickness)
                .extrude(config.height)
                .translate((-half_line_width / 2 - gap / 2, y_pos, z_pos))
            )

            # Right line
            right_line = (
                cq.Workplane("XY")
                .rect(half_line_width, config.thickness)
                .extrude(config.height)
                .translate((half_line_width / 2 + gap / 2, y_pos, z_pos))
            )

            # Center ornament (diamond)
            ornament = (
                cq.Workplane("XY")
                .polygon(4, ornament_size)
                .extrude(config.height)
                .rotate((0, 0, 0), (0, 0, 1), 45)
                .translate((0, y_pos, z_pos))
            )

            return left_line.union(right_line).union(ornament)
        except Exception as e:
            print(f"Error creating ornamental divider: {e}")
            return None
