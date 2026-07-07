@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo Установка Terminal Shadows
echo.

python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python не найден в PATH. Поставь с python.org и отметь "Add Python to PATH".
    pause
    exit /b 1
)

echo Создаю виртуальное окружение...
python -m venv venv
call venv\Scripts\activate.bat

echo Ставлю зависимости...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt

if not exist "%USERPROFILE%\.terminal_shadows\saves" mkdir "%USERPROFILE%\.terminal_shadows\saves"

echo.
echo Готово. Запуск: run_game.bat
echo Данные и сохранения: %USERPROFILE%\.terminal_shadows\
echo.
pause
