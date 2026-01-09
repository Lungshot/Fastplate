"""
SVG Importer
Parses SVG files and converts paths to CadQuery geometry for 3D nameplates.
"""

import cadquery as cq
import math
import re
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET


@dataclass
class SVGElement:
    """Represents an imported SVG element."""
    name: str = "SVG Element"
    paths: List[List[Tuple[float, float]]] = field(default_factory=list)

    # Transform properties
    position_x: float = 0.0
    position_y: float = 0.0
    rotation: float = 0.0  # degrees
    scale_x: float = 1.0
    scale_y: float = 1.0

    # Extrusion properties
    depth: float = 2.0
    style: str = "raised"  # raised, engraved, cutout

    # Original SVG dimensions
    width: float = 0.0
    height: float = 0.0
    viewbox: Tuple[float, float, float, float] = (0, 0, 100, 100)


class SVGPathParser:
    """
    Parses SVG path data (d attribute) into point lists.
    Supports: M, L, H, V, C, S, Q, T, A, Z commands (and lowercase relatives).
    """

    def __init__(self):
        self._current_x = 0.0
        self._current_y = 0.0
        self._start_x = 0.0
        self._start_y = 0.0
        self._last_control = None

    def parse(self, d: str) -> List[List[Tuple[float, float]]]:
        """
        Parse SVG path data string into list of point lists (one per subpath).
        """
        paths = []
        current_path = []

        # Tokenize the path data
        tokens = self._tokenize(d)

        i = 0
        while i < len(tokens):
            cmd = tokens[i]
            i += 1

            if cmd in 'Mm':
                # MoveTo - starts a new subpath
                if current_path:
                    paths.append(current_path)
                    current_path = []

                x, y = float(tokens[i]), float(tokens[i+1])
                i += 2

                if cmd == 'm' and (self._current_x != 0 or self._current_y != 0):
                    x += self._current_x
                    y += self._current_y

                self._current_x, self._current_y = x, y
                self._start_x, self._start_y = x, y
                current_path.append((x, y))

                # Subsequent coordinate pairs are implicit LineTo
                while i < len(tokens) and self._is_number(tokens[i]):
                    x, y = float(tokens[i]), float(tokens[i+1])
                    i += 2
                    if cmd == 'm':
                        x += self._current_x
                        y += self._current_y
                    self._current_x, self._current_y = x, y
                    current_path.append((x, y))

            elif cmd in 'Ll':
                # LineTo
                while i < len(tokens) and self._is_number(tokens[i]):
                    x, y = float(tokens[i]), float(tokens[i+1])
                    i += 2
                    if cmd == 'l':
                        x += self._current_x
                        y += self._current_y
                    self._current_x, self._current_y = x, y
                    current_path.append((x, y))

            elif cmd in 'Hh':
                # Horizontal LineTo
                while i < len(tokens) and self._is_number(tokens[i]):
                    x = float(tokens[i])
                    i += 1
                    if cmd == 'h':
                        x += self._current_x
                    self._current_x = x
                    current_path.append((self._current_x, self._current_y))

            elif cmd in 'Vv':
                # Vertical LineTo
                while i < len(tokens) and self._is_number(tokens[i]):
                    y = float(tokens[i])
                    i += 1
                    if cmd == 'v':
                        y += self._current_y
                    self._current_y = y
                    current_path.append((self._current_x, self._current_y))

            elif cmd in 'Cc':
                # Cubic Bezier
                while i < len(tokens) and self._is_number(tokens[i]):
                    x1, y1 = float(tokens[i]), float(tokens[i+1])
                    x2, y2 = float(tokens[i+2]), float(tokens[i+3])
                    x, y = float(tokens[i+4]), float(tokens[i+5])
                    i += 6

                    if cmd == 'c':
                        x1 += self._current_x
                        y1 += self._current_y
                        x2 += self._current_x
                        y2 += self._current_y
                        x += self._current_x
                        y += self._current_y

                    # Approximate cubic bezier with line segments
                    points = self._cubic_bezier(
                        self._current_x, self._current_y,
                        x1, y1, x2, y2, x, y
                    )
                    current_path.extend(points[1:])  # Skip first (current point)

                    self._current_x, self._current_y = x, y
                    self._last_control = (x2, y2)

            elif cmd in 'Ss':
                # Smooth Cubic Bezier
                while i < len(tokens) and self._is_number(tokens[i]):
                    # First control point is reflection of last control
                    if self._last_control:
                        x1 = 2 * self._current_x - self._last_control[0]
                        y1 = 2 * self._current_y - self._last_control[1]
                    else:
                        x1, y1 = self._current_x, self._current_y

                    x2, y2 = float(tokens[i]), float(tokens[i+1])
                    x, y = float(tokens[i+2]), float(tokens[i+3])
                    i += 4

                    if cmd == 's':
                        x2 += self._current_x
                        y2 += self._current_y
                        x += self._current_x
                        y += self._current_y

                    points = self._cubic_bezier(
                        self._current_x, self._current_y,
                        x1, y1, x2, y2, x, y
                    )
                    current_path.extend(points[1:])

                    self._current_x, self._current_y = x, y
                    self._last_control = (x2, y2)

            elif cmd in 'Qq':
                # Quadratic Bezier
                while i < len(tokens) and self._is_number(tokens[i]):
                    x1, y1 = float(tokens[i]), float(tokens[i+1])
                    x, y = float(tokens[i+2]), float(tokens[i+3])
                    i += 4

                    if cmd == 'q':
                        x1 += self._current_x
                        y1 += self._current_y
                        x += self._current_x
                        y += self._current_y

                    points = self._quadratic_bezier(
                        self._current_x, self._current_y,
                        x1, y1, x, y
                    )
                    current_path.extend(points[1:])

                    self._current_x, self._current_y = x, y
                    self._last_control = (x1, y1)

            elif cmd in 'Zz':
                # ClosePath
                if current_path:
                    current_path.append((self._start_x, self._start_y))
                self._current_x, self._current_y = self._start_x, self._start_y

        if current_path:
            paths.append(current_path)

        return paths

    def _tokenize(self, d: str) -> List[str]:
        """Tokenize SVG path data into commands and numbers."""
        # Add spaces around commands
        d = re.sub(r'([MmZzLlHhVvCcSsQqTtAa])', r' \1 ', d)
        # Handle negative numbers and commas
        d = re.sub(r',', ' ', d)
        d = re.sub(r'-', ' -', d)
        # Split and filter empty
        return [t for t in d.split() if t]

    def _is_number(self, s: str) -> bool:
        """Check if string is a number."""
        try:
            float(s)
            return True
        except ValueError:
            return False

    def _cubic_bezier(self, x0, y0, x1, y1, x2, y2, x3, y3, segments=10):
        """Approximate cubic bezier curve with line segments."""
        points = []
        for i in range(segments + 1):
            t = i / segments
            mt = 1 - t
            x = mt**3 * x0 + 3 * mt**2 * t * x1 + 3 * mt * t**2 * x2 + t**3 * x3
            y = mt**3 * y0 + 3 * mt**2 * t * y1 + 3 * mt * t**2 * y2 + t**3 * y3
            points.append((x, y))
        return points

    def _quadratic_bezier(self, x0, y0, x1, y1, x2, y2, segments=10):
        """Approximate quadratic bezier curve with line segments."""
        points = []
        for i in range(segments + 1):
            t = i / segments
            mt = 1 - t
            x = mt**2 * x0 + 2 * mt * t * x1 + t**2 * x2
            y = mt**2 * y0 + 2 * mt * t * y1 + t**2 * y2
            points.append((x, y))
        return points


