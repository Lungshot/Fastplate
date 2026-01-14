"""
Arc Text Generator
Creates text along curved paths.
"""

import cadquery as cq
import math
from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import Enum


class ArcDirection(Enum):
    """Direction of text on arc."""
    CLOCKWISE = "clockwise"       # Top of letters face outward (concave down)
    COUNTERCLOCKWISE = "counterclockwise"  # Top of letters face inward (concave up)


@dataclass
class ArcTextConfig:
    """Configuration for arc text."""
    text: str = ""
    font_path: str = ""
    font_size: float = 12.0
    depth: float = 2.0
    arc_radius: float = 50.0      # Radius of the arc in mm
    arc_angle: float = 180.0      # Total angle span in degrees
    start_angle: float = 0.0      # Starting angle (0 = right, 90 = top)
    direction: ArcDirection = ArcDirection.COUNTERCLOCKWISE
    position_x: float = 0.0
    position_y: float = 0.0


class ArcTextGenerator:
    """Generates text along an arc path."""

    def create_arc_text(self, config: ArcTextConfig) -> Optional[cq.Workplane]:
        """
        Create 3D text geometry along an arc.

        Args:
            config: Arc text configuration

        Returns:
            CadQuery Workplane with arc text geometry
        """
        if not config.text or not config.font_path:
            return None

        try:
            # Get individual character widths for spacing
            char_widths = self._get_character_widths(config)
            if not char_widths:
                return None

            # Calculate total text width
            total_width = sum(char_widths)

            # Calculate angle per unit of width
            arc_length = config.arc_radius * math.radians(config.arc_angle)
            scale = arc_length / total_width if total_width > 0 else 1

            # Generate each character positioned along the arc
            result = None
            current_angle = config.start_angle

            if config.direction == ArcDirection.COUNTERCLOCKWISE:
                # Start from start_angle and go counterclockwise (increasing angle)
                current_angle = config.start_angle + config.arc_angle / 2
                angle_direction = -1
            else:
                # Start from start_angle and go clockwise (decreasing angle)
                current_angle = config.start_angle - config.arc_angle / 2
                angle_direction = 1

            # Calculate starting position (beginning of text)
            accumulated_width = 0

            for i, char in enumerate(config.text):
                if char == ' ':
                    accumulated_width += char_widths[i]
                    continue

                # Calculate center position for this character
                char_center_width = accumulated_width + char_widths[i] / 2
                char_angle_offset = (char_center_width / total_width) * config.arc_angle

                if config.direction == ArcDirection.COUNTERCLOCKWISE:
                    char_angle = current_angle + angle_direction * char_angle_offset
                else:
                    char_angle = current_angle + angle_direction * char_angle_offset

                # Convert angle to radians
                angle_rad = math.radians(char_angle)

                # Calculate position on arc
                x = config.arc_radius * math.cos(angle_rad) + config.position_x
                y = config.arc_radius * math.sin(angle_rad) + config.position_y

                # Create character geometry
                try:
                    char_geom = (
                        cq.Workplane("XY")
                        .text(char, config.font_size, config.depth,
                              font=config.font_path, halign='center', valign='center')
                    )

                    # Rotate character to follow arc tangent
                    if config.direction == ArcDirection.COUNTERCLOCKWISE:
                        rotation = char_angle - 90  # Tangent angle
                    else:
                        rotation = char_angle + 90

                    char_geom = char_geom.rotate((0, 0, 0), (0, 0, 1), rotation)

                    # Move to position on arc
                    char_geom = char_geom.translate((x, y, 0))

                    if result is None:
                        result = char_geom
                    else:
                        result = result.union(char_geom)

                except Exception as e:
                    print(f"Error creating arc character '{char}': {e}")
                    continue

                accumulated_width += char_widths[i]

            return result

        except Exception as e:
            print(f"Arc text error: {e}")
            return None

    def _get_character_widths(self, config: ArcTextConfig) -> List[float]:
        """Get the width of each character in the text."""
        widths = []
        for char in config.text:
            if char == ' ':
                # Approximate space width as 30% of font size
                widths.append(config.font_size * 0.3)
            else:
                try:
                    # Create character and measure its bounding box
                    char_geom = (
                        cq.Workplane("XY")
                        .text(char, config.font_size, 1,
                              font=config.font_path, halign='center', valign='center')
                    )
                    bbox = char_geom.val().BoundingBox()
                    width = bbox.xmax - bbox.xmin
                    # Add small spacing between characters (10% of font size)
                    widths.append(width + config.font_size * 0.1)
                except Exception:
                    # Fallback width estimate
                    widths.append(config.font_size * 0.6)
        return widths

    def get_bounding_box(self, config: ArcTextConfig) -> Tuple[float, float, float, float]:
        """Get approximate bounding box for arc text."""
        # Calculate outer bounds based on arc geometry
        outer_radius = config.arc_radius + config.font_size
        return (
            config.position_x - outer_radius,
            config.position_y - outer_radius,
            config.position_x + outer_radius,
            config.position_y + outer_radius,
        )
