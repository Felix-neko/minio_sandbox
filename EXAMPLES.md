# Примеры использования MinIO + Keycloak

## Быстрый старт

### 1. Запуск окружения
```bash
./start.sh
```

Подождите, пока все сервисы запустятся (~60 секунд).

### 2. Проверка доступности файлов

Тестовый файл доступен публично:
```bash
curl http://localhost:9000/testbucket/test/test.json
```

Ожидаемый результат:
```json
{"message": "Hello from MinIO!", "timestamp": "2024-01-01T00:00:00Z"}
```

### 3. Вход в MinIO Console

Откройте в браузере: http://localhost:9001

**Вариант 1: Root-пользователь**
- Логин: `minioadmin`
- Пароль: `minioadmin`

**Вариант 2: SSO через Keycloak**
- Используйте кнопку SSO (если доступна)
- Логин: `minio`
- Пароль: `minio123`

### 4. Вход в Keycloak Admin Console

Откройте: http://localhost:8080

- Логин: `admin`
- Пароль: `admin`

## Работа с MinIO через CLI

### Установка MinIO Client (mc)
```bash
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv mc /usr/local/bin/
```

### Настройка alias
```bash
mc alias set local http://localhost:9000 minioadmin minioadmin
```

### Список бакетов
```bash
mc ls local
```

### Загрузка файла
```bash
echo "Test content" > test.txt
mc cp test.txt local/testbucket/
```

### Публичный доступ к бакету
```bash
mc anonymous set download local/testbucket
```

## Работа с Keycloak через API

### Получение токена для пользователя 'minio'

```bash
curl -X POST http://localhost:8080/realms/myrealm/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=account" \
  -d "client_secret=minio-client-secret-12345" \
  -d "username=minio" \
  -d "password=minio123" \
  -d "grant_type=password" | jq
```

Ответ содержит:
- `access_token` - JWT-токен для доступа к MinIO
- `refresh_token` - токен для обновления
- `expires_in` - время жизни токена

## Тестирование

### Запуск всех тестов
```bash
source .venv/bin/activate
pytest tests/ -v
```

### Запуск конкретного теста
```bash
pytest tests/test_integration.py::TestKeycloakAvailability -v
```

### Запуск с подробным выводом
```bash
pytest tests/ -v -s
```

## Проверка интеграции

### 1. Проверка OIDC-конфигурации
```bash
curl http://localhost:8080/realms/myrealm/.well-known/openid-configuration | jq
```

### 2. Проверка realm Keycloak
```bash
curl http://localhost:8080/realms/myrealm | jq
```

### 3. Проверка здоровья MinIO
```bash
curl http://localhost:9000/minio/health/live
```

## Остановка окружения

```bash
./stop.sh
```

Это остановит все контейнеры и удалит все данные (volumes).

## Полезные команды Docker Compose

### Просмотр логов всех сервисов
```bash
docker compose logs -f
```

### Просмотр логов конкретного сервиса
```bash
docker compose logs -f keycloak
docker compose logs -f minio
docker compose logs -f minio-init
```

### Перезапуск сервиса
```bash
docker compose restart minio
```

### Проверка статуса
```bash
docker compose ps
```

## Решение проблем

### Keycloak не импортирует realm

Проверьте логи:
```bash
docker compose logs keycloak | grep -i import
```

Должно быть сообщение: `Realm 'myrealm' imported`

### MinIO не может подключиться к Keycloak

Проверьте логи MinIO:
```bash
docker compose logs minio | grep -i openid
```

Убедитесь, что Keycloak запустился раньше MinIO.

### Порты заняты

Если порты 8080, 9000 или 9001 заняты другими процессами:

1. Остановите конфликтующие процессы
2. Или измените порты в `docker-compose.yaml`

### Очистка всего окружения

```bash
docker compose down -v
docker system prune -f
```

## Дополнительно

### Экспорт realm из Keycloak

```bash
docker exec keycloak /opt/keycloak/bin/kc.sh export \
  --file /tmp/realm-export-new.json \
  --realm myrealm
  
docker cp keycloak:/tmp/realm-export-new.json ./realm-export-new.json
```

### Создание нового пользователя в Keycloak

Через Admin Console:
1. Откройте http://localhost:8080
2. Войдите как admin
3. Выберите realm 'myrealm'
4. Users → Add user
5. Заполните данные и сохраните
6. Вкладка Credentials → установите пароль
7. Вкладка Role Mappings → назначьте роли

### Изменение времени жизни токена

В `realm-export.json` найдите клиент `account` и измените:
```json
"attributes": {
  "access.token.lifespan": "3600"
}
```

Затем перезапустите окружение:
```bash
./stop.sh
./start.sh
```
