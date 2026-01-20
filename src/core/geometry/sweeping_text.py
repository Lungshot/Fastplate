"""
Sweeping Text Builder
Creates 3D text that curves along an arc, similar to the popular
"Sweeping 2-line nameplate" style.
"""

import cadquery as cq
import math
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from pathlib import Path

from .text_builder import TextConfig, TextLineConfig, TextSegment, TextStyle


@dataclass
class SweepingTextConfig:
    """Configuration for sweeping/curved text."""
    # Arc parameters
    curve_radius: float = 80.0      # mm - radius of the text arc
    curve_angle: float = 90.0       # degrees - total angle the text spans

    # Text configuration
    text_config: TextConfig = field(default_factory=TextConfig)

    # Positioning
    start_angle: float = -45.0      # degrees - where text starts (0 = top)
    text_on_outside: bool = True    # True = text on outer surface, False = inner

    # Vertical stacking for multi-line
    line_gap: float = 2.0           # mm - gap between lines


class SweepingTextBuilder:
    """
    Builds 3D text that curves along an arc.

    The text follows a circular arc, with each character rotated
    to be tangent to the curve. This creates the classic "sweeping nameplate"
    look where the text wraps around a curved surface.
    """

    def __init__(self, config: Optional[SweepingTextConfig] = None):
        self.config = config or SweepingTextConfig()

    def generate(self, config: Optional[SweepingTextConfig] = None) -> Tuple[cq.Workplane, Tuple[float, float, float, float]]:
        """
        Generate swept 3D text geometry.

        Args:
            config: Optional config override

        Returns:
            Tuple of (CadQuery Workplane with text solid, bounding box)
        """
        cfg = config or self.config
        text_cfg = cfg.text_config

        print(f"[SweepingText] Starting generation: radius={cfg.curve_radius}, angle={cfg.curve_angle}")
        print(f"[SweepingText] Lines: {len(text_cfg.lines) if text_cfg.lines else 0}")

        if not text_cfg.lines or all(not line.has_content() for line in text_cfg.lines):
            print("[SweepingText] No content, returning empty")
            return cq.Workplane("XY"), (0, 0, 0, 0)

        # Filter to non-empty lines
        active_lines = [line for line in text_cfg.lines if line.has_content()]
        print(f"[SweepingText] Active lines: {len(active_lines)}")
        for i, line in enumerate(active_lines):
            segs = line.get_effective_segments()
            print(f"[SweepingText] Line {i}: {len(segs)} segments")
            for j, seg in enumerate(segs):
                print(f"[SweepingText]   Seg {j}: '{seg.content}' font={seg.font_family} size={seg.font_size}")

        if not active_lines:
            print("[SweepingText] No active lines!")
            return cq.Workplane("XY"), (0, 0, 0, 0)

        # Generate each line along the arc
        all_line_objects = []

        # Calculate vertical offsets for each line
        # Lines are stacked radially (different radii for each line)
        num_lines = len(active_lines)

        try:
            for line_idx, line_cfg in enumerate(active_lines):
                # Calculate radius for this line (outer lines have larger radius)
                # First line is at the specified radius, subsequent lines are offset inward
                if cfg.text_on_outside:
                    line_radius = cfg.curve_radius - (line_idx * (self._get_max_font_size(line_cfg) + cfg.line_gap))
                else:
                    line_radius = cfg.curve_radius + (line_idx * (self._get_max_font_size(line_cfg) + cfg.line_gap))

                print(f"[SweepingText] Generating line {line_idx} at radius {line_radius}")

                # Generate this line along the arc
                line_obj = self._generate_swept_line(line_cfg, line_radius, cfg, text_cfg.depth)

                print(f"[SweepingText] Line {line_idx} result: {line_obj is not None}")

                if line_obj is not None:
                    all_line_objects.append(line_obj)

            print(f"[SweepingText] Total line objects: {len(all_line_objects)}")

            if not all_line_objects:
                print("[SweepingText] No line objects generated!")
                return cq.Workplane("XY"), (0, 0, 0, 0)

            # Combine all lines
            combined = self._combine_objects(all_line_objects)
            print(f"[SweepingText] Combined result: {combined is not None}")

            # Calculate bounding box
            try:
                bb = combined.val().BoundingBox()
                overall_bbox = (bb.xmin, bb.ymin, bb.xmax, bb.ymax)
                print(f"[SweepingText] BBox: {overall_bbox}")
            except Exception as e:
                print(f"[SweepingText] BBox error: {e}")
                overall_bbox = (-50, -30, 50, 30)

            return combined, overall_bbox

        except Exception as e:
            import traceback
            print(f"[SweepingText] ERROR: {e}")
            traceback.print_exc()
            return cq.Workplane("XY"), (0, 0, 0, 0)

    def _get_max_font_size(self, line_cfg: TextLineConfig) -> float:
        """Get the maximum font size from a line's segments."""
        segments = line_cfg.get_effective_segments()
        if segments:
            return max(s.font_size for s in segments)
        return line_cfg.font_size

    def _generate_swept_line(self, line_cfg: TextLineConfig, radius: float,
                              sweep_cfg: SweepingTextConfig, depth: float) -> Optional[cq.Workplane]:
        """Generate a single line of text swept along an arc."""
        segments = line_cfg.get_effective_segments()
        if not segments:
            return None

        # Get all characters with their font info
        all_chars = []
        for seg in segments:
            for char in seg.content:
                all_chars.append((char, seg))

        if not all_chars:
            return None

        # First pass: measure all character widths
        char_infos = []  # [(char, segment, width, char_obj), ...]

        for char, seg in all_chars:
            if char == ' ':
                char_infos.append((char, seg, seg.font_size * 0.3, None))
            else:
                try:
                    text_params = {
                        'fontsize': seg.font_size,
                        'distance': depth,
                        'font': seg.font_family,
                        'kind': seg.get_cadquery_kind(),
                        'halign': 'center',
                        'valign': 'center',
                        'combine': True
                    }
                    if seg.font_path and seg.font_path.exists():
                        text_params['fontPath'] = str(seg.font_path)

                    char_obj = cq.Workplane("XY").text(char, **text_params)
                    bb = char_obj.val().BoundingBox()
                    width = bb.xmax - bb.xmin
                    char_infos.append((char, seg, width, char_obj))
                except Exception as e:
                    # Fallback width
                    char_infos.append((char, seg, seg.font_size * 0.6, None))

        # Calculate total arc length needed for all characters
        total_width = sum(info[2] for info in char_infos)

        # Add letter spacing
        spacing_total = 0
        for i, (char, seg, width, obj) in enumerate(char_infos):
            if i > 0 and seg.letter_spacing != 0:
                spacing_total += seg.font_size * (seg.letter_spacing / 100.0)
        total_width += spacing_total

        # Convert total width to angle
        # Arc length = radius * angle (in radians)
        total_angle_rad = total_width / radius
        total_angle_deg = math.degrees(total_angle_rad)

        # Limit to configured curve angle
        if total_angle_deg > sweep_cfg.curve_angle:
            # Scale down to fit
            scale_factor = sweep_cfg.curve_angle / total_angle_deg
            total_angle_deg = sweep_cfg.curve_angle
            total_angle_rad = math.radians(total_angle_deg)

        # Position each character along the arc
        positioned_chars = []

        # Start angle (centered around 0 = top of arc)
        current_angle = -total_angle_rad / 2

        for i, (char, seg, width, char_obj) in enumerate(char_infos):
            if char_obj is None:
                # Skip spaces but account for their width
                char_angle = width / radius
                current_angle += char_angle
                if i < len(char_infos) - 1 and seg.letter_spacing != 0:
                    current_angle += (seg.font_size * (seg.letter_spacing / 100.0)) / radius
                continue

            # Calculate angle for center of this character
            char_angle = width / radius
            center_angle = current_angle + char_angle / 2

            # Position on arc
            # Arc is in the XY plane, curving in Y direction
            # At angle=0, character is at (0, radius)
            # Positive angle goes counter-clockwise (left)
            x = radius * math.sin(center_angle)
            y = radius * math.cos(center_angle)

            # Rotate character to be tangent to arc
            # Character needs to be rotated by -center_angle (in degrees) around Z axis
            rotation_deg = -math.degrees(center_angle)

            try:
                # Position the character
                positioned = (
                    char_obj
                    .rotate((0, 0, 0), (0, 0, 1), rotation_deg)  # Rotate to follow arc
                    .translate((x, y - radius, 0))  # Position (shift Y so arc center is at origin)
                )
                positioned_chars.append(positioned)
            except Exception as e:
                print(f"[SweepingText] Error positioning character '{char}': {e}")

            # Move to next character position
            current_angle += char_angle
            if i < len(char_infos) - 1 and seg.letter_spacing != 0:
                current_angle += (seg.font_size * (seg.letter_spacing / 100.0)) / radius

        if not positioned_chars:
            return None

        # Combine all positioned characters
        return self._combine_objects(positioned_chars)

    def _combine_objects(self, objects: List[cq.Workplane]) -> cq.Workplane:
        """Combine multiple CadQuery objects into one using compound."""
        if len(objects) == 1:
            return objects[0]

        from OCP.TopoDS import TopoDS_Compound
        from OCP.BRep import BRep_Builder

        all_shapes = []
        for obj in objects:
            try:
                val = obj.val()
                if hasattr(val, 'wrapped'):
                    shape = val.wrapped
                else:
                    shape = val
                all_shapes.append(shape)
            except Exception as e:
                print(f"[SweepingText] Error getting shape: {e}")

        if not all_shapes:
            return objects[0] if objects else cq.Workplane("XY")

        # Create compound
        builder = BRep_Builder()
        compound = TopoDS_Compound()
        builder.MakeCompound(compound)

        for shape in all_shapes:
            builder.Add(compound, shape)

        # Wrap in cq.Shape for proper CadQuery handling
        return cq.Workplane("XY").newObject([cq.Shape(compound)])


