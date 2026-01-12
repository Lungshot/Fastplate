# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for 3D Nameplate Generator - SINGLE FILE BUILD

Creates a single .exe file (larger but easier to distribute).
"""

import sys
import os
from pathlib import Path
import glob

spec_dir = os.path.dirname(os.path.abspath(SPEC))
src_dir = os.path.join(spec_dir, 'src')

block_cipher = None

# Resources to bundle
datas = [
    (os.path.join(src_dir, 'resources', 'data', 'glyphnames.json'),
     os.path.join('resources', 'data')),
    (os.path.join(src_dir, 'resources', 'presets'),
     os.path.join('resources', 'presets')),
]

# Collect casadi binaries
casadi_path = None
try:
    import casadi
    casadi_path = os.path.dirname(casadi.__file__)
except ImportError:
    pass

binaries = []
if casadi_path:
    # Collect all DLLs and pyd files from casadi
    # CRITICAL: Must go in root '.', not 'casadi' subfolder for Windows to find them!
    for dll in glob.glob(os.path.join(casadi_path, '*.dll')):
        binaries.append((dll, '.'))  # Root of _internal
    for pyd in glob.glob(os.path.join(casadi_path, '*.pyd')):
        binaries.append((pyd, '.'))
    # Also add exe files that might be needed
    for exe in glob.glob(os.path.join(casadi_path, '*.exe')):
        binaries.append((exe, '.'))

# Collect OCP binaries
ocp_path = None
try:
    import OCP
    ocp_path = os.path.dirname(OCP.__file__)
except ImportError:
    pass

if ocp_path:
    for dll in glob.glob(os.path.join(ocp_path, '*.dll')):
        binaries.append((dll, 'OCP'))
    for pyd in glob.glob(os.path.join(ocp_path, '*.pyd')):
        binaries.append((pyd, 'OCP'))

# Hidden imports for CadQuery, PyQt5, and OpenGL
hiddenimports = [
    'cadquery', 'cadquery.cq', 'cadquery.occ_impl', 'cadquery.occ_impl.shapes',
    'cadquery.occ_impl.geom', 'cadquery.occ_impl.exporters', 'cadquery.occ_impl.importers',
    'OCP', 'OCP.BRep', 'OCP.BRepAlgoAPI', 'OCP.BRepBuilderAPI', 'OCP.BRepFilletAPI',
    'OCP.BRepGProp', 'OCP.BRepMesh', 'OCP.BRepOffsetAPI', 'OCP.BRepPrimAPI',
    'OCP.BRepTools', 'OCP.Font', 'OCP.GProp', 'OCP.Geom', 'OCP.GeomAbs', 'OCP.GeomAPI',
    'OCP.TopAbs', 'OCP.TopExp', 'OCP.TopLoc', 'OCP.TopoDS', 'OCP.gp', 'OCP.StlAPI',
    'OCP.STEPControl', 'OCP.IFSelect', 'OCP.TopTools', 'OCP.ShapeAnalysis',
    'OCP.ShapeFix', 'OCP.TColgp', 'OCP.TColStd', 'OCP.TCollection', 'OCP.TDF',
    'OCP.TDocStd', 'OCP.XCAFApp', 'OCP.XCAFDoc', 'OCP.XSControl', 'OCP.Quantity',
    'OCP.Message', 'OCP.Standard', 'OCP.NCollection',
    'casadi', 'casadi._casadi',
    'PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.QtOpenGL', 'PyQt5.sip',
    'pyqtgraph', 'pyqtgraph.opengl',
    'OpenGL', 'OpenGL.GL', 'OpenGL.GLU', 'OpenGL.GLUT', 'OpenGL.arrays', 'OpenGL.platform',
    'numpy', 'numpy.core',
    'fontTools', 'fontTools.ttLib',
    'json', 'typing', 'dataclasses', 'enum', 'pathlib', 'functools', 'winreg',
]

excludes = ['matplotlib', 'scipy', 'pandas', 'PIL', 'tkinter', 'test', 'tests', 'unittest']

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

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Single file executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NameplateGenerator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(src_dir, 'resources', 'icon.ico') if os.path.exists(os.path.join(src_dir, 'resources', 'icon.ico')) else None,
)
