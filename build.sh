#!/bin/bash

echo "Установка зависимостей..."
pip install -r requirements.txt

echo "Сборка исполняемого файла с помощью PyInstaller..."
pyinstaller app.spec

echo "Сборка завершена."
read -p "Нажмите Enter для выхода..."