@dataclass
class RevolvedTextConfig:
    """Configuration for revolve-based sweeping text (like OpenSCAD rotate_extrude)."""
    sweep_radius: float = 13.0   # mm - distance from center axis (text_excenter)
    sweep_angle: float = 65.0    # degrees - angle to sweep (cutangle)
    sweep_direction: str = "up"  # "up" or "down"
    text_config: TextConfig = field(default_factory=TextConfig)
    base_height: float = 1.0     # mm - thickness of the base


class RevolvedTextBuilder:
    """
    Creates text that wraps around a cylindrical surface using revolve.

    This matches the OpenSCAD rotate_extrude effect where:
    1. 2D text profile is created
    2. Offset from center axis by sweep_radius
    3. Revolved around axis by sweep_angle degrees

    The result is text that appears wrapped around a section of a cylinder.
    """

    def __init__(self, config: Optional[RevolvedTextConfig] = None):
        self.config = config or RevolvedTextConfig()

    def generate(self, config: Optional[RevolvedTextConfig] = None) -> Tuple[cq.Workplane, Tuple[float, float, float, float]]:
        """
        Generate revolved/swept 3D text geometry.

        Returns:
            Tuple of (CadQuery Workplane with text solid, bounding box)
        """
        cfg = config or self.config
        text_cfg = cfg.text_config

        print(f"[RevolvedText] Starting: radius={cfg.sweep_radius}, angle={cfg.sweep_angle}, direction={cfg.sweep_direction}")

        if not text_cfg.lines or all(not line.has_content() for line in text_cfg.lines):
            print("[RevolvedText] No content, returning empty")
            return cq.Workplane("XY"), (0, 0, 0, 0)

        # Filter to non-empty lines
        active_lines = [line for line in text_cfg.lines if line.has_content()]
        if not active_lines:
            return cq.Workplane("XY"), (0, 0, 0, 0)

        try:
            # Create 2D text profiles for all lines
            all_text_profiles = []
            total_height = 0
            line_heights = []

            for line_idx, line_cfg in enumerate(active_lines):
                segments = line_cfg.get_effective_segments()
                if not segments:
                    continue

                # Combine all segment text into one line
                line_text = ""
                max_font_size = 0
                font_family = "Arial"
                font_path = None

                for seg in segments:
                    line_text += seg.content
                    if seg.font_size > max_font_size:
                        max_font_size = seg.font_size
                        font_family = seg.font_family
                        font_path = seg.font_path

                if not line_text.strip():
                    continue

                line_heights.append(max_font_size)
                total_height += max_font_size

            # Add spacing between lines
            line_spacing = text_cfg.line_spacing
            if len(line_heights) > 1:
                avg_height = sum(line_heights) / len(line_heights)
                total_height += (len(line_heights) - 1) * avg_height * (line_spacing - 1)

            # Generate each line and position vertically
            current_y = total_height / 2
            positioned_profiles = []

            for line_idx, line_cfg in enumerate(active_lines):
                segments = line_cfg.get_effective_segments()
                if not segments:
                    continue

                line_text = "".join(seg.content for seg in segments)
                if not line_text.strip():
                    continue

                # Get font settings from first segment with content
                seg = next((s for s in segments if s.content.strip()), segments[0])
                font_size = seg.font_size
                font_family = seg.font_family
                font_path = seg.font_path

                # Create 2D text outline (as a very thin extrusion we'll use for revolve)
                # CadQuery text() creates 3D, so we use minimal depth and revolve that
                text_params = {
                    'fontsize': font_size,
                    'distance': 0.1,  # Minimal depth - we'll revolve this
                    'font': font_family,
                    'kind': seg.get_cadquery_kind(),
                    'halign': 'center',
                    'valign': 'center',
                    'combine': True
                }
                if font_path and font_path.exists():
                    text_params['fontPath'] = str(font_path)

                # Create thin text profile
                text_profile = cq.Workplane("XY").text(line_text, **text_params)

                # Position this line vertically
                line_center_y = current_y - font_size / 2
                text_profile = text_profile.translate((0, line_center_y, 0))
                positioned_profiles.append(text_profile)

                # Move to next line position
                current_y -= font_size
                if line_idx < len(active_lines) - 1:
                    current_y -= font_size * (line_spacing - 1)

            if not positioned_profiles:
                return cq.Workplane("XY"), (0, 0, 0, 0)

            # Combine all line profiles
            combined_profile = self._combine_objects(positioned_profiles)

            # Now revolve the text around the Y axis
            # The text needs to be positioned in the XZ plane, offset from the Y axis
            # Then revolved around Y

            # Rotate text to XZ plane (from XY to XZ)
            rotated_text = combined_profile.rotate((0, 0, 0), (1, 0, 0), 90)

            # Translate outward from Y axis by sweep_radius
            # Direction determines if we translate in +X or account for which way curves
            offset_x = cfg.sweep_radius
            translated_text = rotated_text.translate((offset_x, 0, 0))

            # Create the revolved geometry using revolve
            # Since CadQuery doesn't have a simple partial revolve on arbitrary workplanes,
            # we'll use a different approach: create the geometry character by character
            # positioned along the arc with radial extrusion

            # Alternative approach: position text along arc with proper 3D orientation
            result = self._create_revolved_text(cfg, active_lines, text_cfg.depth)

            if result is None:
                return cq.Workplane("XY"), (0, 0, 0, 0)

            # Calculate bounding box
            try:
                bb = result.val().BoundingBox()
                bbox = (bb.xmin, bb.ymin, bb.xmax, bb.ymax)
                print(f"[RevolvedText] BBox: {bbox}")
            except Exception as e:
                print(f"[RevolvedText] BBox error: {e}")
                bbox = (-50, -30, 50, 30)

            return result, bbox

        except Exception as e:
            import traceback
            print(f"[RevolvedText] ERROR: {e}")
            traceback.print_exc()
            return cq.Workplane("XY"), (0, 0, 0, 0)

    def _create_revolved_text(self, cfg: RevolvedTextConfig, active_lines: List,
                               depth: float) -> Optional[cq.Workplane]:
        """
        Create text that appears wrapped around a cylindrical surface.

        Replicates the OpenSCAD rotate_extrude effect:
        1. Text is created in XY plane
        2. Rotated to stand vertical (around X axis by 90°)
        3. Positioned at distance sweep_radius from the rotation axis
        4. Each character is rotated around the vertical axis to follow the arc

        For "up" direction: edges of text curve upward
        For "down" direction: edges curve downward
        """
        text_cfg = cfg.text_config
        sweep_radius = cfg.sweep_radius
        sweep_angle_deg = cfg.sweep_angle
        direction = cfg.sweep_direction

        print(f"[RevolvedText] Creating revolved text: radius={sweep_radius}, angle={sweep_angle_deg}, dir={direction}")

        # Calculate total text height for vertical positioning
        line_heights = []
        for line_cfg in active_lines:
            segments = line_cfg.get_effective_segments()
            if segments:
                max_size = max(s.font_size for s in segments)
                line_heights.append(max_size)

        total_height = sum(line_heights)
        line_spacing = text_cfg.line_spacing
        if len(line_heights) > 1:
            avg_height = sum(line_heights) / len(line_heights)
            total_height += (len(line_heights) - 1) * avg_height * (line_spacing - 1)

        all_chars = []

        # Current vertical position (Y in final output, starting from top)
        current_text_y = total_height / 2

        for line_idx, line_cfg in enumerate(active_lines):
            segments = line_cfg.get_effective_segments()
            if not segments:
                continue

            # Get all characters with their properties
            line_chars = []
            for seg in segments:
                for char in seg.content:
                    line_chars.append((char, seg))

            if not line_chars:
                continue

            font_size = line_chars[0][1].font_size

            # Measure actual character widths by creating temporary geometry
            char_widths = []
            char_objects = []
            for char, seg in line_chars:
                if char == ' ':
                    char_widths.append(seg.font_size * 0.3)
                    char_objects.append(None)
                else:
                    try:
                        text_params = {
                            'fontsize': seg.font_size,
                            'distance': depth,
                            'font': seg.font_family,
                            'kind': seg.get_cadquery_kind(),
                            'halign': 'center',
                            'valign': 'center',
                            'combine': True
                        }
                        if seg.font_path and seg.font_path.exists():
                            text_params['fontPath'] = str(seg.font_path)

                        char_obj = cq.Workplane("XY").text(char, **text_params)
                        bb = char_obj.val().BoundingBox()
                        width = bb.xmax - bb.xmin
                        char_widths.append(width)
                        char_objects.append(char_obj)
                    except Exception as e:
                        print(f"[RevolvedText] Error measuring char '{char}': {e}")
                        char_widths.append(seg.font_size * 0.6)
                        char_objects.append(None)

            total_line_width = sum(char_widths)
            print(f"[RevolvedText] Line {line_idx}: {len(line_chars)} chars, total width={total_line_width:.1f}mm")

            # Convert total width to arc angle
            # Arc length = radius * angle, so angle = arc_length / radius
            max_angle_rad = math.radians(sweep_angle_deg / 2)

            # Scale characters to fit within sweep angle
            arc_length_available = sweep_radius * 2 * max_angle_rad
            scale = min(1.0, arc_length_available / total_line_width) if total_line_width > 0 else 1.0

            print(f"[RevolvedText] Arc available: {arc_length_available:.1f}mm, scale: {scale:.2f}")

            # Position each character along the arc
            cumulative_width = 0
            line_y_pos = current_text_y - font_size / 2
            total_scaled_width = total_line_width * scale

            for i, ((char, seg), width, char_obj) in enumerate(zip(line_chars, char_widths, char_objects)):
                if char == ' ':
                    cumulative_width += width
                    continue

                # Character X position: normal left-to-right reading, centered
                char_center = cumulative_width + width / 2
                char_x = (char_center - total_line_width / 2) * scale

                # Normalized position from center: -0.5 to +0.5
                normalized_pos = (char_center / total_line_width) - 0.5 if total_line_width > 0 else 0

                # Calculate angle from center position
                char_angle_rad = normalized_pos * math.radians(sweep_angle_deg)

                # Sweeping effect: flat front face with angled extrusion
                #
                # The front face of the text remains flat (all at same Y plane).
                # The extrusion direction is angled based on position:
                # - Center: extrusion goes straight back (in +Z direction)
                # - Edges: extrusion is tilted up/down following the sweep arc
                #
                # The tilt angle determines how much the extrusion is angled.
                # For "up" direction: left edge tilts up-left, right edge tilts up-right
                # This creates the sweeping arc effect in the extrusion.

                # Calculate the tilt angle for this character's extrusion
                # The angle is proportional to the character's position from center
                tilt_angle_deg = math.degrees(char_angle_rad)

                # For "down" direction, invert the tilt
                if direction == "down":
                    tilt_angle_deg = -tilt_angle_deg

                all_chars.append({
                    'char': char,
                    'seg': seg,
                    'x': char_x,  # X position (reading direction)
                    'y': line_y_pos,  # Y position (same for all chars - flat front)
                    'z': 0,  # Z=0 for front face (extrusion goes into +Z then tilts)
                    'tilt_x': tilt_angle_deg,  # Tilt angle for extrusion direction
                    'depth': depth,
                    'char_obj': char_obj,
                })
                print(f"[RevolvedText] Char '{char}': x={char_x:.2f}, tilt={tilt_angle_deg:.1f}°")

                cumulative_width += width

            # Move to next line
            current_text_y -= font_size
            if line_idx < len(active_lines) - 1:
                current_text_y -= font_size * (line_spacing - 1)

        if not all_chars:
            return None

        print(f"[RevolvedText] Generating {len(all_chars)} character geometries")

        # Generate 3D geometry for each character
        char_geometries = []
        for char_info in all_chars:
            char = char_info['char']
            seg = char_info['seg']

            if char.strip() == '':
                continue

            try:
                char_obj = char_info.get('char_obj')
                if char_obj is None:
                    text_params = {
                        'fontsize': seg.font_size,
                        'distance': char_info['depth'],
                        'font': seg.font_family,
                        'kind': seg.get_cadquery_kind(),
                        'halign': 'center',
                        'valign': 'center',
                        'combine': True
                    }
                    if seg.font_path and seg.font_path.exists():
                        text_params['fontPath'] = str(seg.font_path)
                    char_obj = cq.Workplane("XY").text(char, **text_params)

                # Sweeping effect: flat front face, angled extrusion
                #
                # The text front face remains flat and readable.
                # The extrusion (depth) goes at an angle following the sweep arc.
                #
                # For "up" direction:
                # - Center character: extrusion goes straight back (+Z after rotation)
                # - Edge characters: extrusion angles upward following the cylinder
                #
                # We achieve this by:
                # 1. Rotating the extruded text so the extrusion direction is angled
                # 2. But keeping the front face aligned

                tilt_angle = char_info.get('tilt_x', 0)

                # The character was created with extrusion in +Z direction.
                # We need to rotate it so the extrusion follows the sweep angle,
                # but from the viewer's perspective the front face stays readable.
                #
                # Rotate around the character's own X axis by the tilt angle.
                # This tips the extrusion up/down while the face stays in the XY plane.
                if abs(tilt_angle) > 0.1:
                    char_obj = char_obj.rotate((0, 0, 0), (1, 0, 0), -tilt_angle)

                # Translate to position (x along reading direction, y for line, z stays at 0)
                char_obj = char_obj.translate((
                    char_info['x'],
                    char_info['y'],
                    0  # Front face stays at Z=0
                ))

                char_geometries.append(char_obj)

            except Exception as e:
                print(f"[RevolvedText] Error creating char '{char}': {e}")
                continue

        if not char_geometries:
            return None

        print(f"[RevolvedText] Combining {len(char_geometries)} character geometries")

        # Combine all characters
        return self._combine_objects(char_geometries)

    def _combine_objects(self, objects: List[cq.Workplane]) -> cq.Workplane:
        """Combine multiple CadQuery objects into one using compound."""
        if len(objects) == 1:
            return objects[0]

        from OCP.TopoDS import TopoDS_Compound
        from OCP.BRep import BRep_Builder

        all_shapes = []
        for obj in objects:
            try:
                val = obj.val()
                if hasattr(val, 'wrapped'):
                    shape = val.wrapped
                else:
                    shape = val
                all_shapes.append(shape)
            except Exception as e:
                print(f"[RevolvedText] Error getting shape: {e}")

        if not all_shapes:
            return objects[0] if objects else cq.Workplane("XY")

        builder = BRep_Builder()
        compound = TopoDS_Compound()
        builder.MakeCompound(compound)

        for shape in all_shapes:
            builder.Add(compound, shape)

        return cq.Workplane("XY").newObject([cq.Shape(compound)])


