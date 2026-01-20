"""
Text Builder
Creates 3D text geometry using CadQuery with support for custom fonts.
"""

import cadquery as cq
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from pathlib import Path

from .shape_utils import create_compound, combine_workplanes


class TextStyle(Enum):
    """Text extrusion styles."""
    RAISED = "raised"       # Text protrudes above base
    ENGRAVED = "engraved"   # Text is cut into base (debossed)
    CUTOUT = "cutout"       # Text cuts through entirely
    SWEEPING = "sweeping"   # Text wrapped around cylindrical surface (like OpenSCAD rotate_extrude)


class TextAlign(Enum):
    """Text horizontal alignment."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class TextVAlign(Enum):
    """Text vertical alignment."""
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"


class TextOrientation(Enum):
    """Text orientation on the plate."""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class TextEffect(Enum):
    """Text visual effects."""
    NONE = "none"
    BEVEL = "bevel"       # Chamfered top edges
    ROUNDED = "rounded"   # Filleted top edges
    OUTLINE = "outline"   # Hollow/outline text


@dataclass
class TextSegment:
    """A segment of text within a line, with its own font settings."""
    content: str = ""
    font_family: str = "Arial"
    font_path: Optional[Path] = None
    font_style: str = "Regular"  # Regular, Bold, Italic, Bold Italic
    font_size: float = 12.0      # mm height
    letter_spacing: float = 0.0  # Additional spacing between letters (%)
    vertical_offset: float = 0.0 # mm vertical offset (positive = up, negative = down)
    is_icon: bool = False        # True if this is a Nerd Font icon

    def get_cadquery_kind(self) -> str:
        """Convert font style to CadQuery kind parameter."""
        style_lower = self.font_style.lower()
        if 'bold' in style_lower and 'italic' in style_lower:
            return 'bold'  # CadQuery doesn't have bold-italic, use bold
        elif 'bold' in style_lower:
            return 'bold'
        elif 'italic' in style_lower:
            return 'italic'
        return 'regular'

    def to_dict(self) -> dict:
        """Serialize TextSegment to a dictionary."""
        return {
            'content': self.content,
            'font_family': self.font_family,
            'font_path': str(self.font_path) if self.font_path else None,
            'font_style': self.font_style,
            'font_size': self.font_size,
            'letter_spacing': self.letter_spacing,
            'vertical_offset': self.vertical_offset,
            'is_icon': self.is_icon,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TextSegment':
        """Deserialize TextSegment from a dictionary."""
        font_path = data.get('font_path')
        if font_path:
            font_path = Path(font_path)

        return cls(
            content=data.get('content', ''),
            font_family=data.get('font_family', 'Arial'),
            font_path=font_path,
            font_style=data.get('font_style', 'Regular'),
            font_size=data.get('font_size', 12.0),
            letter_spacing=data.get('letter_spacing', 0.0),
            vertical_offset=data.get('vertical_offset', 0.0),
            is_icon=data.get('is_icon', False),
        )


@dataclass
class TextLineConfig:
    """Configuration for a single line of text with multiple segments."""
    # New segment-based format
    segments: List[TextSegment] = field(default_factory=list)
    segment_gap: float = 2.0  # mm gap between segments

    # Legacy single-segment properties (for backward compatibility)
    content: str = ""
    font_family: str = "Arial"
    font_path: Optional[Path] = None
    font_style: str = "Regular"
    font_size: float = 12.0
    letter_spacing: float = 0.0

    def get_cadquery_kind(self) -> str:
        """Convert font style to CadQuery kind parameter (legacy support)."""
        style_lower = self.font_style.lower()
        if 'bold' in style_lower and 'italic' in style_lower:
            return 'bold'
        elif 'bold' in style_lower:
            return 'bold'
        elif 'italic' in style_lower:
            return 'italic'
        return 'regular'

    def get_effective_segments(self) -> List[TextSegment]:
        """Get segments, converting from legacy format if needed."""
        if self.segments:
            return self.segments
        # Convert legacy single-text format to segment
        if self.content:
            return [TextSegment(
                content=self.content,
                font_family=self.font_family,
                font_path=self.font_path,
                font_style=self.font_style,
                font_size=self.font_size,
                letter_spacing=self.letter_spacing
            )]
        return []

    def has_content(self) -> bool:
        """Check if the line has any content."""
        if self.segments:
            return any(s.content.strip() for s in self.segments)
        return bool(self.content.strip())

    def to_dict(self) -> dict:
        """Serialize TextLineConfig to a dictionary."""
        return {
            'segments': [seg.to_dict() for seg in self.segments],
            'segment_gap': self.segment_gap,
            'content': self.content,
            'font_family': self.font_family,
            'font_path': str(self.font_path) if self.font_path else None,
            'font_style': self.font_style,
            'font_size': self.font_size,
            'letter_spacing': self.letter_spacing,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TextLineConfig':
        """Deserialize TextLineConfig from a dictionary."""
        segments = [TextSegment.from_dict(s) for s in data.get('segments', [])]

        font_path = data.get('font_path')
        if font_path:
            font_path = Path(font_path)

        return cls(
            segments=segments,
            segment_gap=data.get('segment_gap', 2.0),
            content=data.get('content', ''),
            font_family=data.get('font_family', 'Arial'),
            font_path=font_path,
            font_style=data.get('font_style', 'Regular'),
            font_size=data.get('font_size', 12.0),
            letter_spacing=data.get('letter_spacing', 0.0),
        )


@dataclass
class TextConfig:
    """Configuration for text generation."""
    lines: List[TextLineConfig] = field(default_factory=lambda: [TextLineConfig()])

    # Overall text settings
    style: TextStyle = TextStyle.RAISED
    depth: float = 2.0           # mm - extrusion depth

    # Alignment
    halign: TextAlign = TextAlign.CENTER
    valign: TextVAlign = TextVAlign.CENTER

    # Orientation
    orientation: TextOrientation = TextOrientation.HORIZONTAL

    # Line spacing
    line_spacing: float = 1.2    # Multiplier of font size

    # Position offset
    offset_x: float = 0.0
    offset_y: float = 0.0

    # Text effects
    effect: TextEffect = TextEffect.NONE
    effect_size: float = 0.3     # mm - size of bevel/fillet/outline
    outline_thickness: float = 1.0  # mm - thickness for outline mode

    # Arc/Sweeping text settings (used when style=SWEEPING or arc_enabled=True)
    arc_enabled: bool = False
    arc_radius: float = 50.0     # mm - radius of the text arc
    arc_angle: float = 180.0     # degrees - maximum angle the text can span
    arc_direction: str = "counterclockwise"  # counterclockwise or clockwise

    # Sweeping text specific settings (like OpenSCAD rotate_extrude)
    sweep_radius: float = 13.0   # mm - distance from center axis (text_excenter in OpenSCAD)
    sweep_angle: float = 65.0    # degrees - angle to sweep (cutangle in OpenSCAD)
    sweep_direction: str = "up"  # "up" = text top is highest, "down" = text bottom is highest

    def add_line(self, content: str = "", **kwargs) -> 'TextConfig':
        """Add a new text line."""
        line = TextLineConfig(content=content, **kwargs)
        self.lines.append(line)
        return self
    
    def get_line(self, index: int) -> Optional[TextLineConfig]:
        """Get a text line by index."""
        if 0 <= index < len(self.lines):
            return self.lines[index]
        return None

    def to_dict(self) -> dict:
        """Serialize TextConfig to a dictionary."""
        return {
            'lines': [line.to_dict() for line in self.lines],
            'style': self.style.value,
            'depth': self.depth,
            'halign': self.halign.value,
            'valign': self.valign.value,
            'orientation': self.orientation.value,
            'line_spacing': self.line_spacing,
            'offset_x': self.offset_x,
            'offset_y': self.offset_y,
            'effect': self.effect.value,
            'effect_size': self.effect_size,
            'outline_thickness': self.outline_thickness,
            'arc_enabled': self.arc_enabled,
            'arc_radius': self.arc_radius,
            'arc_angle': self.arc_angle,
            'arc_direction': self.arc_direction,
            'sweep_radius': self.sweep_radius,
            'sweep_angle': self.sweep_angle,
            'sweep_direction': self.sweep_direction,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TextConfig':
        """Deserialize TextConfig from a dictionary."""
        lines = [TextLineConfig.from_dict(l) for l in data.get('lines', [])]
        if not lines:
            lines = [TextLineConfig()]

        # Handle enum conversions
        style = data.get('style', 'raised')
        if isinstance(style, str):
            style = TextStyle(style)

        halign = data.get('halign', 'center')
        if isinstance(halign, str):
            halign = TextAlign(halign)

        valign = data.get('valign', 'center')
        if isinstance(valign, str):
            valign = TextVAlign(valign)

        orientation = data.get('orientation', 'horizontal')
        if isinstance(orientation, str):
            orientation = TextOrientation(orientation)

        effect = data.get('effect', 'none')
        if isinstance(effect, str):
            effect = TextEffect(effect)

        return cls(
            lines=lines,
            style=style,
            depth=data.get('depth', 2.0),
            halign=halign,
            valign=valign,
            orientation=orientation,
            line_spacing=data.get('line_spacing', 1.2),
            offset_x=data.get('offset_x', 0.0),
            offset_y=data.get('offset_y', 0.0),
            effect=effect,
            effect_size=data.get('effect_size', 0.3),
            outline_thickness=data.get('outline_thickness', 1.0),
            arc_enabled=data.get('arc_enabled', False),
            arc_radius=data.get('arc_radius', 50.0),
            arc_angle=data.get('arc_angle', 180.0),
            arc_direction=data.get('arc_direction', 'counterclockwise'),
            sweep_radius=data.get('sweep_radius', 13.0),
            sweep_angle=data.get('sweep_angle', 65.0),
            sweep_direction=data.get('sweep_direction', 'up'),
        )


class TextBuilder:
    """
    Builds 3D text geometry for nameplates.
    """
    
    def __init__(self, config: Optional[TextConfig] = None):
        self.config = config or TextConfig()
    
    def generate(self, config: Optional[TextConfig] = None) -> Tuple[cq.Workplane, Tuple[float, float, float, float]]:
        """
        Generate 3D text geometry.

        Args:
            config: Optional config override

        Returns:
            Tuple of (CadQuery Workplane with text solid, bounding box (minx, miny, maxx, maxy))
        """
        cfg = config or self.config

        if not cfg.lines or all(not line.has_content() for line in cfg.lines):
            # Return empty workplane and zero bbox if no text
            return cq.Workplane("XY"), (0, 0, 0, 0)

        # If arc/sweeping text is enabled, use the SweepingTextBuilder
        if cfg.arc_enabled:
            return self._generate_arc_text(cfg)

        # Filter to non-empty lines
        active_lines = [line for line in cfg.lines if line.has_content()]

        if not active_lines:
            return cq.Workplane("XY"), (0, 0, 0, 0)
        
        # Generate each line and combine
        line_objects = []
        line_bboxes = []
        
        for line_cfg in active_lines:
            text_obj, bbox = self._generate_line(line_cfg, cfg.depth)
            if text_obj is not None:
                line_objects.append(text_obj)
                line_bboxes.append(bbox)
        
        if not line_objects:
            return cq.Workplane("XY"), (0, 0, 0, 0)
        
        # Calculate total height and positions
        # Line spacing: gap between lines = average_font_size * (line_spacing - 1)
        total_height = 0
        line_heights = []
        gaps = []

        for i, (line_cfg, bbox) in enumerate(zip(active_lines, line_bboxes)):
            line_height = bbox[3] - bbox[1]  # max_y - min_y
            line_heights.append(line_height)
            total_height += line_height

            if i > 0:
                # Gap between this line and previous line
                # Use the max font size from segments for consistent spacing
                def get_max_font_size(line: TextLineConfig) -> float:
                    segments = line.get_effective_segments()
                    if segments:
                        return max(s.font_size for s in segments)
                    return line.font_size

                avg_size = (get_max_font_size(active_lines[i-1]) + get_max_font_size(line_cfg)) / 2
                gap = avg_size * (cfg.line_spacing - 1)
                gaps.append(gap)
                total_height += gap

        # Position lines vertically, centered around Y=0
        positioned_objects = []
        current_y = total_height / 2  # Start from top

        for i, (text_obj, bbox, line_height) in enumerate(zip(line_objects, line_bboxes, line_heights)):
            # Center of this line
            line_center_y = current_y - line_height / 2

            # Horizontal centering - account for bounding box offset
            line_center_x = (bbox[0] + bbox[2]) / 2
            offset_x = -line_center_x  # Center the line

            # Move the text to its position
            positioned = text_obj.translate((offset_x + cfg.offset_x, line_center_y + cfg.offset_y, 0))
            positioned_objects.append(positioned)

            # Move down to next line position
            current_y -= line_height
            if i < len(gaps):
                current_y -= gaps[i]
        
        # Combine all lines using compound to avoid union failures
        combined = combine_workplanes(positioned_objects)
        if combined is None:
            return cq.Workplane("XY"), (0, 0, 0, 0)
        
        # Apply vertical orientation if specified (rotate 90 degrees around Z)
        if cfg.orientation == TextOrientation.VERTICAL:
            combined = combined.rotate((0, 0, 0), (0, 0, 1), 90)

        # Apply text effects
        combined = self._apply_effects(combined, cfg)

        # Calculate overall bounding box
        try:
            bb = combined.val().BoundingBox()
            overall_bbox = (bb.xmin, bb.ymin, bb.xmax, bb.ymax)
        except:
            # Estimate if BoundingBox fails
            overall_bbox = (-50, -15, 50, 15)

        return combined, overall_bbox

    def _generate_arc_text(self, cfg: TextConfig) -> Tuple[cq.Workplane, Tuple[float, float, float, float]]:
        """Generate text that curves along an arc using SweepingTextBuilder."""
        from .sweeping_text import SweepingTextBuilder, SweepingTextConfig

        print(f"[ArcText] Generating arc text: radius={cfg.arc_radius}, angle={cfg.arc_angle}, direction={cfg.arc_direction}")

        # Build sweeping text config from text config
        sweep_cfg = SweepingTextConfig(
            curve_radius=cfg.arc_radius,
            curve_angle=cfg.arc_angle,
            text_config=cfg,
            text_on_outside=(cfg.arc_direction == "counterclockwise"),
        )

        builder = SweepingTextBuilder(sweep_cfg)
        geometry, bbox = builder.generate()

        print(f"[ArcText] Generated geometry: {geometry is not None}, bbox={bbox}")

        # Apply text effects if any
        geometry = self._apply_effects(geometry, cfg)

        return geometry, bbox

    def _apply_effects(self, geometry: cq.Workplane, cfg: TextConfig) -> cq.Workplane:
        """Apply text effects (bevel, rounded, outline) to the geometry.

        Handles both single solids and compound geometries by applying effects
        to each solid individually, then recombining.
        """
        if cfg.effect == TextEffect.NONE:
            return geometry

        try:
            # Get the underlying shape to check if it's a compound
            val = geometry.val()
            shape = val.wrapped if hasattr(val, 'wrapped') else val

            from OCP.TopoDS import TopoDS_Compound, TopoDS_Solid
            from OCP.TopExp import TopExp_Explorer
            from OCP.TopAbs import TopAbs_SOLID, TopAbs_COMPOUND
            from OCP.BRep import BRep_Builder

            # Check if it's a compound containing multiple solids
            # Use ShapeType() comparison which is more reliable than isinstance
            is_compound = shape.ShapeType() == TopAbs_COMPOUND

            if is_compound:
                # Extract individual solids from compound
                solids = []
                explorer = TopExp_Explorer(shape, TopAbs_SOLID)
                while explorer.More():
                    solid = explorer.Current()
                    solids.append(cq.Workplane("XY").newObject([cq.Shape(solid)]))
                    explorer.Next()

                if not solids:
                    return geometry

                # Apply effect to each solid
                effect_size = min(cfg.effect_size, cfg.depth * 0.4)  # Max 40% of depth
                processed_solids = []

                for solid_wp in solids:
                    try:
                        if cfg.effect == TextEffect.BEVEL and effect_size > 0.05:
                            processed = solid_wp.edges(">Z").chamfer(effect_size)
                        elif cfg.effect == TextEffect.ROUNDED and effect_size > 0.05:
                            processed = solid_wp.edges(">Z").fillet(effect_size)
                        elif cfg.effect == TextEffect.OUTLINE:
                            processed = solid_wp.shell(-cfg.outline_thickness)
                        else:
                            processed = solid_wp
                        processed_solids.append(processed)
                    except Exception as e:
                        # If effect fails on this solid, keep original
                        processed_solids.append(solid_wp)

                # Recombine processed solids into compound
                if len(processed_solids) == 1:
                    return processed_solids[0]

                builder = BRep_Builder()
                new_compound = TopoDS_Compound()
                builder.MakeCompound(new_compound)
                for proc_solid in processed_solids:
                    try:
                        proc_val = proc_solid.val()
                        proc_shape = proc_val.wrapped if hasattr(proc_val, 'wrapped') else proc_val
                        builder.Add(new_compound, proc_shape)
                    except:
                        pass

                return cq.Workplane("XY").newObject([cq.Shape(new_compound)])

            else:
                # Single solid - apply effect directly
                effect_size = min(cfg.effect_size, cfg.depth * 0.4)

                if cfg.effect == TextEffect.BEVEL and effect_size > 0.05:
                    return geometry.edges(">Z").chamfer(effect_size)
                elif cfg.effect == TextEffect.ROUNDED and effect_size > 0.05:
                    return geometry.edges(">Z").fillet(effect_size)
                elif cfg.effect == TextEffect.OUTLINE:
                    return geometry.shell(-cfg.outline_thickness)

        except Exception as e:
            # If effect fails, return original geometry
            print(f"Text effect error: {e}")

        return geometry
    
    def _generate_line(self, line_cfg: TextLineConfig, depth: float) -> Tuple[Optional[cq.Workplane], Tuple[float, float, float, float]]:
        """Generate a single line of 3D text, supporting multiple segments with different fonts."""
        segments = line_cfg.get_effective_segments()
        if not segments:
            return None, (0, 0, 0, 0)

        # Filter to non-empty segments
        active_segments = [s for s in segments if s.content.strip()]
        if not active_segments:
            return None, (0, 0, 0, 0)

        # If single segment with no letter spacing, use simple method
        if len(active_segments) == 1 and active_segments[0].letter_spacing == 0:
            return self._generate_single_segment(active_segments[0], depth)

        # Multi-segment rendering: generate each segment, then position them
        segment_objects = []
        segment_widths = []
        segment_heights = []

        for seg in active_segments:
            seg_obj, seg_bbox = self._generate_single_segment(seg, depth)
            if seg_obj is not None:
                segment_objects.append(seg_obj)
                seg_width = seg_bbox[2] - seg_bbox[0]
                seg_height = seg_bbox[3] - seg_bbox[1]
                segment_widths.append(seg_width)
                segment_heights.append(seg_height)
            else:
                # Estimate for failed segment
                segment_objects.append(None)
                segment_widths.append(len(seg.content) * seg.font_size * 0.6)
                segment_heights.append(seg.font_size)

        if not any(obj is not None for obj in segment_objects):
            return None, (0, 0, 0, 0)

        # Calculate total width including gaps
        gap = line_cfg.segment_gap
        total_width = sum(segment_widths) + gap * (len(active_segments) - 1)
        max_height = max(segment_heights) if segment_heights else 12.0

        # Position each segment horizontally
        positioned_segments = []
        current_x = -total_width / 2

        for seg, seg_obj, seg_width, seg_height in zip(active_segments, segment_objects, segment_widths, segment_heights):
            if seg_obj is not None:
                # Center segment at current position
                seg_center_x = current_x + seg_width / 2
                # Baseline alignment: all segments align at bottom (y=0), only user offset shifts them
                y_offset = seg.vertical_offset
                positioned = seg_obj.translate((seg_center_x, y_offset, 0))
                positioned_segments.append(positioned)

            current_x += seg_width + gap

        if not positioned_segments:
            return None, (0, 0, 0, 0)

        # Combine all segments using compound utility
        combined = combine_workplanes(positioned_segments)
        if combined is None:
            return None, (0, 0, 0, 0)

        # Calculate bounding box
        try:
            bb = combined.val().BoundingBox()
            bbox = (bb.xmin, bb.ymin, bb.xmax, bb.ymax)
        except:
            bbox = (-total_width/2, -max_height/2, total_width/2, max_height/2)

        return combined, bbox

    def _generate_single_segment(self, seg: TextSegment, depth: float) -> Tuple[Optional[cq.Workplane], Tuple[float, float, float, float]]:
        """Generate 3D text for a single segment."""
        if not seg.content.strip():
            return None, (0, 0, 0, 0)

        # If letter spacing is non-zero, use per-character rendering
        if seg.letter_spacing != 0:
            return self._generate_segment_with_spacing(seg, depth)

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

            text_obj = cq.Workplane("XY").text(seg.content, **text_params)

            try:
                bb = text_obj.val().BoundingBox()
                bbox = (bb.xmin, bb.ymin, bb.xmax, bb.ymax)
            except:
                est_width = len(seg.content) * seg.font_size * 0.6
                est_height = seg.font_size
                bbox = (-est_width/2, -est_height/2, est_width/2, est_height/2)

            return text_obj, bbox

        except Exception as e:
            print(f"Error generating segment '{seg.content}': {e}")
            return None, (0, 0, 0, 0)

    def _generate_segment_with_spacing(self, seg: TextSegment, depth: float) -> Tuple[Optional[cq.Workplane], Tuple[float, float, float, float]]:
        """Generate text for a segment with custom letter spacing by rendering each character."""
        text = seg.content.strip()
        if not text:
            return None, (0, 0, 0, 0)

        try:
            # Base text parameters
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

            # Calculate additional spacing per character (as percentage of font size)
            extra_spacing = seg.font_size * (seg.letter_spacing / 100.0)

            # Generate each character and measure its width
            char_objects = []
            char_widths = []

            for char in text:
                if char == ' ':
                    # Space character - estimate width
                    char_widths.append(seg.font_size * 0.3)
                    char_objects.append(None)
                else:
                    try:
                        char_obj = cq.Workplane("XY").text(char, **text_params)
                        bb = char_obj.val().BoundingBox()
                        width = bb.xmax - bb.xmin
                        char_widths.append(width)
                        char_objects.append(char_obj)
                    except:
                        # Fallback for failed character
                        char_widths.append(seg.font_size * 0.6)
                        char_objects.append(None)

            # Calculate total width with spacing
            total_width = sum(char_widths) + extra_spacing * (len(text) - 1)

            # Position each character and collect all solids
            positioned_chars = []
            current_x = -total_width / 2

            for i, (char_obj, width) in enumerate(zip(char_objects, char_widths)):
                if char_obj is not None:
                    # Position this character (center of character at current_x + width/2)
                    positioned = char_obj.translate((current_x + width / 2, 0, 0))
                    positioned_chars.append(positioned)

                # Move to next character position
                current_x += width
                if i < len(text) - 1:
                    current_x += extra_spacing

            if not positioned_chars:
                return None, (0, 0, 0, 0)

            # Combine all characters using compound utility
            combined = combine_workplanes(positioned_chars)
            if combined is None:
                return None, (0, 0, 0, 0)

            # Calculate bounding box
            try:
                bb = combined.val().BoundingBox()
                bbox = (bb.xmin, bb.ymin, bb.xmax, bb.ymax)
            except:
                bbox = (-total_width/2, -seg.font_size/2,
                        total_width/2, seg.font_size/2)

            return combined, bbox

        except Exception as e:
            print(f"Error generating text with spacing '{seg.content}': {e}")
            return None, (0, 0, 0, 0)
    
    def generate_icon(self, icon_char: str, font_path: Path, size: float, 
                      depth: float) -> Optional[cq.Workplane]:
        """
        Generate 3D geometry for a Nerd Font icon.
        
        Args:
            icon_char: The Unicode character for the icon
            font_path: Path to the Nerd Font file
            size: Size of the icon in mm
            depth: Extrusion depth in mm
            
        Returns:
            CadQuery Workplane with the icon, or None if failed.
        """
        try:
            text_obj = cq.Workplane("XY").text(
                icon_char,
                fontsize=size,
                distance=depth,
                fontPath=str(font_path),
                halign='center',
                valign='center',
                combine=True
            )
            return text_obj
        except Exception as e:
            print(f"Error generating icon: {e}")
            return None
    
    @staticmethod
    def get_text_bbox(text: str, font_size: float, font_family: str = "Arial",
                      font_path: Optional[Path] = None) -> Tuple[float, float, float, float]:
        """
        Calculate the bounding box of text without generating 3D geometry.
        
        Returns:
            (min_x, min_y, max_x, max_y)
        """
        try:
            params = {
                'fontsize': font_size,
                'distance': 0.1,  # Minimal depth
                'font': font_family,
                'halign': 'center',
                'valign': 'center',
            }
            
            if font_path and font_path.exists():
                params['fontPath'] = str(font_path)
            
            text_obj = cq.Workplane("XY").text(text, **params)
            bb = text_obj.val().BoundingBox()
            return (bb.xmin, bb.ymin, bb.xmax, bb.ymax)
        except:
            # Estimate
            est_width = len(text) * font_size * 0.6
            est_height = font_size
            return (-est_width/2, -est_height/2, est_width/2, est_height/2)
