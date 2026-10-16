#!/usr/bin/env python3
"""
json_to_csv.py - Утилита для преобразования JSON файлов в CSV формат для импорта в PostgreSQL

Особенности:
- Корректная обработка полей (исключает лишние данные)
- Правильное экранирование кавычек и спецсимволов
- Поддержка кодировки UTF-8
- Опция явного указания колонок для соответствия структуре БД

Использование:
    python json_to_csv.py <input_json_file> <output_csv_file>
    python json_to_csv.py --dir <path_to_data_folder> [--output <output_folder>]
    python json_to_csv.py --table card_types --input data/card_types.json --output csv/card_types.csv
    
Пример:
    python json_to_csv.py data/cards.json output/cards.csv
"""

import json
import csv
import sys
import os
from datetime import datetime

# Соответствие таблиц и их колонок для строгого порядка экспорта
# Порядок колонок должен совпадать с порядком в таблице PostgreSQL!
TABLE_COLUMNS = {
    "card_types": ["id", "name", "report_name", "created_at", "updated_at"],
    "cards": ["id", "number", "holder_name", "card_type_id", "balance", "created_at", "updated_at"],
    "transactions": ["id", "card_id", "amount", "transaction_type", "merchant", "category", "created_at"],
}


def convert_value(value):
    """Преобразует значение в строковый формат, подходящий для CSV"""
    if value is None:
        return ''
    elif isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, (list, dict)):
        # Сложные типы данных сериализуем в JSON
        return json.dumps(value, ensure_ascii=False)
    elif isinstance(value, str):
        # Проверяем, не является ли строка датой/временем
        if len(value) == 19 and value[4] == '-' and value[7] == '-':
            try:
                # Попытка распознать дату
                datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
                return value.replace('T', ' ')
            except ValueError:
                pass
        return value
    else:
        return str(value)


def get_columns_for_table(table_name):
    """Возвращает список колонок для указанной таблицы"""
    # Извлекаем имя таблицы из имени файла (без пути и расширения)
    base_name = os.path.splitext(os.path.basename(table_name))[0]
    return TABLE_COLUMNS.get(base_name, None)


def json_to_csv(json_file, csv_file, columns=None):
    """
    Преобразует JSON файл в CSV формат
    
    Args:
        json_file: Путь к входному JSON файлу
        csv_file: Путь к выходному CSV файлу
        columns: Список колонок для экспорта (опционально, для строгого соответствия БД)
        
    Returns:
        bool: True если успешно, False иначе
    """
    print(f"Обработка файла: {json_file}")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Ошибка чтения JSON: {e}")
        return False
    except FileNotFoundError:
        print(f"Файл не найден: {json_file}")
        return False
    
    if not data:
        print(f"Файл {json_file} пустой")
        return False
    
    # Если данные в виде словаря {...}, преобразуем в список
    if isinstance(data, dict):
        data = [data]
    
    if not isinstance(data, list):
        print(f"Неподдерживаемый формат данных в {json_file}. Ожидается список объектов.")
        return False
    
    # Определяем колонки
    if columns:
        fieldnames = columns
        print(f"Используем явный список колонок: {fieldnames}")
    else:
        # Автоматическое определение колонок
        all_keys = set()
        for item in data:
            if isinstance(item, dict):
                all_keys.update(item.keys())
        
        # Сортируем ключи для консистентности
        fieldnames = sorted(list(all_keys))
        print(f"Автоматически определено полей: {len(fieldnames)}")
    
    if not fieldnames:
        print(f"Нет данных для экспорта в {json_file}")
        return False
    
    print(f"Найдено записей: {len(data)}")
    
    try:
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            # Используем QUOTE_MINIMAL для корректного экранирования
            writer = csv.DictWriter(f, fieldnames=fieldnames, 
                                   quoting=csv.QUOTE_MINIMAL,
                                   extrasaction='ignore')  # Игнорируем лишние поля в JSON
            writer.writeheader()
            
            count = 0
            for row in data:
                if not isinstance(row, dict):
                    continue
                
                # Преобразуем все значения в строковый формат
                csv_row = {}
                for key in fieldnames:
                    csv_row[key] = convert_value(row.get(key, ''))
                
                writer.writerow(csv_row)
                count += 1
        
        print(f"Успешно: {json_file} -> {csv_file} ({count} записей)")
        return True
        
    except Exception as e:
        print(f"Ошибка записи CSV: {e}")
        return False


