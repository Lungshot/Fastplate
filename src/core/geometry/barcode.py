"""
Barcode Generator
Creates barcode geometry for nameplates.
Supports Code 128, Code 39, and EAN-13 formats.
"""

import cadquery as cq
from dataclasses import dataclass
from typing import Optional, List, Dict
from enum import Enum


class BarcodeFormat(Enum):
    """Supported barcode formats."""
    CODE128 = "code128"
    CODE39 = "code39"
    EAN13 = "ean13"
    UPC_A = "upc_a"


@dataclass
class BarcodeConfig:
    """Configuration for barcode generation."""
    data: str = ""
    format: BarcodeFormat = BarcodeFormat.CODE128
    width: float = 40.0          # Overall width in mm
    height: float = 15.0         # Bar height in mm
    depth: float = 1.0           # Depth/height of bars
    style: str = "raised"        # raised, engraved, cutout
    show_text: bool = False      # Show human-readable text below
    position_x: float = 0.0
    position_y: float = 0.0


class BarcodeGenerator:
    """Generates barcode geometry."""

    # Code 128 encoding tables
    CODE128_PATTERNS = {
        ' ': '11011001100', '!': '11001101100', '"': '11001100110',
        '#': '10010011000', '$': '10010001100', '%': '10001001100',
        '&': '10011001000', "'": '10011000100', '(': '10001100100',
        ')': '11001001000', '*': '11001000100', '+': '11000100100',
        ',': '10110011100', '-': '10011011100', '.': '10011001110',
        '/': '10111001100', '0': '10011101100', '1': '10011100110',
        '2': '11001110010', '3': '11001011100', '4': '11001001110',
        '5': '11011100100', '6': '11001110100', '7': '11101101110',
        '8': '11101001100', '9': '11100101100', ':': '11100100110',
        ';': '11101100100', '<': '11100110100', '=': '11100110010',
        '>': '11011011000', '?': '11011000110', '@': '11000110110',
        'A': '10100011000', 'B': '10001011000', 'C': '10001000110',
        'D': '10110001000', 'E': '10001101000', 'F': '10001100010',
        'G': '11010001000', 'H': '11000101000', 'I': '11000100010',
        'J': '10110111000', 'K': '10110001110', 'L': '10001101110',
        'M': '10111011000', 'N': '10111000110', 'O': '10001110110',
        'P': '11101110110', 'Q': '11010001110', 'R': '11000101110',
        'S': '11011101000', 'T': '11011100010', 'U': '11011101110',
        'V': '11101011000', 'W': '11101000110', 'X': '11100010110',
        'Y': '11101101000', 'Z': '11101100010', '[': '11100011010',
        '\\': '11101111010', ']': '11001000010', '^': '11110001010',
        '_': '10100110000', '`': '10100001100', 'a': '10010110000',
        'b': '10010000110', 'c': '10000101100', 'd': '10000100110',
        'e': '10110010000', 'f': '10110000100', 'g': '10011010000',
        'h': '10011000010', 'i': '10000110100', 'j': '10000110010',
        'k': '11000010010', 'l': '11001010000', 'm': '11110111010',
        'n': '11000010100', 'o': '10001111010', 'p': '10100111100',
        'q': '10010111100', 'r': '10010011110', 's': '10111100100',
        't': '10011110100', 'u': '10011110010', 'v': '11110100100',
        'w': '11110010100', 'x': '11110010010', 'y': '11011011110',
        'z': '11011110110', '{': '11110110110', '|': '10101111000',
        '}': '10100011110', '~': '10001011110',
    }

    CODE128_START_B = '11010010000'
    CODE128_STOP = '1100011101011'

    # Code 39 encoding
    CODE39_PATTERNS = {
        '0': '101001101101', '1': '110100101011', '2': '101100101011',
        '3': '110110010101', '4': '101001101011', '5': '110100110101',
        '6': '101100110101', '7': '101001011011', '8': '110100101101',
        '9': '101100101101', 'A': '110101001011', 'B': '101101001011',
        'C': '110110100101', 'D': '101011001011', 'E': '110101100101',
        'F': '101101100101', 'G': '101010011011', 'H': '110101001101',
        'I': '101101001101', 'J': '101011001101', 'K': '110101010011',
        'L': '101101010011', 'M': '110110101001', 'N': '101011010011',
        'O': '110101101001', 'P': '101101101001', 'Q': '101010110011',
        'R': '110101011001', 'S': '101101011001', 'T': '101011011001',
        'U': '110010101011', 'V': '100110101011', 'W': '110011010101',
        'X': '100101101011', 'Y': '110010110101', 'Z': '100110110101',
        '-': '100101011011', '.': '110010101101', ' ': '100110101101',
        '$': '100100100101', '/': '100100101001', '+': '100101001001',
        '%': '101001001001', '*': '100101101101',
    }

    # EAN-13 encoding
    EAN_L_PATTERNS = {
        '0': '0001101', '1': '0011001', '2': '0010011', '3': '0111101',
        '4': '0100011', '5': '0110001', '6': '0101111', '7': '0111011',
        '8': '0110111', '9': '0001011',
    }
    EAN_G_PATTERNS = {
        '0': '0100111', '1': '0110011', '2': '0011011', '3': '0100001',
        '4': '0011101', '5': '0111001', '6': '0000101', '7': '0010001',
        '8': '0001001', '9': '0010111',
    }
    EAN_R_PATTERNS = {
        '0': '1110010', '1': '1100110', '2': '1101100', '3': '1000010',
        '4': '1011100', '5': '1001110', '6': '1010000', '7': '1000100',
        '8': '1001000', '9': '1110100',
    }
    EAN_PARITY = {
        '0': 'LLLLLL', '1': 'LLGLGG', '2': 'LLGGLG', '3': 'LLGGGL',
        '4': 'LGLLGG', '5': 'LGGLLG', '6': 'LGGGLL', '7': 'LGLGLG',
        '8': 'LGLGGL', '9': 'LGGLGL',
    }

    def generate(self, config: BarcodeConfig, plate_thickness: float = 3.0) -> Optional[cq.Workplane]:
        """
        Generate barcode geometry.

        Args:
            config: Barcode configuration
            plate_thickness: Thickness of the plate (for positioning)

        Returns:
            CadQuery Workplane with barcode geometry
        """
        if not config.data:
            return None

        try:
            # Generate binary pattern
            if config.format == BarcodeFormat.CODE128:
                pattern = self._encode_code128(config.data)
            elif config.format == BarcodeFormat.CODE39:
                pattern = self._encode_code39(config.data)
            elif config.format in (BarcodeFormat.EAN13, BarcodeFormat.UPC_A):
                pattern = self._encode_ean13(config.data)
            else:
                return None

            if not pattern:
                return None

            # Generate 3D geometry
            return self._create_geometry(
                pattern, config.width, config.height, config.depth,
                config.style, config.position_x, config.position_y,
                plate_thickness
            )

        except Exception as e:
            print(f"Error generating barcode: {e}")
            return None

    def _encode_code128(self, data: str) -> str:
        """Encode data as Code 128 barcode."""
        pattern = self.CODE128_START_B

        checksum = 104  # Start B value
        for i, char in enumerate(data):
            if char in self.CODE128_PATTERNS:
                pattern += self.CODE128_PATTERNS[char]
                # Calculate checksum value
                char_val = ord(char) - 32 if ord(char) >= 32 else ord(char) + 64
                checksum += char_val * (i + 1)

        # Add checksum character
        checksum = checksum % 103
        # Find checksum character (simplified)
        if checksum < 95:
            check_char = chr(checksum + 32)
        else:
            check_char = chr(checksum + 105)
        if check_char in self.CODE128_PATTERNS:
            pattern += self.CODE128_PATTERNS[check_char]

        pattern += self.CODE128_STOP
        return pattern

    def _encode_code39(self, data: str) -> str:
        """Encode data as Code 39 barcode."""
        # Code 39 requires start/stop characters (*)
        full_data = '*' + data.upper() + '*'
        pattern = ''

        for char in full_data:
            if char in self.CODE39_PATTERNS:
                pattern += self.CODE39_PATTERNS[char]
                pattern += '0'  # Inter-character gap

        return pattern[:-1]  # Remove last gap

    def _encode_ean13(self, data: str) -> str:
        """Encode data as EAN-13 barcode."""
        # Pad or truncate to 12 digits (13th is check digit)
        digits = ''.join(c for c in data if c.isdigit())
        if len(digits) < 12:
            digits = digits.zfill(12)
        elif len(digits) > 12:
            digits = digits[:12]

        # Calculate check digit
        check = self._calculate_ean_check(digits)
        digits += str(check)

        # Build pattern
        pattern = '101'  # Start guard

        # First digit determines parity pattern
        parity = self.EAN_PARITY[digits[0]]

        # Left side (digits 1-6)
        for i in range(6):
            digit = digits[i + 1]
            if parity[i] == 'L':
                pattern += self.EAN_L_PATTERNS[digit]
            else:
                pattern += self.EAN_G_PATTERNS[digit]

        pattern += '01010'  # Center guard

        # Right side (digits 7-12)
        for i in range(6):
            digit = digits[i + 7]
            pattern += self.EAN_R_PATTERNS[digit]

        pattern += '101'  # End guard

        return pattern

    def _calculate_ean_check(self, digits: str) -> int:
        """Calculate EAN-13 check digit."""
        total = 0
        for i, d in enumerate(digits[:12]):
            weight = 1 if i % 2 == 0 else 3
            total += int(d) * weight
        return (10 - (total % 10)) % 10

    def _create_geometry(self, pattern: str, width: float, height: float,
                         depth: float, style: str, pos_x: float, pos_y: float,
                         plate_thickness: float) -> Optional[cq.Workplane]:
        """Create 3D geometry from barcode pattern."""
        if not pattern:
            return None

        bar_width = width / len(pattern)
        result = None

        # Starting X position
        start_x = -width / 2 + pos_x

        i = 0
        while i < len(pattern):
            if pattern[i] == '1':
                # Count consecutive 1s
                bar_start = i
                while i < len(pattern) and pattern[i] == '1':
                    i += 1
                bar_count = i - bar_start

                # Create bar
                x = start_x + (bar_start + bar_count / 2) * bar_width
                bar = (
                    cq.Workplane("XY")
                    .rect(bar_width * bar_count, height)
                    .extrude(depth)
                    .translate((x, pos_y, 0))
                )

                if result is None:
                    result = bar
                else:
                    result = result.union(bar)
            else:
                i += 1

        if result is None:
            return None

        # Position based on style
        if style == "raised":
            result = result.translate((0, 0, plate_thickness))
        elif style == "engraved":
            result = result.translate((0, 0, plate_thickness - depth))

        return result


def get_barcode_formats() -> List[str]:
    """Get list of supported barcode format names."""
    return [f.value for f in BarcodeFormat]


def validate_barcode_data(data: str, format: BarcodeFormat) -> tuple:
    """
    Validate barcode data for a given format.

    Returns:
        (is_valid, error_message)
    """
    if not data:
        return False, "No data provided"

    if format == BarcodeFormat.CODE128:
        # Code 128 can encode all ASCII characters
        for char in data:
            if ord(char) < 32 or ord(char) > 126:
                return False, f"Invalid character: {repr(char)}"
        return True, ""

    elif format == BarcodeFormat.CODE39:
        valid_chars = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%")
        for char in data.upper():
            if char not in valid_chars:
                return False, f"Invalid character for Code 39: {char}"
        return True, ""

    elif format in (BarcodeFormat.EAN13, BarcodeFormat.UPC_A):
        digits = ''.join(c for c in data if c.isdigit())
        if len(digits) < 11:
            return False, "EAN-13 requires at least 11 digits"
        return True, ""

    return False, "Unknown format"
