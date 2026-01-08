"""
Icon Browser Dialog
Dialog for browsing and selecting Nerd Font icons.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGridLayout, QScrollArea, QWidget,
    QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from fonts.nerd_fonts import get_nerd_fonts_manager, NerdFontGlyph
from ui.widgets.slider_spin import FocusComboBox


class IconButton(QPushButton):
    """Button displaying a single Nerd Font icon."""
    
    icon_selected = pyqtSignal(object)
    
    def __init__(self, glyph: NerdFontGlyph, font: QFont, parent=None):
        super().__init__(parent)
        self.glyph = glyph
        
        self.setFixedSize(50, 50)
        self.setFont(font)
        self.setText(glyph.unicode_char)
        self.setToolTip(f"{glyph.display_name}\n{glyph.name}\nCode: {glyph.code}")
        
        self.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                border: 1px solid #555;
                border-radius: 5px;
                background-color: #404040;
            }
            QPushButton:hover {
                background-color: #505050;
                border-color: #888;
            }
            QPushButton:pressed {
                background-color: #606060;
            }
        """)
        
        self.clicked.connect(lambda: self.icon_selected.emit(self.glyph))


class IconBrowserDialog(QDialog):
    """Dialog for browsing and selecting Nerd Font icons."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._selected_glyph = None
        self._nerd_fonts = get_nerd_fonts_manager()
        self._icon_font = None
        
        self._setup_ui()
        self._load_icons()
    
    def _setup_ui(self):
        self.setWindowTitle("Select Icon (Nerd Fonts)")
        self.setMinimumSize(600, 500)
        self.resize(700, 550)
        
        layout = QVBoxLayout(self)
        
        # Search bar
        search_layout = QHBoxLayout()
        
        search_layout.addWidget(QLabel("Search:"))
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Type to search icons...")
        self._search_edit.textChanged.connect(self._on_search)
        search_layout.addWidget(self._search_edit, stretch=1)
        
        layout.addLayout(search_layout)
        
        # Category filter
        cat_layout = QHBoxLayout()
        
        cat_layout.addWidget(QLabel("Category:"))
        self._category_combo = FocusComboBox()
        self._category_combo.addItem("All Categories", "all")
        self._category_combo.currentIndexChanged.connect(self._on_category_changed)
        cat_layout.addWidget(self._category_combo, stretch=1)
        
        layout.addLayout(cat_layout)
        
        # Icon grid in scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self._icons_container = QWidget()
        self._icons_layout = QGridLayout(self._icons_container)
        self._icons_layout.setSpacing(5)
        self._icons_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        scroll.setWidget(self._icons_container)
        layout.addWidget(scroll, stretch=1)
        
        # Selected icon display
        selected_frame = QFrame()
        selected_frame.setFrameStyle(QFrame.StyledPanel)
        selected_layout = QHBoxLayout(selected_frame)
        
        self._selected_label = QLabel("No icon selected")
        self._selected_label.setStyleSheet("font-size: 14px;")
        selected_layout.addWidget(self._selected_label)
        
        self._selected_preview = QLabel()
        self._selected_preview.setFixedSize(40, 40)
        self._selected_preview.setAlignment(Qt.AlignCenter)
        self._selected_preview.setStyleSheet("""
            QLabel {
                font-size: 28px;
                border: 1px solid #555;
                border-radius: 5px;
                background-color: #353535;
            }
        """)
        selected_layout.addWidget(self._selected_preview)
        
        layout.addWidget(selected_frame)
        
        # Size option
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Icon Size:"))
        self._size_combo = FocusComboBox()
        self._size_combo.addItems(["8mm", "10mm", "12mm", "14mm", "16mm", "20mm"])
        self._size_combo.setCurrentText("12mm")
        size_layout.addWidget(self._size_combo)
        size_layout.addStretch()
        layout.addLayout(size_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        self._insert_btn = QPushButton("Insert Icon")
        self._insert_btn.setEnabled(False)
        self._insert_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self._insert_btn)
        
        layout.addLayout(btn_layout)
        
        # Try to load Nerd Font
        self._try_load_font()
    
    def _try_load_font(self):
        """Try to load a Nerd Font for displaying icons."""
        from pathlib import Path
        
        # Check for bundled font
        bundled_font = Path(__file__).parent.parent.parent / 'resources' / 'fonts'
        
        # Common Nerd Font names to search for
        font_names = [
            "JetBrainsMono Nerd Font",
            "JetBrainsMonoNerdFont-Regular",
            "FiraCode Nerd Font", 
            "Hack Nerd Font",
            "DejaVuSansMono Nerd Font",
        ]
        
        # For now, use system font that might have the glyphs
        self._icon_font = QFont("Segoe UI Symbol", 24)
    
    def _load_icons(self):
        """Load icons from Nerd Fonts manager."""
        if not self._nerd_fonts.load():
            self._search_edit.setPlaceholderText("Error: Could not load Nerd Fonts data")
            return
        
        # Populate categories
        for cat_id, cat_name, count in self._nerd_fonts.get_categories():
            self._category_combo.addItem(f"{cat_name} ({count})", cat_id)
        
        # Show popular icons initially
        self._display_icons(self._nerd_fonts.get_popular_glyphs(100))
    
    def _display_icons(self, glyphs: list):
        """Display icons in the grid."""
        # Clear existing icons
        while self._icons_layout.count():
            item = self._icons_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add new icons
        cols = 10
        for i, glyph in enumerate(glyphs):
            row = i // cols
            col = i % cols
            
            btn = IconButton(glyph, self._icon_font)
            btn.icon_selected.connect(self._on_icon_selected)
            self._icons_layout.addWidget(btn, row, col)
    
    def _on_search(self, text):
        """Handle search text change."""
        if not text:
            # Show popular when search is cleared
            self._display_icons(self._nerd_fonts.get_popular_glyphs(100))
            return
        
        # Get current category
        category = None
        cat_data = self._category_combo.currentData()
        if cat_data != "all":
            category = cat_data
        
        # Search
        results = self._nerd_fonts.search(text, category, limit=200)
        self._display_icons(results)
    
    def _on_category_changed(self, index):
        """Handle category selection change."""
        cat_data = self._category_combo.currentData()
        
        if cat_data == "all":
            if self._search_edit.text():
                self._on_search(self._search_edit.text())
            else:
                self._display_icons(self._nerd_fonts.get_popular_glyphs(100))
        else:
            glyphs = self._nerd_fonts.get_glyphs_by_category(cat_data)[:200]
            self._display_icons(glyphs)
    
    def _on_icon_selected(self, glyph: NerdFontGlyph):
        """Handle icon selection."""
        self._selected_glyph = glyph
        self._selected_label.setText(f"{glyph.display_name} ({glyph.name})")
        self._selected_preview.setText(glyph.unicode_char)
        self._insert_btn.setEnabled(True)
    
    def get_selected_icon(self) -> dict:
        """Get the selected icon data."""
        if not self._selected_glyph:
            return None
        
        size_text = self._size_combo.currentText()
        size = float(size_text.replace("mm", ""))
        
        return {
            'name': self._selected_glyph.name,
            'char': self._selected_glyph.unicode_char,
            'code': self._selected_glyph.code,
            'size': size,
        }
