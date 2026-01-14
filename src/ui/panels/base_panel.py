"""
Base Plate Settings Panel
UI panel for configuring base plate shape and dimensions.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QCheckBox, QFrame, QPushButton, QFileDialog, QSpinBox
)
from PyQt5.QtCore import pyqtSignal

from ui.widgets.slider_spin import SliderSpinBox, FocusComboBox, ResetableComboBox
from core.geometry.base_plates import PLATE_TEMPLATES
from core.geometry.svg_importer import SVGImporter


class BasePlatePanel(QWidget):
    """Panel for base plate settings."""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Shape section
        shape_group = QGroupBox("Shape")
        shape_layout = QVBoxLayout(shape_group)
        
        shape_row = QHBoxLayout()
        shape_row.addWidget(QLabel("Type:"))
        self._shape_combo = ResetableComboBox(default_text="Rounded Rectangle")
        self._shape_combo.addItems([
            "None (Text Only)",
            "Rectangle",
            "Rounded Rectangle",
            "Oval",
            "Chamfered",
            "Hexagon",
            "Octagon",
            "Badge",
            "Keychain",
            "Star",
            "Diamond",
            "Arrow",
            "Heart",
            "Cloud",
            "Sweeping (Curved)",
            "Custom SVG"
        ])
        self._shape_combo.setCurrentText("Rounded Rectangle")
        self._shape_combo.currentTextChanged.connect(self._on_shape_changed)
        shape_row.addWidget(self._shape_combo, stretch=1)
        shape_layout.addLayout(shape_row)

        # Template selector
        template_row = QHBoxLayout()
        template_row.addWidget(QLabel("Template:"))
        self._template_combo = ResetableComboBox(default_text="Custom")
        self._template_combo.addItem("Custom")
        for name in PLATE_TEMPLATES.keys():
            self._template_combo.addItem(name)
        self._template_combo.currentTextChanged.connect(self._on_template_changed)
        template_row.addWidget(self._template_combo, stretch=1)
        shape_layout.addLayout(template_row)

        # Custom SVG import (hidden by default)
        self._custom_svg_row = QHBoxLayout()
        self._custom_svg_btn = QPushButton("Import SVG Outline...")
        self._custom_svg_btn.clicked.connect(self._on_import_svg)
        self._custom_svg_row.addWidget(self._custom_svg_btn)
        self._custom_svg_label = QLabel("No SVG loaded")
        self._custom_svg_label.setStyleSheet("color: #888;")
        self._custom_svg_row.addWidget(self._custom_svg_label, stretch=1)
        shape_layout.addLayout(self._custom_svg_row)
        self._custom_svg_btn.setVisible(False)
        self._custom_svg_label.setVisible(False)

        # Store custom SVG paths
        self._custom_svg_paths = []
        self._custom_svg_name = ""

        layout.addWidget(shape_group)
        
        # Dimensions section
        dims_group = QGroupBox("Dimensions")
        dims_layout = QVBoxLayout(dims_group)
        
        # Auto-size checkboxes
        auto_row = QHBoxLayout()
        self._auto_width_cb = QCheckBox("Auto Width")
        self._auto_width_cb.stateChanged.connect(self._on_auto_changed)
        auto_row.addWidget(self._auto_width_cb)
        
        self._auto_height_cb = QCheckBox("Auto Height")
        self._auto_height_cb.stateChanged.connect(self._on_auto_changed)
        auto_row.addWidget(self._auto_height_cb)
        auto_row.addStretch()
        dims_layout.addLayout(auto_row)
        
        # Width
        self._width_slider = SliderSpinBox("Width:", 20, 300, 120, decimals=1, suffix=" mm")
        self._width_slider.valueChanged.connect(self._on_changed)
        dims_layout.addWidget(self._width_slider)
        
        # Height
        self._height_slider = SliderSpinBox("Height:", 10, 150, 35, decimals=1, suffix=" mm")
        self._height_slider.valueChanged.connect(self._on_changed)
        dims_layout.addWidget(self._height_slider)
        
        # Thickness
        self._thickness_slider = SliderSpinBox("Thickness:", 1, 15, 4, decimals=1, suffix=" mm")
        self._thickness_slider.valueChanged.connect(self._on_changed)
        dims_layout.addWidget(self._thickness_slider)
        
        layout.addWidget(dims_group)
        
        # Corner/Shape options
        self._options_group = QGroupBox("Shape Options")
        options_layout = QVBoxLayout(self._options_group)
        
        # Corner radius (for rounded shapes)
        self._corner_slider = SliderSpinBox("Corner Radius:", 0, 30, 5, decimals=1, suffix=" mm")
        self._corner_slider.valueChanged.connect(self._on_changed)
        options_layout.addWidget(self._corner_slider)
        
        layout.addWidget(self._options_group)
        
        # Sweeping options (hidden by default)
        self._sweep_group = QGroupBox("Curve Options")
        sweep_layout = QVBoxLayout(self._sweep_group)
        
        self._curve_angle_slider = SliderSpinBox("Curve Angle:", 0, 90, 45, decimals=0, suffix="°")
        self._curve_angle_slider.valueChanged.connect(self._on_changed)
        sweep_layout.addWidget(self._curve_angle_slider)
        
        self._curve_radius_slider = SliderSpinBox("Curve Radius:", 30, 200, 80, decimals=0, suffix=" mm")
        self._curve_radius_slider.valueChanged.connect(self._on_changed)
        sweep_layout.addWidget(self._curve_radius_slider)
        
        base_row = QHBoxLayout()
        base_row.addWidget(QLabel("Base Type:"))
        self._base_type_combo = ResetableComboBox(default_text="Pedestal")
        self._base_type_combo.addItems(["Pedestal", "Minimal", "Flat"])
        self._base_type_combo.currentTextChanged.connect(self._on_changed)
        base_row.addWidget(self._base_type_combo, stretch=1)
        sweep_layout.addLayout(base_row)
        
        self._sweep_group.setVisible(False)
        layout.addWidget(self._sweep_group)
        
        # Padding section
        padding_group = QGroupBox("Padding (Auto-size)")
        padding_layout = QVBoxLayout(padding_group)
        
        self._padding_top = SliderSpinBox("Top:", 0, 30, 5, decimals=1, suffix=" mm")
        self._padding_top.valueChanged.connect(self._on_changed)
        padding_layout.addWidget(self._padding_top)
        
        self._padding_bottom = SliderSpinBox("Bottom:", 0, 30, 5, decimals=1, suffix=" mm")
        self._padding_bottom.valueChanged.connect(self._on_changed)
        padding_layout.addWidget(self._padding_bottom)
        
        self._padding_left = SliderSpinBox("Left:", 0, 50, 10, decimals=1, suffix=" mm")
        self._padding_left.valueChanged.connect(self._on_changed)
        padding_layout.addWidget(self._padding_left)
        
        self._padding_right = SliderSpinBox("Right:", 0, 50, 10, decimals=1, suffix=" mm")
        self._padding_right.valueChanged.connect(self._on_changed)
        padding_layout.addWidget(self._padding_right)
        
        layout.addWidget(padding_group)

        # Pattern section
        pattern_group = QGroupBox("Background Pattern")
        pattern_layout = QVBoxLayout(pattern_group)

        pattern_row = QHBoxLayout()
        pattern_row.addWidget(QLabel("Pattern:"))
        self._pattern_combo = ResetableComboBox(default_text="None")
        self._pattern_combo.addItems([
            "None", "Grid", "Dots", "Diamonds",
            "Hexagons", "Lines", "Crosshatch", "Chevron"
        ])
        self._pattern_combo.currentTextChanged.connect(self._on_pattern_changed)
        pattern_row.addWidget(self._pattern_combo, stretch=1)
        pattern_layout.addLayout(pattern_row)

        # Pattern options (hidden when None)
        self._pattern_spacing = SliderSpinBox("Spacing:", 2, 20, 5, decimals=1, suffix=" mm")
        self._pattern_spacing.valueChanged.connect(self._on_changed)
        self._pattern_spacing.setVisible(False)
        pattern_layout.addWidget(self._pattern_spacing)

        self._pattern_size = SliderSpinBox("Element Size:", 0.5, 5, 1, decimals=1, suffix=" mm")
        self._pattern_size.valueChanged.connect(self._on_changed)
        self._pattern_size.setVisible(False)
        pattern_layout.addWidget(self._pattern_size)

        self._pattern_depth = SliderSpinBox("Depth:", 0.1, 1.0, 0.3, decimals=2, suffix=" mm")
        self._pattern_depth.valueChanged.connect(self._on_changed)
        self._pattern_depth.setVisible(False)
        pattern_layout.addWidget(self._pattern_depth)

        layout.addWidget(pattern_group)

        # Edge finishing section
        edge_group = QGroupBox("Edge Finishing")
        edge_layout = QVBoxLayout(edge_group)

        edge_row = QHBoxLayout()
        edge_row.addWidget(QLabel("Style:"))
        self._edge_style_combo = ResetableComboBox(default_text="None")
        self._edge_style_combo.addItems(["None", "Chamfer", "Fillet"])
        self._edge_style_combo.currentTextChanged.connect(self._on_edge_style_changed)
        edge_row.addWidget(self._edge_style_combo, stretch=1)
        edge_layout.addLayout(edge_row)

        self._edge_size_slider = SliderSpinBox("Size:", 0.2, 2.0, 0.5, decimals=1, suffix=" mm")
        self._edge_size_slider.valueChanged.connect(self._on_changed)
        self._edge_size_slider.setVisible(False)
        edge_layout.addWidget(self._edge_size_slider)

        self._edge_top_only_cb = QCheckBox("Top edges only")
        self._edge_top_only_cb.setChecked(True)
        self._edge_top_only_cb.stateChanged.connect(self._on_changed)
        self._edge_top_only_cb.setVisible(False)
        edge_layout.addWidget(self._edge_top_only_cb)

        layout.addWidget(edge_group)

        # Border/Frame section
        border_group = QGroupBox("Border/Frame")
        border_layout = QVBoxLayout(border_group)

        self._border_enabled_cb = QCheckBox("Enable Border")
        self._border_enabled_cb.stateChanged.connect(self._on_border_enabled_changed)
        border_layout.addWidget(self._border_enabled_cb)

        border_style_row = QHBoxLayout()
        border_style_row.addWidget(QLabel("Style:"))
        self._border_style_combo = ResetableComboBox(default_text="Raised")
        self._border_style_combo.addItems([
            "Raised", "Inset", "Double", "Groove", "Rope", "Dots", "Dashes", "Ornate"
        ])
        self._border_style_combo.currentTextChanged.connect(self._on_changed)
        border_style_row.addWidget(self._border_style_combo, stretch=1)
        border_layout.addLayout(border_style_row)

        self._border_width_slider = SliderSpinBox("Width:", 1, 10, 3, decimals=1, suffix=" mm")
        self._border_width_slider.valueChanged.connect(self._on_changed)
        border_layout.addWidget(self._border_width_slider)

        self._border_height_slider = SliderSpinBox("Height:", 0.5, 3, 1.5, decimals=1, suffix=" mm")
        self._border_height_slider.valueChanged.connect(self._on_changed)
        border_layout.addWidget(self._border_height_slider)

        self._border_offset_slider = SliderSpinBox("Offset:", 1, 15, 2, decimals=1, suffix=" mm")
        self._border_offset_slider.valueChanged.connect(self._on_changed)
        border_layout.addWidget(self._border_offset_slider)

        # Initially hide border controls
        for w in [self._border_style_combo, self._border_width_slider,
                  self._border_height_slider, self._border_offset_slider]:
            w.setVisible(False)

        layout.addWidget(border_group)

        # Layered Plates section
        layered_group = QGroupBox("Layered Plates")
        layered_layout = QVBoxLayout(layered_group)

        self._layered_enabled_cb = QCheckBox("Enable Layered Effect")
        self._layered_enabled_cb.stateChanged.connect(self._on_layered_enabled_changed)
        layered_layout.addWidget(self._layered_enabled_cb)

        layer_count_row = QHBoxLayout()
        layer_count_row.addWidget(QLabel("Layers:"))
        self._layer_count_spin = QSpinBox()
        self._layer_count_spin.setRange(2, 5)
        self._layer_count_spin.setValue(2)
        self._layer_count_spin.valueChanged.connect(self._on_changed)
        layer_count_row.addWidget(self._layer_count_spin)
        layer_count_row.addStretch()
        layered_layout.addLayout(layer_count_row)

        self._layer_offset_slider = SliderSpinBox("Layer Offset:", 0.5, 5.0, 2.0, decimals=1, suffix=" mm")
        self._layer_offset_slider.valueChanged.connect(self._on_changed)
        layered_layout.addWidget(self._layer_offset_slider)

        self._layer_shrink_slider = SliderSpinBox("Layer Shrink:", 1.0, 10.0, 3.0, decimals=1, suffix=" mm")
        self._layer_shrink_slider.valueChanged.connect(self._on_changed)
        layered_layout.addWidget(self._layer_shrink_slider)

        # Initially hide layered controls
        for w in [self._layer_count_spin, self._layer_offset_slider, self._layer_shrink_slider]:
            w.setVisible(False)

        layout.addWidget(layered_group)

        # Inset Panel section
        inset_group = QGroupBox("Inset Panel")
        inset_layout = QVBoxLayout(inset_group)

        self._inset_enabled_cb = QCheckBox("Enable Inset Panel")
        self._inset_enabled_cb.stateChanged.connect(self._on_inset_enabled_changed)
        inset_layout.addWidget(self._inset_enabled_cb)

        self._inset_depth_slider = SliderSpinBox("Depth:", 0.3, 2.0, 1.0, decimals=1, suffix=" mm")
        self._inset_depth_slider.valueChanged.connect(self._on_changed)
        inset_layout.addWidget(self._inset_depth_slider)

        self._inset_margin_slider = SliderSpinBox("Margin:", 2.0, 15.0, 5.0, decimals=1, suffix=" mm")
        self._inset_margin_slider.valueChanged.connect(self._on_changed)
        inset_layout.addWidget(self._inset_margin_slider)

        self._inset_corner_slider = SliderSpinBox("Corner Radius:", 0.0, 10.0, 3.0, decimals=1, suffix=" mm")
        self._inset_corner_slider.valueChanged.connect(self._on_changed)
        inset_layout.addWidget(self._inset_corner_slider)

        # Initially hide inset controls
        for w in [self._inset_depth_slider, self._inset_margin_slider, self._inset_corner_slider]:
            w.setVisible(False)

        layout.addWidget(inset_group)

        layout.addStretch()
    
    def _on_shape_changed(self, shape_text):
        """Handle shape type change."""
        is_none = "None" in shape_text
        is_sweeping = "Sweeping" in shape_text
        is_custom = "Custom SVG" in shape_text

        # Hide/show dimension groups based on shape
        self._sweep_group.setVisible(is_sweeping)
        self._options_group.setVisible(not is_sweeping and not is_none and not is_custom)

        # Show/hide custom SVG import
        self._custom_svg_btn.setVisible(is_custom)
        self._custom_svg_label.setVisible(is_custom)

        # Disable dimensions when no plate selected
        for widget in [self._width_slider, self._height_slider, self._thickness_slider,
                       self._auto_width_cb, self._auto_height_cb]:
            widget.setEnabled(not is_none)

        self._on_changed()

    def _on_template_changed(self, template_name: str):
        """Handle template selection."""
        if template_name == "Custom":
            return

        template = PLATE_TEMPLATES.get(template_name)
        if template:
            self._width_slider.setValue(template['width'])
            self._height_slider.setValue(template['height'])
            self._on_changed()

    def _on_import_svg(self):
        """Handle SVG import for custom plate outline."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Import SVG Outline", "", "SVG Files (*.svg)"
        )
        if filepath:
            importer = SVGImporter()
            element = importer.load_svg(filepath)
            if element and element.paths:
                self._custom_svg_paths = element.paths
                self._custom_svg_name = element.name
                self._custom_svg_label.setText(f"Loaded: {element.name}")
                self._on_changed()
            else:
                self._custom_svg_label.setText("Failed to load SVG")

    def _on_layered_enabled_changed(self, state: int):
        """Handle layered plates enable/disable."""
        from PyQt5.QtCore import Qt
        enabled = state == Qt.Checked
        self._layer_count_spin.setVisible(enabled)
        self._layer_offset_slider.setVisible(enabled)
        self._layer_shrink_slider.setVisible(enabled)
        self._on_changed()

    def _on_inset_enabled_changed(self, state: int):
        """Handle inset panel enable/disable."""
        from PyQt5.QtCore import Qt
        enabled = state == Qt.Checked
        self._inset_depth_slider.setVisible(enabled)
        self._inset_margin_slider.setVisible(enabled)
        self._inset_corner_slider.setVisible(enabled)
        self._on_changed()
    
    def _on_auto_changed(self, state):
        """Handle auto-size checkbox change."""
        self._width_slider.setEnabled(not self._auto_width_cb.isChecked())
        self._height_slider.setEnabled(not self._auto_height_cb.isChecked())
        self._on_changed()
    
    def _on_changed(self, *args):
        self.settings_changed.emit()

    def _on_pattern_changed(self, pattern_text: str):
        """Handle pattern type change."""
        has_pattern = pattern_text != "None"
        self._pattern_spacing.setVisible(has_pattern)
        self._pattern_size.setVisible(has_pattern)
        self._pattern_depth.setVisible(has_pattern)
        self._on_changed()

    def _on_edge_style_changed(self, style_text: str):
        """Handle edge style change."""
        has_edge = style_text != "None"
        self._edge_size_slider.setVisible(has_edge)
        self._edge_top_only_cb.setVisible(has_edge)
        self._on_changed()

    def _on_border_enabled_changed(self, state: int):
        """Handle border enable/disable."""
        from PyQt5.QtCore import Qt
        enabled = state == Qt.Checked
        self._border_style_combo.setVisible(enabled)
        self._border_width_slider.setVisible(enabled)
        self._border_height_slider.setVisible(enabled)
        self._border_offset_slider.setVisible(enabled)
        self._on_changed()

    def get_config(self) -> dict:
        """Get the base plate configuration."""
        shape_map = {
            "None (Text Only)": "none",
            "Rectangle": "rectangle",
            "Rounded Rectangle": "rounded_rectangle",
            "Oval": "oval",
            "Chamfered": "chamfered",
            "Hexagon": "hexagon",
            "Octagon": "octagon",
            "Badge": "badge",
            "Keychain": "keychain",
            "Star": "star",
            "Diamond": "diamond",
            "Arrow": "arrow",
            "Heart": "heart",
            "Cloud": "cloud",
            "Sweeping (Curved)": "sweeping",
            "Custom SVG": "custom",
        }

        pattern_map = {
            "None": "none",
            "Grid": "grid",
            "Dots": "dots",
            "Diamonds": "diamonds",
            "Hexagons": "hexagons",
            "Lines": "lines",
            "Crosshatch": "crosshatch",
            "Chevron": "chevron",
        }

        edge_style_map = {
            "None": "none",
            "Chamfer": "chamfer",
            "Fillet": "fillet",
        }

        border_style_map = {
            "Raised": "raised",
            "Inset": "inset",
            "Double": "double",
            "Groove": "groove",
            "Rope": "rope",
            "Dots": "dots",
            "Dashes": "dashes",
            "Ornate": "ornate",
        }

        return {
            'plate': {
                'shape': shape_map.get(self._shape_combo.currentText(), 'rounded_rectangle'),
                'width': self._width_slider.value(),
                'height': self._height_slider.value(),
                'thickness': self._thickness_slider.value(),
                'corner_radius': self._corner_slider.value(),
                'auto_width': self._auto_width_cb.isChecked(),
                'auto_height': self._auto_height_cb.isChecked(),
                'padding_top': self._padding_top.value(),
                'padding_bottom': self._padding_bottom.value(),
                'padding_left': self._padding_left.value(),
                'padding_right': self._padding_right.value(),
                'edge_style': edge_style_map.get(self._edge_style_combo.currentText(), 'none'),
                'edge_size': self._edge_size_slider.value(),
                'edge_top_only': self._edge_top_only_cb.isChecked(),
                'custom_svg_paths': self._custom_svg_paths,
                'custom_svg_name': self._custom_svg_name,
                'layered_enabled': self._layered_enabled_cb.isChecked(),
                'layer_count': self._layer_count_spin.value(),
                'layer_offset': self._layer_offset_slider.value(),
                'layer_shrink': self._layer_shrink_slider.value(),
                'inset_enabled': self._inset_enabled_cb.isChecked(),
                'inset_depth': self._inset_depth_slider.value(),
                'inset_margin': self._inset_margin_slider.value(),
                'inset_corner_radius': self._inset_corner_slider.value(),
            },
            'sweeping': {
                'width': self._width_slider.value(),
                'height': self._height_slider.value(),
                'thickness': self._thickness_slider.value(),
                'curve_angle': self._curve_angle_slider.value(),
                'curve_radius': self._curve_radius_slider.value(),
                'base_type': self._base_type_combo.currentText().lower(),
            },
            'pattern': {
                'type': pattern_map.get(self._pattern_combo.currentText(), 'none'),
                'spacing': self._pattern_spacing.value(),
                'size': self._pattern_size.value(),
                'depth': self._pattern_depth.value(),
            },
            'border': {
                'enabled': self._border_enabled_cb.isChecked(),
                'style': border_style_map.get(self._border_style_combo.currentText(), 'raised'),
                'width': self._border_width_slider.value(),
                'height': self._border_height_slider.value(),
                'offset': self._border_offset_slider.value(),
            }
        }
    
    def set_config(self, config: dict):
        """Set the base plate configuration."""
        # Block signals during bulk configuration to prevent cascade updates
        self.blockSignals(True)

        try:
            plate = config.get('plate', {})
            sweeping = config.get('sweeping', {})

            shape_map = {
                "none": "None (Text Only)",
                "rectangle": "Rectangle",
                "rounded_rectangle": "Rounded Rectangle",
                "oval": "Oval",
                "chamfered": "Chamfered",
                "hexagon": "Hexagon",
                "octagon": "Octagon",
                "badge": "Badge",
                "keychain": "Keychain",
                "star": "Star",
                "diamond": "Diamond",
                "arrow": "Arrow",
                "heart": "Heart",
                "cloud": "Cloud",
                "sweeping": "Sweeping (Curved)",
                "custom": "Custom SVG",
            }
            self._shape_combo.setCurrentText(shape_map.get(plate.get('shape'), 'Rounded Rectangle'))

            self._width_slider.setValue(plate.get('width', 120))
            self._height_slider.setValue(plate.get('height', 35))
            self._thickness_slider.setValue(plate.get('thickness', 4))
            self._corner_slider.setValue(plate.get('corner_radius', 5))

            self._auto_width_cb.setChecked(plate.get('auto_width', False))
            self._auto_height_cb.setChecked(plate.get('auto_height', False))

            self._padding_top.setValue(plate.get('padding_top', 5))
            self._padding_bottom.setValue(plate.get('padding_bottom', 5))
            self._padding_left.setValue(plate.get('padding_left', 10))
            self._padding_right.setValue(plate.get('padding_right', 10))

            self._curve_angle_slider.setValue(sweeping.get('curve_angle', 45))
            self._curve_radius_slider.setValue(sweeping.get('curve_radius', 80))

            base_type_map = {"pedestal": "Pedestal", "minimal": "Minimal", "flat": "Flat"}
            self._base_type_combo.setCurrentText(base_type_map.get(sweeping.get('base_type'), 'Pedestal'))

            # Custom SVG settings
            self._custom_svg_paths = plate.get('custom_svg_paths', [])
            self._custom_svg_name = plate.get('custom_svg_name', '')
            if self._custom_svg_name:
                self._custom_svg_label.setText(f"Loaded: {self._custom_svg_name}")
            else:
                self._custom_svg_label.setText("No SVG loaded")

            # Layered plate settings
            layered_enabled = plate.get('layered_enabled', False)
            self._layered_enabled_cb.setChecked(layered_enabled)
            self._layer_count_spin.setValue(plate.get('layer_count', 2))
            self._layer_offset_slider.setValue(plate.get('layer_offset', 2.0))
            self._layer_shrink_slider.setValue(plate.get('layer_shrink', 3.0))
            self._layer_count_spin.setVisible(layered_enabled)
            self._layer_offset_slider.setVisible(layered_enabled)
            self._layer_shrink_slider.setVisible(layered_enabled)

            # Inset panel settings
            inset_enabled = plate.get('inset_enabled', False)
            self._inset_enabled_cb.setChecked(inset_enabled)
            self._inset_depth_slider.setValue(plate.get('inset_depth', 1.0))
            self._inset_margin_slider.setValue(plate.get('inset_margin', 5.0))
            self._inset_corner_slider.setValue(plate.get('inset_corner_radius', 3.0))
            self._inset_depth_slider.setVisible(inset_enabled)
            self._inset_margin_slider.setVisible(inset_enabled)
            self._inset_corner_slider.setVisible(inset_enabled)

            # Update UI visibility for shape type
            shape_text = self._shape_combo.currentText()
            is_none = "None" in shape_text
            is_sweeping = "Sweeping" in shape_text
            is_custom = "Custom SVG" in shape_text
            self._sweep_group.setVisible(is_sweeping)
            self._options_group.setVisible(not is_sweeping and not is_none and not is_custom)
            self._custom_svg_btn.setVisible(is_custom)
            self._custom_svg_label.setVisible(is_custom)
            for widget in [self._width_slider, self._height_slider, self._thickness_slider,
                           self._auto_width_cb, self._auto_height_cb]:
                widget.setEnabled(not is_none)

            # Pattern settings
            pattern = config.get('pattern', {})
            pattern_map = {
                "none": "None", "grid": "Grid", "dots": "Dots",
                "diamonds": "Diamonds", "hexagons": "Hexagons",
                "lines": "Lines", "crosshatch": "Crosshatch", "chevron": "Chevron"
            }
            pattern_text = pattern_map.get(pattern.get('type'), 'None')
            self._pattern_combo.setCurrentText(pattern_text)
            self._pattern_spacing.setValue(pattern.get('spacing', 5))
            self._pattern_size.setValue(pattern.get('size', 1))
            self._pattern_depth.setValue(pattern.get('depth', 0.3))

            # Update pattern visibility
            has_pattern = pattern_text != "None"
            self._pattern_spacing.setVisible(has_pattern)
            self._pattern_size.setVisible(has_pattern)
            self._pattern_depth.setVisible(has_pattern)

            # Edge finishing settings
            edge_style_map = {"none": "None", "chamfer": "Chamfer", "fillet": "Fillet"}
            edge_style_text = edge_style_map.get(plate.get('edge_style'), 'None')
            self._edge_style_combo.setCurrentText(edge_style_text)
            self._edge_size_slider.setValue(plate.get('edge_size', 0.5))
            self._edge_top_only_cb.setChecked(plate.get('edge_top_only', True))

            # Update edge visibility
            has_edge = edge_style_text != "None"
            self._edge_size_slider.setVisible(has_edge)
            self._edge_top_only_cb.setVisible(has_edge)

            # Border settings
            border = config.get('border', {})
            border_style_map = {
                "raised": "Raised", "inset": "Inset", "double": "Double",
                "groove": "Groove", "rope": "Rope", "dots": "Dots",
                "dashes": "Dashes", "ornate": "Ornate"
            }
            border_enabled = border.get('enabled', False)
            self._border_enabled_cb.setChecked(border_enabled)
            self._border_style_combo.setCurrentText(border_style_map.get(border.get('style'), 'Raised'))
            self._border_width_slider.setValue(border.get('width', 3))
            self._border_height_slider.setValue(border.get('height', 1.5))
            self._border_offset_slider.setValue(border.get('offset', 2))

            # Update border visibility
            self._border_style_combo.setVisible(border_enabled)
            self._border_width_slider.setVisible(border_enabled)
            self._border_height_slider.setVisible(border_enabled)
            self._border_offset_slider.setVisible(border_enabled)
        finally:
            self.blockSignals(False)

        # Emit a single signal after all configuration is complete
        self.settings_changed.emit()
