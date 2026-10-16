@echo off
chcp 65001 >nul
REM Скрипт проверки активных блокировок и сессий в PostgreSQL
REM Использование: check_locks.bat

set PGHOST=localhost
set PGPORT=5432
set PGDATABASE=transport_cards
set PGPASSWORD=3831043
set PGUSER=postgres

set PG_BIN=D:\PostgreSQL\15\bin

echo ============================================
echo Проверка активных сессий и блокировок
echo ============================================
echo.

echo [1] Активные сессии:
"%PG_BIN%\psql.exe" -c "SELECT pid, usename, application_name, client_addr, backend_start, state, query FROM pg_stat_activity WHERE datname = '%PGDATABASE%' AND pid <> pg_backend_pid();"

echo.
echo [2] Текущие блокировки:
"%PG_BIN%\psql.exe" -c "SELECT blocked_locks.pid AS blocked_pid, blocked_activity.usename AS blocked_user, blocking_locks.pid AS blocking_pid, blocking_activity.usename AS blocking_user, blocked_activity.query AS blocked_statement, blocking_activity.query AS current_statement_in_blocking_process FROM pg_catalog.pg_locks blocked_locks JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid AND blocking_locks.pid != blocked_locks.pid JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid WHERE NOT blocked_locks.GRANTED;"

echo.
echo [3] Длительные запросы (> 30 сек):
"%PG_BIN%\psql.exe" -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state FROM pg_stat_activity WHERE (now() - pg_stat_activity.query_start) > interval '30 seconds' AND datname = '%PGDATABASE%' AND pid <> pg_backend_pid();"

echo.
echo ============================================
echo Для завершения зависшей сессии выполните:
echo SELECT pg_terminate_backend(PID);
echo где PID - номер процесса из списка выше
echo ============================================
pause