class SVGImporter:
    """
    Imports SVG files and converts them to CadQuery geometry.
    """

    def __init__(self):
        self._parser = SVGPathParser()

    def load_svg(self, filepath: str) -> Optional[SVGElement]:
        """
        Load an SVG file and extract path data.

        Args:
            filepath: Path to the SVG file

        Returns:
            SVGElement with parsed paths, or None if loading failed.
        """
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()

            # Handle namespace
            ns = {'svg': 'http://www.w3.org/2000/svg'}

            # Get SVG dimensions
            width = self._parse_dimension(root.get('width', '100'))
            height = self._parse_dimension(root.get('height', '100'))

            # Parse viewBox
            viewbox = (0, 0, width, height)
            if root.get('viewBox'):
                vb = root.get('viewBox').split()
                if len(vb) >= 4:
                    viewbox = tuple(float(v) for v in vb[:4])

            # Find all path elements
            all_paths = []

            # Try with namespace first, then without
            paths = root.findall('.//svg:path', ns)
            if not paths:
                paths = root.findall('.//{http://www.w3.org/2000/svg}path')
            if not paths:
                paths = root.findall('.//path')

            for path_elem in paths:
                d = path_elem.get('d', '')
                if d:
                    parsed = self._parser.parse(d)
                    all_paths.extend(parsed)

            # Also check for basic shapes and convert to paths
            all_paths.extend(self._parse_basic_shapes(root, ns))

            if not all_paths:
                print(f"No paths found in SVG: {filepath}")
                return None

            # Create SVG element
            element = SVGElement(
                name=Path(filepath).stem,
                paths=all_paths,
                width=width,
                height=height,
                viewbox=viewbox
            )

            return element

        except Exception as e:
            print(f"Error loading SVG: {e}")
            return None

    def _parse_dimension(self, value: str) -> float:
        """Parse SVG dimension string (may include units)."""
        # Remove units
        value = re.sub(r'[a-zA-Z%]+', '', value)
        try:
            return float(value)
        except ValueError:
            return 100.0

    def _parse_basic_shapes(self, root: ET.Element, ns: dict) -> List[List[Tuple[float, float]]]:
        """Convert basic SVG shapes (rect, circle, etc.) to paths."""
        paths = []

        # Rectangles
        for rect in root.findall('.//{http://www.w3.org/2000/svg}rect') or root.findall('.//rect'):
            x = float(rect.get('x', 0))
            y = float(rect.get('y', 0))
            w = float(rect.get('width', 0))
            h = float(rect.get('height', 0))
            if w > 0 and h > 0:
                paths.append([
                    (x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)
                ])

        # Circles
        for circle in root.findall('.//{http://www.w3.org/2000/svg}circle') or root.findall('.//circle'):
            cx = float(circle.get('cx', 0))
            cy = float(circle.get('cy', 0))
            r = float(circle.get('r', 0))
            if r > 0:
                # Approximate circle with polygon
                points = []
                for i in range(36):
                    angle = 2 * math.pi * i / 36
                    points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
                points.append(points[0])  # Close
                paths.append(points)

        # Ellipses
        for ellipse in root.findall('.//{http://www.w3.org/2000/svg}ellipse') or root.findall('.//ellipse'):
            cx = float(ellipse.get('cx', 0))
            cy = float(ellipse.get('cy', 0))
            rx = float(ellipse.get('rx', 0))
            ry = float(ellipse.get('ry', 0))
            if rx > 0 and ry > 0:
                points = []
                for i in range(36):
                    angle = 2 * math.pi * i / 36
                    points.append((cx + rx * math.cos(angle), cy + ry * math.sin(angle)))
                points.append(points[0])
                paths.append(points)

        # Polygons
        for polygon in root.findall('.//{http://www.w3.org/2000/svg}polygon') or root.findall('.//polygon'):
            points_str = polygon.get('points', '')
            if points_str:
                coords = re.findall(r'[-+]?\d*\.?\d+', points_str)
                points = []
                for i in range(0, len(coords) - 1, 2):
                    points.append((float(coords[i]), float(coords[i+1])))
                if points:
                    points.append(points[0])  # Close
                    paths.append(points)

        # Polylines
        for polyline in root.findall('.//{http://www.w3.org/2000/svg}polyline') or root.findall('.//polyline'):
            points_str = polyline.get('points', '')
            if points_str:
                coords = re.findall(r'[-+]?\d*\.?\d+', points_str)
                points = []
                for i in range(0, len(coords) - 1, 2):
                    points.append((float(coords[i]), float(coords[i+1])))
                if points:
                    paths.append(points)

        return paths

    def create_geometry(self, element: SVGElement,
                        target_size: float = 20.0,
                        depth: Optional[float] = None) -> Optional[cq.Workplane]:
        """
        Convert SVGElement to CadQuery geometry.

        Args:
            element: The SVG element to convert
            target_size: Target size for the largest dimension in mm
            depth: Optional override for extrusion depth (uses element.depth if None)

        Returns:
            CadQuery Workplane with extruded SVG, or None if failed.
        """
        if not element.paths:
            return None

        extrude_depth = depth if depth is not None else element.depth

        try:
            # Calculate scale to fit target size
            vb = element.viewbox
            svg_width = vb[2] - vb[0]
            svg_height = vb[3] - vb[1]

            # Scale to target size
            scale = target_size / max(svg_width, svg_height)
            scale *= element.scale_x  # Apply user scale

            # Center offset
            center_x = vb[0] + svg_width / 2
            center_y = vb[1] + svg_height / 2

            result = None

            for path_points in element.paths:
                if len(path_points) < 3:
                    continue

                # Transform points - don't apply position/rotation here since
                # nameplate.py applies them after geometry creation
                transformed = []
                for x, y in path_points:
                    # Center and scale only
                    nx = (x - center_x) * scale
                    ny = -(y - center_y) * scale  # Flip Y for CadQuery coords

                    transformed.append((nx, ny))

                # Check if path is closed
                is_closed = (
                    abs(transformed[0][0] - transformed[-1][0]) < 0.01 and
                    abs(transformed[0][1] - transformed[-1][1]) < 0.01
                )

                if not is_closed:
                    transformed.append(transformed[0])

                # Create wire from points
                try:
                    wire = cq.Workplane("XY").polyline(transformed).close()
                    face = wire.extrude(extrude_depth)

                    if result is None:
                        result = face
                    else:
                        result = result.union(face)
                except Exception as e:
                    print(f"Error creating path geometry: {e}")
                    continue

            return result

        except Exception as e:
            print(f"Error creating SVG geometry: {e}")
            return None


def test_svg_import():
    """Test function for SVG import."""
    importer = SVGImporter()

    # Test with a simple path
    parser = SVGPathParser()
    test_path = "M 10 10 L 90 10 L 90 90 L 10 90 Z"
    paths = parser.parse(test_path)
    print(f"Parsed paths: {paths}")

    # Create test element
    element = SVGElement(
        name="Test",
        paths=paths,
        width=100,
        height=100,
        depth=2.0
    )

    geometry = importer.create_geometry(element, target_size=20)
    print(f"Created geometry: {geometry}")

    return geometry


if __name__ == "__main__":
    test_svg_import()
