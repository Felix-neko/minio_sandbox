# ✅ MinIO-Keycloak OIDC Integration - SUCCESS

**Дата**: 27 ноября 2025  
**Статус**: ✅ Полностью работает

## 🎯 Достигнутый результат

MinIO Console успешно интегрирован с Keycloak 26.4 через OpenID Connect (OIDC):

- ✅ Кнопка "Login with Keycloak SSO" появляется на странице логина MinIO
- ✅ Редирект на Keycloak для аутентификации работает корректно
- ✅ После логина пользователь возвращается в MinIO Console с правами доступа
- ✅ Бакеты и объекты доступны согласно policy из JWT-токена

## 🔧 Финальная конфигурация

### MinIO
- **Версия**: `minio/minio:RELEASE.2024-11-07T00-52-20Z`
- **Настройка OIDC**: через `mc admin config` (не через environment variables)
- **Параметры**:
  ```bash
  enable=on
  config_url=http://keycloak:8080/realms/myrealm/.well-known/openid-configuration
  client_id=account
  client_secret=minio-client-secret-12345
  scopes=openid,profile,email
  claim_name=policy
  display_name='Login with Keycloak SSO'
  redirect_uri_dynamic=on
  ```

### Keycloak
- **Версия**: `quay.io/keycloak/keycloak:26.4`
- **Environment variables**:
  ```yaml
  KC_HOSTNAME_URL: http://localhost:8080
  KC_HOSTNAME_ADMIN_URL: http://localhost:8080
  KC_HOSTNAME_STRICT: "false"
  KC_HOSTNAME_STRICT_BACKCHANNEL: "false"
  ```
- **Command**:
  ```yaml
  - start-dev
  - --hostname=http://localhost:8080
  - --hostname-backchannel-dynamic=true
  - --import-realm
  ```

### Realm Configuration
- **Client ID**: `account`
- **Client Secret**: `minio-client-secret-12345`
- **Client Type**: Confidential (не public)
- **Protocol Mapper**: `oidc-hardcoded-claim-mapper`
  - Claim name: `policy`
  - Claim value: `readwrite`
  - Включён в: access token, id token, userinfo

### Тестовый пользователь
- **Username**: `minio`
- **Password**: `minio123`
- **Email**: `minio@example.com`
- **Policy**: `readwrite` (через hardcoded claim mapper)

## 🔍 Ключевые проблемы и решения

### Проблема 1: Кнопка SSO не появлялась
**Причина**: MinIO `latest` (версия из будущего 2025-09-07) имела баги  
**Решение**: Использовать стабильную версию `RELEASE.2024-11-07T00-52-20Z`

### Проблема 2: Environment variables не работали
**Причина**: MinIO требует перезапуска после изменения OIDC через env vars  
**Решение**: Настройка через `mc admin config set` в init-контейнере

### Проблема 3: Keycloak возвращал внутренние URL
**Причина**: Неправильная конфигурация hostname в Keycloak 26.x  
**Решение**: Использовать `KC_HOSTNAME_URL` + `--hostname` в command

### Проблема 4: Policy mapper не работал
**Причина**: Использовался `oidc-usermodel-attribute-mapper` вместо hardcoded  
**Решение**: Изменить на `oidc-hardcoded-claim-mapper` с явным значением `readwrite`

## 📋 Инструкция по запуску

1. **Запуск системы**:
   ```bash
   cd /home/felix/Projects/yandex_swa_pro/minio_sandbox
   docker compose down -v
   docker compose up -d
   ```

2. **Ожидание готовности** (около 50 секунд):
   - Keycloak импортирует realm
   - MinIO запускается
   - minio-init настраивает OIDC и создаёт бакет

3. **Перезапуск MinIO** (для применения OIDC):
   ```bash
   docker compose restart minio
   ```

4. **Проверка**:
   - Открыть http://localhost:9001
   - Должна появиться кнопка "Login with Keycloak SSO"
   - Нажать на кнопку
   - Залогиниться: `minio` / `minio123`
   - Заполнить First name и Last name
   - Попасть в MinIO Console с доступом к бакету `testbucket`

## 🧪 Проверка работоспособности

```bash
# Проверка API login endpoint
curl -s http://localhost:9001/api/v1/login | jq .

# Должен вернуть:
# {
#   "animatedLogin": true,
#   "loginStrategy": "redirect",
#   "redirectRules": [
#     {
#       "displayName": "Login with Keycloak SSO",
#       "redirect": "http://localhost:8080/realms/myrealm/protocol/openid-connect/auth?..."
#     }
#   ]
# }
```

## 📊 Архитектура решения

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Browser   │────────▶│ MinIO Console│────────▶│  Keycloak   │
│             │         │  :9001       │         │   :8080     │
└─────────────┘         └──────────────┘         └─────────────┘
      │                        │                        │
      │  1. Click SSO          │                        │
      │─────────────────────▶  │                        │
      │                        │  2. Redirect to KC     │
      │                        │───────────────────────▶│
      │  3. Login form         │                        │
      │◀──────────────────────────────────────────────  │
      │  4. Submit credentials │                        │
      │───────────────────────────────────────────────▶ │
      │                        │  5. Auth code          │
      │                        │◀────────────────────── │
      │  6. Redirect + code    │                        │
      │◀───────────────────────│                        │
      │  7. Exchange code      │                        │
      │                        │───────────────────────▶│
      │                        │  8. Access token       │
      │                        │◀────────────────────── │
      │  9. MinIO Console      │                        │
      │◀───────────────────────│                        │
```

## 🔐 Безопасность

- ✅ Client secret используется для confidential client
- ✅ Authorization Code Flow (не implicit)
- ✅ HTTPS не используется (только для dev-окружения!)
- ⚠️ **Для продакшена**: обязательно использовать HTTPS и настроить сертификаты

## 📝 Дополнительные заметки

1. **Версия MinIO**: Критически важно использовать стабильную версию, а не `latest`
2. **Настройка OIDC**: `mc admin config` более надёжен чем environment variables
3. **Keycloak 26.x**: Требует явного указания `KC_HOSTNAME_URL` для корректной работы OIDC
4. **Policy mapper**: Hardcoded mapper проще для тестирования, для продакшена использовать user attributes
5. **Backchannel**: `--hostname-backchannel-dynamic=true` позволяет MinIO обращаться к Keycloak по внутреннему имени

## 🎓 Извлечённые уроки

1. **Версионирование важно**: `latest` может содержать нестабильный код
2. **Документация Keycloak 26.x**: Изменилась по сравнению с предыдущими версиями
3. **MinIO OIDC**: Требует точной настройки всех параметров
4. **Docker networking**: Важно понимать разницу между внутренними и внешними URL
5. **Debugging**: Проверка API endpoints помогает быстрее найти проблему

---

**Автор**: Cascade AI Assistant  
**Проект**: minio_sandbox  
**Репозиторий**: Felix-neko/minio_sandbox
