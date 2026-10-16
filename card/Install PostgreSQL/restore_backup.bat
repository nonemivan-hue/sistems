@echo off
REM ================================================
REM Скрипт восстановления базы данных из резервной копии
REM Использование: restore_backup.bat backup_file.sql [database_name]
REM ================================================

setlocal enabledelayedexpansion

REM ==================== НАСТРОЙКИ ====================
set PG_BIN=D:\PostgreSQL\15\bin
set PG_USER=postgres
set PG_PASSWORD=3831043

REM Если имя базы данных не передано, используем по умолчанию
if "%~2"=="" (
    set DB_NAME=card_system
) else (
    set DB_NAME=%~2
)

REM Проверка наличия файла резервной копии
if "%~1"=="" (
    echo [ERROR] Не указан файл резервной копии!
    echo Использование: %~nx0 ^<backup_file^> ^[database_name^]
    echo Пример: %~nx0 C:\PostgreSQL\Backups\backup_card_system_20240101_0200.sql
    exit /b 1
)

set BACKUP_FILE=%~1

if not exist "%BACKUP_FILE%" (
    echo [ERROR] Файл резервной копии не найден: %BACKUP_FILE%
    exit /b 1
)

REM ==================== ОСНОВНАЯ ЧАСТЬ ====================

set PGPASSWORD=%PG_PASSWORD%

echo ================================================
echo Начало восстановления базы данных
echo Файл резервной копии: %BACKUP_FILE%
echo Целевая база данных: %DB_NAME%
echo ================================================
echo.

REM Проверка существования базы данных
echo [INFO] Проверка существования базы данных %DB_NAME%...
"%PG_BIN%\psql.exe" -U %PG_USER% -lqt | findstr /R /C:"%DB_NAME%" > nul

if %ERRORLEVEL% EQU 0 (
    echo [WARNING] База данных %DB_NAME% уже существует.
    echo.
    choice /C YN /M "Удалить существующую базу данных и создать новую"
    if errorlevel 2 (
        echo [INFO] Восстановление отменено пользователем.
        exit /b 0
    )
    
    echo [INFO] Удаление существующей базы данных...
    "%PG_BIN%\dropdb.exe" -U %PG_USER% --if-exists %DB_NAME%
)

REM Создание новой базы данных
echo [INFO] Создание базы данных %DB_NAME%...
"%PG_BIN%\createdb.exe" -U %PG_USER% %DB_NAME%

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Ошибка создания базы данных!
    exit /b 1
)

REM Восстановление из резервной копии
echo [INFO] Восстановление данных из резервной копии...
"%PG_BIN%\pg_restore.exe" -U %PG_USER% -d %DB_NAME% -v "%BACKUP_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Восстановление завершено успешно!
    echo База данных: %DB_NAME%
) else (
    echo.
    echo [ERROR] Ошибка восстановления! Код ошибки: %ERRORLEVEL%
    exit /b 1
)

echo ================================================

REM Очистка переменной с паролем
set PGPASSWORD=

endlocal
exit /b 0
