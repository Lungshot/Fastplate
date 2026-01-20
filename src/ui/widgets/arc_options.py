"""
Arc Text Options Widget
Encapsulates arc text configuration UI.
"""

from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox
from PyQt5.QtCore import pyqtSignal
from ui.widgets.slider_spin import SliderSpinBox, ResetableComboBox


class ArcOptionsWidget(QGroupBox):
    """
    Widget for arc text options.

    Provides controls for:
    - Enable/disable arc text
    - Arc radius
    - Arc angle
    - Arc direction (clockwise/counterclockwise)
    """

    changed = pyqtSignal()
    dragging = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__("Arc Options", parent)
        self._setup_ui()
        self.setVisible(False)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Radius slider
        self._radius_slider = SliderSpinBox(
            "Radius:", 20, 200, 50, decimals=0, suffix=" mm"
        )
        self._radius_slider.valueChanged.connect(self._on_changed)
        self._radius_slider.dragging.connect(self._on_dragging)
        layout.addWidget(self._radius_slider)

        # Angle slider
        self._angle_slider = SliderSpinBox(
            "Angle:", 30, 360, 180, decimals=0, suffix="°"
        )
        self._angle_slider.valueChanged.connect(self._on_changed)
        self._angle_slider.dragging.connect(self._on_dragging)
        layout.addWidget(self._angle_slider)

        # Direction combo
        dir_row = QHBoxLayout()
        dir_row.addWidget(QLabel("Direction:"))
        self._direction_combo = ResetableComboBox(default_text="Counterclockwise")
        self._direction_combo.addItems(["Counterclockwise", "Clockwise"])
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
        """Get arc configuration as dictionary."""
        dir_map = {"Counterclockwise": "counterclockwise", "Clockwise": "clockwise"}
        return {
            'arc_radius': self._radius_slider.value(),
            'arc_angle': self._angle_slider.value(),
            'arc_direction': dir_map.get(self._direction_combo.currentText(), 'counterclockwise'),
        }

    def set_config(self, config: dict):
        """Set arc configuration from dictionary."""
        if 'arc_radius' in config:
            self._radius_slider.setValue(config['arc_radius'])
        if 'arc_angle' in config:
            self._angle_slider.setValue(config['arc_angle'])
        if 'arc_direction' in config:
            dir_map = {"counterclockwise": "Counterclockwise", "clockwise": "Clockwise"}
            self._direction_combo.setCurrentText(
                dir_map.get(config['arc_direction'], 'Counterclockwise')
            )

    def reset_to_defaults(self):
        """Reset all values to defaults."""
        self._radius_slider.setValue(50)
        self._angle_slider.setValue(180)
        self._direction_combo.reset()


class ArcEnableWidget(QCheckBox):
    """
    Checkbox widget for enabling/disabling arc text.
    Manages visibility of the ArcOptionsWidget.
    """

    def __init__(self, arc_options_widget: ArcOptionsWidget, parent=None):
        super().__init__("Arc Text (Curved)", parent)
        self._arc_options = arc_options_widget
        self.stateChanged.connect(self._on_state_changed)

    def _on_state_changed(self, state: int):
        """Show/hide arc options based on checkbox state."""
        enabled = state == 2  # Qt.Checked
        self._arc_options.setVisible(enabled)

    def is_arc_enabled(self) -> bool:
        """Check if arc text is enabled."""
        return self.isChecked()

    def set_arc_enabled(self, enabled: bool):
        """Set arc text enabled state."""
        self.setChecked(enabled)
        self._arc_options.setVisible(enabled)