def process_directory(data_dir, output_dir=None):
    """
    Обрабатывает все JSON файлы в директории
    
    Args:
        data_dir: Путь к папке с JSON файлами
        output_dir: Путь к папке для CSV файлов (по умолчанию создается подпапка 'csv')
    """
    if output_dir is None:
        output_dir = os.path.join(data_dir, 'csv')
    
    os.makedirs(output_dir, exist_ok=True)
    
    json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    
    if not json_files:
        print(f"В папке {data_dir} не найдено JSON файлов")
        return 0, 0
    
    success_count = 0
    failed_count = 0
    
    print(f"Найдено JSON файлов: {len(json_files)}")
    print("=" * 60)
    
    for json_file in sorted(json_files):
        json_path = os.path.join(data_dir, json_file)
        csv_filename = os.path.splitext(json_file)[0] + '.csv'
        csv_path = os.path.join(output_dir, csv_filename)
        
        # Пытаемся определить колонки для этой таблицы
        columns = get_columns_for_table(json_file)
        
        if json_to_csv(json_path, csv_path, columns):
            success_count += 1
        else:
            failed_count += 1
        
        print("-" * 60)
    
    return success_count, failed_count


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nРежимы работы:")
        print("  1. Одиночный файл:")
        print("     python json_to_csv.py <input.json> <output.csv>")
        print("\n  2. Обработка папки:")
        print("     python json_to_csv.py --dir <path_to_data_folder> [--output <output_folder>]")
        print("\n  3. С явным указанием колонок:")
        print("     python json_to_csv.py --table card_types --input data/card_types.json --output csv/card_types.csv")
        sys.exit(1)
    
    # Режим с явным указанием таблицы
    if sys.argv[1] == '--table':
        if len(sys.argv) < 5 or '--input' not in sys.argv or '--output' not in sys.argv:
            print("Ошибка: укажите --table, --input и --output")
            sys.exit(1)
        
        table_name = sys.argv[2]
        input_file = sys.argv[sys.argv.index('--input') + 1]
        output_file = sys.argv[sys.argv.index('--output') + 1]
        
        columns = get_columns_for_table(table_name)
        if not columns:
            print(f"Предупреждение: для таблицы '{table_name}' не задан явный список колонок")
            print("Будет использовано автоматическое определение")
        
        if json_to_csv(input_file, output_file, columns):
            sys.exit(0)
        else:
            sys.exit(1)
    
    # Режим обработки директории
    if sys.argv[1] == '--dir':
        if len(sys.argv) < 3:
            print("Ошибка: укажите путь к папке с данными")
            sys.exit(1)
        
        data_dir = sys.argv[2]
        output_dir = None
        
        if len(sys.argv) >= 5 and sys.argv[3] == '--output':
            output_dir = sys.argv[4]
        
        success, failed = process_directory(data_dir, output_dir)
        
        print("\n" + "=" * 60)
        print(f"Итого: обработано успешно - {success}, с ошибками - {failed}")
        
        sys.exit(0 if failed == 0 else 1)
    
    # Режим одиночного файла
    if len(sys.argv) != 3:
        print("Ошибка: укажите входной и выходной файлы")
        print(__doc__)
        sys.exit(1)
    
    json_file = sys.argv[1]
    csv_file = sys.argv[2]
    
    # Пытаемся определить колонки для этой таблицы
    columns = get_columns_for_table(json_file)
    
    if json_to_csv(json_file, csv_file, columns):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
