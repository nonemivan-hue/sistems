@echo off
REM daily_backup.bat - Скрипт ежедневного резервного копирования PostgreSQL для Windows
REM Сохраните этот файл в папке C:\PostgreSQL\Backups\ или укажите свой путь

REM ==================== НАСТРОЙКИ ====================
REM Путь к бинарным файлам PostgreSQL (измените версию при необходимости)
set PG_BIN=D:\PostgreSQL\15\bin

REM Пользователь PostgreSQL
set PG_USER=postgres

REM Пароль пользователя postgres
set PG_PASSWORD=3831043

REM Имя базы данных для резервного копирования
set DB_NAME=card_system

REM Директория для хранения резервных копий
set BACKUP_DIR=D:\PostgreSQL\Backups

REM Количество дней хранения резервных копий
set RETENTION_DAYS=7

REM ==================== ОСНОВНАЯ ЧАСТЬ ====================

REM Установка переменной окружения с паролем
set PGPASSWORD=%PG_PASSWORD%

REM Формирование имени файла резервной копии с датой и временем
REM Формат: backup_card_system_YYYYMMDD_HHMM.sql
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YEAR=%dt:~0,4%"
set "MONTH=%dt:~4,2%"
set "DAY=%dt:~6,2%"
set "HOUR=%dt:~8,2%"
set "MINUTE=%dt:~10,2%"

set BACKUP_FILE=%BACKUP_DIR%\backup_%DB_NAME%_%YEAR%%MONTH%%DAY%_%HOUR%%MINUTE%.sql

REM Создание директории для резервных копий, если она не существует
if not exist "%BACKUP_DIR%" (
    echo [INFO] Создание директории для резервных копий: %BACKUP_DIR%
    mkdir "%BACKUP_DIR%"
)

REM Логирование начала процесса
echo ================================================
echo [%YEAR%-%MONTH%-%DAY% %HOUR%:%MINUTE%] Начало резервного копирования
echo База данных: %DB_NAME%
echo Файл резервной копии: %BACKUP_FILE%
echo ================================================

REM Выполнение резервного копирования с помощью pg_dump
REM -F c - формат custom (сжатый, подходит для pg_restore)
REM -b - включать большие объекты (BLOBs)
REM -v - подробный режим (verbose)
"%PG_BIN%\pg_dump.exe" -U %PG_USER% -d %DB_NAME% -F c -b -v -f "%BACKUP_FILE%"

REM Проверка результата выполнения
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Резервная копия успешно создана: %BACKUP_FILE%
    echo [SUCCESS] Размер файла: %~z1 байт
) else (
    echo.
    echo [ERROR] Ошибка создания резервной копии! Код ошибки: %ERRORLEVEL%
    echo [%YEAR%-%MONTH%-%DAY% %HOUR%:%MINUTE%] Резервное копирование завершено с ошибкой >> "%BACKUP_DIR%\backup_log.txt"
    exit /b 1
)

REM Удаление старых резервных копий
echo.
echo [INFO] Удаление резервных копий старше %RETENTION_DAYS% дней...
forfiles /p "%BACKUP_DIR%" /s /m backup_*.sql /d -%RETENTION_DAYS% /c "cmd /c echo [DELETE] Удаление старого файла: @path && del @path"

REM Запись в журнал успешного завершения
echo [%YEAR%-%MONTH%-%DAY% %HOUR%:%MINUTE%] Резервное копирование успешно завершено >> "%BACKUP_DIR%\backup_log.txt"

echo.
echo ================================================
echo [%YEAR%-%MONTH%-%DAY% %HOUR%:%MINUTE%] Резервное копирование завершено
echo ================================================

REM Очистка переменной с паролем из окружения
set PGPASSWORD=

exit /b 0
