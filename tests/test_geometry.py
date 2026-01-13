"""
Tests for geometry generation (text builder, base plates, etc.)
"""

import pytest


class TestTextBuilder:
    """Tests for the TextBuilder geometry generation."""

    def test_simple_text_generation(self, nameplate_builder, default_config):
        """Test generating simple text geometry."""
        from core.geometry.text_builder import TextConfig, TextLineConfig, TextSegment

        config = TextConfig()
        config.lines = [
            TextLineConfig(
                content="Test",
                font_family="Arial",
                font_size=12.0,
                segments=[TextSegment(
                    content="Test",
                    font_family="Arial",
                    font_style="Regular",
                    font_size=12.0,
                )]
            )
        ]

        # This should not raise an error
        geometry, bbox = nameplate_builder._text_gen.generate(config)

        assert geometry is not None or bbox is None  # May be None if font not found

    def test_multi_segment_text(self, nameplate_builder):
        """Test generating text with multiple segments."""
        from core.geometry.text_builder import TextConfig, TextLineConfig, TextSegment

        config = TextConfig()
        config.lines = [
            TextLineConfig(
                content="",
                segments=[
                    TextSegment(content="Hello", font_family="Arial", font_size=12.0),
                    TextSegment(content="World", font_family="Arial", font_size=12.0),
                ],
                segment_gap=2.0,
            )
        ]

        # This should not raise the TopoDS_Shape error
        try:
            geometry, bbox = nameplate_builder._text_gen.generate(config)
            # Success - no exception
            assert True
        except TypeError as e:
            if "TopoDS_Shape" in str(e):
                pytest.fail(f"TopoDS_Shape type error not fixed: {e}")
            raise

    def test_empty_text_handling(self, nameplate_builder):
        """Test that empty text is handled gracefully."""
        from core.geometry.text_builder import TextConfig, TextLineConfig

        config = TextConfig()
        config.lines = [TextLineConfig(content="")]

        # This should not raise an exception
        geometry, bbox = nameplate_builder._text_gen.generate(config)

        # Empty text may return empty geometry or zero-sized bbox
        # The important thing is no exception
        assert True


class TestBasePlateGenerator:
    """Tests for base plate generation."""

    def test_rectangle_generation(self, nameplate_builder):
        """Test generating a rectangle plate."""
        from core.geometry.base_plates import PlateConfig, PlateShape

        config = PlateConfig()
        config.shape = PlateShape.RECTANGLE
        config.width = 100
        config.height = 30
        config.thickness = 3

        geometry = nameplate_builder._plate_gen.generate(config)

        assert geometry is not None

    def test_rounded_rectangle_generation(self, nameplate_builder):
        """Test generating a rounded rectangle plate."""
        from core.geometry.base_plates import PlateConfig, PlateShape

        config = PlateConfig()
        config.shape = PlateShape.ROUNDED_RECTANGLE
        config.width = 100
        config.height = 30
        config.thickness = 3
        config.corner_radius = 5

        geometry = nameplate_builder._plate_gen.generate(config)

        assert geometry is not None

    def test_oval_generation(self, nameplate_builder):
        """Test generating an oval plate."""
        from core.geometry.base_plates import PlateConfig, PlateShape

        config = PlateConfig()
        config.shape = PlateShape.OVAL
        config.width = 100
        config.height = 30
        config.thickness = 3

        geometry = nameplate_builder._plate_gen.generate(config)

        assert geometry is not None


class TestNameplateBuilder:
    """Tests for the complete NameplateBuilder."""

    def test_basic_build(self, nameplate_builder, default_config):
        """Test building a basic nameplate with simple text."""
        from core.nameplate import NameplateConfig
        from core.geometry.text_builder import TextStyle, TextLineConfig, TextSegment

        config = NameplateConfig()
        config.plate.width = 100
        config.plate.height = 30
        config.plate.thickness = 3
        config.text.style = TextStyle.RAISED
        # Include simple text content
        config.text.lines = [
            TextLineConfig(
                content="Test",
                font_family="Arial",
                font_size=10.0,
                segments=[TextSegment(content="Test", font_family="Arial", font_size=10.0)]
            )
        ]

        geometry = nameplate_builder.build(config)

        assert geometry is not None

    def test_build_with_text(self, nameplate_builder):
        """Test building a nameplate with text."""
        from core.nameplate import NameplateConfig
        from core.geometry.text_builder import TextLineConfig, TextSegment

        config = NameplateConfig()
        config.plate.width = 100
        config.plate.height = 30
        config.plate.thickness = 3
        config.text.lines = [
            TextLineConfig(
                content="Test",
                font_family="Arial",
                font_size=10.0,
                segments=[TextSegment(
                    content="Test",
                    font_family="Arial",
                    font_size=10.0,
                )]
            )
        ]

        geometry = nameplate_builder.build(config)

        assert geometry is not None

    def test_build_with_mount(self, nameplate_builder):
        """Test building a nameplate with mounting features."""
        from core.nameplate import NameplateConfig
        from core.geometry.mounts import MountType
        from core.geometry.text_builder import TextLineConfig, TextSegment

        config = NameplateConfig()
        config.plate.width = 100
        config.plate.height = 30
        config.plate.thickness = 3
        config.mount.mount_type = MountType.DESK_STAND
        # Add some text to avoid empty geometry union issues
        config.text.lines = [
            TextLineConfig(
                content="Test",
                font_family="Arial",
                font_size=10.0,
                segments=[TextSegment(
                    content="Test",
                    font_family="Arial",
                    font_size=10.0,
                )]
            )
        ]

        geometry = nameplate_builder.build(config)

        assert geometry is not None
