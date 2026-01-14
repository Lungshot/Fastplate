"""
Visual Regression Tests for Fastplate.

These tests generate nameplate geometry with various configurations and compare
against stored baselines. On first run, baselines are created. On subsequent runs,
geometry properties are compared to detect regressions.

Baselines are stored as JSON files in tests/baselines/
"""

import pytest
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional


# Baseline directory
BASELINE_DIR = Path(__file__).parent / "baselines"


@dataclass
class GeometryBaseline:
    """Stores geometry properties for comparison."""
    name: str
    volume: float
    bbox_xlen: float
    bbox_ylen: float
    bbox_zlen: float
    bbox_zmin: float
    bbox_zmax: float
    # Hash of vertices for more precise comparison
    vertex_hash: Optional[str] = None

    def matches(self, other: 'GeometryBaseline', tolerance: float = 0.01) -> tuple[bool, str]:
        """Compare with another baseline, return (matches, reason)."""
        if abs(self.volume - other.volume) / max(self.volume, 0.001) > tolerance:
            return False, f"Volume mismatch: {self.volume:.4f} vs {other.volume:.4f}"

        if abs(self.bbox_xlen - other.bbox_xlen) > tolerance * 10:
            return False, f"X dimension mismatch: {self.bbox_xlen:.2f} vs {other.bbox_xlen:.2f}"

        if abs(self.bbox_ylen - other.bbox_ylen) > tolerance * 10:
            return False, f"Y dimension mismatch: {self.bbox_ylen:.2f} vs {other.bbox_ylen:.2f}"

        if abs(self.bbox_zlen - other.bbox_zlen) > tolerance * 10:
            return False, f"Z dimension mismatch: {self.bbox_zlen:.2f} vs {other.bbox_zlen:.2f}"

        if abs(self.bbox_zmin - other.bbox_zmin) > tolerance:
            return False, f"Z min mismatch: {self.bbox_zmin:.4f} vs {other.bbox_zmin:.4f}"

        if abs(self.bbox_zmax - other.bbox_zmax) > tolerance:
            return False, f"Z max mismatch: {self.bbox_zmax:.4f} vs {other.bbox_zmax:.4f}"

        return True, "OK"


def extract_geometry_properties(geometry, name: str) -> GeometryBaseline:
    """Extract properties from CadQuery geometry for comparison."""
    solid = geometry.val()
    bbox = solid.BoundingBox()

    # Create hash from vertex positions for precise comparison
    try:
        vertices = solid.Vertices()
        vertex_data = sorted([f"{v.X:.4f},{v.Y:.4f},{v.Z:.4f}" for v in vertices])
        vertex_hash = hashlib.md5("|".join(vertex_data).encode()).hexdigest()[:16]
    except Exception:
        vertex_hash = None

    return GeometryBaseline(
        name=name,
        volume=solid.Volume(),
        bbox_xlen=bbox.xlen,
        bbox_ylen=bbox.ylen,
        bbox_zlen=bbox.zlen,
        bbox_zmin=bbox.zmin,
        bbox_zmax=bbox.zmax,
        vertex_hash=vertex_hash
    )


def save_baseline(baseline: GeometryBaseline):
    """Save baseline to JSON file."""
    BASELINE_DIR.mkdir(exist_ok=True)
    filepath = BASELINE_DIR / f"{baseline.name}.json"
    with open(filepath, 'w') as f:
        json.dump(asdict(baseline), f, indent=2)


def load_baseline(name: str) -> Optional[GeometryBaseline]:
    """Load baseline from JSON file."""
    filepath = BASELINE_DIR / f"{name}.json"
    if not filepath.exists():
        return None
    with open(filepath, 'r') as f:
        data = json.load(f)
        return GeometryBaseline(**data)


def compare_or_create_baseline(geometry, name: str, update_baseline: bool = False):
    """Compare geometry against baseline, or create if missing."""
    current = extract_geometry_properties(geometry, name)
    existing = load_baseline(name)

    if existing is None or update_baseline:
        save_baseline(current)
        if existing is None:
            pytest.skip(f"Baseline created for '{name}'. Run tests again to compare.")
        return

    matches, reason = current.matches(existing)
    if not matches:
        # Save current as .current.json for debugging
        current_file = BASELINE_DIR / f"{name}.current.json"
        with open(current_file, 'w') as f:
            json.dump(asdict(current), f, indent=2)

        pytest.fail(f"Visual regression detected for '{name}': {reason}\n"
                   f"Current saved to {current_file}")


