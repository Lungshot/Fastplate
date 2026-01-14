"""
State Manager
Provides undo/redo functionality for the nameplate generator.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from copy import deepcopy
import json


@dataclass
class StateSnapshot:
    """Represents a saved state snapshot."""
    data: Dict[str, Any]
    description: str = ""
    timestamp: float = 0.0


class UndoRedoManager:
    """
    Manages undo/redo state history.

    Uses a stack-based approach with configurable max history size.
    """

    def __init__(self, max_history: int = 50):
        """
        Initialize the undo/redo manager.

        Args:
            max_history: Maximum number of states to keep in history
        """
        self._undo_stack: List[StateSnapshot] = []
        self._redo_stack: List[StateSnapshot] = []
        self._max_history = max_history
        self._current_state: Optional[StateSnapshot] = None
        self._on_change_callbacks: List[Callable[[], None]] = []
        self._is_restoring = False  # Flag to prevent recording during restore

    def save_state(self, state: Dict[str, Any], description: str = "") -> None:
        """
        Save current state to history.

        Args:
            state: The state dictionary to save
            description: Optional description of what changed
        """
        if self._is_restoring:
            return

        import time

        # Create snapshot with deep copy to prevent mutations
        snapshot = StateSnapshot(
            data=deepcopy(state),
            description=description,
            timestamp=time.time()
        )

        # Push current state to undo stack if exists
        if self._current_state is not None:
            self._undo_stack.append(self._current_state)

            # Trim undo stack if exceeds max
            while len(self._undo_stack) > self._max_history:
                self._undo_stack.pop(0)

        # Clear redo stack when new state is saved
        self._redo_stack.clear()

        # Set current state
        self._current_state = snapshot

        self._notify_change()

    def undo(self) -> Optional[Dict[str, Any]]:
        """
        Undo the last change.

        Returns:
            The previous state, or None if nothing to undo
        """
        if not self.can_undo():
            return None

        # Push current state to redo stack
        if self._current_state is not None:
            self._redo_stack.append(self._current_state)

        # Pop from undo stack
        self._current_state = self._undo_stack.pop()

        self._notify_change()

        return deepcopy(self._current_state.data)

    def redo(self) -> Optional[Dict[str, Any]]:
        """
        Redo the last undone change.

        Returns:
            The next state, or None if nothing to redo
        """
        if not self.can_redo():
            return None

        # Push current state to undo stack
        if self._current_state is not None:
            self._undo_stack.append(self._current_state)

        # Pop from redo stack
        self._current_state = self._redo_stack.pop()

        self._notify_change()

        return deepcopy(self._current_state.data)

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self._redo_stack) > 0

    def get_undo_description(self) -> str:
        """Get description of the state that would be restored by undo."""
        if self._undo_stack:
            return self._undo_stack[-1].description
        return ""

    def get_redo_description(self) -> str:
        """Get description of the state that would be restored by redo."""
        if self._redo_stack:
            return self._redo_stack[-1].description
        return ""

    def get_current_state(self) -> Optional[Dict[str, Any]]:
        """Get the current state."""
        if self._current_state is not None:
            return deepcopy(self._current_state.data)
        return None

    def clear(self) -> None:
        """Clear all history."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._current_state = None
        self._notify_change()

    def get_history_size(self) -> int:
        """Get total history size (undo + redo stacks)."""
        return len(self._undo_stack) + len(self._redo_stack)

    def set_restoring(self, restoring: bool) -> None:
        """Set the restoring flag to prevent recording during restore."""
        self._is_restoring = restoring

    def add_change_callback(self, callback: Callable[[], None]) -> None:
        """Add a callback to be called when undo/redo state changes."""
        self._on_change_callbacks.append(callback)

    def remove_change_callback(self, callback: Callable[[], None]) -> None:
        """Remove a change callback."""
        if callback in self._on_change_callbacks:
            self._on_change_callbacks.remove(callback)

    def _notify_change(self) -> None:
        """Notify all callbacks that undo/redo state changed."""
        for callback in self._on_change_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Error in undo/redo callback: {e}")


class ConfigStateAdapter:
    """
    Adapter to convert between UI config and serializable state.
    Handles extracting and restoring configuration from UI panels.
    """

    @staticmethod
    def extract_state(main_window) -> Dict[str, Any]:
        """
        Extract current state from main window panels.

        Args:
            main_window: The main application window

        Returns:
            Dictionary containing all configuration state
        """
        state = {}

        # Extract from each panel if available
        if hasattr(main_window, '_base_panel'):
            state['base'] = main_window._base_panel.get_config()

        if hasattr(main_window, '_text_panel'):
            state['text'] = main_window._text_panel.get_config()

        if hasattr(main_window, '_mount_panel'):
            state['mount'] = main_window._mount_panel.get_config()

        if hasattr(main_window, '_effects_panel'):
            state['effects'] = main_window._effects_panel.get_config()

        return state

    @staticmethod
    def restore_state(main_window, state: Dict[str, Any]) -> None:
        """
        Restore state to main window panels.

        Args:
            main_window: The main application window
            state: Dictionary containing configuration state
        """
        # Restore to each panel if available
        if 'base' in state and hasattr(main_window, '_base_panel'):
            main_window._base_panel.set_config(state['base'])

        if 'text' in state and hasattr(main_window, '_text_panel'):
            main_window._text_panel.set_config(state['text'])

        if 'mount' in state and hasattr(main_window, '_mount_panel'):
            main_window._mount_panel.set_config(state['mount'])

        if 'effects' in state and hasattr(main_window, '_effects_panel'):
            main_window._effects_panel.set_config(state['effects'])
