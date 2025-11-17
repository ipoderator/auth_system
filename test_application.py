#!/usr/bin/env python
"""
Скрипт для проверки работы всего приложения:
- База данных
- API endpoints
- Админка
- Фронтенд

Скрипт автоматически запускает Django сервер перед проверками
и останавливает его после завершения.

Использование:
    python test_application.py
    или
    source venv/bin/activate && python test_application.py

Примечание: Если сервер уже запущен на порту 8000,
скрипт использует существующий экземпляр и не останавливает его.
"""

import os
import sys
import django
import requests
import subprocess
import time
import signal
import atexit
from datetime import datetime
from loguru import logger

# Настройка loguru для тестового скрипта
logger.remove()  # Удаляем стандартный обработчик
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO",
    colorize=True,
)

# Проверка виртуального окружения
has_venv = (
    hasattr(sys, 'real_prefix')
    or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
)
if not has_venv:
    logger.warning(
        "Виртуальное окружение не активировано! "
        "Рекомендуется запускать с активированным окружением: "
        "source venv/bin/activate && python test_application.py"
    )

# Настройка Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.db import connection  # noqa: E402
from apps.authorization.models import (  # noqa: E402
    Resource, Action, Permission, Role, UserRole
)

User = get_user_model()

BASE_URL = "http://localhost:8000"
SERVER_PORT = 8000

# Глобальная переменная для хранения процесса сервера
server_process = None
server_started_by_script = False


def print_header(text):
    """Печать заголовка секции."""
    logger.info("\n" + "=" * 60)
    logger.info(f"  {text}")
    logger.info("=" * 60)


def print_success(text):
    """Печать успешного результата."""
    logger.success(text)


def print_error(text):
    """Печать ошибки."""
    logger.error(text)


def print_info(text):
    """Печать информации."""
    logger.info(text)


def is_server_running():
    """Проверка, запущен ли сервер."""
    try:
        requests.get(f"{BASE_URL}/api/", timeout=2)
        return True
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False


