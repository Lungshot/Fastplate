"""
Main Window
The main application window for Fastplate.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTabWidget, QMenuBar, QMenu, QAction, QFileDialog, QMessageBox,
    QStatusBar, QLabel, QProgressBar, QInputDialog, QPushButton, QApplication
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeySequence

from ui.viewer_widget import Viewer3DWidget, PreviewManager
from ui.panels.text_panel import TextPanel
from ui.panels.base_panel import BasePlatePanel
from ui.panels.mount_panel import MountPanel
from ui.panels.preset_panel import PresetPanel
from ui.panels.svg_panel import SVGPanel
from ui.preview_worker import PreviewWorker
from ui.config_builder import ConfigBuilder

from fonts.font_manager import get_font_manager
from core.nameplate import NameplateBuilder, NameplateConfig
from core.export.exporter import ExportFormat
from core.state_manager import UndoRedoManager
from utils.debug_log import debug_log
from ui.theme_manager import get_theme_manager

# Geometry imports (moved to module level for performance)
from core.geometry.text_builder import (
    TextLineConfig, TextSegment, TextStyle, TextAlign, TextOrientation, TextEffect
)
from core.geometry.base_plates import PlateShape, EdgeStyle
from core.geometry.borders import BorderStyle
from core.geometry.patterns import PatternType
from core.geometry.mounts import MountType, HolePattern, MagnetSize


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        # Core components
        self._font_manager = get_font_manager()
        self._nameplate_builder = NameplateBuilder()
        self._config_builder = ConfigBuilder(self._font_manager)
        self._preview_manager = None
        self._theme_manager = get_theme_manager()

        # Undo/Redo manager
        self._undo_manager = UndoRedoManager(max_history=50)
        self._undo_manager.add_change_callback(self._update_undo_redo_state)

        # Project file tracking
        self._current_project_path = None

        # Debounce timer for preview updates
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._do_update_preview)

        # Flag to auto-fit view on first load
        self._should_auto_fit = True

        # Background worker for geometry generation (prevents UI freezing)
        self._preview_worker = PreviewWorker()
        self._preview_worker.set_builder(self._nameplate_builder)
        self._preview_worker.preview_ready.connect(self._on_preview_ready)
        self._preview_worker.preview_error.connect(self._on_preview_error)
        self._preview_worker.progress_update.connect(self._on_progress_update)
        self._preview_worker.generation_started.connect(self._on_generation_started)
        self._preview_worker.generation_finished.connect(self._on_generation_finished)

        # Track if we're currently generating
        self._is_generating = False

        self._setup_ui()
        self._setup_menus()
        self._connect_signals()
        self._load_fonts()

        # Initial preview
        QTimer.singleShot(500, self._update_preview)
    
    def _setup_ui(self):
        """Set up the main UI layout."""
        self.setWindowTitle("Fastplate")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Main splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side: 3D viewer with Undo/Redo buttons below
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 3D Viewer
        self._viewer = Viewer3DWidget()
        self._preview_manager = PreviewManager(self._viewer)
        left_layout.addWidget(self._viewer, stretch=1)

        # Undo/Redo buttons below viewport
        undo_redo_layout = QHBoxLayout()
        undo_redo_layout.addStretch()

        self._undo_btn = QPushButton("← Undo")
        self._undo_btn.setEnabled(False)
        self._undo_btn.setToolTip("Undo last change (Ctrl+Z)")
        self._undo_btn.clicked.connect(self._on_undo)
        self._undo_btn.setMinimumWidth(80)
        undo_redo_layout.addWidget(self._undo_btn)

        self._redo_btn = QPushButton("Redo →")
        self._redo_btn.setEnabled(False)
        self._redo_btn.setToolTip("Redo last change (Ctrl+Y)")
        self._redo_btn.clicked.connect(self._on_redo)
        self._redo_btn.setMinimumWidth(80)
        undo_redo_layout.addWidget(self._redo_btn)

        undo_redo_layout.addStretch()
        left_layout.addLayout(undo_redo_layout)

        splitter.addWidget(left_widget)
        
        # Right side: Settings tabs
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Settings tabs
        self._tabs = QTabWidget()
        
        # Text panel
        self._text_panel = TextPanel()
        self._tabs.addTab(self._text_panel, "Text")
        
        # Base plate panel
        self._base_panel = BasePlatePanel()
        self._tabs.addTab(self._base_panel, "Base Plate")
        
        # Mount panel
        self._mount_panel = MountPanel()
        self._tabs.addTab(self._mount_panel, "Mounting")

        # SVG panel
        self._svg_panel = SVGPanel()
        self._tabs.addTab(self._svg_panel, "SVG/Graphics")

        # Presets panel (moved from below viewport)
        self._preset_panel = PresetPanel()
        self._tabs.addTab(self._preset_panel, "Presets")

        right_layout.addWidget(self._tabs)
        
        splitter.addWidget(right_widget)
        
        # Set splitter sizes (60% viewer, 40% settings)
        splitter.setSizes([700, 500])
        
        main_layout.addWidget(splitter)
        
        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet("QLabel { padding-right: 5px; }")
        self._status_bar.addWidget(self._status_label, 1)  # Stretch factor 1

        # Copy error button (hidden by default)
        self._copy_error_btn = QPushButton("📋 Copy")
        self._copy_error_btn.setFixedWidth(70)
        self._copy_error_btn.setToolTip("Copy error message to clipboard")
        self._copy_error_btn.clicked.connect(self._copy_error_to_clipboard)
        self._copy_error_btn.setVisible(False)
        self._status_bar.addWidget(self._copy_error_btn)

        self._last_error_text = ""  # Store full error for copying

        self._progress = QProgressBar()
        self._progress.setMaximumWidth(200)
        self._progress.setVisible(False)
        self._status_bar.addPermanentWidget(self._progress)
    
    def _setup_menus(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._on_new)
        file_menu.addAction(new_action)

        open_action = QAction("&Open Project...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._on_open_project)
        file_menu.addAction(open_action)

        save_action = QAction("&Save Project", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._on_save_project)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save Project &As...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self._on_save_project_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()
        
        export_stl = QAction("Export &STL...", self)
        export_stl.setShortcut(QKeySequence("Ctrl+E"))
        export_stl.triggered.connect(lambda: self._on_export(ExportFormat.STL))
        file_menu.addAction(export_stl)
        
        export_step = QAction("Export ST&EP...", self)
        export_step.triggered.connect(lambda: self._on_export(ExportFormat.STEP))
        file_menu.addAction(export_step)
        
        export_3mf = QAction("Export &3MF...", self)
        export_3mf.triggered.connect(lambda: self._on_export(ExportFormat.THREE_MF))
        file_menu.addAction(export_3mf)
        
        file_menu.addSeparator()
        
        export_separate = QAction("Export Separate Parts...", self)
        export_separate.triggered.connect(self._on_export_separate)
        file_menu.addAction(export_separate)

        file_menu.addSeparator()

        batch_action = QAction("&Batch Generate...", self)
        batch_action.setShortcut(QKeySequence("Ctrl+B"))
        batch_action.triggered.connect(self._on_batch_generate)
        file_menu.addAction(batch_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        self._undo_action = QAction("&Undo", self)
        self._undo_action.setShortcut(QKeySequence.Undo)
        self._undo_action.triggered.connect(self._on_undo)
        self._undo_action.setEnabled(False)
        edit_menu.addAction(self._undo_action)

        self._redo_action = QAction("&Redo", self)
        self._redo_action.setShortcut(QKeySequence.Redo)
        self._redo_action.triggered.connect(self._on_redo)
        self._redo_action.setEnabled(False)
        edit_menu.addAction(self._redo_action)

        edit_menu.addSeparator()

        refresh_action = QAction("&Refresh Preview", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self._update_preview)
        edit_menu.addAction(refresh_action)
        
        # Presets menu
        presets_menu = menubar.addMenu("&Presets")

        save_preset = QAction("&Save Current as Preset...", self)
        save_preset.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_preset.triggered.connect(self._on_save_preset)
        presets_menu.addAction(save_preset)

        # View menu
        view_menu = menubar.addMenu("&View")

        self._dark_mode_action = QAction("&Dark Mode", self)
        self._dark_mode_action.setCheckable(True)
        self._dark_mode_action.setChecked(self._theme_manager.is_dark_mode)
        self._dark_mode_action.triggered.connect(self._on_toggle_dark_mode)
        view_menu.addAction(self._dark_mode_action)

        view_menu.addSeparator()

        reset_view_action = QAction("&Reset 3D View", self)
        reset_view_action.setShortcut(QKeySequence("Home"))
        reset_view_action.triggered.connect(self._on_reset_view)
        view_menu.addAction(reset_view_action)

        # Debug menu
        debug_menu = menubar.addMenu("&Debug")

        self._debug_logging_action = QAction("Enable &Debug Logging", self)
        self._debug_logging_action.setCheckable(True)
        self._debug_logging_action.setChecked(debug_log.enabled)
        self._debug_logging_action.triggered.connect(self._on_toggle_debug_logging)
        debug_menu.addAction(self._debug_logging_action)

        open_log_action = QAction("&Open Log File Location...", self)
        open_log_action.triggered.connect(self._on_open_log_location)
        debug_menu.addAction(open_log_action)

        debug_menu.addSeparator()

        dump_config_action = QAction("Dump Current &Config to Log", self)
        dump_config_action.triggered.connect(self._on_dump_config)
        debug_menu.addAction(dump_config_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def _connect_signals(self):
        """Connect UI signals to handlers."""
        # Panel changes trigger preview update
        self._text_panel.settings_changed.connect(self._schedule_update)
        self._base_panel.settings_changed.connect(self._schedule_update)
        self._base_panel.dimension_dragging.connect(self._on_dimension_dragging)
        # Real-time scale preview for width/height/thickness
        self._base_panel.baseplate_scale_dragging.connect(self._on_baseplate_scale_dragging)
        self._base_panel.dimension_drag_started.connect(self._on_baseplate_drag_started)
        self._base_panel.dimension_drag_ended.connect(self._on_baseplate_drag_ended)
        self._mount_panel.settings_changed.connect(self._schedule_update)
        # Real-time mount slider preview during drag
        self._mount_panel.slider_dragging.connect(self._on_dimension_dragging)
        self._svg_panel.settings_changed.connect(self._schedule_update)
        # Real-time SVG position preview during drag
        self._svg_panel.svg_position_dragging.connect(self._on_svg_position_dragging)
        # Real-time SVG slider preview during drag (size, depth)
        self._svg_panel.slider_dragging.connect(self._on_dimension_dragging)
        # Real-time text position preview during drag
        self._text_panel.text_position_dragging.connect(self._on_text_position_dragging)
        # Real-time text slider preview during drag (depth, spacing, effect, arc)
        self._text_panel.slider_dragging.connect(self._on_dimension_dragging)

        # Google icon selection from text panel
        self._text_panel.google_icon_selected.connect(self._on_google_icon_selected)

        # Font Awesome icon selection from text panel
        self._text_panel.font_awesome_icon_selected.connect(self._on_font_awesome_icon_selected)

        # Preset selection
        self._preset_panel.preset_selected.connect(self._on_preset_selected)
        self._preset_panel.save_requested.connect(self._on_save_preset)
    
    def _load_fonts(self):
        """Load system fonts and populate font selectors."""
        self._status_label.setText("Loading fonts...")
        
        try:
            self._font_manager.load_fonts()
            font_names = self._font_manager.get_family_names()
            self._text_panel.set_fonts(font_names)
            self._status_label.setText(f"Loaded {len(font_names)} fonts")
        except Exception as e:
            self._set_status(f"Error loading fonts: {e}", is_error=True)
    
    def _schedule_update(self):
        """Schedule a debounced preview update."""
        # 500ms debounce - gives more time for rapid typing/slider movement
        # before triggering expensive geometry rebuild
        self._update_timer.start(500)
    
    def _update_preview(self):
        """Trigger immediate preview update."""
        self._update_timer.stop()
        self._do_update_preview()
    
    def _do_update_preview(self):
        """Actually perform the preview update using background worker."""
        # Build config from UI (this is fast)
        config = self._build_config()

        # Save state for undo/redo (only if not restoring from undo/redo)
        if not getattr(self, '_is_restoring_state', False):
            self._undo_manager.save_state(config.to_dict(), "Settings changed")

        # Store config for use in the callback
        self._pending_config = config

        # Request preview generation in background thread
        self._preview_worker.request_preview(config)

    def _do_update_preview_no_save(self):
        """Update preview without saving state (used after undo/redo restore)."""
        # Build config from UI (this is fast)
        config = self._build_config()

        # Store config for use in the callback
        self._pending_config = config

        # Request preview generation in background thread
        self._preview_worker.request_preview(config)

    def _on_generation_started(self):
        """Called when background generation starts."""
        self._is_generating = True
        self._status_label.setText("Generating...")
        self._progress.setVisible(True)
        self._progress.setRange(0, 0)  # Indeterminate

    def _on_generation_finished(self):
        """Called when background generation finishes."""
        self._is_generating = False
        self._progress.setVisible(False)

    def _on_progress_update(self, message: str):
        """Called with progress updates from worker."""
        self._status_label.setText(message)

    def _on_preview_ready(self, geometry, base_geom, text_geom):
        """Called when preview geometry is ready from background worker."""
        try:
            if self._preview_manager:
                config = self._pending_config

                # Check if mounts are enabled (which modify the geometry)
                has_mounts = config.mount.mount_type != MountType.NONE

                # Check if there are SVG elements (icons, imported SVGs, etc.)
                # These are only included in combined geometry, not in separate base/text
                has_svg_elements = len(config.svg_elements) > 0

                # For raised text WITHOUT mounts AND without SVG elements,
                # render base and text separately with different colors.
                # When mounts are enabled OR SVG elements exist, we must use
                # combined geometry to show everything correctly.
                if (config.text.style == TextStyle.RAISED and
                    config.plate.shape != PlateShape.NONE and
                    not has_mounts and
                    not has_svg_elements):

                    # Position text on top of plate for raised style
                    if text_geom is not None:
                        if config.plate.shape == PlateShape.SWEEPING:
                            plate_thickness = config.sweeping.thickness
                        else:
                            plate_thickness = config.plate.thickness
                        text_geom = text_geom.translate((0, 0, plate_thickness))

                    self._preview_manager.update_preview_separate(base_geom, text_geom, auto_fit=self._should_auto_fit)
                else:
                    # For engraved/cutout, text-only, raised with mounts, or raised with SVG elements
                    # - use combined geometry
                    self._preview_manager.update_preview(geometry, auto_fit=self._should_auto_fit)

                # Clear any SVG overlays now that full geometry is ready
                # BUT only if not currently dragging (avoid flicker mid-drag)
                if not self._svg_panel.is_dragging():
                    self._preview_manager.clear_svg_overlays()

                # After first load, don't auto-fit anymore
                self._should_auto_fit = False

            self._set_status("Ready")

        except Exception as e:
            self._set_status(f"Error: {e}", is_error=True)
            print(f"Preview display error: {e}")

    def _on_preview_error(self, error_message: str):
        """Called when preview generation fails."""
        self._set_status(f"Error: {error_message}", is_error=True)
        print(f"Preview error: {error_message}")
    
    def _build_config(self) -> NameplateConfig:
        """Build NameplateConfig from current UI state."""
        return self._config_builder.build(
            self._text_panel,
            self._base_panel,
            self._mount_panel,
            self._svg_panel
        )
    
    def _apply_config(self, data: dict):
        """Apply configuration data to UI panels."""
        if 'text' in data:
            self._text_panel.set_config(data['text'])

        if 'plate' in data or 'sweeping' in data:
            self._base_panel.set_config(data)

        if 'mount' in data:
            self._mount_panel.set_config(data['mount'])

        if 'svg_elements' in data:
            self._svg_panel.set_config({'elements': data['svg_elements']})

    def _on_undo(self):
        """Handle Edit > Undo."""
        state = self._undo_manager.undo()
        if state:
            self._restore_state(state)

    def _on_redo(self):
        """Handle Edit > Redo."""
        state = self._undo_manager.redo()
        if state:
            self._restore_state(state)

    def _restore_state(self, state: dict):
        """Restore UI state from undo/redo."""
        # Set flag to prevent saving this restoration as a new state
        self._is_restoring_state = True
        try:
            # Stop any pending scheduled updates to prevent them from
            # saving state after the restoring flag is reset
            self._update_timer.stop()
            self._apply_config(state)
            self._update_preview()
        finally:
            self._is_restoring_state = False
            # Stop timer again in case _apply_config triggered new scheduled updates
            self._update_timer.stop()
            # Now trigger a single update that won't save state
            # (flag is already False but we do immediate update)
            QTimer.singleShot(0, self._do_update_preview_no_save)

    def _update_undo_redo_state(self):
        """Update undo/redo menu action and button enabled states."""
        can_undo = self._undo_manager.can_undo()
        can_redo = self._undo_manager.can_redo()

        # Update menu actions
        if hasattr(self, '_undo_action'):
            self._undo_action.setEnabled(can_undo)
            desc = self._undo_manager.get_undo_description()
            self._undo_action.setText(f"&Undo {desc}" if desc else "&Undo")

        if hasattr(self, '_redo_action'):
            self._redo_action.setEnabled(can_redo)
            desc = self._undo_manager.get_redo_description()
            self._redo_action.setText(f"&Redo {desc}" if desc else "&Redo")

        # Update buttons below viewport
        if hasattr(self, '_undo_btn'):
            self._undo_btn.setEnabled(can_undo)

        if hasattr(self, '_redo_btn'):
            self._redo_btn.setEnabled(can_redo)

    def _set_status(self, message: str, is_error: bool = False):
        """Set status bar message, tracking errors for copy button."""
        self._status_label.setText(message)
        if is_error:
            self._last_error_text = message
            self._status_label.setStyleSheet("QLabel { color: #ff6666; padding-right: 5px; }")
            self._copy_error_btn.setVisible(True)
        else:
            self._last_error_text = ""
            self._status_label.setStyleSheet("QLabel { padding-right: 5px; }")
            self._copy_error_btn.setVisible(False)

    def _copy_error_to_clipboard(self):
        """Copy the last error message to clipboard."""
        # Get the actual text from the status label as fallback
        error_text = self._last_error_text or self._status_label.text()
        if error_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(error_text)
            # Briefly show confirmation
            original_text = error_text
            self._status_label.setText("Error copied to clipboard!")
            QTimer.singleShot(1500, lambda: self._status_label.setText(original_text))

    def _on_new(self):
        """Handle File > New."""
        reply = QMessageBox.question(
            self, "New Design",
            "Clear current design and start fresh?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Reset to defaults
            self._apply_config({
                'text': {
                    'lines': [{'content': 'Your Name', 'font_size': 12}],
                    'style': 'raised',
                    'depth': 2.0,
                },
                'plate': {
                    'shape': 'rounded_rectangle',
                    'width': 120,
                    'height': 35,
                    'thickness': 4,
                },
                'mount': {'type': 'none'},
                'svg_elements': [],
            })
            self._update_preview()
    
    def _on_export(self, format: ExportFormat):
        """Handle export action."""
        ext_map = {
            ExportFormat.STL: ("STL Files", "*.stl"),
            ExportFormat.STEP: ("STEP Files", "*.step"),
            ExportFormat.THREE_MF: ("3MF Files", "*.3mf"),
        }
        
        filter_str = f"{ext_map[format][0]} ({ext_map[format][1]})"
        default_ext = ext_map[format][1].replace("*", "fastplate")
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export", default_ext, filter_str
        )
        
        if filepath:
            self._set_status("Exporting...")
            try:
                if self._nameplate_builder.export(filepath):
                    self._set_status(f"Exported to {filepath}")
                    QMessageBox.information(self, "Export Complete", f"Saved to:\n{filepath}")
                else:
                    self._set_status("Export failed", is_error=True)
                    QMessageBox.warning(self, "Export Failed", "Could not export the file.")
            except Exception as e:
                self._set_status(f"Export error: {e}", is_error=True)
                QMessageBox.warning(self, "Export Error", str(e))
    
    def _on_export_separate(self):
        """Export base and text as separate files for multi-color printing."""
        from ui.dialogs.multicolor_export_dialog import MultiColorExportDialog

        dialog = MultiColorExportDialog(self)
        if dialog.exec_() != MultiColorExportDialog.Accepted:
            return

        config = dialog.get_config()
        ext_map = {'stl': '*.stl', 'step': '*.step', '3mf': '*.3mf'}
        ext = config['format']

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Multi-Color",
            f"fastplate.{ext}",
            f"{ext.upper()} Files ({ext_map[ext]})"
        )

        if not filepath:
            return

        try:
            from pathlib import Path
            path = Path(filepath)
            stem = path.stem
            suffix = path.suffix or f'.{ext}'
            folder = path.parent

            exported_files = []

            # Export base
            if config['export_base']:
                base_path = folder / f"{stem}{config['base_suffix']}{suffix}"
                base_geom = self._nameplate_builder.get_base_geometry()
                if base_geom and self._nameplate_builder._exporter.export(base_geom, base_path):
                    exported_files.append(str(base_path))

            # Export text
            if config['export_text']:
                text_path = folder / f"{stem}{config['text_suffix']}{suffix}"
                text_geom = self._nameplate_builder.get_text_geometry()
                if text_geom and self._nameplate_builder._exporter.export(text_geom, text_path):
                    exported_files.append(str(text_path))

            # Export combined
            if config['export_combined']:
                combined_path = folder / f"{stem}{suffix}"
                if self._nameplate_builder.export(str(combined_path)):
                    exported_files.append(str(combined_path))

            if exported_files:
                files_list = '\n'.join(f'  • {f}' for f in exported_files)
                QMessageBox.information(
                    self, "Export Complete",
                    f"Exported {len(exported_files)} file(s):\n{files_list}"
                )
                self._set_status(f"Exported {len(exported_files)} files")
            else:
                QMessageBox.warning(self, "Export Failed", "No files were exported.")

        except Exception as e:
            QMessageBox.warning(self, "Export Error", str(e))
    
    def _on_batch_generate(self):
        """Open batch generation dialog."""
        from ui.dialogs.batch_dialog import BatchDialog

        dialog = BatchDialog(self._nameplate_builder, self)
        dialog.exec_()

    def _on_preset_selected(self, data: dict):
        """Handle preset selection."""
        self._apply_config(data)
        self._should_auto_fit = True  # Auto-fit when loading preset
        self._update_preview()
    
    def _on_save_preset(self):
        """Save current config as a preset."""
        name, ok = QInputDialog.getText(
            self, "Save Preset", "Enter a name for this preset:"
        )
        
        if ok and name:
            config = self._build_config()
            data = config.to_dict()
            data['name'] = name
            
            self._preset_panel.save_preset(name, data)
    
    def _on_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "About Fastplate",
            "Fastplate\n\n"
            "Create customizable 3D-printable nameplates\n"
            "with any Windows font, Nerd Font icons,\n"
            "Google Material icons, and SVG graphics.\n\n"
            "Version 0.2.0"
        )

    def _on_google_icon_selected(self, icon_data: dict):
        """Handle Google Material icon selection from text panel."""
        svg_content = icon_data.get('svg_content')
        name = icon_data.get('name', 'Material Icon')
        size = icon_data.get('size', 12)
        style = icon_data.get('style', 'baseline')

        if svg_content:
            # Add the icon to the SVG panel
            display_name = f"{name} ({style})"
            success = self._svg_panel.add_svg_from_content(svg_content, display_name, target_size=size)

            if success:
                # Switch to SVG tab to show the added icon
                self._tabs.setCurrentWidget(self._svg_panel)
                self._status_label.setText(f"Added Google icon: {name}")
            else:
                QMessageBox.warning(
                    self,
                    "Icon Import Failed",
                    f"Could not import the Google icon '{name}'.\n"
                    "The icon may not contain valid path data."
                )

    def _on_font_awesome_icon_selected(self, icon_data: dict):
        """Handle Font Awesome icon selection from text panel."""
        svg_content = icon_data.get('svg_content')
        name = icon_data.get('name', 'Font Awesome Icon')
        size = icon_data.get('size', 12)
        style = icon_data.get('style', 'solid')

        if svg_content:
            # Add the icon to the SVG panel
            display_name = f"{name} ({style})"
            success = self._svg_panel.add_svg_from_content(svg_content, display_name, target_size=size)

            if success:
                # Switch to SVG tab to show the added icon
                self._tabs.setCurrentWidget(self._svg_panel)
                self._status_label.setText(f"Added Font Awesome icon: {name}")
            else:
                QMessageBox.warning(
                    self,
                    "Icon Import Failed",
                    f"Could not import the Font Awesome icon '{name}'.\n"
                    "The icon may not contain valid path data."
                )

    def _on_svg_position_dragging(self, element_id: str, x: float, y: float, z: float, rotation: float):
        """Handle real-time SVG position update during slider drag.

        This updates the SVG overlay position instantly without full geometry rebuild.
        """
        if not self._preview_manager:
            return

        # Get the SVG widget to access the element
        svg_widget = self._svg_panel.get_svg_widget_by_id(element_id)
        if not svg_widget:
            return

        element = svg_widget.get_element()

        # Get plate thickness for Z positioning (raised SVGs sit on top)
        config = self._build_config()
        if config.plate.shape.value == 'sweeping':
            plate_thickness = config.sweeping.thickness
        else:
            plate_thickness = config.plate.thickness

        # Calculate Z based on style
        if element.style == "raised":
            z_offset = plate_thickness - 0.1  # Slightly into plate for union
        else:
            z_offset = 0

        # Create overlay if it doesn't exist
        if not self._preview_manager.has_svg_overlay(element_id):
            # Get cached geometry from nameplate builder (at origin, no position)
            svg_geom = self._nameplate_builder._get_cached_svg_geometry(
                element,
                target_size=getattr(element, 'target_size', 20.0)
            )
            if svg_geom:
                self._preview_manager.add_svg_overlay(element_id, svg_geom)

        # Update overlay transform (this is instant)
        self._preview_manager.update_svg_transform(element_id, x, y, z_offset, rotation)

    def _on_text_position_dragging(self, segment_id: str, v_offset: float):
        """Handle real-time text position update during slider drag.

        For text, we trigger an immediate preview update with reduced debounce
        since text geometry is complex and can't easily be transformed like SVG.
        """
        # Trigger immediate update (30ms debounce for responsive feedback)
        self._update_timer.start(30)

    def _on_dimension_dragging(self):
        """Handle real-time dimension update during slider drag.

        Triggers fast preview updates for baseplate and other dimension changes.
        """
        # Trigger immediate update (30ms debounce for responsive feedback)
        self._update_timer.start(30)

    def _on_baseplate_drag_started(self):
        """Handle start of baseplate dimension slider drag.

        Creates a baseplate overlay for real-time scale preview.
        """
        if not self._preview_manager:
            return

        # Get the current baseplate geometry from the builder
        base_geom = self._nameplate_builder.get_base_geometry()
        if base_geom is None:
            return

        # Get current dimensions
        width, height, thickness = self._base_panel.get_current_dimensions()

        # Create the overlay with current geometry and base dimensions
        self._preview_manager.add_baseplate_overlay(base_geom, width, height, thickness)

    def _on_baseplate_scale_dragging(self, width: float, height: float, thickness: float):
        """Handle real-time baseplate scale update during slider drag.

        Updates the baseplate overlay scale instantly without geometry rebuild.
        """
        if not self._preview_manager:
            return

        # Update overlay scale if it exists
        if self._preview_manager.has_baseplate_overlay():
            self._preview_manager.update_baseplate_scale(width, height, thickness)

    def _on_baseplate_drag_ended(self):
        """Handle end of baseplate dimension slider drag.

        Removes the overlay and triggers full geometry rebuild.
        """
        if self._preview_manager:
            self._preview_manager.remove_baseplate_overlay()

        # Trigger full geometry rebuild with final values
        self._update_timer.start(50)

    def _on_toggle_debug_logging(self, checked: bool):
        """Toggle debug logging on/off."""
        if checked:
            debug_log.enable()
            self._debug_logging_action.setText("Disable &Debug Logging")
            log_path = debug_log.log_file_path
            self._set_status(f"Debug logging enabled: {log_path}")
            debug_log.info("Debug logging started from menu")
            # Log current state
            self._on_dump_config()
        else:
            debug_log.info("Debug logging stopped from menu")
            debug_log.disable()
            self._debug_logging_action.setText("Enable &Debug Logging")
            self._set_status("Debug logging disabled")

    def _on_open_log_location(self):
        """Open the folder containing log files."""
        import os
        import subprocess

        log_path = debug_log.log_file_path
        if log_path and log_path.exists():
            # Open the folder containing the log file
            folder = str(log_path.parent)
            subprocess.run(['explorer', folder])
        else:
            # Open the default log location
            import sys
            if getattr(sys, 'frozen', False):
                folder = os.path.expanduser('~/Documents/Fastplate')
            else:
                folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')

            if os.path.exists(folder):
                subprocess.run(['explorer', folder])
            else:
                QMessageBox.information(
                    self, "Log Location",
                    f"No log files yet.\n\nLogs will be saved to:\n{folder}\n\nEnable debug logging first."
                )

    def _on_dump_config(self):
        """Dump current configuration to the debug log."""
        if not debug_log.enabled:
            QMessageBox.information(
                self, "Debug Logging",
                "Please enable debug logging first from the Debug menu."
            )
            return

        try:
            config = self._build_config()
            config_dict = config.to_dict()

            debug_log.info("=== CURRENT CONFIGURATION DUMP ===")
            import json
            formatted = json.dumps(config_dict, indent=2, default=str)
            for line in formatted.split('\n'):
                debug_log.info(line)
            debug_log.info("=== END CONFIGURATION DUMP ===")

            self._set_status("Configuration dumped to log file")
        except Exception as e:
            debug_log.exception(f"Error dumping config: {e}")

    def _on_toggle_dark_mode(self, checked: bool):
        """Toggle dark mode theme."""
        self._theme_manager.set_dark_mode(checked)
        mode = "Dark" if checked else "Light"
        self._set_status(f"{mode} mode enabled")

    def _on_reset_view(self):
        """Reset the 3D viewer to default view."""
        if self._viewer:
            self._viewer.reset_view()
            self._set_status("View reset")

    def showEvent(self, event):
        """Apply theme when window is shown."""
        super().showEvent(event)
        self._theme_manager.apply_theme()

    def _on_open_project(self):
        """Open a project file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "",
            "Fastplate Projects (*.fastplate);;All Files (*.*)"
        )

        if filepath:
            try:
                import json
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Validate it's a fastplate project
                if data.get('format') != 'fastplate':
                    QMessageBox.warning(
                        self, "Invalid File",
                        "This file is not a valid Fastplate project."
                    )
                    return

                # Apply the configuration
                self._apply_config(data)
                self._current_project_path = filepath
                self._update_window_title()
                self._should_auto_fit = True
                self._update_preview()
                self._set_status(f"Opened: {filepath}")

            except Exception as e:
                QMessageBox.warning(
                    self, "Open Error",
                    f"Could not open project:\n{e}"
                )

    def _on_save_project(self):
        """Save project to current path or prompt for new path."""
        if self._current_project_path:
            self._save_project_to_path(self._current_project_path)
        else:
            self._on_save_project_as()

    def _on_save_project_as(self):
        """Save project to a new file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "nameplate.fastplate",
            "Fastplate Projects (*.fastplate)"
        )

        if filepath:
            if not filepath.endswith('.fastplate'):
                filepath += '.fastplate'
            self._save_project_to_path(filepath)

    def _save_project_to_path(self, filepath: str):
        """Save project to the specified path."""
        try:
            import json
            config = self._build_config()
            data = config.to_dict()

            # Add project metadata
            data['format'] = 'fastplate'
            data['version'] = '1.0'

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)

            self._current_project_path = filepath
            self._update_window_title()
            self._set_status(f"Saved: {filepath}")

        except Exception as e:
            QMessageBox.warning(
                self, "Save Error",
                f"Could not save project:\n{e}"
            )

    def _update_window_title(self):
        """Update window title with current project name."""
        if self._current_project_path:
            from pathlib import Path
            name = Path(self._current_project_path).stem
            self.setWindowTitle(f"Fastplate - {name}")
        else:
            self.setWindowTitle("Fastplate")
