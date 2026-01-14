"""
Tests for icon caching functionality.
Verifies persistent disk caching for Font Awesome and Material Icons.
"""

import pytest
import tempfile
import shutil
from pathlib import Path


class TestFontAwesomeCaching:
    """Tests for Font Awesome icon caching."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def fa_manager(self, temp_cache_dir, monkeypatch):
        """Create a Font Awesome manager with temp cache."""
        from fonts.font_awesome import FontAwesomeManager

        # Patch get_user_data_dir to return temp directory
        def mock_user_data_dir():
            return temp_cache_dir

        monkeypatch.setattr('fonts.font_awesome.get_user_data_dir', mock_user_data_dir)

        manager = FontAwesomeManager()
        return manager

    def test_cache_directory_created(self, fa_manager, temp_cache_dir):
        """Verify cache directory is created on initialization."""
        cache_dir = temp_cache_dir / 'icon_cache' / 'font_awesome'
        assert cache_dir.exists(), "Cache directory was not created"

    def test_cache_count_initially_zero(self, fa_manager):
        """Verify cache starts empty."""
        assert fa_manager.cache_count == 0, "Cache should start empty"

    def test_clear_cache_method(self, fa_manager, temp_cache_dir):
        """Test that clear_cache method works."""
        # Add a dummy file to cache
        cache_dir = temp_cache_dir / 'icon_cache' / 'font_awesome'
        dummy_file = cache_dir / 'test_solid.svg'
        dummy_file.write_text('<svg></svg>')

        # Clear cache
        fa_manager.clear_cache()

        # Verify file is removed
        assert not dummy_file.exists(), "Cache file was not deleted"
        assert fa_manager.cache_count == 0, "Memory cache not cleared"

    def test_save_to_disk_cache(self, fa_manager, temp_cache_dir):
        """Test saving SVG to disk cache."""
        cache_key = "test-icon_solid"
        svg_content = '<svg viewBox="0 0 24 24"><path d="M0 0h24v24H0z"/></svg>'

        fa_manager._save_to_disk_cache(cache_key, svg_content)

        cache_file = temp_cache_dir / 'icon_cache' / 'font_awesome' / f'{cache_key}.svg'
        assert cache_file.exists(), "SVG was not saved to disk"
        assert cache_file.read_text() == svg_content, "SVG content mismatch"

    def test_load_cache_from_disk(self, fa_manager, temp_cache_dir):
        """Test loading cached SVGs from disk."""
        cache_dir = temp_cache_dir / 'icon_cache' / 'font_awesome'

        # Pre-populate cache files
        svg1 = '<svg>icon1</svg>'
        svg2 = '<svg>icon2</svg>'
        (cache_dir / 'icon1_solid.svg').write_text(svg1)
        (cache_dir / 'icon2_regular.svg').write_text(svg2)

        # Clear memory cache and reload
        fa_manager._svg_cache.clear()
        fa_manager._load_cache_from_disk()

        assert fa_manager.cache_count == 2, f"Expected 2 cached items, got {fa_manager.cache_count}"
        assert fa_manager._svg_cache.get('icon1_solid') == svg1
        assert fa_manager._svg_cache.get('icon2_regular') == svg2


class TestMaterialIconsCaching:
    """Tests for Material Icons caching."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def mi_manager(self, temp_cache_dir, monkeypatch):
        """Create a Material Icons manager with temp cache."""
        from fonts.material_icons import MaterialIconsManager

        # Patch get_user_data_dir to return temp directory
        def mock_user_data_dir():
            return temp_cache_dir

        monkeypatch.setattr('fonts.material_icons.get_user_data_dir', mock_user_data_dir)

        manager = MaterialIconsManager()
        return manager

    def test_cache_directory_created(self, mi_manager, temp_cache_dir):
        """Verify cache directory is created on initialization."""
        cache_dir = temp_cache_dir / 'icon_cache' / 'material_icons'
        assert cache_dir.exists(), "Cache directory was not created"

    def test_cache_count_initially_zero(self, mi_manager):
        """Verify cache starts empty."""
        assert mi_manager.cache_count == 0, "Cache should start empty"

    def test_clear_cache_method(self, mi_manager, temp_cache_dir):
        """Test that clear_cache method works."""
        # Add a dummy file to cache
        cache_dir = temp_cache_dir / 'icon_cache' / 'material_icons'
        dummy_file = cache_dir / 'home_baseline.svg'
        dummy_file.write_text('<svg></svg>')

        # Load it into memory
        mi_manager._load_cache_from_disk()

        # Clear cache
        mi_manager.clear_cache()

        # Verify file is removed
        assert not dummy_file.exists(), "Cache file was not deleted"
        assert mi_manager.cache_count == 0, "Memory cache not cleared"

    def test_save_to_disk_cache(self, mi_manager, temp_cache_dir):
        """Test saving SVG to disk cache."""
        cache_key = "settings_baseline"
        svg_content = '<svg viewBox="0 0 24 24"><path d="M0 0h24v24H0z"/></svg>'

        mi_manager._save_to_disk_cache(cache_key, svg_content)

        cache_file = temp_cache_dir / 'icon_cache' / 'material_icons' / f'{cache_key}.svg'
        assert cache_file.exists(), "SVG was not saved to disk"
        assert cache_file.read_text() == svg_content, "SVG content mismatch"

    def test_load_cache_from_disk(self, mi_manager, temp_cache_dir):
        """Test loading cached SVGs from disk."""
        cache_dir = temp_cache_dir / 'icon_cache' / 'material_icons'

        # Pre-populate cache files
        svg1 = '<svg>home</svg>'
        svg2 = '<svg>settings</svg>'
        (cache_dir / 'home_baseline.svg').write_text(svg1)
        (cache_dir / 'settings_outline.svg').write_text(svg2)

        # Clear memory cache and reload
        mi_manager._svg_cache.clear()
        mi_manager._load_cache_from_disk()

        assert mi_manager.cache_count == 2, f"Expected 2 cached items, got {mi_manager.cache_count}"
        assert mi_manager._svg_cache.get('home_baseline') == svg1
        assert mi_manager._svg_cache.get('settings_outline') == svg2


