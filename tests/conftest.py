"""
Фикстуры для pytest.
Управляет жизненным циклом Docker Compose окружения для тестов.
"""

import subprocess
import time
from pathlib import Path

import pytest
import requests


@pytest.fixture(scope="session", autouse=True)
def docker_compose_environment():
    """
    Фикстура для управления Docker Compose окружением.
    Запускается один раз перед всеми тестами и останавливается после них.
    """
    project_root = Path(__file__).parent.parent
    compose_file = project_root / "docker-compose.yaml"

    print("\n" + "=" * 80)
    print("🔧 Остановка и очистка старого окружения...")
    print("=" * 80)
    
    # Останавливаем и удаляем старые контейнеры и volumes
    subprocess.run(
        ["docker", "compose", "down", "-v"],
        cwd=project_root,
        capture_output=True,
    )
    
    print("\n" + "=" * 80)
    print("🔨 Сборка образов Docker Compose...")
    print("=" * 80)
    
    # Собираем образы
    result = subprocess.run(
        ["docker", "compose", "build"],
        cwd=project_root,
        capture_output=False,  # Показываем вывод
    )
    
    if result.returncode != 0:
        pytest.fail("❌ Не удалось собрать Docker Compose образы")
    
    print("\n" + "=" * 80)
    print("🚀 Запуск Docker Compose окружения...")
    print("=" * 80)
    
    # Запускаем окружение
    result = subprocess.run(
        ["docker", "compose", "up", "-d"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        print(f"❌ Ошибка запуска: {result.stderr}")
        pytest.fail("Не удалось запустить Docker Compose")
    
    print("✅ Docker Compose запущен")
    
    # Ожидаем готовности Keycloak
    print("\n⏳ Ожидание готовности Keycloak...")
    keycloak_ready = wait_for_service(
        url="http://localhost:8080/realms/myrealm",
        service_name="Keycloak",
        max_attempts=60,  # 2 минуты (60 * 2 секунды)
        interval=2,
    )
    
    if not keycloak_ready:
        # Показываем логи при ошибке
        logs_result = subprocess.run(
            ["docker", "compose", "logs", "keycloak"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        print(f"\n📋 Логи Keycloak:\n{logs_result.stdout}")
        pytest.fail("❌ Keycloak не запустился за отведенное время")
    
    # Ожидаем готовности MinIO
    print("\n⏳ Ожидание готовности MinIO...")
    minio_ready = wait_for_service(
        url="http://localhost:9000/minio/health/live",
        service_name="MinIO",
        max_attempts=30,  # 1 минута
        interval=2,
    )
    
    if not minio_ready:
        logs_result = subprocess.run(
            ["docker", "compose", "logs", "minio"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        print(f"\n📋 Логи MinIO:\n{logs_result.stdout}")
        pytest.fail("❌ MinIO не запустился за отведенное время")
    
    # Даем дополнительное время для инициализации MinIO
    print("\n⏳ Ожидание инициализации MinIO (создание бакета)...")
    time.sleep(10)
    
    print("\n" + "=" * 80)
    print("✅ Все сервисы готовы к работе!")
    print("=" * 80)
    print("🔗 Keycloak: http://localhost:8080")
    print("🔗 MinIO Console: http://localhost:9001")
    print("🔗 MinIO API: http://localhost:9000")
    print("=" * 80 + "\n")
    
    # Передаем управление тестам
    yield
    
    # После всех тестов останавливаем окружение
    print("\n" + "=" * 80)
    print("🛑 Остановка Docker Compose окружения...")
    print("=" * 80)
    
    subprocess.run(
        ["docker", "compose", "down", "-v"],
        cwd=project_root,
        capture_output=True,
    )
    
    print("✅ Окружение остановлено и очищено\n")


def wait_for_service(url: str, service_name: str, max_attempts: int = 30, interval: int = 2) -> bool:
    """
    Ожидает готовности сервиса, проверяя доступность URL.
    
    Args:
        url: URL для проверки доступности
        service_name: Имя сервиса (для вывода в логи)
        max_attempts: Максимальное количество попыток
        interval: Интервал между попытками в секундах
    
    Returns:
        True если сервис готов, False если превышено время ожидания
    """
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code < 500:  # Любой код < 500 означает, что сервис отвечает
                print(f"✓ {service_name} начал отвечать (попытка {attempt}/{max_attempts})")
                # Дополнительная пауза для стабилизации
                time.sleep(3)
                print(f"✓ {service_name} готов к работе")
                return True
        except (requests.exceptions.RequestException, Exception):
            pass  # Игнорируем ошибки и продолжаем ждать
        
        print(f"⏳ Ожидание {service_name}... (попытка {attempt}/{max_attempts})")
        time.sleep(interval)
    
    print(f"✗ {service_name} не запустился за {max_attempts * interval} секунд")
    return False


@pytest.fixture(scope="session")
def service_urls():
    """URL сервисов для тестов."""
    return {
        'keycloak': 'http://localhost:8080',
        'minio_console': 'http://localhost:9001',
        'minio_api': 'http://localhost:9000',
    }
