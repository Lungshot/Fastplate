"""
Base Plate Settings Panel
UI panel for configuring base plate shape and dimensions.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QCheckBox, QFrame
)
from PyQt5.QtCore import pyqtSignal

from ui.widgets.slider_spin import SliderSpinBox, FocusComboBox, ResetableComboBox


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
            "Sweeping (Curved)"
        ])
        self._shape_combo.setCurrentText("Rounded Rectangle")
        self._shape_combo.currentTextChanged.connect(self._on_shape_changed)
        shape_row.addWidget(self._shape_combo, stretch=1)
        shape_layout.addLayout(shape_row)
        
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
        
        layout.addStretch()
    
    def _on_shape_changed(self, shape_text):
        """Handle shape type change."""
        is_none = "None" in shape_text
        is_sweeping = "Sweeping" in shape_text

        # Hide/show dimension groups based on shape
        self._sweep_group.setVisible(is_sweeping)
        self._options_group.setVisible(not is_sweeping and not is_none)

        # Disable dimensions when no plate selected
        for widget in [self._width_slider, self._height_slider, self._thickness_slider,
                       self._auto_width_cb, self._auto_height_cb]:
            widget.setEnabled(not is_none)

        self._on_changed()
    
    def _on_auto_changed(self, state):
        """Handle auto-size checkbox change."""
        self._width_slider.setEnabled(not self._auto_width_cb.isChecked())
        self._height_slider.setEnabled(not self._auto_height_cb.isChecked())
        self._on_changed()
    
    def _on_changed(self, *args):
        self.settings_changed.emit()
    
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
            "Sweeping (Curved)": "sweeping",
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
            },
            'sweeping': {
                'width': self._width_slider.value(),
                'height': self._height_slider.value(),
                'thickness': self._thickness_slider.value(),
                'curve_angle': self._curve_angle_slider.value(),
                'curve_radius': self._curve_radius_slider.value(),
                'base_type': self._base_type_combo.currentText().lower(),
            }
        }
    
    def set_config(self, config: dict):
        """Set the base plate configuration."""
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
            "sweeping": "Sweeping (Curved)",
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