class TestBasicNameplateRegression:
    """Visual regression tests for basic nameplate configurations."""

    def test_simple_raised_text(self, nameplate_builder):
        """Regression test for simple raised text nameplate."""
        from core.nameplate import NameplateConfig
        from core.geometry.text_builder import TextStyle, TextLineConfig, TextSegment

        config = NameplateConfig()
        config.plate.width = 100
        config.plate.height = 30
        config.plate.thickness = 3
        config.text.style = TextStyle.RAISED
        config.text.depth = 1.5
        config.text.lines = [
            TextLineConfig(
                content="BASELINE",
                font_family="Arial",
                font_size=10.0,
                segments=[TextSegment(content="BASELINE", font_family="Arial", font_size=10.0)]
            )
        ]

        result = nameplate_builder.build(config)
        assert result is not None

        compare_or_create_baseline(result, "simple_raised_text")

    def test_simple_engraved_text(self, nameplate_builder):
        """Regression test for simple engraved text nameplate."""
        from core.nameplate import NameplateConfig
        from core.geometry.text_builder import TextStyle, TextLineConfig, TextSegment

        config = NameplateConfig()
        config.plate.width = 100
        config.plate.height = 30
        config.plate.thickness = 3
        config.text.style = TextStyle.ENGRAVED
        config.text.depth = 0.8
        config.text.lines = [
            TextLineConfig(
                content="ENGRAVE",
                font_family="Arial",
                font_size=10.0,
                segments=[TextSegment(content="ENGRAVE", font_family="Arial", font_size=10.0)]
            )
        ]

        result = nameplate_builder.build(config)
        assert result is not None

        compare_or_create_baseline(result, "simple_engraved_text")

    def test_simple_cutout_text(self, nameplate_builder):
        """Regression test for cutout text nameplate."""
        from core.nameplate import NameplateConfig
        from core.geometry.text_builder import TextStyle, TextLineConfig, TextSegment

        config = NameplateConfig()
        config.plate.width = 100
        config.plate.height = 30
        config.plate.thickness = 3
        config.text.style = TextStyle.CUTOUT
        config.text.lines = [
            TextLineConfig(
                content="CUT",
                font_family="Arial",
                font_size=12.0,
                segments=[TextSegment(content="CUT", font_family="Arial", font_size=12.0)]
            )
        ]

        result = nameplate_builder.build(config)
        assert result is not None

        compare_or_create_baseline(result, "simple_cutout_text")


