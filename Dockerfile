# 1. Базовый образ Python 3.11
FROM python:3.11-slim

# 2. Рабочая директория внутри контейнера
WORKDIR /app

# 3. Копируем все файлы проекта внутрь контейнера
COPY . .

# 4. Обновляем pip и ставим зависимости
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 5. Указываем порт для встроенного HTTP сервера (UptimeRobot)
EXPOSE 8080

# 6. Команда запуска бота
CMD ["python", "bot.py"]
