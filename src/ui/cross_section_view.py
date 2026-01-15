"""
Cross-Section View
Displays cross-section visualization of the nameplate.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from ui.widgets.slider_spin import FocusComboBox
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QLinearGradient, QFont
from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import Enum


class SectionPlane(Enum):
    """Available section plane orientations."""
    XY = "xy"  # Top view (looking down Z)
    XZ = "xz"  # Front view (looking along Y)
    YZ = "yz"  # Side view (looking along X)


@dataclass
class CrossSectionConfig:
    """Configuration for cross-section display."""
    plane: SectionPlane = SectionPlane.XZ
    position: float = 0.0  # Position along the normal axis (0.0 = center)
    show_dimensions: bool = True
    show_material_fill: bool = True
    plate_color: QColor = None
    text_color: QColor = None
    engraving_color: QColor = None

    def __post_init__(self):
        if self.plate_color is None:
            self.plate_color = QColor(100, 100, 120)
        if self.text_color is None:
            self.text_color = QColor(60, 60, 80)
        if self.engraving_color is None:
            self.engraving_color = QColor(200, 200, 210)


@dataclass
class PlateSection:
    """Represents a section of the plate geometry."""
    width: float
    height: float
    thickness: float
    text_depth: float = 0.5
    text_raised: bool = False
    has_border: bool = False
    border_width: float = 2.0
    border_height: float = 1.0
    corner_radius: float = 0.0


class CrossSectionWidget(QWidget):
    """
    Widget that displays a cross-section view of the nameplate.
    """

    section_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = CrossSectionConfig()
        self.plate_section = PlateSection(
            width=100.0,
            height=30.0,
            thickness=3.0
        )
        self._setup_ui()

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Controls
        controls = QHBoxLayout()

        # Plane selector
        controls.addWidget(QLabel("Plane:"))
        self.plane_combo = FocusComboBox()
        self.plane_combo.addItems(["Front (XZ)", "Side (YZ)", "Top (XY)"])
        self.plane_combo.currentIndexChanged.connect(self._on_plane_changed)
        controls.addWidget(self.plane_combo)

        # Position slider
        controls.addWidget(QLabel("Position:"))
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(-100, 100)
        self.position_slider.setValue(0)
        self.position_slider.valueChanged.connect(self._on_position_changed)
        controls.addWidget(self.position_slider)

        self.position_label = QLabel("0.0 mm")
        controls.addWidget(self.position_label)

        controls.addStretch()
        layout.addLayout(controls)

        # Drawing area
        self.drawing_area = CrossSectionDrawingArea(self)
        layout.addWidget(self.drawing_area, stretch=1)

    def set_plate_dimensions(self, width: float, height: float, thickness: float):
        """Set the plate dimensions."""
        self.plate_section.width = width
        self.plate_section.height = height
        self.plate_section.thickness = thickness
        self._update_slider_range()
        self.drawing_area.set_section(self.plate_section, self.config)

    def set_text_style(self, depth: float, raised: bool):
        """Set text engraving/raised style."""
        self.plate_section.text_depth = depth
        self.plate_section.text_raised = raised
        self.drawing_area.set_section(self.plate_section, self.config)

    def set_border(self, has_border: bool, width: float = 2.0, height: float = 1.0):
        """Set border properties."""
        self.plate_section.has_border = has_border
        self.plate_section.border_width = width
        self.plate_section.border_height = height
        self.drawing_area.set_section(self.plate_section, self.config)

    def set_corner_radius(self, radius: float):
        """Set corner radius."""
        self.plate_section.corner_radius = radius
        self.drawing_area.set_section(self.plate_section, self.config)

    def _update_slider_range(self):
        """Update slider range based on current plane."""
        plane = self.config.plane
        if plane == SectionPlane.XZ:
            max_val = self.plate_section.height / 2
        elif plane == SectionPlane.YZ:
            max_val = self.plate_section.width / 2
        else:  # XY
            max_val = self.plate_section.thickness / 2

        self.position_slider.setRange(int(-max_val * 10), int(max_val * 10))

    def _on_plane_changed(self, index: int):
        """Handle plane selection change."""
        planes = [SectionPlane.XZ, SectionPlane.YZ, SectionPlane.XY]
        self.config.plane = planes[index]
        self._update_slider_range()
        self.position_slider.setValue(0)
        self.drawing_area.set_section(self.plate_section, self.config)
        self.section_changed.emit()

    def _on_position_changed(self, value: int):
        """Handle position slider change."""
        self.config.position = value / 10.0
        self.position_label.setText(f"{self.config.position:.1f} mm")
        self.drawing_area.set_section(self.plate_section, self.config)
        self.section_changed.emit()


class CrossSectionDrawingArea(QWidget):
    """
    Drawing area for cross-section visualization.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.section: Optional[PlateSection] = None
        self.config = CrossSectionConfig()
        self.setMinimumSize(200, 150)
        self.setStyleSheet("background-color: #2a2a2a;")

    def set_section(self, section: PlateSection, config: CrossSectionConfig):
        """Set the section to display."""
        self.section = section
        self.config = config
        self.update()

    def paintEvent(self, event):
        """Paint the cross-section."""
        super().paintEvent(event)

        if not self.section:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate scale and offset
        margin = 40
        available_width = self.width() - margin * 2
        available_height = self.height() - margin * 2

        if self.config.plane == SectionPlane.XZ:
            # Front view - show width x thickness
            section_width = self.section.width
            section_height = self.section.thickness
        elif self.config.plane == SectionPlane.YZ:
            # Side view - show height x thickness
            section_width = self.section.height
            section_height = self.section.thickness
        else:  # XY
            # Top view - show width x height
            section_width = self.section.width
            section_height = self.section.height

        scale_x = available_width / section_width if section_width > 0 else 1
        scale_y = available_height / section_height if section_height > 0 else 1
        scale = min(scale_x, scale_y) * 0.8

        # Center offset
        offset_x = self.width() / 2
        offset_y = self.height() / 2

        # Draw based on plane
        if self.config.plane == SectionPlane.XZ:
            self._draw_front_section(painter, scale, offset_x, offset_y)
        elif self.config.plane == SectionPlane.YZ:
            self._draw_side_section(painter, scale, offset_x, offset_y)
        else:
            self._draw_top_section(painter, scale, offset_x, offset_y)

        # Draw plane indicator
        self._draw_plane_indicator(painter)

        painter.end()

    def _draw_front_section(self, painter: QPainter, scale: float,
                            cx: float, cy: float):
        """Draw front (XZ) cross-section."""
        w = self.section.width * scale
        h = self.section.thickness * scale

        # Main plate body
        x = cx - w / 2
        y = cy - h / 2

        # Fill with gradient
        if self.config.show_material_fill:
            gradient = QLinearGradient(x, y, x, y + h)
            gradient.setColorAt(0, self.config.plate_color.lighter(120))
            gradient.setColorAt(0.5, self.config.plate_color)
            gradient.setColorAt(1, self.config.plate_color.darker(120))
            painter.setBrush(QBrush(gradient))
        else:
            painter.setBrush(Qt.NoBrush)

        painter.setPen(QPen(QColor(200, 200, 200), 1))

        # Draw with corner radius if applicable
        r = min(self.section.corner_radius * scale, w/4, h/4)
        painter.drawRoundedRect(int(x), int(y), int(w), int(h), r, r)

        # Draw text indication (engraved or raised)
        text_depth = self.section.text_depth * scale
        if self.section.text_raised:
            # Show raised text on top
            text_y = y - text_depth
            painter.setBrush(QBrush(self.config.text_color))
            # Draw several "text bumps"
            for i in range(3):
                bx = x + w * 0.2 + (w * 0.3 * i)
                bw = w * 0.15
                painter.drawRect(int(bx), int(text_y), int(bw), int(text_depth))
        else:
            # Show engraved text (grooves)
            text_y = y
            painter.setBrush(QBrush(self.config.engraving_color))
            for i in range(3):
                bx = x + w * 0.2 + (w * 0.3 * i)
                bw = w * 0.15
                painter.drawRect(int(bx), int(text_y), int(bw), int(text_depth))

        # Draw border if present
        if self.section.has_border:
            border_w = self.section.border_width * scale
            border_h = self.section.border_height * scale
            painter.setBrush(QBrush(self.config.plate_color.lighter(110)))

            # Top border
            painter.drawRect(int(x), int(y - border_h), int(border_w), int(border_h))
            painter.drawRect(int(x + w - border_w), int(y - border_h), int(border_w), int(border_h))

        # Draw dimensions if enabled
        if self.config.show_dimensions:
            self._draw_dimension(painter, x, y + h + 15, x + w, y + h + 15,
                               f"{self.section.width:.1f} mm", "horizontal")
            self._draw_dimension(painter, x + w + 15, y, x + w + 15, y + h,
                               f"{self.section.thickness:.1f} mm", "vertical")

    def _draw_side_section(self, painter: QPainter, scale: float,
                           cx: float, cy: float):
        """Draw side (YZ) cross-section."""
        w = self.section.height * scale
        h = self.section.thickness * scale

        x = cx - w / 2
        y = cy - h / 2

        # Fill with gradient
        if self.config.show_material_fill:
            gradient = QLinearGradient(x, y, x, y + h)
            gradient.setColorAt(0, self.config.plate_color.lighter(120))
            gradient.setColorAt(0.5, self.config.plate_color)
            gradient.setColorAt(1, self.config.plate_color.darker(120))
            painter.setBrush(QBrush(gradient))
        else:
            painter.setBrush(Qt.NoBrush)

        painter.setPen(QPen(QColor(200, 200, 200), 1))

        r = min(self.section.corner_radius * scale, w/4, h/4)
        painter.drawRoundedRect(int(x), int(y), int(w), int(h), r, r)

        # Draw dimensions
        if self.config.show_dimensions:
            self._draw_dimension(painter, x, y + h + 15, x + w, y + h + 15,
                               f"{self.section.height:.1f} mm", "horizontal")
            self._draw_dimension(painter, x + w + 15, y, x + w + 15, y + h,
                               f"{self.section.thickness:.1f} mm", "vertical")

    def _draw_top_section(self, painter: QPainter, scale: float,
                          cx: float, cy: float):
        """Draw top (XY) cross-section."""
        w = self.section.width * scale
        h = self.section.height * scale

        x = cx - w / 2
        y = cy - h / 2

        # Fill
        if self.config.show_material_fill:
            painter.setBrush(QBrush(self.config.plate_color))
        else:
            painter.setBrush(Qt.NoBrush)

        painter.setPen(QPen(QColor(200, 200, 200), 1))

        r = min(self.section.corner_radius * scale, w/4, h/4)
        painter.drawRoundedRect(int(x), int(y), int(w), int(h), r, r)

        # Show text area indication
        text_margin = min(w, h) * 0.1
        painter.setPen(QPen(QColor(150, 150, 150), 1, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(int(x + text_margin), int(y + text_margin),
                        int(w - text_margin * 2), int(h - text_margin * 2))

        # Draw "TEXT" label
        painter.setPen(QColor(150, 150, 150))
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.drawText(int(cx - 15), int(cy + 5), "TEXT")

        # Draw dimensions
        if self.config.show_dimensions:
            self._draw_dimension(painter, x, y + h + 15, x + w, y + h + 15,
                               f"{self.section.width:.1f} mm", "horizontal")
            self._draw_dimension(painter, x + w + 15, y, x + w + 15, y + h,
                               f"{self.section.height:.1f} mm", "vertical")

    def _draw_dimension(self, painter: QPainter, x1: float, y1: float,
                        x2: float, y2: float, label: str, orientation: str):
        """Draw a dimension line with label."""
        painter.setPen(QPen(QColor(100, 150, 255), 1))

        if orientation == "horizontal":
            # Draw dimension line
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            # Draw end ticks
            painter.drawLine(int(x1), int(y1 - 5), int(x1), int(y1 + 5))
            painter.drawLine(int(x2), int(y2 - 5), int(x2), int(y2 + 5))
            # Draw label
            painter.setPen(QColor(200, 200, 200))
            font = QFont("Arial", 8)
            painter.setFont(font)
            painter.drawText(int((x1 + x2) / 2 - 20), int(y1 + 15), label)
        else:
            # Draw dimension line
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            # Draw end ticks
            painter.drawLine(int(x1 - 5), int(y1), int(x1 + 5), int(y1))
            painter.drawLine(int(x2 - 5), int(y2), int(x2 + 5), int(y2))
            # Draw label
            painter.setPen(QColor(200, 200, 200))
            font = QFont("Arial", 8)
            painter.setFont(font)
            painter.save()
            painter.translate(x1 + 15, (y1 + y2) / 2)
            painter.rotate(-90)
            painter.drawText(-20, 0, label)
            painter.restore()

    def _draw_plane_indicator(self, painter: QPainter):
        """Draw a small indicator showing which plane is being viewed."""
        painter.setPen(QColor(150, 150, 150))
        font = QFont("Arial", 9)
        painter.setFont(font)

        plane_names = {
            SectionPlane.XZ: "Front View (XZ)",
            SectionPlane.YZ: "Side View (YZ)",
            SectionPlane.XY: "Top View (XY)"
        }

        label = plane_names.get(self.config.plane, "")
        painter.drawText(10, 20, label)

        # Draw mini coordinate axes
        ax, ay = 30, self.height() - 30
        axis_len = 20

        painter.setPen(QPen(QColor(255, 100, 100), 2))  # X axis - red
        painter.drawLine(ax, ay, ax + axis_len, ay)
        painter.drawText(ax + axis_len + 2, ay + 4, "X")

        if self.config.plane == SectionPlane.XZ:
            painter.setPen(QPen(QColor(100, 100, 255), 2))  # Z axis - blue
            painter.drawLine(ax, ay, ax, ay - axis_len)
            painter.drawText(ax - 4, ay - axis_len - 5, "Z")
        elif self.config.plane == SectionPlane.YZ:
            painter.setPen(QPen(QColor(100, 255, 100), 2))  # Y axis - green
            painter.drawLine(ax, ay, ax + axis_len, ay)
            painter.drawText(ax + axis_len + 2, ay + 4, "Y")
            painter.setPen(QPen(QColor(100, 100, 255), 2))  # Z axis - blue
            painter.drawLine(ax, ay, ax, ay - axis_len)
            painter.drawText(ax - 4, ay - axis_len - 5, "Z")
        else:  # XY
            painter.setPen(QPen(QColor(100, 255, 100), 2))  # Y axis - green
            painter.drawLine(ax, ay, ax, ay - axis_len)
            painter.drawText(ax - 4, ay - axis_len - 5, "Y")


class CrossSectionRenderer:
    """
    Renders cross-section from actual CadQuery geometry.
    """

    @staticmethod
    def get_section_points(workplane, plane: SectionPlane,
                          position: float) -> List[Tuple[float, float]]:
        """
        Get 2D points from a cross-section of the geometry.

        Args:
            workplane: CadQuery workplane to section
            plane: Which plane to section along
            position: Position along the normal axis

        Returns:
            List of (x, y) points forming the section outline
        """
        try:
            import cadquery as cq

            # Create section plane
            if plane == SectionPlane.XZ:
                section = workplane.section(cq.Plane.YZ.offset(position))
            elif plane == SectionPlane.YZ:
                section = workplane.section(cq.Plane.XZ.offset(position))
            else:  # XY
                section = workplane.section(cq.Plane.XY.offset(position))

            # Extract vertices
            vertices = section.vertices().vals()
            points = [(v.X, v.Y) for v in vertices]

            return points

        except Exception as e:
            print(f"Error creating section: {e}")
            return []

    @staticmethod
    def get_bounding_section(workplane) -> Tuple[float, float, float]:
        """
        Get bounding box dimensions from geometry.

        Returns:
            (width, height, thickness) tuple
        """
        try:
            bb = workplane.val().BoundingBox()
            return (
                bb.xmax - bb.xmin,
                bb.ymax - bb.ymin,
                bb.zmax - bb.zmin
            )
        except Exception:
            return (100.0, 30.0, 3.0)
