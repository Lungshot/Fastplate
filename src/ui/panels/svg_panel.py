"""
SVG Import Panel
UI panel for importing and configuring SVG/vector graphics.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGroupBox, QFileDialog, QListWidget,
    QListWidgetItem, QMessageBox
)
from PyQt5.QtCore import pyqtSignal, Qt

from ui.widgets.slider_spin import SliderSpinBox, ResetableComboBox
from core.geometry.svg_importer import SVGImporter, SVGElement


class SVGElementWidget(QFrame):
    """Widget for configuring a single SVG element."""

    changed = pyqtSignal()
    remove_requested = pyqtSignal(object)

    def __init__(self, element: SVGElement, parent=None):
        super().__init__(parent)
        self._element = element

        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("QFrame { background-color: #353535; border-radius: 5px; }")

        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        # Header with name and remove button
        header = QHBoxLayout()
        self._name_label = QLabel(element.name)
        self._name_label.setStyleSheet("font-weight: bold;")
        header.addWidget(self._name_label)
        header.addStretch()

        self._remove_btn = QPushButton("×")
        self._remove_btn.setFixedSize(20, 20)
        self._remove_btn.setStyleSheet("QPushButton { font-weight: bold; }")
        self._remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        header.addWidget(self._remove_btn)
        layout.addLayout(header)

        # Size info
        size_label = QLabel(f"Original: {element.width:.1f} × {element.height:.1f}")
        size_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(size_label)

        # Target size
        self._size_slider = SliderSpinBox("Size:", 5, 100, 20, decimals=1, suffix=" mm")
        self._size_slider.valueChanged.connect(self._on_changed)
        layout.addWidget(self._size_slider)

        # Position X
        self._pos_x_slider = SliderSpinBox("Position X:", -100, 100, 0, decimals=1, suffix=" mm")
        self._pos_x_slider.valueChanged.connect(self._on_changed)
        layout.addWidget(self._pos_x_slider)

        # Position Y
        self._pos_y_slider = SliderSpinBox("Position Y:", -100, 100, 0, decimals=1, suffix=" mm")
        self._pos_y_slider.valueChanged.connect(self._on_changed)
        layout.addWidget(self._pos_y_slider)

        # Rotation
        self._rotation_slider = SliderSpinBox("Rotation:", 0, 360, 0, decimals=0, suffix="°")
        self._rotation_slider.valueChanged.connect(self._on_changed)
        layout.addWidget(self._rotation_slider)

        # Depth
        self._depth_slider = SliderSpinBox("Depth:", 0.5, 10, 2, decimals=1, suffix=" mm")
        self._depth_slider.valueChanged.connect(self._on_changed)
        layout.addWidget(self._depth_slider)

        # Style
        style_row = QHBoxLayout()
        style_row.addWidget(QLabel("Style:"))
        self._style_combo = ResetableComboBox(default_text="Raised")
        self._style_combo.addItems(["Raised", "Engraved", "Cutout"])
        self._style_combo.currentTextChanged.connect(self._on_changed)
        style_row.addWidget(self._style_combo, stretch=1)
        layout.addLayout(style_row)

    def _on_changed(self, *args):
        self.changed.emit()

    def get_element(self) -> SVGElement:
        """Get the configured SVG element."""
        self._element.position_x = self._pos_x_slider.value()
        self._element.position_y = self._pos_y_slider.value()
        self._element.rotation = self._rotation_slider.value()
        self._element.depth = self._depth_slider.value()

        style_map = {"Raised": "raised", "Engraved": "engraved", "Cutout": "cutout"}
        self._element.style = style_map.get(self._style_combo.currentText(), "raised")

        # Store target size for geometry creation
        self._element.target_size = self._size_slider.value()

        return self._element

    def get_config(self) -> dict:
        """Get the element configuration for presets."""
        return {
            'name': self._element.name,
            'paths': self._element.paths,
            'viewbox': self._element.viewbox,
            'width': self._element.width,
            'height': self._element.height,
            'position_x': self._pos_x_slider.value(),
            'position_y': self._pos_y_slider.value(),
            'rotation': self._rotation_slider.value(),
            'depth': self._depth_slider.value(),
            'style': self._style_combo.currentText().lower(),
            'target_size': self._size_slider.value(),
        }

    def set_config(self, config: dict):
        """Set the element configuration from presets."""
        if 'position_x' in config:
            self._pos_x_slider.setValue(config['position_x'])
        if 'position_y' in config:
            self._pos_y_slider.setValue(config['position_y'])
        if 'rotation' in config:
            self._rotation_slider.setValue(config['rotation'])
        if 'depth' in config:
            self._depth_slider.setValue(config['depth'])
        if 'target_size' in config:
            self._size_slider.setValue(config['target_size'])

        style_map = {"raised": "Raised", "engraved": "Engraved", "cutout": "Cutout"}
        if 'style' in config:
            self._style_combo.setCurrentText(style_map.get(config['style'], 'Raised'))


class SVGPanel(QWidget):
    """Panel for SVG import settings."""

    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._svg_widgets = []
        self._importer = SVGImporter()

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Import section
        import_group = QGroupBox("Import SVG")
        import_layout = QVBoxLayout(import_group)

        import_btn = QPushButton("Import SVG File...")
        import_btn.clicked.connect(self._import_svg)
        import_layout.addWidget(import_btn)

        info_label = QLabel("Supports SVG paths, rectangles,\ncircles, ellipses, and polygons.")
        info_label.setStyleSheet("color: #888; font-size: 10px;")
        import_layout.addWidget(info_label)

        layout.addWidget(import_group)

        # SVG elements section
        elements_group = QGroupBox("SVG Elements")
        elements_layout = QVBoxLayout(elements_group)

        # Scrollable area for SVG elements
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setMinimumHeight(200)

        self._elements_container = QWidget()
        self._elements_layout = QVBoxLayout(self._elements_container)
        self._elements_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self._elements_container)

        elements_layout.addWidget(scroll)

        # Clear all button
        clear_btn = QPushButton("Clear All SVGs")
        clear_btn.clicked.connect(self._clear_all)
        elements_layout.addWidget(clear_btn)

        layout.addWidget(elements_group)
        layout.addStretch()

    def _import_svg(self):
        """Open file dialog and import SVG."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Import SVG File",
            "",
            "SVG Files (*.svg);;All Files (*)"
        )

        if filepath:
            element = self._importer.load_svg(filepath)
            if element:
                self._add_element_widget(element)
                self._on_changed()
            else:
                QMessageBox.warning(
                    self,
                    "Import Failed",
                    "Could not import the SVG file. Make sure it contains valid path data."
                )

    def _add_element_widget(self, element: SVGElement):
        """Add a widget for an SVG element."""
        widget = SVGElementWidget(element)
        widget.changed.connect(self._on_changed)
        widget.remove_requested.connect(self._remove_element)

        self._svg_widgets.append(widget)
        self._elements_layout.addWidget(widget)

    def _remove_element(self, widget):
        """Remove an SVG element widget."""
        self._svg_widgets.remove(widget)
        self._elements_layout.removeWidget(widget)
        widget.deleteLater()
        self._on_changed()

    def _clear_all(self):
        """Remove all SVG elements."""
        while self._svg_widgets:
            widget = self._svg_widgets.pop()
            self._elements_layout.removeWidget(widget)
            widget.deleteLater()
        self._on_changed()

    def _on_changed(self, *args):
        self.settings_changed.emit()

    def get_elements(self) -> list:
        """Get all configured SVG elements."""
        return [w.get_element() for w in self._svg_widgets]

    def get_config(self) -> dict:
        """Get SVG configuration for presets."""
        return {
            'elements': [w.get_config() for w in self._svg_widgets]
        }

    def set_config(self, config: dict):
        """Set SVG configuration from presets."""
        self.blockSignals(True)

        try:
            # Clear existing elements
            self._clear_all()

            # Recreate elements from config
            for elem_config in config.get('elements', []):
                # Create SVGElement from config
                element = SVGElement(
                    name=elem_config.get('name', 'SVG Element'),
                    paths=elem_config.get('paths', []),
                    viewbox=tuple(elem_config.get('viewbox', (0, 0, 100, 100))),
                    width=elem_config.get('width', 0),
                    height=elem_config.get('height', 0),
                )

                widget = SVGElementWidget(element)
                widget.set_config(elem_config)
                widget.changed.connect(self._on_changed)
                widget.remove_requested.connect(self._remove_element)

                self._svg_widgets.append(widget)
                self._elements_layout.addWidget(widget)
        finally:
            self.blockSignals(False)

        self.settings_changed.emit()
