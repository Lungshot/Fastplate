"""
Preset Manager
Handles loading, saving, and managing nameplate presets.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from utils.resources import get_presets_path, get_user_presets_dir


@dataclass
class Preset:
    """Represents a saved preset."""
    name: str
    filepath: Path
    data: dict
    is_builtin: bool = False
    
    def __str__(self):
        return self.name


class PresetManager:
    """
    Manages nameplate presets.
    Handles both built-in presets and user-saved presets.
    """
    
    def __init__(self):
        # Paths - use resource helpers for bundled app compatibility
        self._builtin_path = get_presets_path()
        self._user_path = get_user_presets_dir()

        print(f"PresetManager initialized:")
        print(f"  Built-in path: {self._builtin_path.resolve()}")
        print(f"  User path: {self._user_path.resolve()}")

        # Ensure user directory exists (builtin is read-only in bundled app)
        self._user_path.mkdir(parents=True, exist_ok=True)

        # Preset cache
        self._presets: Dict[str, Preset] = {}
        self._loaded = False
    
    def load_presets(self, force_reload: bool = False) -> None:
        """Load all presets from disk."""
        if self._loaded and not force_reload:
            return
        
        self._presets.clear()
        
        # Load built-in presets
        self._load_presets_from_directory(self._builtin_path, is_builtin=True)
        
        # Load user presets
        self._load_presets_from_directory(self._user_path, is_builtin=False)
        
        self._loaded = True
    
    def _load_presets_from_directory(self, directory: Path, is_builtin: bool) -> None:
        """Load all presets from a directory."""
        abs_dir = directory.resolve()
        print(f"Looking for {'builtin' if is_builtin else 'user'} presets in: {abs_dir}")
        if not directory.exists():
            print(f"  Directory does not exist: {abs_dir}")
            return

        json_files = list(directory.glob('*.json'))
        print(f"  Found {len(json_files)} JSON files: {[f.name for f in json_files]}")
        for filepath in json_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                name = data.get('name', filepath.stem)
                
                preset = Preset(
                    name=name,
                    filepath=filepath,
                    data=data,
                    is_builtin=is_builtin
                )
                
                # Use filepath stem as key to avoid name collisions
                key = f"{'builtin' if is_builtin else 'user'}_{filepath.stem}"
                self._presets[key] = preset
                
            except Exception as e:
                print(f"Error loading preset {filepath}: {e}")
    
    def get_preset_names(self) -> List[str]:
        """Get list of all preset names."""
        if not self._loaded:
            self.load_presets()
        
        return [p.name for p in self._presets.values()]
    
    def get_builtin_presets(self) -> List[Preset]:
        """Get list of built-in presets."""
        if not self._loaded:
            self.load_presets()
        
        return [p for p in self._presets.values() if p.is_builtin]
    
    def get_user_presets(self) -> List[Preset]:
        """Get list of user-saved presets."""
        if not self._loaded:
            self.load_presets()
        
        return [p for p in self._presets.values() if not p.is_builtin]
    
    def get_all_presets(self) -> List[Preset]:
        """Get all presets."""
        if not self._loaded:
            self.load_presets()
        
        return list(self._presets.values())
    
    def get_preset(self, name: str) -> Optional[Preset]:
        """Get a preset by name."""
        if not self._loaded:
            self.load_presets()
        
        for preset in self._presets.values():
            if preset.name == name:
                return preset
        
        return None
    
    def save_preset(self, name: str, data: dict) -> bool:
        """
        Save a preset to the user presets directory.
        
        Args:
            name: Name for the preset
            data: Preset configuration data
            
        Returns:
            True if saved successfully.
        """
        try:
            # Sanitize filename
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')
            
            filepath = self._user_path / f"{safe_name}.json"
            
            # Add name to data
            data['name'] = name
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            # Add to cache
            preset = Preset(
                name=name,
                filepath=filepath,
                data=data,
                is_builtin=False
            )
            self._presets[f"user_{safe_name}"] = preset
            
            return True
            
        except Exception as e:
            print(f"Error saving preset: {e}")
            return False
    
    def delete_preset(self, name: str) -> bool:
        """
        Delete a user preset.
        
        Args:
            name: Name of the preset to delete
            
        Returns:
            True if deleted successfully.
        """
        preset = self.get_preset(name)
        
        if preset is None:
            return False
        
        if preset.is_builtin:
            print("Cannot delete built-in presets")
            return False
        
        try:
            preset.filepath.unlink()
            
            # Remove from cache
            key_to_remove = None
            for key, p in self._presets.items():
                if p.name == name:
                    key_to_remove = key
                    break
            
            if key_to_remove:
                del self._presets[key_to_remove]
            
            return True
            
        except Exception as e:
            print(f"Error deleting preset: {e}")
            return False
    
    def create_default_presets(self) -> None:
        """Create the default built-in presets if they don't exist.

        Note: In bundled app, presets are read-only. This only works in dev mode.
        """
        # Don't try to write to bundled resources
        import sys
        if getattr(sys, 'frozen', False):
            return

        # Ensure builtin path exists for dev mode
        self._builtin_path.mkdir(parents=True, exist_ok=True)

        defaults = {
            'desk_nameplate': {
                'name': 'Desk Nameplate',
                'plate': {
                    'shape': 'sweeping',
                    'width': 120,
                    'height': 35,
                    'thickness': 4,
                },
                'sweeping': {
                    'curve_angle': 35,
                    'curve_radius': 90,
                    'base_type': 'pedestal',
                },
                'text': {
                    'lines': [{'content': 'Your Name', 'font_size': 14}],
                    'style': 'raised',
                    'depth': 2,
                },
                'mount': {'type': 'none'},
            },
            'door_sign': {
                'name': 'Door Sign',
                'plate': {
                    'shape': 'rounded_rectangle',
                    'width': 150,
                    'height': 50,
                    'thickness': 5,
                    'corner_radius': 8,
                },
                'text': {
                    'lines': [
                        {'content': 'Room Name', 'font_size': 16},
                        {'content': 'Room Number', 'font_size': 10}
                    ],
                    'style': 'raised',
                    'depth': 2,
                },
                'mount': {
                    'type': 'screw_holes',
                    'hole_pattern': 'two_top',
                },
            },
            'wall_plaque': {
                'name': 'Wall Plaque',
                'plate': {
                    'shape': 'rectangle',
                    'width': 180,
                    'height': 60,
                    'thickness': 6,
                },
                'text': {
                    'lines': [{'content': 'Your Text', 'font_size': 18}],
                    'style': 'raised',
                    'depth': 3,
                },
                'border': {
                    'enabled': True,
                    'style': 'raised',
                    'width': 5,
                    'height': 2,
                },
                'mount': {
                    'type': 'keyhole',
                },
            },
            'cubicle_sign': {
                'name': 'Cubicle Sign',
                'plate': {
                    'shape': 'rounded_rectangle',
                    'width': 100,
                    'height': 30,
                    'thickness': 4,
                    'corner_radius': 5,
                },
                'text': {
                    'lines': [{'content': 'Name', 'font_size': 12}],
                    'style': 'raised',
                    'depth': 1.5,
                },
                'mount': {
                    'type': 'magnet_pockets',
                    'magnet_count': 2,
                },
            },
            'keychain_tag': {
                'name': 'Keychain Tag',
                'plate': {
                    'shape': 'rounded_rectangle',
                    'width': 50,
                    'height': 20,
                    'thickness': 3,
                    'corner_radius': 3,
                },
                'text': {
                    'lines': [{'content': 'Tag', 'font_size': 8}],
                    'style': 'raised',
                    'depth': 1,
                },
                'mount': {
                    'type': 'hanging_hole',
                    'hanging_diameter': 4,
                },
            },
        }
        
        for filename, data in defaults.items():
            filepath = self._builtin_path / f"{filename}.json"
            if not filepath.exists():
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                except Exception as e:
                    print(f"Error creating default preset {filename}: {e}")


# Singleton instance
_preset_manager: Optional[PresetManager] = None


def get_preset_manager() -> PresetManager:
    """Get the global preset manager instance."""
    global _preset_manager
    if _preset_manager is None:
        _preset_manager = PresetManager()
        _preset_manager.create_default_presets()
    return _preset_manager
