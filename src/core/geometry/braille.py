"""
Braille Text Generator
Creates Grade 1 Braille text geometry for accessibility.
"""

import cadquery as cq
from dataclasses import dataclass
from typing import Optional, List, Dict
from enum import Enum


class BrailleGrade(Enum):
    """Braille grades/levels."""
    GRADE1 = "grade1"  # Letter-by-letter (uncontracted)
    # Grade 2 (contracted) would require complex rules, not implemented


@dataclass
class BrailleConfig:
    """Configuration for Braille text generation."""
    text: str = ""
    dot_diameter: float = 1.5     # mm - standard is 1.2-1.5mm
    dot_height: float = 0.5       # mm - standard is 0.5mm raised
    dot_spacing: float = 2.5      # mm - center to center within cell
    cell_spacing: float = 6.0     # mm - center of cell to center of next
    line_spacing: float = 10.0    # mm - between lines
    position_x: float = 0.0
    position_y: float = 0.0


# Braille patterns for Grade 1 (6-dot cell)
# Each character is represented as a tuple of dot positions (1-6)
# Dot positions:
#   1 4
#   2 5
#   3 6
BRAILLE_ALPHABET: Dict[str, tuple] = {
    'a': (1,),
    'b': (1, 2),
    'c': (1, 4),
    'd': (1, 4, 5),
    'e': (1, 5),
    'f': (1, 2, 4),
    'g': (1, 2, 4, 5),
    'h': (1, 2, 5),
    'i': (2, 4),
    'j': (2, 4, 5),
    'k': (1, 3),
    'l': (1, 2, 3),
    'm': (1, 3, 4),
    'n': (1, 3, 4, 5),
    'o': (1, 3, 5),
    'p': (1, 2, 3, 4),
    'q': (1, 2, 3, 4, 5),
    'r': (1, 2, 3, 5),
    's': (2, 3, 4),
    't': (2, 3, 4, 5),
    'u': (1, 3, 6),
    'v': (1, 2, 3, 6),
    'w': (2, 4, 5, 6),
    'x': (1, 3, 4, 6),
    'y': (1, 3, 4, 5, 6),
    'z': (1, 3, 5, 6),
    # Numbers use number sign (3, 4, 5, 6) followed by a-j for 1-0
    '1': (1,),  # With number prefix
    '2': (1, 2),
    '3': (1, 4),
    '4': (1, 4, 5),
    '5': (1, 5),
    '6': (1, 2, 4),
    '7': (1, 2, 4, 5),
    '8': (1, 2, 5),
    '9': (2, 4),
    '0': (2, 4, 5),
    # Punctuation
    ' ': (),  # Space - empty cell
    '.': (2, 5, 6),
    ',': (2,),
    '?': (2, 3, 6),
    '!': (2, 3, 5),
    "'": (3,),
    '-': (3, 6),
    ':': (2, 5),
    ';': (2, 3),
    # Special indicators
    '_capital': (6,),  # Capital letter indicator
    '_number': (3, 4, 5, 6),  # Number indicator
}


