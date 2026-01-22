"""
Config Builder
Extracts configuration building logic from MainWindow for better separation of concerns.
"""

from typing import Optional, TYPE_CHECKING

from core.nameplate import NameplateConfig
from core.geometry.text_builder import (
    TextLineConfig, TextSegment, TextStyle, TextAlign, TextOrientation, TextEffect
)
from core.geometry.base_plates import PlateShape, EdgeStyle
from core.geometry.borders import BorderStyle
from core.geometry.patterns import PatternType
from core.geometry.mounts import MountType, HolePattern, MagnetSize

if TYPE_CHECKING:
    from ui.panels.text_panel import TextPanel
    from ui.panels.base_panel import BasePlatePanel
    from ui.panels.mount_panel import MountPanel
    from ui.panels.svg_panel import SVGPanel
    from fonts.font_manager import FontManager


class ConfigBuilder:
    """
    Builds NameplateConfig from UI panel states.

    Extracts configuration building logic from MainWindow to improve
    testability and separation of concerns.
    """

    def __init__(self, font_manager: 'FontManager'):
        """
        Initialize the ConfigBuilder.

        Args:
            font_manager: FontManager instance for resolving font paths.
        """
        self._font_manager = font_manager

    def build(
        self,
        text_panel: 'TextPanel',
        base_panel: 'BasePlatePanel',
        mount_panel: 'MountPanel',
        svg_panel: 'SVGPanel'
    ) -> NameplateConfig:
        """
        Build a complete NameplateConfig from UI panel states.

        Args:
            text_panel: Text configuration panel.
            base_panel: Base plate configuration panel.
            mount_panel: Mount configuration panel.
            svg_panel: SVG elements panel.

        Returns:
            Complete NameplateConfig with all settings.
        """
        config = NameplateConfig()

        # Build each section
        self._build_text_config(config, text_panel.get_config())
        self._build_plate_config(config, base_panel.get_config())
        self._build_mount_config(config, mount_panel.get_config())
        self._build_svg_config(config, svg_panel)

        return config

    def _build_text_config(self, config: NameplateConfig, text_cfg: dict) -> None:
        """Build text configuration from panel config dict."""
        config.text.lines = []

        for line_data in text_cfg.get('lines', []):
            # Build segments if present
            segments = []
            segments_data = line_data.get('segments', [])

            if segments_data:
                for seg_data in segments_data:
                    seg = TextSegment(
                        content=seg_data.get('content', ''),
                        font_family=seg_data.get('font_family', 'Arial'),
                        font_style=seg_data.get('font_style', 'Regular'),
                        font_size=seg_data.get('font_size', 12.0),
                        letter_spacing=seg_data.get('letter_spacing', 0.0),
                        vertical_offset=seg_data.get('vertical_offset', 0.0),
                        is_icon=seg_data.get('is_icon', False),
                    )
                    # Get font path for this segment
                    font_path = self._font_manager.get_font_path(
                        seg.font_family, seg.font_style
                    )
                    if font_path:
                        seg.font_path = font_path
                    segments.append(seg)

            line = TextLineConfig(
                content=line_data.get('content', ''),
                font_family=line_data.get('font_family', 'Arial'),
                font_style=line_data.get('font_style', 'Regular'),
                font_size=line_data.get('font_size', 12.0),
                letter_spacing=line_data.get('letter_spacing', 0.0),
                segments=segments,
                segment_gap=line_data.get('segment_gap', 2.0),
            )

            # Get font path for legacy content (if no segments)
            if not segments:
                font_path = self._font_manager.get_font_path(
                    line.font_family, line.font_style
                )
                if font_path:
                    line.font_path = font_path

            config.text.lines.append(line)

        # Text style settings
        config.text.style = TextStyle(text_cfg.get('style', 'raised'))
        config.text.depth = text_cfg.get('depth', 2.0)
        config.text.line_spacing = text_cfg.get('line_spacing', 1.2)
        config.text.halign = TextAlign(text_cfg.get('halign', 'center'))
        config.text.orientation = TextOrientation(text_cfg.get('orientation', 'horizontal'))
        config.text.effect = TextEffect(text_cfg.get('effect', 'none'))
        config.text.effect_size = text_cfg.get('effect_size', 0.3)

        # Arc text settings
        config.text.arc_enabled = text_cfg.get('arc_enabled', False)
        config.text.arc_radius = text_cfg.get('arc_radius', 50.0)
        config.text.arc_angle = text_cfg.get('arc_angle', 180.0)
        config.text.arc_direction = text_cfg.get('arc_direction', 'counterclockwise')

    def _build_plate_config(self, config: NameplateConfig, base_cfg: dict) -> None:
        """Build plate configuration from panel config dict."""
        plate = base_cfg.get('plate', {})

        # Basic plate settings
        config.plate.shape = PlateShape(plate.get('shape', 'rounded_rectangle'))
        config.plate.width = plate.get('width', 120.0)
        config.plate.height = plate.get('height', 35.0)
        config.plate.thickness = plate.get('thickness', 4.0)
        config.plate.corner_radius = plate.get('corner_radius', 5.0)

        # Auto-sizing
        config.plate.auto_width = plate.get('auto_width', False)
        config.plate.auto_height = plate.get('auto_height', False)

        # Padding
        config.plate.padding_top = plate.get('padding_top', 5.0)
        config.plate.padding_bottom = plate.get('padding_bottom', 5.0)
        config.plate.padding_left = plate.get('padding_left', 10.0)
        config.plate.padding_right = plate.get('padding_right', 10.0)

        # Edge finishing
        config.plate.edge_style = EdgeStyle(plate.get('edge_style', 'none'))
        config.plate.edge_size = plate.get('edge_size', 0.5)
        config.plate.edge_top_only = plate.get('edge_top_only', True)

        # Layered plate
        config.plate.layered_enabled = plate.get('layered_enabled', False)
        config.plate.layer_count = plate.get('layer_count', 2)
        config.plate.layer_offset = plate.get('layer_offset', 2.0)
        config.plate.layer_shrink = plate.get('layer_shrink', 3.0)

        # Inset panel
        config.plate.inset_enabled = plate.get('inset_enabled', False)
        config.plate.inset_depth = plate.get('inset_depth', 1.0)
        config.plate.inset_margin = plate.get('inset_margin', 5.0)
        config.plate.inset_corner_radius = plate.get('inset_corner_radius', 3.0)

        # Sweeping plate settings
        sweep = base_cfg.get('sweeping', {})
        config.sweeping.width = sweep.get('width', 120.0)
        config.sweeping.height = sweep.get('height', 35.0)
        config.sweeping.thickness = sweep.get('thickness', 4.0)
        config.sweeping.curve_angle = sweep.get('curve_angle', 45.0)
        config.sweeping.curve_radius = sweep.get('curve_radius', 80.0)
        config.sweeping.base_type = sweep.get('base_type', 'pedestal')

        # Border settings
        border = base_cfg.get('border', {})
        config.border.enabled = border.get('enabled', False)
        config.border.style = BorderStyle(border.get('style', 'raised'))
        config.border.width = border.get('width', 3.0)
        config.border.height = border.get('height', 1.5)
        config.border.offset = border.get('offset', 2.0)

        # Pattern settings
        pattern = base_cfg.get('pattern', {})
        config.pattern.pattern_type = PatternType(pattern.get('type', 'none'))
        config.pattern.spacing = pattern.get('spacing', 5.0)
        config.pattern.size = pattern.get('size', 1.0)
        config.pattern.depth = pattern.get('depth', 0.3)

    def _build_mount_config(self, config: NameplateConfig, mount_cfg: dict) -> None:
        """Build mount configuration from panel config dict."""
        config.mount.mount_type = MountType(mount_cfg.get('type', 'none'))

        # Desk stand options
        config.mount.stand_angle = mount_cfg.get('stand_angle', 25.0)
        config.mount.stand_depth = mount_cfg.get('stand_depth', 30.0)
        config.mount.stand_integrated = mount_cfg.get('stand_integrated', True)

        # Screw hole options
        pattern_map = {
            'two_top': HolePattern.TWO_TOP,
            'two_sides': HolePattern.TWO_SIDES,
            'four_corners': HolePattern.FOUR_CORNERS,
            'center_top': HolePattern.CENTER_TOP,
        }
        config.mount.hole_pattern = pattern_map.get(
            mount_cfg.get('hole_pattern', 'two_top'),
            HolePattern.TWO_TOP
        )
        config.mount.hole_diameter = mount_cfg.get('hole_diameter', 4.0)
        config.mount.hole_countersink = mount_cfg.get('countersink', True)
        config.mount.hole_edge_distance = mount_cfg.get('hole_edge_distance', 8.0)

        # Keyhole options
        config.mount.keyhole_large_diameter = mount_cfg.get('keyhole_large', 10.0)
        config.mount.keyhole_small_diameter = mount_cfg.get('keyhole_small', 5.0)
        config.mount.keyhole_length = mount_cfg.get('keyhole_length', 12.0)

        # Magnet options - parse size string like "8x3mm Disc"
        magnet_size_str = mount_cfg.get('magnet_size', '8x3mm Disc')
        magnet_diameter = 8.0
        magnet_height = 3.0
        if 'x' in magnet_size_str:
            try:
                parts = magnet_size_str.split('x')
                magnet_diameter = float(parts[0])
                magnet_height = float(parts[1].replace('mm', '').replace(' Disc', '').replace(' Cube', ''))
            except:
                pass
        config.mount.magnet_size = MagnetSize(magnet_diameter, magnet_height, magnet_size_str)
        config.mount.magnet_count = mount_cfg.get('magnet_count', 2)
        config.mount.magnet_edge_distance = mount_cfg.get('magnet_edge', 10.0)

        # Hanging hole options
        config.mount.hanging_hole_diameter = mount_cfg.get('hanging_diameter', 5.0)
        config.mount.hanging_hole_position = mount_cfg.get('hanging_position', 'top_center')

        # Lanyard slot options
        config.mount.lanyard_slot_width = mount_cfg.get('lanyard_width', 15.0)
        config.mount.lanyard_slot_height = mount_cfg.get('lanyard_height', 4.0)
        config.mount.lanyard_slot_position = mount_cfg.get('lanyard_position', 'top_center')

        # Clip mount options
        config.mount.clip_width = mount_cfg.get('clip_width', 20.0)
        config.mount.clip_thickness = mount_cfg.get('clip_thickness', 2.0)
        config.mount.clip_gap = mount_cfg.get('clip_gap', 3.0)
        config.mount.clip_position = mount_cfg.get('clip_position', 'back_top')

    def _build_svg_config(self, config: NameplateConfig, svg_panel: 'SVGPanel') -> None:
        """Build SVG and QR configuration from panel."""
        config.svg_elements = svg_panel.get_elements()
        config.qr_elements = svg_panel.get_qr_elements()
