"""
Advanced Text Layout
Provides advanced text layout options including vertical stacking, curved text,
and fine-grained spacing controls.
"""

import cadquery as cq
import math
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from enum import Enum
from pathlib import Path

from .shape_utils import create_compound, combine_workplanes


class VerticalTextMode(Enum):
    """Vertical text rendering modes."""
    ROTATED = "rotated"      # Horizontal text rotated 90 degrees
    STACKED = "stacked"      # Characters stacked vertically (top to bottom)
    STACKED_RTL = "stacked_rtl"  # Characters stacked right-to-left (for certain scripts)


class TextPathType(Enum):
    """Types of text paths."""
    LINEAR = "linear"        # Straight line
    ARC = "arc"             # Arc/curve
    CIRCLE = "circle"       # Full circle
    WAVE = "wave"           # Sinusoidal wave
    CUSTOM = "custom"       # Custom path from points


@dataclass
class TextSpacingConfig:
    """Fine-grained text spacing controls."""
    # Letter spacing (tracking)
    letter_spacing: float = 0.0    # Percentage of font size (0 = normal)

    # Word spacing
    word_spacing: float = 0.0      # Additional space for word gaps (mm)

    # Line height/spacing
    line_height: float = 1.2       # Multiplier of font size

    # Paragraph spacing (between blocks)
    paragraph_spacing: float = 0.0  # Additional mm between paragraphs

    # Kerning adjustment
    use_kerning: bool = True       # Use font's built-in kerning
    kerning_scale: float = 1.0     # Scale kerning (1.0 = default)

    # Baseline shift
    baseline_shift: float = 0.0    # mm - positive = up, negative = down

    # Horizontal scaling (stretching)
    horizontal_scale: float = 100.0  # Percentage (100 = normal)

    # Vertical scaling
    vertical_scale: float = 100.0    # Percentage (100 = normal)


@dataclass
class VerticalTextConfig:
    """Configuration for vertical text layout."""
    mode: VerticalTextMode = VerticalTextMode.ROTATED

    # For stacked mode
    char_spacing: float = 0.0       # Additional space between stacked characters (mm)
    char_rotation: float = 0.0      # Rotation applied to each character (degrees)

    # Alignment
    align: str = "center"           # left, center, right

    # Reading direction
    top_to_bottom: bool = True      # True = read top to bottom

    # Width for multi-column layout
    max_chars_per_column: int = 0   # 0 = unlimited (single column)


@dataclass
class CurvedTextConfig:
    """Configuration for text on a curved path."""
    path_type: TextPathType = TextPathType.LINEAR

    # Arc parameters
    radius: float = 50.0            # mm - radius for arc/circle
    start_angle: float = 0.0        # degrees - start position on arc
    end_angle: float = 180.0        # degrees - end position on arc

    # Wave parameters
    amplitude: float = 5.0          # mm - wave height
    frequency: float = 1.0          # cycles per 100mm

    # Common parameters
    char_rotation: str = "follow"   # "follow" path, "upright", or "fixed"
    spacing_mode: str = "uniform"   # "uniform" or "proportional"

    # Custom path points (for CUSTOM type)
    path_points: List[Tuple[float, float]] = field(default_factory=list)


