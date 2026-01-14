"""
Measurement Overlay
Shows dimension annotations on the 3D preview.
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRect, QPoint, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QFontMetrics
from dataclasses import dataclass
from typing import List, Optional, Tuple
import math


@dataclass
class Dimension:
    """Represents a dimension measurement."""
    start: Tuple[float, float]    # Start point (x, y)
    end: Tuple[float, float]      # End point (x, y)
    value: float                   # Dimension value in mm
    label: str = ""               # Optional label
    orientation: str = "horizontal"  # horizontal, vertical, diagonal
    offset: float = 20.0          # Offset from geometry in pixels


@dataclass
class MeasurementConfig:
    """Configuration for measurement display."""
    show_width: bool = True
    show_height: bool = True
    show_thickness: bool = True
    show_text_sizes: bool = False
    unit: str = "mm"
    decimal_places: int = 1
    line_color: QColor = None
    text_color: QColor = None
    font_size: int = 10
    arrow_size: float = 8.0

    def __post_init__(self):
        if self.line_color is None:
            self.line_color = QColor(100, 150, 255)
        if self.text_color is None:
            self.text_color = QColor(255, 255, 255)


class MeasurementOverlay:
    """
    Draws measurement dimensions on the preview widget.
    """

    def __init__(self, config: Optional[MeasurementConfig] = None):
        self.config = config or MeasurementConfig()
        self._dimensions: List[Dimension] = []
        self._plate_width = 100.0
        self._plate_height = 30.0
        self._plate_thickness = 3.0
        self._scale = 1.0
        self._offset_x = 0.0
        self._offset_y = 0.0

    def set_plate_dimensions(self, width: float, height: float, thickness: float):
        """Set the plate dimensions to display."""
        self._plate_width = width
        self._plate_height = height
        self._plate_thickness = thickness
        self._update_dimensions()

    def set_view_transform(self, scale: float, offset_x: float, offset_y: float):
        """Set the view transformation for coordinate conversion."""
        self._scale = scale
        self._offset_x = offset_x
        self._offset_y = offset_y

    def _update_dimensions(self):
        """Update dimension list based on current settings."""
        self._dimensions.clear()

        if self.config.show_width:
            self._dimensions.append(Dimension(
                start=(-self._plate_width / 2, -self._plate_height / 2),
                end=(self._plate_width / 2, -self._plate_height / 2),
                value=self._plate_width,
                orientation="horizontal",
                offset=30
            ))

        if self.config.show_height:
            self._dimensions.append(Dimension(
                start=(self._plate_width / 2, -self._plate_height / 2),
                end=(self._plate_width / 2, self._plate_height / 2),
                value=self._plate_height,
                orientation="vertical",
                offset=30
            ))

        if self.config.show_thickness:
            # Thickness is shown as text annotation
            self._dimensions.append(Dimension(
                start=(-self._plate_width / 2, self._plate_height / 2),
                end=(-self._plate_width / 2, self._plate_height / 2),
                value=self._plate_thickness,
                label="Thickness",
                orientation="annotation",
                offset=20
            ))

    def draw(self, painter: QPainter, widget_rect: QRect):
        """
        Draw measurement overlay on the painter.

        Args:
            painter: QPainter to draw on
            widget_rect: Rectangle bounds of the widget
        """
        painter.save()

        # Set up pen for dimension lines
        pen = QPen(self.config.line_color)
        pen.setWidth(1)
        painter.setPen(pen)

        # Set up font for labels
        font = QFont("Arial", self.config.font_size)
        painter.setFont(font)
        fm = QFontMetrics(font)

        # Widget center
        center_x = widget_rect.width() / 2 + self._offset_x
        center_y = widget_rect.height() / 2 + self._offset_y

        for dim in self._dimensions:
            if dim.orientation == "horizontal":
                self._draw_horizontal_dimension(painter, dim, center_x, center_y, fm)
            elif dim.orientation == "vertical":
                self._draw_vertical_dimension(painter, dim, center_x, center_y, fm)
            elif dim.orientation == "annotation":
                self._draw_annotation(painter, dim, center_x, center_y, fm)

        painter.restore()

    def _world_to_screen(self, x: float, y: float,
                         center_x: float, center_y: float) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates."""
        screen_x = int(center_x + x * self._scale)
        screen_y = int(center_y - y * self._scale)  # Y is flipped
        return screen_x, screen_y

    def _draw_horizontal_dimension(self, painter: QPainter, dim: Dimension,
                                   center_x: float, center_y: float,
                                   fm: QFontMetrics):
        """Draw a horizontal dimension line."""
        x1, y1 = self._world_to_screen(dim.start[0], dim.start[1], center_x, center_y)
        x2, y2 = self._world_to_screen(dim.end[0], dim.end[1], center_x, center_y)

        # Offset the line
        y1 += int(dim.offset)
        y2 += int(dim.offset)

        # Draw extension lines
        painter.drawLine(
            int(center_x + dim.start[0] * self._scale),
            int(center_y - dim.start[1] * self._scale),
            x1, y1
        )
        painter.drawLine(
            int(center_x + dim.end[0] * self._scale),
            int(center_y - dim.end[1] * self._scale),
            x2, y2
        )

        # Draw dimension line
        painter.drawLine(x1, y1, x2, y2)

        # Draw arrows
        self._draw_arrow(painter, x1, y1, 0)
        self._draw_arrow(painter, x2, y2, 180)

        # Draw label
        label = f"{dim.value:.{self.config.decimal_places}f} {self.config.unit}"
        text_width = fm.horizontalAdvance(label)
        text_x = (x1 + x2) // 2 - text_width // 2
        text_y = y1 - 5

        painter.setPen(self.config.text_color)
        painter.drawText(text_x, text_y, label)
        painter.setPen(QPen(self.config.line_color))

    def _draw_vertical_dimension(self, painter: QPainter, dim: Dimension,
                                 center_x: float, center_y: float,
                                 fm: QFontMetrics):
        """Draw a vertical dimension line."""
        x1, y1 = self._world_to_screen(dim.start[0], dim.start[1], center_x, center_y)
        x2, y2 = self._world_to_screen(dim.end[0], dim.end[1], center_x, center_y)

        # Offset the line
        x1 += int(dim.offset)
        x2 += int(dim.offset)

        # Draw extension lines
        painter.drawLine(
            int(center_x + dim.start[0] * self._scale),
            int(center_y - dim.start[1] * self._scale),
            x1, y1
        )
        painter.drawLine(
            int(center_x + dim.end[0] * self._scale),
            int(center_y - dim.end[1] * self._scale),
            x2, y2
        )

        # Draw dimension line
        painter.drawLine(x1, y1, x2, y2)

        # Draw arrows
        self._draw_arrow(painter, x1, y1, 90)
        self._draw_arrow(painter, x2, y2, 270)

        # Draw label (rotated)
        label = f"{dim.value:.{self.config.decimal_places}f} {self.config.unit}"
        text_height = fm.height()
        text_x = x1 + 5
        text_y = (y1 + y2) // 2 + text_height // 4

        painter.setPen(self.config.text_color)
        painter.save()
        painter.translate(text_x, text_y)
        painter.rotate(-90)
        painter.drawText(0, 0, label)
        painter.restore()
        painter.setPen(QPen(self.config.line_color))

    def _draw_annotation(self, painter: QPainter, dim: Dimension,
                         center_x: float, center_y: float,
                         fm: QFontMetrics):
        """Draw a text annotation."""
        x, y = self._world_to_screen(dim.start[0], dim.start[1], center_x, center_y)

        label = f"{dim.label}: {dim.value:.{self.config.decimal_places}f} {self.config.unit}"

        # Position in corner
        x = 10
        y = 20 + len([d for d in self._dimensions if d.orientation == "annotation"]) * 15

        painter.setPen(self.config.text_color)
        painter.drawText(x, y, label)

    def _draw_arrow(self, painter: QPainter, x: int, y: int, angle: float):
        """Draw an arrowhead at the specified position and angle."""
        size = self.config.arrow_size
        rad = math.radians(angle)

        # Arrow points
        p1_x = x + size * math.cos(rad + math.radians(150))
        p1_y = y - size * math.sin(rad + math.radians(150))
        p2_x = x + size * math.cos(rad - math.radians(150))
        p2_y = y - size * math.sin(rad - math.radians(150))

        painter.drawLine(x, y, int(p1_x), int(p1_y))
        painter.drawLine(x, y, int(p2_x), int(p2_y))


class BoundingBoxCalculator:
    """
    Calculates bounding box dimensions from geometry.
    """

    @staticmethod
    def from_cadquery(workplane) -> Tuple[float, float, float]:
        """
        Calculate bounding box dimensions from CadQuery workplane.

        Returns:
            (width, height, thickness) tuple
        """
        try:
            bb = workplane.val().BoundingBox()
            width = bb.xmax - bb.xmin
            height = bb.ymax - bb.ymin
            thickness = bb.zmax - bb.zmin
            return (width, height, thickness)
        except Exception:
            return (100.0, 30.0, 3.0)

    @staticmethod
    def format_dimensions(width: float, height: float, thickness: float,
                          unit: str = "mm", decimals: int = 1) -> str:
        """Format dimensions as a readable string."""
        return (f"{width:.{decimals}f} x {height:.{decimals}f} x "
                f"{thickness:.{decimals}f} {unit}")
