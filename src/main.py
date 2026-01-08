"""
3D Nameplate Generator - Main Entry Point
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def main():
    """Main application entry point."""
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont
    
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    
    # Set application info
    app.setApplicationName("Nameplate Generator")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("NameplateGen")
    
    # Set dark theme
    app.setStyle("Fusion")
    
    # Dark palette
    from PyQt5.QtGui import QPalette, QColor
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(35, 35, 35))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor(35, 35, 35))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    app.setPalette(palette)
    
    # Stylesheet for additional styling
    app.setStyleSheet("""
        QGroupBox {
            font-weight: bold;
            border: 1px solid #555;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QTabWidget::pane {
            border: 1px solid #555;
            border-radius: 5px;
        }
        QTabBar::tab {
            background-color: #404040;
            padding: 8px 20px;
            margin-right: 2px;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        }
        QTabBar::tab:selected {
            background-color: #505050;
        }
        QTabBar::tab:hover {
            background-color: #454545;
        }
        QPushButton {
            padding: 5px 15px;
            border-radius: 3px;
            background-color: #404040;
            border: 1px solid #555;
        }
        QPushButton:hover {
            background-color: #505050;
        }
        QPushButton:pressed {
            background-color: #606060;
        }
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
            padding: 5px;
            border-radius: 3px;
            background-color: #404040;
            border: 1px solid #555;
        }
        QSlider::groove:horizontal {
            height: 6px;
            background: #404040;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #2a82da;
            width: 16px;
            margin: -5px 0;
            border-radius: 8px;
        }
        QScrollBar:vertical {
            background: #353535;
            width: 12px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical {
            background: #555;
            border-radius: 6px;
            min-height: 20px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QListWidget {
            background-color: #353535;
            border: 1px solid #555;
            border-radius: 5px;
        }
        QListWidget::item {
            padding: 5px;
        }
        QListWidget::item:selected {
            background-color: #2a82da;
        }
        QListWidget::item:hover {
            background-color: #454545;
        }
    """)
    
    # Create and show main window
    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()
    
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
