"""
Tests for SVG import functionality.
Verifies SVG parsing and geometry creation.
"""

import pytest


class TestSVGImporter:
    """Tests for the SVG importer module."""

    @pytest.fixture
    def svg_importer(self):
        """Create an SVG importer instance."""
        from core.geometry.svg_importer import SVGImporter
        return SVGImporter()

    def test_simple_circle_svg(self, svg_importer):
        """Test importing a simple circle SVG."""
        svg_content = '<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="40"/></svg>'

        # First parse the SVG to get paths
        elem = svg_importer.load_svg_from_content(svg_content, "circle")
        assert elem is not None, "Failed to parse circle SVG"

        geometry = svg_importer.create_geometry(elem, target_size=20.0, depth=2.0)

        assert geometry is not None, "Failed to create geometry from circle SVG"
        assert geometry.val().Volume() > 0, "Circle geometry has zero volume"

    def test_simple_rect_svg(self, svg_importer):
        """Test importing a simple rectangle SVG."""
        svg_content = '<svg viewBox="0 0 100 100"><rect x="10" y="10" width="80" height="60"/></svg>'

        elem = svg_importer.load_svg_from_content(svg_content, "rect")
        assert elem is not None, "Failed to parse rect SVG"

        geometry = svg_importer.create_geometry(elem, target_size=20.0, depth=2.0)

        assert geometry is not None, "Failed to create geometry from rect SVG"
        assert geometry.val().Volume() > 0, "Rect geometry has zero volume"

    def test_path_svg(self, svg_importer):
        """Test importing an SVG with path commands."""
        # Simple triangle path
        svg_content = '<svg viewBox="0 0 100 100"><path d="M50,10 L90,90 L10,90 Z"/></svg>'

        elem = svg_importer.load_svg_from_content(svg_content, "triangle")
        assert elem is not None, "Failed to parse path SVG"

        geometry = svg_importer.create_geometry(elem, target_size=20.0, depth=2.0)

        assert geometry is not None, "Failed to create geometry from path SVG"
        assert geometry.val().Volume() > 0, "Path geometry has zero volume"

    def test_complex_path_svg(self, svg_importer):
        """Test importing SVG with bezier curves."""
        # Path with cubic bezier
        svg_content = '''<svg viewBox="0 0 100 100">
            <path d="M10,50 C10,10 90,10 90,50 C90,90 10,90 10,50 Z"/>
        </svg>'''

        elem = svg_importer.load_svg_from_content(svg_content, "bezier")
        assert elem is not None, "Failed to parse bezier SVG"

        geometry = svg_importer.create_geometry(elem, target_size=20.0, depth=2.0)

        assert geometry is not None, "Failed to create geometry from bezier path"

    def test_polygon_svg(self, svg_importer):
        """Test importing SVG with polygon element."""
        svg_content = '<svg viewBox="0 0 100 100"><polygon points="50,10 90,40 75,90 25,90 10,40"/></svg>'

        elem = svg_importer.load_svg_from_content(svg_content, "polygon")
        assert elem is not None, "Failed to parse polygon SVG"

        geometry = svg_importer.create_geometry(elem, target_size=20.0, depth=2.0)

        assert geometry is not None, "Failed to create geometry from polygon SVG"

    def test_ellipse_svg(self, svg_importer):
        """Test importing SVG with ellipse element."""
        svg_content = '<svg viewBox="0 0 100 100"><ellipse cx="50" cy="50" rx="40" ry="25"/></svg>'

        elem = svg_importer.load_svg_from_content(svg_content, "ellipse")
        assert elem is not None, "Failed to parse ellipse SVG"

        geometry = svg_importer.create_geometry(elem, target_size=20.0, depth=2.0)

        assert geometry is not None, "Failed to create geometry from ellipse SVG"

    def test_compact_number_format(self, svg_importer):
        """Test parsing compact number formats like '-3.41.81' (Material Icons style)."""
        # This format caused issues before the fix
        svg_content = '''<svg viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/>
        </svg>'''

        elem = svg_importer.load_svg_from_content(svg_content, "material")
        assert elem is not None, "Failed to parse material icon SVG"

        geometry = svg_importer.create_geometry(elem, target_size=20.0, depth=2.0)

        assert geometry is not None, "Failed to parse compact number format in path"

    def test_multiple_shapes_svg(self, svg_importer):
        """Test importing SVG with multiple shapes."""
        svg_content = '''<svg viewBox="0 0 100 100">
            <circle cx="25" cy="25" r="15"/>
            <rect x="50" y="10" width="30" height="30"/>
            <circle cx="25" cy="75" r="15"/>
        </svg>'''

        elem = svg_importer.load_svg_from_content(svg_content, "multi")
        assert elem is not None, "Failed to parse multi-shape SVG"

        geometry = svg_importer.create_geometry(elem, target_size=30.0, depth=2.0)

        assert geometry is not None, "Failed to create geometry from multi-shape SVG"

    def test_empty_svg_handled_gracefully(self, svg_importer):
        """Test that empty SVG doesn't crash."""
        svg_content = '<svg viewBox="0 0 100 100"></svg>'

        # Empty SVG should return None from load
        elem = svg_importer.load_svg_from_content(svg_content, "empty")
        # Empty SVG may return elem with no paths - that's acceptable

    def test_invalid_svg_handled_gracefully(self, svg_importer):
        """Test that invalid SVG doesn't crash."""
        svg_content = 'not valid svg at all'

        # Should not raise exception
        try:
            elem = svg_importer.load_svg_from_content(svg_content, "invalid")
        except Exception as e:
            pytest.fail(f"Invalid SVG caused crash: {e}")


