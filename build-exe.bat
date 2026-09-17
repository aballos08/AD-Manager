@echo off
REM ============================================================
REM  AD Manager - build standalone Windows exe with PyInstaller
REM  Usage: double-click, or run from a terminal:  build-exe.bat
REM  Output: dist\AD-Manager\AD-Manager.exe (+ support files)
REM ============================================================
setlocal
cd /d "%~dp0"

echo [1/3] Installing build dependencies...
pip show pyinstaller >nul 2>&1 || pip install pyinstaller || goto :error

echo [2/3] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist

echo [3/3] Building...
pyinstaller AD-Manager.spec --noconfirm --clean || goto :error

echo.
echo ============================================================
echo  Build OK: dist\AD-Manager\AD-Manager.exe
echo  Distribute the WHOLE dist\AD-Manager folder.
echo ============================================================
goto :eof

:error
echo.
echo BUILD FAILED - see output above.
exit /b 1
