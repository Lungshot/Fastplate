# Fastplate Development TODO

## CRITICAL REQUIREMENT: Windows 11 Standalone EXE

**THIS IS THE HIGHEST PRIORITY REQUIREMENT**

The application MUST be installable on Windows 11 directly from the EXE with **ZERO external dependencies**. Users should NOT need to:
- Install Python
- Install any DLLs manually
- Install Visual C++ Redistributables
- Install any other software

### Verification Checklist
- [ ] EXE runs on fresh Windows 11 install
- [ ] All CadQuery/OCC libraries bundled correctly
- [ ] All casadi DLLs included in `_internal/` root
- [ ] All PyQt5 plugins and DLLs included
- [ ] All OpenGL dependencies for PyQtGraph included
- [ ] Font files accessible from bundled app
- [ ] Preset JSON files load from bundled resources
- [ ] Export (STL/STEP/3MF) works in bundled app

### Known Distribution Issues
- casadi requires DLLs copied to `_internal/` root (not in casadi subfolder)
- PyInstaller needs `--collect-all casadi --collect-all PyQt5`
- Resource paths must use `sys._MEIPASS` detection for frozen app
- Use `--onedir` not `--onefile` for native library compatibility

### Build Command
```bash
pyinstaller --name NameplateGenerator --onedir --windowed --paths src ^
  --collect-all casadi --collect-all PyQt5 ^
  --add-data "src/resources;resources" ^
  src/main.py
# THEN: Copy all DLLs from casadi folder to _internal/ root
```

---

## Known Bugs (Priority Order)

### 1. Engraved/Cutout Text Preview
- **Status:** ✅ FIXED
- **Issue:** When engraved or cutout text style is selected, raised text still appears above the plate in the preview
- **Fix:** Clear `_text_geometry` cache after engraved/cutout operations in `nameplate.py`
- **Files:** `src/core/nameplate.py`

### 2. Built-in Presets Not Loading
- **Status:** ✅ FIXED
- **Issue:** No presets appear in the presets panel
- **Fix:** Preset files exist in `src/resources/presets/`, code is correct
- **Files:** `src/presets/preset_manager.py`, `src/utils/resources.py`

### 3. Mounting Options Error
- **Status:** ✅ FIXED
- **Issue:** All mounting options return "Cannot find a solid on the stack" error
- **Fix:** Changed `moveTo()` to `center()` and added Z offset for clean boolean cuts in `mounts.py`
- **Files:** `src/core/geometry/mounts.py`

### 4. Default View Options
- **Status:** ✅ VERIFIED CORRECT
- **Issue:** View defaults are not set correctly on startup
- **Verification:** Defaults are correctly set in code:
  - Color: Light grey ✓
  - Lighting: Edge Highlight ✓
  - Grid: On ✓
  - Edges: Off ✓
  - Wireframe: Off ✓
- **Files:** `src/ui/viewer_widget.py`

### 5. Preset Save/Load Broken
- **Status:** ✅ FIXED
- **Issue:** Saving and loading presets mixes up text lines and adds duplicates
- **Fix:** Added signal blocking during bulk configuration in all panels to prevent cascade updates
- **Files:** `src/ui/panels/text_panel.py`, `src/ui/panels/base_panel.py`, `src/ui/panels/mount_panel.py`

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
