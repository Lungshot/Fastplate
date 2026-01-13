"""
Text Builder
Creates 3D text geometry using CadQuery with support for custom fonts.
"""

import cadquery as cq
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from pathlib import Path


class TextStyle(Enum):
    """Text extrusion styles."""
    RAISED = "raised"       # Text protrudes above base
    ENGRAVED = "engraved"   # Text is cut into base (debossed)
    CUTOUT = "cutout"       # Text cuts through entirely


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
        if len(positioned_objects) == 1:
            combined = positioned_objects[0]
        else:
            # Collect all solids from all positioned objects
            all_solids = []
            for obj in positioned_objects:
                try:
                    solids = obj.solids().vals()
                    all_solids.extend(solids)
                except:
                    try:
                        # Try getting single solid
                        all_solids.append(obj.val())
                    except:
                        pass

            if all_solids:
                # Create compound from all solids
                from OCP.TopoDS import TopoDS_Compound
                from OCP.BRep import BRep_Builder
                builder = BRep_Builder()
                compound = TopoDS_Compound()
                builder.MakeCompound(compound)
                for solid in all_solids:
                    # Extract OCP shape from CadQuery object
                    shape = solid.wrapped if hasattr(solid, 'wrapped') else solid
                    builder.Add(compound, shape)
                combined = cq.Workplane("XY").newObject([compound])
            else:
                combined = positioned_objects[0]
        
        # Apply vertical orientation if specified (rotate 90 degrees around Z)
        if cfg.orientation == TextOrientation.VERTICAL:
            combined = combined.rotate((0, 0, 0), (0, 0, 1), 90)

        # Calculate overall bounding box
        try:
            bb = combined.val().BoundingBox()
            overall_bbox = (bb.xmin, bb.ymin, bb.xmax, bb.ymax)
        except:
            # Estimate if BoundingBox fails
            overall_bbox = (-50, -15, 50, 15)

        return combined, overall_bbox
    
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
                # Align to baseline (bottom of tallest segment) + vertical offset
                y_offset = (max_height - seg_height) / 2 + seg.vertical_offset
                positioned = seg_obj.translate((seg_center_x, y_offset, 0))
                positioned_segments.append(positioned)

            current_x += seg_width + gap

        if not positioned_segments:
            return None, (0, 0, 0, 0)

        # Combine all segments using compound
        if len(positioned_segments) == 1:
            combined = positioned_segments[0]
        else:
            # Collect all shapes from positioned segments
            from OCP.TopoDS import TopoDS_Compound
            from OCP.BRep import BRep_Builder

            all_shapes = []
            for i, obj in enumerate(positioned_segments):
                try:
                    # Get the underlying shape value
                    val = obj.val()
                    if hasattr(val, 'wrapped'):
                        shape = val.wrapped
                    else:
                        shape = val
                    all_shapes.append(shape)
                    print(f"[TextBuilder] Segment {i}: got shape type {type(shape).__name__}")
                except Exception as e:
                    print(f"[TextBuilder] Segment {i}: failed to get shape: {e}")

            if all_shapes:
                print(f"[TextBuilder] Combining {len(all_shapes)} shapes into compound")
                builder = BRep_Builder()
                compound = TopoDS_Compound()
                builder.MakeCompound(compound)
                for shape in all_shapes:
                    builder.Add(compound, shape)
                combined = cq.Workplane("XY").newObject([cq.Shape(compound)])
            else:
                print("[TextBuilder] WARNING: No shapes found, using first segment only")
                combined = positioned_segments[0]

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

            # Combine all characters using compound to avoid union failures
            if len(positioned_chars) == 1:
                combined = positioned_chars[0]
            else:
                all_solids = []
                for obj in positioned_chars:
                    try:
                        solids = obj.solids().vals()
                        all_solids.extend(solids)
                    except:
                        try:
                            all_solids.append(obj.val())
                        except:
                            pass

                if all_solids:
                    from OCP.TopoDS import TopoDS_Compound
                    from OCP.BRep import BRep_Builder
                    builder = BRep_Builder()
                    compound = TopoDS_Compound()
                    builder.MakeCompound(compound)
                    for solid in all_solids:
                        # Extract OCP shape from CadQuery object
                        shape = solid.wrapped if hasattr(solid, 'wrapped') else solid
                        builder.Add(compound, shape)
                    combined = cq.Workplane("XY").newObject([compound])
                else:
                    combined = positioned_chars[0]

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
