"""
Texture Surfaces
Creates surface textures for nameplates (brushed, wood grain, carbon fiber, etc.)
"""

import cadquery as cq
import math
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class TextureType(Enum):
    """Available surface texture types."""
    NONE = "none"
    BRUSHED = "brushed"           # Brushed metal lines
    WOOD_GRAIN = "wood_grain"     # Wood grain pattern
    CARBON_FIBER = "carbon_fiber" # Carbon fiber weave
    LEATHER = "leather"           # Leather grain
    SANDBLAST = "sandblast"       # Sandblasted/matte dots
    KNURLED = "knurled"           # Diamond knurl pattern
    HAMMERED = "hammered"         # Hammered metal look
    RIPPLE = "ripple"             # Ripple/wave pattern


@dataclass
class TextureConfig:
    """Configuration for surface textures."""
    texture_type: TextureType = TextureType.NONE
    depth: float = 0.2            # Depth of texture features in mm
    spacing: float = 1.0          # Spacing between texture elements
    angle: float = 0.0            # Rotation angle for texture
    scale: float = 1.0            # Overall scale factor
    is_raised: bool = False       # True = raised, False = engraved


class TextureGenerator:
    """
    Generates surface texture geometry.

    Note: Surface textures add many small geometric features which can
    significantly increase file size and processing time.
    """

    def generate(self, config: TextureConfig, plate_width: float,
                 plate_height: float, plate_thickness: float,
                 margin: float = 2.0) -> Optional[cq.Workplane]:
        """
        Generate texture geometry for a plate surface.

        Args:
            config: Texture configuration
            plate_width: Width of the plate
            plate_height: Height of the plate
            plate_thickness: Thickness of the plate
            margin: Margin from plate edges

        Returns:
            CadQuery Workplane with texture geometry to add/subtract
        """
        if config.texture_type == TextureType.NONE:
            return None

        generators = {
            TextureType.BRUSHED: self._make_brushed,
            TextureType.WOOD_GRAIN: self._make_wood_grain,
            TextureType.CARBON_FIBER: self._make_carbon_fiber,
            TextureType.LEATHER: self._make_leather,
            TextureType.SANDBLAST: self._make_sandblast,
            TextureType.KNURLED: self._make_knurled,
            TextureType.HAMMERED: self._make_hammered,
            TextureType.RIPPLE: self._make_ripple,
        }

        generator = generators.get(config.texture_type)
        if generator:
            # Calculate texture area
            tex_width = plate_width - margin * 2
            tex_height = plate_height - margin * 2

            if tex_width <= 0 or tex_height <= 0:
                return None

            texture = generator(config, tex_width, tex_height)
            if texture:
                # Position texture
                z_pos = plate_thickness if config.is_raised else plate_thickness - config.depth
                texture = texture.translate((0, 0, z_pos))

                # Apply rotation if specified
                if config.angle != 0:
                    texture = texture.rotate((0, 0, 0), (0, 0, 1), config.angle)

            return texture

        return None

    def _make_brushed(self, config: TextureConfig,
                      width: float, height: float) -> Optional[cq.Workplane]:
        """Create brushed metal texture (parallel lines)."""
        try:
            result = None
            spacing = config.spacing * config.scale
            line_width = spacing * 0.3

            x = -width / 2
            while x <= width / 2:
                line = (
                    cq.Workplane("XY")
                    .rect(line_width, height)
                    .extrude(config.depth)
                    .translate((x, 0, 0))
                )
                if result is None:
                    result = line
                else:
                    result = result.union(line)
                x += spacing

            return result
        except Exception as e:
            print(f"Error creating brushed texture: {e}")
            return None

    def _make_wood_grain(self, config: TextureConfig,
                         width: float, height: float) -> Optional[cq.Workplane]:
        """Create wood grain texture (wavy parallel lines)."""
        try:
            result = None
            spacing = config.spacing * config.scale * 2
            line_width = spacing * 0.2

            y = -height / 2
            while y <= height / 2:
                # Create wavy line using points
                points = []
                segments = int(width / 2)
                for i in range(segments + 1):
                    x = -width / 2 + (width * i / segments)
                    # Add wave variation
                    wave = math.sin(x * 0.2 + y * 0.1) * spacing * 0.3
                    points.append((x, y + wave))

                # Create line from points
                if len(points) >= 2:
                    try:
                        line = (
                            cq.Workplane("XY")
                            .polyline(points)
                            .offset2D(line_width / 2)
                            .extrude(config.depth)
                        )
                        if result is None:
                            result = line
                        else:
                            result = result.union(line)
                    except Exception:
                        pass

                y += spacing

            return result
        except Exception as e:
            print(f"Error creating wood grain texture: {e}")
            return None

    def _make_carbon_fiber(self, config: TextureConfig,
                           width: float, height: float) -> Optional[cq.Workplane]:
        """Create carbon fiber weave pattern."""
        try:
            result = None
            spacing = config.spacing * config.scale * 3
            fiber_width = spacing * 0.4

            # Create diagonal lines in both directions
            for angle in [45, -45]:
                # Calculate how many lines needed
                diagonal = math.sqrt(width**2 + height**2)
                num_lines = int(diagonal / spacing) + 2

                for i in range(-num_lines, num_lines + 1):
                    offset = i * spacing
                    try:
                        line = (
                            cq.Workplane("XY")
                            .rect(diagonal, fiber_width)
                            .extrude(config.depth / 2)
                            .rotate((0, 0, 0), (0, 0, 1), angle)
                            .translate((offset * math.cos(math.radians(angle + 90)),
                                       offset * math.sin(math.radians(angle + 90)), 0))
                        )
                        if result is None:
                            result = line
                        else:
                            result = result.union(line)
                    except Exception:
                        pass

            # Clip to plate bounds
            if result:
                clip = (
                    cq.Workplane("XY")
                    .rect(width, height)
                    .extrude(config.depth)
                )
                result = result.intersect(clip)

            return result
        except Exception as e:
            print(f"Error creating carbon fiber texture: {e}")
            return None

    def _make_leather(self, config: TextureConfig,
                      width: float, height: float) -> Optional[cq.Workplane]:
        """Create leather grain texture (irregular bumps)."""
        try:
            result = None
            spacing = config.spacing * config.scale * 2
            bump_size = spacing * 0.4

            # Create irregular grid of small bumps
            import random
            random.seed(42)  # Consistent pattern

            y = -height / 2
            while y <= height / 2:
                x = -width / 2
                while x <= width / 2:
                    # Add randomness to position and size
                    rx = x + random.uniform(-spacing * 0.2, spacing * 0.2)
                    ry = y + random.uniform(-spacing * 0.2, spacing * 0.2)
                    rs = bump_size * random.uniform(0.7, 1.3)

                    if -width/2 <= rx <= width/2 and -height/2 <= ry <= height/2:
                        try:
                            bump = (
                                cq.Workplane("XY")
                                .ellipse(rs, rs * 0.7)
                                .extrude(config.depth * random.uniform(0.5, 1.0))
                                .translate((rx, ry, 0))
                            )
                            if result is None:
                                result = bump
                            else:
                                result = result.union(bump)
                        except Exception:
                            pass

                    x += spacing
                y += spacing

            return result
        except Exception as e:
            print(f"Error creating leather texture: {e}")
            return None

    def _make_sandblast(self, config: TextureConfig,
                        width: float, height: float) -> Optional[cq.Workplane]:
        """Create sandblasted/matte texture (many small dots)."""
        try:
            result = None
            spacing = config.spacing * config.scale
            dot_size = spacing * 0.3

            y = -height / 2
            row = 0
            while y <= height / 2:
                x = -width / 2 + (spacing / 2 if row % 2 else 0)
                while x <= width / 2:
                    try:
                        dot = (
                            cq.Workplane("XY")
                            .circle(dot_size / 2)
                            .extrude(config.depth)
                            .translate((x, y, 0))
                        )
                        if result is None:
                            result = dot
                        else:
                            result = result.union(dot)
                    except Exception:
                        pass
                    x += spacing
                y += spacing * 0.866  # Hexagonal packing
                row += 1

            return result
        except Exception as e:
            print(f"Error creating sandblast texture: {e}")
            return None

    def _make_knurled(self, config: TextureConfig,
                      width: float, height: float) -> Optional[cq.Workplane]:
        """Create diamond knurl pattern."""
        try:
            result = None
            spacing = config.spacing * config.scale * 2
            diamond_size = spacing * 0.7

            y = -height / 2
            row = 0
            while y <= height / 2:
                x = -width / 2 + (spacing / 2 if row % 2 else 0)
                while x <= width / 2:
                    # Create small diamond/pyramid
                    try:
                        diamond = (
                            cq.Workplane("XY")
                            .polygon(4, diamond_size)
                            .extrude(config.depth)
                            .translate((x, y, 0))
                        )
                        if result is None:
                            result = diamond
                        else:
                            result = result.union(diamond)
                    except Exception:
                        pass
                    x += spacing
                y += spacing
                row += 1

            return result
        except Exception as e:
            print(f"Error creating knurled texture: {e}")
            return None

    def _make_hammered(self, config: TextureConfig,
                       width: float, height: float) -> Optional[cq.Workplane]:
        """Create hammered metal texture (irregular depressions)."""
        try:
            result = None
            spacing = config.spacing * config.scale * 3
            depression_size = spacing * 0.8

            import random
            random.seed(42)

            y = -height / 2
            while y <= height / 2:
                x = -width / 2
                while x <= width / 2:
                    rx = x + random.uniform(-spacing * 0.3, spacing * 0.3)
                    ry = y + random.uniform(-spacing * 0.3, spacing * 0.3)
                    rs = depression_size * random.uniform(0.6, 1.4)

                    if -width/2 <= rx <= width/2 and -height/2 <= ry <= height/2:
                        try:
                            # Create elliptical depression
                            depression = (
                                cq.Workplane("XY")
                                .ellipse(rs, rs * random.uniform(0.7, 1.0))
                                .extrude(config.depth * random.uniform(0.3, 1.0))
                                .translate((rx, ry, 0))
                            )
                            if result is None:
                                result = depression
                            else:
                                result = result.union(depression)
                        except Exception:
                            pass

                    x += spacing
                y += spacing

            return result
        except Exception as e:
            print(f"Error creating hammered texture: {e}")
            return None

    def _make_ripple(self, config: TextureConfig,
                     width: float, height: float) -> Optional[cq.Workplane]:
        """Create ripple/wave pattern (concentric circles)."""
        try:
            result = None
            spacing = config.spacing * config.scale * 2
            ring_width = spacing * 0.3

            # Create concentric rings from center
            max_radius = math.sqrt((width/2)**2 + (height/2)**2)
            radius = spacing

            while radius <= max_radius:
                try:
                    # Create ring (outer circle - inner circle)
                    outer = (
                        cq.Workplane("XY")
                        .circle(radius + ring_width / 2)
                        .extrude(config.depth)
                    )
                    inner = (
                        cq.Workplane("XY")
                        .circle(radius - ring_width / 2)
                        .extrude(config.depth + 0.1)
                    )
                    ring = outer.cut(inner)

                    if result is None:
                        result = ring
                    else:
                        result = result.union(ring)
                except Exception:
                    pass

                radius += spacing

            # Clip to plate bounds
            if result:
                clip = (
                    cq.Workplane("XY")
                    .rect(width, height)
                    .extrude(config.depth + 0.1)
                )
                result = result.intersect(clip)

            return result
        except Exception as e:
            print(f"Error creating ripple texture: {e}")
            return None


def get_texture_types() -> List[str]:
    """Get list of available texture type names."""
    return [t.value for t in TextureType if t != TextureType.NONE]