class TestMountRegression:
    """Visual regression tests for mount configurations."""

    def test_screw_holes_raised_text(self, nameplate_builder):
        """Regression test for screw holes with raised text."""
        from core.nameplate import NameplateConfig
        from core.geometry.mounts import MountType
        from core.geometry.text_builder import TextStyle, TextLineConfig, TextSegment

        config = NameplateConfig()
        config.plate.width = 100
        config.plate.height = 40
        config.plate.thickness = 3
        config.text.style = TextStyle.RAISED
        config.text.depth = 1.5
        config.text.lines = [
            TextLineConfig(
                content="MOUNT",
                font_family="Arial",
                font_size=10.0,
                segments=[TextSegment(content="MOUNT", font_family="Arial", font_size=10.0)]
            )
        ]
        config.mount.mount_type = MountType.SCREW_HOLES
        config.mount.hole_diameter = 4.0

        result = nameplate_builder.build(config)
        assert result is not None

        compare_or_create_baseline(result, "screw_holes_raised_text")

    def test_keyhole_raised_text(self, nameplate_builder):
        """Regression test for keyhole with raised text."""
        from core.nameplate import NameplateConfig
        from core.geometry.mounts import MountType
        from core.geometry.text_builder import TextStyle, TextLineConfig, TextSegment

        config = NameplateConfig()
        config.plate.width = 120
        config.plate.height = 40
        config.plate.thickness = 3
        config.text.style = TextStyle.RAISED
        config.text.depth = 2.0
        config.text.lines = [
            TextLineConfig(
                content="KEYHOLE",
                font_family="Arial",
                font_size=10.0,
                segments=[TextSegment(content="KEYHOLE", font_family="Arial", font_size=10.0)]
            )
        ]
        config.mount.mount_type = MountType.KEYHOLE

        result = nameplate_builder.build(config)
        assert result is not None

        compare_or_create_baseline(result, "keyhole_raised_text")

    def test_hanging_holes_engraved(self, nameplate_builder):
        """Regression test for hanging holes with engraved text."""
        from core.nameplate import NameplateConfig
        from core.geometry.mounts import MountType
        from core.geometry.text_builder import TextStyle, TextLineConfig, TextSegment

        config = NameplateConfig()
        config.plate.width = 100
        config.plate.height = 40
        config.plate.thickness = 3
        config.text.style = TextStyle.ENGRAVED
        config.text.depth = 1.0
        config.text.lines = [
            TextLineConfig(
                content="HANG",
                font_family="Arial",
                font_size=10.0,
                segments=[TextSegment(content="HANG", font_family="Arial", font_size=10.0)]
            )
        ]
        config.mount.mount_type = MountType.HANGING_HOLE
        config.mount.hanging_hole_diameter = 5.0

        result = nameplate_builder.build(config)
        assert result is not None

        compare_or_create_baseline(result, "hanging_holes_engraved")


class TestBorderRegression:
    """Visual regression tests for border configurations."""

    def test_raised_border_engraved_text(self, nameplate_builder):
        """Regression test for raised border with engraved text."""
        from core.nameplate import NameplateConfig
        from core.geometry.text_builder import TextStyle, TextLineConfig, TextSegment

        config = NameplateConfig()
        config.plate.width = 100
        config.plate.height = 40
        config.plate.thickness = 3
        config.text.style = TextStyle.ENGRAVED
        config.text.depth = 0.8
        config.text.lines = [
            TextLineConfig(
                content="BORDER",
                font_family="Arial",
                font_size=10.0,
                segments=[TextSegment(content="BORDER", font_family="Arial", font_size=10.0)]
            )
        ]
        config.border.enabled = True
        config.border.width = 3.0
        config.border.depth = 1.5
        config.border.style = "raised"

        result = nameplate_builder.build(config)
        assert result is not None

        compare_or_create_baseline(result, "raised_border_engraved")

    def test_raised_border_cutout_text(self, nameplate_builder):
        """Regression test for raised border with cutout text."""
        from core.nameplate import NameplateConfig
        from core.geometry.text_builder import TextStyle, TextLineConfig, TextSegment

        config = NameplateConfig()
        config.plate.width = 100
        config.plate.height = 40
        config.plate.thickness = 3
        config.text.style = TextStyle.CUTOUT
        config.text.lines = [
            TextLineConfig(
                content="CUT",
                font_family="Arial",
                font_size=12.0,
                segments=[TextSegment(content="CUT", font_family="Arial", font_size=12.0)]
            )
        ]
        config.border.enabled = True
        config.border.width = 4.0
        config.border.depth = 2.0
        config.border.style = "raised"

        result = nameplate_builder.build(config)
        assert result is not None

        compare_or_create_baseline(result, "raised_border_cutout")


