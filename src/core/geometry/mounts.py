"""
Mount Generator
Creates mounting features for nameplates (holes, stands, magnet pockets, etc.)
"""

import cadquery as cq
import math
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Tuple


class MountType(Enum):
    """Available mounting types."""
    NONE = "none"
    DESK_STAND = "desk_stand"
    SCREW_HOLES = "screw_holes"
    KEYHOLE = "keyhole"
    MAGNET_POCKETS = "magnet_pockets"
    HANGING_HOLE = "hanging_hole"
    FRENCH_CLEAT = "french_cleat"
    ADHESIVE_RECESS = "adhesive_recess"
    LANYARD_SLOT = "lanyard_slot"
    CLIP_MOUNT = "clip_mount"


class HolePattern(Enum):
    """Screw hole patterns."""
    TWO_TOP = "two_top"
    TWO_SIDES = "two_sides"
    FOUR_CORNERS = "four_corners"
    CENTER_TOP = "center_top"


@dataclass
class MagnetSize:
    """Common magnet sizes."""
    diameter: float
    height: float
    name: str
    
    # Common sizes
    @staticmethod
    def DISC_6x2():
        return MagnetSize(6.0, 2.0, "6x2mm Disc")
    
    @staticmethod
    def DISC_8x3():
        return MagnetSize(8.0, 3.0, "8x3mm Disc")
    
    @staticmethod
    def DISC_10x2():
        return MagnetSize(10.0, 2.0, "10x2mm Disc")
    
    @staticmethod
    def CUBE_5():
        return MagnetSize(5.0, 5.0, "5mm Cube")


@dataclass
class MountConfig:
    """Configuration for mounting features."""
    mount_type: MountType = MountType.NONE
    
    # Desk stand options
    stand_angle: float = 25.0           # degrees
    stand_integrated: bool = True        # Integrated vs separate piece
    stand_depth: float = 30.0           # mm - depth of stand base
    stand_thickness: float = 3.0        # mm
    
    # Screw hole options
    hole_pattern: HolePattern = HolePattern.TWO_TOP
    hole_diameter: float = 4.0          # mm
    hole_countersink: bool = True
    countersink_diameter: float = 8.0   # mm
    countersink_depth: float = 2.0      # mm
    hole_edge_distance: float = 8.0     # mm from edge
    
    # Keyhole options
    keyhole_large_diameter: float = 10.0  # mm
    keyhole_small_diameter: float = 5.0   # mm
    keyhole_length: float = 12.0          # mm
    
    # Magnet options
    magnet_size: MagnetSize = field(default_factory=MagnetSize.DISC_8x3)
    magnet_count: int = 2
    magnet_edge_distance: float = 10.0   # mm from edge
    magnet_tolerance: float = 0.2        # mm - extra space for fit
    
    # Hanging hole options
    hanging_hole_diameter: float = 5.0   # mm
    hanging_hole_position: str = "top_center"  # top_center, corners

    # Lanyard slot options
    lanyard_slot_width: float = 15.0     # mm - length of the slot
    lanyard_slot_height: float = 4.0     # mm - width of the slot opening
    lanyard_slot_position: str = "top_center"  # top_center, top_left, top_right

    # French cleat options
    cleat_angle: float = 45.0           # degrees
    cleat_depth: float = 5.0            # mm
    cleat_width: float = 15.0           # mm

    # Clip mount options
    clip_width: float = 20.0            # mm - width of clip
    clip_thickness: float = 2.0         # mm - material thickness
    clip_gap: float = 3.0               # mm - gap for material to clip onto
    clip_position: str = "back_top"     # back_top, back_bottom, back_both