def start_server():
    """Запуск сервера Django в фоновом режиме."""
    global server_process, server_started_by_script

    if is_server_running():
        print_info("Сервер уже запущен")
        return True

    print_info("Запуск сервера Django...")

    try:
        # Определяем команду для запуска сервера
        python_executable = sys.executable
        manage_py_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "manage.py"
        )

        # Запускаем сервер в фоновом режиме
        server_process = subprocess.Popen(
            [python_executable, manage_py_path, "runserver", str(SERVER_PORT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        server_started_by_script = True
        print_info(f"Процесс сервера запущен (PID: {server_process.pid})")

        # Ждем, пока сервер запустится
        max_attempts = 30
        for attempt in range(max_attempts):
            time.sleep(1)
            if is_server_running():
                print_success("Сервер успешно запущен и готов к работе")
                return True
            if server_process.poll() is not None:
                # Процесс завершился
                stdout, stderr = server_process.communicate()
                print_error(
                    f"Сервер завершился с ошибкой:\n"
                    f"STDOUT: {stdout.decode()[:200]}\n"
                    f"STDERR: {stderr.decode()[:200]}"
                )
                server_started_by_script = False
                return False

        print_error(
            f"Сервер не ответил за {max_attempts} секунд. "
            "Возможно, порт занят или произошла ошибка."
        )
        stop_server()
        return False

    except Exception as e:
        print_error(f"Ошибка при запуске сервера: {e}")
        server_started_by_script = False
        return False


def stop_server():
    """Остановка сервера, запущенного скриптом."""
    global server_process, server_started_by_script

    if not server_started_by_script or server_process is None:
        return

    print_info("Остановка сервера...")

    try:
        # Пытаемся остановить процесс корректно
        server_process.terminate()

        # Ждем завершения процесса (максимум 5 секунд)
        try:
            server_process.wait(timeout=5)
            print_success("Сервер остановлен")
        except subprocess.TimeoutExpired:
            # Если процесс не завершился, принудительно убиваем
            server_process.kill()
            server_process.wait()
            print_info("Сервер принудительно остановлен")

        server_process = None
        server_started_by_script = False

    except Exception as e:
        print_error(f"Ошибка при остановке сервера: {e}")


def cleanup_on_exit():
    """Очистка при выходе из скрипта."""
    stop_server()


# Регистрируем функцию очистки при выходе
atexit.register(cleanup_on_exit)


def signal_handler(signum, frame):
    """Обработчик сигналов для корректной остановки сервера."""
    logger.warning("\n\nПолучен сигнал завершения. Останавливаем сервер...")
    cleanup_on_exit()
    sys.exit(0)


# Регистрируем обработчики сигналов
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def check_database():
    """Проверка базы данных."""
    print_header("ПРОВЕРКА БАЗЫ ДАННЫХ")

    try:
        # Проверка подключения
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print_success("Подключение к БД работает")

        # Проверка таблиц
        tables = [
            'users', 'user_profiles', 'tokens',
            'resources', 'actions', 'permissions',
            'roles', 'role_permissions', 'user_roles'
        ]

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            existing_tables = [row[0] for row in cursor.fetchall()]

        missing_tables = [t for t in tables if t not in existing_tables]
        if missing_tables:
            print_error(
                f"Отсутствуют таблицы: {', '.join(missing_tables)}"
            )
            return False
        else:
            print_success(
                f"Все таблицы существуют ({len(tables)} таблиц)"
            )

        # Проверка данных
        user_count = User.objects.count()
        resource_count = Resource.objects.count()
        action_count = Action.objects.count()
        permission_count = Permission.objects.count()
        role_count = Role.objects.count()
        user_role_count = UserRole.objects.count()

        print_info(f"Пользователей: {user_count}")
        print_info(f"Ресурсов: {resource_count}")
        print_info(f"Действий: {action_count}")
        print_info(f"Разрешений: {permission_count}")
        print_info(f"Ролей: {role_count}")
        print_info(f"Назначений ролей: {user_role_count}")

        if user_count == 0:
            print_error(
                "Нет пользователей в БД. "
                "Запустите: python manage.py init_test_data"
            )
            return False

        if role_count == 0:
            print_error(
                "Нет ролей в БД. "
                "Запустите: python manage.py init_test_data"
            )
            return False

        print_success("База данных содержит тестовые данные")
        return True

    except Exception as e:
        print_error(f"Ошибка при проверке БД: {e}")
        return False


def check_api():
    """Проверка API endpoints."""
    print_header("ПРОВЕРКА API ENDPOINTS")

    try:
        # Проверка доступности сервера
        try:
            response = requests.get(f"{BASE_URL}/api/", timeout=5)
            if response.status_code == 200:
                print_success("API сервер доступен")
            else:
                print_error(
                    f"API сервер вернул статус {response.status_code}"
                )
                return False
        except requests.exceptions.ConnectionError:
            print_error(
                "Сервер недоступен. "
                "Возможно, не удалось запустить сервер автоматически."
            )
            return False

        # Проверка эндпоинта регистрации
        test_data = {
            "email": f"test_{datetime.now().timestamp()}@test.com",
            "password": "Test123456!",
            "password_confirm": "Test123456!",
            "first_name": "Test",
            "last_name": "User"
        }

        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/register/",
                json=test_data,
                timeout=5
            )
            if response.status_code == 201:
                print_success("POST /api/auth/register/ - работает")
            else:
                print_error(
                    f"POST /api/auth/register/ вернул "
                    f"{response.status_code}: {response.text[:100]}"
                )
        except Exception as e:
            print_error(f"Ошибка при проверке регистрации: {e}")

        # Проверка эндпоинта входа (используем тестового пользователя)
        login_data = {
            "email": "user@example.com",
            "password": "user123"
        }

        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/login/",
                json=login_data,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if 'token' in data:
                    print_success("POST /api/auth/login/ - работает")
                    token = data['token']

                    # Проверка защищенного эндпоинта
                    headers = {"Authorization": f"Token {token}"}
                    response = requests.get(
                        f"{BASE_URL}/api/auth/profile/me/",
                        headers=headers,
                        timeout=5
                    )
                    if response.status_code == 200:
                        print_success(
                            "GET /api/auth/profile/me/ - работает"
                        )
                    else:
                        print_error(
                            f"GET /api/auth/profile/me/ вернул "
                            f"{response.status_code}"
                        )

                    # Проверка mock endpoints
                    response = requests.get(
                        f"{BASE_URL}/api/products/",
                        headers=headers,
                        timeout=5
                    )
                    if response.status_code in [200, 403]:
                        print_success(
                            "GET /api/products/ - работает "
                            "(200 или 403 в зависимости от прав)"
                        )
                    else:
                        print_error(
                            f"GET /api/products/ вернул "
                            f"{response.status_code}"
                        )
                else:
                    print_error("Ответ login не содержит токен")
            else:
                print_error(
                    f"POST /api/auth/login/ вернул "
                    f"{response.status_code}: {response.text[:100]}"
                )
        except Exception as e:
            print_error(f"Ошибка при проверке входа: {e}")

        return True

    except Exception as e:
        print_error(f"Ошибка при проверке API: {e}")
        return False


def check_admin():
    """Проверка админки."""
    print_header("ПРОВЕРКА АДМИНКИ")

    try:
        response = requests.get(
            f"{BASE_URL}/admin/",
            timeout=5,
            allow_redirects=False
        )
        if response.status_code in [200, 302, 301]:
            print_success("Админка доступна по адресу /admin/")
            print_info(
                "Для входа используйте суперпользователя "
                "или создайте его:"
            )
            print_info("python manage.py createsuperuser")
            return True
        else:
            print_error(
                f"Админка вернула статус {response.status_code}"
            )
            return False
    except requests.exceptions.ConnectionError:
        print_error("Сервер недоступен")
        return False
    except Exception as e:
        print_error(f"Ошибка при проверке админки: {e}")
        return False


def check_frontend():
    """Проверка фронтенда."""
    print_header("ПРОВЕРКА ФРОНТЕНДА")

    endpoints = [
        ("/", "Главная страница"),
        ("/auth/login/", "Страница входа"),
        ("/auth/register/", "Страница регистрации"),
    ]

    all_ok = True
    for endpoint, description in endpoints:
        try:
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                timeout=5
            )
            if response.status_code == 200:
                print_success(
                    f"{description} ({endpoint}) - доступна"
                )
            else:
                print_error(
                    f"{description} ({endpoint}) вернула статус "
                    f"{response.status_code}"
                )
                all_ok = False
        except requests.exceptions.ConnectionError:
            print_error("Сервер не запущен")
            return False
        except Exception as e:
            print_error(f"Ошибка при проверке {endpoint}: {e}")
            all_ok = False

    return all_ok


def main():
    """Главная функция."""
    logger.info("\n" + "=" * 60)
    logger.info("  ПРОВЕРКА РАБОТЫ ПРИЛОЖЕНИЯ")
    logger.info("=" * 60)
    logger.info(
        f"Время проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    logger.info(f"Базовый URL: {BASE_URL}")

    # Автоматический запуск сервера перед проверками
    print_header("ПОДГОТОВКА СЕРВЕРА")
    if not start_server():
        print_error(
            "Не удалось запустить сервер. "
            "Проверьте, что порт 8000 свободен и Django настроен правильно."
        )
        return 1

    results = {}
    try:
        results = {
            "База данных": check_database(),
            "API": check_api(),
            "Админка": check_admin(),
            "Фронтенд": check_frontend(),
        }
    finally:
        # Останавливаем сервер только если он был запущен скриптом
        if server_started_by_script:
            print_header("ЗАВЕРШЕНИЕ РАБОТЫ")
            stop_server()

    print_header("ИТОГОВЫЕ РЕЗУЛЬТАТЫ")

    for component, result in results.items():
        if result:
            print_success(f"{component}: OK")
        else:
            print_error(f"{component}: FAILED")

    all_passed = all(results.values())

    if all_passed:
        logger.success("\n" + "=" * 60)
        logger.success("  ✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО")
        logger.success("=" * 60)
    else:
        logger.error("\n" + "=" * 60)
        logger.error("  ❌ НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ")
        logger.error("=" * 60)
        logger.info("\nРекомендации:")
        if not results.get("База данных", False):
            logger.info("- Запустите: python manage.py init_test_data")
        api_or_admin_or_frontend = (
            not results.get("API", False)
            or not results.get("Админка", False)
            or not results.get("Фронтенд", False)
        )
        if api_or_admin_or_frontend:
            logger.info(
                "- Проверьте логи сервера выше для диагностики проблем"
            )

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
