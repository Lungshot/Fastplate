"""
Theme Manager
Handles dark/light mode theming for the application.
"""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
import json
from pathlib import Path


class ThemeManager:
    """Manages application themes (dark/light mode)."""

    DARK_STYLESHEET = """
        QMainWindow, QWidget {
            background-color: #2b2b2b;
            color: #e0e0e0;
        }

        QMenuBar {
            background-color: #3c3c3c;
            color: #e0e0e0;
        }

        QMenuBar::item:selected {
            background-color: #505050;
        }

        QMenu {
            background-color: #3c3c3c;
            color: #e0e0e0;
            border: 1px solid #505050;
        }

        QMenu::item:selected {
            background-color: #505050;
        }

        QTabWidget::pane {
            border: 1px solid #505050;
            background-color: #2b2b2b;
        }

        QTabBar::tab {
            background-color: #3c3c3c;
            color: #e0e0e0;
            padding: 8px 16px;
            border: 1px solid #505050;
            border-bottom: none;
        }

        QTabBar::tab:selected {
            background-color: #2b2b2b;
            border-bottom: 1px solid #2b2b2b;
        }

        QTabBar::tab:hover {
            background-color: #454545;
        }

        QGroupBox {
            border: 1px solid #505050;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 8px;
            color: #e0e0e0;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }

        QPushButton {
            background-color: #3c3c3c;
            color: #e0e0e0;
            border: 1px solid #505050;
            border-radius: 4px;
            padding: 6px 12px;
        }

        QPushButton:hover {
            background-color: #454545;
            border-color: #606060;
        }

        QPushButton:pressed {
            background-color: #353535;
        }

        QPushButton:disabled {
            background-color: #2b2b2b;
            color: #606060;
        }

        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #1e1e1e;
            color: #e0e0e0;
            border: 1px solid #505050;
            border-radius: 4px;
            padding: 4px;
        }

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border-color: #0078d4;
        }

        QComboBox {
            background-color: #3c3c3c;
            color: #e0e0e0;
            border: 1px solid #505050;
            border-radius: 4px;
            padding: 4px 8px;
        }

        QComboBox::drop-down {
            border: none;
            width: 20px;
        }

        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid #e0e0e0;
        }

        QComboBox QAbstractItemView {
            background-color: #3c3c3c;
            color: #e0e0e0;
            selection-background-color: #0078d4;
        }

        QSpinBox, QDoubleSpinBox {
            background-color: #1e1e1e;
            color: #e0e0e0;
            border: 1px solid #505050;
            border-radius: 4px;
            padding: 4px;
        }

        QSlider::groove:horizontal {
            height: 6px;
            background-color: #505050;
            border-radius: 3px;
        }

        QSlider::handle:horizontal {
            background-color: #0078d4;
            width: 16px;
            margin: -5px 0;
            border-radius: 8px;
        }

        QSlider::handle:horizontal:hover {
            background-color: #1e90ff;
        }

        QScrollBar:vertical {
            background-color: #2b2b2b;
            width: 12px;
            border: none;
        }

        QScrollBar::handle:vertical {
            background-color: #505050;
            border-radius: 6px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #606060;
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }

        QScrollBar:horizontal {
            background-color: #2b2b2b;
            height: 12px;
            border: none;
        }

        QScrollBar::handle:horizontal {
            background-color: #505050;
            border-radius: 6px;
            min-width: 20px;
        }

        QScrollArea {
            border: none;
        }

        QLabel {
            color: #e0e0e0;
        }

        QCheckBox {
            color: #e0e0e0;
        }

        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #505050;
            border-radius: 3px;
            background-color: #1e1e1e;
        }

        QCheckBox::indicator:checked {
            background-color: #0078d4;
            border-color: #0078d4;
        }

        QStatusBar {
            background-color: #3c3c3c;
            color: #e0e0e0;
        }

        QProgressBar {
            background-color: #1e1e1e;
            border: 1px solid #505050;
            border-radius: 4px;
            text-align: center;
            color: #e0e0e0;
        }

        QProgressBar::chunk {
            background-color: #0078d4;
            border-radius: 3px;
        }

        QSplitter::handle {
            background-color: #505050;
        }

        QToolTip {
            background-color: #3c3c3c;
            color: #e0e0e0;
            border: 1px solid #505050;
            padding: 4px;
        }

        QListWidget {
            background-color: #1e1e1e;
            color: #e0e0e0;
            border: 1px solid #505050;
        }

        QListWidget::item:selected {
            background-color: #0078d4;
        }

        QListWidget::item:hover {
            background-color: #3c3c3c;
        }

        QTreeWidget, QTreeView {
            background-color: #1e1e1e;
            color: #e0e0e0;
            border: 1px solid #505050;
        }

        QHeaderView::section {
            background-color: #3c3c3c;
            color: #e0e0e0;
            border: 1px solid #505050;
            padding: 4px;
        }

        QDialog {
            background-color: #2b2b2b;
            color: #e0e0e0;
        }
    """

    LIGHT_STYLESHEET = ""  # Use system default

    def __init__(self):
        self._dark_mode = False
        self._settings_path = self._get_settings_path()
        self._load_settings()

    def _get_settings_path(self) -> Path:
        """Get path to theme settings file."""
        import sys
        if getattr(sys, 'frozen', False):
            # Running as bundled app
            app_data = Path.home() / 'AppData' / 'Roaming' / 'Fastplate'
        else:
            # Running from source
            app_data = Path(__file__).parent.parent.parent / 'user_data'

        app_data.mkdir(parents=True, exist_ok=True)
        return app_data / 'theme_settings.json'

    def _load_settings(self):
        """Load theme settings from disk."""
        try:
            if self._settings_path.exists():
                with open(self._settings_path, 'r') as f:
                    data = json.load(f)
                    self._dark_mode = data.get('dark_mode', False)
        except Exception:
            self._dark_mode = False

    def _save_settings(self):
        """Save theme settings to disk."""
        try:
            with open(self._settings_path, 'w') as f:
                json.dump({'dark_mode': self._dark_mode}, f)
        except Exception:
            pass

    @property
    def is_dark_mode(self) -> bool:
        """Check if dark mode is enabled."""
        return self._dark_mode

    def toggle_dark_mode(self):
        """Toggle between dark and light mode."""
        self._dark_mode = not self._dark_mode
        self._save_settings()
        self.apply_theme()

    def set_dark_mode(self, enabled: bool):
        """Set dark mode on or off."""
        self._dark_mode = enabled
        self._save_settings()
        self.apply_theme()

    def apply_theme(self):
        """Apply the current theme to the application."""
        app = QApplication.instance()
        if app is None:
            return

        if self._dark_mode:
            app.setStyleSheet(self.DARK_STYLESHEET)
        else:
            app.setStyleSheet(self.LIGHT_STYLESHEET)


# Singleton instance
_theme_manager = None


def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
