@echo off
echo Сборка Serial App в EXE...
pyinstaller --onefile --windowed --name "SerialControlApp" --icon=app_icon.ico serial_app.py
echo Готово! EXE файл находится в папке dist
pause