"""
Preview Animator
Provides animation capabilities for 3D preview widget.
"""

from PyQt5.QtCore import QObject, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtWidgets import QWidget
from enum import Enum
from typing import Optional, Callable
import math


class AnimationType(Enum):
    """Types of preview animations."""
    NONE = "none"
    ROTATE_Y = "rotate_y"           # Continuous Y-axis rotation (turntable)
    ROTATE_X = "rotate_x"           # Continuous X-axis rotation
    TUMBLE = "tumble"               # Combined X and Y rotation
    BOUNCE = "bounce"               # Gentle up/down motion
    ROCK = "rock"                   # Side to side rocking
    ZOOM_PULSE = "zoom_pulse"       # Gentle zoom in/out
    ORBIT = "orbit"                 # Orbit around the object


class PreviewAnimator(QObject):
    """
    Controls animations for 3D preview.

    Emits rotation/zoom changes that should be applied to the view.
    """

    # Signals
    rotation_changed = pyqtSignal(float, float, float)  # x, y, z rotation
    zoom_changed = pyqtSignal(float)                     # zoom level
    animation_finished = pyqtSignal()

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)

        self._animation_type = AnimationType.NONE
        self._is_running = False

        # Current rotation state
        self._rotation_x = 0.0
        self._rotation_y = 0.0
        self._rotation_z = 0.0
        self._zoom = 1.0

        # Animation parameters
        self._speed = 1.0           # Speed multiplier
        self._tick_interval = 16    # ~60 FPS
        self._elapsed = 0           # Elapsed time in ms

        # Rotation speeds (degrees per second)
        self._y_speed = 30.0
        self._x_speed = 15.0

        # Animation limits
        self._rock_amplitude = 15.0     # Degrees
        self._bounce_amplitude = 5.0    # Units
        self._zoom_amplitude = 0.1      # Zoom factor

    def start(self, animation_type: AnimationType, speed: float = 1.0) -> None:
        """
        Start an animation.

        Args:
            animation_type: Type of animation to play
            speed: Speed multiplier (1.0 = normal)
        """
        self._animation_type = animation_type
        self._speed = speed
        self._elapsed = 0
        self._is_running = True

        if animation_type != AnimationType.NONE:
            self._timer.start(self._tick_interval)
        else:
            self._timer.stop()

    def stop(self) -> None:
        """Stop the current animation."""
        self._timer.stop()
        self._is_running = False
        self.animation_finished.emit()

    def pause(self) -> None:
        """Pause the current animation."""
        self._timer.stop()
        self._is_running = False

    def resume(self) -> None:
        """Resume a paused animation."""
        if self._animation_type != AnimationType.NONE:
            self._is_running = True
            self._timer.start(self._tick_interval)

    def is_running(self) -> bool:
        """Check if animation is currently running."""
        return self._is_running

    def get_animation_type(self) -> AnimationType:
        """Get current animation type."""
        return self._animation_type

    def set_speed(self, speed: float) -> None:
        """Set animation speed multiplier."""
        self._speed = max(0.1, min(5.0, speed))

    def set_rotation(self, x: float, y: float, z: float) -> None:
        """Set current rotation state."""
        self._rotation_x = x
        self._rotation_y = y
        self._rotation_z = z

    def set_zoom(self, zoom: float) -> None:
        """Set current zoom level."""
        self._zoom = zoom

    def get_rotation(self) -> tuple:
        """Get current rotation as (x, y, z)."""
        return (self._rotation_x, self._rotation_y, self._rotation_z)

    def get_zoom(self) -> float:
        """Get current zoom level."""
        return self._zoom

    def _on_tick(self) -> None:
        """Handle animation timer tick."""
        self._elapsed += self._tick_interval

        # Calculate time in seconds
        t = self._elapsed / 1000.0 * self._speed

        if self._animation_type == AnimationType.ROTATE_Y:
            self._animate_rotate_y(t)
        elif self._animation_type == AnimationType.ROTATE_X:
            self._animate_rotate_x(t)
        elif self._animation_type == AnimationType.TUMBLE:
            self._animate_tumble(t)
        elif self._animation_type == AnimationType.BOUNCE:
            self._animate_bounce(t)
        elif self._animation_type == AnimationType.ROCK:
            self._animate_rock(t)
        elif self._animation_type == AnimationType.ZOOM_PULSE:
            self._animate_zoom_pulse(t)
        elif self._animation_type == AnimationType.ORBIT:
            self._animate_orbit(t)

    def _animate_rotate_y(self, t: float) -> None:
        """Turntable rotation around Y axis."""
        self._rotation_y = (t * self._y_speed) % 360
        self.rotation_changed.emit(self._rotation_x, self._rotation_y, self._rotation_z)

    def _animate_rotate_x(self, t: float) -> None:
        """Rotation around X axis."""
        self._rotation_x = (t * self._x_speed) % 360
        self.rotation_changed.emit(self._rotation_x, self._rotation_y, self._rotation_z)

    def _animate_tumble(self, t: float) -> None:
        """Combined X and Y rotation."""
        self._rotation_y = (t * self._y_speed) % 360
        self._rotation_x = (t * self._x_speed * 0.5) % 360
        self.rotation_changed.emit(self._rotation_x, self._rotation_y, self._rotation_z)

    def _animate_bounce(self, t: float) -> None:
        """Gentle up/down bouncing motion."""
        # Use sine wave for smooth bounce
        offset = math.sin(t * 2) * self._bounce_amplitude
        # Emit as rotation change (viewer should interpret Z as vertical offset)
        self._rotation_z = offset
        self.rotation_changed.emit(self._rotation_x, self._rotation_y, self._rotation_z)

    def _animate_rock(self, t: float) -> None:
        """Side to side rocking motion."""
        self._rotation_z = math.sin(t * 1.5) * self._rock_amplitude
        self.rotation_changed.emit(self._rotation_x, self._rotation_y, self._rotation_z)

    def _animate_zoom_pulse(self, t: float) -> None:
        """Gentle zoom in/out pulsing."""
        self._zoom = 1.0 + math.sin(t) * self._zoom_amplitude
        self.zoom_changed.emit(self._zoom)

    def _animate_orbit(self, t: float) -> None:
        """Orbit around the object."""
        # Combine rotation with slight elevation change
        self._rotation_y = (t * self._y_speed) % 360
        self._rotation_x = 20 + math.sin(t * 0.5) * 15  # 5-35 degree range
        self.rotation_changed.emit(self._rotation_x, self._rotation_y, self._rotation_z)