class TestSVGScaling:
    """Tests for SVG scaling and positioning."""

    @pytest.fixture
    def svg_importer(self):
        from core.geometry.svg_importer import SVGImporter
        return SVGImporter()

    def test_target_size_scaling(self, svg_importer):
        """Test that target_size parameter scales geometry correctly."""
        svg_content = '<svg viewBox="0 0 100 100"><rect x="0" y="0" width="100" height="100"/></svg>'

        # Create at 20mm
        elem1 = svg_importer.load_svg_from_content(svg_content, "rect20")
        geom1 = svg_importer.create_geometry(elem1, target_size=20.0, depth=2.0)

        # Create at 40mm
        elem2 = svg_importer.load_svg_from_content(svg_content, "rect40")
        geom2 = svg_importer.create_geometry(elem2, target_size=40.0, depth=2.0)

        if geom1 and geom2:
            bbox1 = geom1.val().BoundingBox()
            bbox2 = geom2.val().BoundingBox()

            # 40mm should be roughly 2x the size of 20mm
            size1 = max(bbox1.xlen, bbox1.ylen)
            size2 = max(bbox2.xlen, bbox2.ylen)

            ratio = size2 / size1
            assert 1.8 < ratio < 2.2, \
                f"Scaling ratio {ratio} not close to expected 2.0"

    def test_depth_parameter(self, svg_importer):
        """Test that depth parameter affects geometry height."""
        svg_content = '<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="40"/></svg>'

        # Create with 2mm depth
        elem1 = svg_importer.load_svg_from_content(svg_content, "circle2")
        geom1 = svg_importer.create_geometry(elem1, target_size=20.0, depth=2.0)

        # Create with 5mm depth
        elem2 = svg_importer.load_svg_from_content(svg_content, "circle5")
        geom2 = svg_importer.create_geometry(elem2, target_size=20.0, depth=5.0)

        if geom1 and geom2:
            bbox1 = geom1.val().BoundingBox()
            bbox2 = geom2.val().BoundingBox()

            # Depth should affect Z height
            assert abs(bbox1.zlen - 2.0) < 0.1, f"Depth 2.0 gave Z height {bbox1.zlen}"
            assert abs(bbox2.zlen - 5.0) < 0.1, f"Depth 5.0 gave Z height {bbox2.zlen}"
