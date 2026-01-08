"""
Custom widgets for the nameplate generator UI.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSlider, QDoubleSpinBox,
    QSpinBox, QLabel, QComboBox, QLineEdit, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QWheelEvent


class FocusComboBox(QComboBox):
    """
    ComboBox that only responds to wheel events when it has focus.
    This prevents accidental value changes when scrolling over the widget.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # Set focus policy to StrongFocus so it can receive focus
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, event: QWheelEvent):
        """Only process wheel events if the combo box has focus."""
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            # Pass the event to the parent for scrolling
            event.ignore()


class FocusSpinBox(QSpinBox):
    """
    SpinBox that only responds to wheel events when it has focus.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, event: QWheelEvent):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()


class FocusDoubleSpinBox(QDoubleSpinBox):
    """
    DoubleSpinBox that only responds to wheel events when it has focus.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, event: QWheelEvent):
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()


class SliderSpinBox(QWidget):
    """
    Combined slider and spinbox widget for numeric input.
    Includes optional reset-to-default button.
    """

    valueChanged = pyqtSignal(float)

    def __init__(self, label: str = "", min_val: float = 0, max_val: float = 100,
                 default: float = 50, decimals: int = 1, suffix: str = "",
                 show_reset: bool = True, parent=None):
        super().__init__(parent)

        self._decimals = decimals
        self._multiplier = 10 ** decimals
        self._default = default

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Label
        if label:
            self._label = QLabel(label)
            self._label.setMinimumWidth(80)
            layout.addWidget(self._label)

        # Slider
        self._slider = QSlider(Qt.Horizontal)
        self._slider.setMinimum(int(min_val * self._multiplier))
        self._slider.setMaximum(int(max_val * self._multiplier))
        self._slider.setValue(int(default * self._multiplier))
        self._slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self._slider, stretch=1)

        # Spinbox
        self._spinbox = FocusDoubleSpinBox()
        self._spinbox.setMinimum(min_val)
        self._spinbox.setMaximum(max_val)
        self._spinbox.setValue(default)
        self._spinbox.setDecimals(decimals)
        self._spinbox.setSuffix(suffix)
        self._spinbox.setMinimumWidth(80)
        self._spinbox.valueChanged.connect(self._on_spinbox_changed)
        layout.addWidget(self._spinbox)

        # Reset button
        if show_reset:
            self._reset_btn = QPushButton("↺")
            self._reset_btn.setFixedSize(22, 22)
            self._reset_btn.setToolTip(f"Reset to default ({default}{suffix})")
            self._reset_btn.setStyleSheet("""
                QPushButton {
                    font-size: 12px;
                    padding: 0;
                    border: 1px solid #555;
                    border-radius: 3px;
                    background-color: #404040;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
            """)
            self._reset_btn.clicked.connect(self.reset_to_default)
            layout.addWidget(self._reset_btn)
        else:
            self._reset_btn = None

        self._updating = False
    
    def _on_slider_changed(self, value):
        if self._updating:
            return
        self._updating = True
        float_val = value / self._multiplier
        self._spinbox.setValue(float_val)
        self.valueChanged.emit(float_val)
        self._updating = False
    
    def _on_spinbox_changed(self, value):
        if self._updating:
            return
        self._updating = True
        self._slider.setValue(int(value * self._multiplier))
        self.valueChanged.emit(value)
        self._updating = False
    
    def value(self) -> float:
        return self._spinbox.value()
    
    def setValue(self, value: float):
        self._updating = True
        self._spinbox.setValue(value)
        self._slider.setValue(int(value * self._multiplier))
        self._updating = False
    
    def setRange(self, min_val: float, max_val: float):
        self._slider.setMinimum(int(min_val * self._multiplier))
        self._slider.setMaximum(int(max_val * self._multiplier))
        self._spinbox.setMinimum(min_val)
        self._spinbox.setMaximum(max_val)

    def reset_to_default(self):
        """Reset to the default value."""
        self.setValue(self._default)

    def default(self) -> float:
        """Get the default value."""
        return self._default


class ResetableComboBox(QWidget):
    """ComboBox with optional reset-to-default button."""

    currentIndexChanged = pyqtSignal(int)
    currentTextChanged = pyqtSignal(str)

    def __init__(self, default_text: str = "", show_reset: bool = True, parent=None):
        super().__init__(parent)

        self._default_text = default_text

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._combo = FocusComboBox()
        self._combo.currentIndexChanged.connect(self.currentIndexChanged.emit)
        self._combo.currentTextChanged.connect(self.currentTextChanged.emit)
        layout.addWidget(self._combo, stretch=1)

        if show_reset:
            self._reset_btn = QPushButton("↺")
            self._reset_btn.setFixedSize(22, 22)
            self._reset_btn.setToolTip(f"Reset to default ({default_text})")
            self._reset_btn.setStyleSheet("""
                QPushButton {
                    font-size: 12px;
                    padding: 0;
                    border: 1px solid #555;
                    border-radius: 3px;
                    background-color: #404040;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
            """)
            self._reset_btn.clicked.connect(self.reset_to_default)
            layout.addWidget(self._reset_btn)
        else:
            self._reset_btn = None

    def addItem(self, text: str, data=None):
        self._combo.addItem(text, data)

    def addItems(self, items: list):
        self._combo.addItems(items)

    def clear(self):
        self._combo.clear()

    def currentText(self) -> str:
        return self._combo.currentText()

    def currentIndex(self) -> int:
        return self._combo.currentIndex()

    def setCurrentText(self, text: str):
        self._combo.setCurrentText(text)

    def setCurrentIndex(self, index: int):
        self._combo.setCurrentIndex(index)

    def currentData(self):
        return self._combo.currentData()

    def reset_to_default(self):
        """Reset to the default value."""
        if self._default_text:
            self._combo.setCurrentText(self._default_text)

    def setDefault(self, text: str):
        """Set the default text."""
        self._default_text = text
        if self._reset_btn:
            self._reset_btn.setToolTip(f"Reset to default ({text})")


