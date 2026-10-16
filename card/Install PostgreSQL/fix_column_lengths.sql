-- Скрипт для увеличения длины текстовых полей, чтобы избежать ошибки 
-- "значение не умещается в тип character varying(255)"
-- Выполняется перед импортом данных из JSON/CSV

-- Таблица card_types (Виды карт)
ALTER TABLE IF EXISTS card_types ALTER COLUMN name TYPE TEXT;
ALTER TABLE IF EXISTS card_types ALTER COLUMN print_name TYPE TEXT;
ALTER TABLE IF EXISTS card_types ALTER COLUMN description TYPE TEXT;
ALTER TABLE IF EXISTS card_types ALTER COLUMN report_name TYPE TEXT;

-- Таблица cards (Карты)
ALTER TABLE IF EXISTS cards ALTER COLUMN number TYPE VARCHAR(100); -- Номера карт могут быть длинными
ALTER TABLE IF EXISTS cards ALTER COLUMN holder_name TYPE TEXT;
ALTER TABLE IF EXISTS cards ALTER COLUMN comment TYPE TEXT;

-- Таблица transactions (Транзакции) - на всякий случай
ALTER TABLE IF EXISTS transactions ALTER COLUMN comment TYPE TEXT;
ALTER TABLE IF EXISTS transactions ALTER COLUMN terminal_name TYPE TEXT;
ALTER TABLE IF EXISTS transactions ALTER COLUMN route_info TYPE TEXT;

-- Пересоздание последовательностей (если нужно сбросить ID после очистки)
-- Внимание: Скрипт миграции сам делает TRUNCate, ID сбрасываются там.
