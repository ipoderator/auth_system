# Система аутентификации и авторизации

Backend-приложение с собственной системой аутентификации и авторизации на основе Django REST Framework и PostgreSQL.

## Описание системы доступа

Система использует модель **RBAC (Role-Based Access Control)** с расширенными возможностями управления правами доступа.

### Архитектура системы доступа

#### Основные сущности:

1. **Users (Пользователи)** - пользователи системы
   - Email используется как уникальный идентификатор
   - Поддержка мягкого удаления через поле `is_active`

2. **Resources (Ресурсы)** - объекты/ресурсы системы
   - Примеры: `products`, `orders`, `reports`, `users`
   - Представляют бизнес-объекты, к которым применяются права доступа

3. **Actions (Действия)** - действия, которые можно выполнять над ресурсами
   - Примеры: `create`, `read`, `update`, `delete`, `list`
   - Стандартные CRUD операции

4. **Permissions (Разрешения)** - комбинация Resource + Action
   - Примеры: `products.read`, `orders.create`, `reports.list`
   - Уникальная комбинация ресурса и действия

5. **Roles (Роли)** - роли пользователей
   - Примеры: `Admin`, `Manager`, `User`, `Guest`
   - Роль содержит набор разрешений

6. **RolePermission** - связь роли с разрешением (many-to-many)

7. **UserRole** - назначение роли пользователю (many-to-many)

### Логика проверки доступа:

1. Пользователь имеет одну или несколько ролей (через UserRole)
2. Роль имеет набор разрешений (через RolePermission)
3. Разрешение = Resource + Action
4. При запросе к ресурсу проверяется:
   - Аутентифицирован ли пользователь? → 401 если нет
   - Есть ли у пользователя роль с нужным разрешением? → 403 если нет
   - Если есть → доступ разрешен

### Предустановленные роли и права:

- **Admin**: Все права на все ресурсы
- **Manager**: 
  - `products.*` (все действия)
  - `orders.read`, `orders.list`
- **User**: 
  - `products.read`, `products.list`
  - `orders.create`
- **Guest**: 
  - `products.list`

## Установка и запуск

### Требования

- Python 3.8+
- PostgreSQL 12+
- pip

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Настройка базы данных

1. Создайте базу данных PostgreSQL:

```sql
CREATE DATABASE auth_system;
```

2. Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

3. Отредактируйте `.env` с вашими настройками БД:

```
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=auth_system
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

TOKEN_EXPIRATION_HOURS=24
```

### Применение миграций

```bash
python manage.py migrate
```

### Инициализация тестовых данных

```bash
python manage.py init_test_data
```

Эта команда создаст:
- Ресурсы: products, orders, reports, users
- Действия: create, read, update, delete, list
- Разрешения: все комбинации ресурсов и действий
- Роли: Admin, Manager, User, Guest
- Тестовых пользователей:
  - admin@example.com / admin123 (Admin)
  - manager@example.com / manager123 (Manager)
  - user@example.com / user123 (User)
  - guest@example.com / guest123 (Guest)

### Запуск сервера разработки

```bash
python manage.py runserver
```

Сервер будет доступен по адресу: http://localhost:8000

## API Endpoints

### Аутентификация (`/api/auth/`)

#### Регистрация
```
POST /api/auth/register/
Body: {
    "email": "user@example.com",
    "password": "password123",
    "password_confirm": "password123",
    "first_name": "Иван",
    "last_name": "Иванов",
    "middle_name": "Иванович"
}
```

#### Вход
```
POST /api/auth/login/
Body: {
    "email": "user@example.com",
    "password": "password123"
}
Response: {
    "token": "token-string",
    "user": {...},
    "expires_at": "2024-01-01T12:00:00Z"
}
```

#### Выход
```
POST /api/auth/logout/
Headers: Authorization: Token <token>
```

#### Профиль пользователя
```
GET /api/auth/profile/me/
Headers: Authorization: Token <token>

PUT /api/auth/profile/update_profile/
Headers: Authorization: Token <token>
Body: {
    "first_name": "Новое имя",
    "last_name": "Новая фамилия",
    "middle_name": "Новое отчество"
}

PATCH /api/auth/profile/partial_update_profile/
Headers: Authorization: Token <token>
Body: {
    "first_name": "Новое имя"
}

DELETE /api/auth/profile/delete_account/
Headers: Authorization: Token <token>
(Мягкое удаление аккаунта)
```

### Административные API (`/api/admin/`) - только для администраторов

#### Ресурсы
```
GET /api/admin/resources/
POST /api/admin/resources/
GET /api/admin/resources/{id}/
PUT /api/admin/resources/{id}/
DELETE /api/admin/resources/{id}/
```

#### Действия
```
GET /api/admin/actions/
POST /api/admin/actions/
GET /api/admin/actions/{id}/
PUT /api/admin/actions/{id}/
DELETE /api/admin/actions/{id}/
```

