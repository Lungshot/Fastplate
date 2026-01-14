"""
Variable Data Import Dialog
Dialog for importing CSV data for batch personalization.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QLineEdit, QFileDialog, QComboBox, QSpinBox, QCheckBox,
    QMessageBox, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal
from pathlib import Path
from typing import Optional, Dict

from core.variable_data import VariableDataImporter, VariableDataSet, preview_data


class VariableDataDialog(QDialog):
    """Dialog for importing and mapping variable data."""

    data_imported = pyqtSignal(object)  # Emits VariableDataSet

    def __init__(self, parent=None):
        super().__init__(parent)
        self._importer = VariableDataImporter()
        self._dataset: Optional[VariableDataSet] = None

        self.setWindowTitle("Import Variable Data")
        self.setMinimumSize(700, 500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # File selection
        file_group = QGroupBox("CSV File")
        file_layout = QVBoxLayout(file_group)

        file_row = QHBoxLayout()
        file_row.addWidget(QLabel("File:"))
        self._file_path = QLineEdit()
        self._file_path.setReadOnly(True)
        file_row.addWidget(self._file_path, stretch=1)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_file)
        file_row.addWidget(browse_btn)
        file_layout.addLayout(file_row)

        # Options
        options_row = QHBoxLayout()

        self._has_header = QCheckBox("First row is header")
        self._has_header.setChecked(True)
        self._has_header.stateChanged.connect(self._reload_file)
        options_row.addWidget(self._has_header)

        options_row.addWidget(QLabel("Delimiter:"))
        self._delimiter = QComboBox()
        self._delimiter.addItems(["Comma (,)", "Semicolon (;)", "Tab"])
        self._delimiter.currentIndexChanged.connect(self._reload_file)
        options_row.addWidget(self._delimiter)

        options_row.addWidget(QLabel("Encoding:"))
        self._encoding = QComboBox()
        self._encoding.addItems(["UTF-8", "Latin-1", "Windows-1252"])
        self._encoding.currentIndexChanged.connect(self._reload_file)
        options_row.addWidget(self._encoding)

        options_row.addStretch()
        file_layout.addLayout(options_row)

        layout.addWidget(file_group)

        # Data preview
        preview_group = QGroupBox("Data Preview")
        preview_layout = QVBoxLayout(preview_group)

        self._preview_table = QTableWidget()
        self._preview_table.setMinimumHeight(150)
        preview_layout.addWidget(self._preview_table)

        self._row_count_label = QLabel("0 rows loaded")
        preview_layout.addWidget(self._row_count_label)

        layout.addWidget(preview_group)

        # Field mapping
        mapping_group = QGroupBox("Field Mapping")
        mapping_layout = QVBoxLayout(mapping_group)

        mapping_info = QLabel(
            "Select which CSV field to use for each nameplate property.\n"
            "Fields will replace {{fieldname}} placeholders in your template."
        )
        mapping_info.setStyleSheet("color: #888;")
        mapping_layout.addWidget(mapping_info)

        # Mapping table
        mapping_row = QHBoxLayout()

        # Available fields list
        fields_layout = QVBoxLayout()
        fields_layout.addWidget(QLabel("Available Fields:"))
        self._fields_list = QListWidget()
        self._fields_list.setMaximumWidth(200)
        fields_layout.addWidget(self._fields_list)
        mapping_row.addLayout(fields_layout)

        # Mapping assignments
        assigns_layout = QVBoxLayout()
        assigns_layout.addWidget(QLabel("Map to Nameplate:"))

        # Primary text field
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Primary Text:"))
        self._primary_field = QComboBox()
        self._primary_field.setMinimumWidth(150)
        name_row.addWidget(self._primary_field, stretch=1)
        assigns_layout.addLayout(name_row)

        # Secondary text field
        sec_row = QHBoxLayout()
        sec_row.addWidget(QLabel("Secondary Text:"))
        self._secondary_field = QComboBox()
        self._secondary_field.setMinimumWidth(150)
        sec_row.addWidget(self._secondary_field, stretch=1)
        assigns_layout.addLayout(sec_row)

        # Custom field mappings
        custom_label = QLabel("Custom Mappings (use {{fieldname}} in text):")
        custom_label.setStyleSheet("margin-top: 10px;")
        assigns_layout.addWidget(custom_label)

        self._custom_mappings = QListWidget()
        self._custom_mappings.setMaximumHeight(80)
        assigns_layout.addWidget(self._custom_mappings)

        assigns_layout.addStretch()
        mapping_row.addLayout(assigns_layout, stretch=1)

        mapping_layout.addLayout(mapping_row)

        layout.addWidget(mapping_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        import_btn = QPushButton("Import")
        import_btn.clicked.connect(self._import_data)
        btn_layout.addWidget(import_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _browse_file(self):
        """Browse for CSV file."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "",
            "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)"
        )
        if path:
            self._file_path.setText(path)
            self._load_file(path)

    def _get_delimiter(self) -> str:
        """Get the selected delimiter character."""
        delimiters = [',', ';', '\t']
        return delimiters[self._delimiter.currentIndex()]

    def _get_encoding(self) -> str:
        """Get the selected encoding."""
        encodings = ['utf-8', 'latin-1', 'windows-1252']
        return encodings[self._encoding.currentIndex()]

    def _reload_file(self):
        """Reload the file with current settings."""
        path = self._file_path.text()
        if path:
            self._load_file(path)

    def _load_file(self, path: str):
        """Load the CSV file."""
        try:
            self._dataset = self._importer.import_csv(
                path,
                has_header=self._has_header.isChecked(),
                delimiter=self._get_delimiter(),
                encoding=self._get_encoding()
            )

            if self._dataset:
                self._update_preview()
                self._update_field_lists()
            else:
                QMessageBox.warning(self, "Error", "Failed to load CSV file.")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load file: {e}")

    def _update_preview(self):
        """Update the preview table."""
        if not self._dataset:
            return

        headers = self._dataset.get_field_names()
        row_count = min(self._dataset.row_count, 10)  # Show max 10 rows

        self._preview_table.setColumnCount(len(headers))
        self._preview_table.setRowCount(row_count)
        self._preview_table.setHorizontalHeaderLabels(headers)

        for i in range(row_count):
            row = self._dataset.get_row(i)
            for j, header in enumerate(headers):
                value = row.get(header, "")
                self._preview_table.setItem(i, j, QTableWidgetItem(value))

        # Resize columns
        self._preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self._row_count_label.setText(f"{self._dataset.row_count} rows loaded")

    def _update_field_lists(self):
        """Update the field selection lists."""
        if not self._dataset:
            return

        headers = self._dataset.get_field_names()

        # Update fields list
        self._fields_list.clear()
        for header in headers:
            item = QListWidgetItem(header)
            item.setToolTip(f"Use {{{{header}}}} in text")
            self._fields_list.addItem(item)

        # Update combo boxes
        self._primary_field.clear()
        self._primary_field.addItem("(None)")
        self._primary_field.addItems(headers)
        if headers:
            self._primary_field.setCurrentIndex(1)  # Select first field

        self._secondary_field.clear()
        self._secondary_field.addItem("(None)")
        self._secondary_field.addItems(headers)

        # Update custom mappings list
        self._custom_mappings.clear()
        for header in headers:
            item = QListWidgetItem(f"{{{{header}}}} → {header}")
            self._custom_mappings.addItem(item)

    def _import_data(self):
        """Import the data and close dialog."""
        if not self._dataset:
            QMessageBox.warning(self, "No Data", "Please load a CSV file first.")
            return

        self.data_imported.emit(self._dataset)
        self.accept()

    def get_dataset(self) -> Optional[VariableDataSet]:
        """Get the loaded dataset."""
        return self._dataset

    def get_field_mapping(self) -> Dict[str, str]:
        """Get the field mapping configuration."""
        mapping = {}

        primary = self._primary_field.currentText()
        if primary != "(None)":
            mapping['text.lines[0].segments[0].content'] = primary

        secondary = self._secondary_field.currentText()
        if secondary != "(None)":
            mapping['text.lines[1].segments[0].content'] = secondary

        return mapping