class VerticalTextBuilder:
    """
    Builds vertical text geometry.
    """

    def generate(self, text: str, config: VerticalTextConfig,
                 font_family: str = "Arial", font_size: float = 12.0,
                 depth: float = 2.0, font_path: Optional[Path] = None) -> Optional[cq.Workplane]:
        """
        Generate vertical text geometry.

        Args:
            text: Text to render
            config: Vertical text configuration
            font_family: Font family name
            font_size: Font size in mm
            depth: Extrusion depth in mm
            font_path: Optional path to custom font file

        Returns:
            CadQuery Workplane with vertical text
        """
        if not text.strip():
            return None

        if config.mode == VerticalTextMode.ROTATED:
            return self._generate_rotated(text, font_family, font_size, depth, font_path)
        elif config.mode in (VerticalTextMode.STACKED, VerticalTextMode.STACKED_RTL):
            return self._generate_stacked(text, config, font_family, font_size, depth, font_path)

        return None

    def _generate_rotated(self, text: str, font_family: str, font_size: float,
                          depth: float, font_path: Optional[Path]) -> Optional[cq.Workplane]:
        """Generate text rotated 90 degrees."""
        try:
            params = {
                'fontsize': font_size,
                'distance': depth,
                'font': font_family,
                'halign': 'center',
                'valign': 'center',
                'combine': True
            }

            if font_path and font_path.exists():
                params['fontPath'] = str(font_path)

            text_obj = cq.Workplane("XY").text(text, **params)
            # Rotate 90 degrees
            return text_obj.rotate((0, 0, 0), (0, 0, 1), 90)

        except Exception as e:
            print(f"Error generating rotated text: {e}")
            return None

    def _generate_stacked(self, text: str, config: VerticalTextConfig,
                          font_family: str, font_size: float, depth: float,
                          font_path: Optional[Path]) -> Optional[cq.Workplane]:
        """Generate text with characters stacked vertically."""
        try:
            chars = list(text)
            if not chars:
                return None

            # Reverse if reading bottom to top
            if not config.top_to_bottom:
                chars = chars[::-1]

            # Generate each character
            char_objects = []
            char_heights = []

            params = {
                'fontsize': font_size,
                'distance': depth,
                'font': font_family,
                'halign': 'center',
                'valign': 'center',
                'combine': True
            }

            if font_path and font_path.exists():
                params['fontPath'] = str(font_path)

            for char in chars:
                if char == ' ':
                    # Space - just add height
                    char_heights.append(font_size * 0.5)
                    char_objects.append(None)
                elif char == '\n':
                    # Newline - handled separately for multi-column
                    char_heights.append(0)
                    char_objects.append(None)
                else:
                    try:
                        char_obj = cq.Workplane("XY").text(char, **params)

                        # Apply character rotation if specified
                        if config.char_rotation != 0:
                            char_obj = char_obj.rotate((0, 0, 0), (0, 0, 1), config.char_rotation)

                        # Get bounding box
                        try:
                            bb = char_obj.val().BoundingBox()
                            height = bb.ymax - bb.ymin
                        except:
                            height = font_size

                        char_heights.append(height)
                        char_objects.append(char_obj)

                    except Exception:
                        char_heights.append(font_size)
                        char_objects.append(None)

            # Calculate total height
            total_spacing = config.char_spacing * (len(chars) - 1)
            total_height = sum(char_heights) + total_spacing

            # Position each character vertically
            positioned_chars = []
            current_y = total_height / 2  # Start from top

            for char_obj, height in zip(char_objects, char_heights):
                if char_obj is not None:
                    # Position at current y (center of character)
                    char_center_y = current_y - height / 2
                    positioned = char_obj.translate((0, char_center_y, 0))
                    positioned_chars.append(positioned)

                # Move down
                current_y -= height + config.char_spacing

            if not positioned_chars:
                return None

            # Combine all characters using compound utility
            return combine_workplanes(positioned_chars)

        except Exception as e:
            print(f"Error generating stacked text: {e}")
            return None

    def get_stacked_dimensions(self, text: str, config: VerticalTextConfig,
                               font_size: float) -> Tuple[float, float]:
        """
        Calculate dimensions of stacked vertical text.

        Returns:
            (width, height) tuple in mm
        """
        chars = [c for c in text if c not in (' ', '\n')]
        if not chars:
            return (0, 0)

        # Width is approximately font size (single column)
        width = font_size

        # Height is characters * height + spacing
        char_height = font_size * 1.1  # Approximate
        total_height = len(chars) * char_height + config.char_spacing * (len(chars) - 1)

        return (width, total_height)


