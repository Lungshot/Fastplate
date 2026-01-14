"""
Material Presets
Defines material presets for 3D visualization and print settings.
"""

from dataclasses import dataclass
from typing import Dict, Tuple
from enum import Enum


class MaterialType(Enum):
    """Types of materials."""
    PLA = "pla"
    PETG = "petg"
    ABS = "abs"
    TPU = "tpu"
    WOOD = "wood"
    METAL = "metal"
    RESIN = "resin"
    CUSTOM = "custom"


@dataclass
class MaterialPreset:
    """Defines a material preset for visualization and printing."""
    name: str
    type: MaterialType
    # Visualization colors (RGB 0-255)
    primary_color: Tuple[int, int, int] = (200, 200, 200)
    secondary_color: Tuple[int, int, int] = (150, 150, 150)  # For two-color prints
    # Surface properties (0.0-1.0)
    shininess: float = 0.3
    roughness: float = 0.5
    metallic: float = 0.0
    opacity: float = 1.0
    # Print settings
    print_temp: int = 200          # Nozzle temperature (°C)
    bed_temp: int = 60             # Bed temperature (°C)
    print_speed: int = 50          # Print speed (mm/s)
    layer_height: float = 0.2      # Default layer height (mm)
    infill_percent: int = 20       # Default infill percentage
    # Density for weight estimation (g/cm³)
    density: float = 1.24


# Pre-defined material presets
MATERIAL_PRESETS: Dict[str, MaterialPreset] = {
    # PLA variants
    "PLA Black": MaterialPreset(
        name="PLA Black",
        type=MaterialType.PLA,
        primary_color=(30, 30, 30),
        shininess=0.4,
        roughness=0.4,
        print_temp=200,
        bed_temp=60,
        density=1.24
    ),
    "PLA White": MaterialPreset(
        name="PLA White",
        type=MaterialType.PLA,
        primary_color=(245, 245, 245),
        shininess=0.3,
        roughness=0.5,
        print_temp=200,
        bed_temp=60,
        density=1.24
    ),
    "PLA Red": MaterialPreset(
        name="PLA Red",
        type=MaterialType.PLA,
        primary_color=(200, 40, 40),
        shininess=0.4,
        roughness=0.4,
        print_temp=200,
        bed_temp=60,
        density=1.24
    ),
    "PLA Blue": MaterialPreset(
        name="PLA Blue",
        type=MaterialType.PLA,
        primary_color=(40, 80, 200),
        shininess=0.4,
        roughness=0.4,
        print_temp=200,
        bed_temp=60,
        density=1.24
    ),
    "PLA Green": MaterialPreset(
        name="PLA Green",
        type=MaterialType.PLA,
        primary_color=(40, 160, 60),
        shininess=0.4,
        roughness=0.4,
        print_temp=200,
        bed_temp=60,
        density=1.24
    ),
    "PLA Gold": MaterialPreset(
        name="PLA Gold",
        type=MaterialType.PLA,
        primary_color=(212, 175, 55),
        shininess=0.6,
        roughness=0.3,
        metallic=0.3,
        print_temp=200,
        bed_temp=60,
        density=1.24
    ),
    "PLA Silver": MaterialPreset(
        name="PLA Silver",
        type=MaterialType.PLA,
        primary_color=(192, 192, 192),
        shininess=0.7,
        roughness=0.2,
        metallic=0.4,
        print_temp=200,
        bed_temp=60,
        density=1.24
    ),
    "PLA Wood": MaterialPreset(
        name="PLA Wood",
        type=MaterialType.PLA,
        primary_color=(139, 90, 43),
        shininess=0.1,
        roughness=0.8,
        print_temp=210,
        bed_temp=60,
        density=1.15
    ),

    # PETG variants
    "PETG Clear": MaterialPreset(
        name="PETG Clear",
        type=MaterialType.PETG,
        primary_color=(220, 220, 230),
        shininess=0.8,
        roughness=0.1,
        opacity=0.7,
        print_temp=235,
        bed_temp=80,
        print_speed=40,
        density=1.27
    ),
    "PETG Black": MaterialPreset(
        name="PETG Black",
        type=MaterialType.PETG,
        primary_color=(25, 25, 25),
        shininess=0.5,
        roughness=0.3,
        print_temp=235,
        bed_temp=80,
        print_speed=40,
        density=1.27
    ),

    # ABS variants
    "ABS Black": MaterialPreset(
        name="ABS Black",
        type=MaterialType.ABS,
        primary_color=(35, 35, 35),
        shininess=0.3,
        roughness=0.5,
        print_temp=240,
        bed_temp=100,
        print_speed=50,
        density=1.04
    ),
    "ABS White": MaterialPreset(
        name="ABS White",
        type=MaterialType.ABS,
        primary_color=(240, 240, 240),
        shininess=0.3,
        roughness=0.5,
        print_temp=240,
        bed_temp=100,
        print_speed=50,
        density=1.04
    ),

    # TPU
    "TPU Black": MaterialPreset(
        name="TPU Black",
        type=MaterialType.TPU,
        primary_color=(30, 30, 30),
        shininess=0.2,
        roughness=0.7,
        print_temp=220,
        bed_temp=50,
        print_speed=25,
        density=1.21
    ),
    "TPU Clear": MaterialPreset(
        name="TPU Clear",
        type=MaterialType.TPU,
        primary_color=(200, 200, 210),
        shininess=0.4,
        roughness=0.4,
        opacity=0.8,
        print_temp=220,
        bed_temp=50,
        print_speed=25,
        density=1.21
    ),

    # Specialty
    "Brushed Aluminum": MaterialPreset(
        name="Brushed Aluminum",
        type=MaterialType.METAL,
        primary_color=(180, 180, 185),
        shininess=0.8,
        roughness=0.2,
        metallic=0.9,
        print_temp=200,
        bed_temp=60,
        density=2.7
    ),
    "Brass": MaterialPreset(
        name="Brass",
        type=MaterialType.METAL,
        primary_color=(181, 166, 66),
        shininess=0.9,
        roughness=0.1,
        metallic=0.95,
        print_temp=200,
        bed_temp=60,
        density=8.5
    ),
    "Bronze": MaterialPreset(
        name="Bronze",
        type=MaterialType.METAL,
        primary_color=(140, 100, 50),
        shininess=0.7,
        roughness=0.3,
        metallic=0.85,
        print_temp=200,
        bed_temp=60,
        density=8.0
    ),
    "Resin Grey": MaterialPreset(
        name="Resin Grey",
        type=MaterialType.RESIN,
        primary_color=(128, 128, 128),
        shininess=0.6,
        roughness=0.2,
        print_temp=0,
        bed_temp=0,
        print_speed=0,
        layer_height=0.05,
        density=1.1
    ),
}


def get_material_names() -> list:
    """Get list of all available material preset names."""
    return list(MATERIAL_PRESETS.keys())


def get_material_preset(name: str) -> MaterialPreset:
    """
    Get a material preset by name.

    Args:
        name: Name of the material preset

    Returns:
        MaterialPreset object, or default PLA White if not found
    """
    return MATERIAL_PRESETS.get(name, MATERIAL_PRESETS["PLA White"])


def get_materials_by_type(material_type: MaterialType) -> Dict[str, MaterialPreset]:
    """
    Get all materials of a specific type.

    Args:
        material_type: Type of material to filter by

    Returns:
        Dictionary of matching materials
    """
    return {
        name: preset
        for name, preset in MATERIAL_PRESETS.items()
        if preset.type == material_type
    }
