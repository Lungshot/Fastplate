"""
Nameplate Builder
Main class that combines all geometry components to create complete nameplates.
"""

import cadquery as cq
from dataclasses import dataclass, field
from typing import Optional, Tuple, List
from pathlib import Path

from .geometry.base_plates import BasePlateGenerator, PlateConfig, PlateShape, EdgeStyle
from .geometry.text_builder import TextBuilder, TextConfig, TextStyle, TextLineConfig, TextSegment
from .geometry.borders import BorderGenerator, BorderConfig, BorderStyle
from .geometry.patterns import PatternGenerator, PatternConfig, PatternType
from .geometry.mounts import MountGenerator, MountConfig, MountType
from .geometry.sweeping import SweepingPlateGenerator, SweepingConfig
from .geometry.svg_importer import SVGImporter, SVGElement
from .geometry.qr_generator import QRCodeGenerator, QRConfig, QRStyle
from .geometry.shape_utils import (
    extract_solids_recursive,
    union_solids_from_compound,
    cut_solids_from_compound,
)
from .export.exporter import Exporter, ExportOptions, ExportFormat
from utils.debug_log import debug_log


@dataclass
class NameplateConfig:
    """Complete configuration for a nameplate."""
    # Plate settings
    plate: PlateConfig = field(default_factory=PlateConfig)
    
    # Sweeping settings (used when plate.shape == SWEEPING)
    sweeping: SweepingConfig = field(default_factory=SweepingConfig)
    
    # Text settings
    text: TextConfig = field(default_factory=TextConfig)
    
    # Border settings
    border: BorderConfig = field(default_factory=BorderConfig)

    # Pattern settings
    pattern: PatternConfig = field(default_factory=PatternConfig)

    # Mount settings
    mount: MountConfig = field(default_factory=MountConfig)
    
    # Icons (Nerd Fonts)
    icons: List[dict] = field(default_factory=list)  # List of icon configs

    # SVG elements
    svg_elements: List[SVGElement] = field(default_factory=list)

    # QR code elements
    qr_elements: List[QRConfig] = field(default_factory=list)

    # Metadata
    name: str = "Untitled"
    
    def to_dict(self) -> dict:
        """Convert config to dictionary for serialization."""
        return {
            'name': self.name,
            'plate': self.plate.to_dict(),
            'sweeping': self.sweeping.to_dict(),
            'text': self.text.to_dict(),
            'border': self.border.to_dict(),
            'pattern': self.pattern.to_dict(),
            'mount': self.mount.to_dict(),
            'icons': self.icons,
            'svg_elements': [elem.to_dict() for elem in self.svg_elements],
            'qr_elements': [qr.to_dict() for qr in self.qr_elements] if self.qr_elements else [],
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'NameplateConfig':
        """Create config from dictionary. Handles both new and legacy formats."""
        config = cls()

        if 'name' in data:
            config.name = data['name']

        # Plate config - delegate to PlateConfig.from_dict
        if 'plate' in data:
            config.plate = PlateConfig.from_dict(data['plate'])

        # Sweeping config - delegate to SweepingConfig.from_dict
        if 'sweeping' in data:
            config.sweeping = SweepingConfig.from_dict(data['sweeping'])

        # Text config - delegate to TextConfig.from_dict
        if 'text' in data:
            config.text = TextConfig.from_dict(data['text'])

        # Border config - delegate to BorderConfig.from_dict
        if 'border' in data:
            config.border = BorderConfig.from_dict(data['border'])

        # Pattern config - handle legacy 'type' key vs new 'pattern_type'
        if 'pattern' in data:
            pat = data['pattern']
            # Convert legacy 'type' key to 'pattern_type' for backward compatibility
            if 'type' in pat and 'pattern_type' not in pat:
                pat = dict(pat)  # Copy to avoid modifying original
                pat['pattern_type'] = pat.pop('type')
            config.pattern = PatternConfig.from_dict(pat)

        # Mount config - handle legacy 'type' key vs new 'mount_type'
        if 'mount' in data:
            m = data['mount']
            # Convert legacy 'type' key to 'mount_type' for backward compatibility
            if 'type' in m and 'mount_type' not in m:
                m = dict(m)  # Copy to avoid modifying original
                m['mount_type'] = m.pop('type')
            config.mount = MountConfig.from_dict(m)

        if 'icons' in data:
            config.icons = data['icons']

        # SVG elements - delegate to SVGElement.from_dict
        if 'svg_elements' in data:
            config.svg_elements = [
                SVGElement.from_dict(elem_data) for elem_data in data['svg_elements']
            ]

        # QR elements - delegate to QRConfig.from_dict if available
        if 'qr_elements' in data:
            config.qr_elements = [
                QRConfig.from_dict(qr_data) for qr_data in data['qr_elements']
            ]

        return config


class NameplateBuilder:
    """
    Main builder class that creates complete nameplate geometry.
    """
    
    def __init__(self, config: Optional[NameplateConfig] = None):
        self.config = config or NameplateConfig()
        
        # Component generators
        self._plate_gen = BasePlateGenerator()
        self._sweeping_gen = SweepingPlateGenerator()
        self._text_gen = TextBuilder()
        self._border_gen = BorderGenerator()
        self._pattern_gen = PatternGenerator()
        self._mount_gen = MountGenerator()
        self._svg_importer = SVGImporter()
        self._qr_generator = QRCodeGenerator()
        self._exporter = Exporter()
        
        # Generated geometry cache
        self._base_geometry: Optional[cq.Workplane] = None
        self._text_geometry: Optional[cq.Workplane] = None
        self._border_geometry: Optional[cq.Workplane] = None
        self._combined_geometry: Optional[cq.Workplane] = None
        self._needs_rebuild = True

        # SVG geometry cache - caches SVG shapes by content (not position)
        # This dramatically speeds up position/rotation changes
        self._svg_geometry_cache: Dict[str, cq.Workplane] = {}
    
    def set_config(self, config: NameplateConfig) -> None:
        """Set the configuration and mark for rebuild."""
        self.config = config
        self._needs_rebuild = True

    def _get_svg_cache_key(self, svg_elem, target_size: float, depth: float) -> str:
        """Create cache key for SVG geometry based on content (not position)."""
        import hashlib
        key_parts = [
            str(getattr(svg_elem, 'name', '')),
            str(hash(str(getattr(svg_elem, 'paths', [])))),
            f"size:{target_size:.2f}",
            f"depth:{depth:.2f}",
        ]
        return hashlib.md5('|'.join(key_parts).encode()).hexdigest()[:16]

    def _get_cached_svg_geometry(self, svg_elem, target_size: float, depth: float = None):
        """Get cached SVG geometry or create and cache it.

        Note: CadQuery's .translate()/.rotate() return NEW Workplanes with
        transformed geometry copies, so cached geometry is safe to reuse.
        """
        actual_depth = depth if depth is not None else getattr(svg_elem, 'depth', 2.0)
        cache_key = self._get_svg_cache_key(svg_elem, target_size, actual_depth)

        if cache_key in self._svg_geometry_cache:
            debug_log.debug(f"SVG cache HIT: {cache_key}")
            return self._svg_geometry_cache[cache_key]

        debug_log.debug(f"SVG cache MISS: {cache_key}, generating...")
        geometry = self._svg_importer.create_geometry(
            svg_elem,
            target_size=target_size,
            depth=actual_depth
        )

        if geometry is not None:
            self._svg_geometry_cache[cache_key] = geometry

        return geometry

    def _generate_text(self, cfg: NameplateConfig) -> Tuple[Optional[cq.Workplane], Tuple[float, float, float, float]]:
        """
        Generate text geometry based on config.

        Args:
            cfg: Nameplate configuration

        Returns:
            Tuple of (text_geometry, text_bbox)
        """
        debug_log.debug("Generating text geometry...")
        print(f"[Nameplate] Generating text: arc_enabled={cfg.text.arc_enabled}, style={cfg.text.style}")

        text_geometry, text_bbox = self._text_gen.generate(cfg.text)
        print(f"[Nameplate] Text geometry: {text_geometry is not None}, bbox={text_bbox}")

        debug_log.log_geometry("TEXT_GENERATED", {"bbox": str(text_bbox) if text_bbox else "None"})
        return text_geometry, text_bbox

    def _generate_base(
        self,
        cfg: NameplateConfig,
        text_bbox: Tuple[float, float, float, float]
    ) -> Tuple[cq.Workplane, Tuple[float, float, float]]:
        """
        Generate base plate geometry and handle auto-sizing.

        Args:
            cfg: Nameplate configuration
            text_bbox: Text bounding box for auto-sizing

        Returns:
            Tuple of (base_geometry, (plate_width, plate_height, plate_thickness))
        """
        # Generate base plate
        if cfg.plate.shape == PlateShape.SWEEPING:
            base_geometry = self._sweeping_gen.generate(cfg.sweeping)
            plate_width = cfg.sweeping.width
            plate_height = cfg.sweeping.height
            plate_thickness = cfg.sweeping.thickness
        else:
            base_geometry = self._plate_gen.generate(cfg.plate)
            plate_width = cfg.plate.width
            plate_height = cfg.plate.height
            plate_thickness = cfg.plate.thickness

        # Handle auto-sizing
        if cfg.plate.auto_width or cfg.plate.auto_height:
            combined_bbox = list(text_bbox)

            # Expand bbox to include SVG elements
            for svg_elem in cfg.svg_elements:
                target_size = getattr(svg_elem, 'target_size', 20.0)
                half_size = target_size / 2
                svg_min_x = svg_elem.position_x - half_size
                svg_max_x = svg_elem.position_x + half_size
                svg_min_y = svg_elem.position_y - half_size
                svg_max_y = svg_elem.position_y + half_size

                combined_bbox[0] = min(combined_bbox[0], svg_min_x)
                combined_bbox[1] = min(combined_bbox[1], svg_min_y)
                combined_bbox[2] = max(combined_bbox[2], svg_max_x)
                combined_bbox[3] = max(combined_bbox[3], svg_max_y)

            new_width, new_height = self._plate_gen.calculate_auto_size(
                tuple(combined_bbox), cfg.plate
            )
            if cfg.plate.auto_width:
                cfg.plate.width = new_width
                plate_width = new_width
            if cfg.plate.auto_height:
                cfg.plate.height = new_height
                plate_height = new_height

            # Regenerate base with new size
            if cfg.plate.shape != PlateShape.SWEEPING:
                base_geometry = self._plate_gen.generate(cfg.plate)

        return base_geometry, (plate_width, plate_height, plate_thickness)

    def _apply_border_and_pattern(
        self,
        base: cq.Workplane,
        cfg: NameplateConfig,
        plate_dims: Tuple[float, float, float]
    ) -> cq.Workplane:
        """
        Apply border and pattern to base geometry.

        Args:
            base: Base plate geometry
            cfg: Nameplate configuration
            plate_dims: (width, height, thickness) tuple

        Returns:
            Geometry with border and pattern applied
        """
        plate_width, plate_height, plate_thickness = plate_dims
        result = base

        # Generate and apply border
        print(f"[Border] Generating border: enabled={cfg.border.enabled}, style={cfg.border.style}")
        border_geometry = self._border_gen.generate(
            plate_width, plate_height, plate_thickness, cfg.border
        )
        # Store for real-time preview access
        self._border_geometry = border_geometry
        print(f"[Border] Border geometry: {border_geometry is not None}")

        if border_geometry is not None:
            if cfg.border.style == BorderStyle.INSET:
                result = result.cut(border_geometry)
            else:
                result = result.union(border_geometry)

        # Generate and apply pattern
        print(f"[Pattern] Generating pattern: type={cfg.pattern.pattern_type}")
        pattern_geometry = self._pattern_gen.generate(
            cfg.pattern, plate_width, plate_height, plate_thickness
        )
        print(f"[Pattern] Pattern geometry: {pattern_geometry is not None}")

        if pattern_geometry is not None:
            result = result.cut(pattern_geometry)

        return result

    def _apply_text(
        self,
        result: cq.Workplane,
        text_geometry: Optional[cq.Workplane],
        cfg: NameplateConfig,
        plate_thickness: float
    ) -> cq.Workplane:
        """
        Apply text geometry to the plate based on text style.

        Args:
            result: Current result geometry
            text_geometry: Text geometry to apply
            cfg: Nameplate configuration
            plate_thickness: Plate thickness

        Returns:
            Geometry with text applied
        """
        # Check if text has actual geometry
        text_has_geometry = False
        if text_geometry is not None:
            try:
                val = text_geometry.val()
                debug_log.debug(f"Text geometry val type: {type(val).__name__}")
                print(f"[Nameplate] Text geometry val type: {type(val).__name__}")
                bb = val.BoundingBox()
                text_has_geometry = (bb.xmax - bb.xmin) > 0.001 or (bb.ymax - bb.ymin) > 0.001
                debug_log.debug(f"Text geometry bbox: x={bb.xmin:.2f} to {bb.xmax:.2f}, y={bb.ymin:.2f} to {bb.ymax:.2f}, has_geometry={text_has_geometry}")
                print(f"[Nameplate] Text geometry bbox: x={bb.xmin:.2f} to {bb.xmax:.2f}, y={bb.ymin:.2f} to {bb.ymax:.2f}, has_geometry={text_has_geometry}")
            except Exception as e:
                debug_log.debug(f"Text geometry bbox check failed: {e}")
                print(f"[Nameplate] Text geometry bbox check FAILED: {e}")
                try:
                    text_has_geometry = len(text_geometry.solids().vals()) > 0
                    debug_log.debug(f"Fallback solids check: {text_has_geometry}")
                    print(f"[Nameplate] Fallback solids check: {text_has_geometry}")
                except Exception as e2:
                    debug_log.debug(f"Fallback solids check failed: {e2}")
                    print(f"[Nameplate] Fallback solids check FAILED: {e2}")

        if not text_has_geometry:
            return result

        text_z = plate_thickness
        text_y = 0

        if cfg.text.style == TextStyle.RAISED:
            text_positioned = text_geometry.translate((0, text_y, text_z - 0.1))
            result = union_solids_from_compound(result, text_positioned)
        elif cfg.text.style == TextStyle.ENGRAVED:
            result = self._apply_engraved_text(result, cfg, plate_thickness)
            self._text_geometry = None  # Clear - now part of combined geometry
        elif cfg.text.style == TextStyle.CUTOUT:
            result = self._apply_cutout_text(result, cfg, plate_thickness)
            self._text_geometry = None  # Clear - now part of combined geometry

        return result

    def _apply_engraved_text(
        self,
        result: cq.Workplane,
        cfg: NameplateConfig,
        plate_thickness: float
    ) -> cq.Workplane:
        """Apply engraved text to the plate."""
        from .geometry.text_builder import TextBuilder, TextConfig
        engrave_cfg = TextConfig()
        engrave_cfg.lines = cfg.text.lines
        engrave_cfg.halign = cfg.text.halign
        engrave_cfg.valign = cfg.text.valign
        engrave_cfg.line_spacing = cfg.text.line_spacing
        engrave_cfg.orientation = cfg.text.orientation
        engrave_cfg.offset_x = cfg.text.offset_x
        engrave_cfg.offset_y = cfg.text.offset_y
        engrave_cfg.depth = cfg.text.depth + 10

        engrave_text, _ = TextBuilder().generate(engrave_cfg)
        if engrave_text is not None:
            text_engraved = engrave_text.translate((0, 0, plate_thickness - cfg.text.depth))
            result = cut_solids_from_compound(result, text_engraved)

        return result

    def _apply_cutout_text(
        self,
        result: cq.Workplane,
        cfg: NameplateConfig,
        plate_thickness: float
    ) -> cq.Workplane:
        """Apply cutout text to the plate."""
        from .geometry.text_builder import TextBuilder, TextConfig
        cutout_cfg = TextConfig()
        cutout_cfg.lines = cfg.text.lines
        cutout_cfg.halign = cfg.text.halign
        cutout_cfg.valign = cfg.text.valign
        cutout_cfg.line_spacing = cfg.text.line_spacing
        cutout_cfg.orientation = cfg.text.orientation
        cutout_cfg.offset_x = cfg.text.offset_x
        cutout_cfg.offset_y = cfg.text.offset_y
        cutout_cfg.depth = plate_thickness + 12

        cutout_text, _ = TextBuilder().generate(cutout_cfg)
        if cutout_text is not None:
            text_cutout = cutout_text.translate((0, 0, -1.0))
            result = cut_solids_from_compound(result, text_cutout)

        return result

    def _apply_mounts(
        self,
        result: cq.Workplane,
        cfg: NameplateConfig,
        plate_dims: Tuple[float, float, float]
    ) -> cq.Workplane:
        """Apply mount features to the plate."""
        plate_width, plate_height, plate_thickness = plate_dims

        mount_add, mount_subtract = self._mount_gen.generate(
            plate_width, plate_height, plate_thickness, cfg.mount
        )

        debug_log.debug(f"Mount features: add={mount_add is not None}, subtract={mount_subtract is not None}")

        if mount_add is not None:
            debug_log.debug("Applying mount_add via union")
            result = result.union(mount_add)

        if mount_subtract is not None:
            debug_log.debug("Applying mount_subtract via cut")
            try:
                # Pre-fuse solids before cutting
                try:
                    result_val = result.val()
                    all_result_solids = []
                    extract_solids_recursive(result_val, all_result_solids)

                    if len(all_result_solids) > 1:
                        debug_log.debug(f"Fusing {len(all_result_solids)} solids before mount cut")
                        fused = cq.Workplane("XY").newObject([cq.Shape(all_result_solids[0])])
                        for i, solid in enumerate(all_result_solids[1:]):
                            try:
                                solid_wp = cq.Workplane("XY").newObject([cq.Shape(solid)])
                                fused = fused.union(solid_wp)
                            except Exception as e:
                                debug_log.debug(f"Failed to fuse solid {i+1}: {e}")
                        result = fused
                except Exception as e:
                    debug_log.debug(f"Pre-cut fusion failed: {e}, proceeding with original result")

                result = result.cut(mount_subtract)
            except Exception as e:
                debug_log.debug(f"Mount cut failed: {e}")

        return result

    def _apply_svg_elements(
        self,
        result: cq.Workplane,
        cfg: NameplateConfig,
        plate_thickness: float
    ) -> cq.Workplane:
        """Apply SVG elements to the plate."""
        for svg_elem in cfg.svg_elements:
            target_size = getattr(svg_elem, 'target_size', 20.0)
            svg_geometry = self._get_cached_svg_geometry(svg_elem, target_size)

            if svg_geometry is None:
                continue

            svg_positioned = svg_geometry.translate((
                svg_elem.position_x,
                svg_elem.position_y,
                0
            ))

            if svg_elem.rotation != 0:
                svg_positioned = svg_positioned.rotate(
                    (0, 0, 0), (0, 0, 1), svg_elem.rotation
                )

            if svg_elem.style == "raised":
                svg_final = svg_positioned.translate((0, 0, plate_thickness - 0.1))
                result = union_solids_from_compound(result, svg_final)
            elif svg_elem.style == "engraved":
                svg_engrave = self._get_cached_svg_geometry(
                    svg_elem, target_size, depth=svg_elem.depth + 10
                )
                if svg_engrave is not None:
                    svg_engrave = svg_engrave.translate((
                        svg_elem.position_x,
                        svg_elem.position_y,
                        0
                    ))
                    if svg_elem.rotation != 0:
                        svg_engrave = svg_engrave.rotate(
                            (0, 0, 0), (0, 0, 1), svg_elem.rotation
                        )
                    svg_final = svg_engrave.translate((0, 0, plate_thickness - svg_elem.depth))
                    result = result.cut(svg_final)
            elif svg_elem.style == "cutout":
                svg_cutout = self._get_cached_svg_geometry(
                    svg_elem, target_size, depth=plate_thickness + 10
                )
                if svg_cutout is not None:
                    svg_cutout = svg_cutout.translate((
                        svg_elem.position_x,
                        svg_elem.position_y,
                        -0.5
                    ))
                    if svg_elem.rotation != 0:
                        svg_cutout = svg_cutout.rotate(
                            (0, 0, 0), (0, 0, 1), svg_elem.rotation
                        )
                    result = result.cut(svg_cutout)

        return result

    def _apply_qr_elements(
        self,
        result: cq.Workplane,
        cfg: NameplateConfig,
        plate_thickness: float
    ) -> cq.Workplane:
        """Apply QR code elements to the plate."""
        for qr_elem in cfg.qr_elements:
            qr_geometry = self._qr_generator.create_geometry(qr_elem)
            if qr_geometry is None:
                continue

            if qr_elem.style == QRStyle.RAISED:
                qr_final = qr_geometry.translate((0, 0, plate_thickness - 0.1))
                result = result.union(qr_final)
            elif qr_elem.style == QRStyle.ENGRAVED:
                qr_engrave_config = QRConfig(
                    data=qr_elem.data,
                    size=qr_elem.size,
                    depth=qr_elem.depth + 10,
                    position_x=qr_elem.position_x,
                    position_y=qr_elem.position_y,
                    error_correction=qr_elem.error_correction,
                )
                qr_engrave = self._qr_generator.create_geometry(qr_engrave_config)
                if qr_engrave is not None:
                    qr_final = qr_engrave.translate((0, 0, plate_thickness - qr_elem.depth))
                    result = result.cut(qr_final)
            elif qr_elem.style == QRStyle.CUTOUT:
                qr_cutout_config = QRConfig(
                    data=qr_elem.data,
                    size=qr_elem.size,
                    depth=plate_thickness + 10,
                    position_x=qr_elem.position_x,
                    position_y=qr_elem.position_y,
                    error_correction=qr_elem.error_correction,
                )
                qr_cutout = self._qr_generator.create_geometry(qr_cutout_config)
                if qr_cutout is not None:
                    qr_final = qr_cutout.translate((0, 0, -0.5))
                    result = result.cut(qr_final)

        return result

    def build(self, config: Optional[NameplateConfig] = None) -> cq.Workplane:
        """
        Build the complete nameplate geometry.

        This method orchestrates the generation of all nameplate components
        by delegating to specialized helper methods.

        Args:
            config: Optional config override

        Returns:
            CadQuery Workplane with the complete nameplate.
        """
        cfg = config or self.config

        debug_log.log_geometry("BUILD_START", {
            "plate_shape": cfg.plate.shape.value,
            "text_style": cfg.text.style.value,
            "num_lines": len(cfg.text.lines),
            "mount_type": cfg.mount.mount_type.value,
            "num_svg_elements": len(cfg.svg_elements),
        })

        # Step 1: Generate text (needed for auto-sizing and text-only mode)
        self._text_geometry, text_bbox = self._generate_text(cfg)

        # Step 2: Handle "none" plate shape (text only)
        if cfg.plate.shape == PlateShape.NONE:
            if self._text_geometry is not None:
                self._combined_geometry = self._text_geometry
            else:
                self._combined_geometry = cq.Workplane("XY")
            self._base_geometry = None
            self._needs_rebuild = False
            return self._combined_geometry

        # Step 3: Generate base plate with auto-sizing
        self._base_geometry, plate_dims = self._generate_base(cfg, text_bbox)
        plate_width, plate_height, plate_thickness = plate_dims

        # Step 4: Apply border and pattern to base
        result = self._apply_border_and_pattern(self._base_geometry, cfg, plate_dims)
        self._base_geometry = result  # Update for proper display

        # Step 5: Apply text based on style
        result = self._apply_text(result, self._text_geometry, cfg, plate_thickness)

        # Step 6: Apply mount features
        result = self._apply_mounts(result, cfg, plate_dims)

        # Step 7: Apply SVG elements
        result = self._apply_svg_elements(result, cfg, plate_thickness)

        # Step 8: Apply QR code elements
        result = self._apply_qr_elements(result, cfg, plate_thickness)

        self._combined_geometry = result
        self._needs_rebuild = False

        return result

    def get_geometry(self) -> Optional[cq.Workplane]:
        """Get the current combined geometry, building if necessary."""
        if self._needs_rebuild or self._combined_geometry is None:
            return self.build()
        return self._combined_geometry
    
    def get_base_geometry(self) -> Optional[cq.Workplane]:
        """Get just the base plate geometry."""
        if self._needs_rebuild:
            self.build()
        return self._base_geometry
    
    def get_text_geometry(self) -> Optional[cq.Workplane]:
        """Get just the text geometry."""
        if self._needs_rebuild:
            self.build()
        return self._text_geometry

    def get_border_geometry(self) -> Optional[cq.Workplane]:
        """Get just the border geometry."""
        if self._needs_rebuild:
            self.build()
        return self._border_geometry

    def export(self, filepath: str, options: Optional[ExportOptions] = None) -> bool:
        """
        Export the nameplate to file.
        
        Args:
            filepath: Output file path
            options: Optional export options
            
        Returns:
            True if export succeeded.
        """
        geometry = self.get_geometry()
        if geometry is None:
            return False
        
        return self._exporter.export(geometry, filepath, options)
    
    def export_separate(self, filepath: str, 
                        options: Optional[ExportOptions] = None) -> bool:
        """
        Export base and text as separate files.
        
        Args:
            filepath: Base output file path
            options: Optional export options
            
        Returns:
            True if both exports succeeded.
        """
        if self._needs_rebuild:
            self.build()
        
        if self._base_geometry is None or self._text_geometry is None:
            return False
        
        return self._exporter.export_parts(
            self._base_geometry,
            self._text_geometry,
            filepath,
            options
        )
    
    def invalidate(self) -> None:
        """Mark the geometry cache as invalid, forcing rebuild."""
        self._needs_rebuild = True
        self._combined_geometry = None


def create_default_nameplate() -> NameplateBuilder:
    """Create a nameplate builder with sensible defaults."""
    config = NameplateConfig()
    config.plate.shape = PlateShape.ROUNDED_RECTANGLE
    config.plate.width = 120.0
    config.plate.height = 35.0
    config.plate.thickness = 4.0
    config.plate.corner_radius = 5.0
    
    config.text.lines = [TextLineConfig(content="Your Name", font_size=14.0)]
    config.text.style = TextStyle.RAISED
    config.text.depth = 2.0
    
    return NameplateBuilder(config)
