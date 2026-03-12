@echo off
echo ========================================
echo   Compilando AdminGuiaMedica para Windows
echo ========================================

echo 1. Instalando dependencias necesarias...
pip install kivy kivymd psycopg[binary] reportlab pyinstaller

echo 2. Iniciando compilacion con PyInstaller...
pyinstaller --onefile --windowed --name "AdminGuiaMedica" ^
 --add-data "studio_logo.png;." ^
 --add-data "icon.png;." ^
 admin_manager.py

echo ========================================
echo   PROCESO TERMINADO
echo   El ejecutable se encuentra en la carpeta 'dist'
echo ========================================
pause
