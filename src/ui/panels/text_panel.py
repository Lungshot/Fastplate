"""
Text Settings Panel
UI panel for configuring text content and styling.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QGroupBox, QToolButton, QSizePolicy, QCheckBox
)
from PyQt5.QtCore import pyqtSignal, Qt

from ui.widgets.slider_spin import SliderSpinBox, LabeledComboBox, LabeledLineEdit, FocusComboBox, ResetableComboBox
from core.geometry.text_builder import TextStyle, TextAlign


class TextSegmentWidget(QFrame):
    """Widget for configuring a single text segment within a line."""

    changed = pyqtSignal()
    remove_requested = pyqtSignal(object)
    move_up_requested = pyqtSignal(object)
    move_down_requested = pyqtSignal(object)
    # Signal for real-time position preview: (segment_id, v_offset)
    position_dragging = pyqtSignal(str, float)
    drag_started = pyqtSignal()
    drag_ended = pyqtSignal()
    # Signal for real-time preview during any slider drag (font size, spacing)
    slider_dragging = pyqtSignal()

    # Stylesheet for the segment widget with improved visibility
    SEGMENT_STYLE = """
        TextSegmentWidget {
            background-color: #4a4a4a;
            border: 1px solid #666;
            border-radius: 4px;
            margin: 2px;
        }
        QLabel {
            color: #ddd;
        }
        QLineEdit {
            background-color: #555;
            border: 1px solid #777;
            border-radius: 3px;
            padding: 3px;
            color: #fff;
        }
        QComboBox {
            background-color: #5a5a5a;
            border: 1px solid #888;
            border-radius: 3px;
            padding: 3px;
            color: #fff;
        }
        QComboBox:hover {
            background-color: #656565;
            border: 1px solid #999;
        }
        QComboBox::drop-down {
            border: none;
        }
        QToolButton {
            background-color: #555;
            border: 1px solid #666;
            border-radius: 3px;
            color: #ccc;
        }
        QToolButton:hover {
            background-color: #666;
            border: 1px solid #888;
        }
        QSlider::groove:horizontal {
            background: #555;
            height: 6px;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #888;
            width: 14px;
            margin: -4px 0;
            border-radius: 7px;
            border: 1px solid #999;
        }
        QSlider::handle:horizontal:hover {
            background: #aaa;
        }
        QSlider::sub-page:horizontal {
            background: #6a8fbd;
            border-radius: 3px;
        }
    """

    def __init__(self, segment_number: int = 1, parent=None):
        super().__init__(parent)
        self.segment_number = segment_number
        self.is_icon = False  # Track if this segment is a Nerd Font icon
        self._segment_id = f"text_seg_{id(self)}"  # Unique ID for real-time preview

        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet(self.SEGMENT_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Header with segment label and control buttons
        header = QHBoxLayout()
        header.setSpacing(3)

        self._label = QLabel(f"Seg {segment_number}")
        self._label.setStyleSheet("font-size: 10px; font-weight: bold; color: #bbb;")
        header.addWidget(self._label)
        header.addStretch()

        # Move up button
        self._up_btn = QToolButton()
        self._up_btn.setText("◀")
        self._up_btn.setFixedSize(20, 20)
        self._up_btn.setToolTip("Move segment left")
        self._up_btn.clicked.connect(lambda: self.move_up_requested.emit(self))
        header.addWidget(self._up_btn)

        # Move down button
        self._down_btn = QToolButton()
        self._down_btn.setText("▶")
        self._down_btn.setFixedSize(20, 20)
        self._down_btn.setToolTip("Move segment right")
        self._down_btn.clicked.connect(lambda: self.move_down_requested.emit(self))
        header.addWidget(self._down_btn)

        # Remove button
        self._remove_btn = QToolButton()
        self._remove_btn.setText("✕")
        self._remove_btn.setFixedSize(20, 20)
        self._remove_btn.setStyleSheet("QToolButton { font-weight: bold; color: #ff6666; } QToolButton:hover { color: #ff8888; background-color: #553333; }")
        self._remove_btn.setToolTip("Remove segment")
        self._remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        header.addWidget(self._remove_btn)

        layout.addLayout(header)

        # Text content
        self._content_edit = QLineEdit()
        self._content_edit.setPlaceholderText("Text...")
        self._content_edit.textChanged.connect(self._on_changed)
        layout.addWidget(self._content_edit)

        # Text transform buttons
        transform_row = QHBoxLayout()
        transform_row.setSpacing(2)

        upper_btn = QToolButton()
        upper_btn.setText("ABC")
        upper_btn.setToolTip("UPPERCASE")
        upper_btn.setFixedSize(36, 20)
        upper_btn.clicked.connect(self._to_uppercase)
        transform_row.addWidget(upper_btn)

        lower_btn = QToolButton()
        lower_btn.setText("abc")
        lower_btn.setToolTip("lowercase")
        lower_btn.setFixedSize(36, 20)
        lower_btn.clicked.connect(self._to_lowercase)
        transform_row.addWidget(lower_btn)

        title_btn = QToolButton()
        title_btn.setText("Abc")
        title_btn.setToolTip("Title Case")
        title_btn.setFixedSize(36, 20)
        title_btn.clicked.connect(self._to_titlecase)
        transform_row.addWidget(title_btn)

        transform_row.addStretch()
        layout.addLayout(transform_row)

        # Font selection row
        font_row = QHBoxLayout()
        font_row.setSpacing(4)

        self._font_combo = FocusComboBox()
        self._font_combo.setMinimumWidth(100)
        self._font_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._font_combo.currentTextChanged.connect(self._on_changed)
        font_row.addWidget(self._font_combo)

        self._style_combo = FocusComboBox()
        self._style_combo.addItems(["Regular", "Bold", "Italic", "Bold Italic"])
        self._style_combo.setFixedWidth(85)
        self._style_combo.currentTextChanged.connect(self._on_changed)
        font_row.addWidget(self._style_combo)

        layout.addLayout(font_row)

        # Size and spacing row
        size_row = QHBoxLayout()
        size_row.setSpacing(4)

        size_label = QLabel("Size:")
        size_label.setStyleSheet("font-weight: bold;")
        size_row.addWidget(size_label)
        self._size_slider = SliderSpinBox("", 4, 50, 12, decimals=1, suffix="mm")
        self._size_slider.valueChanged.connect(self._on_changed)
        self._size_slider.dragging.connect(self._on_slider_dragging)
        size_row.addWidget(self._size_slider)

        layout.addLayout(size_row)

        # Letter spacing
        spacing_row = QHBoxLayout()
        spacing_row.setSpacing(4)
        spacing_label = QLabel("Spacing:")
        spacing_label.setStyleSheet("font-weight: bold;")
        spacing_row.addWidget(spacing_label)
        self._spacing_slider = SliderSpinBox("", -50, 100, 0, decimals=0, suffix="%")
        self._spacing_slider.valueChanged.connect(self._on_changed)
        self._spacing_slider.dragging.connect(self._on_slider_dragging)
        spacing_row.addWidget(self._spacing_slider)
        layout.addLayout(spacing_row)

        # Vertical offset
        voffset_row = QHBoxLayout()
        voffset_row.setSpacing(4)
        voffset_label = QLabel("V-Offset:")
        voffset_label.setStyleSheet("font-weight: bold;")
        voffset_row.addWidget(voffset_label)
        self._voffset_slider = SliderSpinBox("", -10, 10, 0, decimals=1, suffix="mm")
        self._voffset_slider.valueChanged.connect(self._on_changed)
        # Connect for real-time preview
        self._voffset_slider.dragging.connect(self._on_position_dragging)
        self._voffset_slider.dragStarted.connect(self.drag_started)
        self._voffset_slider.dragEnded.connect(self.drag_ended)
        voffset_row.addWidget(self._voffset_slider)
        layout.addLayout(voffset_row)

    def _on_changed(self, *args):
        self.changed.emit()

    def _on_slider_dragging(self, value):
        """Emit slider_dragging for real-time preview during slider drag."""
        self.slider_dragging.emit()

    def _on_position_dragging(self, value):
        """Emit position during drag for real-time preview."""
        self.position_dragging.emit(self._segment_id, value)

    def get_segment_id(self) -> str:
        """Get the unique segment ID for real-time preview."""
        return self._segment_id

    def _to_uppercase(self):
        """Convert text to UPPERCASE."""
        self._content_edit.setText(self._content_edit.text().upper())

    def _to_lowercase(self):
        """Convert text to lowercase."""
        self._content_edit.setText(self._content_edit.text().lower())

    def _to_titlecase(self):
        """Convert text to Title Case."""
        self._content_edit.setText(self._content_edit.text().title())

    def set_fonts(self, font_names: list):
        """Set available fonts."""
        current = self._font_combo.currentText()
        self._font_combo.clear()
        self._font_combo.addItems(font_names)
        if current in font_names:
            self._font_combo.setCurrentText(current)

    def update_label(self, number: int):
        """Update the segment number label."""
        self.segment_number = number
        self._label.setText(f"Seg {number}")

    def get_config(self) -> dict:
        """Get the segment configuration."""
        return {
            'content': self._content_edit.text(),
            'font_family': self._font_combo.currentText(),
            'font_style': self._style_combo.currentText(),
            'font_size': self._size_slider.value(),
            'letter_spacing': self._spacing_slider.value(),
            'vertical_offset': self._voffset_slider.value(),
            'is_icon': self.is_icon,
        }

    def set_config(self, config: dict):
        """Set the segment configuration."""
        self._content_edit.setText(config.get('content', ''))
        if config.get('font_family'):
            self._font_combo.setCurrentText(config['font_family'])
        if config.get('font_style'):
            self._style_combo.setCurrentText(config['font_style'])
        if config.get('font_size'):
            self._size_slider.setValue(config['font_size'])
        if 'letter_spacing' in config:
            self._spacing_slider.setValue(config['letter_spacing'])
        if 'vertical_offset' in config:
            self._voffset_slider.setValue(config['vertical_offset'])
        self.is_icon = config.get('is_icon', False)


class TextLineWidget(QFrame):
    """Widget for configuring a single line of text with multiple segments."""

    changed = pyqtSignal()
    remove_requested = pyqtSignal(object)
    # Signal for real-time text position preview: (segment_id, v_offset)
    segment_position_dragging = pyqtSignal(str, float)
    drag_started = pyqtSignal()
    drag_ended = pyqtSignal()
    # Signal for real-time preview during any slider drag in segments
    segment_slider_dragging = pyqtSignal()

    def __init__(self, line_number: int = 1, parent=None):
        super().__init__(parent)
        self.line_number = line_number
        self._font_names = []
        self._segment_widgets = []
        self._active_drag_count = 0

        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("QFrame { background-color: #353535; border-radius: 5px; }")

        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        # Header with line number and remove button
        header = QHBoxLayout()
        self._line_label = QLabel(f"Line {line_number}")
        self._line_label.setStyleSheet("font-weight: bold;")
        header.addWidget(self._line_label)
        header.addStretch()

        self._remove_btn = QPushButton("×")
        self._remove_btn.setFixedSize(20, 20)
        self._remove_btn.setStyleSheet("QPushButton { font-weight: bold; }")
        self._remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        header.addWidget(self._remove_btn)
        layout.addLayout(header)

        # Container for segments
        self._segments_container = QWidget()
        self._segments_layout = QVBoxLayout(self._segments_container)
        self._segments_layout.setContentsMargins(0, 0, 0, 0)
        self._segments_layout.setSpacing(3)
        layout.addWidget(self._segments_container)

        # Add segment button and gap slider row
        controls_row = QHBoxLayout()

        add_seg_btn = QPushButton("+ Add Segment")
        add_seg_btn.setFixedWidth(110)
        add_seg_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a7a9a;
                border: 1px solid #5a8aaa;
                border-radius: 4px;
                padding: 4px 8px;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a8aaa;
                border: 1px solid #6a9aba;
            }
            QPushButton:pressed {
                background-color: #3a6a8a;
            }
        """)
        add_seg_btn.clicked.connect(self._add_segment)
        controls_row.addWidget(add_seg_btn)

        controls_row.addWidget(QLabel("Gap:"))
        self._gap_slider = SliderSpinBox("", 0, 10, 2, decimals=1, suffix="mm")
        self._gap_slider.valueChanged.connect(self._on_changed)
        self._gap_slider.dragging.connect(self._on_gap_dragging)
        controls_row.addWidget(self._gap_slider)

        layout.addLayout(controls_row)

        # Add initial segment
        self._add_segment_silent()

    def _add_segment(self):
        """Add a new segment and emit changed signal."""
        self._add_segment_silent()
        self._on_changed()

    def _add_segment_silent(self):
        """Add a new segment without emitting signals."""
        seg_num = len(self._segment_widgets) + 1
        seg_widget = TextSegmentWidget(seg_num)
        seg_widget.set_fonts(self._font_names)
        seg_widget.changed.connect(self._on_changed)
        seg_widget.remove_requested.connect(self._remove_segment)
        seg_widget.move_up_requested.connect(self._move_segment_up)
        seg_widget.move_down_requested.connect(self._move_segment_down)
        # Connect for real-time preview
        seg_widget.position_dragging.connect(self.segment_position_dragging)
        seg_widget.drag_started.connect(self._on_drag_started)
        seg_widget.drag_ended.connect(self._on_drag_ended)
        # Connect slider dragging for real-time preview (font size, spacing)
        seg_widget.slider_dragging.connect(self.segment_slider_dragging)

        self._segment_widgets.append(seg_widget)
        self._segments_layout.addWidget(seg_widget)

    def _remove_segment(self, widget):
        """Remove a segment widget."""
        if len(self._segment_widgets) <= 1:
            return  # Keep at least one segment

        idx = self._segment_widgets.index(widget)
        self._segment_widgets.remove(widget)
        self._segments_layout.removeWidget(widget)
        widget.deleteLater()

        # Renumber remaining segments
        self._renumber_segments()
        self._on_changed()

    def _move_segment_up(self, widget):
        """Move a segment up (left) in the list."""
        idx = self._segment_widgets.index(widget)
        if idx <= 0:
            return  # Already at top

        # Swap with previous
        self._segment_widgets[idx], self._segment_widgets[idx-1] = \
            self._segment_widgets[idx-1], self._segment_widgets[idx]

        # Rebuild layout
        self._rebuild_segments_layout()
        self._on_changed()

    def _move_segment_down(self, widget):
        """Move a segment down (right) in the list."""
        idx = self._segment_widgets.index(widget)
        if idx >= len(self._segment_widgets) - 1:
            return  # Already at bottom

        # Swap with next
        self._segment_widgets[idx], self._segment_widgets[idx+1] = \
            self._segment_widgets[idx+1], self._segment_widgets[idx]

        # Rebuild layout
        self._rebuild_segments_layout()
        self._on_changed()

    def _rebuild_segments_layout(self):
        """Rebuild the segments layout after reordering."""
        # Remove all widgets from layout (but don't delete them)
        for seg in self._segment_widgets:
            self._segments_layout.removeWidget(seg)

        # Re-add in new order
        for seg in self._segment_widgets:
            self._segments_layout.addWidget(seg)

        self._renumber_segments()

    def _renumber_segments(self):
        """Update segment numbers after reordering or removal."""
        for i, seg in enumerate(self._segment_widgets):
            seg.update_label(i + 1)

    def _on_changed(self, *args):
        self.changed.emit()

    def _on_gap_dragging(self, value):
        """Emit segment_slider_dragging for real-time preview during gap slider drag."""
        self.segment_slider_dragging.emit()

    def _on_drag_started(self):
        """Track when a position drag starts."""
        self._active_drag_count += 1
        self.drag_started.emit()

    def _on_drag_ended(self):
        """Track when a position drag ends."""
        self._active_drag_count = max(0, self._active_drag_count - 1)
        self.drag_ended.emit()

    def is_dragging(self) -> bool:
        """Check if any segment is being dragged."""
        return self._active_drag_count > 0

    def set_fonts(self, font_names: list):
        """Set available fonts for all segments."""
        self._font_names = font_names
        for widget in self._segment_widgets:
            widget.set_fonts(font_names)

    def update_line_label(self, number: int):
        """Update the line number label."""
        self.line_number = number
        self._line_label.setText(f"Line {number}")

    def get_config(self) -> dict:
        """Get the line configuration with all segments."""
        segments_config = [w.get_config() for w in self._segment_widgets]

        # For backward compatibility, if there's only one segment,
        # also include legacy single-segment properties
        if len(segments_config) == 1:
            seg = segments_config[0]
            return {
                'content': seg.get('content', ''),
                'font_family': seg.get('font_family', 'Arial'),
                'font_style': seg.get('font_style', 'Regular'),
                'font_size': seg.get('font_size', 12),
                'letter_spacing': seg.get('letter_spacing', 0),
                'segments': segments_config,
                'segment_gap': self._gap_slider.value(),
            }

        return {
            'segments': segments_config,
            'segment_gap': self._gap_slider.value(),
        }

    def set_config(self, config: dict):
        """Set the line configuration."""
        # Block signals during bulk configuration
        self.blockSignals(True)

        try:
            # Clear existing segments
            while self._segment_widgets:
                widget = self._segment_widgets.pop()
                widget.blockSignals(True)
                self._segments_layout.removeWidget(widget)
                widget.deleteLater()

            # Check for new segment format
            segments = config.get('segments', [])

            if segments:
                # New multi-segment format
                for seg_config in segments:
                    self._add_segment_silent()
                    self._segment_widgets[-1].set_config(seg_config)
            else:
                # Legacy single-segment format - convert to segment
                self._add_segment_silent()
                self._segment_widgets[0].set_config({
                    'content': config.get('content', ''),
                    'font_family': config.get('font_family', 'Arial'),
                    'font_style': config.get('font_style', 'Regular'),
                    'font_size': config.get('font_size', 12),
                    'letter_spacing': config.get('letter_spacing', 0),
                })

            # Set gap
            if 'segment_gap' in config:
                self._gap_slider.setValue(config['segment_gap'])

        finally:
            self.blockSignals(False)


