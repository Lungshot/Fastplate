@echo off
REM ============================================================================
REM Fastplate - Build Script for Windows
REM ============================================================================
REM
REM Usage:
REM   build.bat           - Build folder distribution (smaller, faster)
REM   build.bat onefile   - Build single .exe file (larger, easier to share)
REM   build.bat clean     - Clean build artifacts
REM   build.bat install   - Install dependencies only
REM   build.bat run       - Run from source
REM
REM Prerequisites:
REM   1. Python 3.9+ with CadQuery installed via conda:
REM      conda install -c cadquery -c conda-forge cadquery
REM   2. pip install -r requirements.txt
REM ============================================================================

setlocal EnableDelayedExpansion

set PROJECT_DIR=%~dp0
set BUILD_DIR=%PROJECT_DIR%build
set DIST_DIR=%PROJECT_DIR%dist
set SRC_DIR=%PROJECT_DIR%src
set SPEC_FILE=%PROJECT_DIR%fastplate.spec
set SPEC_ONEFILE=%PROJECT_DIR%fastplate_onefile.spec

REM Check for command argument
if "%1"=="clean" goto :clean
if "%1"=="install" goto :install
if "%1"=="run" goto :run
if "%1"=="onefile" goto :build_onefile

REM ============================================================================
REM BUILD FOLDER DISTRIBUTION (default)
REM ============================================================================
:build
echo.
echo ============================================================
echo  Fastplate - Build (Folder Distribution)
echo ============================================================
echo.

call :check_deps
if errorlevel 1 exit /b 1

echo [1/2] Running PyInstaller (folder mode)...
pyinstaller --clean --noconfirm "%SPEC_FILE%"

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    exit /b 1
)

echo [2/2] Build complete!
echo.
echo ============================================================
echo  Output: %DIST_DIR%\Fastplate\
echo  Run:    %DIST_DIR%\Fastplate\Fastplate.exe
echo ============================================================
goto :end

REM ============================================================================
REM BUILD SINGLE FILE
REM ============================================================================
:build_onefile
echo.
echo ============================================================
echo  Fastplate - Build (Single File)
echo ============================================================
echo.
echo NOTE: Single file builds are larger and slower to start,
echo       but easier to distribute.
echo.

call :check_deps
if errorlevel 1 exit /b 1

echo [1/2] Running PyInstaller (onefile mode)...
pyinstaller --clean --noconfirm "%SPEC_ONEFILE%"

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    exit /b 1
)

echo [2/2] Build complete!
echo.
echo ============================================================
echo  Output: %DIST_DIR%\Fastplate.exe
echo ============================================================
goto :end

REM ============================================================================
REM CHECK DEPENDENCIES
REM ============================================================================
:check_deps
REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    exit /b 1
)

REM Check CadQuery
python -c "import cadquery" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: CadQuery not installed!
    echo.
    echo Install via Conda:
    echo   conda install -c cadquery -c conda-forge cadquery
    echo.
    exit /b 1
)

REM Check PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo Checking dependencies...
pip install -r requirements.txt --quiet
exit /b 0

REM ============================================================================
REM RUN FROM SOURCE
REM ============================================================================
:run
echo Running from source...
cd "%SRC_DIR%"
python main.py
goto :end

REM ============================================================================
REM CLEAN
REM ============================================================================
:clean
echo Cleaning build artifacts...
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
for /d /r "%PROJECT_DIR%" %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
echo Clean complete.
goto :end

REM ============================================================================
REM INSTALL DEPENDENCIES
REM ============================================================================
:install
echo.
echo Installing dependencies...
echo.
echo IMPORTANT: Install CadQuery via Conda first:
echo   conda install -c cadquery -c conda-forge cadquery
echo.
pip install -r requirements.txt
echo.
echo Done. You can now run: build.bat run
goto :end

:end
endlocal
