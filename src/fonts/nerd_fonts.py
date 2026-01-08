"""
Nerd Fonts Manager
Provides access to 9,000+ Nerd Font icons with searchable categories.
"""

import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from functools import lru_cache

from utils.resources import get_data_path


@dataclass
class NerdFontGlyph:
    """Represents a single Nerd Font glyph/icon."""
    name: str           # e.g., "dev-python"
    char: str           # The actual character
    code: str           # Hex code e.g., "ed1b"
    category: str       # e.g., "dev", "fa", "md"
    
    @property
    def unicode_char(self) -> str:
        """Get the Unicode character from the hex code."""
        try:
            return chr(int(self.code, 16))
        except (ValueError, OverflowError):
            return self.char
    
    @property
    def display_name(self) -> str:
        """Get a human-readable display name."""
        # Remove category prefix and replace hyphens with spaces
        if '-' in self.name:
            parts = self.name.split('-', 1)
            if len(parts) > 1:
                return parts[1].replace('-', ' ').replace('_', ' ').title()
        return self.name.replace('-', ' ').replace('_', ' ').title()
    
    def __hash__(self):
        return hash(self.name)


# Category descriptions
CATEGORY_INFO = {
    'cod': ('Codicons', 'VS Code icons'),
    'custom': ('Custom', 'Custom Nerd Font glyphs'),
    'dev': ('Devicons', 'Developer/technology icons'),
    'fa': ('Font Awesome', 'Font Awesome icons'),
    'fae': ('Font Awesome Ext', 'Font Awesome Extension icons'),
    'iec': ('IEC Power', 'IEC power symbols'),
    'indent': ('Indentation', 'Indentation guides'),
    'linux': ('Linux', 'Linux distribution logos'),
    'md': ('Material Design', 'Material Design icons'),
    'oct': ('Octicons', 'GitHub Octicons'),
    'pl': ('Powerline', 'Powerline symbols'),
    'ple': ('Powerline Extra', 'Powerline Extra symbols'),
    'pom': ('Pomicons', 'Pomodoro icons'),
    'seti': ('Seti UI', 'Seti UI file icons'),
    'weather': ('Weather', 'Weather icons'),
}


class NerdFontsManager:
    """
    Manages Nerd Font glyphs and provides search/browsing functionality.
    """
    
    def __init__(self, glyphnames_path: Optional[Path] = None):
        """
        Initialize the Nerd Fonts manager.
        
        Args:
            glyphnames_path: Path to glyphnames.json. If None, looks in resources/data.
        """
        self._glyphs: Dict[str, NerdFontGlyph] = {}
        self._by_category: Dict[str, List[NerdFontGlyph]] = {}
        self._loaded = False
        
        if glyphnames_path:
            self._glyphnames_path = glyphnames_path
        else:
            # Use resource helper for bundled app compatibility
            self._glyphnames_path = get_data_path('glyphnames.json')
    
    def load(self, force_reload: bool = False) -> bool:
        """
        Load glyphs from glyphnames.json.
        
        Returns:
            True if loaded successfully, False otherwise.
        """
        if self._loaded and not force_reload:
            return True
        
        self._glyphs.clear()
        self._by_category.clear()
        
        if not self._glyphnames_path.exists():
            return False
        
        try:
            with open(self._glyphnames_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for name, info in data.items():
                # Skip metadata entries
                if name == 'METADATA' or not isinstance(info, dict):
                    continue
                
                if 'code' not in info:
                    continue
                
                # Extract category from name (e.g., "dev-python" -> "dev")
                category = name.split('-')[0] if '-' in name else 'other'
                
                glyph = NerdFontGlyph(
                    name=name,
                    char=info.get('char', ''),
                    code=info.get('code', ''),
                    category=category
                )
                
                self._glyphs[name] = glyph
                
                if category not in self._by_category:
                    self._by_category[category] = []
                self._by_category[category].append(glyph)
            
            self._loaded = True
            return True
            
        except Exception as e:
            print(f"Error loading Nerd Fonts: {e}")
            return False
    
    @property
    def is_loaded(self) -> bool:
        """Check if glyphs have been loaded."""
        return self._loaded
    
    @property
    def glyph_count(self) -> int:
        """Get total number of loaded glyphs."""
        return len(self._glyphs)
    
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
    
    def get_glyphs_by_category(self, category: str) -> List[NerdFontGlyph]:
        """Get all glyphs in a specific category."""
        if not self._loaded:
            self.load()
        
        return self._by_category.get(category, [])
    
    def get_glyph(self, name: str) -> Optional[NerdFontGlyph]:
        """Get a specific glyph by its full name."""
        if not self._loaded:
            self.load()
        
        return self._glyphs.get(name)
    
    def search(self, query: str, category: Optional[str] = None, 
               limit: int = 100) -> List[NerdFontGlyph]:
        """
        Search for glyphs matching a query.
        
        Args:
            query: Search string (searches in glyph names)
            category: Optional category to limit search
            limit: Maximum number of results
            
        Returns:
            List of matching glyphs.
        """
        if not self._loaded:
            self.load()
        
        query_lower = query.lower()
        results = []
        
        # Determine which glyphs to search
        if category:
            search_glyphs = self._by_category.get(category, [])
        else:
            search_glyphs = self._glyphs.values()
        
        for glyph in search_glyphs:
            if query_lower in glyph.name.lower():
                results.append(glyph)
                if len(results) >= limit:
                    break
        
        # Sort by relevance (exact matches first, then alphabetically)
        results.sort(key=lambda g: (
            not g.name.lower().startswith(query_lower),
            g.name.lower()
        ))
        
        return results
    
    def get_popular_glyphs(self, limit: int = 50) -> List[NerdFontGlyph]:
        """
        Get a curated list of popular/commonly used glyphs.
        """
        if not self._loaded:
            self.load()
        
        # Popular glyph names
        popular_names = [
            # Developer
            'dev-python', 'dev-javascript', 'dev-java', 'dev-rust',
            'dev-go', 'dev-react', 'dev-vue', 'dev-angular',
            'dev-docker', 'dev-git', 'dev-github_badge', 'dev-linux',
            'dev-windows8', 'dev-apple', 'dev-android',
            # Font Awesome
            'fa-user', 'fa-users', 'fa-home', 'fa-cog', 'fa-cogs',
            'fa-star', 'fa-heart', 'fa-envelope', 'fa-phone',
            'fa-briefcase', 'fa-building', 'fa-coffee', 'fa-code',
            # Codicons
            'cod-account', 'cod-home', 'cod-mail', 'cod-tools',
            'cod-gear', 'cod-terminal', 'cod-folder', 'cod-file',
            # Material Design
            'md-account', 'md-home', 'md-email', 'md-phone',
            'md-star', 'md-heart', 'md-settings', 'md-work',
        ]
        
        results = []
        for name in popular_names:
            glyph = self._glyphs.get(name)
            if glyph:
                results.append(glyph)
            if len(results) >= limit:
                break
        
        return results
    
    def get_all_glyphs(self) -> List[NerdFontGlyph]:
        """Get all loaded glyphs."""
        if not self._loaded:
            self.load()
        return list(self._glyphs.values())


# Singleton instance
_nerd_fonts_manager: Optional[NerdFontsManager] = None


def get_nerd_fonts_manager() -> NerdFontsManager:
    """Get the global Nerd Fonts manager instance."""
    global _nerd_fonts_manager
    if _nerd_fonts_manager is None:
        _nerd_fonts_manager = NerdFontsManager()
    return _nerd_fonts_manager
