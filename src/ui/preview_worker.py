"""
Preview Worker
Background thread for geometry generation to prevent UI blocking.
"""

from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker
from typing import Optional, Any, Dict, Tuple
import hashlib
import json
import time


class GeometryCache:
    """
    LRU cache for preview geometries.

    Avoids regenerating geometry when config hasn't changed.
    """

    def __init__(self, max_entries: int = 10):
        self._cache: Dict[str, Tuple[Any, Any, Any]] = {}
        self._max_entries = max_entries
        self._access_order = []

    def _config_to_key(self, config) -> str:
        """
        Create a hash key from a NameplateConfig.

        Only includes geometry-affecting properties.
        """
        try:
            # Build a dict of all geometry-affecting values
            key_parts = []

            # Text config
            if hasattr(config, 'text'):
                text = config.text
                text_data = {
                    'style': str(text.style) if hasattr(text, 'style') else '',
                    'depth': getattr(text, 'depth', 0),
                    'halign': str(getattr(text, 'halign', '')),
                    'valign': str(getattr(text, 'valign', '')),
                    'orientation': str(getattr(text, 'orientation', '')),
                    'line_spacing': getattr(text, 'line_spacing', 0),
                    'offset_x': getattr(text, 'offset_x', 0),
                    'offset_y': getattr(text, 'offset_y', 0),
                    'effect': str(getattr(text, 'effect', '')),
                    'effect_size': getattr(text, 'effect_size', 0),
                }

                # Add line content
                lines_data = []
                if hasattr(text, 'lines'):
                    for line in text.lines:
                        line_data = {'gap': getattr(line, 'segment_gap', 0)}
                        segments = []
                        if hasattr(line, 'segments'):
                            for seg in line.segments:
                                segments.append({
                                    'content': getattr(seg, 'content', ''),
                                    'font': getattr(seg, 'font_family', ''),
                                    'size': getattr(seg, 'font_size', 0),
                                    'style': getattr(seg, 'font_style', ''),
                                    'spacing': getattr(seg, 'letter_spacing', 0),
                                    'offset': getattr(seg, 'vertical_offset', 0),
                                })
                        line_data['segments'] = segments
                        lines_data.append(line_data)
                text_data['lines'] = lines_data
                key_parts.append(('text', text_data))

            # Plate config
            if hasattr(config, 'plate'):
                plate = config.plate
                plate_data = {
                    'shape': str(getattr(plate, 'shape', '')),
                    'width': getattr(plate, 'width', 0),
                    'height': getattr(plate, 'height', 0),
                    'thickness': getattr(plate, 'thickness', 0),
                    'corner_radius': getattr(plate, 'corner_radius', 0),
                }
                key_parts.append(('plate', plate_data))

            # Border config
            if hasattr(config, 'border'):
                border = config.border
                border_data = {
                    'enabled': getattr(border, 'enabled', False),
                    'style': str(getattr(border, 'style', '')),
                    'width': getattr(border, 'width', 0),
                    'height': getattr(border, 'height', 0),
                    'inset': getattr(border, 'inset', 0),
                }
                key_parts.append(('border', border_data))

            # Mount config
            if hasattr(config, 'mount'):
                mount = config.mount
                mount_data = {
                    'type': str(getattr(mount, 'mount_type', '')),
                }
                key_parts.append(('mount', mount_data))

            # SVG elements (icons, imported SVGs)
            if hasattr(config, 'svg_elements') and config.svg_elements:
                svg_list = []
                for svg_elem in config.svg_elements:
                    svg_data = {
                        'name': getattr(svg_elem, 'name', ''),
                        'style': str(getattr(svg_elem, 'style', '')),
                        'size': getattr(svg_elem, 'target_size', 0),
                        'depth': getattr(svg_elem, 'depth', 0),
                        'x': getattr(svg_elem, 'position_x', 0),
                        'y': getattr(svg_elem, 'position_y', 0),
                        'rotation': getattr(svg_elem, 'rotation', 0),
                        'paths_hash': hash(str(getattr(svg_elem, 'paths', []))),
                    }
                    svg_list.append(svg_data)
                key_parts.append(('svg_elements', svg_list))

            # QR elements
            if hasattr(config, 'qr_elements') and config.qr_elements:
                qr_list = []
                for qr_elem in config.qr_elements:
                    qr_data = {
                        'data': getattr(qr_elem, 'data', ''),
                        'size': getattr(qr_elem, 'size', 0),
                        'depth': getattr(qr_elem, 'depth', 0),
                        'style': str(getattr(qr_elem, 'style', '')),
                        'x': getattr(qr_elem, 'position_x', 0),
                        'y': getattr(qr_elem, 'position_y', 0),
                    }
                    qr_list.append(qr_data)
                key_parts.append(('qr_elements', qr_list))

            # Create deterministic JSON string
            key_str = json.dumps(key_parts, sort_keys=True, default=str)
            return hashlib.sha256(key_str.encode()).hexdigest()[:32]

        except Exception as e:
            print(f"[GeometryCache] Key generation error: {e}")
            # Return unique key on error to prevent false cache hits
            return hashlib.sha256(str(time.time()).encode()).hexdigest()[:32]

    def get(self, config) -> Optional[Tuple[Any, Any, Any]]:
        """
        Get cached geometry if available.

        Returns:
            Tuple of (combined_geometry, base_geometry, text_geometry) or None
        """
        key = self._config_to_key(config)

        if key in self._cache:
            # Move to end of access order (LRU)
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            print(f"[GeometryCache] Cache HIT for key {key[:8]}...")
            return self._cache[key]

        print(f"[GeometryCache] Cache MISS for key {key[:8]}...")
        return None

    def put(self, config, geometry, base_geom, text_geom):
        """Cache geometry for a config."""
        key = self._config_to_key(config)

        # Evict oldest entries if cache is full
        while len(self._cache) >= self._max_entries and self._access_order:
            oldest_key = self._access_order.pop(0)
            self._cache.pop(oldest_key, None)
            print(f"[GeometryCache] Evicted old entry {oldest_key[:8]}...")

        self._cache[key] = (geometry, base_geom, text_geom)
        self._access_order.append(key)
        print(f"[GeometryCache] Cached entry {key[:8]}... ({len(self._cache)} entries)")

    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()
        self._access_order.clear()
        print("[GeometryCache] Cache cleared")

    def size(self) -> int:
        """Get number of cached entries."""
        return len(self._cache)


