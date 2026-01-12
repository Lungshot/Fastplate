# Fastplate

A Windows application for creating customizable 3D-printable nameplates, door signs, desk signs, and more.

## Features

- **Any Windows Font**: Use any TrueType or OpenType font installed on your system
- **9,000+ Icons**: Nerd Fonts icon library built-in
- **Multiple Plate Shapes**: Rectangle, rounded, oval, hexagon, octagon, sweeping curves
- **Text Styles**: Raised, engraved (debossed), or cutout text
- **Mounting Options**: Desk stands, screw holes, keyholes, magnet pockets, hanging holes
- **Live 3D Preview**: See your design in real-time
- **Preset System**: Built-in templates + save your own
- **Export Formats**: STL, STEP, 3MF for 3D printing

## Installation

### Option 1: Pre-built Executable (Recommended)

Download the latest release from the Releases page and run `Fastplate.exe`.

### Option 2: Run from Source

**Prerequisites:**
- Python 3.9 or higher
- Conda (recommended for CadQuery)

**Setup:**

```bash
# Create conda environment
conda create -n fastplate python=3.10
conda activate fastplate

# Install CadQuery (required - best via conda)
conda install -c cadquery -c conda-forge cadquery

# Install other dependencies
pip install -r requirements.txt

# Run the application
cd src
python main.py
```

## Building Standalone Executable

To build a standalone Windows executable:

```bash
# Activate your conda environment with CadQuery
conda activate fastplate

# Run the build script
build.bat
```

The executable will be created in `dist/Fastplate/`.

### Build Requirements

- All runtime dependencies installed
- PyInstaller (`pip install pyinstaller`)
- Windows 10/11

### Custom Icon

To add a custom application icon:
1. Create a 256x256 `.ico` file
2. Save it as `src/resources/icon.ico`
3. Rebuild the application

## Usage

1. **Select a Preset** or start from scratch
2. **Configure Text**: Enter your text, choose font, style, and size
3. **Adjust Base Plate**: Set dimensions, shape, and thickness
4. **Add Mounting**: Choose desk stand, screw holes, magnets, etc.
5. **Preview**: Rotate and inspect your design in 3D
6. **Export**: Save as STL for 3D printing

## Project Structure

```
Fastplate/
├── src/
│   ├── main.py              # Application entry point
│   ├── core/                # 3D geometry generation
│   │   ├── nameplate.py     # Main builder class
│   │   ├── geometry/        # Shape generators
│   │   └── export/          # File exporters
│   ├── fonts/               # Font management
│   ├── presets/             # Preset management
│   ├── ui/                  # GUI components
│   │   ├── main_window.py   # Main window
│   │   ├── viewer_widget.py # 3D preview
│   │   ├── panels/          # Settings panels
│   │   └── dialogs/         # Pop-up dialogs
│   ├── utils/               # Utility modules
│   └── resources/           # Bundled data files
├── requirements.txt         # Python dependencies
├── fastplate.spec           # PyInstaller config
└── build.bat               # Build script
```

## Troubleshooting

### "CadQuery not found"
CadQuery must be installed via conda:
```bash
conda install -c cadquery -c conda-forge cadquery
```

### Build fails with missing modules
Ensure all dependencies are installed in your conda environment before building.

### 3D preview shows nothing
Check that PyOpenGL and pyqtgraph are installed:
```bash
pip install PyOpenGL pyqtgraph
```

## License

MIT License
