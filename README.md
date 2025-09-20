# Foodgram

Foodgram — сервис для публикации и обмена рецептами. Пользователи могут регистрироваться, создавать и редактировать собственные блюда, добавлять чужие рецепты в избранное и формировать список покупок. Проект состоит из Django backend, React frontend и инфраструктуры на Docker Compose.

## Возможности
- регистрация и аутентификация по токену
- управление профилем пользователя и аватаром
- создание, редактирование и удаление рецептов с ингредиентами
- добавление рецептов в избранное и загрузка списка покупок
- подписки на авторов и получение их рецептов в ленте
- короткие ссылки на рецепты и документация API по адресу `/api/docs/`

## Технологии
- Python 3.11, Django 4.2, Django REST Framework, PostgreSQL 13
- Gunicorn, Nginx, Docker, Docker Compose
- React (frontend-сборка подключается через Nginx)
- Токенная аутентификация DRF

## Структура репозитория
- `backend/` — исходный код Django-приложения и Dockerfile
- `frontend/` — исходники и сборка клиентской части
- `infra/` — `docker-compose.yml`, конфигурация Nginx и пример `.env`
- `data/` — вспомогательные файлы для загрузки данных
- `docs/` — спецификации и документация
- `postman_collection/` — коллекция запросов для тестирования API

## Требования
- Docker 20.10+
- Docker Compose plugin 2.0+ (`docker compose`)
- Порт 80 на хосте должен быть свободен

## Переменные окружения
Файл `infra/.env` используется как источник переменных для всех контейнеров.

| Переменная | Назначение | Значение по умолчанию |
|-----------|------------|-----------------------|
| `POSTGRES_DB` | имя БД PostgreSQL | `foodgram` |
| `POSTGRES_USER` | пользователь БД | `foodgram` |
| `POSTGRES_PASSWORD` | пароль пользователя БД | `foodgram` |
| `POSTGRES_HOST` | адрес БД для Django | `db` |
| `POSTGRES_PORT` | порт БД | `5432` |
| `DJANGO_SECRET_KEY` | секретный ключ Django | `change_me` |
| `DJANGO_DEBUG` | режим отладки (`True`/`False`) | `False` |
| `ALLOWED_HOSTS` | список хостов (через запятую) | `*` |
| `SITE_URL` | базовый URL для генерации ссылок | `http://localhost` |

Отредактируйте значения под свою среду перед запуском.

## Запуск в Docker
1. Клонируйте репозиторий и перейдите в директорию проекта.
2. Проверьте настройки в `infra/.env`.
3. Соберите и поднимите контейнеры:
   ```bash
   cd infra
   docker compose up -d --build
   ```
4. После успешного старта приложения доступны (после запуска контейнеров страницы становятся активными):
   - веб-интерфейс: http://localhost/
   - документация API: http://localhost/api/docs/

### Первичная настройка
```bash
# применить миграции (запускается автоматически, но можно повторить при необходимости)
docker compose exec backend python manage.py migrate

# создать суперпользователя
docker compose exec backend python manage.py createsuperuser

# загрузить демонстрационные данные
docker compose exec backend python manage.py create_demo

# Загрузить ингридиенты
docker compose exec backend python manage.py import_ingredients --dir /app/data   
```

Для остановки контейнеров используйте `docker compose down`. Статические и медиаданные сохраняются в именованных volume, поэтому не теряются между перезапусками.

## Документация и примеры API
Документация в формате ReDoc доступна по адресу `/api/docs/` только после развёртывания проекта. Ниже приведено несколько примеров запросов и ответов для общего представления о формате API.

### Получить список рецептов
**Запрос**
```http
GET /api/recipes/
```

**Ответ**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Тыквенный суп",
      "image": "http://localhost/media/recipes/pumpkin_soup.jpg",
      "text": "Пюрировать запечённую тыкву с овощами.",
      "cooking_time": 30,
      "author": {
        "email": "chef@example.com",
        "id": 5,
        "username": "chef",
        "first_name": "Анна",
        "last_name": "Иванова",
        "is_subscribed": true,
        "avatar": "http://localhost/media/users/chef.png"
      },
      "ingredients": [
        {
          "id": 3,
          "name": "Тыква",
          "measurement_unit": "г",
          "amount": 500
        },
        {
          "id": 7,
          "name": "Сливки",
          "measurement_unit": "мл",
          "amount": 200
        }
      ],
      "is_favorited": true,
      "is_in_shopping_cart": false
    }
  ]
}
```

### Создать рецепт
**Запрос**
```http
POST /api/recipes/
Authorization: Token <token>
Content-Type: application/json

{
  "name": "Смузи",
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB...",
  "text": "Смешать ягоды, банан и йогурт в блендере.",
  "cooking_time": 5,
  "ingredients": [
    {"id": 12, "amount": 150},
    {"id": 18, "amount": 100}
  ]
}
```

**Ответ**
```json
{
  "id": 42,
  "name": "Смузи",
  "image": "http://localhost/media/recipes/smuzi.png",
  "text": "Смешать ягоды, банан и йогурт в блендере.",
  "cooking_time": 5,
  "author": {
    "email": "user@example.com",
    "id": 7,
    "username": "user",
    "first_name": "Мария",
    "last_name": "Петрова",
    "is_subscribed": false,
    "avatar": null
  },
  "ingredients": [
    {
      "id": 12,
      "name": "Клубника",
      "measurement_unit": "г",
      "amount": 150
    },
    {
      "id": 18,
      "name": "Йогурт",
      "measurement_unit": "мл",
      "amount": 100
    }
  ],
  "is_favorited": false,
  "is_in_shopping_cart": false
}
```

### Подписаться на автора
**Запрос**
```http
POST /api/users/5/subscribe/
Authorization: Token <token>
```

**Ответ**
```json
{
  "email": "chef@example.com",
  "id": 5,
  "username": "chef",
  "first_name": "Анна",
  "last_name": "Иванова",
  "is_subscribed": true,
  "avatar": "http://localhost/media/users/chef.png",
  "recipes": [
    {
      "id": 1,
      "name": "Тыквенный суп",
      "image": "http://localhost/media/recipes/pumpkin_soup.jpg",
      "cooking_time": 30
    }
  ],
  "recipes_count": 1
}
```

### Добавить рецепт в список покупок
**Запрос**
```http
POST /api/recipes/1/shopping_cart/
Authorization: Token <token>
```

**Ответ**
```json
{
  "id": 1,
  "name": "Тыквенный суп",
  "image": "http://localhost/media/recipes/pumpkin_soup.jpg",
  "cooking_time": 30
}
```

## Локальная разработка без Docker
1. Установите и запустите PostgreSQL 13, создайте базу и пользователя из `.env`.
2. Создайте виртуальное окружение и установите зависимости:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Экспортируйте переменные окружения (или используйте инструмент вроде `direnv`):
   ```bash
   export POSTGRES_DB=foodgram
   export POSTGRES_USER=foodgram
   export POSTGRES_PASSWORD=foodgram
   export POSTGRES_HOST=127.0.0.1
   export DJANGO_SECRET_KEY="change_me"
   export DJANGO_DEBUG=True
   ```
4. Выполните миграции и запустите сервер разработки:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

## Автор
Кичиков Алексей Михайлович
