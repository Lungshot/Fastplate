"""
Pytest configuration and fixtures for Fastplate tests.
"""

import sys
import os
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the entire test session."""
    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def main_window(qapp, qtbot):
    """Create a MainWindow instance for testing."""
    from ui.main_window import MainWindow

    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    return window


@pytest.fixture
def text_panel(qapp, qtbot):
    """Create a standalone TextPanel for testing."""
    from ui.panels.text_panel import TextPanel

    panel = TextPanel()
    qtbot.addWidget(panel)
    panel.show()
    qtbot.waitExposed(panel)
    return panel


@pytest.fixture
def base_panel(qapp, qtbot):
    """Create a standalone BasePlatePanel for testing."""
    from ui.panels.base_panel import BasePlatePanel

    panel = BasePlatePanel()
    qtbot.addWidget(panel)
    panel.show()
    qtbot.waitExposed(panel)
    return panel


@pytest.fixture
def mount_panel(qapp, qtbot):
    """Create a standalone MountPanel for testing."""
    from ui.panels.mount_panel import MountPanel

    panel = MountPanel()
    qtbot.addWidget(panel)
    panel.show()
    qtbot.waitExposed(panel)
    return panel


@pytest.fixture
def nameplate_builder():
    """Create a NameplateBuilder instance for testing."""
    from core.nameplate import NameplateBuilder

    return NameplateBuilder()


@pytest.fixture
def default_config():
    """Create a default NameplateConfig for testing."""
    from core.nameplate import NameplateConfig

    return NameplateConfig()


@pytest.fixture
def sample_fonts():
    """Get a list of sample font names that should be available."""
    return ["Arial", "Times New Roman", "Verdana"]
