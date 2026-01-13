"""
Font Awesome Free Icons Manager
Provides access to Font Awesome free icons with searchable categories.
Icons are fetched from the Font Awesome GitHub repository.
"""

import json
import urllib.request
import urllib.error
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from utils.resources import get_data_path


@dataclass
class FontAwesomeIcon:
    """Represents a single Font Awesome icon."""
    name: str           # e.g., "house", "gear"
    style: str          # "solid", "regular", or "brands"
    category: str       # e.g., "objects", "communication"
    keywords: List[str] # Search keywords

    @property
    def display_name(self) -> str:
        """Get a human-readable display name."""
        return self.name.replace('-', ' ').title()


# Category descriptions
CATEGORY_INFO = {
    'accessibility': ('Accessibility', 'Accessibility icons'),
    'alert': ('Alert', 'Alert and warning icons'),
    'arrows': ('Arrows', 'Arrow and direction icons'),
    'audio': ('Audio/Video', 'Audio and video controls'),
    'brands': ('Brands', 'Brand and logo icons'),
    'business': ('Business', 'Business and commerce'),
    'charts': ('Charts', 'Charts and data visualization'),
    'code': ('Code', 'Coding and development'),
    'communication': ('Communication', 'Email, chat, messaging'),
    'design': ('Design', 'Design and editing tools'),
    'devices': ('Devices', 'Device and hardware'),
    'editing': ('Editing', 'Text and document editing'),
    'emoji': ('Emoji', 'Emoji and expressions'),
    'energy': ('Energy', 'Energy and environment'),
    'files': ('Files', 'Files and folders'),
    'food': ('Food', 'Food and beverage'),
    'gaming': ('Gaming', 'Games and entertainment'),
    'hands': ('Hands', 'Hand gestures'),
    'health': ('Health', 'Medical and health'),
    'holidays': ('Holidays', 'Seasonal and holiday'),
    'household': ('Household', 'Home and household'),
    'images': ('Images', 'Images and media'),
    'interfaces': ('Interfaces', 'UI elements'),
    'logistics': ('Logistics', 'Shipping and logistics'),
    'maps': ('Maps', 'Maps and navigation'),
    'math': ('Math', 'Mathematical symbols'),
    'money': ('Money', 'Currency and finance'),
    'moving': ('Moving', 'Moving and transportation'),
    'music': ('Music', 'Music and audio'),
    'nature': ('Nature', 'Nature and animals'),
    'numbers': ('Numbers', 'Numbers and counting'),
    'objects': ('Objects', 'Common objects'),
    'people': ('People', 'People and users'),
    'political': ('Political', 'Political icons'),
    'religion': ('Religion', 'Religious symbols'),
    'science': ('Science', 'Science and education'),
    'security': ('Security', 'Security and safety'),
    'shapes': ('Shapes', 'Shapes and symbols'),
    'shopping': ('Shopping', 'Shopping and commerce'),
    'social': ('Social', 'Social media'),
    'spinners': ('Spinners', 'Loading spinners'),
    'sports': ('Sports', 'Sports and activities'),
    'symbols': ('Symbols', 'Symbols and icons'),
    'text': ('Text', 'Text formatting'),
    'time': ('Time', 'Time and scheduling'),
    'toggle': ('Toggle', 'Toggle elements'),
    'transportation': ('Transportation', 'Vehicles and transport'),
    'travel': ('Travel', 'Travel and tourism'),
    'users': ('Users', 'User and account'),
    'weather': ('Weather', 'Weather icons'),
    'writing': ('Writing', 'Writing and editing'),
}

# Icon style variants available
ICON_STYLES = ['solid', 'regular', 'brands']


