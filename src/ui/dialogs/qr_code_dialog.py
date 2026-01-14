"""
QR Code Dialog
Dialog for creating and configuring QR codes.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox,
    QPushButton, QDialogButtonBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor


class QRCodeDialog(QDialog):
    """Dialog for creating QR codes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add QR Code")
        self.setMinimumSize(500, 400)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Data input section
        data_group = QGroupBox("QR Code Data")
        data_layout = QVBoxLayout(data_group)

        # Data type selector
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self._type_combo = QComboBox()
        self._type_combo.addItems(["Text/URL", "Email", "Phone", "WiFi", "vCard"])
        type_layout.addWidget(self._type_combo)
        type_layout.addStretch()
        data_layout.addLayout(type_layout)

        # Text input
        self._data_edit = QTextEdit()
        self._data_edit.setPlaceholderText("Enter text, URL, or data to encode...")
        self._data_edit.setMaximumHeight(80)
        data_layout.addWidget(self._data_edit)

        layout.addWidget(data_group)

        # Settings section
        settings_group = QGroupBox("QR Code Settings")
        settings_layout = QFormLayout(settings_group)

        # Size
        self._size_spin = QDoubleSpinBox()
        self._size_spin.setRange(5.0, 100.0)
        self._size_spin.setValue(20.0)
        self._size_spin.setSuffix(" mm")
        settings_layout.addRow("Size:", self._size_spin)

        # Depth
        self._depth_spin = QDoubleSpinBox()
        self._depth_spin.setRange(0.5, 10.0)
        self._depth_spin.setValue(1.0)
        self._depth_spin.setSuffix(" mm")
        settings_layout.addRow("Depth:", self._depth_spin)

        # Style
        self._style_combo = QComboBox()
        self._style_combo.addItems(["Raised", "Engraved", "Cutout"])
        settings_layout.addRow("Style:", self._style_combo)

        # Error correction
        self._ec_combo = QComboBox()
        self._ec_combo.addItems(["L - Low (7%)", "M - Medium (15%)", "Q - Quartile (25%)", "H - High (30%)"])
        self._ec_combo.setCurrentIndex(1)  # Medium default
        settings_layout.addRow("Error Correction:", self._ec_combo)

        # Position
        pos_layout = QHBoxLayout()
        self._pos_x_spin = QDoubleSpinBox()
        self._pos_x_spin.setRange(-200.0, 200.0)
        self._pos_x_spin.setValue(0.0)
        self._pos_x_spin.setSuffix(" mm")
        pos_layout.addWidget(QLabel("X:"))
        pos_layout.addWidget(self._pos_x_spin)

        self._pos_y_spin = QDoubleSpinBox()
        self._pos_y_spin.setRange(-200.0, 200.0)
        self._pos_y_spin.setValue(0.0)
        self._pos_y_spin.setSuffix(" mm")
        pos_layout.addWidget(QLabel("Y:"))
        pos_layout.addWidget(self._pos_y_spin)
        pos_layout.addStretch()

        settings_layout.addRow("Position:", pos_layout)

        layout.addWidget(settings_group)

        # Preview section
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)

        self._preview_label = QLabel()
        self._preview_label.setAlignment(Qt.AlignCenter)
        self._preview_label.setMinimumSize(150, 150)
        self._preview_label.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        preview_layout.addWidget(self._preview_label)

        # Preview button
        preview_btn = QPushButton("Generate Preview")
        preview_btn.clicked.connect(self._update_preview)
        preview_layout.addWidget(preview_btn)

        layout.addWidget(preview_group)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _connect_signals(self):
        """Connect signals."""
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)

    def _on_type_changed(self, index: int):
        """Handle data type change."""
        placeholders = {
            0: "Enter text, URL, or data to encode...",
            1: "email@example.com",
            2: "+1234567890",
            3: "WIFI:T:WPA;S:NetworkName;P:Password;;",
            4: "BEGIN:VCARD\nVERSION:3.0\nN:LastName;FirstName\nEND:VCARD",
        }
        self._data_edit.setPlaceholderText(placeholders.get(index, ""))

    def _update_preview(self):
        """Generate and show QR code preview."""
        data = self._data_edit.toPlainText().strip()
        if not data:
            self._preview_label.setText("Enter data to preview")
            return

        try:
            import qrcode

            ec_map = {0: 'L', 1: 'M', 2: 'Q', 3: 'H'}
            ec = ec_map.get(self._ec_combo.currentIndex(), 'M')

            ec_levels = {
                'L': qrcode.constants.ERROR_CORRECT_L,
                'M': qrcode.constants.ERROR_CORRECT_M,
                'Q': qrcode.constants.ERROR_CORRECT_Q,
                'H': qrcode.constants.ERROR_CORRECT_H,
            }

            qr = qrcode.QRCode(
                version=None,
                error_correction=ec_levels[ec],
                box_size=4,
                border=2,
            )
            qr.add_data(data)
            qr.make(fit=True)

            # Create PIL image
            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to QPixmap
            img_data = img.tobytes("raw", "L")
            qimg = QImage(img_data, img.size[0], img.size[1], QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(qimg)

            # Scale to fit preview area
            scaled = pixmap.scaled(140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._preview_label.setPixmap(scaled)

        except ImportError:
            # Draw a placeholder pattern
            self._preview_label.setText("QR preview\n(qrcode lib\nnot installed)")
        except Exception as e:
            self._preview_label.setText(f"Error:\n{str(e)[:50]}")

    def get_config(self) -> dict:
        """Get the QR code configuration."""
        ec_map = {0: 'L', 1: 'M', 2: 'Q', 3: 'H'}
        style_map = {0: 'raised', 1: 'engraved', 2: 'cutout'}

        return {
            'data': self._data_edit.toPlainText().strip(),
            'size': self._size_spin.value(),
            'depth': self._depth_spin.value(),
            'style': style_map.get(self._style_combo.currentIndex(), 'raised'),
            'error_correction': ec_map.get(self._ec_combo.currentIndex(), 'M'),
            'position_x': self._pos_x_spin.value(),
            'position_y': self._pos_y_spin.value(),
        }
