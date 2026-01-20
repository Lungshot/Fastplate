"""
Sweeping Text Options Widget
Encapsulates sweeping text configuration UI.
"""

from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import pyqtSignal
from ui.widgets.slider_spin import SliderSpinBox, ResetableComboBox


class SweepingOptionsWidget(QGroupBox):
    """
    Widget for sweeping text options.

    Provides controls for:
    - Sweep radius
    - Sweep angle
    - Sweep direction (up/down)
    """

    changed = pyqtSignal()
    dragging = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__("Sweeping Options", parent)
        self._setup_ui()
        self.setVisible(False)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Sweep radius slider
        self._radius_slider = SliderSpinBox(
            "Sweep Radius:", 5, 50, 13, decimals=1, suffix=" mm"
        )
        self._radius_slider.valueChanged.connect(self._on_changed)
        self._radius_slider.dragging.connect(self._on_dragging)
        layout.addWidget(self._radius_slider)

        # Sweep angle slider
        self._angle_slider = SliderSpinBox(
            "Sweep Angle:", 20, 180, 65, decimals=0, suffix="°"
        )
        self._angle_slider.valueChanged.connect(self._on_changed)
        self._angle_slider.dragging.connect(self._on_dragging)
        layout.addWidget(self._angle_slider)

        # Direction combo
        dir_row = QHBoxLayout()
        dir_row.addWidget(QLabel("Direction:"))
        self._direction_combo = ResetableComboBox(default_text="Up")
        self._direction_combo.addItems(["Up", "Down"])
        self._direction_combo.currentTextChanged.connect(self._on_changed)
        dir_row.addWidget(self._direction_combo, stretch=1)
        layout.addLayout(dir_row)

    def _on_changed(self):
        """Emit changed signal."""
        self.changed.emit()

    def _on_dragging(self, is_dragging: bool):
        """Emit dragging signal."""
        self.dragging.emit(is_dragging)

    def get_config(self) -> dict:
        """Get sweeping configuration as dictionary."""
        dir_map = {"Up": "up", "Down": "down"}
        return {
            'sweep_radius': self._radius_slider.value(),
            'sweep_angle': self._angle_slider.value(),
            'sweep_direction': dir_map.get(self._direction_combo.currentText(), 'up'),
        }

    def set_config(self, config: dict):
        """Set sweeping configuration from dictionary."""
        if 'sweep_radius' in config:
            self._radius_slider.setValue(config['sweep_radius'])
        if 'sweep_angle' in config:
            self._angle_slider.setValue(config['sweep_angle'])
        if 'sweep_direction' in config:
            dir_map = {"up": "Up", "down": "Down"}
            self._direction_combo.setCurrentText(
                dir_map.get(config['sweep_direction'], 'Up')
            )

    def reset_to_defaults(self):
        """Reset all values to defaults."""
        self._radius_slider.setValue(13)
        self._angle_slider.setValue(65)
        self._direction_combo.reset()
