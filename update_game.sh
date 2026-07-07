#!/bin/bash
cd "$(dirname "$0")"

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "Виртуальное окружение не найдено. Сначала запусти ./install.sh"
    read -p "Enter для выхода..."
    exit 1
fi

if [ ! -f "updater.py" ]; then
    echo "Апдейтер не найден."
    read -p "Enter для выхода..."
    exit 1
fi

python3 updater.py
read -p "Enter для выхода..."
