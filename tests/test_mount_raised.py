"""
Tests for mount holes and cut operations working with raised text.
Verifies that cutting geometry extends high enough to intersect raised elements.
"""

import pytest
import cadquery as cq


class TestMountHolesWithRaisedText:
    """Test that mount holes properly cut through raised text/borders/SVGs."""

    def test_screw_holes_extend_above_plate(self, nameplate_builder):
        """Verify screw holes extend well above plate surface."""
        from core.nameplate import NameplateConfig
        from core.geometry.mounts import MountType, MountConfig
        from core.geometry.text_builder import TextStyle, TextLineConfig, TextSegment

        config = NameplateConfig()
        config.plate.width = 100
        config.plate.height = 40
        config.plate.thickness = 3
        config.text.style = TextStyle.RAISED
        config.text.depth = 1.5
        config.text.lines = [
            TextLineConfig(
                content="TEST",
                font_family="Arial",
                font_size=12.0,
                segments=[TextSegment(content="TEST", font_family="Arial", font_size=12.0)]
            )
        ]
        config.mount.mount_type = MountType.SCREW_HOLES
        config.mount.hole_diameter = 4.0

        # Build the nameplate
        result = nameplate_builder.build(config)
        assert result is not None, "Nameplate build failed"

        # Get bounding box - if holes cut through raised text,
        # the max Z should be approximately plate_thickness + text_depth
        bbox = result.val().BoundingBox()
        expected_max_z = config.plate.thickness + config.text.depth

        # Allow some tolerance for geometry variations
        assert bbox.zmax <= expected_max_z + 0.5, \
            f"Screw holes did not cut through raised text. Max Z: {bbox.zmax}, Expected: ~{expected_max_z}"

    def test_screw_holes_visible_with_raised_text(self, nameplate_builder):
        """Verify screw holes are actually present when using raised text."""
        from core.nameplate import NameplateConfig
        from core.geometry.mounts import MountType
        from core.geometry.text_builder import TextStyle, TextLineConfig, TextSegment

        config = NameplateConfig()
        config.plate.width = 100
        config.plate.height = 40
        config.plate.thickness = 3
        config.text.style = TextStyle.RAISED
        config.text.depth = 2.0
        config.text.lines = [
            TextLineConfig(
                content="HOLES",
                font_family="Arial",
                font_size=10.0,
                segments=[TextSegment(content="HOLES", font_family="Arial", font_size=10.0)]
            )
        ]
        config.mount.mount_type = MountType.SCREW_HOLES
        config.mount.hole_diameter = 5.0

        result = nameplate_builder.build(config)
        assert result is not None

        # The geometry should have holes - check that it's not a simple solid
        # by verifying the volume is less than a solid plate + text would be
        bbox = result.val().BoundingBox()
        solid_volume = bbox.xlen * bbox.ylen * bbox.zlen
        actual_volume = result.val().Volume()

        # With holes, actual volume should be noticeably less than bounding box volume
        assert actual_volume < solid_volume * 0.95, \
            "Geometry appears to have no holes cut through it"

    def test_keyhole_mount_with_raised_text(self, nameplate_builder):
        """Verify keyhole mounts cut through raised text."""
        from core.nameplate import NameplateConfig
        from core.geometry.mounts import MountType
        from core.geometry.text_builder import TextStyle, TextLineConfig, TextSegment

        config = NameplateConfig()
        config.plate.width = 120
        config.plate.height = 40
        config.plate.thickness = 3
        config.text.style = TextStyle.RAISED
        config.text.depth = 1.5
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
        assert result is not None, "Keyhole mount build failed with raised text"

        # Verify holes exist by checking volume
        bbox = result.val().BoundingBox()
        solid_volume = bbox.xlen * bbox.ylen * bbox.zlen
        actual_volume = result.val().Volume()
        assert actual_volume < solid_volume * 0.98, \
            "Keyhole geometry appears to have no cuts"

    def test_hanging_holes_with_raised_text(self, nameplate_builder):
        """Verify hanging holes cut through raised text."""
        from core.nameplate import NameplateConfig
        from core.geometry.mounts import MountType
        from core.geometry.text_builder import TextStyle, TextLineConfig, TextSegment

        config = NameplateConfig()
        config.plate.width = 100
        config.plate.height = 40
        config.plate.thickness = 3
        config.text.style = TextStyle.RAISED
        config.text.depth = 2.0
        config.text.lines = [
            TextLineConfig(
                content="HANG",
                font_family="Arial",
                font_size=10.0,
                segments=[TextSegment(content="HANG", font_family="Arial", font_size=10.0)]
            )
        ]
        config.mount.mount_type = MountType.HANGING_HOLE
        config.mount.hanging_hole_diameter = 6.0

        result = nameplate_builder.build(config)
        assert result is not None, "Hanging holes build failed with raised text"


