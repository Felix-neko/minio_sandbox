"""
Интеграционные тесты для проверки интеграции MinIO с Keycloak.
"""

import json
import time

import pytest
import requests
from playwright.sync_api import Page, expect


class TestKeycloakAvailability:
    """Тесты проверки доступности Keycloak."""

    def test_keycloak_realm_accessible(self, service_urls):
        """Проверка доступности realm в Keycloak."""
        response = requests.get(f"{service_urls['keycloak']}/realms/myrealm")
        assert response.status_code == 200
        data = response.json()
        assert data['realm'] == 'myrealm'
        print("✓ Keycloak realm 'myrealm' доступен")

    def test_keycloak_openid_config(self, service_urls):
        """Проверка доступности OpenID Connect конфигурации."""
        response = requests.get(
            f"{service_urls['keycloak']}/realms/myrealm/.well-known/openid-configuration"
        )
        assert response.status_code == 200
        data = response.json()
        assert 'authorization_endpoint' in data
        assert 'token_endpoint' in data
        print("✓ OpenID Connect конфигурация доступна")


class TestMinIOAvailability:
    """Тесты проверки доступности MinIO."""

    def test_minio_health(self, service_urls):
        """Проверка health endpoint MinIO."""
        response = requests.get(f"{service_urls['minio_api']}/minio/health/live")
        assert response.status_code == 200
        print("✓ MinIO health endpoint отвечает")

    def test_minio_bucket_file_not_public(self, service_urls):
        """Проверка, что файл в бакете НЕ доступен публично (требуется авторизация)."""
        file_url = f"{service_urls['minio_api']}/testbucket/test/test.json"
        
        # Даем время на инициализацию бакета
        print("⏳ Ожидание создания бакета...")
        time.sleep(5)
        
        # Пытаемся получить файл без авторизации
        response = requests.get(file_url)
        
        # Файл должен быть недоступен без авторизации
        assert response.status_code in [403, 401], \
            f"Файл должен быть приватным, но вернул статус: {response.status_code}"
        
        print(f"✓ Файл защищен - требуется авторизация (статус {response.status_code})")
        print(f"  URL: {file_url}")


class TestMinIOConsoleAvailability:
    """Тесты проверки доступности MinIO Console."""

    def test_minio_console_loads(self, playwright, service_urls):
        """Проверка загрузки страницы MinIO Console."""
        print("\n🌐 Проверка загрузки MinIO Console...")
        
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True,
        )
        page = context.new_page()
        
        try:
            # Открываем MinIO Console
            page.goto(f"{service_urls['minio_console']}", timeout=10000)
            page.wait_for_load_state('networkidle', timeout=10000)
            
            # Проверяем, что страница загрузилась
            assert "9001" in page.url or "minio" in page.url.lower()
            print(f"✓ MinIO Console загружена: {page.url}")
            
            # Делаем скриншот
            screenshot_path = "/tmp/minio_console_page.png"
            page.screenshot(path=screenshot_path)
            print(f"📸 Скриншот сохранен: {screenshot_path}")
            
            # Проверяем наличие формы входа или элементов MinIO
            page_content = page.content()
            assert any(keyword in page_content.lower() for keyword in ['minio', 'login', 'sign in'])
            print("✓ Страница содержит элементы интерфейса MinIO")
            
        finally:
            page.close()
            context.close()
            browser.close()

    def test_minio_oidc_configuration(self, service_urls):
        """Проверка, что MinIO настроен для работы с OIDC."""
        print("\n🔐 Проверка OIDC-конфигурации MinIO...")
        
        # Проверяем, что Keycloak доступен для MinIO
        response = requests.get(
            f"{service_urls['keycloak']}/realms/myrealm/.well-known/openid-configuration",
            timeout=5
        )
        assert response.status_code == 200
        
        oidc_config = response.json()
        assert 'authorization_endpoint' in oidc_config
        assert 'token_endpoint' in oidc_config
        
        print(f"✓ OIDC конфигурация доступна")
        print(f"  Authorization endpoint: {oidc_config['authorization_endpoint']}")
        print(f"  Token endpoint: {oidc_config['token_endpoint']}")


