"""
Main Window
The main application window for the Nameplate Generator.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTabWidget, QMenuBar, QMenu, QAction, QFileDialog, QMessageBox,
    QStatusBar, QLabel, QProgressBar, QInputDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeySequence

from ui.viewer_widget import Viewer3DWidget, PreviewManager
from ui.panels.text_panel import TextPanel
from ui.panels.base_panel import BasePlatePanel
from ui.panels.mount_panel import MountPanel
from ui.panels.preset_panel import PresetPanel

from fonts.font_manager import get_font_manager
from core.nameplate import NameplateBuilder, NameplateConfig
from core.export.exporter import ExportFormat


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        # Core components
        self._font_manager = get_font_manager()
        self._nameplate_builder = NameplateBuilder()
        self._preview_manager = None
        
        # Debounce timer for preview updates
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._do_update_preview)
        
        self._setup_ui()
        self._setup_menus()
        self._connect_signals()
        self._load_fonts()
        
        # Initial preview
        QTimer.singleShot(500, self._update_preview)
    
    def _setup_ui(self):
        """Set up the main UI layout."""
        self.setWindowTitle("3D Nameplate Generator")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Main splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side: 3D viewer and presets
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 3D Viewer
        self._viewer = Viewer3DWidget()
        self._preview_manager = PreviewManager(self._viewer)
        left_layout.addWidget(self._viewer, stretch=3)
        
        # Presets panel
        self._preset_panel = PresetPanel()
        left_layout.addWidget(self._preset_panel, stretch=1)
        
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
        
        right_layout.addWidget(self._tabs)
        
        splitter.addWidget(right_widget)
        
        # Set splitter sizes (60% viewer, 40% settings)
        splitter.setSizes([700, 500])
        
        main_layout.addWidget(splitter)
        
        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        
        self._status_label = QLabel("Ready")
        self._status_bar.addWidget(self._status_label)
        
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
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
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
        self._mount_panel.settings_changed.connect(self._schedule_update)
        
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
            self._status_label.setText(f"Error loading fonts: {e}")
    
    def _schedule_update(self):
        """Schedule a debounced preview update."""
        self._update_timer.start(300)  # 300ms debounce
    
    def _update_preview(self):
        """Trigger immediate preview update."""
        self._update_timer.stop()
        self._do_update_preview()
    
    def _do_update_preview(self):
        """Actually perform the preview update."""
        self._status_label.setText("Generating preview...")
        self._progress.setVisible(True)
        self._progress.setRange(0, 0)  # Indeterminate

        try:
            # Build config from UI
            config = self._build_config()
            self._nameplate_builder.set_config(config)

            # Generate geometry
            geometry = self._nameplate_builder.build()

            # Update viewer with separate geometries for different colors
            if self._preview_manager:
                from core.geometry.text_builder import TextStyle
                from core.geometry.base_plates import PlateShape

                # For raised text, render base and text separately with different colors
                if (config.text.style == TextStyle.RAISED and
                    config.plate.shape != PlateShape.NONE):
                    base_geom = self._nameplate_builder.get_base_geometry()
                    text_geom = self._nameplate_builder.get_text_geometry()

                    # Position text on top of plate for raised style
                    if text_geom is not None:
                        if config.plate.shape == PlateShape.SWEEPING:
                            plate_thickness = config.sweeping.thickness
                        else:
                            plate_thickness = config.plate.thickness
                        text_geom = text_geom.translate((0, 0, plate_thickness))

                    self._preview_manager.update_preview_separate(base_geom, text_geom)
                else:
                    # For engraved/cutout or text-only, use combined geometry
                    self._preview_manager.update_preview(geometry)

            self._status_label.setText("Ready")

        except Exception as e:
            self._status_label.setText(f"Error: {e}")
            print(f"Preview error: {e}")

        finally:
            self._progress.setVisible(False)
    
    def _build_config(self) -> NameplateConfig:
        """Build NameplateConfig from current UI state."""
        config = NameplateConfig()
        
        # Get text config
        text_cfg = self._text_panel.get_config()
        from core.geometry.text_builder import TextLineConfig, TextStyle, TextAlign, TextOrientation

        config.text.lines = []
        for line_data in text_cfg.get('lines', []):
            line = TextLineConfig(
                content=line_data.get('content', ''),
                font_family=line_data.get('font_family', 'Arial'),
                font_style=line_data.get('font_style', 'Regular'),
                font_size=line_data.get('font_size', 12.0),
            )
            # Get font path
            font_path = self._font_manager.get_font_path(
                line.font_family, line.font_style
            )
            if font_path:
                line.font_path = font_path
            config.text.lines.append(line)

        config.text.style = TextStyle(text_cfg.get('style', 'raised'))
        config.text.depth = text_cfg.get('depth', 2.0)
        config.text.line_spacing = text_cfg.get('line_spacing', 1.2)
        config.text.orientation = TextOrientation(text_cfg.get('orientation', 'horizontal'))
        
        # Get base plate config
        base_cfg = self._base_panel.get_config()
        from core.geometry.base_plates import PlateShape
        
        plate = base_cfg.get('plate', {})
        config.plate.shape = PlateShape(plate.get('shape', 'rounded_rectangle'))
        config.plate.width = plate.get('width', 120.0)
        config.plate.height = plate.get('height', 35.0)
        config.plate.thickness = plate.get('thickness', 4.0)
        config.plate.corner_radius = plate.get('corner_radius', 5.0)
        config.plate.auto_width = plate.get('auto_width', False)
        config.plate.auto_height = plate.get('auto_height', False)
        config.plate.padding_top = plate.get('padding_top', 5.0)
        config.plate.padding_bottom = plate.get('padding_bottom', 5.0)
        config.plate.padding_left = plate.get('padding_left', 10.0)
        config.plate.padding_right = plate.get('padding_right', 10.0)
        
        sweep = base_cfg.get('sweeping', {})
        config.sweeping.width = sweep.get('width', 120.0)
        config.sweeping.height = sweep.get('height', 35.0)
        config.sweeping.thickness = sweep.get('thickness', 4.0)
        config.sweeping.curve_angle = sweep.get('curve_angle', 45.0)
        config.sweeping.curve_radius = sweep.get('curve_radius', 80.0)
        config.sweeping.base_type = sweep.get('base_type', 'pedestal')
        
        # Get mount config
        mount_cfg = self._mount_panel.get_config()
        from core.geometry.mounts import MountType, HolePattern, MagnetSize

        config.mount.mount_type = MountType(mount_cfg.get('type', 'none'))

        # Desk stand options
        config.mount.stand_angle = mount_cfg.get('stand_angle', 25.0)
        config.mount.stand_depth = mount_cfg.get('stand_depth', 30.0)
        config.mount.stand_integrated = mount_cfg.get('stand_integrated', True)

        # Screw hole options
        pattern_map = {
            'two_top': HolePattern.TWO_TOP,
            'two_sides': HolePattern.TWO_SIDES,
            'four_corners': HolePattern.FOUR_CORNERS,
            'center_top': HolePattern.CENTER_TOP,
        }
        config.mount.hole_pattern = pattern_map.get(
            mount_cfg.get('hole_pattern', 'two_top'),
            HolePattern.TWO_TOP
        )
        config.mount.hole_diameter = mount_cfg.get('hole_diameter', 4.0)
        config.mount.hole_countersink = mount_cfg.get('countersink', True)
        config.mount.hole_edge_distance = mount_cfg.get('hole_edge_distance', 8.0)

        # Keyhole options
        config.mount.keyhole_large_diameter = mount_cfg.get('keyhole_large', 10.0)
        config.mount.keyhole_small_diameter = mount_cfg.get('keyhole_small', 5.0)
        config.mount.keyhole_length = mount_cfg.get('keyhole_length', 12.0)

        # Magnet options - parse size string like "8x3mm Disc"
        magnet_size_str = mount_cfg.get('magnet_size', '8x3mm Disc')
        magnet_diameter = 8.0
        magnet_height = 3.0
        if 'x' in magnet_size_str:
            try:
                parts = magnet_size_str.split('x')
                magnet_diameter = float(parts[0])
                magnet_height = float(parts[1].replace('mm', '').replace(' Disc', '').replace(' Cube', ''))
            except:
                pass
        config.mount.magnet_size = MagnetSize(magnet_diameter, magnet_height, magnet_size_str)
        config.mount.magnet_count = mount_cfg.get('magnet_count', 2)
        config.mount.magnet_edge_distance = mount_cfg.get('magnet_edge', 10.0)

        # Hanging hole options
        config.mount.hanging_hole_diameter = mount_cfg.get('hanging_diameter', 5.0)
        config.mount.hanging_hole_position = mount_cfg.get('hanging_position', 'top_center')

        return config
    
    def _apply_config(self, data: dict):
        """Apply configuration data to UI panels."""
        if 'text' in data:
            self._text_panel.set_config(data['text'])
        
        if 'plate' in data or 'sweeping' in data:
            self._base_panel.set_config(data)
        
        if 'mount' in data:
            self._mount_panel.set_config(data['mount'])
    
    def _on_new(self):
        """Handle File > New."""
        reply = QMessageBox.question(
            self, "New Nameplate",
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
        default_ext = ext_map[format][1].replace("*", "nameplate")
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Nameplate", default_ext, filter_str
        )
        
        if filepath:
            self._status_label.setText("Exporting...")
            try:
                if self._nameplate_builder.export(filepath):
                    self._status_label.setText(f"Exported to {filepath}")
                    QMessageBox.information(self, "Export Complete", f"Saved to:\n{filepath}")
                else:
                    self._status_label.setText("Export failed")
                    QMessageBox.warning(self, "Export Failed", "Could not export the file.")
            except Exception as e:
                self._status_label.setText(f"Export error: {e}")
                QMessageBox.warning(self, "Export Error", str(e))
    
    def _on_export_separate(self):
        """Export base and text as separate files."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Separate Parts", "nameplate.stl", "STL Files (*.stl)"
        )
        
        if filepath:
            try:
                if self._nameplate_builder.export_separate(filepath):
                    QMessageBox.information(
                        self, "Export Complete",
                        f"Exported separate base and text files."
                    )
            except Exception as e:
                QMessageBox.warning(self, "Export Error", str(e))
    
    def _on_preset_selected(self, data: dict):
        """Handle preset selection."""
        self._apply_config(data)
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
            self, "About Nameplate Generator",
            "3D Nameplate Generator\n\n"
            "Create customizable 3D-printable nameplates\n"
            "with any Windows font and Nerd Font icons.\n\n"
            "Version 0.1.0"
        )
