"""
Advanced Features Panel
UI panel for configuring advanced features like QR codes, barcodes, decorations, etc.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QCheckBox, QStackedWidget, QScrollArea,
    QLineEdit, QPushButton, QTextEdit, QFrame
)
from PyQt5.QtCore import pyqtSignal, Qt

from ui.widgets.slider_spin import SliderSpinBox, FocusComboBox, ResetableComboBox


class CollapsibleSection(QWidget):
    """A collapsible section widget."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._is_expanded = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header button
        self._header = QPushButton(f"+ {title}")
        self._header.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px;
                background-color: #3a3a4a;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a4a5a;
            }
        """)
        self._header.clicked.connect(self._toggle)
        layout.addWidget(self._header)

        # Content area
        self._content = QWidget()
        self._content.setVisible(False)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(10, 5, 5, 5)
        layout.addWidget(self._content)

        self._title = title

    def _toggle(self):
        self._is_expanded = not self._is_expanded
        self._content.setVisible(self._is_expanded)
        prefix = "-" if self._is_expanded else "+"
        self._header.setText(f"{prefix} {self._title}")

    def add_widget(self, widget: QWidget):
        self._content_layout.addWidget(widget)

    def add_layout(self, layout):
        self._content_layout.addLayout(layout)

    def set_expanded(self, expanded: bool):
        if self._is_expanded != expanded:
            self._toggle()


class AdvancedPanel(QWidget):
    """Panel for advanced feature settings."""

    settings_changed = pyqtSignal()
    slider_dragging = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _on_slider_dragging(self, value):
        """Emit slider_dragging for real-time preview during slider drag."""
        self.slider_dragging.emit()

    def _setup_ui(self):
        # Scroll area for many options
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # QR Code Section
        self._qr_section = self._create_qr_section()
        layout.addWidget(self._qr_section)

        # Barcode Section
        self._barcode_section = self._create_barcode_section()
        layout.addWidget(self._barcode_section)

        # Corner Decorations Section
        self._corner_section = self._create_corner_section()
        layout.addWidget(self._corner_section)

        # Texture Section
        self._texture_section = self._create_texture_section()
        layout.addWidget(self._texture_section)

        # Braille Section
        self._braille_section = self._create_braille_section()
        layout.addWidget(self._braille_section)

        layout.addStretch()

        scroll.setWidget(container)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _create_qr_section(self) -> CollapsibleSection:
        """Create QR code section."""
        section = CollapsibleSection("QR Code")

        # Enable checkbox
        self._qr_enabled = QCheckBox("Enable QR Code")
        self._qr_enabled.stateChanged.connect(self._on_changed)
        section.add_widget(self._qr_enabled)

        # Data input
        data_row = QHBoxLayout()
        data_row.addWidget(QLabel("Data:"))
        self._qr_data = QLineEdit()
        self._qr_data.setPlaceholderText("URL or text to encode")
        self._qr_data.textChanged.connect(self._on_changed)
        data_row.addWidget(self._qr_data, stretch=1)
        section.add_layout(data_row)

        # Size
        self._qr_size = SliderSpinBox("Size:", 10, 50, 20, decimals=0, suffix=" mm")
        self._qr_size.valueChanged.connect(self._on_changed)
        self._qr_size.dragging.connect(self._on_slider_dragging)
        section.add_widget(self._qr_size)

        # Module size
        self._qr_module = SliderSpinBox("Module Size:", 0.3, 2.0, 0.8, decimals=1, suffix=" mm")
        self._qr_module.valueChanged.connect(self._on_changed)
        self._qr_module.dragging.connect(self._on_slider_dragging)
        section.add_widget(self._qr_module)

        # Position
        pos_row = QHBoxLayout()
        pos_row.addWidget(QLabel("Position:"))
        self._qr_position = ResetableComboBox(default_text="Right")
        self._qr_position.addItems(["Center", "Left", "Right", "Top Right", "Top Left", "Bottom Right", "Bottom Left"])
        self._qr_position.currentTextChanged.connect(self._on_changed)
        pos_row.addWidget(self._qr_position, stretch=1)
        section.add_layout(pos_row)

        # Style
        style_row = QHBoxLayout()
        style_row.addWidget(QLabel("Style:"))
        self._qr_style = ResetableComboBox(default_text="Raised")
        self._qr_style.addItems(["Raised", "Engraved", "Cutout"])
        self._qr_style.currentTextChanged.connect(self._on_changed)
        style_row.addWidget(self._qr_style, stretch=1)
        section.add_layout(style_row)

        # Error correction
        ec_row = QHBoxLayout()
        ec_row.addWidget(QLabel("Error Correction:"))
        self._qr_error = ResetableComboBox(default_text="Medium (M)")
        self._qr_error.addItems(["Low (L)", "Medium (M)", "Quartile (Q)", "High (H)"])
        self._qr_error.setCurrentText("Medium (M)")
        self._qr_error.currentTextChanged.connect(self._on_changed)
        ec_row.addWidget(self._qr_error, stretch=1)
        section.add_layout(ec_row)

        return section

    def _create_barcode_section(self) -> CollapsibleSection:
        """Create barcode section."""
        section = CollapsibleSection("Barcode")

        # Enable checkbox
        self._barcode_enabled = QCheckBox("Enable Barcode")
        self._barcode_enabled.stateChanged.connect(self._on_changed)
        section.add_widget(self._barcode_enabled)

        # Data input
        data_row = QHBoxLayout()
        data_row.addWidget(QLabel("Data:"))
        self._barcode_data = QLineEdit()
        self._barcode_data.setPlaceholderText("Numbers or text to encode")
        self._barcode_data.textChanged.connect(self._on_changed)
        data_row.addWidget(self._barcode_data, stretch=1)
        section.add_layout(data_row)

        # Format
        format_row = QHBoxLayout()
        format_row.addWidget(QLabel("Format:"))
        self._barcode_format = ResetableComboBox(default_text="Code 128")
        self._barcode_format.addItems(["Code 128", "Code 39", "EAN-13", "UPC-A"])
        self._barcode_format.currentTextChanged.connect(self._on_changed)
        format_row.addWidget(self._barcode_format, stretch=1)
        section.add_layout(format_row)

        # Width
        self._barcode_width = SliderSpinBox("Width:", 20, 80, 40, decimals=0, suffix=" mm")
        self._barcode_width.valueChanged.connect(self._on_changed)
        self._barcode_width.dragging.connect(self._on_slider_dragging)
        section.add_widget(self._barcode_width)

        # Height
        self._barcode_height = SliderSpinBox("Height:", 5, 20, 10, decimals=0, suffix=" mm")
        self._barcode_height.valueChanged.connect(self._on_changed)
        self._barcode_height.dragging.connect(self._on_slider_dragging)
        section.add_widget(self._barcode_height)

        # Style
        style_row = QHBoxLayout()
        style_row.addWidget(QLabel("Style:"))
        self._barcode_style = ResetableComboBox(default_text="Raised")
        self._barcode_style.addItems(["Raised", "Engraved", "Cutout"])
        self._barcode_style.currentTextChanged.connect(self._on_changed)
        style_row.addWidget(self._barcode_style, stretch=1)
        section.add_layout(style_row)

        return section

    def _create_corner_section(self) -> CollapsibleSection:
        """Create corner decorations section."""
        section = CollapsibleSection("Corner Decorations")

        # Enable checkbox
        self._corner_enabled = QCheckBox("Enable Corner Decorations")
        self._corner_enabled.stateChanged.connect(self._on_changed)
        section.add_widget(self._corner_enabled)

        # Style
        style_row = QHBoxLayout()
        style_row.addWidget(QLabel("Style:"))
        self._corner_style = ResetableComboBox(default_text="Simple")
        self._corner_style.addItems([
            "Simple", "Flourish", "Bracket", "Floral",
            "Art Deco", "Victorian", "Celtic", "Modern"
        ])
        self._corner_style.currentTextChanged.connect(self._on_changed)
        style_row.addWidget(self._corner_style, stretch=1)
        section.add_layout(style_row)

        # Size
        self._corner_size = SliderSpinBox("Size:", 5, 30, 12, decimals=0, suffix=" mm")
        self._corner_size.valueChanged.connect(self._on_changed)
        self._corner_size.dragging.connect(self._on_slider_dragging)
        section.add_widget(self._corner_size)

        # Depth
        self._corner_depth = SliderSpinBox("Depth:", 0.3, 3.0, 0.8, decimals=1, suffix=" mm")
        self._corner_depth.valueChanged.connect(self._on_changed)
        self._corner_depth.dragging.connect(self._on_slider_dragging)
        section.add_widget(self._corner_depth)

        # Which corners
        corners_row = QHBoxLayout()
        corners_row.addWidget(QLabel("Apply to:"))
        self._corner_which = ResetableComboBox(default_text="All Corners")
        self._corner_which.addItems(["All Corners", "Top Only", "Bottom Only", "Diagonal (TL/BR)", "Diagonal (TR/BL)"])
        self._corner_which.currentTextChanged.connect(self._on_changed)
        corners_row.addWidget(self._corner_which, stretch=1)
        section.add_layout(corners_row)

        # Raised/engraved
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Type:"))
        self._corner_type = ResetableComboBox(default_text="Engraved")
        self._corner_type.addItems(["Raised", "Engraved"])
        self._corner_type.currentTextChanged.connect(self._on_changed)
        type_row.addWidget(self._corner_type, stretch=1)
        section.add_layout(type_row)

        return section

    def _create_texture_section(self) -> CollapsibleSection:
        """Create texture section."""
        section = CollapsibleSection("Surface Texture")

        # Enable checkbox
        self._texture_enabled = QCheckBox("Enable Surface Texture")
        self._texture_enabled.stateChanged.connect(self._on_changed)
        section.add_widget(self._texture_enabled)

        # Type
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Type:"))
        self._texture_type = ResetableComboBox(default_text="Brushed")
        self._texture_type.addItems([
            "Brushed", "Wood Grain", "Carbon Fiber", "Leather",
            "Sandblast", "Knurled", "Hammered", "Ripple"
        ])
        self._texture_type.currentTextChanged.connect(self._on_changed)
        type_row.addWidget(self._texture_type, stretch=1)
        section.add_layout(type_row)

        # Depth
        self._texture_depth = SliderSpinBox("Depth:", 0.1, 1.0, 0.2, decimals=1, suffix=" mm")
        self._texture_depth.valueChanged.connect(self._on_changed)
        self._texture_depth.dragging.connect(self._on_slider_dragging)
        section.add_widget(self._texture_depth)

        # Spacing
        self._texture_spacing = SliderSpinBox("Spacing:", 0.5, 5.0, 1.0, decimals=1, suffix=" mm")
        self._texture_spacing.valueChanged.connect(self._on_changed)
        self._texture_spacing.dragging.connect(self._on_slider_dragging)
        section.add_widget(self._texture_spacing)

        # Angle
        self._texture_angle = SliderSpinBox("Angle:", 0, 90, 0, decimals=0, suffix="°")
        self._texture_angle.valueChanged.connect(self._on_changed)
        self._texture_angle.dragging.connect(self._on_slider_dragging)
        section.add_widget(self._texture_angle)

        # Raised/engraved
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode:"))
        self._texture_mode = ResetableComboBox(default_text="Engraved")
        self._texture_mode.addItems(["Raised", "Engraved"])
        self._texture_mode.currentTextChanged.connect(self._on_changed)
        mode_row.addWidget(self._texture_mode, stretch=1)
        section.add_layout(mode_row)

        # Warning label
        warning = QLabel("Note: Textures can significantly\nincrease file size and processing time.")
        warning.setStyleSheet("color: #888; font-size: 10px;")
        section.add_widget(warning)

        return section

    def _create_braille_section(self) -> CollapsibleSection:
        """Create braille section."""
        section = CollapsibleSection("Braille Text")

        # Enable checkbox
        self._braille_enabled = QCheckBox("Enable Braille Text")
        self._braille_enabled.stateChanged.connect(self._on_changed)
        section.add_widget(self._braille_enabled)

        # Text input
        text_row = QHBoxLayout()
        text_row.addWidget(QLabel("Text:"))
        self._braille_text = QLineEdit()
        self._braille_text.setPlaceholderText("Text to convert to Braille")
        self._braille_text.textChanged.connect(self._on_changed)
        text_row.addWidget(self._braille_text, stretch=1)
        section.add_layout(text_row)

        # Preview
        preview_row = QHBoxLayout()
        preview_row.addWidget(QLabel("Preview:"))
        self._braille_preview = QLabel("")
        self._braille_preview.setStyleSheet("font-size: 16px;")
        preview_row.addWidget(self._braille_preview, stretch=1)
        section.add_layout(preview_row)

        # Dot size
        self._braille_dot = SliderSpinBox("Dot Size:", 1.0, 2.0, 1.5, decimals=1, suffix=" mm")
        self._braille_dot.valueChanged.connect(self._on_changed)
        self._braille_dot.dragging.connect(self._on_slider_dragging)
        section.add_widget(self._braille_dot)

        # Dot height
        self._braille_height = SliderSpinBox("Dot Height:", 0.3, 1.0, 0.5, decimals=1, suffix=" mm")
        self._braille_height.valueChanged.connect(self._on_changed)
        self._braille_height.dragging.connect(self._on_slider_dragging)
        section.add_widget(self._braille_height)

        # Position
        pos_row = QHBoxLayout()
        pos_row.addWidget(QLabel("Position:"))
        self._braille_position = ResetableComboBox(default_text="Bottom")
        self._braille_position.addItems(["Bottom", "Top", "Center", "Below Main Text"])
        self._braille_position.currentTextChanged.connect(self._on_changed)
        pos_row.addWidget(self._braille_position, stretch=1)
        section.add_layout(pos_row)

        # Info
        info = QLabel("ADA Compliant: 1.5mm dot, 0.5mm raised")
        info.setStyleSheet("color: #888; font-size: 10px;")
        section.add_widget(info)

        return section

    def _on_changed(self, *args):
        # Update braille preview
        try:
            from core.geometry.braille import text_to_braille_preview
            text = self._braille_text.text()
            if text:
                preview = text_to_braille_preview(text)
                self._braille_preview.setText(preview)
            else:
                self._braille_preview.setText("")
        except:
            pass

        self.settings_changed.emit()

    def get_config(self) -> dict:
        """Get the advanced features configuration."""
        # Map error correction
        ec_map = {
            "Low (L)": "L",
            "Medium (M)": "M",
            "Quartile (Q)": "Q",
            "High (H)": "H"
        }

        # Map barcode formats
        format_map = {
            "Code 128": "code128",
            "Code 39": "code39",
            "EAN-13": "ean13",
            "UPC-A": "upca"
        }

        # Map corner styles
        corner_map = {
            "Simple": "simple",
            "Flourish": "flourish",
            "Bracket": "bracket",
            "Floral": "floral",
            "Art Deco": "art_deco",
            "Victorian": "victorian",
            "Celtic": "celtic",
            "Modern": "modern"
        }

        # Map texture types
        texture_map = {
            "Brushed": "brushed",
            "Wood Grain": "wood_grain",
            "Carbon Fiber": "carbon_fiber",
            "Leather": "leather",
            "Sandblast": "sandblast",
            "Knurled": "knurled",
            "Hammered": "hammered",
            "Ripple": "ripple"
        }

        return {
            # QR Code
            'qr_enabled': self._qr_enabled.isChecked(),
            'qr_data': self._qr_data.text(),
            'qr_size': self._qr_size.value(),
            'qr_module_size': self._qr_module.value(),
            'qr_position': self._qr_position.currentText().lower().replace(' ', '_'),
            'qr_style': self._qr_style.currentText().lower(),
            'qr_error_correction': ec_map.get(self._qr_error.currentText(), 'M'),

            # Barcode
            'barcode_enabled': self._barcode_enabled.isChecked(),
            'barcode_data': self._barcode_data.text(),
            'barcode_format': format_map.get(self._barcode_format.currentText(), 'code128'),
            'barcode_width': self._barcode_width.value(),
            'barcode_height': self._barcode_height.value(),
            'barcode_style': self._barcode_style.currentText().lower(),

            # Corner Decorations
            'corner_enabled': self._corner_enabled.isChecked(),
            'corner_style': corner_map.get(self._corner_style.currentText(), 'simple'),
            'corner_size': self._corner_size.value(),
            'corner_depth': self._corner_depth.value(),
            'corner_which': self._corner_which.currentText().lower().replace(' ', '_'),
            'corner_type': self._corner_type.currentText().lower(),

            # Texture
            'texture_enabled': self._texture_enabled.isChecked(),
            'texture_type': texture_map.get(self._texture_type.currentText(), 'brushed'),
            'texture_depth': self._texture_depth.value(),
            'texture_spacing': self._texture_spacing.value(),
            'texture_angle': self._texture_angle.value(),
            'texture_mode': self._texture_mode.currentText().lower(),

            # Braille
            'braille_enabled': self._braille_enabled.isChecked(),
            'braille_text': self._braille_text.text(),
            'braille_dot_size': self._braille_dot.value(),
            'braille_dot_height': self._braille_height.value(),
            'braille_position': self._braille_position.currentText().lower().replace(' ', '_'),
        }

    def set_config(self, config: dict):
        """Set the advanced features configuration."""
        self.blockSignals(True)

        try:
            # QR Code
            if 'qr_enabled' in config:
                self._qr_enabled.setChecked(config['qr_enabled'])
            if 'qr_data' in config:
                self._qr_data.setText(config['qr_data'])
            if 'qr_size' in config:
                self._qr_size.setValue(config['qr_size'])
            if 'qr_module_size' in config:
                self._qr_module.setValue(config['qr_module_size'])

            # Error correction reverse map
            ec_reverse = {'L': 'Low (L)', 'M': 'Medium (M)', 'Q': 'Quartile (Q)', 'H': 'High (H)'}
            if 'qr_error_correction' in config:
                self._qr_error.setCurrentText(ec_reverse.get(config['qr_error_correction'], 'Medium (M)'))

            # Barcode
            if 'barcode_enabled' in config:
                self._barcode_enabled.setChecked(config['barcode_enabled'])
            if 'barcode_data' in config:
                self._barcode_data.setText(config['barcode_data'])
            if 'barcode_width' in config:
                self._barcode_width.setValue(config['barcode_width'])
            if 'barcode_height' in config:
                self._barcode_height.setValue(config['barcode_height'])

            # Format reverse map
            format_reverse = {'code128': 'Code 128', 'code39': 'Code 39', 'ean13': 'EAN-13', 'upca': 'UPC-A'}
            if 'barcode_format' in config:
                self._barcode_format.setCurrentText(format_reverse.get(config['barcode_format'], 'Code 128'))

            # Corner Decorations
            if 'corner_enabled' in config:
                self._corner_enabled.setChecked(config['corner_enabled'])
            if 'corner_size' in config:
                self._corner_size.setValue(config['corner_size'])
            if 'corner_depth' in config:
                self._corner_depth.setValue(config['corner_depth'])

            # Corner style reverse map
            corner_reverse = {
                'simple': 'Simple', 'flourish': 'Flourish', 'bracket': 'Bracket',
                'floral': 'Floral', 'art_deco': 'Art Deco', 'victorian': 'Victorian',
                'celtic': 'Celtic', 'modern': 'Modern'
            }
            if 'corner_style' in config:
                self._corner_style.setCurrentText(corner_reverse.get(config['corner_style'], 'Simple'))

            # Texture
            if 'texture_enabled' in config:
                self._texture_enabled.setChecked(config['texture_enabled'])
            if 'texture_depth' in config:
                self._texture_depth.setValue(config['texture_depth'])
            if 'texture_spacing' in config:
                self._texture_spacing.setValue(config['texture_spacing'])
            if 'texture_angle' in config:
                self._texture_angle.setValue(config['texture_angle'])

            # Texture type reverse map
            texture_reverse = {
                'brushed': 'Brushed', 'wood_grain': 'Wood Grain', 'carbon_fiber': 'Carbon Fiber',
                'leather': 'Leather', 'sandblast': 'Sandblast', 'knurled': 'Knurled',
                'hammered': 'Hammered', 'ripple': 'Ripple'
            }
            if 'texture_type' in config:
                self._texture_type.setCurrentText(texture_reverse.get(config['texture_type'], 'Brushed'))

            # Braille
            if 'braille_enabled' in config:
                self._braille_enabled.setChecked(config['braille_enabled'])
            if 'braille_text' in config:
                self._braille_text.setText(config['braille_text'])
            if 'braille_dot_size' in config:
                self._braille_dot.setValue(config['braille_dot_size'])
            if 'braille_dot_height' in config:
                self._braille_height.setValue(config['braille_dot_height'])

        finally:
            self.blockSignals(False)

        self.settings_changed.emit()