class CurvedTextBuilder:
    """
    Builds text along curved paths.
    """

    def generate(self, text: str, config: CurvedTextConfig,
                 font_family: str = "Arial", font_size: float = 12.0,
                 depth: float = 2.0, font_path: Optional[Path] = None) -> Optional[cq.Workplane]:
        """
        Generate text along a curved path.

        Args:
            text: Text to render
            config: Curved text configuration
            font_family: Font family name
            font_size: Font size in mm
            depth: Extrusion depth in mm
            font_path: Optional path to custom font file

        Returns:
            CadQuery Workplane with curved text
        """
        if not text.strip():
            return None

        if config.path_type == TextPathType.ARC:
            return self._generate_arc_text(text, config, font_family, font_size, depth, font_path)
        elif config.path_type == TextPathType.CIRCLE:
            return self._generate_circle_text(text, config, font_family, font_size, depth, font_path)
        elif config.path_type == TextPathType.WAVE:
            return self._generate_wave_text(text, config, font_family, font_size, depth, font_path)
        elif config.path_type == TextPathType.CUSTOM and config.path_points:
            return self._generate_custom_path_text(text, config, font_family, font_size, depth, font_path)

        return None

    def _generate_arc_text(self, text: str, config: CurvedTextConfig,
                           font_family: str, font_size: float, depth: float,
                           font_path: Optional[Path]) -> Optional[cq.Workplane]:
        """Generate text along an arc."""
        try:
            chars = list(text)
            if not chars:
                return None

            # Calculate angle span
            angle_span = config.end_angle - config.start_angle

            # Calculate angle per character
            if len(chars) > 1:
                angle_step = angle_span / (len(chars) - 1)
            else:
                angle_step = 0

            # Base text parameters
            params = {
                'fontsize': font_size,
                'distance': depth,
                'font': font_family,
                'halign': 'center',
                'valign': 'center',
                'combine': True
            }

            if font_path and font_path.exists():
                params['fontPath'] = str(font_path)

            # Generate and position each character
            positioned_chars = []

            for i, char in enumerate(chars):
                if char == ' ':
                    continue

                try:
                    # Calculate position on arc
                    angle = math.radians(config.start_angle + i * angle_step)
                    x = config.radius * math.cos(angle)
                    y = config.radius * math.sin(angle)

                    # Generate character
                    char_obj = cq.Workplane("XY").text(char, **params)

                    # Calculate rotation based on char_rotation mode
                    if config.char_rotation == "follow":
                        # Rotate to follow the arc tangent
                        rotation = config.start_angle + i * angle_step + 90
                    elif config.char_rotation == "upright":
                        rotation = 0
                    else:
                        rotation = float(config.char_rotation) if config.char_rotation.replace('.', '').replace('-', '').isdigit() else 0

                    # Apply rotation and translation
                    char_obj = char_obj.rotate((0, 0, 0), (0, 0, 1), rotation)
                    char_obj = char_obj.translate((x, y, 0))

                    positioned_chars.append(char_obj)

                except Exception:
                    pass

            return self._combine_chars(positioned_chars)

        except Exception as e:
            print(f"Error generating arc text: {e}")
            return None

    def _generate_circle_text(self, text: str, config: CurvedTextConfig,
                              font_family: str, font_size: float, depth: float,
                              font_path: Optional[Path]) -> Optional[cq.Workplane]:
        """Generate text around a full circle."""
        # Use arc text with 360 degree span
        circle_config = CurvedTextConfig(
            path_type=TextPathType.ARC,
            radius=config.radius,
            start_angle=0,
            end_angle=360 * (len(text) / (len(text) + 1)),  # Leave gap at end
            char_rotation=config.char_rotation,
            spacing_mode=config.spacing_mode
        )
        return self._generate_arc_text(text, circle_config, font_family, font_size, depth, font_path)

    def _generate_wave_text(self, text: str, config: CurvedTextConfig,
                            font_family: str, font_size: float, depth: float,
                            font_path: Optional[Path]) -> Optional[cq.Workplane]:
        """Generate text along a sinusoidal wave."""
        try:
            chars = list(text)
            if not chars:
                return None

            # Calculate text width
            estimated_width = len(chars) * font_size * 0.6

            # Base text parameters
            params = {
                'fontsize': font_size,
                'distance': depth,
                'font': font_family,
                'halign': 'center',
                'valign': 'center',
                'combine': True
            }

            if font_path and font_path.exists():
                params['fontPath'] = str(font_path)

            # Generate and position each character
            positioned_chars = []
            char_width = font_size * 0.6

            for i, char in enumerate(chars):
                if char == ' ':
                    continue

                try:
                    # Calculate position on wave
                    x = (i - len(chars) / 2) * char_width
                    # Sinusoidal y position
                    wave_x = x / 100.0 * config.frequency * 2 * math.pi
                    y = config.amplitude * math.sin(wave_x)

                    # Generate character
                    char_obj = cq.Workplane("XY").text(char, **params)

                    # Calculate rotation if following path
                    if config.char_rotation == "follow":
                        # Derivative of sine is cosine, so tangent angle is atan of derivative
                        derivative = config.amplitude * config.frequency * 2 * math.pi / 100.0 * math.cos(wave_x)
                        rotation = math.degrees(math.atan(derivative))
                    elif config.char_rotation == "upright":
                        rotation = 0
                    else:
                        rotation = float(config.char_rotation) if config.char_rotation.replace('.', '').replace('-', '').isdigit() else 0

                    # Apply rotation and translation
                    char_obj = char_obj.rotate((0, 0, 0), (0, 0, 1), rotation)
                    char_obj = char_obj.translate((x, y, 0))

                    positioned_chars.append(char_obj)

                except Exception:
                    pass

            return self._combine_chars(positioned_chars)

        except Exception as e:
            print(f"Error generating wave text: {e}")
            return None

    def _generate_custom_path_text(self, text: str, config: CurvedTextConfig,
                                   font_family: str, font_size: float, depth: float,
                                   font_path: Optional[Path]) -> Optional[cq.Workplane]:
        """Generate text along a custom path defined by points."""
        try:
            chars = list(text)
            points = config.path_points

            if not chars or len(points) < 2:
                return None

            # Calculate path length and positions
            path_lengths = [0.0]
            total_length = 0.0

            for i in range(1, len(points)):
                dx = points[i][0] - points[i-1][0]
                dy = points[i][1] - points[i-1][1]
                segment_length = math.sqrt(dx*dx + dy*dy)
                total_length += segment_length
                path_lengths.append(total_length)

            # Base text parameters
            params = {
                'fontsize': font_size,
                'distance': depth,
                'font': font_family,
                'halign': 'center',
                'valign': 'center',
                'combine': True
            }

            if font_path and font_path.exists():
                params['fontPath'] = str(font_path)

            # Generate and position each character
            positioned_chars = []

            for i, char in enumerate(chars):
                if char == ' ':
                    continue

                try:
                    # Calculate position along path
                    t = i / (len(chars) - 1) if len(chars) > 1 else 0
                    target_length = t * total_length

                    # Find which segment we're on
                    seg_idx = 0
                    for j in range(1, len(path_lengths)):
                        if path_lengths[j] >= target_length:
                            seg_idx = j - 1
                            break

                    # Interpolate position within segment
                    seg_start = path_lengths[seg_idx]
                    seg_end = path_lengths[seg_idx + 1] if seg_idx + 1 < len(path_lengths) else seg_start
                    seg_t = (target_length - seg_start) / (seg_end - seg_start) if seg_end > seg_start else 0

                    p1 = points[seg_idx]
                    p2 = points[seg_idx + 1] if seg_idx + 1 < len(points) else p1

                    x = p1[0] + seg_t * (p2[0] - p1[0])
                    y = p1[1] + seg_t * (p2[1] - p1[1])

                    # Generate character
                    char_obj = cq.Workplane("XY").text(char, **params)

                    # Calculate rotation
                    if config.char_rotation == "follow":
                        dx = p2[0] - p1[0]
                        dy = p2[1] - p1[1]
                        rotation = math.degrees(math.atan2(dy, dx))
                    elif config.char_rotation == "upright":
                        rotation = 0
                    else:
                        rotation = float(config.char_rotation) if config.char_rotation.replace('.', '').replace('-', '').isdigit() else 0

                    char_obj = char_obj.rotate((0, 0, 0), (0, 0, 1), rotation)
                    char_obj = char_obj.translate((x, y, 0))

                    positioned_chars.append(char_obj)

                except Exception:
                    pass

            return self._combine_chars(positioned_chars)

        except Exception as e:
            print(f"Error generating custom path text: {e}")
            return None

    def _combine_chars(self, char_objects: List[cq.Workplane]) -> Optional[cq.Workplane]:
        """Combine character workplanes into a single compound."""
        return combine_workplanes(char_objects)


