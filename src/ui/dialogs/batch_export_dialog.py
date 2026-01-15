"""
Batch Export Dialog
Dialog for exporting multiple nameplate variations.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QLineEdit, QFileDialog, QProgressBar, QCheckBox, QMessageBox,
    QSpinBox, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from ui.widgets.slider_spin import FocusComboBox
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional


class ExportWorker(QThread):
    """Worker thread for batch export."""

    progress = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal(dict)  # results

    def __init__(self, exporter, items, config):
        super().__init__()
        self.exporter = exporter
        self.items = items
        self.config = config

    def run(self):
        self.exporter.set_progress_callback(self._on_progress)
        results = self.exporter.export_batch(self.items, self.config)
        self.finished.emit(results)

    def _on_progress(self, current, total, message):
        self.progress.emit(current, total, message)


class BatchExportDialog(QDialog):
    """Dialog for batch exporting multiple nameplates."""

    def __init__(self, generator_func: Callable[[Dict], Any], parent=None):
        super().__init__(parent)
        self.generator_func = generator_func
        self._items = []
        self._worker = None

        self.setWindowTitle("Batch Export")
        self.setMinimumSize(600, 500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Source section
        source_group = QGroupBox("Data Source")
        source_layout = QVBoxLayout(source_group)

        # Text list input
        text_label = QLabel("Enter names/text (one per line):")
        source_layout.addWidget(text_label)

        self._text_input = QTextEdit()
        self._text_input.setPlaceholderText("John Smith\nJane Doe\nBob Johnson")
        self._text_input.setMaximumHeight(100)
        source_layout.addWidget(self._text_input)

        # Or import from CSV
        csv_row = QHBoxLayout()
        csv_row.addWidget(QLabel("Or import from CSV:"))
        self._csv_path = QLineEdit()
        self._csv_path.setPlaceholderText("Select CSV file...")
        self._csv_path.setReadOnly(True)
        csv_row.addWidget(self._csv_path, stretch=1)
        csv_btn = QPushButton("Browse...")
        csv_btn.clicked.connect(self._browse_csv)
        csv_row.addWidget(csv_btn)
        source_layout.addLayout(csv_row)

        layout.addWidget(source_group)

        # Preview table
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)

        self._preview_table = QTableWidget()
        self._preview_table.setColumnCount(2)
        self._preview_table.setHorizontalHeaderLabels(["Name", "Filename"])
        self._preview_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._preview_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        preview_layout.addWidget(self._preview_table)

        update_btn = QPushButton("Update Preview")
        update_btn.clicked.connect(self._update_preview)
        preview_layout.addWidget(update_btn)

        layout.addWidget(preview_group)

        # Output settings
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout(output_group)

        # Output directory
        dir_row = QHBoxLayout()
        dir_row.addWidget(QLabel("Output Directory:"))
        self._output_dir = QLineEdit()
        self._output_dir.setPlaceholderText("Select output folder...")
        dir_row.addWidget(self._output_dir, stretch=1)
        dir_btn = QPushButton("Browse...")
        dir_btn.clicked.connect(self._browse_output_dir)
        dir_row.addWidget(dir_btn)
        output_layout.addLayout(dir_row)

        # Format
        format_row = QHBoxLayout()
        format_row.addWidget(QLabel("Format:"))
        self._format_combo = FocusComboBox()
        self._format_combo.addItems(["STL", "STEP"])
        format_row.addWidget(self._format_combo, stretch=1)
        output_layout.addLayout(format_row)

        # Naming pattern
        naming_row = QHBoxLayout()
        naming_row.addWidget(QLabel("Naming Pattern:"))
        self._naming_pattern = QLineEdit("{index:03d}_{name}")
        naming_row.addWidget(self._naming_pattern, stretch=1)
        output_layout.addLayout(naming_row)

        # Create subdirectory
        self._subdir_check = QCheckBox("Create timestamped subdirectory")
        self._subdir_check.setChecked(True)
        output_layout.addWidget(self._subdir_check)

        layout.addWidget(output_group)

        # Progress
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)

        self._progress_bar = QProgressBar()
        self._progress_bar.setTextVisible(True)
        progress_layout.addWidget(self._progress_bar)

        self._status_label = QLabel("Ready")
        progress_layout.addWidget(self._status_label)

        layout.addWidget(progress_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._export_btn = QPushButton("Export")
        self._export_btn.clicked.connect(self._start_export)
        btn_layout.addWidget(self._export_btn)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self._cancel_export)
        self._cancel_btn.setEnabled(False)
        btn_layout.addWidget(self._cancel_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _browse_csv(self):
        """Browse for CSV file."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "",
            "CSV Files (*.csv);;All Files (*)"
        )
        if path:
            self._csv_path.setText(path)
            self._load_csv(path)

    def _load_csv(self, path: str):
        """Load data from CSV file."""
        try:
            from core.variable_data import VariableDataImporter, preview_data

            importer = VariableDataImporter()
            dataset = importer.import_csv(path)

            if dataset:
                # Clear text input and show CSV data
                lines = []
                for i in range(min(dataset.row_count, 100)):  # Limit preview
                    row = dataset.get_row(i)
                    # Use first field as the name
                    first_field = list(row.values())[0] if row else ""
                    lines.append(first_field)

                self._text_input.setText("\n".join(lines))
                self._update_preview()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load CSV: {e}")

    def _browse_output_dir(self):
        """Browse for output directory."""
        path = QFileDialog.getExistingDirectory(
            self, "Select Output Directory"
        )
        if path:
            self._output_dir.setText(path)

    def _update_preview(self):
        """Update the preview table."""
        text = self._text_input.toPlainText()
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        self._preview_table.setRowCount(len(lines))
        self._items = []

        pattern = self._naming_pattern.text()
        fmt = self._format_combo.currentText().lower()

        for i, line in enumerate(lines):
            # Generate filename
            try:
                filename = pattern.format(index=i+1, name=line, format=fmt)
            except:
                filename = f"{i+1:03d}_{line}"

            if not filename.endswith(f".{fmt}"):
                filename += f".{fmt}"

            # Make safe filename
            safe_filename = "".join(
                c if c.isalnum() or c in "-_." else "_"
                for c in filename
            )

            self._preview_table.setItem(i, 0, QTableWidgetItem(line))
            self._preview_table.setItem(i, 1, QTableWidgetItem(safe_filename))

            self._items.append({
                'name': line,
                'filename': safe_filename
            })

    def _start_export(self):
        """Start the batch export."""
        if not self._items:
            QMessageBox.warning(self, "No Items", "Please enter some names first.")
            return

        if not self._output_dir.text():
            QMessageBox.warning(self, "No Output", "Please select an output directory.")
            return

        # Import here to avoid circular imports
        from core.batch_export import BatchExporter, BatchExportConfig, ExportItem

        # Create export items
        base_config = self._get_base_config()
        export_items = []

        for item in self._items:
            config = base_config.copy()
            # Update text in config
            if 'text' in config and 'lines' in config['text']:
                if config['text']['lines']:
                    config['text']['lines'][0]['segments'][0]['content'] = item['name']

            export_items.append(ExportItem(
                name=item['name'],
                config=config,
                filename=item['filename']
            ))

        # Create batch config
        batch_config = BatchExportConfig(
            output_directory=self._output_dir.text(),
            format=self._format_combo.currentText().lower(),
            create_subdirectory=self._subdir_check.isChecked(),
            naming_pattern=self._naming_pattern.text()
        )

        # Create exporter and worker
        exporter = BatchExporter(self.generator_func)

        self._worker = ExportWorker(exporter, export_items, batch_config)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)

        # Update UI
        self._export_btn.setEnabled(False)
        self._cancel_btn.setEnabled(True)
        self._progress_bar.setMaximum(len(export_items))
        self._progress_bar.setValue(0)

        self._worker.start()

    def _get_base_config(self) -> dict:
        """Get the base configuration from the main window."""
        # This should be overridden or connected to the main window
        return {
            'text': {
                'lines': [{'segments': [{'content': ''}]}]
            }
        }

    def set_base_config(self, config: dict):
        """Set the base configuration to use for all exports."""
        self._base_config = config

    def _get_base_config(self) -> dict:
        """Get the base configuration."""
        if hasattr(self, '_base_config'):
            return self._base_config.copy()
        return {'text': {'lines': [{'segments': [{'content': ''}]}]}}

    def _cancel_export(self):
        """Cancel the export."""
        if self._worker:
            # Signal cancellation through the exporter
            pass  # Worker will check cancellation

        self._status_label.setText("Cancelled")
        self._export_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)

    def _on_progress(self, current, total, message):
        """Handle progress update."""
        self._progress_bar.setValue(current)
        self._status_label.setText(message)

    def _on_finished(self, results: dict):
        """Handle export completion."""
        self._export_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)

        exported = len(results.get('exported', []))
        failed = len(results.get('failed', []))

        if failed == 0:
            self._status_label.setText(f"Complete! Exported {exported} files.")
            QMessageBox.information(
                self, "Export Complete",
                f"Successfully exported {exported} nameplates to:\n{results.get('output_dir', '')}"
            )
        else:
            self._status_label.setText(f"Completed with errors: {exported} exported, {failed} failed.")
            failures = "\n".join(f"- {name}: {error}" for name, error in results.get('failed', []))
            QMessageBox.warning(
                self, "Export Complete with Errors",
                f"Exported {exported} files, {failed} failed:\n\n{failures}"
            )
