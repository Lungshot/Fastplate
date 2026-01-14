"""
Corner Decorations
Creates ornamental corner pieces for nameplates.
"""

import cadquery as cq
import math
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class CornerStyle(Enum):
    """Available corner decoration styles."""
    NONE = "none"
    SIMPLE = "simple"           # Simple L-shaped corner
    FLOURISH = "flourish"       # Curved flourish
    BRACKET = "bracket"         # Bracket/brace style
    FLORAL = "floral"           # Floral/leaf pattern
    ART_DECO = "art_deco"       # Art deco geometric
    VICTORIAN = "victorian"     # Victorian ornate
    CELTIC = "celtic"           # Celtic knot-inspired
    MODERN = "modern"           # Modern geometric


@dataclass
class CornerConfig:
    """Configuration for corner decorations."""
    style: CornerStyle = CornerStyle.NONE
    size: float = 15.0          # Size of corner decoration in mm
    thickness: float = 1.5      # Line thickness in mm
    height: float = 1.0         # Extrusion height in mm
    is_raised: bool = True      # True = raised, False = engraved
    all_corners: bool = True    # Apply to all 4 corners
    # Individual corner control (if all_corners is False)
    top_left: bool = True
    top_right: bool = True
    bottom_left: bool = True
    bottom_right: bool = True


