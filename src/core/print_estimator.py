"""
Print Time Estimator
Estimates print time, filament usage, and cost for 3D printed nameplates.
"""

from dataclasses import dataclass
from typing import Optional
import cadquery as cq

from core.material_presets import MaterialPreset, get_material_preset


@dataclass
class PrintEstimate:
    """Print estimate results."""
    # Time estimates
    print_time_minutes: float = 0.0
    print_time_formatted: str = "0:00"

    # Material usage
    volume_mm3: float = 0.0
    volume_cm3: float = 0.0
    weight_grams: float = 0.0
    filament_length_m: float = 0.0

    # Cost (based on filament price per kg)
    material_cost: float = 0.0
    electricity_cost: float = 0.0
    total_cost: float = 0.0

    # Print settings used
    layer_height: float = 0.2
    infill_percent: int = 20
    print_speed: int = 50
    material_name: str = ""


@dataclass
class PrinterSettings:
    """3D printer settings for estimation."""
    layer_height: float = 0.2          # mm
    infill_percent: int = 20           # %
    wall_count: int = 3                # Number of perimeters
    top_layers: int = 4
    bottom_layers: int = 4
    print_speed: int = 50              # mm/s - infill
    perimeter_speed: int = 40          # mm/s
    travel_speed: int = 150            # mm/s
    first_layer_speed: int = 20        # mm/s
    nozzle_diameter: float = 0.4       # mm
    filament_diameter: float = 1.75    # mm
    # Cost settings
    filament_cost_per_kg: float = 25.0  # USD
    electricity_cost_per_kwh: float = 0.12  # USD
    printer_power_watts: int = 200      # Average printer power consumption


