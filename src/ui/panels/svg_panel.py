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
from core.geometry.qr_generator import QRCodeGenerator, QRConfig, QRStyle


class QRElementWidget(QFrame):
    """Widget for configuring a QR code element."""

    changed = pyqtSignal()
    remove_requested = pyqtSignal(object)

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self._config = config
        self._qr_generator = QRCodeGenerator()

        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("QFrame { background-color: #353535; border-radius: 5px; }")

        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        # Header
        header = QHBoxLayout()
        data_preview = config.get('data', '')[:30]
        if len(config.get('data', '')) > 30:
            data_preview += '...'
        self._name_label = QLabel(f"QR: {data_preview}")
        self._name_label.setStyleSheet("font-weight: bold;")
        header.addWidget(self._name_label)
        header.addStretch()

        self._remove_btn = QPushButton("×")
        self._remove_btn.setFixedSize(20, 20)
        self._remove_btn.setStyleSheet("QPushButton { font-weight: bold; }")
        self._remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        header.addWidget(self._remove_btn)
        layout.addLayout(header)

        # Size
        self._size_slider = SliderSpinBox("Size:", 5, 100, config.get('size', 20), decimals=1, suffix=" mm")
        self._size_slider.valueChanged.connect(self._on_changed)
        layout.addWidget(self._size_slider)

        # Position X
        self._pos_x_slider = SliderSpinBox("Position X:", -100, 100, config.get('position_x', 0), decimals=1, suffix=" mm")
        self._pos_x_slider.valueChanged.connect(self._on_changed)
        layout.addWidget(self._pos_x_slider)

        # Position Y
        self._pos_y_slider = SliderSpinBox("Position Y:", -100, 100, config.get('position_y', 0), decimals=1, suffix=" mm")
        self._pos_y_slider.valueChanged.connect(self._on_changed)
        layout.addWidget(self._pos_y_slider)

        # Depth
        self._depth_slider = SliderSpinBox("Depth:", 0.5, 10, config.get('depth', 1), decimals=1, suffix=" mm")
        self._depth_slider.valueChanged.connect(self._on_changed)
        layout.addWidget(self._depth_slider)

        # Style
        style_row = QHBoxLayout()
        style_row.addWidget(QLabel("Style:"))
        self._style_combo = ResetableComboBox(default_text="Raised")
        self._style_combo.addItems(["Raised", "Engraved", "Cutout"])
        style_map = {"raised": "Raised", "engraved": "Engraved", "cutout": "Cutout"}
        self._style_combo.setCurrentText(style_map.get(config.get('style', 'raised'), 'Raised'))
        self._style_combo.currentTextChanged.connect(self._on_changed)
        style_row.addWidget(self._style_combo, stretch=1)
        layout.addLayout(style_row)

    def _on_changed(self, *args):
        self.changed.emit()

    def get_qr_config(self) -> QRConfig:
        """Get QRConfig object for geometry generation."""
        style_map = {"Raised": QRStyle.RAISED, "Engraved": QRStyle.ENGRAVED, "Cutout": QRStyle.CUTOUT}
        return QRConfig(
            data=self._config.get('data', ''),
            size=self._size_slider.value(),
            depth=self._depth_slider.value(),
            style=style_map.get(self._style_combo.currentText(), QRStyle.RAISED),
            position_x=self._pos_x_slider.value(),
            position_y=self._pos_y_slider.value(),
            error_correction=self._config.get('error_correction', 'M'),
        )

    def get_config(self) -> dict:
        """Get configuration for presets."""
        return {
            'type': 'qr',
            'data': self._config.get('data', ''),
            'size': self._size_slider.value(),
            'depth': self._depth_slider.value(),
            'style': self._style_combo.currentText().lower(),
            'position_x': self._pos_x_slider.value(),
            'position_y': self._pos_y_slider.value(),
            'error_correction': self._config.get('error_correction', 'M'),
        }

    def set_config(self, config: dict):
        """Set configuration from presets."""
        if 'size' in config:
            self._size_slider.setValue(config['size'])
        if 'depth' in config:
            self._depth_slider.setValue(config['depth'])
        if 'position_x' in config:
            self._pos_x_slider.setValue(config['position_x'])
        if 'position_y' in config:
            self._pos_y_slider.setValue(config['position_y'])
        style_map = {"raised": "Raised", "engraved": "Engraved", "cutout": "Cutout"}
        if 'style' in config:
            self._style_combo.setCurrentText(style_map.get(config['style'], 'Raised'))


