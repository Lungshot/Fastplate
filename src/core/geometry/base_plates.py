"""
Base Plate Generators
Creates various base plate shapes for nameplates.
"""

import cadquery as cq
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Tuple, List


class PlateShape(Enum):
    """Available base plate shapes."""
    NONE = "none"  # Text only, no base plate
    RECTANGLE = "rectangle"
    ROUNDED_RECTANGLE = "rounded_rectangle"
    OVAL = "oval"
    CHAMFERED = "chamfered"
    HEXAGON = "hexagon"
    OCTAGON = "octagon"
    SWEEPING = "sweeping"  # Handled by SweepingPlateGenerator
    BADGE = "badge"  # Shield/badge shape
    KEYCHAIN = "keychain"  # Small plate with hole
    STAR = "star"  # Star shape
    DIAMOND = "diamond"  # Diamond/rhombus shape
    ARROW = "arrow"  # Arrow pointing right
    HEART = "heart"  # Heart shape
    CLOUD = "cloud"  # Cloud shape
    CUSTOM = "custom"  # Custom SVG outline


# Industry-standard plate templates
PLATE_TEMPLATES = {
    "Business Card (3.5x2 in)": {"width": 89.0, "height": 51.0},
    "Credit Card (3.4x2.1 in)": {"width": 86.0, "height": 54.0},
    "ID Badge (3.4x2.1 in)": {"width": 86.0, "height": 54.0},
    "Name Tag Small (3x1 in)": {"width": 76.0, "height": 25.0},
    "Name Tag Medium (3x1.5 in)": {"width": 76.0, "height": 38.0},
    "Name Tag Large (4x1.5 in)": {"width": 102.0, "height": 38.0},
    "Desk Plate (8x2 in)": {"width": 203.0, "height": 51.0},
    "Door Sign (6x2 in)": {"width": 152.0, "height": 51.0},
    "Luggage Tag (3x2 in)": {"width": 76.0, "height": 51.0},
    "Pet Tag Small (1 in circle)": {"width": 25.0, "height": 25.0},
    "Pet Tag Medium (1.25 in circle)": {"width": 32.0, "height": 32.0},
    "Keychain (2x0.75 in)": {"width": 51.0, "height": 19.0},
    "Trophy Plate (4x1 in)": {"width": 102.0, "height": 25.0},
    "Award Plate (6x1.5 in)": {"width": 152.0, "height": 38.0},
    "Military Tag (2x1.1 in)": {"width": 51.0, "height": 28.0},
}


class EdgeStyle(Enum):
    """Edge finishing styles for plate edges."""
    NONE = "none"           # Sharp edges
    CHAMFER = "chamfer"     # Angled cut
    FILLET = "fillet"       # Rounded edges
    BEVEL = "bevel"         # Same as chamfer (alias)


@dataclass
class PlateConfig:
    """Configuration for base plate generation."""
    shape: PlateShape = PlateShape.ROUNDED_RECTANGLE
    width: float = 100.0          # mm
    height: float = 30.0          # mm
    thickness: float = 3.0        # mm
    corner_radius: float = 5.0    # mm (for rounded shapes)
    chamfer_size: float = 3.0     # mm (for chamfered shape)

    # Edge finishing options
    edge_style: EdgeStyle = EdgeStyle.NONE
    edge_size: float = 0.5        # mm - size of chamfer/fillet
    edge_top_only: bool = True    # Apply only to top edges (preserves flat bottom)

    # Auto-sizing options
    auto_width: bool = False
    auto_height: bool = False

    # Padding (when auto-sizing)
    padding_top: float = 5.0
    padding_bottom: float = 5.0
    padding_left: float = 10.0
    padding_right: float = 10.0

    # Custom SVG shape (for CUSTOM shape type)
    custom_svg_paths: List[List[Tuple[float, float]]] = field(default_factory=list)
    custom_svg_name: str = ""

    # Layered plate options
    layered_enabled: bool = False
    layer_count: int = 2
    layer_offset: float = 2.0     # mm - offset between layers
    layer_shrink: float = 3.0     # mm - how much smaller each layer is

    # Inset panel options
    inset_enabled: bool = False
    inset_depth: float = 1.0      # mm - depth of inset
    inset_margin: float = 5.0     # mm - margin from edge
    inset_corner_radius: float = 3.0  # mm - corner radius of inset

    def get_total_padding(self) -> Tuple[float, float]:
        """Get total horizontal and vertical padding."""
        return (
            self.padding_left + self.padding_right,
            self.padding_top + self.padding_bottom
        )


