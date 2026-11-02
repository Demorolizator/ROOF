@echo off
cd /d "%~dp0"
python -m pip install --upgrade pyinstaller ezdxf
python -m PyInstaller --noconfirm --clean --onefile --windowed --name RoofStudio_v0.5 roofstudio.py
if exist dist\RoofStudio_v0.5.exe echo Сборка готова: dist\RoofStudio_v0.5.exe
pause