class FontAwesomeManager:
    """
    Manages Font Awesome free icons with search and download functionality.
    """

    # GitHub raw URL template
    CDN_URL = "https://raw.githubusercontent.com/FortAwesome/Font-Awesome/7.x/svgs/{style}/{name}.svg"

    def __init__(self, icons_path: Optional[Path] = None):
        """
        Initialize the Font Awesome manager.

        Args:
            icons_path: Path to font_awesome_icons.json. If None, looks in resources/data.
        """
        self._icons: Dict[str, FontAwesomeIcon] = {}
        self._by_category: Dict[str, List[FontAwesomeIcon]] = {}
        self._by_style: Dict[str, List[FontAwesomeIcon]] = {}
        self._loaded = False
        self._svg_cache: Dict[str, str] = {}  # Cache downloaded SVGs

        if icons_path:
            self._icons_path = icons_path
        else:
            self._icons_path = get_data_path('font_awesome_icons.json')

    def load(self, force_reload: bool = False) -> bool:
        """
        Load icons from font_awesome_icons.json.

        Returns:
            True if loaded successfully, False otherwise.
        """
        if self._loaded and not force_reload:
            return True

        self._icons.clear()
        self._by_category.clear()
        self._by_style.clear()

        if not self._icons_path.exists():
            print(f"Font Awesome icons data not found at: {self._icons_path}")
            return False

        try:
            with open(self._icons_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for icon_data in data.get('icons', []):
                name = icon_data.get('name', '')
                if not name:
                    continue

                style = icon_data.get('style', 'solid')
                category = icon_data.get('category', 'objects')
                keywords = icon_data.get('keywords', [])

                # Create unique key for icon (name + style)
                icon_key = f"{name}_{style}"

                icon = FontAwesomeIcon(
                    name=name,
                    style=style,
                    category=category,
                    keywords=keywords
                )

                self._icons[icon_key] = icon

                if category not in self._by_category:
                    self._by_category[category] = []
                self._by_category[category].append(icon)

                if style not in self._by_style:
                    self._by_style[style] = []
                self._by_style[style].append(icon)

            self._loaded = True
            return True

        except Exception as e:
            print(f"Error loading Font Awesome Icons: {e}")
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

    def get_icons_by_category(self, category: str) -> List[FontAwesomeIcon]:
        """Get all icons in a specific category."""
        if not self._loaded:
            self.load()

        return self._by_category.get(category, [])

    def get_icons_by_style(self, style: str) -> List[FontAwesomeIcon]:
        """Get all icons of a specific style."""
        if not self._loaded:
            self.load()

        return self._by_style.get(style, [])

    def get_icon(self, name: str, style: str = 'solid') -> Optional[FontAwesomeIcon]:
        """Get a specific icon by its name and style."""
        if not self._loaded:
            self.load()

        icon_key = f"{name}_{style}"
        return self._icons.get(icon_key)

    def search(self, query: str, category: Optional[str] = None,
               style: Optional[str] = None, limit: int = 100) -> List[FontAwesomeIcon]:
        """
        Search for icons matching a query.

        Args:
            query: Search string (searches in icon names and keywords)
            category: Optional category to limit search
            style: Optional style to limit search
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
        elif style:
            search_icons = self._by_style.get(style, [])
        else:
            search_icons = self._icons.values()

        for icon in search_icons:
            # Filter by style if specified
            if style and icon.style != style:
                continue

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

    def get_popular_icons(self, limit: int = 50) -> List[FontAwesomeIcon]:
        """
        Get a curated list of popular/commonly used icons.
        """
        if not self._loaded:
            self.load()

        # Popular icon names (solid style)
        popular_names = [
            # Common actions
            'house', 'gear', 'magnifying-glass', 'bars', 'xmark', 'check',
            'plus', 'minus', 'pen', 'trash', 'floppy-disk', 'rotate',
            # Navigation
            'arrow-left', 'arrow-right', 'chevron-down', 'chevron-up',
            'chevron-left', 'chevron-right', 'ellipsis-vertical', 'ellipsis',
            # Communication
            'envelope', 'phone', 'comment', 'message', 'bell', 'share-nodes',
            # User & Account
            'user', 'users', 'circle-user', 'user-group', 'face-smile',
            # Content
            'star', 'heart', 'bookmark', 'tag', 'flag',
            # Business
            'briefcase', 'building', 'suitcase', 'id-badge', 'certificate',
            # Media
            'play', 'pause', 'stop', 'volume-high', 'microphone',
            # Misc
            'circle-info', 'circle-question', 'triangle-exclamation', 'circle-xmark',
            'circle-check', 'clock', 'location-dot', 'calendar', 'paperclip', 'link',
        ]

        results = []
        for name in popular_names:
            icon = self.get_icon(name, 'solid')
            if icon:
                results.append(icon)
            if len(results) >= limit:
                break

        return results

    def download_svg(self, name: str, style: str = 'solid') -> Optional[str]:
        """
        Download SVG content for an icon from GitHub.

        Args:
            name: Icon name (e.g., 'house', 'gear')
            style: Icon style ('solid', 'regular', 'brands')

        Returns:
            SVG content as string, or None if download failed.
        """
        if style not in ICON_STYLES:
            style = 'solid'

        cache_key = f"{name}_{style}"
        if cache_key in self._svg_cache:
            return self._svg_cache[cache_key]

        url = self.CDN_URL.format(name=name, style=style)

        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                svg_content = response.read().decode('utf-8')
                self._svg_cache[cache_key] = svg_content
                return svg_content
        except urllib.error.HTTPError as e:
            print(f"HTTP error downloading Font Awesome icon {name}: {e.code}")
            return None
        except urllib.error.URLError as e:
            print(f"URL error downloading Font Awesome icon {name}: {e.reason}")
            return None
        except Exception as e:
            print(f"Error downloading Font Awesome icon {name}: {e}")
            return None

    def get_all_icons(self) -> List[FontAwesomeIcon]:
        """Get all loaded icons."""
        if not self._loaded:
            self.load()
        return list(self._icons.values())


# Singleton instance
_font_awesome_manager: Optional[FontAwesomeManager] = None


def get_font_awesome_manager() -> FontAwesomeManager:
    """Get the global Font Awesome manager instance."""
    global _font_awesome_manager
    if _font_awesome_manager is None:
        _font_awesome_manager = FontAwesomeManager()
    return _font_awesome_manager
