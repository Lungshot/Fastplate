"""
QR Code Generator
Creates QR code geometry for nameplates.
"""

import cadquery as cq
from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import Enum


class QRStyle(Enum):
    """QR code rendering styles."""
    RAISED = "raised"
    ENGRAVED = "engraved"
    CUTOUT = "cutout"


@dataclass
class QRConfig:
    """Configuration for QR code generation."""
    data: str = ""
    size: float = 20.0  # Overall size in mm
    depth: float = 1.0  # Depth for raised/engraved
    style: QRStyle = QRStyle.RAISED
    position_x: float = 0.0
    position_y: float = 0.0
    error_correction: str = "M"  # L, M, Q, H
    border: int = 1  # Quiet zone border modules


class QRCodeGenerator:
    """Generates QR code geometry."""

    def __init__(self):
        self._qr_matrix = None
        self._module_count = 0

    def generate_matrix(self, data: str, error_correction: str = "M") -> List[List[bool]]:
        """
        Generate QR code matrix from data.

        Args:
            data: The data to encode
            error_correction: Error correction level (L, M, Q, H)

        Returns:
            2D list of booleans (True = black module)
        """
        try:
            import qrcode

            ec_levels = {
                'L': qrcode.constants.ERROR_CORRECT_L,
                'M': qrcode.constants.ERROR_CORRECT_M,
                'Q': qrcode.constants.ERROR_CORRECT_Q,
                'H': qrcode.constants.ERROR_CORRECT_H,
            }

            qr = qrcode.QRCode(
                version=None,  # Auto-size
                error_correction=ec_levels.get(error_correction, qrcode.constants.ERROR_CORRECT_M),
                box_size=1,
                border=0,
            )
            qr.add_data(data)
            qr.make(fit=True)

            # Get the matrix
            matrix = qr.modules
            self._qr_matrix = matrix
            self._module_count = len(matrix)

            return matrix

        except ImportError:
            # Fallback: create a simple pattern if qrcode not installed
            return self._generate_fallback_matrix(data)

    def _generate_fallback_matrix(self, data: str) -> List[List[bool]]:
        """Generate a simple pattern when qrcode library not available."""
        # Create a deterministic pattern based on data hash
        import hashlib
        hash_bytes = hashlib.md5(data.encode()).digest()

        size = 21  # Minimum QR code size
        matrix = []

        for row in range(size):
            row_data = []
            for col in range(size):
                # Use hash to determine module state
                idx = (row * size + col) % 16
                byte_val = hash_bytes[idx]
                bit = (row + col) % 8
                is_black = bool((byte_val >> bit) & 1)
                row_data.append(is_black)
            matrix.append(row_data)

        # Add position patterns (corners)
        self._add_position_pattern(matrix, 0, 0)
        self._add_position_pattern(matrix, 0, size - 7)
        self._add_position_pattern(matrix, size - 7, 0)

        self._qr_matrix = matrix
        self._module_count = size
        return matrix

    def _add_position_pattern(self, matrix: List[List[bool]], row: int, col: int):
        """Add a position detection pattern (7x7) at the given location."""
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
                if 0 <= row + r < len(matrix) and 0 <= col + c < len(matrix[0]):
                    matrix[row + r][col + c] = bool(pattern[r][c])

    def create_geometry(self, config: QRConfig) -> Optional[cq.Workplane]:
        """
        Create 3D geometry from QR code.

        Args:
            config: QR code configuration

        Returns:
            CadQuery Workplane with QR code geometry
        """
        if not config.data:
            return None

        # Generate the matrix
        matrix = self.generate_matrix(config.data, config.error_correction)
        if not matrix:
            return None

        module_count = len(matrix) + config.border * 2
        module_size = config.size / module_count

        # Create geometry for each black module
        result = None

        for row_idx, row in enumerate(matrix):
            for col_idx, is_black in enumerate(row):
                if is_black:
                    # Calculate module position (centered)
                    x = (col_idx + config.border - module_count / 2 + 0.5) * module_size
                    y = -(row_idx + config.border - module_count / 2 + 0.5) * module_size

                    # Create module cube
                    module = (
                        cq.Workplane("XY")
                        .box(module_size * 0.95, module_size * 0.95, config.depth)
                        .translate((x + config.position_x, y + config.position_y, config.depth / 2))
                    )

                    if result is None:
                        result = module
                    else:
                        result = result.union(module)

        return result

    def get_bounding_box(self, config: QRConfig) -> Tuple[float, float, float, float]:
        """Get the bounding box of the QR code."""
        half_size = config.size / 2
        return (
            config.position_x - half_size,
            config.position_y - half_size,
            config.position_x + half_size,
            config.position_y + half_size,
        )