#### Разрешения
```
GET /api/admin/permissions/
POST /api/admin/permissions/
POST /api/admin/permissions/create-by-names/
Body: {
    "resource_name": "products",
    "action_name": "read"
}
GET /api/admin/permissions/{id}/
PUT /api/admin/permissions/{id}/
DELETE /api/admin/permissions/{id}/
```

#### Роли
```
GET /api/admin/roles/
POST /api/admin/roles/
Body: {
    "name": "NewRole",
    "description": "Description",
    "permission_ids": [1, 2, 3]
}
GET /api/admin/roles/{id}/
PUT /api/admin/roles/{id}/
DELETE /api/admin/roles/{id}/

POST /api/admin/roles/{id}/permissions/
Body: {
    "permission_id": 1
    # или
    "resource_name": "products",
    "action_name": "read"
}

DELETE /api/admin/roles/{id}/permissions/{permission_id}/
```

#### Назначение ролей пользователям
```
GET /api/admin/user-roles/
POST /api/admin/user-roles/assign/
Body: {
    "user_id": 1,
    "role_id": 2
}
GET /api/admin/user-roles/user/{user_id}/
DELETE /api/admin/user-roles/{id}/
```

### Mock бизнес-объекты (`/api/`)

#### Продукты
```
GET /api/products/
Headers: Authorization: Token <token>
(Требует: products.list)

GET /api/products/{id}/
Headers: Authorization: Token <token>
(Требует: products.read)

POST /api/products/
Headers: Authorization: Token <token>
Body: {
    "name": "Product Name",
    "price": 100,
    "description": "Description"
}
(Требует: products.create)

PUT /api/products/{id}/
Headers: Authorization: Token <token>
(Требует: products.update)

DELETE /api/products/{id}/
Headers: Authorization: Token <token>
(Требует: products.delete)
```

#### Заказы
```
GET /api/orders/
Headers: Authorization: Token <token>
(Требует: orders.list)

GET /api/orders/{id}/
Headers: Authorization: Token <token>
(Требует: orders.read)

POST /api/orders/
Headers: Authorization: Token <token>
Body: {
    "product_ids": [1, 2],
    "total": 300,
    "status": "pending"
}
(Требует: orders.create)

PUT /api/orders/{id}/
Headers: Authorization: Token <token>
(Требует: orders.update)

DELETE /api/orders/{id}/
Headers: Authorization: Token <token>
(Требует: orders.delete)
```

#### Отчеты
```
GET /api/reports/
Headers: Authorization: Token <token>
(Требует: reports.list)

GET /api/reports/{id}/
Headers: Authorization: Token <token>
(Требует: reports.read)
```

## Коды ошибок

- **401 Unauthorized**: Пользователь не аутентифицирован (нет токена или токен недействителен)
- **403 Forbidden**: Пользователь аутентифицирован, но не имеет прав доступа к ресурсу
- **404 Not Found**: Ресурс не найден
- **400 Bad Request**: Неверные данные запроса

## Примеры использования

### 1. Регистрация и вход

```bash
# Регистрация
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "password123",
    "password_confirm": "password123",
    "first_name": "Иван",
    "last_name": "Иванов"
  }'

# Вход
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "user123"
  }'
```

### 2. Получение списка продуктов (требует products.list)

```bash
curl -X GET http://localhost:8000/api/products/ \
  -H "Authorization: Token <your-token>"
```

### 3. Создание продукта (требует products.create)

```bash
curl -X POST http://localhost:8000/api/products/ \
  -H "Authorization: Token <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Product",
    "price": 150,
    "description": "Product description"
  }'
```

### 4. Назначение роли пользователю (только для администратора)

```bash
curl -X POST http://localhost:8000/api/admin/user-roles/assign/ \
  -H "Authorization: Token <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "role_id": 3
  }'
```

## Структура проекта

```
auth_system/
├── config/              # Настройки Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── logging.py       # Настройка логирования loguru
├── logs/                # Директория с логами (создается автоматически)
│   ├── app_YYYY-MM-DD.log
│   └── errors_YYYY-MM-DD.log
├── apps/
│   ├── users/           # Модуль пользователей
│   │   ├── models.py    # CustomUser, UserProfile, Token
│   │   ├── views.py     # AuthViewSet, ProfileViewSet
│   │   ├── serializers.py
│   │   ├── authentication.py  # CustomTokenAuthentication
│   │   └── urls.py
│   ├── authorization/   # Модуль авторизации
│   │   ├── models.py    # Role, Resource, Action, Permission, etc.
│   │   ├── views.py     # Admin ViewSets
│   │   ├── permissions.py  # HasResourcePermission, IsAdmin
│   │   ├── serializers.py
│   │   └── urls.py
│   └── mock_business/   # Mock бизнес-объекты
│       ├── views.py     # MockProductViewSet, MockOrderViewSet
│       └── urls.py
├── manage.py
├── requirements.txt
├── test_application.py  # Скрипт для проверки работы приложения
└── README.md
```

## Особенности реализации

