"""
3D Viewer Widget
PyQt5 widget for displaying CadQuery geometry with interactive controls.
Uses PyQtGraph and OpenGL for rendering.
"""

import numpy as np
import sip
from typing import Optional, Tuple
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QCheckBox
from PyQt5.QtCore import Qt, pyqtSignal
from ui.widgets.slider_spin import FocusComboBox

try:
    import pyqtgraph as pg
    import pyqtgraph.opengl as gl
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False

try:
    import cadquery as cq
    CADQUERY_AVAILABLE = True
except ImportError:
    CADQUERY_AVAILABLE = False


class Viewer3DWidget(QWidget):
    """
    3D viewer widget for displaying CadQuery geometry.
    Provides interactive rotation, pan, and zoom.
    """

    # Signals
    view_changed = pyqtSignal()

    # Predefined colors (name, RGBA tuple) - brighter for visibility
    MESH_COLORS = {
        'Light Blue': (0.5, 0.7, 0.95, 1.0),
        'Silver': (0.85, 0.85, 0.9, 1.0),
        'Light Grey': (0.75, 0.75, 0.75, 1.0),
        'White': (0.95, 0.95, 0.95, 1.0),
        'Gold': (0.95, 0.8, 0.3, 1.0),
        'Bronze': (0.8, 0.5, 0.2, 1.0),
        'Copper': (0.85, 0.55, 0.4, 1.0),
        'Green': (0.4, 0.85, 0.5, 1.0),
        'Forest': (0.2, 0.6, 0.3, 1.0),
        'Orange': (1.0, 0.6, 0.3, 1.0),
        'Red': (0.9, 0.3, 0.3, 1.0),
        'Cyan': (0.4, 0.9, 0.9, 1.0),
        'Purple': (0.7, 0.5, 0.9, 1.0),
        'Pink': (0.95, 0.6, 0.75, 1.0),
        'Yellow': (0.95, 0.9, 0.4, 1.0),
        'Black': (0.15, 0.15, 0.15, 1.0),
    }

    # Available shaders for lighting effects
    SHADERS = {
        'Shaded': 'shaded',
        'Smooth': 'balloon',
        'Normal Color': 'normalColor',
        'View Normal': 'viewNormalColor',
        'Edge Highlight': 'edgeHilight',
        'Heightmap': 'heightColor',
    }

    # View presets (elevation, azimuth) - adjusted for correct orientation
    # In pyqtgraph: azimuth 0 = looking from +X, 90 = looking from +Y
    VIEW_PRESETS = {
        'front': {'elevation': 0, 'azimuth': -90},      # Looking from -Y toward +Y
        'back': {'elevation': 0, 'azimuth': 90},        # Looking from +Y toward -Y
        'left': {'elevation': 0, 'azimuth': 180},       # Looking from -X toward +X
        'right': {'elevation': 0, 'azimuth': 0},        # Looking from +X toward -X
        'top': {'elevation': 90, 'azimuth': -90},       # Looking from +Z down
        'bottom': {'elevation': -90, 'azimuth': -90},   # Looking from -Z up
        'iso': {'elevation': 30, 'azimuth': -45},       # Isometric view
        'iso_back': {'elevation': 30, 'azimuth': 135},  # Isometric from back
    }

    # Text color offset - makes text slightly different from base
    TEXT_COLOR_OFFSET = 0.15

    def __init__(self, parent=None):
        super().__init__(parent)

        self._geometry = None
        self._base_geometry = None
        self._text_geometry = None
        self._mesh_item = None
        self._text_mesh_item = None
        self._grid_item = None
        self._current_color = self.MESH_COLORS['Light Blue']  # Default color
        self._current_shader = 'edgeHilight'  # Edge Highlight shader
        self._wireframe_mode = False
        self._show_edges = False
        self._cached_vertices = None  # Cache for base mesh refresh
        self._cached_faces = None     # Cache for base mesh refresh
        self._cached_text_vertices = None  # Cache for text mesh refresh
        self._cached_text_faces = None     # Cache for text mesh refresh
        self._model_center = np.array([0.0, 0.0, 0.0])  # Center of current model
        self._model_size = 100.0      # Size of current model for camera distance

        # SVG overlay system for real-time preview during drag
        self._svg_overlay_items = {}  # id -> GLMeshItem
        self._svg_overlay_data = {}   # id -> (vertices, faces, base_geometry)

        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if not PYQTGRAPH_AVAILABLE:
            # Show error message if PyQtGraph not available
            error_label = QLabel("PyQtGraph not installed.\nInstall with: pip install pyqtgraph PyOpenGL")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("color: red; font-size: 14px;")
            layout.addWidget(error_label)
            return
        
        # Create 3D view widget
        self._view = gl.GLViewWidget()
        self._view.setBackgroundColor((70, 75, 80, 255))  # Lighter background for contrast
        self._view.setCameraPosition(distance=150, elevation=30, azimuth=45)
        
        layout.addWidget(self._view)
        
        # Add grid with better visibility
        self._grid_item = gl.GLGridItem()
        self._grid_item.setSize(200, 200, 1)
        self._grid_item.setSpacing(10, 10, 10)
        self._grid_item.setColor((100, 100, 110, 80))  # Subtle grid lines
        self._view.addItem(self._grid_item)
        
        # Add axis indicator
        self._add_axis_indicator()
        
        # Control buttons - first row for views
        btn_layout = QHBoxLayout()

        self._fit_btn = QPushButton("Fit")
        self._fit_btn.setToolTip("Fit view to model")
        self._fit_btn.clicked.connect(self.fit_view)
        btn_layout.addWidget(self._fit_btn)

        # View preset dropdown
        btn_layout.addWidget(QLabel("View:"))
        self._view_combo = FocusComboBox()
        self._view_combo.addItems(["Isometric", "Front", "Back", "Left", "Right", "Top", "Bottom", "Iso Back"])
        self._view_combo.setCurrentText("Isometric")
        self._view_combo.currentTextChanged.connect(self._on_view_changed)
        self._view_combo.setMinimumWidth(80)
        btn_layout.addWidget(self._view_combo)

        btn_layout.addStretch()

        # Wireframe checkbox
        self._wireframe_cb = QCheckBox("Wireframe")
        self._wireframe_cb.setChecked(False)
        self._wireframe_cb.stateChanged.connect(self._on_wireframe_changed)
        btn_layout.addWidget(self._wireframe_cb)

        # Show edges checkbox
        self._edges_cb = QCheckBox("Edges")
        self._edges_cb.setChecked(False)  # Default off
        self._edges_cb.stateChanged.connect(self._on_edges_changed)
        btn_layout.addWidget(self._edges_cb)

        # Grid checkbox
        self._grid_cb = QCheckBox("Grid")
        self._grid_cb.setChecked(True)
        self._grid_cb.stateChanged.connect(self._on_grid_changed)
        btn_layout.addWidget(self._grid_cb)

        # Shader/lighting selector
        btn_layout.addWidget(QLabel("Lighting:"))
        self._shader_combo = FocusComboBox()
        self._shader_combo.addItems(list(self.SHADERS.keys()))
        self._shader_combo.setCurrentText('Edge Highlight')  # Default
        self._shader_combo.currentTextChanged.connect(self._on_shader_changed)
        self._shader_combo.setMinimumWidth(90)
        btn_layout.addWidget(self._shader_combo)

        # Color selector
        btn_layout.addWidget(QLabel("Color:"))
        self._color_combo = FocusComboBox()
        self._color_combo.addItems(list(self.MESH_COLORS.keys()))
        self._color_combo.setCurrentText('Light Blue')  # Default
        self._color_combo.currentTextChanged.connect(self._on_color_changed)
        self._color_combo.setMinimumWidth(90)
        btn_layout.addWidget(self._color_combo)

        layout.addLayout(btn_layout)
    
    def _on_color_changed(self, color_name: str):
        """Handle color selection change."""
        if color_name in self.MESH_COLORS:
            self._current_color = self.MESH_COLORS[color_name]
            self._refresh_mesh_display()

    def _on_wireframe_changed(self, state: int):
        """Handle wireframe toggle."""
        self._wireframe_mode = (state == Qt.Checked)
        self._refresh_mesh_display()

    def _on_edges_changed(self, state: int):
        """Handle edges toggle."""
        self._show_edges = (state == Qt.Checked)
        self._refresh_mesh_display()

    def _on_grid_changed(self, state: int):
        """Handle grid toggle."""
        if self._grid_item is not None:
            self._grid_item.setVisible(state == Qt.Checked)

    def _on_shader_changed(self, shader_name: str):
        """Handle shader/lighting selection change."""
        if shader_name in self.SHADERS:
            self._current_shader = self.SHADERS[shader_name]
            self._refresh_mesh_display()

    def _on_view_changed(self, view_name: str):
        """Handle view preset selection."""
        view_map = {
            'Isometric': 'iso',
            'Front': 'front',
            'Back': 'back',
            'Left': 'left',
            'Right': 'right',
            'Top': 'top',
            'Bottom': 'bottom',
            'Iso Back': 'iso_back',
        }
        preset = view_map.get(view_name, 'iso')
        self.set_view(preset)

    def _get_text_color(self) -> Tuple[float, float, float, float]:
        """Calculate a contrasting color for text based on base color."""
        r, g, b, a = self._current_color
        # Calculate luminance
        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        # If base is light, make text darker; if dark, make text lighter
        if luminance > 0.5:
            # Darken the text
            factor = 1.0 - self.TEXT_COLOR_OFFSET * 1.5
            return (r * factor, g * factor, b * factor, a)
        else:
            # Lighten the text
            factor = 1.0 + self.TEXT_COLOR_OFFSET * 2
            return (min(r * factor, 1.0), min(g * factor, 1.0), min(b * factor, 1.0), a)

    def _refresh_mesh_display(self):
        """Refresh mesh display settings without changing camera position."""
        # Refresh base mesh
        if self._mesh_item is not None and self._cached_vertices is not None:
            self._view.removeItem(self._mesh_item)

            mesh_data = gl.MeshData(vertexes=self._cached_vertices, faces=self._cached_faces)
            self._mesh_item = gl.GLMeshItem(
                meshdata=mesh_data,
                smooth=True,
                shader=self._current_shader,
                color=self._current_color,
                drawFaces=not self._wireframe_mode,
                drawEdges=self._show_edges or self._wireframe_mode,
                edgeColor=(0.2, 0.2, 0.25, 0.8) if not self._wireframe_mode else self._current_color,
                glOptions='opaque'
            )
            self._view.addItem(self._mesh_item)

        # Refresh text mesh with contrasting color
        if self._text_mesh_item is not None and self._cached_text_vertices is not None:
            self._view.removeItem(self._text_mesh_item)

            text_color = self._get_text_color()
            mesh_data = gl.MeshData(vertexes=self._cached_text_vertices, faces=self._cached_text_faces)
            self._text_mesh_item = gl.GLMeshItem(
                meshdata=mesh_data,
                smooth=True,
                shader=self._current_shader,
                color=text_color,
                drawFaces=not self._wireframe_mode,
                drawEdges=self._show_edges or self._wireframe_mode,
                edgeColor=(0.2, 0.2, 0.25, 0.8) if not self._wireframe_mode else text_color,
                glOptions='opaque'
            )
            self._view.addItem(self._text_mesh_item)

    def _add_axis_indicator(self):
        """Add XYZ axis indicator."""
        if not PYQTGRAPH_AVAILABLE:
            return
        
        axis_length = 20
        
        # X axis (red)
        x_axis = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [axis_length, 0, 0]]),
            color=(1, 0, 0, 1),
            width=2
        )
        self._view.addItem(x_axis)
        
        # Y axis (green)
        y_axis = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [0, axis_length, 0]]),
            color=(0, 1, 0, 1),
            width=2
        )
        self._view.addItem(y_axis)
        
        # Z axis (blue)
        z_axis = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [0, 0, axis_length]]),
            color=(0, 0, 1, 1),
            width=2
        )
        self._view.addItem(z_axis)
    
    def set_geometry(self, geometry, auto_fit: bool = True) -> bool:
        """
        Set the CadQuery geometry to display.

        Args:
            geometry: CadQuery Workplane or Shape
            auto_fit: If True, automatically fit view to model

        Returns:
            True if geometry was set successfully.
        """
        if not PYQTGRAPH_AVAILABLE or not CADQUERY_AVAILABLE:
            return False

        if geometry is None:
            self.clear_geometry()
            return True

        # Save current camera state if we need to preserve it
        saved_camera = None
        if not auto_fit:
            saved_camera = {
                'distance': self._view.opts.get('distance', 150),
                'elevation': self._view.opts.get('elevation', 30),
                'azimuth': self._view.opts.get('azimuth', 45),
                'center': self._view.opts.get('center', pg.Vector(0, 0, 0)),
            }

        try:
            # Get mesh data from CadQuery geometry
            vertices, faces = self._tessellate_geometry(geometry)

            if vertices is None or faces is None:
                return False

            # Cache vertices and faces for display refresh
            self._cached_vertices = vertices
            self._cached_faces = faces

            # Calculate and cache model center and size
            min_vals = vertices.min(axis=0)
            max_vals = vertices.max(axis=0)
            self._model_center = (min_vals + max_vals) / 2
            self._model_size = np.linalg.norm(max_vals - min_vals)

            # Remove existing meshes (both base and text)
            if self._mesh_item is not None:
                self._view.removeItem(self._mesh_item)
                self._mesh_item = None
            if self._text_mesh_item is not None:
                self._view.removeItem(self._text_mesh_item)
                self._text_mesh_item = None

            # Clear text caches since we're using single geometry mode
            self._cached_text_vertices = None
            self._cached_text_faces = None
            self._text_geometry = None

            # Create mesh item with current display settings
            mesh_data = gl.MeshData(vertexes=vertices, faces=faces)

            self._mesh_item = gl.GLMeshItem(
                meshdata=mesh_data,
                smooth=True,
                shader=self._current_shader,
                color=self._current_color,
                drawFaces=not self._wireframe_mode,
                drawEdges=self._show_edges or self._wireframe_mode,
                edgeColor=(0.2, 0.2, 0.25, 0.8) if not self._wireframe_mode else self._current_color,
                glOptions='opaque'
            )

            self._view.addItem(self._mesh_item)
            self._geometry = geometry

            # Auto-fit view only if requested (new geometry)
            if auto_fit:
                self.fit_view()
            elif saved_camera:
                # Restore camera state to preserve user's view
                self._view.opts['center'] = saved_camera['center']
                self._view.setCameraPosition(
                    distance=saved_camera['distance'],
                    elevation=saved_camera['elevation'],
                    azimuth=saved_camera['azimuth']
                )

            return True

        except Exception as e:
            print(f"Error setting geometry: {e}")
            return False
    
    def _tessellate_geometry(self, geometry) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Convert CadQuery geometry to mesh vertices and faces.
        """
        try:
            # Get the shape from workplane
            if hasattr(geometry, 'val'):
                shape = geometry.val()
            else:
                shape = geometry
            
            # Tessellate the shape
            # Use 0.2mm precision for faster preview (0.1 for final export)
            tess = shape.tessellate(0.2, 0.2)
            
            vertices = np.array([(v.x, v.y, v.z) for v in tess[0]])
            faces = np.array(tess[1])
            
            return vertices, faces
            
        except Exception as e:
            print(f"Tessellation error: {e}")
            return None, None
    
    def fit_view(self):
        """Fit the camera view to the current model."""
        if not PYQTGRAPH_AVAILABLE:
            return

        # Use cached model info
        distance = max(self._model_size * 2, 50)

        # Reset camera to look at model center with isometric view
        self._view.opts['center'] = pg.Vector(
            self._model_center[0],
            self._model_center[1],
            self._model_center[2]
        )
        self._view.setCameraPosition(
            distance=distance,
            elevation=30,
            azimuth=-45
        )

    def set_geometries(self, base_geometry, text_geometry, auto_fit: bool = True) -> bool:
        """
        Set separate base and text geometries to display with different colors.

        Args:
            base_geometry: CadQuery Workplane for the base plate
            text_geometry: CadQuery Workplane for the text
            auto_fit: If True, automatically fit view to model

        Returns:
            True if geometries were set successfully.
        """
        if not PYQTGRAPH_AVAILABLE or not CADQUERY_AVAILABLE:
            return False

        # Save current camera state if we need to preserve it
        saved_camera = None
        if not auto_fit:
            saved_camera = {
                'distance': self._view.opts.get('distance', 150),
                'elevation': self._view.opts.get('elevation', 30),
                'azimuth': self._view.opts.get('azimuth', 45),
                'center': self._view.opts.get('center', pg.Vector(0, 0, 0)),
            }

        # Clear existing meshes
        self.clear_geometry()

        # Handle case where both are None
        if base_geometry is None and text_geometry is None:
            return True

        try:
            all_vertices = []

            # Process base geometry
            if base_geometry is not None:
                vertices, faces = self._tessellate_geometry(base_geometry)
                if vertices is not None and faces is not None:
                    self._cached_vertices = vertices
                    self._cached_faces = faces
                    all_vertices.append(vertices)

                    mesh_data = gl.MeshData(vertexes=vertices, faces=faces)
                    self._mesh_item = gl.GLMeshItem(
                        meshdata=mesh_data,
                        smooth=True,
                        shader=self._current_shader,
                        color=self._current_color,
                        drawFaces=not self._wireframe_mode,
                        drawEdges=self._show_edges or self._wireframe_mode,
                        edgeColor=(0.2, 0.2, 0.25, 0.8) if not self._wireframe_mode else self._current_color,
                        glOptions='opaque'
                    )
                    self._view.addItem(self._mesh_item)
                    self._base_geometry = base_geometry

            # Process text geometry
            if text_geometry is not None:
                vertices, faces = self._tessellate_geometry(text_geometry)
                if vertices is not None and faces is not None:
                    self._cached_text_vertices = vertices
                    self._cached_text_faces = faces
                    all_vertices.append(vertices)

                    text_color = self._get_text_color()
                    mesh_data = gl.MeshData(vertexes=vertices, faces=faces)
                    self._text_mesh_item = gl.GLMeshItem(
                        meshdata=mesh_data,
                        smooth=True,
                        shader=self._current_shader,
                        color=text_color,
                        drawFaces=not self._wireframe_mode,
                        drawEdges=self._show_edges or self._wireframe_mode,
                        edgeColor=(0.2, 0.2, 0.25, 0.8) if not self._wireframe_mode else text_color,
                        glOptions='opaque'
                    )
                    self._view.addItem(self._text_mesh_item)
                    self._text_geometry = text_geometry

            # Calculate model center and size from combined geometry
            if all_vertices:
                combined = np.vstack(all_vertices)
                min_vals = combined.min(axis=0)
                max_vals = combined.max(axis=0)
                self._model_center = (min_vals + max_vals) / 2
                self._model_size = np.linalg.norm(max_vals - min_vals)

            # Auto-fit view only if requested
            if auto_fit:
                self.fit_view()
            elif saved_camera:
                # Restore camera state to preserve user's view
                self._view.opts['center'] = saved_camera['center']
                self._view.setCameraPosition(
                    distance=saved_camera['distance'],
                    elevation=saved_camera['elevation'],
                    azimuth=saved_camera['azimuth']
                )

            return True

        except Exception as e:
            print(f"Error setting geometries: {e}")
            return False

    def clear_geometry(self):
        """Remove all geometry from the view."""
        if PYQTGRAPH_AVAILABLE:
            if self._mesh_item is not None:
                self._view.removeItem(self._mesh_item)
                self._mesh_item = None
            if self._text_mesh_item is not None:
                self._view.removeItem(self._text_mesh_item)
                self._text_mesh_item = None
            # Clear SVG overlays
            self.clear_svg_overlays()
        self._geometry = None
        self._base_geometry = None
        self._text_geometry = None
        self._cached_vertices = None
        self._cached_faces = None
        self._cached_text_vertices = None
        self._cached_text_faces = None

    # --- SVG Overlay System for Real-Time Preview ---

    def add_svg_overlay(self, svg_id: str, geometry, color: Tuple[float, float, float, float] = None):
        """
        Add or update an SVG overlay mesh for real-time preview.

        Args:
            svg_id: Unique identifier for this SVG element
            geometry: CadQuery geometry for the SVG (at origin, no position applied)
            color: Optional color tuple (r, g, b, a), defaults to orange highlight
        """
        if not PYQTGRAPH_AVAILABLE or geometry is None:
            return

        # Default highlight color for SVG overlays
        if color is None:
            color = (1.0, 0.6, 0.2, 0.9)  # Orange highlight

        # Tessellate geometry
        vertices, faces = self._tessellate_geometry(geometry)
        if vertices is None or faces is None:
            return

        # Remove existing overlay if present
        if svg_id in self._svg_overlay_items:
            self._view.removeItem(self._svg_overlay_items[svg_id])

        # Create mesh item
        mesh_data = gl.MeshData(vertexes=vertices, faces=faces)
        mesh_item = gl.GLMeshItem(
            meshdata=mesh_data,
            smooth=True,
            shader=self._current_shader,
            color=color,
            drawFaces=True,
            drawEdges=True,
            edgeColor=(0.3, 0.3, 0.3, 0.5),
            glOptions='opaque'
        )
        self._view.addItem(mesh_item)

        # Store references
        self._svg_overlay_items[svg_id] = mesh_item
        self._svg_overlay_data[svg_id] = (vertices.copy(), faces.copy(), geometry)

    def update_svg_overlay_transform(self, svg_id: str, x: float, y: float, z: float, rotation: float = 0):
        """
        Update the transform of an SVG overlay without rebuilding mesh.
        This is the key method for real-time preview - it's very fast.

        Args:
            svg_id: The SVG element identifier
            x, y, z: Translation offsets
            rotation: Rotation around Z axis in degrees
        """
        if svg_id not in self._svg_overlay_items:
            return

        mesh_item = self._svg_overlay_items[svg_id]

        # Guard against use-after-delete (Codex review recommendation)
        if sip.isdeleted(mesh_item):
            del self._svg_overlay_items[svg_id]
            return

        # Create transform matrix
        from PyQt5.QtGui import QMatrix4x4
        transform = QMatrix4x4()
        transform.translate(x, y, z)
        if rotation != 0:
            transform.rotate(rotation, 0, 0, 1)

        # Apply transform - this is instant, no geometry rebuild
        mesh_item.setTransform(transform)

    def remove_svg_overlay(self, svg_id: str):
        """Remove a specific SVG overlay."""
        if svg_id in self._svg_overlay_items:
            if PYQTGRAPH_AVAILABLE:
                self._view.removeItem(self._svg_overlay_items[svg_id])
            del self._svg_overlay_items[svg_id]
        if svg_id in self._svg_overlay_data:
            del self._svg_overlay_data[svg_id]

    def clear_svg_overlays(self):
        """Remove all SVG overlays."""
        for svg_id in list(self._svg_overlay_items.keys()):
            self.remove_svg_overlay(svg_id)

    def has_svg_overlay(self, svg_id: str) -> bool:
        """Check if an SVG overlay exists."""
        return svg_id in self._svg_overlay_items

    # --- End SVG Overlay System ---

    def reset_view(self):
        """Reset to default isometric view centered on model."""
        if PYQTGRAPH_AVAILABLE:
            self.fit_view()

    def set_view(self, view_name: str):
        """Set a predefined view angle, keeping focus on model."""
        if not PYQTGRAPH_AVAILABLE:
            return

        if view_name in self.VIEW_PRESETS:
            params = self.VIEW_PRESETS[view_name]
            # Keep current distance, just change angles
            self._view.setCameraPosition(
                elevation=params['elevation'],
                azimuth=params['azimuth']
            )
    
    def set_background_color(self, color: Tuple[int, int, int, int]):
        """Set the background color of the 3D view."""
        if PYQTGRAPH_AVAILABLE:
            self._view.setBackgroundColor(color)
    
    def set_mesh_color(self, color: Tuple[float, float, float, float]):
        """Set the color of the displayed mesh."""
        if self._mesh_item is not None:
            self._mesh_item.setColor(color)
    
    def show_grid(self, visible: bool):
        """Show or hide the grid."""
        if self._grid_item is not None:
            self._grid_item.setVisible(visible)
    
    def get_geometry(self):
        """Get the current geometry."""
        return self._geometry


class PreviewManager:
    """
    Manages the 3D preview, handling updates and caching.
    """

    def __init__(self, viewer: Viewer3DWidget):
        self.viewer = viewer
        self._pending_update = False
        self._update_timer = None

    def update_preview(self, geometry, immediate: bool = False, auto_fit: bool = False):
        """
        Update the preview with new geometry.

        Args:
            geometry: CadQuery geometry to display
            immediate: If True, update immediately. Otherwise, debounce.
            auto_fit: If True, fit view to model. Default False to preserve camera.
        """
        if immediate:
            self.viewer.set_geometry(geometry, auto_fit=auto_fit)
        else:
            # Debounced update would go here
            # For now, just update immediately
            self.viewer.set_geometry(geometry, auto_fit=auto_fit)

    def update_preview_separate(self, base_geometry, text_geometry, immediate: bool = False, auto_fit: bool = False):
        """
        Update the preview with separate base and text geometries (different colors).

        Args:
            base_geometry: CadQuery geometry for base plate
            text_geometry: CadQuery geometry for text
            immediate: If True, update immediately. Otherwise, debounce.
            auto_fit: If True, fit view to model. Default False to preserve camera.
        """
        if immediate:
            self.viewer.set_geometries(base_geometry, text_geometry, auto_fit=auto_fit)
        else:
            # For now, just update immediately
            self.viewer.set_geometries(base_geometry, text_geometry, auto_fit=auto_fit)

    def clear_preview(self):
        """Clear the preview."""
        self.viewer.clear_geometry()

    # --- SVG Overlay Methods for Real-Time Preview ---

    def add_svg_overlay(self, svg_id: str, geometry, color=None):
        """Add an SVG overlay for real-time preview during drag."""
        self.viewer.add_svg_overlay(svg_id, geometry, color)

    def update_svg_transform(self, svg_id: str, x: float, y: float, z: float, rotation: float = 0):
        """Update SVG overlay position/rotation instantly without geometry rebuild."""
        self.viewer.update_svg_overlay_transform(svg_id, x, y, z, rotation)

    def remove_svg_overlay(self, svg_id: str):
        """Remove an SVG overlay."""
        self.viewer.remove_svg_overlay(svg_id)

    def clear_svg_overlays(self):
        """Clear all SVG overlays."""
        self.viewer.clear_svg_overlays()

    def has_svg_overlay(self, svg_id: str) -> bool:
        """Check if an SVG overlay exists."""
        return self.viewer.has_svg_overlay(svg_id)