class TransitionAnimator(QObject):
    """
    Provides smooth transitions between view states.
    """

    # Signals
    transition_update = pyqtSignal(float, float, float, float)  # x, y, z, zoom
    transition_finished = pyqtSignal()

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)

        self._duration = 500  # ms
        self._elapsed = 0
        self._is_running = False

        # Start state
        self._start_x = 0.0
        self._start_y = 0.0
        self._start_z = 0.0
        self._start_zoom = 1.0

        # End state
        self._end_x = 0.0
        self._end_y = 0.0
        self._end_z = 0.0
        self._end_zoom = 1.0

        self._easing = self._ease_out_cubic

    def transition_to(self, x: float, y: float, z: float, zoom: float,
                      duration: int = 500) -> None:
        """
        Start a smooth transition to new view state.

        Args:
            x, y, z: Target rotation
            zoom: Target zoom level
            duration: Transition duration in ms
        """
        # Use current values as start if known, otherwise start from 0
        self._start_x = self._end_x if self._is_running else 0
        self._start_y = self._end_y if self._is_running else 0
        self._start_z = self._end_z if self._is_running else 0
        self._start_zoom = self._end_zoom if self._is_running else 1.0

        self._end_x = x
        self._end_y = y
        self._end_z = z
        self._end_zoom = zoom

        self._duration = duration
        self._elapsed = 0
        self._is_running = True

        self._timer.start(16)

    def stop(self) -> None:
        """Stop the transition."""
        self._timer.stop()
        self._is_running = False

    def _on_tick(self) -> None:
        """Handle transition timer tick."""
        self._elapsed += 16

        if self._elapsed >= self._duration:
            self._elapsed = self._duration
            self._timer.stop()
            self._is_running = False

            # Emit final values
            self.transition_update.emit(
                self._end_x, self._end_y, self._end_z, self._end_zoom
            )
            self.transition_finished.emit()
            return

        # Calculate progress (0-1)
        progress = self._elapsed / self._duration
        eased = self._easing(progress)

        # Interpolate values
        x = self._lerp(self._start_x, self._end_x, eased)
        y = self._lerp(self._start_y, self._end_y, eased)
        z = self._lerp(self._start_z, self._end_z, eased)
        zoom = self._lerp(self._start_zoom, self._end_zoom, eased)

        self.transition_update.emit(x, y, z, zoom)

    @staticmethod
    def _lerp(start: float, end: float, t: float) -> float:
        """Linear interpolation."""
        return start + (end - start) * t

    @staticmethod
    def _ease_out_cubic(t: float) -> float:
        """Cubic ease-out function."""
        return 1 - (1 - t) ** 3


# Preset view angles
VIEW_PRESETS = {
    "Front": (0, 0, 0),
    "Back": (0, 180, 0),
    "Top": (90, 0, 0),
    "Bottom": (-90, 0, 0),
    "Left": (0, -90, 0),
    "Right": (0, 90, 0),
    "Isometric": (30, 45, 0),
    "Isometric Back": (30, 135, 0),
}


def get_view_preset(name: str) -> tuple:
    """Get a view preset by name."""
    return VIEW_PRESETS.get(name, (0, 0, 0))


def get_view_preset_names() -> list:
    """Get list of all view preset names."""
    return list(VIEW_PRESETS.keys())
