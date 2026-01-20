"""
Pattern Generator
Creates decorative patterns for nameplate backgrounds.
Optimized for performance using batch operations.
"""

import cadquery as cq
import math
from dataclasses import dataclass
from typing import Optional, List, Tuple
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

    def to_dict(self) -> dict:
        """Serialize PatternConfig to a dictionary."""
        return {
            'pattern_type': self.pattern_type.value,
            'spacing': self.spacing,
            'size': self.size,
            'depth': self.depth,
            'angle': self.angle,
            'style': self.style,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PatternConfig':
        """Deserialize PatternConfig from a dictionary."""
        pattern_type = data.get('pattern_type', 'none')
        if isinstance(pattern_type, str):
            pattern_type = PatternType(pattern_type)

        return cls(
            pattern_type=pattern_type,
            spacing=data.get('spacing', 5.0),
            size=data.get('size', 1.0),
            depth=data.get('depth', 0.3),
            angle=data.get('angle', 0.0),
            style=data.get('style', 'engraved'),
        )


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
            if pattern:
                # Apply rotation if specified
                if config.angle != 0:
                    pattern = pattern.rotate((0, 0, 0), (0, 0, 1), config.angle)
                # Position pattern at TOP of plate surface
                # All patterns use extrude() starting at Z=0, going to Z=depth
                # Translate so pattern cuts from plate_thickness-depth to plate_thickness
                z_position = plate_thickness - config.depth
                pattern = pattern.translate((0, 0, z_position))
            return pattern

        return None

    def _make_grid(self, config: PatternConfig, width: float, height: float) -> Optional[cq.Workplane]:
        """Create a grid pattern of lines - optimized with single sketch."""
        spacing = config.spacing
        line_width = config.size

        # Build all lines in a single sketch
        sketch = cq.Sketch()

        # Vertical lines
        x = -width / 2
        while x <= width / 2:
            sketch = sketch.push([(x, 0)]).rect(line_width, height).reset()
            x += spacing

        # Horizontal lines
        y = -height / 2
        while y <= height / 2:
            sketch = sketch.push([(0, y)]).rect(width, line_width).reset()
            y += spacing

        # Extrude once
        result = cq.Workplane("XY").placeSketch(sketch).extrude(config.depth)
        return result

    def _make_dots(self, config: PatternConfig, width: float, height: float) -> Optional[cq.Workplane]:
        """Create a pattern of dots - optimized with pushPoints."""
        spacing = config.spacing
        radius = config.size / 2

        # Collect all dot positions
        points = []
        y = -height / 2 + spacing / 2
        while y <= height / 2:
            x = -width / 2 + spacing / 2
            while x <= width / 2:
                points.append((x, y))
                x += spacing
            y += spacing

        if not points:
            return None

        # Create all dots at once using pushPoints
        result = (
            cq.Workplane("XY")
            .pushPoints(points)
            .circle(radius)
            .extrude(config.depth)
        )
        return result

    def _make_diamonds(self, config: PatternConfig, width: float, height: float) -> Optional[cq.Workplane]:
        """Create a diamond pattern - optimized with sketch."""
        spacing = config.spacing
        size = config.size

        # Build sketch with all diamonds
        sketch = cq.Sketch()

        y = -height / 2
        row = 0
        while y <= height / 2 + spacing:
            x_offset = (row % 2) * spacing / 2
            x = -width / 2 + x_offset
            while x <= width / 2 + spacing:
                # Add rotated square (diamond) at this position
                sketch = sketch.push([(x, y)]).regularPolygon(size / 1.414, 4, angle=45).reset()
                x += spacing
            y += spacing
            row += 1

        # Extrude once
        result = cq.Workplane("XY").placeSketch(sketch).extrude(config.depth)
        return result

    def _make_hexagons(self, config: PatternConfig, width: float, height: float) -> Optional[cq.Workplane]:
        """Create a honeycomb pattern - optimized with sketch."""
        spacing = config.spacing
        size = config.size

        # Hexagon dimensions
        hex_width = size * 2
        hex_height = size * math.sqrt(3)
        horiz_spacing = max(hex_width * 0.75, spacing)
        vert_spacing = max(hex_height, spacing)

        # Build sketch with all hexagons
        sketch = cq.Sketch()

        y = -height / 2
        row = 0
        count = 0
        max_shapes = 200  # Limit to prevent crashes

        while y <= height / 2 + vert_spacing and count < max_shapes:
            x_offset = (row % 2) * horiz_spacing / 2
            x = -width / 2 + x_offset
            while x <= width / 2 + horiz_spacing and count < max_shapes:
                sketch = sketch.push([(x, y)]).regularPolygon(size, 6).reset()
                x += horiz_spacing
                count += 1
            y += vert_spacing
            row += 1

        # Extrude once
        result = cq.Workplane("XY").placeSketch(sketch).extrude(config.depth)
        return result

    def _make_lines(self, config: PatternConfig, width: float, height: float) -> Optional[cq.Workplane]:
        """Create parallel lines pattern - optimized with single sketch."""
        spacing = config.spacing
        line_width = config.size

        # Build all lines in a single sketch
        sketch = cq.Sketch()

        y = -height / 2
        while y <= height / 2:
            sketch = sketch.push([(0, y)]).rect(width, line_width).reset()
            y += spacing

        # Extrude once
        result = cq.Workplane("XY").placeSketch(sketch).extrude(config.depth)
        return result

    def _make_crosshatch(self, config: PatternConfig, width: float, height: float) -> Optional[cq.Workplane]:
        """Create a crosshatch pattern - optimized with single sketch."""
        spacing = config.spacing
        line_width = config.size

        # Calculate diagonal length needed
        diagonal = math.sqrt(width**2 + height**2)

        # Build all lines in a single sketch
        sketch = cq.Sketch()

        offset = -diagonal / 2
        while offset <= diagonal / 2:
            # Line at +45 degrees (rotated rect)
            x1 = offset * 0.707
            sketch = sketch.push([(x1, 0)]).rect(line_width, diagonal * 1.5, angle=45).reset()

            # Line at -45 degrees
            sketch = sketch.push([(x1, 0)]).rect(line_width, diagonal * 1.5, angle=-45).reset()

            offset += spacing

        # Extrude once
        result = cq.Workplane("XY").placeSketch(sketch).extrude(config.depth)
        return result

    def _make_chevron(self, config: PatternConfig, width: float, height: float) -> Optional[cq.Workplane]:
        """Create a chevron/arrow pattern - optimized."""
        spacing = config.spacing
        size = config.size

        # Collect all chevron shapes
        shapes = []
        y = -height / 2

        while y <= height / 2 + spacing:
            # Create V-shaped chevron points
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
            shapes.append(chevron)
            y += spacing

        # Combine all shapes - use compound for efficiency
        if not shapes:
            return None

        if len(shapes) == 1:
            return shapes[0]

        # Batch union - combine pairs recursively for better performance
        result = self._batch_union(shapes)
        return result

    def _batch_union(self, shapes: List[cq.Workplane]) -> cq.Workplane:
        """
        Efficiently union multiple shapes using divide-and-conquer.
        This is O(n log n) instead of O(n²) for sequential unions.
        """
        if len(shapes) == 1:
            return shapes[0]
        if len(shapes) == 2:
            return shapes[0].union(shapes[1])

        # Split and recursively union
        mid = len(shapes) // 2
        left = self._batch_union(shapes[:mid])
        right = self._batch_union(shapes[mid:])
        return left.union(right)
