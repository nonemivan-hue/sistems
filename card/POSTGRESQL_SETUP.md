# Настройка PostgreSQL для системы учета транспортных карт

## Параметры подключения к PostgreSQL

Для работы программы с базой данных PostgreSQL `card_system` используются следующие параметры:

- **Хост**: localhost
- **Порт**: 5432
- **База данных**: card_system
- **Пользователь**: postgres
- **Пароль**: 3831043
- **Путь к PostgreSQL**: d:\PostgreSQL\15

## Файлы конфигурации

### 1. Файл .env (в корне проекта)
```
USE_POSTGRES=true
DB_HOST=localhost
DB_PORT=5432
DB_NAME=card_system
DB_USER=postgres
DB_PASSWORD=3831043
```

### 2. app.py
В начале файла app.py настроены переменные окружения для подключения к PostgreSQL:
```python
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "card_system",
    "user": "postgres",
    "password": "3831043",
}
```

### 3. postgres/storage_pg.py
Конфигурация подключения в модуле хранения:
```python
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "database": os.environ.get("DB_NAME", "card_system"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "3831043"),
}
```

## Логирование

Все действия пользователей и операции с базой данных логируются в файлы:
- **Директория логов**: logs/
- **Формат имени файла**: app_YYYYMMDD.log
- **Частота ротации**: ежедневная

В логах фиксируются:
- Действия пользователей (LOGIN, LOGOUT, CREATE_CARD, UPDATE_CARD и т.д.)
- DB операции (SELECT, INSERT, UPDATE, DELETE) с указанием времени выполнения
- Ошибки с полной трассировкой стека
- Метрики производительности

## Диагностика подвисаний

Для диагностики подвисаний программы:
1. Запустите программу
2. Воспроизведите проблему с подвисанием
3. Откройте файл лога за текущую дату в папке logs/
4. Найдите медленные операции (duration > 1000ms) или ошибки

Пример записи в логе:
```
2025-09-10 14:30:15,123 - DB_OPERATION - cards - SELECT - duration: 2500ms
2025-09-10 14:30:15,456 - USER_ACTION - user123 - LOGIN - User admin logged in
2025-09-10 14:30:16,789 - ERROR - Database connection timeout - Traceback...
```

## Установка зависимостей

Для работы с PostgreSQL необходим psycopg2:
```bash
pip install psycopg2-binary
```

## Запуск программы

Программа автоматически использует PostgreSQL при наличии переменных окружения.
Для принудительного использования PostgreSQL убедитесь, что USE_POSTGRES=true.

При работе в Windows (путь d:\card):
1. Убедитесь, что PostgreSQL запущен
2. Проверьте доступность базы данных card_system
3. Запустите приложение
4. Логи будут создаваться в d:\card\logs\
