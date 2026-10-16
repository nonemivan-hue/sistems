@echo off
REM migrate_from_json.bat - Скрипт миграции данных из JSON файлов в PostgreSQL
REM Версия: 2.0 (с исправлением длин полей и явным указанием колонок)
REM Использование: migrate_from_json.bat [путь_к_папке_data] [имя_БД] [пользователь]

SETLOCAL EnableDelayedExpansion

REM ============================================
REM НАСТРОЙКИ (измените под вашу систему)
REM ============================================
set PG_BIN=D:\PostgreSQL\15\bin
set PG_USER=postgres
set PG_PASSWORD=3831043
set DB_NAME=card_system
set DATA_DIR=D:\card\data
set SCRIPT_DIR=%~dp0

REM Переопределение параметров из командной строки (если переданы)
if not "%~1"=="" set DATA_DIR=%~1
if not "%~2"=="" set DB_NAME=%~2
if not "%~3"=="" set PG_USER=%~3

REM Установка переменной окружения для пароля
set PGPASSWORD=%PG_PASSWORD%

echo ====================================================
echo Миграция данных из JSON в PostgreSQL (Версия 2.0)
echo ====================================================
echo Параметры:
echo   - База данных: %DB_NAME%
echo   - Пользователь: %PG_USER%
echo   - Папка с данными: %DATA_DIR%
echo   - Путь к PostgreSQL: %PG_BIN%
echo ====================================================
echo.

REM Проверка существования папки с данными
if not exist "%DATA_DIR%" (
    echo ОШИБКА: Папка с данными не найдена: %DATA_DIR%
    exit /b 1
)

REM Проверка существования утилит PostgreSQL
if not exist "%PG_BIN%\psql.exe" (
    echo ОШИБКА: psql.exe не найден. Проверьте путь к PostgreSQL: %PG_BIN%
    exit /b 1
)

REM Шаг 0: Исправление длин полей в БД (чтобы избежать ошибок переполнения)
echo Шаг 0: Изменение типов данных столбцов (увеличение длины)...
if exist "%SCRIPT_DIR%fix_column_lengths.sql" (
    "%PG_BIN%\psql.exe" -U %PG_USER% -d %DB_NAME% -f "%SCRIPT_DIR%fix_column_lengths.sql"
    if !ERRORLEVEL! NEQ 0 (
        echo ПРЕДУПРЕЖДЕНИЕ: Не удалось выполнить скрипт fix_column_lengths.sql
        echo Убедитесь, что таблицы уже созданы в базе данных.
        echo Продолжаем миграцию...
    ) else (
        echo [УСПЕХ] Типы данных изменены.
    )
) else (
    echo ПРЕДУПРЕЖДЕНИЕ: Файл fix_column_lengths.sql не найден.
    echo Если возникнет ошибка "значение не умещается в тип character varying",
    echo выполните этот скрипт вручную после создания таблиц.
)
echo.

REM Создание временной папки для CSV файлов
set TEMP_CSV_DIR=%TEMP%\pg_migration_%RANDOM%
mkdir "%TEMP_CSV_DIR%"

echo Шаг 1: Преобразование JSON файлов в CSV...
echo.

REM ============================================
REM Функция преобразования JSON в CSV (Python)
REM ============================================
if not exist "json_to_csv.py" (
    echo Создание скрипта json_to_csv.py...
    (
        echo import json
        echo import csv
        echo import sys
        echo import os
        echo.
        echo def json_to_csv(json_file, csv_file):
        echo     with open^(json_file, 'r', encoding='utf-8'^) as f:
        echo         data = json.load^(f^)
        echo.
        echo     if not data:
        echo         print^(f"Файл {json_file} пустой"^)
        echo         return False
        echo.
        echo     # Если данные в виде словаря ^{...^}, преобразуем в список
        echo     if isinstance^(data, dict^):
        echo         data = [data]
        echo.
        echo     if not isinstance^(data, list^):
        echo         print^f"Неподдерживаемый формат данных в {json_file}"^)
        echo         return False
        echo.
        echo     # Получаем заголовки из первого элемента
        echo     fieldnames = list^(data[0].keys^(^^)
        echo.
        echo     with open^(csv_file, 'w', encoding='utf-8', newline=''^) as f:
        echo         writer = csv.DictWriter^(f, fieldnames=fieldnames^)
        echo         writer.writeheader^(^)
        echo         for row in data:
        echo             # Преобразуем сложные типы данных в строки
        echo             for key in fieldnames:
        echo                 if isinstance^(row.get^(key^), ^(list, dict^)^):
        echo                     row[key] = json.dumps^(row[key], ensure_ascii=False^)
        echo                 elif row.get^(key^) is None:
        echo                     row[key] = ''
        echo             writer.writerow^(row^)
        echo.
        echo     return True
        echo.
        echo if __name__ == "__main__":
        echo     if len^(sys.argv^) != 3:
        echo         print^("Использование: python json_to_csv.py ^<json_file^> ^<csv_file^>"^)
        echo         sys.exit^(1^)
        echo.
        echo     json_file = sys.argv[1]
        echo     csv_file = sys.argv[2]
        echo.
        echo     if json_to_csv^(json_file, csv_file^):
        echo         print^f"Успешно: {json_file} -^> {csv_file}"^)
        echo         sys.exit^(0^)
        echo     else:
        echo         sys.exit^(1^)
    ) > "json_to_csv.py"
)

REM Обработка каждого JSON файла
set FILES_PROCESSED=0
set FILES_FAILED=0

