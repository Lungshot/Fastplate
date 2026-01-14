"""
QR Code Generator
Creates QR code geometry for nameplates.
"""

import cadquery as cq
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class QRErrorCorrection(Enum):
    """QR code error correction levels."""
    LOW = "L"       # ~7% recovery
    MEDIUM = "M"    # ~15% recovery
    QUARTILE = "Q"  # ~25% recovery
    HIGH = "H"      # ~30% recovery


@dataclass
class QRConfig:
    """Configuration for QR code generation."""
    data: str = ""
    size: float = 20.0           # Overall size in mm
    depth: float = 1.0           # Depth/height of modules
    style: str = "raised"        # raised, engraved, cutout
    error_correction: QRErrorCorrection = QRErrorCorrection.MEDIUM
    border: int = 1              # Quiet zone border (modules)
    position_x: float = 0.0
    position_y: float = 0.0


class QRCodeGenerator:
    """
    Generates QR code geometry using a pure Python implementation.
    No external QR library required - implements QR encoding directly.
    """

    # QR Code constants
    MODE_NUMERIC = 1
    MODE_ALPHANUMERIC = 2
    MODE_BYTE = 4

    ALPHANUMERIC_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"

    # Error correction codewords per version (L, M, Q, H)
    EC_CODEWORDS = {
        1: (7, 10, 13, 17),
        2: (10, 16, 22, 28),
        3: (15, 26, 36, 44),
        4: (20, 36, 52, 64),
        5: (26, 48, 72, 88),
    }

    # Data capacity per version for byte mode (L, M, Q, H)
    CAPACITY_BYTE = {
        1: (17, 14, 11, 7),
        2: (32, 26, 20, 14),
        3: (53, 42, 32, 24),
        4: (78, 62, 46, 34),
        5: (106, 84, 60, 44),
    }

    def generate(self, config: QRConfig, plate_thickness: float = 3.0) -> Optional[cq.Workplane]:
        """
        Generate QR code geometry.

        Args:
            config: QR code configuration
            plate_thickness: Thickness of the plate (for positioning)

        Returns:
            CadQuery Workplane with QR code geometry
        """
        if not config.data:
            return None

        try:
            # Generate QR matrix
            matrix = self._generate_qr_matrix(config.data, config.error_correction)
            if not matrix:
                return None

            # Calculate module size
            modules = len(matrix)
            total_modules = modules + config.border * 2
            module_size = config.size / total_modules

            # Generate 3D geometry
            return self._create_geometry(
                matrix, module_size, config.depth, config.style,
                config.border, config.position_x, config.position_y,
                plate_thickness
            )

        except Exception as e:
            print(f"Error generating QR code: {e}")
            return None

    def _generate_qr_matrix(self, data: str, error_correction: QRErrorCorrection) -> Optional[List[List[int]]]:
        """Generate QR code matrix using simplified encoding."""
        # Determine version needed
        ec_index = {"L": 0, "M": 1, "Q": 2, "H": 3}[error_correction.value]
        version = None

        for v in range(1, 6):
            if len(data) <= self.CAPACITY_BYTE[v][ec_index]:
                version = v
                break

        if version is None:
            print("Data too long for QR code (max version 5 supported)")
            return None

        # QR code size: 21 + (version-1)*4
        size = 21 + (version - 1) * 4
        matrix = [[0] * size for _ in range(size)]

        # Add finder patterns
        self._add_finder_pattern(matrix, 0, 0)
        self._add_finder_pattern(matrix, size - 7, 0)
        self._add_finder_pattern(matrix, 0, size - 7)

        # Add timing patterns
        for i in range(8, size - 8):
            matrix[6][i] = 1 if i % 2 == 0 else 0
            matrix[i][6] = 1 if i % 2 == 0 else 0

        # Add alignment pattern for version 2+
        if version >= 2:
            pos = size - 7
            self._add_alignment_pattern(matrix, pos, pos)

        # Add format info (simplified - uses mask 0)
        self._add_format_info(matrix, size, ec_index)

        # Encode data into matrix
        self._encode_data(matrix, data, size, version, ec_index)

        return matrix

    def _add_finder_pattern(self, matrix: List[List[int]], row: int, col: int):
        """Add 7x7 finder pattern at specified position."""
        pattern = [
            [1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 1, 1, 0, 1],
            [1, 0, 1, 1, 1, 0, 1],
            [1, 0, 1, 1, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1],
        ]
        for r in range(7):
            for c in range(7):
                if 0 <= row + r < len(matrix) and 0 <= col + c < len(matrix):
                    matrix[row + r][col + c] = pattern[r][c]

        # Add separator (white border)
        for i in range(8):
            if row + 7 < len(matrix) and 0 <= col + i < len(matrix):
                matrix[row + 7][col + i] = 0
            if 0 <= row + i < len(matrix) and col + 7 < len(matrix):
                matrix[row + i][col + 7] = 0

    def _add_alignment_pattern(self, matrix: List[List[int]], row: int, col: int):
        """Add 5x5 alignment pattern at specified center position."""
        pattern = [
            [1, 1, 1, 1, 1],
            [1, 0, 0, 0, 1],
            [1, 0, 1, 0, 1],
            [1, 0, 0, 0, 1],
            [1, 1, 1, 1, 1],
        ]
        for r in range(-2, 3):
            for c in range(-2, 3):
                if 0 <= row + r < len(matrix) and 0 <= col + c < len(matrix):
                    matrix[row + r][col + c] = pattern[r + 2][c + 2]

    def _add_format_info(self, matrix: List[List[int]], size: int, ec_level: int):
        """Add format information around finder patterns."""
        # Simplified format info - just mark the areas
        # Real implementation would encode EC level and mask pattern
        format_bits = [1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0]

        # Around top-left finder
        for i in range(6):
            matrix[8][i] = format_bits[i]
        matrix[8][7] = format_bits[6]
        matrix[8][8] = format_bits[7]
        matrix[7][8] = format_bits[8]
        for i in range(6):
            matrix[5 - i][8] = format_bits[9 + i]

        # Around other finders
        for i in range(8):
            matrix[size - 1 - i][8] = format_bits[i]
        for i in range(7):
            matrix[8][size - 7 + i] = format_bits[8 + i]

        # Dark module
        matrix[size - 8][8] = 1

    def _encode_data(self, matrix: List[List[int]], data: str, size: int,
                     version: int, ec_level: int):
        """Encode data into the QR matrix."""
        # Convert data to binary
        bits = []

        # Mode indicator (byte mode = 0100)
        bits.extend([0, 1, 0, 0])

        # Character count (8 bits for version 1-9 byte mode)
        count = len(data)
        for i in range(7, -1, -1):
            bits.append((count >> i) & 1)

        # Data
        for char in data:
            byte = ord(char)
            for i in range(7, -1, -1):
                bits.append((byte >> i) & 1)

        # Terminator
        bits.extend([0, 0, 0, 0])

        # Pad to byte boundary
        while len(bits) % 8 != 0:
            bits.append(0)

        # Add padding codewords
        total_codewords = (size * size - 225) // 8  # Approximate
        pad_patterns = [[1, 1, 1, 0, 1, 1, 0, 0], [0, 0, 0, 1, 0, 0, 0, 1]]
        pad_idx = 0
        while len(bits) < total_codewords * 8:
            bits.extend(pad_patterns[pad_idx % 2])
            pad_idx += 1

        # Place bits in matrix (simplified placement)
        bit_idx = 0
        col = size - 1
        going_up = True

        while col > 0:
            if col == 6:
                col -= 1
                continue

            for row in (range(size - 1, -1, -1) if going_up else range(size)):
                for c in [col, col - 1]:
                    if self._is_data_area(row, c, size):
                        if bit_idx < len(bits):
                            # Apply mask (mask 0: (row + col) % 2 == 0)
                            val = bits[bit_idx]
                            if (row + c) % 2 == 0:
                                val = 1 - val
                            matrix[row][c] = val
                            bit_idx += 1

            col -= 2
            going_up = not going_up

    def _is_data_area(self, row: int, col: int, size: int) -> bool:
        """Check if position is available for data."""
        # Finder patterns and separators
        if row < 9 and col < 9:
            return False
        if row < 9 and col >= size - 8:
            return False
        if row >= size - 8 and col < 9:
            return False

        # Timing patterns
        if row == 6 or col == 6:
            return False

        # Format info
        if row == 8 or col == 8:
            if row < 9 or col < 9 or row >= size - 8 or col >= size - 8:
                return False

        return True

    def _create_geometry(self, matrix: List[List[int]], module_size: float,
                         depth: float, style: str, border: int,
                         pos_x: float, pos_y: float,
                         plate_thickness: float) -> Optional[cq.Workplane]:
        """Create 3D geometry from QR matrix."""
        modules = len(matrix)
        result = None

        # Calculate offset to center the QR code
        total_size = (modules + border * 2) * module_size
        offset = -total_size / 2

        for row in range(modules):
            for col in range(modules):
                if matrix[row][col] == 1:
                    # Calculate position
                    x = offset + (col + border + 0.5) * module_size + pos_x
                    y = offset + (modules - row - 1 + border + 0.5) * module_size + pos_y

                    # Create module
                    module = (
                        cq.Workplane("XY")
                        .rect(module_size * 0.95, module_size * 0.95)  # Slight gap between modules
                        .extrude(depth)
                        .translate((x, y, 0))
                    )

                    if result is None:
                        result = module
                    else:
                        result = result.union(module)

        if result is None:
            return None

        # Position based on style
        if style == "raised":
            result = result.translate((0, 0, plate_thickness))
        elif style == "engraved":
            result = result.translate((0, 0, plate_thickness - depth))

        return result


def generate_qr_preview(data: str, size: int = 200) -> Optional[List[List[int]]]:
    """
    Generate a QR matrix for preview purposes.

    Args:
        data: Text to encode
        size: Not used (matrix size is determined by data)

    Returns:
        2D list of 0s and 1s representing the QR code
    """
    generator = QRCodeGenerator()
    return generator._generate_qr_matrix(data, QRErrorCorrection.MEDIUM)