def generate_sweeping_nameplate(
    line1_text: str = "First Line",
    line2_text: str = "Second Line",
    font_size1: float = 14.0,
    font_size2: float = 10.0,
    curve_radius: float = 80.0,
    curve_angle: float = 60.0,
    text_depth: float = 2.0,
    font_family: str = "Arial",
    line_gap: float = 2.0,
) -> Tuple[cq.Workplane, Tuple[float, float, float, float]]:
    """
    Convenience function to generate a sweeping 2-line nameplate.

    Args:
        line1_text: Text for the first (top) line
        line2_text: Text for the second (bottom) line
        font_size1: Font size for first line
        font_size2: Font size for second line
        curve_radius: Radius of the text arc (larger = flatter curve)
        curve_angle: Maximum angle the text can span
        text_depth: Extrusion depth
        font_family: Font to use
        line_gap: Gap between lines

    Returns:
        Tuple of (geometry, bounding_box)
    """
    # Build text config
    text_cfg = TextConfig(
        lines=[
            TextLineConfig(segments=[
                TextSegment(content=line1_text, font_size=font_size1, font_family=font_family)
            ]),
            TextLineConfig(segments=[
                TextSegment(content=line2_text, font_size=font_size2, font_family=font_family)
            ]),
        ],
        depth=text_depth,
        style=TextStyle.RAISED,
    )

    # Build sweeping config
    sweep_cfg = SweepingTextConfig(
        curve_radius=curve_radius,
        curve_angle=curve_angle,
        text_config=text_cfg,
        line_gap=line_gap,
    )

    builder = SweepingTextBuilder(sweep_cfg)
    return builder.generate()