class BasePlateGenerator:
    """
    Generates base plate geometry for nameplates.
    """
    
    def __init__(self, config: Optional[PlateConfig] = None):
        self.config = config or PlateConfig()
    
    def generate(self, config: Optional[PlateConfig] = None) -> cq.Workplane:
        """
        Generate a base plate according to configuration.

        Args:
            config: Optional config override

        Returns:
            CadQuery Workplane with the base plate solid.
        """
        cfg = config or self.config

        if cfg.shape == PlateShape.RECTANGLE:
            plate = self._make_rectangle(cfg)
        elif cfg.shape == PlateShape.ROUNDED_RECTANGLE:
            plate = self._make_rounded_rectangle(cfg)
        elif cfg.shape == PlateShape.OVAL:
            plate = self._make_oval(cfg)
        elif cfg.shape == PlateShape.CHAMFERED:
            plate = self._make_chamfered(cfg)
        elif cfg.shape == PlateShape.HEXAGON:
            plate = self._make_hexagon(cfg)
        elif cfg.shape == PlateShape.OCTAGON:
            plate = self._make_octagon(cfg)
        elif cfg.shape == PlateShape.BADGE:
            plate = self._make_badge(cfg)
        elif cfg.shape == PlateShape.KEYCHAIN:
            plate = self._make_keychain(cfg)
        elif cfg.shape == PlateShape.STAR:
            plate = self._make_star(cfg)
        elif cfg.shape == PlateShape.DIAMOND:
            plate = self._make_diamond(cfg)
        elif cfg.shape == PlateShape.ARROW:
            plate = self._make_arrow(cfg)
        elif cfg.shape == PlateShape.HEART:
            plate = self._make_heart(cfg)
        elif cfg.shape == PlateShape.CLOUD:
            plate = self._make_cloud(cfg)
        elif cfg.shape == PlateShape.CUSTOM:
            plate = self._make_custom(cfg)
        else:
            # Default to rounded rectangle
            plate = self._make_rounded_rectangle(cfg)

        # Apply layered effect if enabled
        if cfg.layered_enabled and cfg.layer_count > 1:
            plate = self._apply_layered_effect(plate, cfg)

        # Apply inset panel if enabled
        if cfg.inset_enabled:
            plate = self._apply_inset_panel(plate, cfg)

        # Apply edge finishing if configured
        return self._apply_edge_finishing(plate, cfg)

    def _apply_edge_finishing(self, plate: cq.Workplane, cfg: PlateConfig) -> cq.Workplane:
        """Apply edge chamfer or fillet to the plate."""
        if cfg.edge_style == EdgeStyle.NONE or cfg.edge_size <= 0:
            return plate

        try:
            # Limit edge size to avoid geometry errors
            max_size = min(cfg.thickness / 2 - 0.1, cfg.edge_size)
            if max_size <= 0:
                return plate

            if cfg.edge_top_only:
                # Apply only to top horizontal edges
                edge_selector = ">Z"
            else:
                # Apply to all horizontal edges (top and bottom)
                edge_selector = "#Z"

            if cfg.edge_style in (EdgeStyle.CHAMFER, EdgeStyle.BEVEL):
                return plate.edges(edge_selector).chamfer(max_size)
            elif cfg.edge_style == EdgeStyle.FILLET:
                return plate.edges(edge_selector).fillet(max_size)

        except Exception as e:
            print(f"Warning: Could not apply edge finishing: {e}")

        return plate
    
    def _make_rectangle(self, cfg: PlateConfig) -> cq.Workplane:
        """Create a simple rectangular plate."""
        return (
            cq.Workplane("XY")
            .box(cfg.width, cfg.height, cfg.thickness)
            .translate((0, 0, cfg.thickness / 2))
        )
    
    def _make_rounded_rectangle(self, cfg: PlateConfig) -> cq.Workplane:
        """Create a rectangle with rounded corners."""
        # Ensure corner radius isn't larger than half the smallest dimension
        max_radius = min(cfg.width, cfg.height) / 2 - 0.1
        radius = min(cfg.corner_radius, max_radius)
        
        if radius <= 0:
            return self._make_rectangle(cfg)
        
        return (
            cq.Workplane("XY")
            .box(cfg.width, cfg.height, cfg.thickness)
            .translate((0, 0, cfg.thickness / 2))
            .edges("|Z")
            .fillet(radius)
        )
    
    def _make_oval(self, cfg: PlateConfig) -> cq.Workplane:
        """Create an oval/ellipse plate."""
        return (
            cq.Workplane("XY")
            .ellipse(cfg.width / 2, cfg.height / 2)
            .extrude(cfg.thickness)
        )
    
    def _make_chamfered(self, cfg: PlateConfig) -> cq.Workplane:
        """Create a rectangle with chamfered corners."""
        # Ensure chamfer isn't too large
        max_chamfer = min(cfg.width, cfg.height) / 2 - 0.1
        chamfer = min(cfg.chamfer_size, max_chamfer)
        
        if chamfer <= 0:
            return self._make_rectangle(cfg)
        
        return (
            cq.Workplane("XY")
            .box(cfg.width, cfg.height, cfg.thickness)
            .translate((0, 0, cfg.thickness / 2))
            .edges("|Z")
            .chamfer(chamfer)
        )
    
    def _make_hexagon(self, cfg: PlateConfig) -> cq.Workplane:
        """Create a hexagonal plate."""
        # Use the smaller dimension to fit the hexagon
        size = min(cfg.width, cfg.height) / 2
        
        return (
            cq.Workplane("XY")
            .polygon(6, size * 2)
            .extrude(cfg.thickness)
        )
    
    def _make_octagon(self, cfg: PlateConfig) -> cq.Workplane:
        """Create an octagonal plate."""
        size = min(cfg.width, cfg.height) / 2

        return (
            cq.Workplane("XY")
            .polygon(8, size * 2)
            .extrude(cfg.thickness)
        )

    def _make_badge(self, cfg: PlateConfig) -> cq.Workplane:
        """Create a shield/badge shaped plate."""
        w = cfg.width / 2
        h = cfg.height / 2

        # Shield shape: flat top with pointed bottom
        points = [
            (-w, h),           # Top left
            (w, h),            # Top right
            (w, 0),            # Right side middle
            (w * 0.6, -h * 0.6),  # Right curve down
            (0, -h),           # Bottom point
            (-w * 0.6, -h * 0.6), # Left curve down
            (-w, 0),           # Left side middle
        ]

        return (
            cq.Workplane("XY")
            .polyline(points)
            .close()
            .extrude(cfg.thickness)
        )

    def _make_keychain(self, cfg: PlateConfig) -> cq.Workplane:
        """Create a keychain plate with hole for ring."""
        # Ensure corner radius isn't larger than half the smallest dimension
        max_radius = min(cfg.width, cfg.height) / 2 - 0.1
        radius = min(cfg.corner_radius, max_radius)

        # Create rounded rectangle base
        if radius > 0:
            plate = (
                cq.Workplane("XY")
                .box(cfg.width, cfg.height, cfg.thickness)
                .translate((0, 0, cfg.thickness / 2))
                .edges("|Z")
                .fillet(radius)
            )
        else:
            plate = (
                cq.Workplane("XY")
                .box(cfg.width, cfg.height, cfg.thickness)
                .translate((0, 0, cfg.thickness / 2))
            )

        # Add keychain hole on the left side
        hole_radius = min(cfg.height * 0.15, 3.0)  # 15% of height or 3mm max
        hole_x = -cfg.width / 2 + hole_radius + 3  # 3mm from edge

        hole = (
            cq.Workplane("XY")
            .center(hole_x, 0)
            .circle(hole_radius)
            .extrude(cfg.thickness + 10)
        )

        return plate.cut(hole)

    def _make_star(self, cfg: PlateConfig) -> cq.Workplane:
        """Create a 5-pointed star plate."""
        import math

        # Use smaller dimension for star size
        outer_r = min(cfg.width, cfg.height) / 2
        inner_r = outer_r * 0.4  # Inner radius for star points

        points = []
        for i in range(10):
            angle = math.pi / 2 + i * math.pi / 5  # Start from top
            r = outer_r if i % 2 == 0 else inner_r
            x = r * math.cos(angle)
            y = r * math.sin(angle)
            points.append((x, y))

        return (
            cq.Workplane("XY")
            .polyline(points)
            .close()
            .extrude(cfg.thickness)
        )

    def _make_diamond(self, cfg: PlateConfig) -> cq.Workplane:
        """Create a diamond/rhombus plate."""
        w = cfg.width / 2
        h = cfg.height / 2

        points = [
            (0, h),    # Top
            (w, 0),    # Right
            (0, -h),   # Bottom
            (-w, 0),   # Left
        ]

        return (
            cq.Workplane("XY")
            .polyline(points)
            .close()
            .extrude(cfg.thickness)
        )

    def _make_arrow(self, cfg: PlateConfig) -> cq.Workplane:
        """Create an arrow pointing right."""
        w = cfg.width / 2
        h = cfg.height / 2
        shaft_h = h * 0.4  # Shaft height is 40% of total height
        head_start = w * 0.3  # Arrow head starts at 30% from center

        points = [
            (-w, shaft_h),      # Shaft top left
            (head_start, shaft_h),  # Shaft top right
            (head_start, h),    # Arrow head top
            (w, 0),             # Arrow point
            (head_start, -h),   # Arrow head bottom
            (head_start, -shaft_h),  # Shaft bottom right
            (-w, -shaft_h),     # Shaft bottom left
        ]

        return (
            cq.Workplane("XY")
            .polyline(points)
            .close()
            .extrude(cfg.thickness)
        )

    def _make_heart(self, cfg: PlateConfig) -> cq.Workplane:
        """Create a heart shaped plate."""
        import math

        # Heart parametric equation approximation
        scale = min(cfg.width, cfg.height) / 2 * 0.9
        points = []

        for i in range(50):
            t = i * 2 * math.pi / 50
            # Heart curve parametric equations
            x = 16 * math.sin(t) ** 3
            y = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)
            points.append((x * scale / 16, y * scale / 16))

        return (
            cq.Workplane("XY")
            .polyline(points)
            .close()
            .extrude(cfg.thickness)
        )

    def _make_cloud(self, cfg: PlateConfig) -> cq.Workplane:
        """Create a cloud shaped plate using overlapping circles."""
        w = cfg.width / 2
        h = cfg.height / 2

        # Create cloud from multiple overlapping circles
        r1 = h * 0.7  # Main body radius
        r2 = h * 0.5  # Side bumps
        r3 = h * 0.4  # Smaller bumps

        # Start with center circle
        cloud = (
            cq.Workplane("XY")
            .circle(r1)
            .extrude(cfg.thickness)
        )

        # Add overlapping circles for cloud shape
        offsets = [
            (-w * 0.4, h * 0.1, r2),   # Left bump
            (w * 0.4, h * 0.1, r2),    # Right bump
            (-w * 0.2, h * 0.3, r3),   # Top left
            (w * 0.2, h * 0.3, r3),    # Top right
            (0, h * 0.35, r3),         # Top center
        ]

        for ox, oy, r in offsets:
            bump = (
                cq.Workplane("XY")
                .center(ox, oy)
                .circle(r)
                .extrude(cfg.thickness)
            )
            cloud = cloud.union(bump)

        return cloud

    def _make_custom(self, cfg: PlateConfig) -> cq.Workplane:
        """Create a plate from custom SVG paths."""
        if not cfg.custom_svg_paths:
            # Fallback to rounded rectangle if no custom paths
            return self._make_rounded_rectangle(cfg)

        try:
            # Find the largest closed path to use as the outline
            best_path = None
            best_area = 0

            for path in cfg.custom_svg_paths:
                if len(path) < 3:
                    continue

                # Check if path is closed
                is_closed = (
                    abs(path[0][0] - path[-1][0]) < 0.01 and
                    abs(path[0][1] - path[-1][1]) < 0.01
                )
                if not is_closed:
                    path = list(path) + [path[0]]

                # Estimate area using shoelace formula
                area = 0
                for i in range(len(path) - 1):
                    area += path[i][0] * path[i+1][1]
                    area -= path[i+1][0] * path[i][1]
                area = abs(area) / 2

                if area > best_area:
                    best_area = area
                    best_path = path

            if not best_path:
                return self._make_rounded_rectangle(cfg)

            # Calculate bounds and scale to fit width/height
            min_x = min(p[0] for p in best_path)
            max_x = max(p[0] for p in best_path)
            min_y = min(p[1] for p in best_path)
            max_y = max(p[1] for p in best_path)

            svg_width = max_x - min_x
            svg_height = max_y - min_y

            if svg_width <= 0 or svg_height <= 0:
                return self._make_rounded_rectangle(cfg)

            # Calculate scale to fit desired dimensions
            scale_x = cfg.width / svg_width
            scale_y = cfg.height / svg_height
            scale = min(scale_x, scale_y)  # Maintain aspect ratio

            # Center offset
            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2

            # Transform points
            transformed = []
            for x, y in best_path:
                nx = (x - center_x) * scale
                ny = (y - center_y) * scale
                transformed.append((nx, ny))

            # Create wire and extrude
            return (
                cq.Workplane("XY")
                .polyline(transformed)
                .close()
                .extrude(cfg.thickness)
            )

        except Exception as e:
            print(f"Error creating custom plate: {e}")
            return self._make_rounded_rectangle(cfg)

    def _apply_layered_effect(self, plate: cq.Workplane, cfg: PlateConfig) -> cq.Workplane:
        """Apply layered/stacked plate effect."""
        try:
            result = plate
            layer_thickness = cfg.thickness / cfg.layer_count

            for i in range(1, cfg.layer_count):
                # Calculate shrink for this layer
                shrink = cfg.layer_shrink * i
                new_width = cfg.width - shrink * 2
                new_height = cfg.height - shrink * 2

                if new_width <= 0 or new_height <= 0:
                    break

                # Create a smaller plate for this layer
                layer_cfg = PlateConfig(
                    shape=cfg.shape if cfg.shape != PlateShape.CUSTOM else PlateShape.ROUNDED_RECTANGLE,
                    width=new_width,
                    height=new_height,
                    thickness=layer_thickness,
                    corner_radius=max(0, cfg.corner_radius - shrink),
                    chamfer_size=max(0, cfg.chamfer_size - shrink),
                )

                # Generate the layer
                if layer_cfg.shape == PlateShape.RECTANGLE:
                    layer = self._make_rectangle(layer_cfg)
                elif layer_cfg.shape == PlateShape.ROUNDED_RECTANGLE:
                    layer = self._make_rounded_rectangle(layer_cfg)
                elif layer_cfg.shape == PlateShape.OVAL:
                    layer = self._make_oval(layer_cfg)
                elif layer_cfg.shape == PlateShape.CHAMFERED:
                    layer = self._make_chamfered(layer_cfg)
                else:
                    layer = self._make_rounded_rectangle(layer_cfg)

                # Position layer on top of previous
                z_offset = cfg.thickness + i * cfg.layer_offset
                layer = layer.translate((0, 0, z_offset))

                result = result.union(layer)

            return result

        except Exception as e:
            print(f"Error applying layered effect: {e}")
            return plate

    def _apply_inset_panel(self, plate: cq.Workplane, cfg: PlateConfig) -> cq.Workplane:
        """Apply an inset panel recess to the plate."""
        try:
            # Calculate inset dimensions
            inset_width = cfg.width - cfg.inset_margin * 2
            inset_height = cfg.height - cfg.inset_margin * 2

            if inset_width <= 0 or inset_height <= 0:
                return plate

            # Ensure corner radius fits
            max_radius = min(inset_width, inset_height) / 2 - 0.1
            radius = min(cfg.inset_corner_radius, max_radius)

            # Create the inset cutout
            if radius > 0:
                inset = (
                    cq.Workplane("XY")
                    .box(inset_width, inset_height, cfg.inset_depth + 0.1)
                    .edges("|Z")
                    .fillet(radius)
                    .translate((0, 0, cfg.thickness - cfg.inset_depth / 2 + 0.05))
                )
            else:
                inset = (
                    cq.Workplane("XY")
                    .box(inset_width, inset_height, cfg.inset_depth + 0.1)
                    .translate((0, 0, cfg.thickness - cfg.inset_depth / 2 + 0.05))
                )

            return plate.cut(inset)

        except Exception as e:
            print(f"Error applying inset panel: {e}")
            return plate

    def calculate_auto_size(self, text_bbox: Tuple[float, float, float, float],
                           config: Optional[PlateConfig] = None) -> Tuple[float, float]:
        """
        Calculate automatic plate dimensions based on text bounding box.

        Args:
            text_bbox: (min_x, min_y, max_x, max_y) of text
            config: Optional config override

        Returns:
            (width, height) for the plate
        """
        cfg = config or self.config

        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        width = cfg.width
        height = cfg.height

        if cfg.auto_width:
            width = text_width + cfg.padding_left + cfg.padding_right

        if cfg.auto_height:
            height = text_height + cfg.padding_top + cfg.padding_bottom

        return (width, height)