class TestSVGRegression:
    """Visual regression tests for SVG configurations."""

    def test_svg_raised_circle(self, nameplate_builder):
        """Regression test for raised SVG circle."""
        from core.nameplate import NameplateConfig, SVGElement
        from core.geometry.text_builder import TextLineConfig, TextSegment

        config = NameplateConfig()
        config.plate.width = 80
        config.plate.height = 40
        config.plate.thickness = 3
        config.text.lines = [
            TextLineConfig(
                content="SVG",
                font_family="Arial",
                font_size=8.0,
                segments=[TextSegment(content="SVG", font_family="Arial", font_size=8.0)]
            )
        ]

        svg_elem = SVGElement()
        svg_elem.enabled = True
        svg_elem.svg_content = '<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="40"/></svg>'
        svg_elem.style = "raised"
        svg_elem.depth = 1.5
        svg_elem.target_size = 15.0
        svg_elem.position_x = 25.0
        svg_elem.position_y = 0.0
        config.svg_elements = [svg_elem]

        result = nameplate_builder.build(config)
        assert result is not None

        compare_or_create_baseline(result, "svg_raised_circle")

    def test_svg_engraved_rect(self, nameplate_builder):
        """Regression test for engraved SVG rectangle."""
        from core.nameplate import NameplateConfig, SVGElement
        from core.geometry.text_builder import TextStyle, TextLineConfig, TextSegment

        config = NameplateConfig()
        config.plate.width = 80
        config.plate.height = 40
        config.plate.thickness = 3
        config.text.style = TextStyle.RAISED
        config.text.depth = 1.0
        config.text.lines = [
            TextLineConfig(
                content="ENG",
                font_family="Arial",
                font_size=8.0,
                segments=[TextSegment(content="ENG", font_family="Arial", font_size=8.0)]
            )
        ]

        svg_elem = SVGElement()
        svg_elem.enabled = True
        svg_elem.svg_content = '<svg viewBox="0 0 100 100"><rect x="10" y="10" width="80" height="80"/></svg>'
        svg_elem.style = "engraved"
        svg_elem.depth = 0.5
        svg_elem.target_size = 12.0
        svg_elem.position_x = -25.0
        svg_elem.position_y = 0.0
        config.svg_elements = [svg_elem]

        result = nameplate_builder.build(config)
        assert result is not None

        compare_or_create_baseline(result, "svg_engraved_rect")


class TestComplexRegression:
    """Visual regression tests for complex configurations."""

    def test_full_featured_nameplate(self, nameplate_builder):
        """Regression test for nameplate with all features."""
        from core.nameplate import NameplateConfig, SVGElement
        from core.geometry.mounts import MountType
        from core.geometry.text_builder import TextStyle, TextLineConfig, TextSegment

        config = NameplateConfig()
        config.plate.width = 120
        config.plate.height = 50
        config.plate.thickness = 3
        config.text.style = TextStyle.RAISED
        config.text.depth = 1.5
        config.text.lines = [
            TextLineConfig(
                content="FULL TEST",
                font_family="Arial",
                font_size=10.0,
                segments=[TextSegment(content="FULL TEST", font_family="Arial", font_size=10.0)]
            )
        ]
        config.mount.mount_type = MountType.SCREW_HOLES
        config.mount.hole_diameter = 4.0
        config.border.enabled = True
        config.border.width = 3.0
        config.border.depth = 1.0
        config.border.style = "raised"

        svg_elem = SVGElement()
        svg_elem.enabled = True
        svg_elem.svg_content = '<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="30"/></svg>'
        svg_elem.style = "engraved"
        svg_elem.depth = 0.5
        svg_elem.target_size = 10.0
        svg_elem.position_x = 40.0
        svg_elem.position_y = 0.0
        config.svg_elements = [svg_elem]

        result = nameplate_builder.build(config)
        assert result is not None

        compare_or_create_baseline(result, "full_featured_nameplate")

    def test_multiline_text(self, nameplate_builder):
        """Regression test for multi-line text."""
        from core.nameplate import NameplateConfig
        from core.geometry.text_builder import TextStyle, TextLineConfig, TextSegment

        config = NameplateConfig()
        config.plate.width = 100
        config.plate.height = 50
        config.plate.thickness = 3
        config.text.style = TextStyle.RAISED
        config.text.depth = 1.0
        config.text.line_spacing = 1.2
        config.text.lines = [
            TextLineConfig(
                content="LINE ONE",
                font_family="Arial",
                font_size=8.0,
                segments=[TextSegment(content="LINE ONE", font_family="Arial", font_size=8.0)]
            ),
            TextLineConfig(
                content="LINE TWO",
                font_family="Arial",
                font_size=8.0,
                segments=[TextSegment(content="LINE TWO", font_family="Arial", font_size=8.0)]
            )
        ]

        result = nameplate_builder.build(config)
        assert result is not None

        compare_or_create_baseline(result, "multiline_text")
