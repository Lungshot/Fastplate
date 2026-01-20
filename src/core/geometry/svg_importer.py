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

    # Target size for scaling
    target_size: float = 20.0

    def to_dict(self) -> dict:
        """Serialize SVGElement to a dictionary."""
        return {
            'name': self.name,
            'paths': self.paths,
            'position_x': self.position_x,
            'position_y': self.position_y,
            'rotation': self.rotation,
            'scale_x': self.scale_x,
            'scale_y': self.scale_y,
            'depth': self.depth,
            'style': self.style,
            'width': self.width,
            'height': self.height,
            'viewbox': list(self.viewbox),
            'target_size': self.target_size,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SVGElement':
        """Deserialize SVGElement from a dictionary."""
        viewbox = data.get('viewbox', (0, 0, 100, 100))
        if isinstance(viewbox, list):
            viewbox = tuple(viewbox)

        elem = cls(
            name=data.get('name', 'SVG Element'),
            paths=data.get('paths', []),
            position_x=data.get('position_x', 0.0),
            position_y=data.get('position_y', 0.0),
            rotation=data.get('rotation', 0.0),
            scale_x=data.get('scale_x', 1.0),
            scale_y=data.get('scale_y', 1.0),
            depth=data.get('depth', 2.0),
            style=data.get('style', 'raised'),
            width=data.get('width', 0.0),
            height=data.get('height', 0.0),
            viewbox=viewbox,
        )
        elem.target_size = data.get('target_size', 20.0)
        return elem


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

            elif cmd in 'Tt':
                # Smooth Quadratic Bezier
                while i < len(tokens) and self._is_number(tokens[i]):
                    # Control point is reflection of last control
                    if self._last_control:
                        x1 = 2 * self._current_x - self._last_control[0]
                        y1 = 2 * self._current_y - self._last_control[1]
                    else:
                        x1, y1 = self._current_x, self._current_y

                    x, y = float(tokens[i]), float(tokens[i+1])
                    i += 2

                    if cmd == 't':
                        x += self._current_x
                        y += self._current_y

                    points = self._quadratic_bezier(
                        self._current_x, self._current_y,
                        x1, y1, x, y
                    )
                    current_path.extend(points[1:])

                    self._current_x, self._current_y = x, y
                    self._last_control = (x1, y1)

            elif cmd in 'Aa':
                # Arc - approximate with line segments
                while i < len(tokens) and self._is_number(tokens[i]):
                    rx = float(tokens[i])
                    ry = float(tokens[i+1])
                    x_rot = float(tokens[i+2])
                    large_arc = int(float(tokens[i+3]))
                    sweep = int(float(tokens[i+4]))
                    x, y = float(tokens[i+5]), float(tokens[i+6])
                    i += 7

                    if cmd == 'a':
                        x += self._current_x
                        y += self._current_y

                    # Approximate arc with line segments
                    points = self._arc_to_points(
                        self._current_x, self._current_y,
                        rx, ry, x_rot, large_arc, sweep, x, y
                    )
                    current_path.extend(points[1:])

                    self._current_x, self._current_y = x, y
                    self._last_control = None

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
        # Use regex to properly extract all tokens (commands and numbers)
        # SVG numbers can be: -1.5, .5, 1., 1e-5, etc.
        # Numbers can be separated by: whitespace, comma, or sign change, or implicit decimal

        tokens = []
        # Pattern matches: commands OR numbers (with optional exponent)
        # Numbers: optional sign, then either (digits with optional decimal) or (decimal with digits)
        pattern = r'([MmZzLlHhVvCcSsQqTtAa])|([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)'

        for match in re.finditer(pattern, d):
            cmd = match.group(1)
            num = match.group(2)
            if cmd:
                tokens.append(cmd)
            elif num:
                tokens.append(num)

        return tokens

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

    def _arc_to_points(self, x0, y0, rx, ry, x_rot, large_arc, sweep, x, y, segments=20):
        """Approximate elliptical arc with line segments."""
        # Handle edge cases
        if rx == 0 or ry == 0:
            return [(x0, y0), (x, y)]

        # Convert rotation to radians
        phi = math.radians(x_rot)
        cos_phi = math.cos(phi)
        sin_phi = math.sin(phi)

        # Compute center point (simplified endpoint parameterization)
        dx = (x0 - x) / 2
        dy = (y0 - y) / 2

        # Transform to unit circle space
        x1p = cos_phi * dx + sin_phi * dy
        y1p = -sin_phi * dx + cos_phi * dy

        # Correct radii if needed
        rx = abs(rx)
        ry = abs(ry)
        lambda_sq = (x1p**2 / rx**2) + (y1p**2 / ry**2)
        if lambda_sq > 1:
            rx *= math.sqrt(lambda_sq)
            ry *= math.sqrt(lambda_sq)

        # Compute center point
        sq = max(0, (rx**2 * ry**2 - rx**2 * y1p**2 - ry**2 * x1p**2) /
                    (rx**2 * y1p**2 + ry**2 * x1p**2))
        sq = math.sqrt(sq)
        if large_arc == sweep:
            sq = -sq

        cxp = sq * rx * y1p / ry
        cyp = -sq * ry * x1p / rx

        cx = cos_phi * cxp - sin_phi * cyp + (x0 + x) / 2
        cy = sin_phi * cxp + cos_phi * cyp + (y0 + y) / 2

        # Compute start and end angles
        def angle(ux, uy, vx, vy):
            n = math.sqrt(ux**2 + uy**2) * math.sqrt(vx**2 + vy**2)
            if n == 0:
                return 0
            c = (ux * vx + uy * vy) / n
            c = max(-1, min(1, c))
            a = math.acos(c)
            if ux * vy - uy * vx < 0:
                a = -a
            return a

        theta1 = angle(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
        dtheta = angle((x1p - cxp) / rx, (y1p - cyp) / ry,
                       (-x1p - cxp) / rx, (-y1p - cyp) / ry)

        if sweep == 0 and dtheta > 0:
            dtheta -= 2 * math.pi
        elif sweep == 1 and dtheta < 0:
            dtheta += 2 * math.pi

        # Generate points along the arc
        points = []
        for i in range(segments + 1):
            t = theta1 + (i / segments) * dtheta
            xp = rx * math.cos(t)
            yp = ry * math.sin(t)
            px = cos_phi * xp - sin_phi * yp + cx
            py = sin_phi * xp + cos_phi * yp + cy
            points.append((px, py))

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
            name = Path(filepath).stem
            return self._parse_svg_root(root, name)
        except Exception as e:
            print(f"Error loading SVG file: {e}")
            return None

    def load_svg_from_content(self, content: str, name: str = "SVG Element") -> Optional[SVGElement]:
        """
        Load SVG from a string content.

        Args:
            content: SVG content as a string
            name: Name for the element

        Returns:
            SVGElement with parsed paths, or None if parsing failed.
        """
        try:
            root = ET.fromstring(content)
            return self._parse_svg_root(root, name)
        except Exception as e:
            print(f"Error parsing SVG content: {e}")
            return None

    def _parse_svg_root(self, root: ET.Element, name: str) -> Optional[SVGElement]:
        """
        Parse SVG from an ElementTree root element.

        Args:
            root: The root SVG element
            name: Name for the element

        Returns:
            SVGElement with parsed paths, or None if parsing failed.
        """
        try:
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
                print(f"No paths found in SVG: {name}")
                return None

            # Create SVG element
            element = SVGElement(
                name=name,
                paths=all_paths,
                width=width,
                height=height,
                viewbox=viewbox
            )

            return element

        except Exception as e:
            print(f"Error parsing SVG: {e}")
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

    def _get_path_bounds(self, points: list) -> tuple:
        """Get bounding box of a path as (min_x, min_y, max_x, max_y)."""
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return (min(xs), min(ys), max(xs), max(ys))

    def _bounds_contains(self, outer: tuple, inner: tuple) -> bool:
        """Check if outer bounds completely contains inner bounds."""
        return (outer[0] <= inner[0] and outer[1] <= inner[1] and
                outer[2] >= inner[2] and outer[3] >= inner[3])

    def _get_bounds_area(self, bounds: tuple) -> float:
        """Get area of a bounding box."""
        return (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])

    def create_geometry(self, element: SVGElement,
                        target_size: float = 20.0,
                        depth: Optional[float] = None) -> Optional[cq.Workplane]:
        """
        Convert SVGElement to CadQuery geometry.

        Handles multi-path SVGs with even-odd fill rule by cutting inner
        shapes from outer shapes to create proper visual appearance.

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

            # Transform and clean all paths first
            cleaned_paths = []
            for path_idx, path_points in enumerate(element.paths):
                if len(path_points) < 3:
                    continue

                # Transform points
                transformed = []
                for x, y in path_points:
                    nx = (x - center_x) * scale
                    ny = -(y - center_y) * scale  # Flip Y for CadQuery coords
                    transformed.append((nx, ny))

                # Remove duplicate consecutive points
                cleaned = [transformed[0]]
                for i in range(1, len(transformed)):
                    px, py = cleaned[-1]
                    cx, cy = transformed[i]
                    if abs(cx - px) > 0.001 or abs(cy - py) > 0.001:
                        cleaned.append((cx, cy))

                if len(cleaned) < 3:
                    continue

                # If already closed, remove duplicate end point
                is_closed = (
                    abs(cleaned[0][0] - cleaned[-1][0]) < 0.01 and
                    abs(cleaned[0][1] - cleaned[-1][1]) < 0.01
                )
                if is_closed and len(cleaned) > 3:
                    cleaned = cleaned[:-1]

                cleaned_paths.append(cleaned)

            if not cleaned_paths:
                return None

            # For single path, just extrude it
            if len(cleaned_paths) == 1:
                try:
                    wire = cq.Workplane("XY").polyline(cleaned_paths[0]).close()
                    return wire.extrude(extrude_depth)
                except Exception as e:
                    print(f"Error creating single path geometry: {e}")
                    return None

            # For multiple paths, determine nesting and use even-odd fill rule
            # Calculate bounds for each path
            path_info = []
            for idx, cleaned in enumerate(cleaned_paths):
                bounds = self._get_path_bounds(cleaned)
                area = self._get_bounds_area(bounds)
                path_info.append({
                    'idx': idx,
                    'points': cleaned,
                    'bounds': bounds,
                    'area': area,
                    'nesting_level': 0
                })

            # Sort by area (largest first)
            path_info.sort(key=lambda p: p['area'], reverse=True)

            # Determine nesting levels based on containment
            for i, inner in enumerate(path_info):
                for outer in path_info[:i]:  # Only check larger paths
                    if self._bounds_contains(outer['bounds'], inner['bounds']):
                        inner['nesting_level'] = outer['nesting_level'] + 1
                        break  # Found the immediate parent

            # Build geometry using even-odd rule:
            # - Level 0: extrude (filled)
            # - Level 1: cut (hole)
            # - Level 2: extrude (filled again)
            # - etc.
            result = None

            for pinfo in path_info:
                try:
                    wire = cq.Workplane("XY").polyline(pinfo['points']).close()
                    face = wire.extrude(extrude_depth)

                    if result is None:
                        result = face
                    elif pinfo['nesting_level'] % 2 == 0:
                        # Even nesting level: union (fill)
                        result = result.union(face)
                    else:
                        # Odd nesting level: cut (hole)
                        result = result.cut(face)
                except Exception as e:
                    print(f"Error creating path geometry for path {pinfo['idx']}: {e}")
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
