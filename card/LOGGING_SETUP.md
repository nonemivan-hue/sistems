# Настройка логирования в PostgreSQL для Transport Cards Accounting System

## Обзор

Добавлена система логирования всех действий пользователей и операций с базой данных в файл лога. Это поможет диагностировать проблемы с подвисанием программы при работе с PostgreSQL.

## Что добавлено

### 1. Модуль логирования (`app/logger.py`)

Создан новый модуль `app/logger.py` который предоставляет:

- **log_user_action()** - Логирование действий пользователей (вход, выход, создание карт и т.д.)
- **log_db_query()** - Логирование операций с БД с указанием времени выполнения
- **log_error()** - Логирование ошибок с трассировкой стека
- **log_performance_metric()** - Логирование метрик производительности
- **log_warning()** - Логирование предупреждений

### 2. Интеграция с моделями (`app/models.py`)

Функция `log_action()` теперь записывает действия пользователей:
- В базу данных (таблица `action_log`)
- В файл лога

### 3. Логирование в хранилище PostgreSQL (`postgres/storage_pg.py`)

Все операции с базой данных теперь логируются:
- SELECT, INSERT, UPDATE, DELETE операции
- Время выполнения каждой операции в миллисекундах
- Ошибки с подробной информацией

### 4. Логирование в JSON хранилище (`app/storage.py`)

Аналогичное логирование добавлено для JSON хранилища (для отладки).

## Расположение файлов лога

Файлы логов создаются в директории `/workspace/logs/`:
- `app_YYYYMMDD.log` - ежедневные файлы логов

Пример: `logs/app_20260910.log`

## Формат записи лога

```
2026-09-10 13:37:14 | INFO     | USER_ACTION | user_id=xxx | action=LOGIN | details=User logged in | ip=
2026-09-10 13:37:14 | INFO     | DB_OPERATION | table=cards | op=SELECT | duration=15.23ms
2026-09-10 13:37:14 | ERROR    | ERROR | context=insert(cards) | connection timeout | table=cards
```

## Как использовать для диагностики подвисаний

1. **Запустите программу** и воспроизведите проблему с подвисанием

2. **Откройте файл лога** за текущую дату в директории `logs/`

3. **Найдите медленные операции** - обратите внимание на операции с большим временем выполнения:
   ```
   DB_OPERATION | table=cards | op=SELECT | duration=5000.00ms  # 5 секунд!
   ```

4. **Проверьте блокировки** - если видите много ожидающих операций, возможно есть блокировки в PostgreSQL

5. **Посмотрите ошибки** - раздел ERROR покажет проблемы подключения или выполнения запросов

## Диагностика проблем с PostgreSQL

### Медленные запросы
Если время выполнения запросов превышает 1000ms (1 секунда), это указывает на проблему:
- Отсутствие индексов
- Большие таблицы без оптимизации
- Проблемы с подключением

### Блокировки
Если программа подвисает на операциях UPDATE/DELETE, проверьте:
```sql
-- В PostgreSQL выполните:
SELECT * FROM pg_stat_activity WHERE state = 'idle in transaction';
SELECT * FROM pg_locks WHERE NOT granted;
```

### Проблемы подключения
Ошибки подключения будут записаны в лог:
```
ERROR | context=get_connection | could not connect to server
```

## Рекомендуемые действия

1. **Включите slow query log в PostgreSQL**:
   ```sql
   ALTER SYSTEM SET log_min_duration_statement = 1000;  -- 1 секунда
   SELECT pg_reload_conf();
   ```

2. **Проверьте индексы** в таблице `cards`:
   ```sql
   CREATE INDEX IF NOT EXISTS idx_cards_status ON cards(status);
   CREATE INDEX IF NOT EXISTS idx_cards_type ON cards(card_type_id);
   CREATE INDEX IF NOT EXISTS idx_cards_owner ON cards(owner_id);
   ```

3. **Настройте pool соединений** если у вас много одновременных пользователей

4. **Мониторьте размер таблиц**:
   ```sql
   SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
   FROM pg_tables
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
   ```

## Просмотр логов в реальном времени

```bash
# Linux/Mac
tail -f /workspace/logs/app_*.log

# Windows (PowerShell)
Get-Content d:\card\logs\app_*.log -Wait -Tail 50
```

## Примечания

- Логи автоматически создаются каждый день
- Старые логи можно архивировать или удалять
- Для production рекомендуется настроить ротацию логов
