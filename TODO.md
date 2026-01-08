# Fastplate Development TODO

## Known Bugs (Priority Order)

### 1. Engraved/Cutout Text Preview
- **Status:** In Progress
- **Issue:** When engraved or cutout text style is selected, raised text still appears above the plate in the preview
- **Expected:** Engraved should show text cut into the top surface; Cutout should show text cut completely through
- **Files:** `src/ui/viewer_widget.py`, `src/core/nameplate.py`

### 2. Built-in Presets Not Loading
- **Status:** Not Started
- **Issue:** No presets appear in the presets panel
- **Expected:** Built-in presets (desk nameplate, door sign, etc.) should be available
- **Files:** `src/presets/preset_manager.py`, `src/utils/resources.py`

### 3. Mounting Options Error
- **Status:** Not Started
- **Issue:** All mounting options return "Cannot find a solid on the stack" error
- **Expected:** Mounting features (screw holes, keyholes, magnets, etc.) should work
- **Files:** `src/core/geometry/mounts.py`, `src/ui/main_window.py`

### 4. Default View Options
- **Status:** Not Started
- **Issue:** View defaults are not set correctly on startup
- **Expected Defaults:**
  - Color: Light grey
  - Lighting: Edge Highlight
  - Grid: On
  - Edges: Off
  - Wireframe: Off
- **Files:** `src/ui/viewer_widget.py`

### 5. Preset Save/Load Broken
- **Status:** Not Started
- **Issue:** Saving and loading presets mixes up text lines and adds duplicates
- **Files:** `src/presets/preset_manager.py`, `src/ui/panels/preset_panel.py`, `src/ui/panels/text_panel.py`

### 6. Reset-to-Default Buttons
- **Status:** Partially Done
- **Issue:** Settings need individual reset buttons to restore default values
- **Progress:** `FocusComboBox` and `ResetableComboBox` widgets created
- **Files:** `src/ui/widgets/slider_spin.py`, all panel files

## Feature Wishlist

- [ ] Multi-color STL export (for multi-material printing)
- [ ] QR code support
- [ ] Logo/image import
- [ ] Undo/redo system
- [ ] Dark mode UI theme

## Development Notes

### Running the Application
```bash
cd src
python main.py
```

### Building Distribution
```bash
# Run build.bat or:
pyinstaller NameplateGenerator.spec
# Then copy casadi DLLs to dist/NameplateGenerator/_internal/
```

### Key Architecture
- **CadQuery** - 3D geometry generation
- **PyQt5** - GUI framework
- **PyQtGraph/OpenGL** - 3D preview rendering
- **JSON** - Preset storage format