class TextPanel(QWidget):
    """Panel for all text settings."""

    settings_changed = pyqtSignal()
    google_icon_selected = pyqtSignal(dict)  # Emitted when Google icon is selected
    font_awesome_icon_selected = pyqtSignal(dict)  # Emitted when Font Awesome icon is selected
    # Signal for real-time text position preview: (segment_id, v_offset)
    text_position_dragging = pyqtSignal(str, float)
    # Signal for real-time preview during any slider drag
    slider_dragging = pyqtSignal()
    # Signals for real-time text scale preview (size, depth)
    text_scale_dragging = pyqtSignal(float, float)
    text_drag_started = pyqtSignal()
    text_drag_ended = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._font_names = []
        self._line_widgets = []
        self._active_drag_count = 0
        self._is_text_dragging = False

        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Text lines section
        lines_group = QGroupBox("Text Lines")
        lines_layout = QVBoxLayout(lines_group)
        
        # Scrollable area for lines
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setMaximumHeight(450)
        
        self._lines_container = QWidget()
        self._lines_layout = QVBoxLayout(self._lines_container)
        self._lines_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self._lines_container)
        
        lines_layout.addWidget(scroll)
        
        # Add line button
        add_btn = QPushButton("+ Add Text Line")
        add_btn.clicked.connect(self._add_line)
        lines_layout.addWidget(add_btn)
        
        layout.addWidget(lines_group)
        
        # Text style section
        style_group = QGroupBox("Text Style")
        style_layout = QVBoxLayout(style_group)
        
        # Text style (raised/engraved/cutout)
        style_row = QHBoxLayout()
        style_row.addWidget(QLabel("Style:"))
        self._text_style_combo = ResetableComboBox(default_text="Raised")
        self._text_style_combo.addItems(["Raised", "Engraved", "Cutout"])
        self._text_style_combo.currentTextChanged.connect(self._on_style_changed)
        style_row.addWidget(self._text_style_combo, stretch=1)
        style_layout.addLayout(style_row)
        
        # Text depth
        self._depth_slider = SliderSpinBox("Depth:", 0.5, 10, 2, decimals=1, suffix=" mm")
        self._depth_slider.valueChanged.connect(self._on_changed)
        self._depth_slider.dragging.connect(self._on_text_scale_dragging)
        self._depth_slider.dragStarted.connect(self._on_text_drag_started)
        self._depth_slider.dragEnded.connect(self._on_text_drag_ended)
        style_layout.addWidget(self._depth_slider)

        # Line spacing
        self._spacing_slider = SliderSpinBox("Line Spacing:", 0.8, 3.0, 1.2, decimals=1, suffix="x")
        self._spacing_slider.valueChanged.connect(self._on_changed)
        self._spacing_slider.dragging.connect(self._on_slider_dragging)
        style_layout.addWidget(self._spacing_slider)
        
        # Alignment
        align_row = QHBoxLayout()
        align_row.addWidget(QLabel("Align:"))
        self._align_combo = ResetableComboBox(default_text="Center")
        self._align_combo.addItems(["Left", "Center", "Right"])
        self._align_combo.setCurrentText("Center")
        self._align_combo.currentTextChanged.connect(self._on_changed)
        align_row.addWidget(self._align_combo, stretch=1)
        style_layout.addLayout(align_row)

        # Text orientation
        orient_row = QHBoxLayout()
        orient_row.addWidget(QLabel("Orientation:"))
        self._orient_combo = ResetableComboBox(default_text="Horizontal")
        self._orient_combo.addItems(["Horizontal", "Vertical"])
        self._orient_combo.setCurrentText("Horizontal")
        self._orient_combo.currentTextChanged.connect(self._on_changed)
        orient_row.addWidget(self._orient_combo, stretch=1)
        style_layout.addLayout(orient_row)

        # Arc text option
        self._arc_enabled_cb = QCheckBox("Arc Text (Curved)")
        self._arc_enabled_cb.stateChanged.connect(self._on_arc_enabled_changed)
        style_layout.addWidget(self._arc_enabled_cb)

        # Arc options group (hidden by default)
        self._arc_group = QGroupBox("Arc Options")
        arc_layout = QVBoxLayout(self._arc_group)

        self._arc_radius_slider = SliderSpinBox("Radius:", 20, 200, 50, decimals=0, suffix=" mm")
        self._arc_radius_slider.valueChanged.connect(self._on_changed)
        self._arc_radius_slider.dragging.connect(self._on_slider_dragging)
        arc_layout.addWidget(self._arc_radius_slider)

        self._arc_angle_slider = SliderSpinBox("Angle:", 30, 360, 180, decimals=0, suffix="°")
        self._arc_angle_slider.valueChanged.connect(self._on_changed)
        self._arc_angle_slider.dragging.connect(self._on_slider_dragging)
        arc_layout.addWidget(self._arc_angle_slider)

        arc_dir_row = QHBoxLayout()
        arc_dir_row.addWidget(QLabel("Direction:"))
        self._arc_direction_combo = ResetableComboBox(default_text="Counterclockwise")
        self._arc_direction_combo.addItems(["Counterclockwise", "Clockwise"])
        self._arc_direction_combo.currentTextChanged.connect(self._on_changed)
        arc_dir_row.addWidget(self._arc_direction_combo, stretch=1)
        arc_layout.addLayout(arc_dir_row)

        self._arc_group.setVisible(False)
        style_layout.addWidget(self._arc_group)

        # Text effect
        effect_row = QHBoxLayout()
        effect_row.addWidget(QLabel("Effect:"))
        self._effect_combo = ResetableComboBox(default_text="None")
        self._effect_combo.addItems(["None", "Bevel", "Rounded", "Outline"])
        self._effect_combo.currentTextChanged.connect(self._on_effect_changed)
        effect_row.addWidget(self._effect_combo, stretch=1)
        style_layout.addLayout(effect_row)

        # Effect size (shown only when effect is not None)
        self._effect_size_slider = SliderSpinBox("Effect Size:", 0.1, 2.0, 0.3, decimals=1, suffix=" mm")
        self._effect_size_slider.valueChanged.connect(self._on_changed)
        self._effect_size_slider.dragging.connect(self._on_slider_dragging)
        self._effect_size_slider.setVisible(False)
        style_layout.addWidget(self._effect_size_slider)

        layout.addWidget(style_group)

        # Add icon buttons
        font_awesome_btn = QPushButton("🔣 Add Icon (Font Awesome)")
        font_awesome_btn.clicked.connect(self._on_add_font_awesome_icon)
        layout.addWidget(font_awesome_btn)

        icon_btn = QPushButton("🔣 Add Icon (Nerd Fonts)")
        icon_btn.clicked.connect(self._on_add_icon)
        layout.addWidget(icon_btn)

        google_icon_btn = QPushButton("🔣 Add Icon (Google)")
        google_icon_btn.clicked.connect(self._on_add_google_icon)
        layout.addWidget(google_icon_btn)

        layout.addStretch()
        
        # Add initial line
        self._add_line()
    
    def _add_line(self):
        """Add a new text line widget."""
        self._add_line_silent()
        self._on_changed()

    def _add_line_silent(self):
        """Add a new text line widget without emitting signals."""
        line_num = len(self._line_widgets) + 1
        line_widget = TextLineWidget(line_num)
        line_widget.set_fonts(self._font_names)
        line_widget.changed.connect(self._on_changed)
        line_widget.remove_requested.connect(self._remove_line)
        # Connect for real-time preview
        line_widget.segment_position_dragging.connect(self.text_position_dragging)
        line_widget.drag_started.connect(self._on_drag_started)
        line_widget.drag_ended.connect(self._on_drag_ended)
        # Connect slider dragging from segments (font size, spacing, gap)
        line_widget.segment_slider_dragging.connect(self.slider_dragging)

        self._line_widgets.append(line_widget)
        self._lines_layout.addWidget(line_widget)
    
    def _remove_line(self, widget):
        """Remove a text line widget."""
        if len(self._line_widgets) <= 1:
            return  # Keep at least one line

        self._line_widgets.remove(widget)
        self._lines_layout.removeWidget(widget)
        widget.deleteLater()

        # Renumber remaining lines
        for i, w in enumerate(self._line_widgets):
            w.update_line_label(i + 1)

        self._on_changed()
    
    def _on_changed(self, *args):
        self.settings_changed.emit()

    def _on_slider_dragging(self, value):
        """Emit slider_dragging for real-time preview during slider drag."""
        self.slider_dragging.emit()

    def _on_text_scale_dragging(self, value):
        """Emit text scale values for real-time transform-based preview."""
        # Get average font size from first segment (approximation)
        avg_size = 12.0  # Default
        if self._line_widgets:
            first_line = self._line_widgets[0]
            if hasattr(first_line, '_segment_widgets') and first_line._segment_widgets:
                first_seg = first_line._segment_widgets[0]
                if hasattr(first_seg, '_size_slider'):
                    avg_size = first_seg._size_slider.value()
        depth = self._depth_slider.value()
        self.text_scale_dragging.emit(avg_size, depth)

    def _on_text_drag_started(self):
        """Handle text depth/size slider drag start."""
        if not self._is_text_dragging:
            self._is_text_dragging = True
            self.text_drag_started.emit()

    def _on_text_drag_ended(self):
        """Handle text depth/size slider drag end."""
        if self._is_text_dragging:
            self._is_text_dragging = False
            self.text_drag_ended.emit()

    def get_current_text_params(self) -> tuple:
        """Get current text size and depth for overlay creation."""
        avg_size = 12.0
        if self._line_widgets:
            first_line = self._line_widgets[0]
            if hasattr(first_line, '_segment_widgets') and first_line._segment_widgets:
                first_seg = first_line._segment_widgets[0]
                if hasattr(first_seg, '_size_slider'):
                    avg_size = first_seg._size_slider.value()
        return (avg_size, self._depth_slider.value())

    def _on_drag_started(self):
        """Track when a position drag starts."""
        self._active_drag_count += 1

    def _on_drag_ended(self):
        """Track when a position drag ends."""
        self._active_drag_count = max(0, self._active_drag_count - 1)

    def is_dragging(self) -> bool:
        """Check if any text segment position is being dragged."""
        return self._active_drag_count > 0

    def _on_effect_changed(self, effect_text: str):
        """Handle effect type change."""
        # Show/hide effect size slider based on effect selection
        self._effect_size_slider.setVisible(effect_text != "None")
        self._on_changed()

    def _on_arc_enabled_changed(self, state: int):
        """Handle arc text enable/disable."""
        is_enabled = state == Qt.Checked
        self._arc_group.setVisible(is_enabled)
        self._on_changed()

    def _on_style_changed(self, style_text: str):
        """Handle text style change."""
        self._on_changed()

    def _on_add_icon(self):
        """Open icon browser dialog."""
        from ui.dialogs.icon_browser import IconBrowserDialog
        dialog = IconBrowserDialog(self)
        if dialog.exec_():
            icon_data = dialog.get_selected_icon()
            if icon_data:
                icon_char = icon_data.get('char', '')
                if icon_char and self._line_widgets:
                    # Add a new segment to the first line with the icon
                    line_widget = self._line_widgets[0]
                    line_widget._add_segment_silent()
                    new_seg = line_widget._segment_widgets[-1]
                    new_seg._content_edit.setText(icon_char)
                    new_seg.is_icon = True
                    # Set the font path if available
                    font_path = icon_data.get('font_path')
                    if font_path:
                        # Add the Nerd Font to the combo if not present
                        font_name = "Symbols Nerd Font"
                        if font_name not in self._font_names:
                            self._font_names.append(font_name)
                            line_widget.set_fonts(self._font_names)
                        new_seg._font_combo.setCurrentText(font_name)
                    self._on_changed()

    def _on_add_google_icon(self):
        """Open Google Material Icons browser dialog."""
        from ui.dialogs.material_icons_dialog import MaterialIconsDialog
        dialog = MaterialIconsDialog(self)
        if dialog.exec_():
            icon_data = dialog.get_selected_icon()
            if icon_data:
                # Signal to main window that we want to add an SVG icon
                # The main window will handle adding it via SVG panel
                self._pending_google_icon = icon_data
                # For now, we'll emit settings changed so the main window
                # can check for pending icons
                self.google_icon_selected.emit(icon_data)

    def _on_add_font_awesome_icon(self):
        """Open Font Awesome Icons browser dialog."""
        from ui.dialogs.font_awesome_dialog import FontAwesomeDialog
        dialog = FontAwesomeDialog(self)
        if dialog.exec_():
            icon_data = dialog.get_selected_icon()
            if icon_data:
                # Signal to main window that we want to add an SVG icon
                # The main window will handle adding it via SVG panel
                self.font_awesome_icon_selected.emit(icon_data)

    def set_fonts(self, font_names: list):
        """Set available fonts for all line widgets."""
        self._font_names = font_names
        for widget in self._line_widgets:
            widget.set_fonts(font_names)
    
    def get_config(self) -> dict:
        """Get the complete text configuration."""
        style_map = {"Raised": "raised", "Engraved": "engraved", "Cutout": "cutout"}
        align_map = {"Left": "left", "Center": "center", "Right": "right"}
        orient_map = {"Horizontal": "horizontal", "Vertical": "vertical"}
        effect_map = {"None": "none", "Bevel": "bevel", "Rounded": "rounded", "Outline": "outline"}
        arc_dir_map = {"Counterclockwise": "counterclockwise", "Clockwise": "clockwise"}

        return {
            'lines': [w.get_config() for w in self._line_widgets],
            'style': style_map.get(self._text_style_combo.currentText(), 'raised'),
            'depth': self._depth_slider.value(),
            'line_spacing': self._spacing_slider.value(),
            'halign': align_map.get(self._align_combo.currentText(), 'center'),
            'orientation': orient_map.get(self._orient_combo.currentText(), 'horizontal'),
            'effect': effect_map.get(self._effect_combo.currentText(), 'none'),
            'effect_size': self._effect_size_slider.value(),
            'arc_enabled': self._arc_enabled_cb.isChecked(),
            'arc_radius': self._arc_radius_slider.value(),
            'arc_angle': self._arc_angle_slider.value(),
            'arc_direction': arc_dir_map.get(self._arc_direction_combo.currentText(), 'counterclockwise'),
        }

    def set_config(self, config: dict):
        """Set the text configuration."""
        # Block signals during bulk configuration to prevent cascade updates
        self.blockSignals(True)

        try:
            # Clear ALL existing lines (bypass the "keep one" check)
            while self._line_widgets:
                widget = self._line_widgets.pop()
                widget.blockSignals(True)  # Block individual widget signals too
                self._lines_layout.removeWidget(widget)
                widget.deleteLater()

            # Add lines from config
            lines = config.get('lines', [])
            if not lines:
                # Ensure at least one empty line
                self._add_line_silent()
            else:
                for line_config in lines:
                    self._add_line_silent()
                    self._line_widgets[-1].set_config(line_config)

            # Set style options
            style_map = {"raised": "Raised", "engraved": "Engraved", "cutout": "Cutout"}
            style_text = style_map.get(config.get('style'), 'Raised')
            self._text_style_combo.setCurrentText(style_text)

            if 'depth' in config:
                self._depth_slider.setValue(config['depth'])

            if 'line_spacing' in config:
                self._spacing_slider.setValue(config['line_spacing'])

            align_map = {"left": "Left", "center": "Center", "right": "Right"}
            self._align_combo.setCurrentText(align_map.get(config.get('halign'), 'Center'))

            orient_map = {"horizontal": "Horizontal", "vertical": "Vertical"}
            self._orient_combo.setCurrentText(orient_map.get(config.get('orientation'), 'Horizontal'))

            # Set effect options
            effect_map = {"none": "None", "bevel": "Bevel", "rounded": "Rounded", "outline": "Outline"}
            effect_text = effect_map.get(config.get('effect'), 'None')
            self._effect_combo.setCurrentText(effect_text)
            self._effect_size_slider.setVisible(effect_text != "None")

            if 'effect_size' in config:
                self._effect_size_slider.setValue(config['effect_size'])

            # Set arc text options
            arc_enabled = config.get('arc_enabled', False)
            self._arc_enabled_cb.setChecked(arc_enabled)
            self._arc_group.setVisible(arc_enabled)

            if 'arc_radius' in config:
                self._arc_radius_slider.setValue(config['arc_radius'])
            if 'arc_angle' in config:
                self._arc_angle_slider.setValue(config['arc_angle'])

            arc_dir_map = {"counterclockwise": "Counterclockwise", "clockwise": "Clockwise"}
            self._arc_direction_combo.setCurrentText(arc_dir_map.get(config.get('arc_direction'), 'Counterclockwise'))
        finally:
            self.blockSignals(False)

        # Emit a single signal after all configuration is complete
        self.settings_changed.emit()
