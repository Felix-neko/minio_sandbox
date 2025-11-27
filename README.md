# MinIO + Keycloak Integration Demo

Учебный проект для демонстрации интеграции объектного хранилища MinIO с системой единой аутентификации Keycloak.

## Описание

Проект демонстрирует:
- Настройку SSO (Single Sign-On) для MinIO через Keycloak
- Автоматический импорт конфигурации Keycloak из realm-export.json
- Создание тестового бакета и файлов в MinIO
- Публичный доступ к файлам через HTTP

## Требования

- Docker и Docker Compose
- Python 3.12+
- uv (для управления зависимостями Python)

## Установка

1. Создать виртуальное окружение:
```bash
uv venv --python 3.12
source .venv/bin/activate
```

2. Установить зависимости:
```bash
uv pip install -e .
```

3. Установить браузеры для Playwright:
```bash
playwright install chromium
```

## Запуск

### Быстрый запуск
```bash
./start.sh
```

Скрипт автоматически:
- Соберет Docker-образы
- Запустит все сервисы
- Дождется их готовности
- Создаст тестовый бакет с файлом
- Выведет информацию о доступе

### Ручной запуск
```bash
docker compose build
docker compose up -d
```

Дождитесь готовности сервисов (около 60 секунд).

### Доступ к сервисам
- **MinIO Console:** http://localhost:9001
- **MinIO API:** http://localhost:9000
- **Keycloak Admin:** http://localhost:8080

## Учетные данные

### Keycloak Admin
- URL: http://localhost:8080
- Username: `admin`
- Password: `admin`

### MinIO Root
- Username: `minioadmin`
- Password: `minioadmin`

### MinIO SSO User (через Keycloak)
- Username: `minio`
- Password: `minio123`

## Тестирование

Запуск автотестов:
```bash
pytest tests/
```

Тесты проверяют:
- Запуск и готовность Keycloak
- Запуск и готовность MinIO
- OIDC-интеграцию между MinIO и Keycloak
- Защиту файлов (приватный доступ - требуется авторизация)
- Вход в MinIO Console (поддержка root-входа и SSO)
- Доступ к файлам после авторизации

## Остановка

### Быстрая остановка
```bash
./stop.sh
```

### Ручная остановка
Остановить и удалить все данные:
```bash
docker compose down -v
```

**Примечание:** Флаг `-v` удаляет все volumes, включая данные Keycloak и MinIO.

## Структура проекта

```
.
├── docker-compose.yaml      # Конфигурация Docker-сервисов (Keycloak, MinIO, minio-init)
├── realm-export.json        # Конфигурация Keycloak realm с пользователями и клиентами
├── pyproject.toml          # Зависимости Python (uv)
├── start.sh                # Скрипт быстрого запуска окружения
├── stop.sh                 # Скрипт остановки и очистки окружения
├── .gitignore              # Исключения для Git
├── tests/                  # Автотесты на Playwright + pytest
│   ├── conftest.py        # Фикстуры pytest (управление Docker Compose)
│   └── test_integration.py # Интеграционные тесты (8 тестов)
└── README.md              # Документация проекта
```

## Технологии

- **MinIO** - S3-совместимое объектное хранилище
- **Keycloak** - Сервер SSO и управления идентификацией
- **Playwright** - Фреймворк для E2E-тестирования
- **pytest** - Фреймворк для тестирования Python
- **uv** - Быстрый менеджер пакетов Python
