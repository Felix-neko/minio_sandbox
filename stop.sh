#!/bin/bash
# Скрипт для остановки и очистки MinIO + Keycloak окружения

echo "🛑 Остановка MinIO + Keycloak окружения..."
echo ""

# Остановка и удаление контейнеров с volumes
docker compose down -v

echo ""
echo "✅ Окружение остановлено и очищено"
echo ""