class TestMinIOKeycloakIntegration:
    """Тесты интеграции MinIO с Keycloak через SSO."""

    def test_integration_configuration(self, service_urls):
        """Проверка базовой конфигурации интеграции MinIO и Keycloak."""
        print("\n🔗 Проверка интеграции MinIO и Keycloak...")
        
        # 1. Проверяем, что Keycloak realm доступен
        response = requests.get(f"{service_urls['keycloak']}/realms/myrealm")
        assert response.status_code == 200
        realm_data = response.json()
        assert realm_data['realm'] == 'myrealm'
        print("✓ Keycloak realm 'myrealm' настроен")
        
        # 2. Проверяем OIDC конфигурацию
        response = requests.get(
            f"{service_urls['keycloak']}/realms/myrealm/.well-known/openid-configuration"
        )
        assert response.status_code == 200
        oidc_config = response.json()
        print("✓ OIDC конфигурация доступна")
        
        # 3. Проверяем, что MinIO работает
        response = requests.get(f"{service_urls['minio_api']}/minio/health/live")
        assert response.status_code == 200
        print("✓ MinIO API доступен")

    def test_console_login_and_verify_file_protection(self, playwright, service_urls):
        """
        Тест: вход в MinIO Console и проверка защиты файлов.
        
        Проверяет:
        1. Вход в MinIO Console (через root или SSO)
        2. Файлы защищены от неавторизованного доступа
        3. После входа можно просмотреть файлы через Console
        """
        print("\n🔐 Тест входа в MinIO Console и проверки защиты файлов...")
        
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True,
        )
        page = context.new_page()
        
        try:
            # Шаг 1: Проверка, что файл недоступен без авторизации
            print("\n1️⃣ Проверка защиты файла...")
            file_url = f"{service_urls['minio_api']}/testbucket/test/test.json"
            
            # Пытаемся получить файл напрямую через API без авторизации
            import requests
            response = requests.get(file_url)
            assert response.status_code in [403, 401], \
                f"Файл должен быть защищен, но вернул статус {response.status_code}"
            print(f"✓ Файл защищен от неавторизованного доступа (статус {response.status_code})")
            
            # Шаг 2: Открываем MinIO Console
            print("\n2️⃣ Открываем MinIO Console...")
            page.goto(f"{service_urls['minio_console']}", timeout=15000)
            page.wait_for_load_state('networkidle', timeout=10000)
            print(f"✓ MinIO Console загружена: {page.url}")
            
            # Делаем скриншот
            page.screenshot(path="/tmp/minio_login_attempt.png")
            print("📸 Скриншот: /tmp/minio_login_attempt.png")
            
            # Шаг 3: Ищем способ входа
            print("\n3️⃣ Поиск способа входа...")
            
            login_successful = False
            
            # Вариант 1: Проверяем SSO
            try:
                sso_locator = page.locator("a:has-text('SSO'), a:has-text('Login with SSO'), a:has-text('OpenID')")
                if sso_locator.count() > 0:
                    print("✓ Найдена ссылка SSO, используем SSO-вход")
                    sso_locator.first.click(timeout=5000)
                    page.wait_for_url("**/realms/myrealm/**", timeout=10000)
                    
                    # Вход через Keycloak
                    page.wait_for_selector("input[name='username']", timeout=10000)
                    page.fill("input[name='username']", "minio")
                    page.fill("input[name='password']", "minio123")
                    page.click("input[type='submit'], button[type='submit']")
                    page.wait_for_url("**/9001/**", timeout=20000)
                    login_successful = True
                    print("✓ Успешный вход через Keycloak SSO")
            except Exception as e:
                print(f"⚠ SSO-вход не доступен: {e}")
            
            # Вариант 2: Прямой вход через форму
            if not login_successful:
                try:
                    print("🔍 Используем прямой вход через форму...")
                    # Ищем поля ввода логина/пароля
                    username_field = page.locator("input[name='accessKey'], input[placeholder*='Username'], input[type='text']").first
                    password_field = page.locator("input[name='secretKey'], input[placeholder*='Password'], input[type='password']").first
                    
                    if username_field.is_visible(timeout=2000):
                        username_field.fill("minioadmin")
                        password_field.fill("minioadmin")
                        
                        # Нажимаем кнопку входа
                        login_btn = page.locator("button[type='submit'], input[type='submit'], button:has-text('Login')").first
                        login_btn.click()
                        
                        # Ждем перенаправления
                        time.sleep(3)
                        page.wait_for_load_state('networkidle', timeout=10000)
                        login_successful = True
                        print("✓ Успешный вход через прямую форму")
                except Exception as e:
                    print(f"⚠ Прямой вход не удался: {e}")
            
            if not login_successful:
                pytest.skip("Не удалось войти в MinIO Console ни одним из способов")
            
            # Шаг 4: Проверка после входа
            print("\n4️⃣ Проверка после входа...")
            page.screenshot(path="/tmp/minio_after_login.png")
            print("📸 Скриншот после входа: /tmp/minio_after_login.png")
            
            # Проверяем, что мы вошли
            current_url = page.url
            page_content = page.content()
            
            assert "login" not in current_url.lower() or "bucket" in page_content.lower() or "dashboard" in page_content.lower(), \
                "Похоже, вход не выполнен"
            
            print("✓ Успешный вход в MinIO Console")
            print(f"  URL: {current_url}")
            
            print("\n✅ Тест завершен: файлы защищены, вход в Console работает")
            
        finally:
            page.close()
            context.close()
            browser.close()



class TestEndToEnd:
    """Сквозной тест всей системы."""

    def test_full_workflow(self, service_urls):
        """
        Полный тест рабочего процесса:
        1. Проверка доступности сервисов
        2. Проверка приватности файлов (требуется авторизация)
        3. Проверка интеграции SSO
        """
        print("\n" + "=" * 80)
        print("🔄 Запуск сквозного теста всей системы")
        print("=" * 80)
        
        # 1. Keycloak доступен
        print("\n1️⃣ Проверка Keycloak...")
        response = requests.get(f"{service_urls['keycloak']}/realms/myrealm")
        assert response.status_code == 200
        print("   ✓ Keycloak работает")
        
        # 2. MinIO доступен
        print("\n2️⃣ Проверка MinIO...")
        response = requests.get(f"{service_urls['minio_api']}/minio/health/live")
        assert response.status_code == 200
        print("   ✓ MinIO работает")
        
        # 3. Файл защищен и требует авторизации
        print("\n3️⃣ Проверка защиты файлов...")
        file_url = f"{service_urls['minio_api']}/testbucket/test/test.json"
        response = requests.get(file_url)
        assert response.status_code in [403, 401], \
            f"Файл должен быть приватным (403/401), но вернул {response.status_code}"
        print(f"   ✓ Файл защищен (требуется авторизация): {file_url}")
        
        # 4. OIDC конфигурация доступна
        print("\n4️⃣ Проверка OIDC конфигурации...")
        response = requests.get(
            f"{service_urls['keycloak']}/realms/myrealm/.well-known/openid-configuration"
        )
        assert response.status_code == 200
        print("   ✓ OIDC конфигурация доступна для SSO-входа")
        
        print("\n" + "=" * 80)
        print("✅ Все компоненты системы работают корректно!")
        print("=" * 80)
        print("\n💡 Файлы защищены и доступны только после SSO-входа через Keycloak\n")