class BrailleGenerator:
    """
    Generates Braille text geometry.

    Follows standard Braille cell dimensions for tactile readability.
    """

    def generate(self, config: BrailleConfig,
                 plate_thickness: float = 3.0) -> Optional[cq.Workplane]:
        """
        Generate Braille text geometry.

        Args:
            config: Braille configuration
            plate_thickness: Thickness of the plate (for positioning)

        Returns:
            CadQuery Workplane with Braille dots
        """
        if not config.text:
            return None

        try:
            # Convert text to Braille cells
            cells = self._text_to_cells(config.text)
            if not cells:
                return None

            # Generate 3D geometry
            return self._create_geometry(cells, config, plate_thickness)

        except Exception as e:
            print(f"Error generating Braille: {e}")
            return None

    def _text_to_cells(self, text: str) -> List[tuple]:
        """Convert text string to Braille cell patterns."""
        cells = []
        in_number = False

        for char in text:
            lower_char = char.lower()

            # Handle spaces
            if char == ' ':
                cells.append(BRAILLE_ALPHABET.get(' ', ()))
                in_number = False
                continue

            # Handle numbers
            if char.isdigit():
                if not in_number:
                    cells.append(BRAILLE_ALPHABET.get('_number', ()))
                    in_number = True
                cells.append(BRAILLE_ALPHABET.get(char, ()))
                continue

            in_number = False

            # Handle capital letters
            if char.isupper() and lower_char in BRAILLE_ALPHABET:
                cells.append(BRAILLE_ALPHABET.get('_capital', ()))

            # Handle letters and punctuation
            if lower_char in BRAILLE_ALPHABET:
                cells.append(BRAILLE_ALPHABET.get(lower_char, ()))

        return cells

    def _create_geometry(self, cells: List[tuple], config: BrailleConfig,
                         plate_thickness: float) -> Optional[cq.Workplane]:
        """Create 3D geometry from Braille cells."""
        result = None
        dot_radius = config.dot_diameter / 2

        # Dot position offsets within a cell (relative to cell center)
        # Using standard 2x3 grid
        dot_offsets = {
            1: (-config.dot_spacing / 2, config.dot_spacing),
            2: (-config.dot_spacing / 2, 0),
            3: (-config.dot_spacing / 2, -config.dot_spacing),
            4: (config.dot_spacing / 2, config.dot_spacing),
            5: (config.dot_spacing / 2, 0),
            6: (config.dot_spacing / 2, -config.dot_spacing),
        }

        # Starting position
        start_x = config.position_x
        start_y = config.position_y

        cell_x = start_x
        for cell in cells:
            if not cell:  # Empty cell (space)
                cell_x += config.cell_spacing
                continue

            # Create dots for this cell
            for dot_num in cell:
                if dot_num in dot_offsets:
                    dx, dy = dot_offsets[dot_num]
                    x = cell_x + dx
                    y = start_y + dy

                    try:
                        # Create hemisphere for dot (more realistic than cylinder)
                        # Using cylinder for simplicity and printability
                        dot = (
                            cq.Workplane("XY")
                            .circle(dot_radius)
                            .extrude(config.dot_height)
                            .translate((x, y, plate_thickness))
                        )

                        if result is None:
                            result = dot
                        else:
                            result = result.union(dot)
                    except Exception:
                        pass

            cell_x += config.cell_spacing

        return result

    def get_text_width(self, text: str, config: BrailleConfig) -> float:
        """Calculate the width of Braille text."""
        cells = self._text_to_cells(text)
        if not cells:
            return 0
        return len(cells) * config.cell_spacing

    def get_text_height(self, config: BrailleConfig) -> float:
        """Get the height of a single line of Braille."""
        return config.dot_spacing * 2 + config.dot_diameter


def text_to_braille_preview(text: str) -> str:
    """
    Convert text to Unicode Braille for preview.

    Args:
        text: Text to convert

    Returns:
        String with Unicode Braille characters
    """
    # Unicode Braille patterns start at U+2800
    # Bits map: 1=0x01, 2=0x02, 3=0x04, 4=0x08, 5=0x10, 6=0x20

    dot_to_bit = {1: 0x01, 2: 0x02, 3: 0x04, 4: 0x08, 5: 0x10, 6: 0x20}
    result = []

    in_number = False
    for char in text:
        lower_char = char.lower()

        if char == ' ':
            result.append(' ')
            in_number = False
            continue

        if char.isdigit():
            if not in_number:
                # Number indicator
                pattern = BRAILLE_ALPHABET.get('_number', ())
                bits = sum(dot_to_bit.get(d, 0) for d in pattern)
                result.append(chr(0x2800 + bits))
                in_number = True
            pattern = BRAILLE_ALPHABET.get(char, ())
            bits = sum(dot_to_bit.get(d, 0) for d in pattern)
            result.append(chr(0x2800 + bits))
            continue

        in_number = False

        if char.isupper() and lower_char in BRAILLE_ALPHABET:
            # Capital indicator
            pattern = BRAILLE_ALPHABET.get('_capital', ())
            bits = sum(dot_to_bit.get(d, 0) for d in pattern)
            result.append(chr(0x2800 + bits))

        if lower_char in BRAILLE_ALPHABET:
            pattern = BRAILLE_ALPHABET.get(lower_char, ())
            bits = sum(dot_to_bit.get(d, 0) for d in pattern)
            result.append(chr(0x2800 + bits))

    return ''.join(result)


def get_braille_info() -> str:
    """Get information about Braille standards."""
    return """
Braille Standards (ADA Compliant):
- Dot diameter: 1.5mm (0.059")
- Dot height: 0.5mm (0.02") - raised
- Dot spacing: 2.3-2.5mm center to center
- Cell spacing: 6.0mm center to center
- Line spacing: 10mm between baselines

This generator produces Grade 1 (uncontracted) Braille,
which represents each letter individually.
"""