class PrintEstimator:
    """
    Estimates print time and material usage for 3D models.

    Uses simplified calculations based on volume and layer count.
    Actual print times depend on many factors and may vary.
    """

    def __init__(self, settings: Optional[PrinterSettings] = None):
        """
        Initialize the print estimator.

        Args:
            settings: Printer settings, uses defaults if not provided
        """
        self.settings = settings or PrinterSettings()

    def estimate(self, solid: cq.Workplane,
                 material_name: str = "PLA White",
                 settings: Optional[PrinterSettings] = None) -> PrintEstimate:
        """
        Estimate print time and material usage for a solid.

        Args:
            solid: CadQuery workplane containing the solid to estimate
            material_name: Name of material preset to use
            settings: Optional settings override

        Returns:
            PrintEstimate with all calculated values
        """
        cfg = settings or self.settings
        material = get_material_preset(material_name)

        # Calculate volume
        try:
            volume_mm3 = self._calculate_volume(solid)
        except Exception as e:
            print(f"Error calculating volume: {e}")
            volume_mm3 = 0.0

        volume_cm3 = volume_mm3 / 1000.0

        # Calculate bounding box for layer/time estimates
        try:
            bbox = self._get_bounding_box(solid)
            height = bbox[5] - bbox[4]  # Z max - Z min
            width = bbox[1] - bbox[0]   # X max - X min
            depth = bbox[3] - bbox[2]   # Y max - Y min
        except Exception:
            height = 3.0  # Default nameplate height
            width = 100.0
            depth = 30.0

        # Calculate layer count
        layer_count = max(1, int(height / cfg.layer_height))

        # Calculate print time
        print_time = self._estimate_print_time(
            volume_mm3, layer_count, width, depth, height, cfg
        )

        # Calculate material usage
        # Account for infill - solid volume at edges, infill in middle
        shell_volume = self._estimate_shell_volume(volume_mm3, width, depth, height, cfg)
        infill_volume = (volume_mm3 - shell_volume) * (cfg.infill_percent / 100.0)
        actual_volume = shell_volume + infill_volume

        # Weight based on material density
        weight_grams = (actual_volume / 1000.0) * material.density

        # Filament length (for 1.75mm diameter filament)
        filament_area = 3.14159 * (cfg.filament_diameter / 2) ** 2
        filament_length_mm = actual_volume / filament_area
        filament_length_m = filament_length_mm / 1000.0

        # Cost calculations
        material_cost = (weight_grams / 1000.0) * cfg.filament_cost_per_kg
        electricity_cost = (
            (print_time / 60.0) *  # Hours
            (cfg.printer_power_watts / 1000.0) *  # kW
            cfg.electricity_cost_per_kwh
        )
        total_cost = material_cost + electricity_cost

        # Format time
        hours = int(print_time // 60)
        minutes = int(print_time % 60)
        if hours > 0:
            time_formatted = f"{hours}h {minutes}m"
        else:
            time_formatted = f"{minutes}m"

        return PrintEstimate(
            print_time_minutes=print_time,
            print_time_formatted=time_formatted,
            volume_mm3=volume_mm3,
            volume_cm3=volume_cm3,
            weight_grams=weight_grams,
            filament_length_m=filament_length_m,
            material_cost=material_cost,
            electricity_cost=electricity_cost,
            total_cost=total_cost,
            layer_height=cfg.layer_height,
            infill_percent=cfg.infill_percent,
            print_speed=cfg.print_speed,
            material_name=material_name
        )

    def _calculate_volume(self, solid: cq.Workplane) -> float:
        """Calculate volume of the solid in mm³."""
        try:
            # Get the solid from the workplane
            if hasattr(solid, 'val'):
                s = solid.val()
                if hasattr(s, 'Volume'):
                    return abs(s.Volume())

            # Try to get volume from compound
            if hasattr(solid, 'solids'):
                total = 0.0
                for s in solid.solids().vals():
                    if hasattr(s, 'Volume'):
                        total += abs(s.Volume())
                return total

        except Exception:
            pass

        return 0.0

    def _get_bounding_box(self, solid: cq.Workplane) -> tuple:
        """Get bounding box as (xmin, xmax, ymin, ymax, zmin, zmax)."""
        try:
            bb = solid.val().BoundingBox()
            return (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)
        except Exception:
            return (0, 100, 0, 30, 0, 3)

    def _estimate_shell_volume(self, total_volume: float, width: float,
                               depth: float, height: float,
                               cfg: PrinterSettings) -> float:
        """Estimate volume of shell (walls, top, bottom)."""
        # Wall thickness
        wall_thickness = cfg.wall_count * cfg.nozzle_diameter

        # Top/bottom thickness
        top_thickness = cfg.top_layers * cfg.layer_height
        bottom_thickness = cfg.bottom_layers * cfg.layer_height

        # Calculate interior volume
        inner_width = max(0, width - 2 * wall_thickness)
        inner_depth = max(0, depth - 2 * wall_thickness)
        inner_height = max(0, height - top_thickness - bottom_thickness)

        if inner_width <= 0 or inner_depth <= 0 or inner_height <= 0:
            # Object is all shell (very thin)
            return total_volume

        # Approximate interior as simple box ratio
        inner_ratio = (inner_width * inner_depth * inner_height) / (width * depth * height)
        shell_volume = total_volume * (1 - inner_ratio)

        return shell_volume

    def _estimate_print_time(self, volume_mm3: float, layer_count: int,
                             width: float, depth: float, height: float,
                             cfg: PrinterSettings) -> float:
        """
        Estimate print time in minutes.

        This is a simplified estimate. Actual times depend on:
        - Slicer settings and path optimization
        - Printer acceleration and jerk settings
        - Number of retractions
        - Cooling requirements
        """
        if volume_mm3 <= 0:
            return 0.0

        # Time components:

        # 1. Extrusion time - based on volume and extrusion rate
        # Extrusion rate = nozzle area * layer height * speed
        extrusion_area = cfg.nozzle_diameter * cfg.layer_height
        avg_speed = (cfg.print_speed + cfg.perimeter_speed) / 2
        extrusion_rate_mm3_per_s = extrusion_area * avg_speed

        # Account for infill (less material = less time)
        shell_volume = self._estimate_shell_volume(volume_mm3, width, depth, height, cfg)
        infill_volume = (volume_mm3 - shell_volume) * (cfg.infill_percent / 100.0)
        actual_volume = shell_volume + infill_volume

        extrusion_time_s = actual_volume / max(1, extrusion_rate_mm3_per_s)

        # 2. Travel time - estimate based on layer count and size
        # Assume some travel per layer
        avg_travel_per_layer = (width + depth) * 2  # Perimeter
        total_travel = avg_travel_per_layer * layer_count
        travel_time_s = total_travel / cfg.travel_speed

        # 3. Layer change time - small delay per layer
        layer_change_time_s = layer_count * 0.5  # ~0.5s per layer change

        # 4. First layer is slower
        first_layer_penalty = (cfg.print_speed / cfg.first_layer_speed - 1) * 30

        # 5. Add some overhead for heating, homing, etc.
        overhead_s = 60  # 1 minute startup

        # Total time
        total_time_s = (
            extrusion_time_s +
            travel_time_s +
            layer_change_time_s +
            first_layer_penalty +
            overhead_s
        )

        # Add 20% buffer for retractions, cooling, etc.
        total_time_s *= 1.2

        return total_time_s / 60.0  # Convert to minutes


def format_estimate(estimate: PrintEstimate) -> str:
    """Format a print estimate as a readable string."""
    lines = [
        f"Print Time: {estimate.print_time_formatted}",
        f"Material: {estimate.material_name}",
        f"",
        f"Volume: {estimate.volume_cm3:.2f} cm³",
        f"Weight: {estimate.weight_grams:.1f} g",
        f"Filament: {estimate.filament_length_m:.2f} m",
        f"",
        f"Settings:",
        f"  Layer Height: {estimate.layer_height} mm",
        f"  Infill: {estimate.infill_percent}%",
        f"  Print Speed: {estimate.print_speed} mm/s",
        f"",
        f"Estimated Cost:",
        f"  Material: ${estimate.material_cost:.2f}",
        f"  Electricity: ${estimate.electricity_cost:.2f}",
        f"  Total: ${estimate.total_cost:.2f}",
    ]
    return "\n".join(lines)
