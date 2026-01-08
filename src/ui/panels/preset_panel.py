"""
Preset Panel
UI panel for browsing and managing presets.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QInputDialog,
    QMessageBox
)
from PyQt5.QtCore import pyqtSignal, Qt

from presets.preset_manager import get_preset_manager, Preset


class PresetPanel(QWidget):
    """Panel for preset management."""
    
    preset_selected = pyqtSignal(dict)  # Emits preset data
    save_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._preset_manager = get_preset_manager()
        self._setup_ui()
        self._load_presets()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Built-in presets
        builtin_group = QGroupBox("Built-in Presets")
        builtin_layout = QVBoxLayout(builtin_group)
        
        self._builtin_list = QListWidget()
        self._builtin_list.itemDoubleClicked.connect(self._on_preset_activated)
        builtin_layout.addWidget(self._builtin_list)
        
        layout.addWidget(builtin_group)
        
        # User presets
        user_group = QGroupBox("My Presets")
        user_layout = QVBoxLayout(user_group)
        
        self._user_list = QListWidget()
        self._user_list.itemDoubleClicked.connect(self._on_preset_activated)
        user_layout.addWidget(self._user_list)
        
        # User preset buttons
        user_btn_layout = QHBoxLayout()
        
        self._save_btn = QPushButton("Save Current")
        self._save_btn.clicked.connect(self._on_save)
        user_btn_layout.addWidget(self._save_btn)
        
        self._delete_btn = QPushButton("Delete")
        self._delete_btn.clicked.connect(self._on_delete)
        user_btn_layout.addWidget(self._delete_btn)
        
        user_layout.addLayout(user_btn_layout)
        
        layout.addWidget(user_group)
        
        # Load button
        self._load_btn = QPushButton("Load Selected Preset")
        self._load_btn.clicked.connect(self._on_load_clicked)
        layout.addWidget(self._load_btn)
        
        layout.addStretch()
    
    def _load_presets(self):
        """Load presets into the lists."""
        self._builtin_list.clear()
        self._user_list.clear()
        
        self._preset_manager.load_presets(force_reload=True)
        
        # Built-in presets
        for preset in self._preset_manager.get_builtin_presets():
            item = QListWidgetItem(preset.name)
            item.setData(Qt.UserRole, preset)
            self._builtin_list.addItem(item)
        
        # User presets
        for preset in self._preset_manager.get_user_presets():
            item = QListWidgetItem(preset.name)
            item.setData(Qt.UserRole, preset)
            self._user_list.addItem(item)
    
    def _get_selected_preset(self) -> Preset:
        """Get the currently selected preset."""
        # Check builtin list first
        items = self._builtin_list.selectedItems()
        if items:
            return items[0].data(Qt.UserRole)
        
        # Then user list
        items = self._user_list.selectedItems()
        if items:
            return items[0].data(Qt.UserRole)
        
        return None
    
    def _on_preset_activated(self, item):
        """Handle preset double-click."""
        preset = item.data(Qt.UserRole)
        if preset:
            self.preset_selected.emit(preset.data)
    
    def _on_load_clicked(self):
        """Handle load button click."""
        preset = self._get_selected_preset()
        if preset:
            self.preset_selected.emit(preset.data)
        else:
            QMessageBox.information(self, "No Selection", "Please select a preset to load.")
    
    def _on_save(self):
        """Handle save button click."""
        name, ok = QInputDialog.getText(
            self, "Save Preset", "Enter a name for this preset:"
        )
        
        if ok and name:
            self.save_requested.emit()
            # The main window will call save_preset with the current config
    
    def save_preset(self, name: str, data: dict) -> bool:
        """Save a preset with the given name and data."""
        if self._preset_manager.save_preset(name, data):
            self._load_presets()  # Refresh list
            QMessageBox.information(self, "Saved", f"Preset '{name}' saved successfully.")
            return True
        else:
            QMessageBox.warning(self, "Error", "Failed to save preset.")
            return False
    
    def _on_delete(self):
        """Handle delete button click."""
        items = self._user_list.selectedItems()
        if not items:
            QMessageBox.information(self, "No Selection", "Please select a user preset to delete.")
            return
        
        preset = items[0].data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{preset.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self._preset_manager.delete_preset(preset.name):
                self._load_presets()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete preset.")
    
    def refresh(self):
        """Refresh the preset lists."""
        self._load_presets()
