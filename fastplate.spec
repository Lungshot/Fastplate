# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Fastplate

CadQuery/OCP bundling requires special handling due to OpenCASCADE dependencies.
"""

import sys
import os
from pathlib import Path

# Get the project root directory
spec_dir = os.path.dirname(os.path.abspath(SPEC))
src_dir = os.path.join(spec_dir, 'src')

block_cipher = None

# ============================================================================
# DATA FILES
# ============================================================================
# Resources to bundle with the application
datas = [
    # Nerd Fonts glyph data
    (os.path.join(src_dir, 'resources', 'data', 'glyphnames.json'),
     os.path.join('resources', 'data')),
    # Google Material Icons data
    (os.path.join(src_dir, 'resources', 'data', 'material_icons.json'),
     os.path.join('resources', 'data')),
    # Font Awesome Icons data
    (os.path.join(src_dir, 'resources', 'data', 'font_awesome_icons.json'),
     os.path.join('resources', 'data')),
    # Built-in presets
    (os.path.join(src_dir, 'resources', 'presets'),
     os.path.join('resources', 'presets')),
]

# ============================================================================
# BINARY COLLECTION (Critical: casadi DLLs must be in root!)
# ============================================================================
import glob

binaries = []

# Collect casadi binaries - MUST go in root of _internal, not subfolder!
try:
    import casadi
    casadi_path = os.path.dirname(casadi.__file__)
    for dll in glob.glob(os.path.join(casadi_path, '*.dll')):
        binaries.append((dll, '.'))  # '.' = root of _internal
    for pyd in glob.glob(os.path.join(casadi_path, '*.pyd')):
        binaries.append((pyd, '.'))
except ImportError:
    print("Warning: casadi not found - DLLs will not be bundled")

# Collect OCP binaries
try:
    import OCP
    ocp_path = os.path.dirname(OCP.__file__)
    for dll in glob.glob(os.path.join(ocp_path, '*.dll')):
        binaries.append((dll, 'OCP'))
    for pyd in glob.glob(os.path.join(ocp_path, '*.pyd')):
        binaries.append((pyd, 'OCP'))
except ImportError:
    print("Warning: OCP not found")

# ============================================================================
# HIDDEN IMPORTS
# ============================================================================
# CadQuery and OCP have many dynamically loaded modules
hiddenimports = [
    # CadQuery core
    'cadquery',
    'cadquery.cq',
    'cadquery.occ_impl',
    'cadquery.occ_impl.shapes',
    'cadquery.occ_impl.geom',
    'cadquery.occ_impl.exporters',
    'cadquery.occ_impl.importers',

    # OCP (pythonOCC bindings)
    'OCP',
    'OCP.BRep',
    'OCP.BRepAlgoAPI',
    'OCP.BRepBuilderAPI',
    'OCP.BRepFilletAPI',
    'OCP.BRepGProp',
    'OCP.BRepMesh',
    'OCP.BRepOffsetAPI',
    'OCP.BRepPrimAPI',
    'OCP.BRepTools',
    'OCP.Font',
    'OCP.GProp',
    'OCP.Geom',
    'OCP.GeomAbs',
    'OCP.GeomAPI',
    'OCP.TopAbs',
    'OCP.TopExp',
    'OCP.TopLoc',
    'OCP.TopoDS',
    'OCP.gp',
    'OCP.StlAPI',
    'OCP.STEPControl',
    'OCP.IFSelect',
    'OCP.TopTools',
    'OCP.ShapeAnalysis',
    'OCP.ShapeFix',
    'OCP.TColgp',
    'OCP.TColStd',
    'OCP.TCollection',
    'OCP.TDF',
    'OCP.TDocStd',
    'OCP.XCAFApp',
    'OCP.XCAFDoc',
    'OCP.XSControl',
    'OCP.Quantity',
    'OCP.Message',
    'OCP.Standard',
    'OCP.NCollection',

    # PyQt5
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.QtOpenGL',
    'PyQt5.sip',

    # PyQtGraph and OpenGL
    'pyqtgraph',
    'pyqtgraph.opengl',
    'OpenGL',
    'OpenGL.GL',
    'OpenGL.GLU',
    'OpenGL.GLUT',
    'OpenGL.arrays',
    'OpenGL.platform',

    # Numpy
    'numpy',
    'numpy.core',

    # Font tools
    'fonttools',
    'fontTools',
    'fontTools.ttLib',

    # Standard library that might be missed
    'json',
    'typing',
    'dataclasses',
    'enum',
    'pathlib',
    'functools',
    'winreg',
]

# ============================================================================
# BINARY EXCLUSIONS (reduce size)
# ============================================================================
excludes = [
    'matplotlib',
    'scipy',
    'pandas',
    'PIL',
    'tkinter',
    'test',
    'tests',
    'unittest',
]

# ============================================================================
# ANALYSIS
# ============================================================================
a = Analysis(
    [os.path.join(src_dir, 'main.py')],
    pathex=[src_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ============================================================================
# FILTER OUT UNNECESSARY FILES (reduce size)
# ============================================================================
# Remove test files and documentation
def filter_files(toc):
    """Filter out unnecessary files to reduce bundle size."""
    filtered = []
    exclude_patterns = [
        'test', 'tests', 'testing',
        '__pycache__',
        '.pyc',
        'docs',
        'examples',
        'sample',
    ]
    for item in toc:
        name = item[0].lower()
        should_exclude = any(pattern in name for pattern in exclude_patterns)
        if not should_exclude:
            filtered.append(item)
    return filtered

a.datas = filter_files(a.datas)

# ============================================================================
# PYZ (Python bytecode archive)
# ============================================================================
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ============================================================================
# EXE (Executable)
# ============================================================================
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Fastplate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(src_dir, 'resources', 'icon.ico') if os.path.exists(os.path.join(src_dir, 'resources', 'icon.ico')) else None,
)

# ============================================================================
# COLLECT (Bundle all files together)
# ============================================================================
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Fastplate',
)
