@echo off
title LinkMEdin Launcher

echo ==========================================
echo [*] LinkMEdin Baslatiliyor...
echo ==========================================
echo.

cd /d "%~dp0"

:: Playwright'in kurulu oldugu Python yorumlayicisi ile Streamlit'i calistir
"C:\Users\Muhsin\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe" -m streamlit run app.py

if %errorlevel% neq 0 (
    echo [!] Ozel Python yolu basarisiz oldu, varsayilan python deneniyor...
    python -m streamlit run app.py
)

pause
