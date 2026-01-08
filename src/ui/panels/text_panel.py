"""
Text Settings Panel
UI panel for configuring text content and styling.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QGroupBox
)
from PyQt5.QtCore import pyqtSignal, Qt

from ui.widgets.slider_spin import SliderSpinBox, LabeledComboBox, LabeledLineEdit, FocusComboBox, ResetableComboBox
from core.geometry.text_builder import TextStyle, TextAlign


class TextLineWidget(QFrame):
    """Widget for configuring a single line of text."""
    
    changed = pyqtSignal()
    remove_requested = pyqtSignal(object)
    
    def __init__(self, line_number: int = 1, parent=None):
        super().__init__(parent)
        self.line_number = line_number
        
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("QFrame { background-color: #353535; border-radius: 5px; }")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # Header with line number and remove button
        header = QHBoxLayout()
        header.addWidget(QLabel(f"Line {line_number}"))
        header.addStretch()
        
        self._remove_btn = QPushButton("×")
        self._remove_btn.setFixedSize(20, 20)
        self._remove_btn.setStyleSheet("QPushButton { font-weight: bold; }")
        self._remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        header.addWidget(self._remove_btn)
        layout.addLayout(header)
        
        # Text content
        self._content_edit = QLineEdit()
        self._content_edit.setPlaceholderText("Enter text...")
        self._content_edit.textChanged.connect(self._on_changed)
        layout.addWidget(self._content_edit)
        
        # Font selection row
        font_row = QHBoxLayout()

        self._font_combo = FocusComboBox()
        self._font_combo.setMinimumWidth(150)
        self._font_combo.currentTextChanged.connect(self._on_changed)
        font_row.addWidget(QLabel("Font:"))
        font_row.addWidget(self._font_combo, stretch=1)

        self._style_combo = FocusComboBox()
        self._style_combo.addItems(["Regular", "Bold", "Italic", "Bold Italic"])
        self._style_combo.currentTextChanged.connect(self._on_changed)
        font_row.addWidget(self._style_combo)

        layout.addLayout(font_row)
        
        # Size slider
        self._size_slider = SliderSpinBox("Size:", 4, 50, 12, decimals=1, suffix=" mm")
        self._size_slider.valueChanged.connect(self._on_changed)
        layout.addWidget(self._size_slider)
    
    def _on_changed(self, *args):
        self.changed.emit()
    
    def set_fonts(self, font_names: list):
        """Set available fonts."""
        current = self._font_combo.currentText()
        self._font_combo.clear()
        self._font_combo.addItems(font_names)
        if current in font_names:
            self._font_combo.setCurrentText(current)
    
    def get_config(self) -> dict:
        """Get the line configuration."""
        return {
            'content': self._content_edit.text(),
            'font_family': self._font_combo.currentText(),
            'font_style': self._style_combo.currentText(),
            'font_size': self._size_slider.value(),
        }
    
    def set_config(self, config: dict):
        """Set the line configuration."""
        self._content_edit.setText(config.get('content', ''))
        if config.get('font_family'):
            self._font_combo.setCurrentText(config['font_family'])
        if config.get('font_style'):
            self._style_combo.setCurrentText(config['font_style'])
        if config.get('font_size'):
            self._size_slider.setValue(config['font_size'])


class TextPanel(QWidget):
    """Panel for all text settings."""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._font_names = []
        self._line_widgets = []
        
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
        scroll.setMaximumHeight(300)
        
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
        self._text_style_combo.currentTextChanged.connect(self._on_changed)
        style_row.addWidget(self._text_style_combo, stretch=1)
        style_layout.addLayout(style_row)
        
        # Text depth
        self._depth_slider = SliderSpinBox("Depth:", 0.5, 10, 2, decimals=1, suffix=" mm")
        self._depth_slider.valueChanged.connect(self._on_changed)
        style_layout.addWidget(self._depth_slider)
        
        # Line spacing
        self._spacing_slider = SliderSpinBox("Line Spacing:", 0.8, 3.0, 1.2, decimals=1, suffix="x")
        self._spacing_slider.valueChanged.connect(self._on_changed)
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

        layout.addWidget(style_group)
        
        # Add icon button
        icon_btn = QPushButton("🔣 Add Icon (Nerd Fonts)")
        icon_btn.clicked.connect(self._on_add_icon)
        layout.addWidget(icon_btn)
        
        layout.addStretch()
        
        # Add initial line
        self._add_line()
    
    def _add_line(self):
        """Add a new text line widget."""
        line_num = len(self._line_widgets) + 1
        line_widget = TextLineWidget(line_num)
        line_widget.set_fonts(self._font_names)
        line_widget.changed.connect(self._on_changed)
        line_widget.remove_requested.connect(self._remove_line)
        
        self._line_widgets.append(line_widget)
        self._lines_layout.addWidget(line_widget)
        
        self._on_changed()
    
    def _remove_line(self, widget):
        """Remove a text line widget."""
        if len(self._line_widgets) <= 1:
            return  # Keep at least one line
        
        self._line_widgets.remove(widget)
        self._lines_layout.removeWidget(widget)
        widget.deleteLater()
        
        # Renumber remaining lines
        for i, w in enumerate(self._line_widgets):
            w.line_number = i + 1
        
        self._on_changed()
    
    def _on_changed(self, *args):
        self.settings_changed.emit()
    
    def _on_add_icon(self):
        """Open icon browser dialog."""
        from ui.dialogs.icon_browser import IconBrowserDialog
        dialog = IconBrowserDialog(self)
        if dialog.exec_():
            icon_data = dialog.get_selected_icon()
            if icon_data:
                # Insert icon character into the first line or create a new line
                icon_char = icon_data.get('char', '')
                if icon_char and self._line_widgets:
                    # Insert into first line's content
                    line_widget = self._line_widgets[0]
                    current_text = line_widget._content_edit.text()
                    line_widget._content_edit.setText(current_text + icon_char)
                    self._on_changed()
    
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

        return {
            'lines': [w.get_config() for w in self._line_widgets],
            'style': style_map.get(self._text_style_combo.currentText(), 'raised'),
            'depth': self._depth_slider.value(),
            'line_spacing': self._spacing_slider.value(),
            'halign': align_map.get(self._align_combo.currentText(), 'center'),
            'orientation': orient_map.get(self._orient_combo.currentText(), 'horizontal'),
        }

    def set_config(self, config: dict):
        """Set the text configuration."""
        # Clear ALL existing lines (bypass the "keep one" check)
        while self._line_widgets:
            widget = self._line_widgets.pop()
            self._lines_layout.removeWidget(widget)
            widget.deleteLater()

        # Add lines from config
        lines = config.get('lines', [])
        if not lines:
            # Ensure at least one empty line
            self._add_line()
        else:
            for line_config in lines:
                self._add_line()
                self._line_widgets[-1].set_config(line_config)

        # Set style options
        style_map = {"raised": "Raised", "engraved": "Engraved", "cutout": "Cutout"}
        self._text_style_combo.setCurrentText(style_map.get(config.get('style'), 'Raised'))

        if 'depth' in config:
            self._depth_slider.setValue(config['depth'])

        if 'line_spacing' in config:
            self._spacing_slider.setValue(config['line_spacing'])

        align_map = {"left": "Left", "center": "Center", "right": "Right"}
        self._align_combo.setCurrentText(align_map.get(config.get('halign'), 'Center'))

        orient_map = {"horizontal": "Horizontal", "vertical": "Vertical"}
        self._orient_combo.setCurrentText(orient_map.get(config.get('orientation'), 'Horizontal'))
