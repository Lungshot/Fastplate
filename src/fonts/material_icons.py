"""
Google Material Icons Manager
Provides access to Material Design icons with searchable categories.
Icons are fetched from the material-icons GitHub CDN.
Downloaded icons are cached locally for offline use.
"""

import json
import urllib.request
import urllib.error
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from utils.resources import get_data_path, get_user_data_dir


@dataclass
class MaterialIcon:
    """Represents a single Material Design icon."""
    name: str           # e.g., "home", "settings"
    category: str       # e.g., "action", "navigation"
    keywords: List[str] # Search keywords

    @property
    def display_name(self) -> str:
        """Get a human-readable display name."""
        return self.name.replace('_', ' ').title()


# Category descriptions
CATEGORY_INFO = {
    'action': ('Action', 'Common actions like search, settings, home'),
    'alert': ('Alert', 'Alerts and notifications'),
    'av': ('Audio/Video', 'Media controls and playback'),
    'communication': ('Communication', 'Email, chat, phone icons'),
    'content': ('Content', 'Text editing and content'),
    'device': ('Device', 'Device and hardware icons'),
    'editor': ('Editor', 'Text and document editing'),
    'file': ('File', 'File and folder operations'),
    'hardware': ('Hardware', 'Computer and device hardware'),
    'home': ('Home', 'Smart home and IoT'),
    'image': ('Image', 'Photo and image editing'),
    'maps': ('Maps', 'Location and navigation'),
    'navigation': ('Navigation', 'App navigation elements'),
    'notification': ('Notification', 'Notification icons'),
    'places': ('Places', 'Buildings and locations'),
    'social': ('Social', 'Social media and sharing'),
    'toggle': ('Toggle', 'Toggle and switch elements'),
}

# Icon style variants available
ICON_STYLES = ['baseline', 'outline', 'round', 'sharp', 'twotone']


