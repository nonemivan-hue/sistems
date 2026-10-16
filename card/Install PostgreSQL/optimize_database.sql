-- Скрипт оптимизации базы данных Transport Cards
-- Предназначен для устранения проблем с производительностью и ограничениями длины полей

-- 1. Исправление ограничений длины полей (решает ошибку "value too long for type character varying")
-- Увеличиваем длину текстовых полей до TEXT для свободы ввода данных

ALTER TABLE IF EXISTS card_types 
    ALTER COLUMN print_name TYPE TEXT,
    ALTER COLUMN description TYPE TEXT;

ALTER TABLE IF EXISTS cards 
    ALTER COLUMN note TYPE TEXT;

-- 2. Создание индексов для ускорения выборок (решает проблему "подвисания")
-- Индексы критически важны для быстрого поиска карт и формирования отчетов

-- Индекс для поиска карты по номеру
CREATE INDEX IF NOT EXISTS idx_cards_number ON cards(number);

-- Индекс для поиска карт по типу
CREATE INDEX IF NOT EXISTS idx_cards_card_type_id ON cards(card_type_id);

-- Индекс для поиска транзакций по дате (важно для отчета "Отчет за период")
CREATE INDEX IF NOT EXISTS idx_transactions_transaction_date ON transactions(transaction_date);

-- Индекс для поиска транзакций по карте
CREATE INDEX IF NOT EXISTS idx_transactions_card_id ON transactions(card_id);

-- Индекс для поиска по UUID (стандартная практика для PostgreSQL)
CREATE INDEX IF NOT EXISTS idx_cards_id ON cards(id);
CREATE INDEX IF NOT EXISTS idx_card_types_id ON card_types(id);
CREATE INDEX IF NOT EXISTS idx_transactions_id ON transactions(id);

-- 3. Оптимизация хранилища и обновление статистики
-- VACUUM освобождает место, ANALYZE обновляет статистику для планировщика запросов
VACUUM ANALYZE card_types;
VACUUM ANALYZE cards;
VACUUM ANALYZE transactions;

-- Вывод сообщения об успехе
SELECT 'Оптимизация базы данных успешно завершена!' AS result;
