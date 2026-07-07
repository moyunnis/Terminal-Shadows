#!/bin/bash
cd "$(dirname "$0")"

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "Виртуальное окружение не найдено. Сначала запусти ./install.sh"
    read -p "Enter для выхода..."
    exit 1
fi

python3 main.py
code=$?
if [ $code -ne 0 ]; then
    echo "Игра завершилась с ошибкой (код $code)."
    read -p "Enter для выхода..."
fi