class TextSpacingCalculator:
    """
    Calculates adjusted text metrics based on spacing configuration.
    """

    @staticmethod
    def apply_spacing(text: str, config: TextSpacingConfig,
                     base_font_size: float) -> Tuple[float, float]:
        """
        Calculate adjusted text dimensions with spacing applied.

        Args:
            text: Text string
            config: Spacing configuration
            base_font_size: Base font size in mm

        Returns:
            (adjusted_width, adjusted_height) tuple
        """
        if not text:
            return (0, 0)

        # Base character width estimate
        char_width = base_font_size * 0.6 * (config.horizontal_scale / 100.0)

        # Count characters and words
        char_count = len(text.replace(' ', ''))
        word_count = len(text.split())
        space_count = word_count - 1 if word_count > 0 else 0

        # Calculate width
        # Characters + letter spacing + word spacing
        letter_space = base_font_size * (config.letter_spacing / 100.0)
        total_letter_spacing = letter_space * (char_count - 1) if char_count > 1 else 0
        total_word_spacing = config.word_spacing * space_count

        width = (char_count * char_width +
                total_letter_spacing +
                total_word_spacing +
                space_count * char_width * 0.3)  # Base space width

        # Calculate height (single line)
        height = base_font_size * (config.vertical_scale / 100.0)

        return (width, height)

    @staticmethod
    def get_kerning_adjustment(char1: str, char2: str,
                              font_size: float,
                              kerning_scale: float = 1.0) -> float:
        """
        Get kerning adjustment between two characters.

        Note: This is a simplified approximation. Real kerning
        would require font file parsing.

        Returns:
            Adjustment in mm (negative = closer together)
        """
        # Common kerning pairs (simplified)
        kerning_pairs = {
            ('A', 'V'): -0.1,
            ('A', 'W'): -0.1,
            ('A', 'Y'): -0.1,
            ('A', 'T'): -0.05,
            ('L', 'T'): -0.08,
            ('L', 'V'): -0.08,
            ('L', 'W'): -0.08,
            ('L', 'Y'): -0.08,
            ('T', 'a'): -0.08,
            ('T', 'e'): -0.08,
            ('T', 'o'): -0.08,
            ('V', 'a'): -0.08,
            ('V', 'e'): -0.08,
            ('V', 'o'): -0.08,
            ('W', 'a'): -0.05,
            ('W', 'e'): -0.05,
            ('W', 'o'): -0.05,
            ('Y', 'a'): -0.1,
            ('Y', 'e'): -0.1,
            ('Y', 'o'): -0.1,
            ('f', 'f'): -0.02,
            ('f', 'i'): -0.02,
        }

        # Check both orders (symmetric for simplicity)
        pair = (char1.upper(), char2.upper())
        reverse_pair = (char2.upper(), char1.upper())

        adjustment = kerning_pairs.get(pair, 0) or kerning_pairs.get(reverse_pair, 0)

        return adjustment * font_size * kerning_scale


