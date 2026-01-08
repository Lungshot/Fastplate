"""
Windows Font Manager
Enumerates and provides access to all installed Windows fonts.
"""

import os
import winreg
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from fontTools.ttLib import TTFont
from functools import lru_cache


@dataclass
class FontVariant:
    """Represents a specific variant of a font (e.g., Bold, Italic)."""
    name: str
    file_path: Path
    style: str  # Regular, Bold, Italic, Bold Italic
    weight: int  # 100-900 (400 = Regular, 700 = Bold)
    is_italic: bool = False
    
    def __hash__(self):
        return hash(self.file_path)


@dataclass 
class FontFamily:
    """Represents a font family with all its variants."""
    name: str
    variants: Dict[str, FontVariant] = field(default_factory=dict)
    
    def get_regular(self) -> Optional[FontVariant]:
        """Get the regular variant of this font."""
        for key in ['Regular', 'Normal', 'Book', 'Roman']:
            if key in self.variants:
                return self.variants[key]
        # Return first variant if no regular found
        if self.variants:
            return next(iter(self.variants.values()))
        return None
    
    def get_bold(self) -> Optional[FontVariant]:
        """Get the bold variant of this font."""
        for key in ['Bold', 'Heavy', 'Black']:
            if key in self.variants:
                return self.variants[key]
        return None
    
    def get_italic(self) -> Optional[FontVariant]:
        """Get the italic variant of this font."""
        for key in ['Italic', 'Oblique']:
            if key in self.variants:
                return self.variants[key]
        return None
    
    def get_bold_italic(self) -> Optional[FontVariant]:
        """Get the bold italic variant of this font."""
        for key in ['Bold Italic', 'BoldItalic', 'Bold Oblique']:
            if key in self.variants:
                return self.variants[key]
        return None
    
    def get_variant(self, style: str = 'Regular') -> Optional[FontVariant]:
        """Get a specific variant by style name."""
        style_lower = style.lower()
        
        if style_lower in ['regular', 'normal']:
            return self.get_regular()
        elif style_lower == 'bold':
            return self.get_bold()
        elif style_lower == 'italic':
            return self.get_italic()
        elif style_lower in ['bold italic', 'bolditalic']:
            return self.get_bold_italic()
        
        # Try direct match
        if style in self.variants:
            return self.variants[style]
        
        return self.get_regular()


