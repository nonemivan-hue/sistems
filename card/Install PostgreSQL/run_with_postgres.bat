@echo off
REM Запуск приложения с подключением к PostgreSQL
REM Настройка переменных окружения для PostgreSQL

set USE_POSTGRES=true
set DB_HOST=localhost
set DB_PORT=5432
set DB_NAME=transport_cards
set DB_USER=postgres
set DB_PASSWORD=3831043

REM Переход в директорию приложения
cd /d "D:\card"

REM Запуск Flask приложения
echo Запуск системы учета транспортных карт с PostgreSQL...
python app.py

pause