class LabeledComboBox(QWidget):
    """ComboBox with a label."""

    currentIndexChanged = pyqtSignal(int)
    currentTextChanged = pyqtSignal(str)

    def __init__(self, label: str = "", items: list = None, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if label:
            self._label = QLabel(label)
            self._label.setMinimumWidth(80)
            layout.addWidget(self._label)

        self._combo = FocusComboBox()
        if items:
            self._combo.addItems(items)
        self._combo.currentIndexChanged.connect(self.currentIndexChanged.emit)
        self._combo.currentTextChanged.connect(self.currentTextChanged.emit)
        layout.addWidget(self._combo, stretch=1)
    
    def addItem(self, text: str, data=None):
        self._combo.addItem(text, data)
    
    def addItems(self, items: list):
        self._combo.addItems(items)
    
    def clear(self):
        self._combo.clear()
    
    def currentText(self) -> str:
        return self._combo.currentText()
    
    def currentIndex(self) -> int:
        return self._combo.currentIndex()
    
    def setCurrentText(self, text: str):
        self._combo.setCurrentText(text)
    
    def setCurrentIndex(self, index: int):
        self._combo.setCurrentIndex(index)
    
    def currentData(self):
        return self._combo.currentData()


class LabeledLineEdit(QWidget):
    """LineEdit with a label."""
    
    textChanged = pyqtSignal(str)
    editingFinished = pyqtSignal()
    
    def __init__(self, label: str = "", placeholder: str = "", parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if label:
            self._label = QLabel(label)
            self._label.setMinimumWidth(80)
            layout.addWidget(self._label)
        
        self._edit = QLineEdit()
        if placeholder:
            self._edit.setPlaceholderText(placeholder)
        self._edit.textChanged.connect(self.textChanged.emit)
        self._edit.editingFinished.connect(self.editingFinished.emit)
        layout.addWidget(self._edit, stretch=1)
    
    def text(self) -> str:
        return self._edit.text()
    
    def setText(self, text: str):
        self._edit.setText(text)
    
    def setPlaceholderText(self, text: str):
        self._edit.setPlaceholderText(text)


class CollapsibleSection(QWidget):
    """A collapsible section widget."""
    
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        
        self._expanded = True
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header button
        self._header = QPushButton(f"▼ {title}")
        self._header.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 5px;
                background-color: #404040;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)
        self._header.clicked.connect(self._toggle)
        layout.addWidget(self._header)
        
        # Content frame
        self._content = QFrame()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(10, 5, 5, 5)
        layout.addWidget(self._content)
        
        self._title = title
    
    def _toggle(self):
        self._expanded = not self._expanded
        self._content.setVisible(self._expanded)
        arrow = "▼" if self._expanded else "▶"
        self._header.setText(f"{arrow} {self._title}")
    
    def addWidget(self, widget: QWidget):
        self._content_layout.addWidget(widget)
    
    def addLayout(self, layout):
        self._content_layout.addLayout(layout)
    
    def setExpanded(self, expanded: bool):
        if expanded != self._expanded:
            self._toggle()


class ColorButton(QPushButton):
    """Button that shows and allows selecting a color."""
    
    colorChanged = pyqtSignal(tuple)
    
    def __init__(self, color: tuple = (100, 150, 200), parent=None):
        super().__init__(parent)
        self._color = color
        self._update_style()
        self.clicked.connect(self._on_clicked)
    
    def _update_style(self):
        r, g, b = self._color[:3]
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgb({r}, {g}, {b});
                border: 1px solid #666;
                min-width: 40px;
                min-height: 25px;
            }}
        """)
    
    def _on_clicked(self):
        from PyQt5.QtWidgets import QColorDialog
        from PyQt5.QtGui import QColor
        
        current = QColor(*self._color[:3])
        color = QColorDialog.getColor(current, self, "Select Color")
        
        if color.isValid():
            self._color = (color.red(), color.green(), color.blue())
            self._update_style()
            self.colorChanged.emit(self._color)
    
    def color(self) -> tuple:
        return self._color
    
    def setColor(self, color: tuple):
        self._color = color
        self._update_style()