for %%F in ("%DATA_DIR%\*.json") do (
    set JSON_FILE=%%F
    set FILENAME=%%~nF
    set CSV_FILE=%TEMP_CSV_DIR%\!FILENAME!.csv
    
    echo Обработка: !FILENAME!.json
    python json_to_csv.py "!JSON_FILE!" "!CSV_FILE!"
    
    if !ERRORLEVEL! EQU 0 (
        set /a FILES_PROCESSED+=1
    ) else (
        set /a FILES_FAILED+=1
        echo ОШИБКА при обработке !FILENAME!.json
    )
)

echo.
echo Преобразование завершено: %FILES_PROCESSED% файлов успешно, %FILES_FAILED% с ошибками
echo.

REM ============================================
REM Шаг 2: Загрузка данных в PostgreSQL
REM ============================================
echo Шаг 2: Загрузка данных в PostgreSQL...
echo.

REM Функция загрузки CSV в таблицу с явным указанием колонок
:LOAD_TABLE
set TABLE_NAME=%1
set CSV_FILE=%2
set COLUMNS=%3

if exist "%CSV_FILE%" (
    echo Загрузка таблицы %TABLE_NAME%...
    
    REM Очистка таблицы перед загрузкой (если таблица существует)
    "%PG_BIN%\psql.exe" -U %PG_USER% -d %DB_NAME% -c "TRUNCATE TABLE %TABLE_NAME% RESTART IDENTITY CASCADE;" 2>nul
    
    REM Загружаем данные через COPY с явным указанием колонок
    if "%COLUMNS%"=="" (
        REM Если колонки не указаны, используем заголовки из CSV
        "%PG_BIN%\psql.exe" -U %PG_USER% -d %DB_NAME% -c "\copy %TABLE_NAME% FROM '%CSV_FILE%' WITH CSV HEADER ENCODING 'UTF8';"
    ) else (
        REM Используем явно указанный список колонок
        "%PG_BIN%\psql.exe" -U %PG_USER% -d %DB_NAME% -c "\copy %TABLE_NAME% (%COLUMNS%) FROM '%CSV_FILE%' WITH CSV HEADER ENCODING 'UTF8';"
    )
    
    if !ERRORLEVEL! EQU 0 (
        echo [УСПЕХ] Таблица %TABLE_NAME% загружена.
    ) else (
        echo [ОШИБКА] Не удалось загрузить таблицу %TABLE_NAME%.
        echo Проверьте соответствие структуры CSV и таблицы.
    )
) else (
    echo [ПРОПУСК] Файл %CSV_FILE% не найден.
)
goto :EOF

REM Загрузка основных таблиц (порядок важен из-за внешних ключей)
REM Для каждой таблицы явно указываем колонки в правильном порядке
call :LOAD_TABLE "card_types" "%TEMP_CSV_DIR%\card_types.csv" "id,created_at,updated_at,name,print_name,description,report_name,is_active,sort_order"
call :LOAD_TABLE "cards" "%TEMP_CSV_DIR%\cards.csv" "id,created_at,updated_at,card_type_id,number,holder_name,issue_date,expiry_date,status,comment,balance"
call :LOAD_TABLE "transactions" "%TEMP_CSV_DIR%\transactions.csv" "id,created_at,card_id,amount,transaction_type,transaction_date,terminal_id,terminal_name,route_info,comment"
call :LOAD_TABLE "owners" "%TEMP_CSV_DIR%\owners.csv" "id,created_at,updated_at,name,inn,kpp,address,phone,email"
call :LOAD_TABLE "employees" "%TEMP_CSV_DIR%\employees.csv" "id,created_at,updated_at,full_name,position,login,is_active"
call :LOAD_TABLE "organizations" "%TEMP_CSV_DIR%\organizations.csv" "id,created_at,updated_at,name,inn,kpp,address"
call :LOAD_TABLE "constants" "%TEMP_CSV_DIR%\constants.csv" "id,key,value,description"
call :LOAD_TABLE "counters" "%TEMP_CSV_DIR%\counters.csv" "id,name,current_value,prefix"
call :LOAD_TABLE "mfcs" "%TEMP_CSV_DIR%\mfcs.csv" "id,name,address,phone"
call :LOAD_TABLE "applicants" "%TEMP_CSV_DIR%\applicants.csv" "id,owner_id,full_name,birth_date,document_type,document_number,document_issue_date,document_issuer"
call :LOAD_TABLE "documents" "%TEMP_CSV_DIR%\documents.csv" "id,applicant_id,document_type,document_number,issue_date,issuer"
call :LOAD_TABLE "action_log" "%TEMP_CSV_DIR%\action_log.csv" "id,created_at,user_id,action_type,table_name,record_id,old_values,new_values"

echo.
echo ====================================================
echo Миграция завершена!
echo ====================================================
echo.
echo Важно: После миграции проверьте данные в базе:
echo   "%PG_BIN%\psql.exe" -U %PG_USER% -d %DB_NAME% -c "SELECT COUNT(*) FROM cards;"
echo   "%PG_BIN%\psql.exe" -U %PG_USER% -d %DB_NAME% -c "SELECT COUNT(*) FROM card_types;"
echo   "%PG_BIN%\psql.exe" -U %PG_USER% -d %DB_NAME% -c "SELECT COUNT(*) FROM transactions;"
echo.

REM Очистка временных файлов
echo Очистка временных файлов...
rmdir /s /q "%TEMP_CSV_DIR%"
if exist "json_to_csv.py" del /q "json_to_csv.py"

echo Готово!
pause
