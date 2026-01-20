"""
Base Batch Dialog
Common base classes for batch operation dialogs.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from typing import Optional


class BaseBatchWorker(QThread):
    """
    Base worker thread for batch operations.

    Subclasses should override the run() method and emit signals appropriately.
    """

    progress = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal(object)  # results (dict, list, or other)
    error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cancelled = False

    def cancel(self):
        """Cancel the batch operation."""
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        """Check if the operation has been cancelled."""
        return self._cancelled

    def run(self):
        """
        Run the batch operation. Override in subclasses.

        Subclasses should:
        1. Check self.is_cancelled periodically
        2. Emit self.progress(current, total, message) for updates
        3. Emit self.finished(results) when done
        4. Emit self.error(message) on failure
        """
        raise NotImplementedError("Subclasses must implement run()")


class BaseBatchDialog(QDialog):
    """
    Base dialog for batch operations with progress tracking.

    Provides:
    - Progress bar and status label
    - Action, cancel, and close buttons with state management
    - Standard handlers for progress, completion, and errors

    Subclasses should:
    1. Call super().__init__() and _setup_base_ui() in their __init__
    2. Add their specific UI elements to self._main_layout
    3. Override _create_worker() to return their specific worker
    4. Override _get_action_button_text() for custom button label
    5. Override _validate_inputs() for input validation
    6. Override _on_operation_finished() for custom completion handling
    """

    def __init__(self, parent=None, title: str = "Batch Operation",
                 min_width: int = 500, min_height: int = 400):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(min_width, min_height)

        self._worker: Optional[BaseBatchWorker] = None
        self._main_layout: Optional[QVBoxLayout] = None

    def _setup_base_ui(self):
        """
        Set up the base UI elements. Call this in subclass __init__ after
        setting up any required instance variables.
        """
        self._main_layout = QVBoxLayout(self)

        # Progress section (will be at bottom, before buttons)
        self._progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(self._progress_group)

        self._progress_bar = QProgressBar()
        self._progress_bar.setTextVisible(True)
        progress_layout.addWidget(self._progress_bar)

        self._status_label = QLabel("Ready")
        progress_layout.addWidget(self._status_label)

        # Buttons
        self._button_layout = QHBoxLayout()

        self._action_btn = QPushButton(self._get_action_button_text())
        self._action_btn.clicked.connect(self._start_operation)
        self._button_layout.addWidget(self._action_btn)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self._cancel_operation)
        self._cancel_btn.setEnabled(False)
        self._button_layout.addWidget(self._cancel_btn)

        self._button_layout.addStretch()

        self._close_btn = QPushButton("Close")
        self._close_btn.clicked.connect(self.reject)
        self._button_layout.addWidget(self._close_btn)

    def _finalize_layout(self):
        """
        Finalize the layout by adding progress section and buttons.
        Call this after adding all custom UI elements to _main_layout.
        """
        self._main_layout.addWidget(self._progress_group)
        self._main_layout.addLayout(self._button_layout)

    def _get_action_button_text(self) -> str:
        """Return the text for the main action button. Override in subclasses."""
        return "Start"

    def _validate_inputs(self) -> bool:
        """
        Validate inputs before starting operation. Override in subclasses.
        Return True if valid, False otherwise.
        Show appropriate error messages if invalid.
        """
        return True

    def _create_worker(self) -> Optional[BaseBatchWorker]:
        """
        Create and return the worker for the batch operation.
        Override in subclasses to return the appropriate worker.
        """
        raise NotImplementedError("Subclasses must implement _create_worker()")

    def _get_total_items(self) -> int:
        """Return the total number of items to process. Override in subclasses."""
        return 0

    def _set_ui_running_state(self, running: bool):
        """Set UI state for running/not running. Can be extended in subclasses."""
        self._action_btn.setEnabled(not running)
        self._cancel_btn.setEnabled(running)

    def _start_operation(self):
        """Start the batch operation."""
        if not self._validate_inputs():
            return

        # Update UI state
        self._set_ui_running_state(True)

        # Set up progress
        total = self._get_total_items()
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(0)
        self._status_label.setText("Starting...")

        # Create and start worker
        self._worker = self._create_worker()
        if self._worker is None:
            self._set_ui_running_state(False)
            return

        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _cancel_operation(self):
        """Cancel the batch operation."""
        if self._worker:
            self._worker.cancel()
            self._status_label.setText("Cancelling...")

    def _on_progress(self, current: int, total: int, message: str):
        """Handle progress update."""
        self._progress_bar.setValue(current)
        self._status_label.setText(message)

    def _on_finished(self, results):
        """
        Handle operation completion. Override for custom handling.
        Default implementation restores UI state.
        """
        self._set_ui_running_state(False)
        self._on_operation_finished(results)

    def _on_operation_finished(self, results):
        """
        Called when operation finishes. Override for custom completion handling.
        Default shows a simple completion message.
        """
        self._status_label.setText("Complete!")

    def _on_error(self, error: str):
        """Handle error."""
        self._set_ui_running_state(False)
        self._status_label.setText(f"Error: {error}")
        QMessageBox.warning(self, "Error", error)

    def closeEvent(self, event):
        """Handle dialog close - cancel any running operation."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(1000)  # Wait up to 1 second
        event.accept()
