@echo off
chcp 65001 > nul
cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Виртуальное окружение не найдено. Сначала запусти install.bat
    pause
    exit /b 1
)

python main.py
if %errorlevel% neq 0 (
    echo Игра завершилась с ошибкой (код %errorlevel%).
    pause
)
