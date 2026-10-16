@echo off
REM Запуск приложения с локальной базой данных (папка Data)

set USE_POSTGRES=false

REM Переход в директорию приложения
cd /d "D:\card"

REM Запуск Flask приложения
echo Запуск системы учета транспортных карт с локальной БД (Data)...
python app.py

pause
