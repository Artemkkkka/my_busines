# **Busines helper**

# Оглавление

- Авторы

- Технологический стек

- Установка и запуск проекта

- API эндпоинты

- Главная страница

- Тестирование

- Лицензия

# Авторы
**(контакт-ссылки для связи по email)**

- [Артем Брагин](mailto:bragin15bragin@yandex.ru) - developer  

# Технологический стек

- Python 3.11

- fastapi

- fastapi-users

- sqlalchemy

- alembic

- PostgreSQL

- Git для управления версиями

# Установка и запуск проекта
**Ниже приведены команды для клонирования,
настройки и запуска проекта YaMDb.**

*1. Клонирование репозитория и создание виртуального окружения*
```bash
git clone git@github.com:Artemkkkka/my_busines.git
cd my_busines

python3 -m venv venv
```
*2. Создайте .env*
```bash
touch .env
```
```bash
cp .env.example .env
```

*3. Активация окружения и запуск проекта*
```bash
# macOS/Linux:
source venv/bin/activate
```
```bash
# Windows:
venv\Scripts\activate
```
```bash
docker compose up --build
```

# API эндпоинты
**Полная спецификация доступна после запуска сервера в [документации API](http://127.0.0.1:8000/docs)**

# Главная страница
**На главной [странице](http://127.0.0.1:8000/) Вы можете найти ссылки на документацию и на страницу [календаря](http://127.0.0.1:8000/calendar)**

# Тестирование

**Запуск тестов с измерением процента покрытия кода в дирректории `api_yamdb`:**
- Установка:
```bash
pip install pytest-cov
```
- Запуск:
```bash
pytest --cov=src
```