class SVGElementWidget(QFrame):
    """Widget for configuring a single SVG element."""

    changed = pyqtSignal()
    remove_requested = pyqtSignal(object)
    # Signal for real-time position preview: (element_id, x, y, z, rotation)
    position_dragging = pyqtSignal(str, float, float, float, float)
    # Signals for drag state tracking
    drag_started = pyqtSignal()
    drag_ended = pyqtSignal()

    def __init__(self, element: SVGElement, parent=None):
        super().__init__(parent)
        self._element = element
        self._element_id = f"svg_{id(element)}"  # Unique ID for this element

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
        self._pos_x_slider.dragging.connect(self._on_position_dragging)
        self._pos_x_slider.dragStarted.connect(self.drag_started)
        self._pos_x_slider.dragEnded.connect(self.drag_ended)
        layout.addWidget(self._pos_x_slider)

        # Position Y
        self._pos_y_slider = SliderSpinBox("Position Y:", -100, 100, 0, decimals=1, suffix=" mm")
        self._pos_y_slider.valueChanged.connect(self._on_changed)
        self._pos_y_slider.dragging.connect(self._on_position_dragging)
        self._pos_y_slider.dragStarted.connect(self.drag_started)
        self._pos_y_slider.dragEnded.connect(self.drag_ended)
        layout.addWidget(self._pos_y_slider)

        # Rotation
        self._rotation_slider = SliderSpinBox("Rotation:", 0, 360, 0, decimals=0, suffix="°")
        self._rotation_slider.valueChanged.connect(self._on_changed)
        self._rotation_slider.dragging.connect(self._on_position_dragging)
        self._rotation_slider.dragStarted.connect(self.drag_started)
        self._rotation_slider.dragEnded.connect(self.drag_ended)
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

    def _on_position_dragging(self, value):
        """Emit position/rotation during drag for real-time preview."""
        # Get current position and rotation values
        x = self._pos_x_slider.value()
        y = self._pos_y_slider.value()
        rotation = self._rotation_slider.value()
        # Z offset depends on style - for raised, it sits on top of plate
        # This will be handled by the viewer - just emit 0 for now
        z = 0
        self.position_dragging.emit(self._element_id, x, y, z, rotation)

    def get_element_id(self) -> str:
        """Get the unique element ID for overlay tracking."""
        return self._element_id

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
    # Signal for real-time SVG position preview: (element_id, x, y, z, rotation)
    svg_position_dragging = pyqtSignal(str, float, float, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._svg_widgets = []
        self._qr_widgets = []
        self._importer = SVGImporter()
        self._qr_generator = QRCodeGenerator()
        self._active_drag_count = 0  # Track number of active drags

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Import section
        import_group = QGroupBox("Import Graphics")
        import_layout = QVBoxLayout(import_group)

        import_btn = QPushButton("Import SVG File...")
        import_btn.clicked.connect(self._import_svg)
        import_layout.addWidget(import_btn)

        qr_btn = QPushButton("Add QR Code...")
        qr_btn.clicked.connect(self._add_qr_code)
        import_layout.addWidget(qr_btn)

        info_label = QLabel("SVG: paths, shapes, polygons\nQR: URLs, text, contact info")
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

    def _add_qr_code(self):
        """Open QR code dialog and add QR element."""
        from ui.dialogs.qr_code_dialog import QRCodeDialog

        dialog = QRCodeDialog(self)
        if dialog.exec_() == QRCodeDialog.Accepted:
            config = dialog.get_config()
            if config.get('data'):
                self._add_qr_widget(config)
                self._on_changed()
            else:
                QMessageBox.warning(
                    self,
                    "No Data",
                    "Please enter data to encode in the QR code."
                )

    def _add_qr_widget(self, config: dict):
        """Add a widget for a QR code element."""
        widget = QRElementWidget(config)
        widget.changed.connect(self._on_changed)
        widget.remove_requested.connect(self._remove_qr_element)

        self._qr_widgets.append(widget)
        self._elements_layout.addWidget(widget)

    def _remove_qr_element(self, widget):
        """Remove a QR code element widget."""
        self._qr_widgets.remove(widget)
        self._elements_layout.removeWidget(widget)
        widget.deleteLater()
        self._on_changed()

    def add_svg_from_content(self, svg_content: str, name: str, target_size: float = None) -> bool:
        """
        Add an SVG element from SVG content string.

        Args:
            svg_content: The SVG XML content as a string
            name: Display name for the element
            target_size: Optional initial target size in mm

        Returns:
            True if successful, False otherwise
        """
        element = self._importer.load_svg_from_content(svg_content, name)
        if element:
            self._add_element_widget(element, target_size=target_size)
            self._on_changed()
            return True
        return False

    def _add_element_widget(self, element: SVGElement, target_size: float = None):
        """Add a widget for an SVG element."""
        widget = SVGElementWidget(element)
        widget.changed.connect(self._on_changed)
        widget.remove_requested.connect(self._remove_element)
        # Connect position dragging for real-time preview
        widget.position_dragging.connect(self.svg_position_dragging)
        # Connect drag state tracking
        widget.drag_started.connect(self._on_drag_started)
        widget.drag_ended.connect(self._on_drag_ended)

        # Set target size if provided
        if target_size is not None:
            widget._size_slider.setValue(target_size)

        self._svg_widgets.append(widget)
        self._elements_layout.addWidget(widget)

    def _remove_element(self, widget):
        """Remove an SVG element widget."""
        self._svg_widgets.remove(widget)
        self._elements_layout.removeWidget(widget)
        widget.deleteLater()
        self._on_changed()

    def _clear_all(self):
        """Remove all SVG and QR elements."""
        while self._svg_widgets:
            widget = self._svg_widgets.pop()
            self._elements_layout.removeWidget(widget)
            widget.deleteLater()
        while self._qr_widgets:
            widget = self._qr_widgets.pop()
            self._elements_layout.removeWidget(widget)
            widget.deleteLater()
        self._on_changed()

    def _on_changed(self, *args):
        self.settings_changed.emit()

    def _on_drag_started(self):
        """Track when a position drag starts."""
        self._active_drag_count += 1

    def _on_drag_ended(self):
        """Track when a position drag ends."""
        self._active_drag_count = max(0, self._active_drag_count - 1)

    def is_dragging(self) -> bool:
        """Check if any SVG position slider is currently being dragged."""
        return self._active_drag_count > 0

    def get_elements(self) -> list:
        """Get all configured SVG elements."""
        return [w.get_element() for w in self._svg_widgets]

    def get_svg_widget_by_id(self, element_id: str):
        """Get SVG widget by element ID for real-time preview."""
        for widget in self._svg_widgets:
            if widget.get_element_id() == element_id:
                return widget
        return None

    def get_qr_elements(self) -> list:
        """Get all configured QR code elements."""
        return [w.get_qr_config() for w in self._qr_widgets]

    def get_config(self) -> dict:
        """Get SVG/QR configuration for presets."""
        elements = [w.get_config() for w in self._svg_widgets]
        qr_elements = [w.get_config() for w in self._qr_widgets]
        return {
            'elements': elements + qr_elements
        }

    def set_config(self, config: dict):
        """Set SVG/QR configuration from presets."""
        self.blockSignals(True)

        try:
            # Clear existing elements
            self._clear_all()

            # Recreate elements from config
            for elem_config in config.get('elements', []):
                if elem_config.get('type') == 'qr':
                    # QR code element
                    widget = QRElementWidget(elem_config)
                    widget.set_config(elem_config)
                    widget.changed.connect(self._on_changed)
                    widget.remove_requested.connect(self._remove_qr_element)

                    self._qr_widgets.append(widget)
                    self._elements_layout.addWidget(widget)
                else:
                    # SVG element
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
