"""
Pattern Generator
Creates decorative patterns for nameplate backgrounds.
"""

import cadquery as cq
import math
from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum


class PatternType(Enum):
    """Available background patterns."""
    NONE = "none"
    GRID = "grid"              # Grid of lines
    DOTS = "dots"              # Array of dots/circles
    DIAMONDS = "diamonds"      # Diamond/rhombus pattern
    HEXAGONS = "hexagons"      # Honeycomb pattern
    LINES = "lines"            # Parallel lines
    CROSSHATCH = "crosshatch"  # Crossed diagonal lines
    WAVES = "waves"            # Wavy lines
    CHEVRON = "chevron"        # Chevron/arrow pattern


@dataclass
class PatternConfig:
    """Configuration for pattern generation."""
    pattern_type: PatternType = PatternType.NONE
    spacing: float = 5.0       # mm between pattern elements
    size: float = 1.0          # mm size of pattern elements
    depth: float = 0.3         # mm depth of engraved pattern
    angle: float = 0.0         # degrees rotation of pattern
    style: str = "engraved"    # "engraved" or "raised"


class PatternGenerator:
    """Generates decorative patterns for backgrounds."""

    def generate(self, config: PatternConfig, width: float, height: float,
                 plate_thickness: float) -> Optional[cq.Workplane]:
        """
        Generate pattern geometry.

        Args:
            config: Pattern configuration
            width: Width of the area to fill
            height: Height of the area to fill
            plate_thickness: Thickness of the plate (for positioning)

        Returns:
            CadQuery Workplane with pattern geometry (for subtraction/union)
        """
        if config.pattern_type == PatternType.NONE:
            return None

        generators = {
            PatternType.GRID: self._make_grid,
            PatternType.DOTS: self._make_dots,
            PatternType.DIAMONDS: self._make_diamonds,
            PatternType.HEXAGONS: self._make_hexagons,
            PatternType.LINES: self._make_lines,
            PatternType.CROSSHATCH: self._make_crosshatch,
            PatternType.CHEVRON: self._make_chevron,
        }

        generator = generators.get(config.pattern_type)
        if generator:
            pattern = generator(config, width, height)
            if pattern and config.angle != 0:
                pattern = pattern.rotate((0, 0, 0), (0, 0, 1), config.angle)
            return pattern

        return None

    def _make_grid(self, config: PatternConfig, width: float, height: float) -> Optional[cq.Workplane]:
        """Create a grid pattern of lines."""
        result = None
        spacing = config.spacing
        line_width = config.size

        # Vertical lines
        x = -width / 2
        while x <= width / 2:
            line = (
                cq.Workplane("XY")
                .box(line_width, height, config.depth)
                .translate((x, 0, config.depth / 2))
            )
            if result is None:
                result = line
            else:
                result = result.union(line)
            x += spacing

        # Horizontal lines
        y = -height / 2
        while y <= height / 2:
            line = (
                cq.Workplane("XY")
                .box(width, line_width, config.depth)
                .translate((0, y, config.depth / 2))
            )
            result = result.union(line)
            y += spacing

        return result

    def _make_dots(self, config: PatternConfig, width: float, height: float) -> Optional[cq.Workplane]:
        """Create a pattern of dots."""
        result = None
        spacing = config.spacing
        radius = config.size / 2

        y = -height / 2 + spacing / 2
        while y <= height / 2:
            x = -width / 2 + spacing / 2
            while x <= width / 2:
                dot = (
                    cq.Workplane("XY")
                    .circle(radius)
                    .extrude(config.depth)
                    .translate((x, y, 0))
                )
                if result is None:
                    result = dot
                else:
                    result = result.union(dot)
                x += spacing
            y += spacing

        return result

    def _make_diamonds(self, config: PatternConfig, width: float, height: float) -> Optional[cq.Workplane]:
        """Create a diamond pattern."""
        result = None
        spacing = config.spacing
        size = config.size

        y = -height / 2
        row = 0
        while y <= height / 2 + spacing:
            x_offset = (row % 2) * spacing / 2
            x = -width / 2 + x_offset
            while x <= width / 2 + spacing:
                # Create diamond shape
                diamond = (
                    cq.Workplane("XY")
                    .polygon(4, size, circumscribed=False)
                    .extrude(config.depth)
                    .rotate((0, 0, 0), (0, 0, 1), 45)
                    .translate((x, y, 0))
                )
                if result is None:
                    result = diamond
                else:
                    result = result.union(diamond)
                x += spacing
            y += spacing
            row += 1

        return result

    def _make_hexagons(self, config: PatternConfig, width: float, height: float) -> Optional[cq.Workplane]:
        """Create a honeycomb pattern."""
        result = None
        spacing = config.spacing
        size = config.size

        # Hexagon dimensions
        hex_width = size * 2
        hex_height = size * math.sqrt(3)
        horiz_spacing = hex_width * 0.75
        vert_spacing = hex_height

        y = -height / 2
        row = 0
        while y <= height / 2 + vert_spacing:
            x_offset = (row % 2) * horiz_spacing / 2
            x = -width / 2 + x_offset
            while x <= width / 2 + horiz_spacing:
                hex_shape = (
                    cq.Workplane("XY")
                    .polygon(6, size)
                    .extrude(config.depth)
                    .translate((x, y, 0))
                )
                if result is None:
                    result = hex_shape
                else:
                    result = result.union(hex_shape)
                x += horiz_spacing
            y += vert_spacing
            row += 1

        return result

    def _make_lines(self, config: PatternConfig, width: float, height: float) -> Optional[cq.Workplane]:
        """Create parallel lines pattern."""
        result = None
        spacing = config.spacing
        line_width = config.size

        # Horizontal lines
        y = -height / 2
        while y <= height / 2:
            line = (
                cq.Workplane("XY")
                .box(width, line_width, config.depth)
                .translate((0, y, config.depth / 2))
            )
            if result is None:
                result = line
            else:
                result = result.union(line)
            y += spacing

        return result

    def _make_crosshatch(self, config: PatternConfig, width: float, height: float) -> Optional[cq.Workplane]:
        """Create a crosshatch pattern."""
        result = None
        spacing = config.spacing
        line_width = config.size

        # Calculate diagonal length needed
        diagonal = math.sqrt(width**2 + height**2)

        # Create lines at 45 degrees
        offset = -diagonal / 2
        while offset <= diagonal / 2:
            # Line at +45 degrees
            line1 = (
                cq.Workplane("XY")
                .box(line_width, diagonal * 1.5, config.depth)
                .rotate((0, 0, 0), (0, 0, 1), 45)
                .translate((offset * 0.707, 0, config.depth / 2))
            )

            # Line at -45 degrees
            line2 = (
                cq.Workplane("XY")
                .box(line_width, diagonal * 1.5, config.depth)
                .rotate((0, 0, 0), (0, 0, 1), -45)
                .translate((offset * 0.707, 0, config.depth / 2))
            )

            if result is None:
                result = line1.union(line2)
            else:
                result = result.union(line1).union(line2)

            offset += spacing

        return result

    def _make_chevron(self, config: PatternConfig, width: float, height: float) -> Optional[cq.Workplane]:
        """Create a chevron/arrow pattern."""
        result = None
        spacing = config.spacing
        size = config.size

        y = -height / 2
        while y <= height / 2 + spacing:
            # Create V-shaped chevron
            half_width = width / 2 + spacing
            points = [
                (-half_width, 0),
                (0, size),
                (half_width, 0),
                (half_width, -size / 2),
                (0, size / 2),
                (-half_width, -size / 2),
            ]

            chevron = (
                cq.Workplane("XY")
                .polyline(points)
                .close()
                .extrude(config.depth)
                .translate((0, y, 0))
            )

            if result is None:
                result = chevron
            else:
                result = result.union(chevron)

            y += spacing

        return result
