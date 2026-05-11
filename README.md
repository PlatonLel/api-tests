# Описание
Домашнее задание по FastAPI в рамках курса "Прикладной Python"
# API для сервиса сокращения ссылок – shortist


## Описание API

Этот сервис предоставляет REST API для:
- Аутентификации пользователей (регистрация, вход, выход)
- Создания, управления и отслеживания сокращенных ссылок
- Получения статистики по ссылкам

API разделен на две основные группы эндпоинтов:
- `/auth` - для работы с пользователями
- `/links` - для работы со ссылками

## Примеры запросов

### Аутентификация

#### Регистрация нового пользователя
```http
POST /auth/register

{
  "email": "user@example.com",
  "password": "string",
  "is_active": true,
  "is_superuser": false,
  "is_verified": false
}
```

#### Вход пользователя
```http
POST /auth/jwt/login
grant_type=password&username=username@example.com&password=password
```

#### Выход пользователя
```http
POST /auth/jwt/logout
```

### Работа со ссылками
#### Создание сокращенной ссылки
```http
POST /links/shorten

{
"original_url": "https://example.com",
"custom_alias": "my-link",
"expire_at": "2025-04-30T22:30+00:00"
}
```
#### Получение оригинальной ссылки (редирект)
```http
GET /links/{short_id}
```

#### Получение статистики по ссылке
```http
GET /links/{short_id}/stats
```

#### Обновление ссылки
```http
PUT /links/{short_id}

{
"original_url": "https://new-example.com",
"expire_at": "2025-05-30T22:30+00:00"
}
```


#### Удаление ссылки
```http
DELETE /links/{short_id}
```

#### Поиск ссылок
```http
GET /links/search/?original_url=http://example.com
```


### Инструкция по запуску

- Создайте и наполните .env файл под вашу конфигурацию
- Запустите сборку контейнеров: `docker-compose up -d --build`
- Выполните миграцию с инициализацией БД по схеме проекта: `docker-compose exec web alembic upgrade head`

Сервис готов к использованию 🎉

## Тестирование

Тесты лежат в папке `tests/`. Для них используется отдельная временная SQLite-база, поэтому реальная PostgreSQL-база не затрагивается.

Запустить тесты:

```bash
pytest tests
```

Проверить покрытие:

```bash
coverage run -m pytest tests
coverage report -m
```

Сгенерировать HTML-отчет:

```bash
coverage html
```

Отчет будет в `htmlcov/index.html`.

## Нагрузочное тестирование

Сценарий для Locust находится в `locustfile.py`: пользователи создают короткие ссылки и иногда переходят по ним.

Запустить Locust:

```bash
locust -f locustfile.py
```