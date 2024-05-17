import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
import os

# Базовый URL Lenta.ru
BASE_URL = 'https://lenta.ru'

# Заголовки для запросов
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
}

# Асинхронная функция для выполнения сетевых запросов
async def fetch(session, url):
    # Выводим информацию о том, какой URL мы запрашиваем
    print(f"Запрос URL: {url}")
    async with session.get(url, headers=HEADERS) as response:
        # Возвращаем текст ответа
        return await response.text()

# Асинхронная функция для парсинга статьи
async def parse_article(session, url):
    try:
        # Выводим информацию о том, какую статью мы парсим
        print(f"Парсинг статьи: {url}")
        # Получаем HTML содержимое статьи
        html = await fetch(session, url)
        # Создаем объект BeautifulSoup для работы с HTML
        soup = BeautifulSoup(html, 'lxml')

        # Ищем заголовок статьи
        title = soup.find('h1') or soup.find('title')  # Более общий селектор
        # Ищем содержимое статьи
        content_elements = soup.find_all('p')
        # Ищем категорию статьи
        category = soup.find('a', class_='rubric-label')  # Обновленный класс
        # Ищем дату публикации статьи
        created_date = soup.find('time')  # Более общий селектор

        # Создаем словарь для хранения данных о статье
        article_data = {}
        # Проверяем наличие заголовка и содержимого статьи
        if title and content_elements:
            # Получаем текст заголовка и удаляем лишние пробелы
            article_data['title'] = title.get_text(strip=True)
            # Получаем текст содержимого статьи и объединяем в строку
            article_data['content'] = " ".join(p.get_text(strip=True) for p in content_elements)
            # Получаем текст категории статьи
            article_data['category'] = category.get_text(strip=True) if category else "N/A"
            # Получаем дату публикации статьи
            article_data['created_date'] = created_date['datetime'] if created_date and 'datetime' in created_date.attrs else "Unknown"
            # Сохраняем URL статьи
            article_data['url'] = url

            # Выводим информацию о том, что статья успешно спарсена
            print(f"Статья успешно спарсена: {article_data['title']}")
        else:
            # Выводим сообщение о том, что не хватает некоторых элементов, и статья не была спарсена
            print("Отсутствует заголовок или содержимое, статья не спарсена")

        return article_data
    except Exception as e:
        # Выводим сообщение об ошибке, если что-то пошло не так при парсинге статьи
        print(f"Ошибка при парсинге статьи {url}: {e}")
        return {}

# Асинхронная функция для парсинга главной страницы
async def parse_main_page():
    async with aiohttp.ClientSession() as session:
        # Получаем HTML содержимое главной страницы
        main_page = await fetch(session, BASE_URL)
        # Создаем объект BeautifulSoup для работы с HTML
        soup = BeautifulSoup(main_page, 'lxml')
        # Создаем список для хранения URL статей
        articles_urls = []

        # Ищем ссылки на статьи
        for a in soup.select('a'):  # Более общий селектор
            href = a.get('href', '')
            if href.startswith('/'):
                href = BASE_URL + href
            if BASE_URL in href and href not in articles_urls:
                articles_urls.append(href)

        # Выводим информацию о количестве найденных статей
        print(f"Найдено {len(articles_urls)} статей")
        # Создаем список для хранения задач парсинга статей
        tasks = [asyncio.create_task(parse_article(session, url)) for url in articles_urls]
        # Выполняем все задачи параллельно
        articles_data = await asyncio.gather(*tasks)

        # Фильтруем пустые результаты
        articles_data = [article for article in articles_data if article]

        # Создаем папку для результатов, если ее нет
        results_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
        os.makedirs(results_dir, exist_ok=True)
       