class PreviewWorker(QThread):
    """
    Worker thread for generating nameplate geometry in the background.

    This prevents the UI from freezing during expensive CadQuery operations.
    """

    # Signals
    preview_ready = pyqtSignal(object, object, object)  # geometry, base_geom, text_geom
    preview_error = pyqtSignal(str)
    progress_update = pyqtSignal(str)  # status message
    generation_started = pyqtSignal()
    generation_finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._builder = None
        self._config = None
        self._mutex = QMutex()
        self._abort = False
        self._pending_config = None
        self._is_running = False
        self._cache = GeometryCache(max_entries=10)

    def set_builder(self, builder):
        """Set the nameplate builder instance."""
        self._builder = builder

    def request_preview(self, config):
        """
        Request a new preview generation.

        If already generating, queues the new config for when current finishes.
        This ensures we always show the most recent requested config.
        """
        with QMutexLocker(self._mutex):
            self._pending_config = config
            self._abort = False

        if not self.isRunning():
            self.start()

    def abort(self):
        """Request abort of current generation."""
        with QMutexLocker(self._mutex):
            self._abort = True

    def clear_cache(self):
        """Clear the geometry cache."""
        self._cache.clear()

    def get_cache_size(self) -> int:
        """Get current cache size."""
        return self._cache.size()

    def run(self):
        """Generate preview geometry in background thread."""
        self._is_running = True

        while True:
            # Get pending config
            with QMutexLocker(self._mutex):
                config = self._pending_config
                self._pending_config = None
                should_abort = self._abort

            if config is None or should_abort:
                break

            self.generation_started.emit()

            try:
                # Check cache first
                cached = self._cache.get(config)
                if cached is not None:
                    geometry, base_geom, text_geom = cached
                    self.progress_update.emit("Loaded from cache")

                    # Check if newer request came in
                    with QMutexLocker(self._mutex):
                        if self._pending_config is not None:
                            continue

                    self.preview_ready.emit(geometry, base_geom, text_geom)
                    self.generation_finished.emit()
                    continue

                # Generate new geometry
                self.progress_update.emit("Generating geometry...")

                if self._builder is None:
                    self.preview_error.emit("Builder not set")
                    continue

                # Build geometry
                self._builder.set_config(config)
                geometry = self._builder.build()

                # Check for abort or new request
                with QMutexLocker(self._mutex):
                    if self._abort or self._pending_config is not None:
                        self.generation_finished.emit()
                        continue

                # Get separate geometries for coloring
                base_geom = self._builder.get_base_geometry()
                text_geom = self._builder.get_text_geometry()

                # Cache the result
                self._cache.put(config, geometry, base_geom, text_geom)

                # Final check before emitting
                with QMutexLocker(self._mutex):
                    if self._pending_config is not None:
                        # Newer request waiting, skip this result
                        self.generation_finished.emit()
                        continue

                # Emit result
                self.preview_ready.emit(geometry, base_geom, text_geom)

            except Exception as e:
                self.preview_error.emit(str(e))
                import traceback
                traceback.print_exc()

            self.generation_finished.emit()

        self._is_running = False


class TessellationWorker(QThread):
    """
    Worker thread for mesh tessellation.

    Can be used to further offload tessellation from main thread.
    """

    tessellation_ready = pyqtSignal(object, object, object, object)  # base_verts, base_faces, text_verts, text_faces
    tessellation_error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._base_geometry = None
        self._text_geometry = None
        self._precision = 0.2  # Lower precision for speed
        self._mutex = QMutex()

    def set_geometries(self, base_geom, text_geom, precision: float = 0.2):
        """Set geometries to tessellate."""
        with QMutexLocker(self._mutex):
            self._base_geometry = base_geom
            self._text_geometry = text_geom
            self._precision = precision

    def run(self):
        """Perform tessellation in background."""
        try:
            import numpy as np

            with QMutexLocker(self._mutex):
                base_geom = self._base_geometry
                text_geom = self._text_geometry
                precision = self._precision

            base_verts, base_faces = None, None
            text_verts, text_faces = None, None

            # Tessellate base geometry
            if base_geom is not None:
                base_verts, base_faces = self._tessellate(base_geom, precision)

            # Tessellate text geometry
            if text_geom is not None:
                text_verts, text_faces = self._tessellate(text_geom, precision)

            self.tessellation_ready.emit(base_verts, base_faces, text_verts, text_faces)

        except Exception as e:
            self.tessellation_error.emit(str(e))

    def _tessellate(self, geometry, precision: float):
        """Convert geometry to mesh."""
        import numpy as np

        try:
            if hasattr(geometry, 'val'):
                shape = geometry.val()
            else:
                shape = geometry

            tess = shape.tessellate(precision, precision)
            vertices = np.array([(v.x, v.y, v.z) for v in tess[0]])
            faces = np.array(tess[1])

            return vertices, faces

        except Exception as e:
            print(f"Tessellation error: {e}")
            return None, None