def create_text_with_spacing(text: str, spacing_config: TextSpacingConfig,
                            font_family: str = "Arial", font_size: float = 12.0,
                            depth: float = 2.0, font_path: Optional[Path] = None) -> Optional[cq.Workplane]:
    """
    Create 3D text with custom spacing applied.

    This is a convenience function that applies all spacing controls
    to generate properly spaced text.

    Args:
        text: Text to render
        spacing_config: Spacing configuration
        font_family: Font family name
        font_size: Base font size in mm
        depth: Extrusion depth in mm
        font_path: Optional path to custom font

    Returns:
        CadQuery Workplane with spaced text
    """
    if not text.strip():
        return None

    try:
        # Apply scaling to font size
        scaled_font_size = font_size * (spacing_config.vertical_scale / 100.0)

        # Base text parameters
        params = {
            'fontsize': scaled_font_size,
            'distance': depth,
            'font': font_family,
            'halign': 'center',
            'valign': 'center',
            'combine': True
        }

        if font_path and font_path.exists():
            params['fontPath'] = str(font_path)

        # If no special spacing needed, use simple text
        if (spacing_config.letter_spacing == 0 and
            spacing_config.word_spacing == 0 and
            spacing_config.horizontal_scale == 100.0 and
            spacing_config.baseline_shift == 0):
            text_obj = cq.Workplane("XY").text(text, **params)
            return text_obj

        # Generate each character separately for custom spacing
        chars = list(text)
        char_objects = []
        char_widths = []

        # Calculate letter spacing in mm
        letter_space = font_size * (spacing_config.letter_spacing / 100.0)

        for char in chars:
            if char == ' ':
                # Space width + word spacing
                space_width = font_size * 0.3 * (spacing_config.horizontal_scale / 100.0)
                char_widths.append(space_width + spacing_config.word_spacing)
                char_objects.append(None)
            else:
                try:
                    char_obj = cq.Workplane("XY").text(char, **params)

                    # Apply horizontal scaling
                    if spacing_config.horizontal_scale != 100.0:
                        scale_factor = spacing_config.horizontal_scale / 100.0
                        char_obj = char_obj.scale((scale_factor, 1.0, 1.0))

                    # Get width
                    try:
                        bb = char_obj.val().BoundingBox()
                        width = bb.xmax - bb.xmin
                    except:
                        width = font_size * 0.6 * (spacing_config.horizontal_scale / 100.0)

                    char_widths.append(width)
                    char_objects.append(char_obj)
                except:
                    char_widths.append(font_size * 0.6)
                    char_objects.append(None)

        # Apply kerning if enabled
        if spacing_config.use_kerning:
            for i in range(len(chars) - 1):
                if chars[i] != ' ' and chars[i+1] != ' ':
                    kern = TextSpacingCalculator.get_kerning_adjustment(
                        chars[i], chars[i+1], font_size, spacing_config.kerning_scale
                    )
                    char_widths[i] += kern

        # Calculate total width
        total_width = sum(char_widths) + letter_space * (len(chars) - 1)

        # Position each character
        positioned_chars = []
        current_x = -total_width / 2

        for i, (char_obj, width) in enumerate(zip(char_objects, char_widths)):
            if char_obj is not None:
                # Position character
                x = current_x + width / 2
                y = spacing_config.baseline_shift
                positioned = char_obj.translate((x, y, 0))
                positioned_chars.append(positioned)

            current_x += width
            if i < len(chars) - 1:
                current_x += letter_space

        if not positioned_chars:
            return None

        # Combine characters using compound utility
        return combine_workplanes(positioned_chars)

    except Exception as e:
        print(f"Error creating text with spacing: {e}")
        return None