class FontManager:
    """
    Manages access to Windows system fonts.
    Enumerates fonts from both system and user font directories.
    """
    
    # Windows font directories
    SYSTEM_FONT_DIR = Path(os.environ.get('WINDIR', 'C:\\Windows')) / 'Fonts'
    USER_FONT_DIR = Path(os.environ.get('LOCALAPPDATA', '')) / 'Microsoft' / 'Windows' / 'Fonts'
    
    # Registry keys for fonts
    SYSTEM_FONT_KEY = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts'
    USER_FONT_KEY = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts'
    
    def __init__(self):
        self._font_families: Dict[str, FontFamily] = {}
        self._font_paths: Dict[str, Path] = {}  # Map font name to path
        self._loaded = False
    
    def load_fonts(self, force_reload: bool = False) -> None:
        """Load all available fonts from the system."""
        if self._loaded and not force_reload:
            return
        
        self._font_families.clear()
        self._font_paths.clear()
        
        # Load from registry (most reliable)
        self._load_fonts_from_registry()
        
        # Also scan directories for any fonts not in registry
        self._scan_font_directory(self.SYSTEM_FONT_DIR)
        if self.USER_FONT_DIR.exists():
            self._scan_font_directory(self.USER_FONT_DIR)
        
        self._loaded = True
    
    def _load_fonts_from_registry(self) -> None:
        """Load font information from Windows registry."""
        # System fonts
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, self.SYSTEM_FONT_KEY) as key:
                self._enumerate_registry_fonts(key, self.SYSTEM_FONT_DIR)
        except WindowsError:
            pass
        
        # User fonts
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.USER_FONT_KEY) as key:
                self._enumerate_registry_fonts(key, self.USER_FONT_DIR)
        except WindowsError:
            pass
    
    def _enumerate_registry_fonts(self, key, default_dir: Path) -> None:
        """Enumerate fonts from a registry key."""
        try:
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    i += 1
                    
                    # Skip non-TrueType/OpenType fonts
                    if not (value.lower().endswith('.ttf') or 
                            value.lower().endswith('.otf') or
                            value.lower().endswith('.ttc')):
                        continue
                    
                    # Determine full path
                    if os.path.isabs(value):
                        font_path = Path(value)
                    else:
                        font_path = default_dir / value
                    
                    if font_path.exists():
                        self._process_font_file(font_path, name)
                        
                except WindowsError:
                    break
        except Exception:
            pass
    
    def _scan_font_directory(self, directory: Path) -> None:
        """Scan a directory for font files."""
        if not directory.exists():
            return
        
        for font_file in directory.iterdir():
            if font_file.suffix.lower() in ['.ttf', '.otf', '.ttc']:
                if font_file not in self._font_paths.values():
                    self._process_font_file(font_file)
    
    def _process_font_file(self, font_path: Path, registry_name: str = None) -> None:
        """Process a font file and add it to the font families."""
        try:
            # Handle .ttc (TrueType Collection) files
            if font_path.suffix.lower() == '.ttc':
                self._process_ttc_file(font_path)
                return
            
            font = TTFont(font_path)
            
            # Get font names from the name table
            name_table = font['name']
            
            family_name = None
            subfamily_name = 'Regular'
            full_name = None
            
            for record in name_table.names:
                # Platform 3 (Windows), Encoding 1 (Unicode BMP)
                if record.platformID == 3 and record.langID == 0x409:
                    try:
                        text = record.toUnicode()
                    except:
                        continue
                    
                    if record.nameID == 1:  # Font Family
                        family_name = text
                    elif record.nameID == 2:  # Font Subfamily
                        subfamily_name = text
                    elif record.nameID == 4:  # Full Name
                        full_name = text
            
            # Fallback to platform 1 (Mac) if needed
            if not family_name:
                for record in name_table.names:
                    if record.platformID == 1:
                        try:
                            text = record.toUnicode()
                        except:
                            continue
                        
                        if record.nameID == 1:
                            family_name = text
                        elif record.nameID == 2:
                            subfamily_name = text
            
            if not family_name:
                family_name = font_path.stem
            
            # Get weight from OS/2 table
            weight = 400
            is_italic = False
            if 'OS/2' in font:
                os2 = font['OS/2']
                weight = os2.usWeightClass
                is_italic = bool(os2.fsSelection & 0x01)
            
            font.close()
            
            # Create or update font family
            if family_name not in self._font_families:
                self._font_families[family_name] = FontFamily(name=family_name)
            
            variant = FontVariant(
                name=full_name or f"{family_name} {subfamily_name}",
                file_path=font_path,
                style=subfamily_name,
                weight=weight,
                is_italic=is_italic
            )
            
            self._font_families[family_name].variants[subfamily_name] = variant
            self._font_paths[variant.name] = font_path
            
        except Exception as e:
            # Skip fonts that can't be read
            pass
    
    def _process_ttc_file(self, font_path: Path) -> None:
        """Process a TrueType Collection file."""
        try:
            # Get number of fonts in collection
            font = TTFont(font_path, fontNumber=0)
            font.close()
            
            # Process each font in the collection
            i = 0
            while True:
                try:
                    font = TTFont(font_path, fontNumber=i)
                    name_table = font['name']
                    
                    family_name = None
                    subfamily_name = 'Regular'
                    
                    for record in name_table.names:
                        if record.platformID == 3 and record.langID == 0x409:
                            try:
                                text = record.toUnicode()
                            except:
                                continue
                            
                            if record.nameID == 1:
                                family_name = text
                            elif record.nameID == 2:
                                subfamily_name = text
                    
                    if family_name:
                        if family_name not in self._font_families:
                            self._font_families[family_name] = FontFamily(name=family_name)
                        
                        weight = 400
                        is_italic = False
                        if 'OS/2' in font:
                            os2 = font['OS/2']
                            weight = os2.usWeightClass
                            is_italic = bool(os2.fsSelection & 0x01)
                        
                        variant = FontVariant(
                            name=f"{family_name} {subfamily_name}",
                            file_path=font_path,
                            style=subfamily_name,
                            weight=weight,
                            is_italic=is_italic
                        )
                        
                        self._font_families[family_name].variants[subfamily_name] = variant
                    
                    font.close()
                    i += 1
                except:
                    break
        except:
            pass
    
    @property
    def families(self) -> Dict[str, FontFamily]:
        """Get all font families."""
        if not self._loaded:
            self.load_fonts()
        return self._font_families
    
    def get_family_names(self) -> List[str]:
        """Get sorted list of all font family names."""
        if not self._loaded:
            self.load_fonts()
        return sorted(self._font_families.keys(), key=str.lower)
    
    def get_family(self, name: str) -> Optional[FontFamily]:
        """Get a specific font family by name."""
        if not self._loaded:
            self.load_fonts()
        return self._font_families.get(name)
    
    def get_font_path(self, family_name: str, style: str = 'Regular') -> Optional[Path]:
        """Get the file path for a specific font variant."""
        family = self.get_family(family_name)
        if family:
            variant = family.get_variant(style)
            if variant:
                return variant.file_path
        return None
    
    def search_fonts(self, query: str) -> List[str]:
        """Search for fonts matching a query string."""
        if not self._loaded:
            self.load_fonts()
        
        query_lower = query.lower()
        matches = []
        
        for family_name in self._font_families:
            if query_lower in family_name.lower():
                matches.append(family_name)
        
        return sorted(matches, key=str.lower)
    
    def get_font_info(self, family_name: str) -> Optional[Dict]:
        """Get detailed information about a font family."""
        family = self.get_family(family_name)
        if not family:
            return None
        
        return {
            'name': family.name,
            'variants': list(family.variants.keys()),
            'has_bold': family.get_bold() is not None,
            'has_italic': family.get_italic() is not None,
            'has_bold_italic': family.get_bold_italic() is not None,
            'regular_path': str(family.get_regular().file_path) if family.get_regular() else None
        }


# Singleton instance
_font_manager: Optional[FontManager] = None


def get_font_manager() -> FontManager:
    """Get the global font manager instance."""
    global _font_manager
    if _font_manager is None:
        _font_manager = FontManager()
    return _font_manager
