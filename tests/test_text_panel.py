"""
Tests for the TextPanel and segment functionality.
"""

import pytest
from PyQt5.QtCore import Qt


class TestTextPanel:
    """Tests for the TextPanel widget."""

    def test_initial_state(self, text_panel):
        """Test that the text panel initializes correctly."""
        assert text_panel is not None
        assert len(text_panel._line_widgets) == 1  # Should have one default line

    def test_add_line(self, text_panel, qtbot):
        """Test adding a new text line."""
        initial_lines = len(text_panel._line_widgets)

        # Click the add line button
        add_btn = None
        for child in text_panel.findChildren(type(text_panel)):
            pass  # Find the add button

        # Direct method call
        text_panel._add_line()

        assert len(text_panel._line_widgets) == initial_lines + 1

    def test_get_config(self, text_panel):
        """Test that get_config returns valid configuration."""
        config = text_panel.get_config()

        assert 'lines' in config
        assert 'style' in config
        assert 'depth' in config
        assert 'line_spacing' in config
        assert 'halign' in config

    def test_set_config(self, text_panel):
        """Test that set_config properly applies configuration."""
        config = {
            'lines': [
                {
                    'content': 'Test Line 1',
                    'font_family': 'Arial',
                    'font_size': 14,
                    'segments': [{
                        'content': 'Test Line 1',
                        'font_family': 'Arial',
                        'font_style': 'Regular',
                        'font_size': 14,
                        'letter_spacing': 0,
                    }]
                }
            ],
            'style': 'raised',
            'depth': 3.0,
            'line_spacing': 1.5,
            'halign': 'center',
        }

        text_panel.set_config(config)

        result_config = text_panel.get_config()
        assert result_config['style'] == 'raised'
        assert result_config['depth'] == 3.0
        assert result_config['line_spacing'] == 1.5


class TestTextLineWidget:
    """Tests for the TextLineWidget and segments."""

    def test_segment_add(self, text_panel, qtbot):
        """Test adding a segment to a line."""
        line_widget = text_panel._line_widgets[0]
        initial_segments = len(line_widget._segment_widgets)

        line_widget._add_segment()

        assert len(line_widget._segment_widgets) == initial_segments + 1

    def test_segment_remove(self, text_panel, qtbot):
        """Test removing a segment from a line."""
        line_widget = text_panel._line_widgets[0]

        # Add a segment first
        line_widget._add_segment()
        assert len(line_widget._segment_widgets) == 2

        # Remove the last segment
        line_widget._remove_segment(line_widget._segment_widgets[-1])
        assert len(line_widget._segment_widgets) == 1

    def test_cannot_remove_last_segment(self, text_panel):
        """Test that the last segment cannot be removed."""
        line_widget = text_panel._line_widgets[0]
        assert len(line_widget._segment_widgets) == 1

        # Try to remove the only segment
        line_widget._remove_segment(line_widget._segment_widgets[0])

        # Should still have one segment
        assert len(line_widget._segment_widgets) == 1

    def test_segment_config(self, text_panel):
        """Test that segment configuration is properly returned."""
        line_widget = text_panel._line_widgets[0]
        seg_widget = line_widget._segment_widgets[0]

        # Set some values
        seg_widget._content_edit.setText("Test Content")
        seg_widget._size_slider.setValue(16.0)

        config = seg_widget.get_config()

        assert config['content'] == "Test Content"
        assert config['font_size'] == 16.0


class TestTextSegmentWidget:
    """Tests for individual TextSegmentWidget."""

    def test_segment_styling(self, text_panel):
        """Test that segments have proper styling applied."""
        line_widget = text_panel._line_widgets[0]
        seg_widget = line_widget._segment_widgets[0]

        # Check that the widget has the expected stylesheet
        style = seg_widget.styleSheet()
        assert 'background-color' in style

    def test_segment_set_config(self, text_panel):
        """Test setting segment configuration."""
        line_widget = text_panel._line_widgets[0]
        seg_widget = line_widget._segment_widgets[0]

        config = {
            'content': 'Hello World',
            'font_family': 'Arial',
            'font_style': 'Bold',
            'font_size': 20.0,
            'letter_spacing': 5.0,
        }

        seg_widget.set_config(config)

        result = seg_widget.get_config()
        assert result['content'] == 'Hello World'
        assert result['font_style'] == 'Bold'
        assert result['font_size'] == 20.0
        assert result['letter_spacing'] == 5.0