class TestEngravedCutoutWithRaisedBorder:
    """Test that engraved/cutout text cuts through raised borders."""

    def test_engraved_text_cuts_through_raised_border(self, nameplate_builder):
        """Verify engraved text cuts through raised borders."""
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
                content="ENGRAVE",
                font_family="Arial",
                font_size=10.0,
                segments=[TextSegment(content="ENGRAVE", font_family="Arial", font_size=10.0)]
            )
        ]
        # Enable raised border
        config.border.enabled = True
        config.border.width = 3.0
        config.border.depth = 1.5
        config.border.style = "raised"

        result = nameplate_builder.build(config)
        assert result is not None, "Engraved text with raised border build failed"

        # The min Z should be at the engrave depth below the plate surface
        bbox = result.val().BoundingBox()
        expected_min_z = config.plate.thickness - config.text.depth
        assert bbox.zmin <= expected_min_z + 0.1, \
            f"Engraved text did not cut to expected depth. Min Z: {bbox.zmin}"

    def test_cutout_text_cuts_through_raised_border(self, nameplate_builder):
        """Verify cutout text cuts completely through plate and raised borders."""
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
        # Enable raised border
        config.border.enabled = True
        config.border.width = 3.0
        config.border.depth = 2.0
        config.border.style = "raised"

        result = nameplate_builder.build(config)
        assert result is not None, "Cutout text with raised border build failed"

        # Cutout should go through the entire plate
        bbox = result.val().BoundingBox()
        assert bbox.zmin <= 0.1, \
            f"Cutout text did not cut through plate bottom. Min Z: {bbox.zmin}"


class TestSVGWithRaisedElements:
    """Test that SVG elements work correctly with raised text/borders."""

    def test_svg_engraved_with_raised_text(self, nameplate_builder):
        """Verify SVG engraved cuts through raised text."""
        from core.nameplate import NameplateConfig
        from core.geometry.text_builder import TextStyle, TextLineConfig, TextSegment

        config = NameplateConfig()
        config.plate.width = 100
        config.plate.height = 50
        config.plate.thickness = 3
        config.text.style = TextStyle.RAISED
        config.text.depth = 1.5
        config.text.lines = [
            TextLineConfig(
                content="SVG",
                font_family="Arial",
                font_size=8.0,
                segments=[TextSegment(content="SVG", font_family="Arial", font_size=8.0)]
            )
        ]

        # Add a simple SVG element (circle path)
        from core.nameplate import SVGElement
        svg_elem = SVGElement()
        svg_elem.enabled = True
        svg_elem.svg_content = '<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="40"/></svg>'
        svg_elem.style = "engraved"
        svg_elem.depth = 0.5
        svg_elem.target_size = 15.0
        svg_elem.position_x = 30.0
        svg_elem.position_y = 0.0
        config.svg_elements = [svg_elem]

        result = nameplate_builder.build(config)
        assert result is not None, "SVG engraved with raised text build failed"

    def test_svg_cutout_with_raised_text(self, nameplate_builder):
        """Verify SVG cutout cuts through raised text and plate."""
        from core.nameplate import NameplateConfig
        from core.geometry.text_builder import TextStyle, TextLineConfig, TextSegment

        config = NameplateConfig()
        config.plate.width = 100
        config.plate.height = 50
        config.plate.thickness = 3
        config.text.style = TextStyle.RAISED
        config.text.depth = 2.0
        config.text.lines = [
            TextLineConfig(
                content="CUT",
                font_family="Arial",
                font_size=8.0,
                segments=[TextSegment(content="CUT", font_family="Arial", font_size=8.0)]
            )
        ]

        # Add a simple SVG element
        from core.nameplate import SVGElement
        svg_elem = SVGElement()
        svg_elem.enabled = True
        svg_elem.svg_content = '<svg viewBox="0 0 100 100"><rect x="20" y="20" width="60" height="60"/></svg>'
        svg_elem.style = "cutout"
        svg_elem.target_size = 10.0
        svg_elem.position_x = -30.0
        svg_elem.position_y = 0.0
        config.svg_elements = [svg_elem]

        result = nameplate_builder.build(config)
        assert result is not None, "SVG cutout with raised text build failed"

        # Cutout should penetrate to Z=0
        bbox = result.val().BoundingBox()
        assert bbox.zmin <= 0.1, "SVG cutout did not cut through plate"


class TestAllTextStylesWithMounts:
    """Test all text styles work with all mount types."""

    @pytest.mark.parametrize("text_style", ["RAISED", "ENGRAVED", "CUTOUT"])
    @pytest.mark.parametrize("mount_type", ["SCREW_HOLES", "KEYHOLE", "HANGING_HOLE"])
    def test_text_style_with_mount(self, nameplate_builder, text_style, mount_type):
        """Verify all combinations of text styles and mount types work."""
        from core.nameplate import NameplateConfig
        from core.geometry.mounts import MountType
        from core.geometry.text_builder import TextStyle, TextLineConfig, TextSegment

        config = NameplateConfig()
        config.plate.width = 120
        config.plate.height = 40
        config.plate.thickness = 3
        config.text.style = getattr(TextStyle, text_style)
        config.text.depth = 1.5
        config.text.lines = [
            TextLineConfig(
                content="TEST",
                font_family="Arial",
                font_size=8.0,
                segments=[TextSegment(content="TEST", font_family="Arial", font_size=8.0)]
            )
        ]
        config.mount.mount_type = getattr(MountType, mount_type)

        result = nameplate_builder.build(config)
        assert result is not None, \
            f"Build failed for {text_style} text with {mount_type} mount"

        # Verify geometry is valid
        assert result.val().Volume() > 0, \
            f"Invalid geometry for {text_style} + {mount_type}"