class CornerDecorationGenerator:
    """Generates corner decoration geometry."""

    def generate(self, config: CornerConfig, plate_width: float,
                 plate_height: float, plate_thickness: float) -> Optional[cq.Workplane]:
        """
        Generate corner decorations for a plate.

        Args:
            config: Corner decoration configuration
            plate_width: Width of the plate
            plate_height: Height of the plate
            plate_thickness: Thickness of the plate

        Returns:
            CadQuery Workplane with corner decorations
        """
        if config.style == CornerStyle.NONE:
            return None

        # Generate single corner
        corner = self._create_corner(config)
        if corner is None:
            return None

        result = None

        # Position corners
        positions = []
        half_w = plate_width / 2 - config.size / 2
        half_h = plate_height / 2 - config.size / 2

        if config.all_corners or config.top_left:
            positions.append((-half_w, half_h, 0))      # Top left
        if config.all_corners or config.top_right:
            positions.append((half_w, half_h, 90))     # Top right
        if config.all_corners or config.bottom_right:
            positions.append((half_w, -half_h, 180))   # Bottom right
        if config.all_corners or config.bottom_left:
            positions.append((-half_w, -half_h, 270))  # Bottom left

        z_pos = plate_thickness if config.is_raised else plate_thickness - config.height

        for x, y, rotation in positions:
            placed = (
                corner
                .rotate((0, 0, 0), (0, 0, 1), rotation)
                .translate((x, y, z_pos))
            )
            if result is None:
                result = placed
            else:
                result = result.union(placed)

        return result

    def _create_corner(self, config: CornerConfig) -> Optional[cq.Workplane]:
        """Create a single corner decoration (oriented for top-left)."""
        generators = {
            CornerStyle.SIMPLE: self._make_simple,
            CornerStyle.FLOURISH: self._make_flourish,
            CornerStyle.BRACKET: self._make_bracket,
            CornerStyle.FLORAL: self._make_floral,
            CornerStyle.ART_DECO: self._make_art_deco,
            CornerStyle.VICTORIAN: self._make_victorian,
            CornerStyle.CELTIC: self._make_celtic,
            CornerStyle.MODERN: self._make_modern,
        }

        generator = generators.get(config.style)
        if generator:
            return generator(config)
        return None

    def _make_simple(self, config: CornerConfig) -> Optional[cq.Workplane]:
        """Create simple L-shaped corner."""
        try:
            s = config.size
            t = config.thickness

            # L-shape points
            points = [
                (0, 0),
                (s, 0),
                (s, t),
                (t, t),
                (t, s),
                (0, s),
            ]

            return (
                cq.Workplane("XY")
                .polyline(points)
                .close()
                .extrude(config.height)
                .translate((-s/2, -s/2, 0))
            )
        except Exception as e:
            print(f"Error creating simple corner: {e}")
            return None

    def _make_flourish(self, config: CornerConfig) -> Optional[cq.Workplane]:
        """Create curved flourish corner."""
        try:
            s = config.size
            t = config.thickness

            # Create curved L-shape with flourish
            points = []
            segments = 20

            # Outer curve
            for i in range(segments + 1):
                angle = math.pi / 2 * i / segments
                x = s * math.cos(angle)
                y = s * math.sin(angle)
                points.append((x, y))

            # Inner curve (reversed)
            inner_r = s - t * 2
            for i in range(segments, -1, -1):
                angle = math.pi / 2 * i / segments
                x = inner_r * math.cos(angle)
                y = inner_r * math.sin(angle)
                points.append((x, y))

            return (
                cq.Workplane("XY")
                .polyline(points)
                .close()
                .extrude(config.height)
                .translate((-s/2, -s/2, 0))
            )
        except Exception as e:
            print(f"Error creating flourish corner: {e}")
            return None

    def _make_bracket(self, config: CornerConfig) -> Optional[cq.Workplane]:
        """Create bracket/brace style corner."""
        try:
            s = config.size
            t = config.thickness

            # Bracket shape
            points = [
                (0, 0),
                (s * 0.3, 0),
                (s * 0.4, t),
                (s, t),
                (s, t * 2),
                (s * 0.4, t * 2),
                (s * 0.3, t),
                (t, t),
                (t, s * 0.3),
                (t * 2, s * 0.4),
                (t * 2, s),
                (t, s),
                (t, s * 0.4),
                (0, s * 0.3),
            ]

            return (
                cq.Workplane("XY")
                .polyline(points)
                .close()
                .extrude(config.height)
                .translate((-s/2, -s/2, 0))
            )
        except Exception as e:
            print(f"Error creating bracket corner: {e}")
            return None

    def _make_floral(self, config: CornerConfig) -> Optional[cq.Workplane]:
        """Create floral/leaf pattern corner."""
        try:
            s = config.size
            result = None

            # Create leaf shapes
            leaf_size = s * 0.3

            # Main L-frame
            frame = self._make_simple(config)
            if frame:
                result = frame

            # Add leaf/petal at corner
            for angle in [45]:
                petal_points = []
                for i in range(20):
                    t = i / 19.0
                    # Leaf curve
                    x = leaf_size * t * math.cos(t * math.pi)
                    y = leaf_size * t * math.sin(t * math.pi) * 0.5
                    petal_points.append((x, y))

                # Close the leaf
                for i in range(19, -1, -1):
                    t = i / 19.0
                    x = leaf_size * t * math.cos(t * math.pi)
                    y = -leaf_size * t * math.sin(t * math.pi) * 0.5
                    petal_points.append((x, y))

                try:
                    petal = (
                        cq.Workplane("XY")
                        .polyline(petal_points)
                        .close()
                        .extrude(config.height)
                        .rotate((0, 0, 0), (0, 0, 1), angle)
                        .translate((0, 0, 0))
                    )
                    if result:
                        result = result.union(petal)
                    else:
                        result = petal
                except Exception:
                    pass

            return result
        except Exception as e:
            print(f"Error creating floral corner: {e}")
            return None

    def _make_art_deco(self, config: CornerConfig) -> Optional[cq.Workplane]:
        """Create art deco geometric corner."""
        try:
            s = config.size
            t = config.thickness

            result = None

            # Create stepped pattern
            steps = 4
            for i in range(steps):
                step_s = s * (1 - i * 0.2)
                offset = i * t * 1.5

                points = [
                    (offset, offset),
                    (step_s, offset),
                    (step_s, offset + t),
                    (offset + t, offset + t),
                    (offset + t, step_s),
                    (offset, step_s),
                ]

                try:
                    step = (
                        cq.Workplane("XY")
                        .polyline(points)
                        .close()
                        .extrude(config.height)
                        .translate((-s/2, -s/2, 0))
                    )
                    if result is None:
                        result = step
                    else:
                        result = result.union(step)
                except Exception:
                    pass

            return result
        except Exception as e:
            print(f"Error creating art deco corner: {e}")
            return None

    def _make_victorian(self, config: CornerConfig) -> Optional[cq.Workplane]:
        """Create Victorian ornate corner."""
        try:
            s = config.size
            t = config.thickness

            result = None

            # Base L-shape
            base = self._make_simple(config)
            if base:
                result = base

            # Add decorative circles
            circle_r = t * 0.8
            positions = [
                (s * 0.2, s * 0.2),
                (s * 0.5, t * 1.5),
                (t * 1.5, s * 0.5),
            ]

            for x, y in positions:
                try:
                    circle = (
                        cq.Workplane("XY")
                        .circle(circle_r)
                        .extrude(config.height)
                        .translate((x - s/2, y - s/2, 0))
                    )
                    if result:
                        result = result.union(circle)
                except Exception:
                    pass

            return result
        except Exception as e:
            print(f"Error creating Victorian corner: {e}")
            return None

    def _make_celtic(self, config: CornerConfig) -> Optional[cq.Workplane]:
        """Create Celtic knot-inspired corner."""
        try:
            s = config.size
            t = config.thickness

            result = None

            # Create interwoven pattern (simplified)
            # Outer frame
            outer = self._make_simple(config)
            if outer:
                result = outer

            # Inner frame (offset)
            inner_config = CornerConfig(
                style=CornerStyle.SIMPLE,
                size=s * 0.7,
                thickness=t * 0.8,
                height=config.height
            )
            inner = self._make_simple(inner_config)
            if inner and result:
                result = result.union(inner)

            # Diagonal connector
            try:
                diag = (
                    cq.Workplane("XY")
                    .rect(t, s * 0.5)
                    .extrude(config.height)
                    .rotate((0, 0, 0), (0, 0, 1), 45)
                    .translate((0, 0, 0))
                )
                if result:
                    result = result.union(diag)
            except Exception:
                pass

            return result
        except Exception as e:
            print(f"Error creating Celtic corner: {e}")
            return None

    def _make_modern(self, config: CornerConfig) -> Optional[cq.Workplane]:
        """Create modern geometric corner."""
        try:
            s = config.size
            t = config.thickness

            result = None

            # Create geometric shapes
            # Triangle
            tri_points = [
                (0, 0),
                (s * 0.4, 0),
                (0, s * 0.4),
            ]
            try:
                tri = (
                    cq.Workplane("XY")
                    .polyline(tri_points)
                    .close()
                    .extrude(config.height)
                    .translate((-s/2, -s/2, 0))
                )
                result = tri
            except Exception:
                pass

            # Line accent
            try:
                line = (
                    cq.Workplane("XY")
                    .rect(s * 0.8, t * 0.5)
                    .extrude(config.height)
                    .rotate((0, 0, 0), (0, 0, 1), 45)
                    .translate((s * 0.1, s * 0.1, 0))
                )
                if result:
                    result = result.union(line)
                else:
                    result = line
            except Exception:
                pass

            return result
        except Exception as e:
            print(f"Error creating modern corner: {e}")
            return None


def get_corner_styles() -> List[str]:
    """Get list of available corner style names."""
    return [s.value for s in CornerStyle if s != CornerStyle.NONE]