class MountGenerator:
    """
    Generates mounting features for nameplates.
    """
    
    def __init__(self, config: Optional[MountConfig] = None):
        self.config = config or MountConfig()
    
    def generate(self, plate_width: float, plate_height: float,
                 plate_thickness: float,
                 config: Optional[MountConfig] = None) -> Tuple[Optional[cq.Workplane], Optional[cq.Workplane]]:
        """
        Generate mounting features.

        Args:
            plate_width: Width of the base plate
            plate_height: Height of the base plate
            plate_thickness: Thickness of the base plate
            config: Optional config override

        Returns:
            Tuple of (features_to_add, features_to_subtract)
            Either may be None if not applicable.
        """
        cfg = config or self.config

        print(f"[Mount] Generating mount type: {cfg.mount_type}, plate: {plate_width}x{plate_height}x{plate_thickness}")

        if cfg.mount_type == MountType.NONE:
            print("[Mount] Mount type is NONE, returning None")
            return None, None
        elif cfg.mount_type == MountType.DESK_STAND:
            result = self._make_desk_stand(plate_width, plate_height, plate_thickness, cfg)
            print(f"[Mount] Desk stand result: {result}")
            return result, None
        elif cfg.mount_type == MountType.SCREW_HOLES:
            result = self._make_screw_holes(plate_width, plate_height, plate_thickness, cfg)
            print(f"[Mount] Screw holes result: {result}")
            return None, result
        elif cfg.mount_type == MountType.KEYHOLE:
            result = self._make_keyholes(plate_width, plate_height, plate_thickness, cfg)
            print(f"[Mount] Keyhole result: {result}")
            return None, result
        elif cfg.mount_type == MountType.MAGNET_POCKETS:
            result = self._make_magnet_pockets(plate_width, plate_height, plate_thickness, cfg)
            print(f"[Mount] Magnet pockets result: {result}")
            return None, result
        elif cfg.mount_type == MountType.HANGING_HOLE:
            result = self._make_hanging_holes(plate_width, plate_height, plate_thickness, cfg)
            print(f"[Mount] Hanging holes result: {result}")
            return None, result
        elif cfg.mount_type == MountType.ADHESIVE_RECESS:
            result = self._make_adhesive_recess(plate_width, plate_height, plate_thickness, cfg)
            print(f"[Mount] Adhesive recess result: {result}")
            return None, result
        elif cfg.mount_type == MountType.LANYARD_SLOT:
            result = self._make_lanyard_slot(plate_width, plate_height, plate_thickness, cfg)
            print(f"[Mount] Lanyard slot result: {result}")
            return None, result
        elif cfg.mount_type == MountType.CLIP_MOUNT:
            result = self._make_clip_mount(plate_width, plate_height, plate_thickness, cfg)
            print(f"[Mount] Clip mount result: {result}")
            return result, None  # Clips are added, not subtracted

        print(f"[Mount] Unknown mount type: {cfg.mount_type}")
        return None, None
    
    def _make_desk_stand(self, plate_width: float, plate_height: float,
                         plate_thickness: float, cfg: MountConfig) -> cq.Workplane:
        """Create an integrated desk stand."""
        angle_rad = math.radians(cfg.stand_angle)
        
        # Calculate stand dimensions
        stand_height = cfg.stand_depth * math.sin(angle_rad)
        stand_base = cfg.stand_depth * math.cos(angle_rad)
        
        # Create triangular profile for stand
        # The stand attaches to the back bottom of the plate
        pts = [
            (0, 0),
            (stand_base, 0),
            (0, stand_height)
        ]
        
        # Create the stand shape
        stand = (
            cq.Workplane("XZ")
            .polyline(pts)
            .close()
            .extrude(plate_width * 0.8)  # 80% of plate width
            .translate((0, -plate_width * 0.4, 0))  # Center it
        )
        
        # Rotate and position
        # Stand should be at the back of the plate
        # Add 0.1mm overlap for reliable union with raised text
        stand = stand.translate((0, -plate_height/2 + 0.1, 0))
        
        return stand
    
    def _make_screw_holes(self, plate_width: float, plate_height: float,
                          plate_thickness: float, cfg: MountConfig) -> cq.Workplane:
        """Create screw holes for wall mounting."""
        # Determine hole positions based on pattern
        positions = []
        edge_dist = cfg.hole_edge_distance

        if cfg.hole_pattern == HolePattern.TWO_TOP:
            positions = [
                (-plate_width/2 + edge_dist, plate_height/2 - edge_dist),
                (plate_width/2 - edge_dist, plate_height/2 - edge_dist)
            ]
        elif cfg.hole_pattern == HolePattern.TWO_SIDES:
            positions = [
                (-plate_width/2 + edge_dist, 0),
                (plate_width/2 - edge_dist, 0)
            ]
        elif cfg.hole_pattern == HolePattern.FOUR_CORNERS:
            positions = [
                (-plate_width/2 + edge_dist, plate_height/2 - edge_dist),
                (plate_width/2 - edge_dist, plate_height/2 - edge_dist),
                (-plate_width/2 + edge_dist, -plate_height/2 + edge_dist),
                (plate_width/2 - edge_dist, -plate_height/2 + edge_dist)
            ]
        elif cfg.hole_pattern == HolePattern.CENTER_TOP:
            positions = [(0, plate_height/2 - edge_dist)]

        if not positions:
            return None

        # Create holes - first hole becomes base, others union to it
        # Extend holes well above plate surface to cut through any raised elements (text, borders, SVGs)
        holes = None
        for x, y in positions:
            try:
                # Create main hole cylinder - starts below Z=0 and extends above plate
                # to cut through raised text/borders/SVGs
                main_hole = (
                    cq.Workplane("XY")
                    .center(x, y)
                    .circle(cfg.hole_diameter / 2)
                    .extrude(plate_thickness + 10)  # Extra height for raised elements
                    .translate((0, 0, -0.1))
                )

                if cfg.hole_countersink:
                    # Create countersink - extends above plate for raised elements
                    countersink = (
                        cq.Workplane("XY")
                        .center(x, y)
                        .circle(cfg.countersink_diameter / 2)
                        .extrude(10 + cfg.countersink_depth)  # Extra height for raised elements
                        .translate((0, 0, plate_thickness - cfg.countersink_depth))
                    )
                    hole = main_hole.union(countersink)
                else:
                    hole = main_hole

                if holes is None:
                    holes = hole
                else:
                    holes = holes.union(hole)
            except Exception as e:
                print(f"Error creating screw hole at ({x}, {y}): {e}")

        return holes
    
    def _make_keyholes(self, plate_width: float, plate_height: float,
                       plate_thickness: float, cfg: MountConfig) -> cq.Workplane:
        """Create keyhole slots for wall mounting."""
        # Position keyholes
        positions = [
            (-plate_width/4, plate_height/2 - cfg.hole_edge_distance),
            (plate_width/4, plate_height/2 - cfg.hole_edge_distance)
        ]

        if not positions:
            return None

        holes = None
        for x, y in positions:
            try:
                # Keyhole: large entry hole on top/back, narrow slot goes through
                # Create the narrow slot - extends above plate to cut through raised elements
                slot = (
                    cq.Workplane("XY")
                    .center(x, y - cfg.keyhole_length / 2)
                    .slot2D(cfg.keyhole_length, cfg.keyhole_small_diameter)
                    .extrude(plate_thickness + 10)  # Extra height for raised elements
                    .translate((0, 0, -0.1))
                )

                # Create the large entry hole on the back (Z=0 side)
                # Goes partway through the plate
                large_hole = (
                    cq.Workplane("XY")
                    .center(x, y)
                    .circle(cfg.keyhole_large_diameter / 2)
                    .extrude(plate_thickness / 2 + 0.1)
                    .translate((0, 0, -0.1))
                )

                keyhole = slot.union(large_hole)

                if holes is None:
                    holes = keyhole
                else:
                    holes = holes.union(keyhole)
            except Exception as e:
                print(f"Error creating keyhole at ({x}, {y}): {e}")

        return holes
    
    def _make_magnet_pockets(self, plate_width: float, plate_height: float,
                             plate_thickness: float, cfg: MountConfig) -> cq.Workplane:
        """Create pockets for magnets on the back of the plate."""
        # Determine magnet positions
        positions = []
        edge_dist = cfg.magnet_edge_distance
        magnet_d = cfg.magnet_size.diameter + cfg.magnet_tolerance
        magnet_h = min(cfg.magnet_size.height + cfg.magnet_tolerance, plate_thickness - 0.5)

        if cfg.magnet_count == 2:
            positions = [
                (-plate_width/2 + edge_dist, 0),
                (plate_width/2 - edge_dist, 0)
            ]
        elif cfg.magnet_count == 4:
            positions = [
                (-plate_width/2 + edge_dist, plate_height/2 - edge_dist),
                (plate_width/2 - edge_dist, plate_height/2 - edge_dist),
                (-plate_width/2 + edge_dist, -plate_height/2 + edge_dist),
                (plate_width/2 - edge_dist, -plate_height/2 + edge_dist)
            ]

        if not positions:
            return None

        # Create cylindrical pockets on the back (Z=0 side)
        pockets = None
        for x, y in positions:
            try:
                pocket = (
                    cq.Workplane("XY")
                    .center(x, y)
                    .circle(magnet_d / 2)
                    .extrude(magnet_h + 0.1)
                    .translate((0, 0, -0.1))
                )
                if pockets is None:
                    pockets = pocket
                else:
                    pockets = pockets.union(pocket)
            except Exception as e:
                print(f"Error creating magnet pocket at ({x}, {y}): {e}")

        return pockets
    
    def _make_hanging_holes(self, plate_width: float, plate_height: float,
                            plate_thickness: float, cfg: MountConfig) -> cq.Workplane:
        """Create simple hanging holes."""
        positions = []

        if cfg.hanging_hole_position == "top_center":
            positions = [(0, plate_height/2 - cfg.hole_edge_distance)]
        elif cfg.hanging_hole_position in ("corners", "top_corners"):
            positions = [
                (-plate_width/2 + cfg.hole_edge_distance, plate_height/2 - cfg.hole_edge_distance),
                (plate_width/2 - cfg.hole_edge_distance, plate_height/2 - cfg.hole_edge_distance)
            ]

        if not positions:
            return None

        # Create holes - first becomes base, others union to it
        # Extend above plate to cut through raised elements
        holes = None
        for x, y in positions:
            try:
                hole = (
                    cq.Workplane("XY")
                    .center(x, y)
                    .circle(cfg.hanging_hole_diameter / 2)
                    .extrude(plate_thickness + 10)  # Extra height for raised elements
                    .translate((0, 0, -0.1))
                )
                if holes is None:
                    holes = hole
                else:
                    holes = holes.union(hole)
            except Exception as e:
                print(f"Error creating hanging hole at ({x}, {y}): {e}")

        return holes
    
    def _make_adhesive_recess(self, plate_width: float, plate_height: float,
                              plate_thickness: float, cfg: MountConfig) -> cq.Workplane:
        """Create a recess on the back for adhesive strips."""
        # Create rectangular recesses for adhesive strips
        recess_width = plate_width * 0.7
        recess_height = 15.0  # Standard adhesive strip width
        recess_depth = 1.0    # Shallow recess

        try:
            recess = (
                cq.Workplane("XY")
                .rect(recess_width, recess_height)
                .extrude(recess_depth + 0.1)
                .translate((0, 0, -0.1))
            )
            return recess
        except Exception as e:
            print(f"Error creating adhesive recess: {e}")
            return None

    def _make_lanyard_slot(self, plate_width: float, plate_height: float,
                           plate_thickness: float, cfg: MountConfig) -> cq.Workplane:
        """Create an elongated slot for lanyard attachment."""
        # Determine slot position
        positions = []
        edge_dist = cfg.hole_edge_distance

        if cfg.lanyard_slot_position == "top_center":
            positions = [(0, plate_height / 2 - edge_dist)]
        elif cfg.lanyard_slot_position == "top_left":
            positions = [(-plate_width / 4, plate_height / 2 - edge_dist)]
        elif cfg.lanyard_slot_position == "top_right":
            positions = [(plate_width / 4, plate_height / 2 - edge_dist)]
        elif cfg.lanyard_slot_position == "both_sides":
            positions = [
                (-plate_width / 4, plate_height / 2 - edge_dist),
                (plate_width / 4, plate_height / 2 - edge_dist)
            ]

        if not positions:
            return None

        slots = None
        for x, y in positions:
            try:
                # Create stadium/slot shape (rounded rectangle)
                # slot2D creates a slot with rounded ends
                slot = (
                    cq.Workplane("XY")
                    .center(x, y)
                    .slot2D(cfg.lanyard_slot_width, cfg.lanyard_slot_height)
                    .extrude(plate_thickness + 10)  # Extra height for raised elements
                    .translate((0, 0, -0.1))
                )

                if slots is None:
                    slots = slot
                else:
                    slots = slots.union(slot)
            except Exception as e:
                print(f"Error creating lanyard slot at ({x}, {y}): {e}")

        return slots

    def _make_clip_mount(self, plate_width: float, plate_height: float,
                         plate_thickness: float, cfg: MountConfig) -> cq.Workplane:
        """Create spring clip attachments on the back of the plate."""
        # Clip profile: C-shaped bracket that can clip onto a surface
        # The clip extends from the back of the plate

        positions = []
        if cfg.clip_position in ("back_top", "back_both"):
            positions.append((0, plate_height / 2 - cfg.clip_width / 2 - 5, "top"))
        if cfg.clip_position in ("back_bottom", "back_both"):
            positions.append((0, -plate_height / 2 + cfg.clip_width / 2 + 5, "bottom"))

        if not positions:
            return None

        clips = None
        for x, y, pos_type in positions:
            try:
                # Create C-shaped clip profile
                # The clip has a back plate, a gap, and a spring arm
                clip_depth = cfg.clip_gap + cfg.clip_thickness * 2
                arm_length = cfg.clip_gap + cfg.clip_thickness

                # Back mounting plate
                back = (
                    cq.Workplane("XY")
                    .rect(cfg.clip_width, cfg.clip_thickness)
                    .extrude(clip_depth)
                    .translate((x, y, -clip_depth))
                )

                # Bottom/base of clip
                base = (
                    cq.Workplane("XY")
                    .rect(cfg.clip_width, arm_length)
                    .extrude(cfg.clip_thickness)
                    .translate((x, y - arm_length / 2 + cfg.clip_thickness / 2, -clip_depth))
                )

                # Spring arm (angled slightly inward for grip)
                arm_points = [
                    (0, 0),
                    (cfg.clip_thickness, 0),
                    (cfg.clip_thickness * 0.7, clip_depth * 0.8),
                    (0, clip_depth * 0.9),
                ]
                arm = (
                    cq.Workplane("XZ")
                    .polyline(arm_points)
                    .close()
                    .extrude(cfg.clip_width)
                    .translate((x - cfg.clip_width / 2, y - arm_length + cfg.clip_thickness, -clip_depth))
                )

                clip = back.union(base).union(arm)

                if clips is None:
                    clips = clip
                else:
                    clips = clips.union(clip)

            except Exception as e:
                print(f"Error creating clip mount at ({x}, {y}): {e}")

        return clips


def get_common_magnet_sizes() -> List[MagnetSize]:
    """Get list of common magnet sizes."""
    return [
        MagnetSize(6.0, 2.0, "6x2mm Disc"),
        MagnetSize(8.0, 3.0, "8x3mm Disc"),
        MagnetSize(10.0, 2.0, "10x2mm Disc"),
        MagnetSize(10.0, 3.0, "10x3mm Disc"),
        MagnetSize(12.0, 2.0, "12x2mm Disc"),
        MagnetSize(5.0, 5.0, "5mm Cube"),
        MagnetSize(10.0, 10.0, "10mm Cube"),
    ]
