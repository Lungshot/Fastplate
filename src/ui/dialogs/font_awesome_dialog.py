"""
Font Awesome Icons Browser Dialog
Dialog for browsing and selecting Font Awesome free icons.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGridLayout, QScrollArea, QWidget,
    QFrame, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QByteArray
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtSvg import QSvgRenderer

from fonts.font_awesome import get_font_awesome_manager, FontAwesomeIcon, ICON_STYLES
from ui.widgets.slider_spin import FocusComboBox


class FontAwesomeIconButton(QPushButton):
    """Button displaying a single Font Awesome Icon."""

    icon_selected = pyqtSignal(object)

    def __init__(self, icon: FontAwesomeIcon, parent=None):
        super().__init__(parent)
        self.icon = icon
        self._svg_content = None

        self.setFixedSize(50, 50)
        self.setToolTip(f"{icon.display_name}\nStyle: {icon.style}\nCategory: {icon.category}")

        self.setStyleSheet("""
            QPushButton {
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

        self.clicked.connect(lambda: self.icon_selected.emit(self.icon))

        # Show icon name as placeholder
        self.setText(icon.name[:3])

    def set_svg_content(self, svg_content: str):
        """Set the SVG content and render as icon."""
        self._svg_content = svg_content
        if svg_content:
            pixmap = self._render_svg(svg_content, 40)
            if pixmap:
                self.setIcon(pixmap)
                self.setIconSize(pixmap.size())
                self.setText("")

    def _render_svg(self, svg_content: str, size: int) -> QPixmap:
        """Render SVG content to a QPixmap."""
        try:
            # Modify SVG to use light color for visibility
            svg_colored = svg_content.replace('fill="black"', 'fill="#e0e0e0"')
            svg_colored = svg_colored.replace('fill="#000000"', 'fill="#e0e0e0"')
            svg_colored = svg_colored.replace('fill="currentColor"', 'fill="#e0e0e0"')
            # If no fill specified, add fill attribute
            if 'fill=' not in svg_colored:
                svg_colored = svg_colored.replace('<svg ', '<svg fill="#e0e0e0" ')

            renderer = QSvgRenderer(QByteArray(svg_colored.encode()))
            if not renderer.isValid():
                return None

            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()

            return pixmap
        except Exception as e:
            print(f"Error rendering SVG: {e}")
            return None

    def setIcon(self, pixmap: QPixmap):
        """Set the button icon from a pixmap."""
        from PyQt5.QtGui import QIcon
        super().setIcon(QIcon(pixmap))


class FontAwesomeDialog(QDialog):
    """Dialog for browsing and selecting Font Awesome free icons."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._selected_icon = None
        self._selected_svg = None
        self._manager = get_font_awesome_manager()
        self._icon_buttons = []
        self._current_style = 'solid'

        self._setup_ui()
        self._load_icons()

    def _setup_ui(self):
        self.setWindowTitle("Select Icon (Font Awesome)")
        self.setMinimumSize(650, 550)
        self.resize(750, 600)

        layout = QVBoxLayout(self)

        # Search bar
        search_layout = QHBoxLayout()

        search_layout.addWidget(QLabel("Search:"))
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Type to search icons...")
        self._search_edit.textChanged.connect(self._on_search)
        search_layout.addWidget(self._search_edit, stretch=1)

        layout.addLayout(search_layout)

        # Category and Style filters
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Category:"))
        self._category_combo = FocusComboBox()
        self._category_combo.addItem("All Categories", "all")
        self._category_combo.currentIndexChanged.connect(self._on_category_changed)
        filter_layout.addWidget(self._category_combo, stretch=1)

        filter_layout.addSpacing(20)

        filter_layout.addWidget(QLabel("Style:"))
        self._style_combo = FocusComboBox()
        self._style_combo.addItem("Solid", "solid")
        self._style_combo.addItem("Regular", "regular")
        self._style_combo.addItem("Brands", "brands")
        self._style_combo.currentIndexChanged.connect(self._on_style_changed)
        filter_layout.addWidget(self._style_combo)

        layout.addLayout(filter_layout)

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

        # Loading indicator
        self._loading_label = QLabel("")
        self._loading_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self._loading_label)

        # Selected icon display
        selected_frame = QFrame()
        selected_frame.setFrameStyle(QFrame.StyledPanel)
        selected_layout = QHBoxLayout(selected_frame)

        self._selected_label = QLabel("No icon selected")
        self._selected_label.setStyleSheet("font-size: 14px;")
        selected_layout.addWidget(self._selected_label)

        selected_layout.addStretch()

        self._selected_preview = QLabel()
        self._selected_preview.setFixedSize(48, 48)
        self._selected_preview.setAlignment(Qt.AlignCenter)
        self._selected_preview.setStyleSheet("""
            QLabel {
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
        self._size_combo.addItems(["8mm", "10mm", "12mm", "14mm", "16mm", "20mm", "25mm", "30mm"])
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
        self._insert_btn.clicked.connect(self._on_insert)
        btn_layout.addWidget(self._insert_btn)

        layout.addLayout(btn_layout)

    def _load_icons(self):
        """Load icons from Font Awesome manager."""
        if not self._manager.load():
            self._search_edit.setPlaceholderText("Error: Could not load Font Awesome icons data")
            return

        # Populate categories
        for cat_id, cat_name, count in self._manager.get_categories():
            self._category_combo.addItem(f"{cat_name} ({count})", cat_id)

        # Show popular icons initially
        self._display_icons(self._manager.get_popular_icons(100))

    def _display_icons(self, icons: list):
        """Display icons in the grid."""
        # Clear existing icons
        while self._icons_layout.count():
            item = self._icons_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._icon_buttons = []

        # Add new icons
        cols = 11
        for i, icon in enumerate(icons):
            row = i // cols
            col = i % cols

            btn = FontAwesomeIconButton(icon)
            btn.icon_selected.connect(self._on_icon_selected)
            self._icons_layout.addWidget(btn, row, col)
            self._icon_buttons.append(btn)

        # Load SVG previews in background
        self._load_svg_previews()

    def _load_svg_previews(self):
        """Load SVG previews for visible icons."""
        # Load first batch immediately
        for i, btn in enumerate(self._icon_buttons[:20]):
            svg = self._manager.download_svg(btn.icon.name, btn.icon.style)
            if svg:
                btn.set_svg_content(svg)

        # Schedule remaining icons
        if len(self._icon_buttons) > 20:
            self._loading_label.setText(f"Loading icon previews...")
            QTimer.singleShot(100, lambda: self._load_remaining_previews(20))

    def _load_remaining_previews(self, start_index: int):
        """Load remaining SVG previews in batches."""
        batch_size = 10
        end_index = min(start_index + batch_size, len(self._icon_buttons))

        for i in range(start_index, end_index):
            btn = self._icon_buttons[i]
            svg = self._manager.download_svg(btn.icon.name, btn.icon.style)
            if svg:
                btn.set_svg_content(svg)

        if end_index < len(self._icon_buttons):
            QTimer.singleShot(50, lambda: self._load_remaining_previews(end_index))
        else:
            self._loading_label.setText("")

    def _on_search(self, text):
        """Handle search text change."""
        if not text:
            # Show popular when search is cleared
            self._display_icons(self._manager.get_popular_icons(100))
            return

        # Get current category and style
        category = None
        cat_data = self._category_combo.currentData()
        if cat_data != "all":
            category = cat_data

        style = None
        style_data = self._style_combo.currentData()
        if style_data != 'solid':
            style = style_data

        # Search
        results = self._manager.search(text, category, style, limit=200)
        self._display_icons(results)

    def _on_category_changed(self, index):
        """Handle category selection change."""
        cat_data = self._category_combo.currentData()

        if cat_data == "all":
            if self._search_edit.text():
                self._on_search(self._search_edit.text())
            else:
                self._display_icons(self._manager.get_popular_icons(100))
        else:
            icons = self._manager.get_icons_by_category(cat_data)[:200]
            self._display_icons(icons)

    def _on_style_changed(self, index):
        """Handle style selection change."""
        style = self._style_combo.currentData() or 'solid'
        self._current_style = style

        # Filter icons by style
        if self._search_edit.text():
            self._on_search(self._search_edit.text())
        else:
            icons = self._manager.get_icons_by_style(style)[:200]
            if not icons:
                icons = self._manager.get_popular_icons(100)
            self._display_icons(icons)

        # Update selected preview if we have a selection
        if self._selected_icon:
            self._update_selected_preview()

    def _on_icon_selected(self, icon: FontAwesomeIcon):
        """Handle icon selection."""
        self._selected_icon = icon
        self._selected_label.setText(f"{icon.display_name} ({icon.name})")
        self._insert_btn.setEnabled(True)

        self._update_selected_preview()

    def _update_selected_preview(self):
        """Update the selected icon preview."""
        if not self._selected_icon:
            return

        svg = self._manager.download_svg(self._selected_icon.name, self._selected_icon.style)

        if svg:
            self._selected_svg = svg
            pixmap = self._render_svg_preview(svg, 40)
            if pixmap:
                self._selected_preview.setPixmap(pixmap)

    def _render_svg_preview(self, svg_content: str, size: int) -> QPixmap:
        """Render SVG content to a QPixmap for preview."""
        try:
            # Modify SVG to use light color for visibility
            svg_colored = svg_content.replace('fill="black"', 'fill="#e0e0e0"')
            svg_colored = svg_colored.replace('fill="#000000"', 'fill="#e0e0e0"')
            svg_colored = svg_colored.replace('fill="currentColor"', 'fill="#e0e0e0"')
            if 'fill=' not in svg_colored:
                svg_colored = svg_colored.replace('<svg ', '<svg fill="#e0e0e0" ')

            renderer = QSvgRenderer(QByteArray(svg_colored.encode()))
            if not renderer.isValid():
                return None

            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()

            return pixmap
        except Exception as e:
            print(f"Error rendering SVG preview: {e}")
            return None

    def _on_insert(self):
        """Handle insert button click."""
        if not self._selected_icon:
            return

        # Ensure we have SVG content
        if not self._selected_svg:
            self._selected_svg = self._manager.download_svg(
                self._selected_icon.name,
                self._selected_icon.style
            )

        if not self._selected_svg:
            QMessageBox.warning(
                self,
                "Download Failed",
                f"Could not download the icon '{self._selected_icon.name}'.\n"
                "Please check your internet connection and try again."
            )
            return

        self.accept()

    def get_selected_icon(self) -> dict:
        """Get the selected icon data including SVG content."""
        if not self._selected_icon or not self._selected_svg:
            return None

        size_text = self._size_combo.currentText()
        size = float(size_text.replace("mm", ""))

        return {
            'name': self._selected_icon.name,
            'style': self._selected_icon.style,
            'svg_content': self._selected_svg,
            'size': size,
            'category': self._selected_icon.category,
        }
