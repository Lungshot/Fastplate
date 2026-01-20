"""
Mount Settings Panel
UI panel for configuring mounting options.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QCheckBox, QStackedWidget
)
from PyQt5.QtCore import pyqtSignal

from ui.widgets.slider_spin import SliderSpinBox, FocusComboBox, ResetableComboBox


class MountPanel(QWidget):
    """Panel for mounting settings."""

    settings_changed = pyqtSignal()
    # Signal for real-time preview during slider drag
    slider_dragging = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Mount type selection
        type_group = QGroupBox("Mounting Type")
        type_layout = QVBoxLayout(type_group)
        
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Type:"))
        self._type_combo = ResetableComboBox(default_text="None")
        self._type_combo.addItems([
            "None",
            "Desk Stand",
            "Screw Holes",
            "Keyhole Slots",
            "Magnet Pockets",
            "Hanging Hole",
            "Lanyard Slot",
            "Adhesive Recess",
            "Clip Mount"
        ])
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_row.addWidget(self._type_combo, stretch=1)
        type_layout.addLayout(type_row)
        
        layout.addWidget(type_group)
        
        # Options stack (different options for each mount type)
        self._options_stack = QStackedWidget()
        
        # None options (empty)
        self._none_widget = QWidget()
        self._options_stack.addWidget(self._none_widget)
        
        # Desk stand options
        self._stand_widget = self._create_stand_options()
        self._options_stack.addWidget(self._stand_widget)
        
        # Screw holes options
        self._screw_widget = self._create_screw_options()
        self._options_stack.addWidget(self._screw_widget)
        
        # Keyhole options
        self._keyhole_widget = self._create_keyhole_options()
        self._options_stack.addWidget(self._keyhole_widget)
        
        # Magnet options
        self._magnet_widget = self._create_magnet_options()
        self._options_stack.addWidget(self._magnet_widget)
        
        # Hanging hole options
        self._hanging_widget = self._create_hanging_options()
        self._options_stack.addWidget(self._hanging_widget)

        # Lanyard slot options
        self._lanyard_widget = self._create_lanyard_options()
        self._options_stack.addWidget(self._lanyard_widget)

        # Adhesive options
        self._adhesive_widget = self._create_adhesive_options()
        self._options_stack.addWidget(self._adhesive_widget)

        # Clip mount options
        self._clip_widget = self._create_clip_options()
        self._options_stack.addWidget(self._clip_widget)

        layout.addWidget(self._options_stack)
        layout.addStretch()
    
    def _create_stand_options(self) -> QWidget:
        """Create desk stand options widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group = QGroupBox("Desk Stand Options")
        group_layout = QVBoxLayout(group)
        
        self._stand_angle = SliderSpinBox("Angle:", 10, 75, 25, decimals=0, suffix="°")
        self._stand_angle.valueChanged.connect(self._on_changed)
        self._stand_angle.dragging.connect(self._on_slider_dragging)
        group_layout.addWidget(self._stand_angle)

        self._stand_depth = SliderSpinBox("Depth:", 15, 60, 30, decimals=0, suffix=" mm")
        self._stand_depth.valueChanged.connect(self._on_changed)
        self._stand_depth.dragging.connect(self._on_slider_dragging)
        group_layout.addWidget(self._stand_depth)
        
        self._stand_integrated = QCheckBox("Integrated (single piece)")
        self._stand_integrated.setChecked(True)
        self._stand_integrated.stateChanged.connect(self._on_changed)
        group_layout.addWidget(self._stand_integrated)
        
        layout.addWidget(group)
        return widget
    
    def _create_screw_options(self) -> QWidget:
        """Create screw hole options widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group = QGroupBox("Screw Hole Options")
        group_layout = QVBoxLayout(group)
        
        pattern_row = QHBoxLayout()
        pattern_row.addWidget(QLabel("Pattern:"))
        self._hole_pattern = ResetableComboBox(default_text="Two Top")
        self._hole_pattern.addItems([
            "Two Top",
            "Two Sides",
            "Four Corners",
            "Center Top"
        ])
        self._hole_pattern.currentTextChanged.connect(self._on_changed)
        pattern_row.addWidget(self._hole_pattern, stretch=1)
        group_layout.addLayout(pattern_row)
        
        self._hole_diameter = SliderSpinBox("Hole Diameter:", 2, 10, 4, decimals=1, suffix=" mm")
        self._hole_diameter.valueChanged.connect(self._on_changed)
        self._hole_diameter.dragging.connect(self._on_slider_dragging)
        group_layout.addWidget(self._hole_diameter)

        self._countersink = QCheckBox("Countersink")
        self._countersink.setChecked(True)
        self._countersink.stateChanged.connect(self._on_changed)
        group_layout.addWidget(self._countersink)

        self._hole_edge = SliderSpinBox("Edge Distance:", 3, 20, 8, decimals=1, suffix=" mm")
        self._hole_edge.valueChanged.connect(self._on_changed)
        self._hole_edge.dragging.connect(self._on_slider_dragging)
        group_layout.addWidget(self._hole_edge)
        
        layout.addWidget(group)
        return widget
    
    def _create_keyhole_options(self) -> QWidget:
        """Create keyhole options widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group = QGroupBox("Keyhole Options")
        group_layout = QVBoxLayout(group)
        
        self._keyhole_large = SliderSpinBox("Large Diameter:", 6, 15, 10, decimals=1, suffix=" mm")
        self._keyhole_large.valueChanged.connect(self._on_changed)
        self._keyhole_large.dragging.connect(self._on_slider_dragging)
        group_layout.addWidget(self._keyhole_large)

        self._keyhole_small = SliderSpinBox("Small Diameter:", 3, 10, 5, decimals=1, suffix=" mm")
        self._keyhole_small.valueChanged.connect(self._on_changed)
        self._keyhole_small.dragging.connect(self._on_slider_dragging)
        group_layout.addWidget(self._keyhole_small)

        self._keyhole_length = SliderSpinBox("Slot Length:", 8, 25, 12, decimals=1, suffix=" mm")
        self._keyhole_length.valueChanged.connect(self._on_changed)
        self._keyhole_length.dragging.connect(self._on_slider_dragging)
        group_layout.addWidget(self._keyhole_length)
        
        layout.addWidget(group)
        return widget
    
    def _create_magnet_options(self) -> QWidget:
        """Create magnet pocket options widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group = QGroupBox("Magnet Pocket Options")
        group_layout = QVBoxLayout(group)
        
        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Magnet Size:"))
        self._magnet_size = ResetableComboBox(default_text="8x3mm Disc")
        self._magnet_size.addItems([
            "6x2mm Disc",
            "8x3mm Disc",
            "10x2mm Disc",
            "10x3mm Disc",
            "12x2mm Disc",
            "5mm Cube"
        ])
        self._magnet_size.setCurrentText("8x3mm Disc")
        self._magnet_size.currentTextChanged.connect(self._on_changed)
        size_row.addWidget(self._magnet_size, stretch=1)
        group_layout.addLayout(size_row)

        count_row = QHBoxLayout()
        count_row.addWidget(QLabel("Count:"))
        self._magnet_count = ResetableComboBox(default_text="2")
        self._magnet_count.addItems(["2", "4"])
        self._magnet_count.currentTextChanged.connect(self._on_changed)
        count_row.addWidget(self._magnet_count, stretch=1)
        group_layout.addLayout(count_row)
        
        self._magnet_edge = SliderSpinBox("Edge Distance:", 5, 25, 10, decimals=1, suffix=" mm")
        self._magnet_edge.valueChanged.connect(self._on_changed)
        self._magnet_edge.dragging.connect(self._on_slider_dragging)
        group_layout.addWidget(self._magnet_edge)
        
        layout.addWidget(group)
        return widget
    
    def _create_hanging_options(self) -> QWidget:
        """Create hanging hole options widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group = QGroupBox("Hanging Hole Options")
        group_layout = QVBoxLayout(group)
        
        pos_row = QHBoxLayout()
        pos_row.addWidget(QLabel("Position:"))
        self._hanging_pos = ResetableComboBox(default_text="Top Center")
        self._hanging_pos.addItems(["Top Center", "Top Corners"])
        self._hanging_pos.currentTextChanged.connect(self._on_changed)
        pos_row.addWidget(self._hanging_pos, stretch=1)
        group_layout.addLayout(pos_row)
        
        self._hanging_diameter = SliderSpinBox("Diameter:", 3, 10, 5, decimals=1, suffix=" mm")
        self._hanging_diameter.valueChanged.connect(self._on_changed)
        self._hanging_diameter.dragging.connect(self._on_slider_dragging)
        group_layout.addWidget(self._hanging_diameter)
        
        layout.addWidget(group)
        return widget

    def _create_lanyard_options(self) -> QWidget:
        """Create lanyard slot options widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("Lanyard Slot Options")
        group_layout = QVBoxLayout(group)

        pos_row = QHBoxLayout()
        pos_row.addWidget(QLabel("Position:"))
        self._lanyard_pos = ResetableComboBox(default_text="Top Center")
        self._lanyard_pos.addItems(["Top Center", "Top Left", "Top Right", "Both Sides"])
        self._lanyard_pos.currentTextChanged.connect(self._on_changed)
        pos_row.addWidget(self._lanyard_pos, stretch=1)
        group_layout.addLayout(pos_row)

        self._lanyard_width = SliderSpinBox("Slot Width:", 8, 30, 15, decimals=1, suffix=" mm")
        self._lanyard_width.valueChanged.connect(self._on_changed)
        self._lanyard_width.dragging.connect(self._on_slider_dragging)
        group_layout.addWidget(self._lanyard_width)

        self._lanyard_height = SliderSpinBox("Slot Height:", 2, 8, 4, decimals=1, suffix=" mm")
        self._lanyard_height.valueChanged.connect(self._on_changed)
        self._lanyard_height.dragging.connect(self._on_slider_dragging)
        group_layout.addWidget(self._lanyard_height)

        layout.addWidget(group)
        return widget

    def _create_adhesive_options(self) -> QWidget:
        """Create adhesive recess options widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("Adhesive Recess")
        group_layout = QVBoxLayout(group)

        info = QLabel("Creates shallow recesses on the back\nfor adhesive strips or tape.")
        info.setStyleSheet("color: #888;")
        group_layout.addWidget(info)

        layout.addWidget(group)
        return widget

    def _create_clip_options(self) -> QWidget:
        """Create clip mount options widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("Clip Mount Options")
        group_layout = QVBoxLayout(group)

        info = QLabel("Creates a spring clip on the back\nfor clipping onto edges or pockets.")
        info.setStyleSheet("color: #888;")
        group_layout.addWidget(info)

        pos_row = QHBoxLayout()
        pos_row.addWidget(QLabel("Position:"))
        self._clip_pos = ResetableComboBox(default_text="Back Top")
        self._clip_pos.addItems(["Back Top", "Back Bottom", "Both"])
        self._clip_pos.currentTextChanged.connect(self._on_changed)
        pos_row.addWidget(self._clip_pos, stretch=1)
        group_layout.addLayout(pos_row)

        self._clip_width = SliderSpinBox("Clip Width:", 10, 50, 20, decimals=0, suffix=" mm")
        self._clip_width.valueChanged.connect(self._on_changed)
        self._clip_width.dragging.connect(self._on_slider_dragging)
        group_layout.addWidget(self._clip_width)

        self._clip_thickness = SliderSpinBox("Clip Thickness:", 1, 4, 2, decimals=1, suffix=" mm")
        self._clip_thickness.valueChanged.connect(self._on_changed)
        self._clip_thickness.dragging.connect(self._on_slider_dragging)
        group_layout.addWidget(self._clip_thickness)

        self._clip_gap = SliderSpinBox("Clip Gap:", 1, 8, 3, decimals=1, suffix=" mm")
        self._clip_gap.valueChanged.connect(self._on_changed)
        self._clip_gap.dragging.connect(self._on_slider_dragging)
        group_layout.addWidget(self._clip_gap)

        layout.addWidget(group)
        return widget

    def _on_type_changed(self, index):
        """Handle mount type change."""
        self._options_stack.setCurrentIndex(index)
        self._on_changed()

    def _on_changed(self, *args):
        self.settings_changed.emit()

    def _on_slider_dragging(self, value):
        """Emit slider_dragging for real-time preview during slider drag."""
        self.slider_dragging.emit()
    
    def get_config(self) -> dict:
        """Get the mount configuration."""
        type_map = {
            0: "none",
            1: "desk_stand",
            2: "screw_holes",
            3: "keyhole",
            4: "magnet_pockets",
            5: "hanging_hole",
            6: "lanyard_slot",
            7: "adhesive_recess",
            8: "clip_mount"
        }
        
        pattern_map = {
            "Two Top": "two_top",
            "Two Sides": "two_sides",
            "Four Corners": "four_corners",
            "Center Top": "center_top"
        }
        
        return {
            'type': type_map.get(self._type_combo.currentIndex(), 'none'),
            'stand_angle': self._stand_angle.value(),
            'stand_depth': self._stand_depth.value(),
            'stand_integrated': self._stand_integrated.isChecked(),
            'hole_pattern': pattern_map.get(self._hole_pattern.currentText(), 'two_top'),
            'hole_diameter': self._hole_diameter.value(),
            'countersink': self._countersink.isChecked(),
            'hole_edge_distance': self._hole_edge.value(),
            'keyhole_large': self._keyhole_large.value(),
            'keyhole_small': self._keyhole_small.value(),
            'keyhole_length': self._keyhole_length.value(),
            'magnet_size': self._magnet_size.currentText(),
            'magnet_count': int(self._magnet_count.currentText()),
            'magnet_edge': self._magnet_edge.value(),
            'hanging_position': self._hanging_pos.currentText().lower().replace(' ', '_'),
            'hanging_diameter': self._hanging_diameter.value(),
            'lanyard_position': self._lanyard_pos.currentText().lower().replace(' ', '_'),
            'lanyard_width': self._lanyard_width.value(),
            'lanyard_height': self._lanyard_height.value(),
            'clip_position': self._clip_pos.currentText().lower().replace(' ', '_'),
            'clip_width': self._clip_width.value(),
            'clip_thickness': self._clip_thickness.value(),
            'clip_gap': self._clip_gap.value(),
        }
    
    def set_config(self, config: dict):
        """Set the mount configuration."""
        # Block signals during bulk configuration to prevent cascade updates
        self.blockSignals(True)

        try:
            type_map = {
                "none": 0,
                "desk_stand": 1,
                "screw_holes": 2,
                "keyhole": 3,
                "magnet_pockets": 4,
                "hanging_hole": 5,
                "lanyard_slot": 6,
                "adhesive_recess": 7,
                "clip_mount": 8
            }
            self._type_combo.setCurrentIndex(type_map.get(config.get('type'), 0))
            self._options_stack.setCurrentIndex(type_map.get(config.get('type'), 0))

            if 'stand_angle' in config:
                self._stand_angle.setValue(config['stand_angle'])
            if 'stand_depth' in config:
                self._stand_depth.setValue(config['stand_depth'])
            if 'stand_integrated' in config:
                self._stand_integrated.setChecked(config['stand_integrated'])

            pattern_map = {
                "two_top": "Two Top",
                "two_sides": "Two Sides",
                "four_corners": "Four Corners",
                "center_top": "Center Top"
            }
            self._hole_pattern.setCurrentText(pattern_map.get(config.get('hole_pattern'), 'Two Top'))

            if 'hole_diameter' in config:
                self._hole_diameter.setValue(config['hole_diameter'])
            if 'countersink' in config:
                self._countersink.setChecked(config['countersink'])
            if 'hole_edge_distance' in config:
                self._hole_edge.setValue(config['hole_edge_distance'])

            # Keyhole settings
            if 'keyhole_large' in config:
                self._keyhole_large.setValue(config['keyhole_large'])
            if 'keyhole_small' in config:
                self._keyhole_small.setValue(config['keyhole_small'])
            if 'keyhole_length' in config:
                self._keyhole_length.setValue(config['keyhole_length'])

            # Magnet settings
            if 'magnet_size' in config:
                self._magnet_size.setCurrentText(config['magnet_size'])
            if 'magnet_count' in config:
                self._magnet_count.setCurrentText(str(config['magnet_count']))
            if 'magnet_edge' in config:
                self._magnet_edge.setValue(config['magnet_edge'])

            # Hanging hole settings
            pos_map = {
                "top_center": "Top Center",
                "top_corners": "Top Corners",
                "corners": "Top Corners"
            }
            if 'hanging_position' in config:
                self._hanging_pos.setCurrentText(pos_map.get(config['hanging_position'], 'Top Center'))
            if 'hanging_diameter' in config:
                self._hanging_diameter.setValue(config['hanging_diameter'])

            # Lanyard slot settings
            lanyard_pos_map = {
                "top_center": "Top Center",
                "top_left": "Top Left",
                "top_right": "Top Right",
                "both_sides": "Both Sides"
            }
            if 'lanyard_position' in config:
                self._lanyard_pos.setCurrentText(lanyard_pos_map.get(config['lanyard_position'], 'Top Center'))
            if 'lanyard_width' in config:
                self._lanyard_width.setValue(config['lanyard_width'])
            if 'lanyard_height' in config:
                self._lanyard_height.setValue(config['lanyard_height'])

            # Clip mount settings
            clip_pos_map = {
                "back_top": "Back Top",
                "back_bottom": "Back Bottom",
                "both": "Both"
            }
            if 'clip_position' in config:
                self._clip_pos.setCurrentText(clip_pos_map.get(config['clip_position'], 'Back Top'))
            if 'clip_width' in config:
                self._clip_width.setValue(config['clip_width'])
            if 'clip_thickness' in config:
                self._clip_thickness.setValue(config['clip_thickness'])
            if 'clip_gap' in config:
                self._clip_gap.setValue(config['clip_gap'])
        finally:
            self.blockSignals(False)

        # Emit a single signal after all configuration is complete
        self.settings_changed.emit()
