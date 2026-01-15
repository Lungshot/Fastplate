"""
Batch Generation Dialog
Dialog for generating multiple nameplates from a list.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QTextEdit, QPushButton, QCheckBox,
    QDialogButtonBox, QFileDialog, QProgressBar, QLineEdit,
    QSpinBox, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from ui.widgets.slider_spin import FocusComboBox
from pathlib import Path


class BatchWorker(QThread):
    """Worker thread for batch generation."""

    progress = pyqtSignal(int, int, str)  # current, total, name
    finished = pyqtSignal(list)  # list of exported files
    error = pyqtSignal(str)

    def __init__(self, names: list, builder, output_dir: str, format: str,
                 base_config: dict):
        super().__init__()
        self.names = names
        self.builder = builder
        self.output_dir = output_dir
        self.format = format
        self.base_config = base_config
        self._cancelled = False

    def cancel(self):
        """Cancel the batch operation."""
        self._cancelled = True

    def run(self):
        """Run the batch generation."""
        exported = []
        total = len(self.names)

        for i, name in enumerate(self.names):
            if self._cancelled:
                break

            self.progress.emit(i + 1, total, name)

            try:
                # Update first text line with current name
                config = self.builder.config
                if config.text.lines:
                    # Update first line's first segment or content
                    if config.text.lines[0].segments:
                        config.text.lines[0].segments[0].content = name
                    config.text.lines[0].content = name

                # Rebuild geometry
                self.builder._needs_rebuild = True
                self.builder.build()

                # Export
                safe_name = "".join(c for c in name if c.isalnum() or c in ' _-').strip()
                safe_name = safe_name.replace(' ', '_')
                filename = f"{safe_name}.{self.format}"
                filepath = Path(self.output_dir) / filename

                if self.builder.export(str(filepath)):
                    exported.append(str(filepath))

            except Exception as e:
                print(f"Error generating '{name}': {e}")
                continue

        self.finished.emit(exported)


class BatchDialog(QDialog):
    """Dialog for batch nameplate generation."""

    def __init__(self, nameplate_builder, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Generation")
        self.setMinimumSize(500, 500)

        self._builder = nameplate_builder
        self._worker = None
        self._output_dir = ""

        self._setup_ui()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Input section
        input_group = QGroupBox("Names/Text List")
        input_layout = QVBoxLayout(input_group)

        input_label = QLabel("Enter one name per line:")
        input_layout.addWidget(input_label)

        self._names_edit = QTextEdit()
        self._names_edit.setPlaceholderText(
            "John Smith\n"
            "Jane Doe\n"
            "Bob Johnson\n"
            "..."
        )
        input_layout.addWidget(self._names_edit)

        # Import from file
        import_row = QHBoxLayout()
        import_btn = QPushButton("Import from CSV/TXT...")
        import_btn.clicked.connect(self._import_names)
        import_row.addWidget(import_btn)
        import_row.addStretch()

        count_label = QLabel("Names: 0")
        self._count_label = count_label
        import_row.addWidget(count_label)
        input_layout.addLayout(import_row)

        self._names_edit.textChanged.connect(self._update_count)

        layout.addWidget(input_group)

        # Output section
        output_group = QGroupBox("Output Settings")
        output_layout = QFormLayout(output_group)

        # Output directory
        dir_row = QHBoxLayout()
        self._dir_edit = QLineEdit()
        self._dir_edit.setPlaceholderText("Select output directory...")
        self._dir_edit.setReadOnly(True)
        dir_row.addWidget(self._dir_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_output)
        dir_row.addWidget(browse_btn)
        output_layout.addRow("Output folder:", dir_row)

        # Format
        self._format_combo = FocusComboBox()
        self._format_combo.addItems(["STL", "STEP", "3MF"])
        output_layout.addRow("File format:", self._format_combo)

        layout.addWidget(output_group)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)

        self._use_template_check = QCheckBox("Use current design as template")
        self._use_template_check.setChecked(True)
        self._use_template_check.setToolTip(
            "The first text line will be replaced with each name.\n"
            "All other settings (fonts, plate, etc.) will be kept."
        )
        options_layout.addWidget(self._use_template_check)

        self._overwrite_check = QCheckBox("Overwrite existing files")
        self._overwrite_check.setChecked(False)
        options_layout.addWidget(self._overwrite_check)

        layout.addWidget(options_group)

        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)

        self._progress_bar = QProgressBar()
        self._progress_bar.setTextVisible(True)
        progress_layout.addWidget(self._progress_bar)

        self._status_label = QLabel("Ready")
        progress_layout.addWidget(self._status_label)

        layout.addWidget(progress_group)

        # Buttons
        button_layout = QHBoxLayout()

        self._generate_btn = QPushButton("Generate All")
        self._generate_btn.clicked.connect(self._start_generation)
        button_layout.addWidget(self._generate_btn)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self._cancel_generation)
        self._cancel_btn.setEnabled(False)
        button_layout.addWidget(self._cancel_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _update_count(self):
        """Update the names count label."""
        names = self._get_names()
        self._count_label.setText(f"Names: {len(names)}")

    def _get_names(self) -> list:
        """Get list of names from text edit."""
        text = self._names_edit.toPlainText()
        names = [n.strip() for n in text.split('\n') if n.strip()]
        return names

    def _import_names(self):
        """Import names from a CSV or TXT file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Import Names",
            "",
            "Text Files (*.txt *.csv);;All Files (*.*)"
        )

        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Handle CSV (take first column)
                if filepath.lower().endswith('.csv'):
                    import csv
                    from io import StringIO
                    reader = csv.reader(StringIO(content))
                    names = [row[0] for row in reader if row and row[0].strip()]
                else:
                    names = [n.strip() for n in content.split('\n') if n.strip()]

                self._names_edit.setPlainText('\n'.join(names))

            except Exception as e:
                QMessageBox.warning(self, "Import Error", f"Could not import file:\n{e}")

    def _browse_output(self):
        """Browse for output directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory",
            self._output_dir or str(Path.home())
        )

        if directory:
            self._output_dir = directory
            self._dir_edit.setText(directory)

    def _start_generation(self):
        """Start the batch generation process."""
        names = self._get_names()
        if not names:
            QMessageBox.warning(self, "No Names", "Please enter at least one name.")
            return

        if not self._output_dir:
            QMessageBox.warning(self, "No Output", "Please select an output directory.")
            return

        # Disable UI
        self._generate_btn.setEnabled(False)
        self._cancel_btn.setEnabled(True)
        self._names_edit.setEnabled(False)

        # Set up progress
        self._progress_bar.setMaximum(len(names))
        self._progress_bar.setValue(0)

        # Get format
        format_map = {"STL": "stl", "STEP": "step", "3MF": "3mf"}
        export_format = format_map.get(self._format_combo.currentText(), "stl")

        # Create and start worker
        self._worker = BatchWorker(
            names, self._builder, self._output_dir, export_format,
            {}
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _cancel_generation(self):
        """Cancel the batch generation."""
        if self._worker:
            self._worker.cancel()
            self._status_label.setText("Cancelling...")

    def _on_progress(self, current: int, total: int, name: str):
        """Handle progress update."""
        self._progress_bar.setValue(current)
        self._status_label.setText(f"Generating: {name} ({current}/{total})")

    def _on_finished(self, exported: list):
        """Handle batch completion."""
        self._generate_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._names_edit.setEnabled(True)

        if exported:
            self._status_label.setText(f"Complete! Generated {len(exported)} files.")
            QMessageBox.information(
                self, "Batch Complete",
                f"Successfully generated {len(exported)} nameplates.\n\n"
                f"Output folder:\n{self._output_dir}"
            )
        else:
            self._status_label.setText("No files generated.")
            QMessageBox.warning(self, "Batch Failed", "No files were generated.")

    def _on_error(self, error: str):
        """Handle error."""
        self._generate_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._names_edit.setEnabled(True)
        self._status_label.setText(f"Error: {error}")
        QMessageBox.warning(self, "Error", error)
