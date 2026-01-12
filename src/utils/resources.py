"""
Resource path helper for PyInstaller bundled applications.

When running from source, resources are in the src/resources folder.
When bundled with PyInstaller, resources are extracted to a temp folder.
"""

import sys
import os
from pathlib import Path


def get_base_path() -> Path:
    """Get the base path for the application.

    Returns the path to the application's root directory,
    whether running from source or as a bundled executable.
    """
    if getattr(sys, 'frozen', False):
        # Running as bundled executable
        return Path(sys._MEIPASS)
    else:
        # Running from source - go up from utils to src
        return Path(__file__).parent.parent


def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to a resource file.

    Args:
        relative_path: Path relative to the resources folder
                      (e.g., "data/glyphnames.json")

    Returns:
        Absolute path to the resource file
    """
    base = get_base_path()
    return base / "resources" / relative_path


def get_data_path(filename: str) -> Path:
    """Get path to a data file in resources/data/."""
    return get_resource_path(f"data/{filename}")


def get_presets_path() -> Path:
    """Get path to the built-in presets folder."""
    return get_resource_path("presets")


def get_user_data_dir() -> Path:
    """Get path to user data directory for saving presets, settings, etc."""
    if sys.platform == 'win32':
        base = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
    else:
        base = Path.home() / '.config'

    user_dir = base / 'Fastplate'
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def get_user_presets_dir() -> Path:
    """Get path to user presets directory."""
    presets_dir = get_user_data_dir() / 'presets'
    presets_dir.mkdir(parents=True, exist_ok=True)
    return presets_dir


def ensure_user_dirs():
    """Ensure all user directories exist."""
    get_user_data_dir()
    get_user_presets_dir()
