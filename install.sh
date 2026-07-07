#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "Установка Terminal Shadows"
echo

if ! command -v python3 &> /dev/null; then
    echo "Python 3 не найден. Установи: sudo apt install python3 python3-venv python3-pip"
    exit 1
fi
echo "Python: $(python3 --version)"

echo "Создаю виртуальное окружение..."
python3 -m venv venv
source venv/bin/activate

echo "Ставлю зависимости..."
pip install --upgrade pip --quiet
pip install -r requirements.txt

mkdir -p ~/.terminal_shadows/saves

chmod +x run_game.sh update_game.sh 2>/dev/null || true

echo
echo "Готово. Запуск: ./run_game.sh"
echo "Данные и сохранения: ~/.terminal_shadows/"
