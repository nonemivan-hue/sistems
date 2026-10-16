# Инструкция по загрузке данных из локальной папки Data в PostgreSQL

Данное руководство описывает процесс переноса данных из JSON-файлов локальной папки `Data` в базу данных PostgreSQL.

## Содержание

1. [Подготовка](#подготовка)
2. [Способ 1: Автоматическая миграция через скрипт (РЕКОМЕНДУЕТСЯ)](#способ-1-автоматическая-миграция-через-скрипт-рекомендуется)
3. [Способ 2: Ручная загрузка через Python утилиту](#способ-2-ручная-загрузка-через-python-утилиту)
4. [Способ 3: Пошаговая загрузка через psql](#способ-3-пошаговая-загрузка-через-psql)
5. [Решение проблемы с длиной полей (ОШИБКА: значение не умещается)](#решение-проблемы-с-длиной-полей-ошибка-значение-не-умещается)
6. [Проверка результатов](#проверка-результатов)
7. [Устранение неполадок](#устранение-неполадок)

---

## Подготовка

### Требования

- Установленный PostgreSQL 15 по пути: `D:\PostgreSQL\15`
- Приложение установлено по пути: `D:\card`
- Пароль PostgreSQL: `3831043`
- Python 3.8+ с модулями `json` и `csv` (входят в стандартную библиотеку)
- Папка `Data` с JSON-файлами экспортированных данных
- Созданная база данных PostgreSQL с инициализированной схемой

### Шаг 1: Проверка структуры папки Data

Убедитесь, что папка `Data` содержит следующие JSON-файлы:

```
D:\card\Data\
├── card_types.json      # Типы карт
├── cards.json           # Карты
├── transactions.json    # Транзакции
├── owners.json          # Владельцы карт
├── applicants.json      # Заявители
├── organizations.json   # Организации
├── mfcs.json            # МФЦ
├── employees.json       # Сотрудники
├── documents.json       # Документы
├── action_log.json      # Журнал действий
├── constants.json       # Константы системы
└── counters.json        # Счетчики
```

### Шаг 2: Инициализация схемы БД

Перед загрузкой данных необходимо создать структуру таблиц:

```cmd
"D:\PostgreSQL\15\bin\psql.exe" -U postgres -d card_system -f "D:\card\postgres\init.sql"
```

Или через pgAdmin: выполните SQL-скрипт создания таблиц.

---

## Решение проблемы с длиной полей (ОШИБКА: значение не умещается)

**ВАЖНО:** Перед миграцией данных выполните скрипт увеличения длины текстовых полей, чтобы избежать ошибки:
> ОШИБКА: значение не умещается в тип character varying(255)

### Автоматическое решение

Скрипт миграции `migrate_from_json.bat` **автоматически** выполняет скрипт `fix_column_lengths.sql` перед загрузкой данных.

### Ручное выполнение (если нужно)

```cmd
"D:\PostgreSQL\15\bin\psql.exe" -U postgres -d card_system -f "D:\card\Install PostgreSQL\fix_column_lengths.sql"
```

Этот скрипт изменяет типы данных следующих полей на `TEXT`:
- `card_types`: name, print_name, description, report_name
- `cards`: number, holder_name, comment
- `transactions`: comment, terminal_name, route_info

---

## Способ 1: Автоматическая миграция через скрипт (РЕКОМЕНДУЕТСЯ)

### Быстрый старт

1. Откройте командную строку (cmd) от имени администратора
2. Перейдите в папку со скриптами:
   ```cmd
   cd D:\card\Install PostgreSQL
   ```
3. Запустите скрипт миграции:
   ```cmd
   migrate_from_json.bat
   ```

### Параметры командной строки

```cmd
migrate_from_json.bat [путь_к_папке_Data] [имя_БД] [пользователь]
```

Пример:
```cmd
migrate_from_json.bat D:\card\Data card_system postgres
```

### Что делает скрипт:

1. **Шаг 0**: Выполняет `fix_column_lengths.sql` для увеличения длины текстовых полей
2. **Шаг 1**: Конвертирует все JSON файлы из папки `Data` в CSV формат
3. **Шаг 2**: Загружает данные в PostgreSQL с явным указанием колонок
4. **Шаг 3**: Очищает временные файлы

### Логирование

Скрипт выводит подробный лог в консоль:
- `[УСПЕХ]` - операция выполнена успешно
- `[ОШИБКА]` - критическая ошибка, требующая вмешательства
- `[ПРЕДУПРЕЖДЕНИЕ]` - не критичная проблема
- `[ПРОПУСК]` - файл/таблица пропущены

---

## Способ 2: Ручная загрузка через Python утилиту

### Шаг 1: Конвертация JSON в CSV

```cmd
cd D:\card\Install PostgreSQL
python json_to_csv.py --dir D:\card\Data --output D:\card\csv_output
```

### Шаг 2: Импорт через psql

```cmd
"D:\PostgreSQL\15\bin\psql.exe" -U postgres -d card_system -c "\COPY card_types (id,created_at,updated_at,name,print_name,description,report_name,is_active,sort_order) FROM 'D:\card\csv_output\card_types.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');"
```

---

## Способ 3: Пошаговая загрузка через psql

### Для таблицы card_types:

```sql
-- Очистка таблицы
TRUNCATE TABLE card_types RESTART IDENTITY CASCADE;

-- Импорт данных
\COPY card_types (id,created_at,updated_at,name,print_name,description,report_name,is_active,sort_order) 
FROM 'D:\card\Data\card_types.csv' 
WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
```

### Для таблицы cards:

```sql
TRUNCATE TABLE cards RESTART IDENTITY CASCADE;

\COPY cards (id,created_at,updated_at,card_type_id,number,holder_name,issue_date,expiry_date,status,comment,balance) 
FROM 'D:\card\Data\cards.csv' 
WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
```

### Для таблицы transactions:

```sql
TRUNCATE TABLE transactions RESTART IDENTITY CASCADE;

\COPY transactions (id,created_at,card_id,amount,transaction_type,transaction_date,terminal_id,terminal_name,route_info,comment) 
FROM 'D:\card\Data\transactions.csv' 
WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
```

---

## Проверка результатов

После миграции выполните проверки:

```cmd
REM Подсчет записей в таблицах
"D:\PostgreSQL\15\bin\psql.exe" -U postgres -d card_system -c "SELECT COUNT(*) FROM card_types;"
"D:\PostgreSQL\15\bin\psql.exe" -U postgres -d card_system -c "SELECT COUNT(*) FROM cards;"
"D:\PostgreSQL\15\bin\psql.exe" -U postgres -d card_system -c "SELECT COUNT(*) FROM transactions;"

REM Проверка последних записей
"D:\PostgreSQL\15\bin\psql.exe" -U postgres -d card_system -c "SELECT * FROM card_types ORDER BY created_at DESC LIMIT 5;"
```

---

## Устранение неполадок

### Ошибка: "значение не умещается в тип character varying(255)"

**Решение:** Выполните скрипт `fix_column_lengths.sql` перед импортом:

```cmd
"D:\PostgreSQL\15\bin\psql.exe" -U postgres -d card_system -f "D:\card\Install PostgreSQL\fix_column_lengths.sql"
```

### Ошибка: "лишние данные после содержимого последнего столбца"

**Причина:** Порядок колонок в CSV не совпадает с таблицей или есть лишние поля.

**Решение:** Используйте явное указание колонок в команде COPY:

```sql
\COPY table_name (col1,col2,col3) FROM 'file.csv' WITH (FORMAT csv, HEADER true);
```

### Ошибка: "файл не найден"

**Решение:**
1. Проверьте путь к файлу (используйте абсолютные пути)
2. Убедитесь, что файл существует
3. Проверьте права доступа к файлу

### Ошибка: "отношение уже существует"

**Решение:** Очистите таблицу перед импортом:

```sql
TRUNCATE TABLE table_name RESTART IDENTITY CASCADE;
```

---

## Контакты и поддержка

При возникновении проблем обратитесь к документации PostgreSQL или системному администратору.
