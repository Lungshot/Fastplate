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
class TextLineConfig:
    """Configuration for a single line of text."""
    content: str = ""
    font_family: str = "Arial"
    font_path: Optional[Path] = None
    font_style: str = "Regular"  # Regular, Bold, Italic, Bold Italic
    font_size: float = 12.0      # mm height
    letter_spacing: float = 0.0   # Additional spacing between letters (%)
    
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
        
        if not cfg.lines or all(not line.content for line in cfg.lines):
            # Return empty workplane and zero bbox if no text
            return cq.Workplane("XY"), (0, 0, 0, 0)
        
        # Filter to non-empty lines
        active_lines = [line for line in cfg.lines if line.content.strip()]
        
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
                # Use the larger of the two font sizes for consistent spacing
                avg_size = (active_lines[i-1].font_size + line_cfg.font_size) / 2
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
        
        # Combine all lines
        if len(positioned_objects) == 1:
            combined = positioned_objects[0]
        else:
            combined = positioned_objects[0]
            for obj in positioned_objects[1:]:
                try:
                    combined = combined.union(obj)
                except:
                    # If union fails, try to add as separate solid
                    pass
        
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
        """Generate a single line of 3D text."""
        if not line_cfg.content.strip():
            return None, (0, 0, 0, 0)
        
        try:
            # Build text parameters
            text_params = {
                'fontsize': line_cfg.font_size,
                'distance': depth,
                'font': line_cfg.font_family,
                'kind': line_cfg.get_cadquery_kind(),
                'halign': 'center',
                'valign': 'center',
                'combine': True
            }
            
            # Add font path if specified
            if line_cfg.font_path and line_cfg.font_path.exists():
                text_params['fontPath'] = str(line_cfg.font_path)
            
            # Create text
            text_obj = cq.Workplane("XY").text(
                line_cfg.content,
                **text_params
            )
            
            # Get bounding box
            try:
                bb = text_obj.val().BoundingBox()
                bbox = (bb.xmin, bb.ymin, bb.xmax, bb.ymax)
            except:
                # Estimate based on font size and character count
                est_width = len(line_cfg.content) * line_cfg.font_size * 0.6
                est_height = line_cfg.font_size
                bbox = (-est_width/2, -est_height/2, est_width/2, est_height/2)
            
            return text_obj, bbox
            
        except Exception as e:
            print(f"Error generating text '{line_cfg.content}': {e}")
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
