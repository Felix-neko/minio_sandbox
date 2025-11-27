#!/bin/bash
# Скрипт для запуска MinIO + Keycloak окружения

set -e

echo "🚀 Запуск MinIO + Keycloak окружения..."
echo ""

# Сборка образов
echo "🔨 Сборка Docker-образов..."
docker compose build

echo ""
echo "🌟 Запуск сервисов..."
docker compose up -d

echo ""
echo "⏳ Ожидание готовности сервисов..."

# Функция для проверки доступности сервиса
wait_for_service() {
  local url=$1
  local name=$2
  local max_attempts=60
  local attempt=1
  
  while [ $attempt -le $max_attempts ]; do
    if curl -s -f "$url" > /dev/null 2>&1; then
      echo "✓ $name готов (попытка $attempt/$max_attempts)"
      return 0
    fi
    echo "⏳ Ожидание $name... (попытка $attempt/$max_attempts)"
    sleep 2
    attempt=$((attempt + 1))
  done
  
  echo "✗ $name не запустился за $((max_attempts * 2)) секунд"
  return 1
}

# Ожидание Keycloak
wait_for_service "http://localhost:8080/realms/myrealm" "Keycloak"

# Ожидание MinIO
wait_for_service "http://localhost:9000/minio/health/live" "MinIO"

# Дополнительное время для инициализации
echo ""
echo "⏳ Ожидание инициализации бакета (10 секунд)..."
sleep 10

echo ""
echo "=" | awk '{for(i=1;i<=80;i++)printf "="; print ""}'
echo "✅ Все сервисы запущены и готовы к работе!"
echo "=" | awk '{for(i=1;i<=80;i++)printf "="; print ""}'
echo ""
echo "🔗 Доступные сервисы:"
echo "   • Keycloak Admin:  http://localhost:8080 (admin / admin)"
echo "   • MinIO Console:   http://localhost:9001"
echo "   • MinIO API:       http://localhost:9000"
echo ""
echo "👤 Учетные данные для MinIO через Keycloak:"
echo "   • Логин:  minio"
echo "   • Пароль: minio123"
echo ""
echo "=" | awk '{for(i=1;i<=80;i++)printf "="; print ""}'
echo ""
echo "💡 Полезные команды:"
echo "   • Просмотр логов:    docker compose logs -f"
echo "   • Остановка:         ./stop.sh  или  docker compose down -v"
echo "   • Запуск тестов:     pytest tests/ -v"
echo ""
