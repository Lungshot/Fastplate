"""
Multi-Color Export Dialog
Dialog for configuring multi-color/multi-part exports.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QCheckBox,
    QDialogButtonBox, QColorDialog, QFileDialog
)
from PyQt5.QtCore import Qt
from ui.widgets.slider_spin import FocusComboBox
from PyQt5.QtGui import QColor


class ColorButton(QPushButton):
    """Button that displays and allows selecting a color."""

    def __init__(self, color: QColor = QColor(200, 200, 200), parent=None):
        super().__init__(parent)
        self._color = color
        self._update_style()
        self.clicked.connect(self._on_click)
        self.setFixedWidth(60)

    def _update_style(self):
        """Update button style to show current color."""
        self.setStyleSheet(
            f"background-color: {self._color.name()}; "
            f"border: 2px solid #888; border-radius: 4px; "
            f"min-height: 24px;"
        )

    def _on_click(self):
        """Open color picker dialog."""
        color = QColorDialog.getColor(self._color, self, "Select Color")
        if color.isValid():
            self._color = color
            self._update_style()

    def color(self) -> QColor:
        """Get the current color."""
        return self._color

    def set_color(self, color: QColor):
        """Set the color."""
        self._color = color
        self._update_style()


class MultiColorExportDialog(QDialog):
    """Dialog for multi-color export configuration."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Multi-Color Export")
        self.setMinimumWidth(450)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Export mode
        mode_group = QGroupBox("Export Mode")
        mode_layout = QVBoxLayout(mode_group)

        self._separate_files_radio = QCheckBox("Separate STL files (for manual assembly in slicer)")
        self._separate_files_radio.setChecked(True)
        mode_layout.addWidget(self._separate_files_radio)

        info_label = QLabel(
            "Exports base plate and text as separate files:\n"
            "  • filename_base.stl - The base plate\n"
            "  • filename_text.stl - The text/graphics\n"
            "\nLoad both files in your slicer and assign different colors."
        )
        info_label.setStyleSheet("color: #888; font-size: 11px; margin-left: 20px;")
        mode_layout.addWidget(info_label)

        layout.addWidget(mode_group)

        # Color preview (informational)
        color_group = QGroupBox("Color Preview (Reference Only)")
        color_layout = QFormLayout(color_group)

        # Base color
        self._base_color_btn = ColorButton(QColor(180, 180, 180))
        color_layout.addRow("Base plate color:", self._base_color_btn)

        # Text color
        self._text_color_btn = ColorButton(QColor(50, 50, 50))
        color_layout.addRow("Text/graphics color:", self._text_color_btn)

        note = QLabel("These colors are for reference only.\nActual colors are set in your slicer.")
        note.setStyleSheet("color: #888; font-size: 10px;")
        color_layout.addRow(note)

        layout.addWidget(color_group)

        # Output settings
        output_group = QGroupBox("Output Settings")
        output_layout = QFormLayout(output_group)

        # File format
        self._format_combo = FocusComboBox()
        self._format_combo.addItems(["STL", "STEP", "3MF"])
        output_layout.addRow("File format:", self._format_combo)

        # File name suffixes
        self._base_suffix = QLineEdit("_base")
        output_layout.addRow("Base suffix:", self._base_suffix)

        self._text_suffix = QLineEdit("_text")
        output_layout.addRow("Text suffix:", self._text_suffix)

        layout.addWidget(output_group)

        # Components to export
        parts_group = QGroupBox("Components")
        parts_layout = QVBoxLayout(parts_group)

        self._export_base_check = QCheckBox("Export base plate")
        self._export_base_check.setChecked(True)
        parts_layout.addWidget(self._export_base_check)

        self._export_text_check = QCheckBox("Export text/graphics")
        self._export_text_check.setChecked(True)
        parts_layout.addWidget(self._export_text_check)

        self._export_combined_check = QCheckBox("Also export combined single file")
        self._export_combined_check.setChecked(False)
        parts_layout.addWidget(self._export_combined_check)

        layout.addWidget(parts_group)

        layout.addStretch()

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_config(self) -> dict:
        """Get the export configuration."""
        format_map = {"STL": "stl", "STEP": "step", "3MF": "3mf"}
        return {
            'export_separate': self._separate_files_radio.isChecked(),
            'format': format_map.get(self._format_combo.currentText(), 'stl'),
            'base_suffix': self._base_suffix.text() or '_base',
            'text_suffix': self._text_suffix.text() or '_text',
            'export_base': self._export_base_check.isChecked(),
            'export_text': self._export_text_check.isChecked(),
            'export_combined': self._export_combined_check.isChecked(),
            'base_color': self._base_color_btn.color().name(),
            'text_color': self._text_color_btn.color().name(),
        }