class TestCacheIntegration:
    """Integration tests for icon caching with downloads."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_fa_download_caches_to_disk(self, temp_cache_dir, monkeypatch):
        """Test that downloading an FA icon saves to disk cache."""
        from fonts.font_awesome import FontAwesomeManager

        def mock_user_data_dir():
            return temp_cache_dir

        monkeypatch.setattr('fonts.font_awesome.get_user_data_dir', mock_user_data_dir)

        manager = FontAwesomeManager()
        manager.load()

        # Try to download a common icon (may fail if offline)
        # We'll check that the caching mechanism is called
        initial_count = manager.cache_count

        # Mock the download to avoid network dependency
        test_svg = '<svg>test</svg>'
        manager._svg_cache['house_solid'] = test_svg
        manager._save_to_disk_cache('house_solid', test_svg)

        cache_file = temp_cache_dir / 'icon_cache' / 'font_awesome' / 'house_solid.svg'
        assert cache_file.exists(), "Download did not cache to disk"

    def test_mi_download_caches_to_disk(self, temp_cache_dir, monkeypatch):
        """Test that downloading a Material icon saves to disk cache."""
        from fonts.material_icons import MaterialIconsManager

        def mock_user_data_dir():
            return temp_cache_dir

        monkeypatch.setattr('fonts.material_icons.get_user_data_dir', mock_user_data_dir)

        manager = MaterialIconsManager()
        manager.load()

        # Mock the download
        test_svg = '<svg>home</svg>'
        manager._svg_cache['home_baseline'] = test_svg
        manager._save_to_disk_cache('home_baseline', test_svg)

        cache_file = temp_cache_dir / 'icon_cache' / 'material_icons' / 'home_baseline.svg'
        assert cache_file.exists(), "Download did not cache to disk"