class MaterialIconsManager:
    """
    Manages Google Material Design icons with search and download functionality.
    """

    # CDN URL template
    CDN_URL = "https://material-icons.github.io/material-icons/svg/{name}/{style}.svg"

    def __init__(self, icons_path: Optional[Path] = None):
        """
        Initialize the Material Icons manager.

        Args:
            icons_path: Path to material_icons.json. If None, looks in resources/data.
        """
        self._icons: Dict[str, MaterialIcon] = {}
        self._by_category: Dict[str, List[MaterialIcon]] = {}
        self._loaded = False
        self._svg_cache: Dict[str, str] = {}  # In-memory cache

        if icons_path:
            self._icons_path = icons_path
        else:
            self._icons_path = get_data_path('material_icons.json')

        # Set up persistent cache directory
        self._cache_dir = get_user_data_dir() / 'icon_cache' / 'material_icons'
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._load_cache_from_disk()

    def load(self, force_reload: bool = False) -> bool:
        """
        Load icons from material_icons.json.

        Returns:
            True if loaded successfully, False otherwise.
        """
        if self._loaded and not force_reload:
            return True

        self._icons.clear()
        self._by_category.clear()

        if not self._icons_path.exists():
            print(f"Material icons data not found at: {self._icons_path}")
            return False

        try:
            with open(self._icons_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for icon_data in data.get('icons', []):
                name = icon_data.get('name', '')
                if not name:
                    continue

                category = icon_data.get('category', 'other')
                keywords = icon_data.get('keywords', [])

                icon = MaterialIcon(
                    name=name,
                    category=category,
                    keywords=keywords
                )

                self._icons[name] = icon

                if category not in self._by_category:
                    self._by_category[category] = []
                self._by_category[category].append(icon)

            self._loaded = True
            return True

        except Exception as e:
            print(f"Error loading Material Icons: {e}")
            return False

    @property
    def is_loaded(self) -> bool:
        """Check if icons have been loaded."""
        return self._loaded

    @property
    def icon_count(self) -> int:
        """Get total number of loaded icons."""
        return len(self._icons)

    def get_categories(self) -> List[Tuple[str, str, int]]:
        """
        Get list of available categories.

        Returns:
            List of (category_id, display_name, count) tuples.
        """
        if not self._loaded:
            self.load()

        result = []
        for cat_id in sorted(self._by_category.keys()):
            info = CATEGORY_INFO.get(cat_id, (cat_id.title(), ''))
            result.append((cat_id, info[0], len(self._by_category[cat_id])))

        return result

    def get_icons_by_category(self, category: str) -> List[MaterialIcon]:
        """Get all icons in a specific category."""
        if not self._loaded:
            self.load()

        return self._by_category.get(category, [])

    def get_icon(self, name: str) -> Optional[MaterialIcon]:
        """Get a specific icon by its name."""
        if not self._loaded:
            self.load()

        return self._icons.get(name)

    def search(self, query: str, category: Optional[str] = None,
               limit: int = 100) -> List[MaterialIcon]:
        """
        Search for icons matching a query.

        Args:
            query: Search string (searches in icon names and keywords)
            category: Optional category to limit search
            limit: Maximum number of results

        Returns:
            List of matching icons.
        """
        if not self._loaded:
            self.load()

        query_lower = query.lower()
        results = []

        # Determine which icons to search
        if category:
            search_icons = self._by_category.get(category, [])
        else:
            search_icons = self._icons.values()

        for icon in search_icons:
            # Check name
            if query_lower in icon.name.lower():
                results.append(icon)
            # Check keywords
            elif any(query_lower in kw.lower() for kw in icon.keywords):
                results.append(icon)

            if len(results) >= limit:
                break

        # Sort by relevance (exact name matches first, then alphabetically)
        results.sort(key=lambda i: (
            not i.name.lower().startswith(query_lower),
            i.name.lower()
        ))

        return results

    def get_popular_icons(self, limit: int = 50) -> List[MaterialIcon]:
        """
        Get a curated list of popular/commonly used icons.
        """
        if not self._loaded:
            self.load()

        # Popular icon names
        popular_names = [
            # Common actions
            'home', 'settings', 'search', 'menu', 'close', 'check',
            'add', 'remove', 'edit', 'delete', 'save', 'refresh',
            # Navigation
            'arrow_back', 'arrow_forward', 'expand_more', 'expand_less',
            'chevron_left', 'chevron_right', 'more_vert', 'more_horiz',
            # Communication
            'email', 'phone', 'chat', 'message', 'notifications', 'share',
            # User & Account
            'person', 'people', 'account_circle', 'group', 'face',
            # Content
            'star', 'favorite', 'bookmark', 'label', 'flag',
            # Business
            'work', 'business', 'briefcase', 'badge', 'verified',
            # Media
            'play_arrow', 'pause', 'stop', 'volume_up', 'mic',
            # Misc
            'info', 'help', 'warning', 'error', 'done', 'schedule',
            'location_on', 'calendar_today', 'attach_file', 'link',
        ]

        results = []
        for name in popular_names:
            icon = self._icons.get(name)
            if icon:
                results.append(icon)
            if len(results) >= limit:
                break

        return results

    def download_svg(self, name: str, style: str = 'baseline') -> Optional[str]:
        """
        Download SVG content for an icon from the CDN.

        Args:
            name: Icon name (e.g., 'home', 'settings')
            style: Icon style ('baseline', 'outline', 'round', 'sharp', 'twotone')

        Returns:
            SVG content as string, or None if download failed.
        """
        if style not in ICON_STYLES:
            style = 'baseline'

        cache_key = f"{name}_{style}"

        # Check in-memory cache first
        if cache_key in self._svg_cache:
            return self._svg_cache[cache_key]

        # Check disk cache
        cache_file = self._cache_dir / f"{cache_key}.svg"
        if cache_file.exists():
            try:
                svg_content = cache_file.read_text(encoding='utf-8')
                self._svg_cache[cache_key] = svg_content
                return svg_content
            except Exception:
                pass  # Fall through to download

        # Download from CDN
        url = self.CDN_URL.format(name=name, style=style)

        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                svg_content = response.read().decode('utf-8')
                self._svg_cache[cache_key] = svg_content
                # Save to disk cache
                self._save_to_disk_cache(cache_key, svg_content)
                return svg_content
        except urllib.error.HTTPError as e:
            print(f"HTTP error downloading icon {name}: {e.code}")
            return None
        except urllib.error.URLError as e:
            print(f"URL error downloading icon {name}: {e.reason}")
            return None
        except Exception as e:
            print(f"Error downloading icon {name}: {e}")
            return None

    def _load_cache_from_disk(self):
        """Load cached SVGs from disk into memory."""
        try:
            for svg_file in self._cache_dir.glob("*.svg"):
                cache_key = svg_file.stem  # filename without extension
                try:
                    self._svg_cache[cache_key] = svg_file.read_text(encoding='utf-8')
                except Exception:
                    pass
        except Exception as e:
            print(f"Error loading Material Icons cache: {e}")

    def _save_to_disk_cache(self, cache_key: str, svg_content: str):
        """Save an SVG to the disk cache."""
        try:
            cache_file = self._cache_dir / f"{cache_key}.svg"
            cache_file.write_text(svg_content, encoding='utf-8')
        except Exception as e:
            print(f"Error saving to Material Icons cache: {e}")

    def clear_cache(self):
        """Clear all cached SVGs (both memory and disk)."""
        self._svg_cache.clear()
        try:
            for svg_file in self._cache_dir.glob("*.svg"):
                svg_file.unlink()
            print("Material Icons cache cleared")
        except Exception as e:
            print(f"Error clearing Material Icons cache: {e}")

    @property
    def cache_count(self) -> int:
        """Get the number of cached SVGs."""
        return len(self._svg_cache)

    def get_all_icons(self) -> List[MaterialIcon]:
        """Get all loaded icons."""
        if not self._loaded:
            self.load()
        return list(self._icons.values())


# Singleton instance
_material_icons_manager: Optional[MaterialIconsManager] = None


def get_material_icons_manager() -> MaterialIconsManager:
    """Get the global Material Icons manager instance."""
    global _material_icons_manager
    if _material_icons_manager is None:
        _material_icons_manager = MaterialIconsManager()
    return _material_icons_manager