1. **Собственная система токенов**: Не используется стандартный `rest_framework.authtoken`, реализована собственная модель Token с поддержкой истечения срока действия
2. **Мягкое удаление**: Пользователи не удаляются физически, устанавливается `is_active=False`
3. **Custom Permission Classes**: Реализованы собственные классы разрешений для проверки доступа к ресурсам
4. **RBAC система**: Гибкая система управления правами через роли и разрешения
5. **Логирование с Loguru**: Используется библиотека [loguru](https://github.com/Delgan/loguru) для структурированного логирования с автоматической ротацией и архивацией логов. Все записи используют московский часовой пояс (UTC+3)

## Разработка

### Создание миграций

```bash
python manage.py makemigrations
python manage.py migrate
```

### Создание суперпользователя

```bash
python manage.py createsuperuser
```

### Доступ к админ-панели Django

```
http://localhost:8000/admin/
```

### Логирование

Проект использует библиотеку **loguru** для логирования. Логирование настроено автоматически при запуске Django приложения.

#### Особенности логирования:

- **Консольный вывод**: Цветной вывод в консоль для разработки (уровень DEBUG и выше)
- **Файловое логирование**: 
  - `logs/app_YYYY-MM-DD.log` - общий лог всех событий (ротация в полночь, хранение 30 дней)
  - `logs/errors_YYYY-MM-DD.log` - отдельный файл для ошибок (хранение 90 дней)
- **Московское время**: Все записи в логах используют московский часовой пояс (UTC+3, Europe/Moscow)
- **Автоматическая ротация**: Логи ротируются ежедневно в полночь по московскому времени
- **Автоматическое сжатие**: Старые логи автоматически сжимаются в ZIP
- **Интеграция с Django**: Перехватывает сообщения из стандартного logging Django

#### Использование в коде:

```python
from loguru import logger

# Различные уровни логирования
logger.debug("Отладочная информация")
logger.info("Информационное сообщение")
logger.success("Успешная операция")
logger.warning("Предупреждение")
logger.error("Ошибка")
logger.exception("Ошибка с полным traceback")
```

#### Что логируется:

- **Аутентификация**: попытки входа, регистрации, выхода, ошибки токенов
- **Авторизация**: проверка прав доступа, отказы в доступе
- **Операции пользователей**: регистрация, обновление профиля, удаление аккаунтов
- **Ошибки**: все исключения и ошибки приложения

#### Настройка уровня логирования:

Уровень логирования можно настроить через переменные окружения:

```bash
# Linux / macOS
export LOGURU_LEVEL=INFO

# Windows
setx LOGURU_LEVEL INFO
```

Доступные уровни: `TRACE`, `DEBUG`, `INFO`, `SUCCESS`, `WARNING`, `ERROR`, `CRITICAL`

#### Просмотр логов:

```bash
# Просмотр последних записей общего лога
tail -f logs/app_$(date +%Y-%m-%d).log

# Просмотр ошибок
tail -f logs/errors_$(date +%Y-%m-%d).log

# Поиск по логам
grep "ERROR" logs/app_*.log
```

### Тестирование приложения

В проекте доступен скрипт `test_application.py` для автоматической проверки работы всего приложения.

#### Что проверяет скрипт:

- **База данных**: подключение, наличие таблиц, наличие тестовых данных
- **API endpoints**: доступность API, регистрация, вход, защищенные эндпоинты
- **Админка**: доступность админ-панели Django
- **Фронтенд**: доступность основных страниц

#### Использование:

```bash
python test_application.py
```

или с активированным виртуальным окружением:

```bash
source venv/bin/activate && python test_application.py
```

#### Особенности:

- **Автоматический запуск сервера**: Скрипт автоматически запускает Django сервер перед проверками и останавливает его после завершения
- **Умное определение сервера**: Если сервер уже запущен на порту 8000, скрипт использует существующий экземпляр и не останавливает его
- **Корректная очистка**: При завершении скрипта (включая Ctrl+C) сервер корректно останавливается

#### Требования перед запуском:

1. Применены миграции: `python manage.py migrate`
2. Инициализированы тестовые данные: `python manage.py init_test_data`
3. Порт 8000 свободен (или сервер уже запущен)

#### Пример вывода:

```
============================================================
  ПРОВЕРКА РАБОТЫ ПРИЛОЖЕНИЯ
============================================================
Время проверки: 2024-01-01 12:00:00
Базовый URL: http://localhost:8000

============================================================
  ПОДГОТОВКА СЕРВЕРА
============================================================
ℹ️  Запуск сервера Django...
ℹ️  Процесс сервера запущен (PID: 12345)
✅ Сервер успешно запущен и готов к работе

============================================================
  ПРОВЕРКА БАЗЫ ДАННЫХ
============================================================
✅ Подключение к БД работает
✅ Все таблицы существуют (9 таблиц)
...
```

## Лицензия

Проект создан в качестве тестового задания для EffectiveMobile 

