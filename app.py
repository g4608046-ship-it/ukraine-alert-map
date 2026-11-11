import os
import time
import threading
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# Стартовый лог
latest_logs = [
    {"channel": "Система", "time": "00:00", "text": "Ожидание данных от каналов Telegram..."},
]

CHANNELS = ["raketa_trevoga", "timofii_kucher", "kiev_nebo"]

def fetch_telegram_posts():
    global latest_logs
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,uk;q=0.8"
    }
    
    while True:
        all_messages = []
        for channel in CHANNELS:
            url = f"https://t.me/s/{channel}"
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    messages = soup.find_all('div', class_='tgme_widget_message')
                    
                    if not messages:
                        # Если новый класс не найден, пробуем искать текст напрямую
                        texts = soup.find_all('div', class_='tgme_widget_message_text')
                        for t in texts[-3:]:
                            content = t.get_text(strip=True)
                            if content:
                                all_messages.append({
                                    "channel": f"@{channel}",
                                    "time": "LIVE",
                                    "text": content[:127] + "..." if len(content) > 130 else content
                                })
                    else:
                        for msg in messages[-3:]:
                            text_elem = msg.find('div', class_='tgme_widget_message_text')
                            time_elem = msg.find('time', class_='tgme_widget_message_date')
                            
                            text = text_elem.get_text(strip=True) if text_elem else ""
                            post_time = "LIVE"
                            if time_elem and time_elem.has_attr('datetime'):
                                dt_str = time_elem['datetime']
                                if 'T' in dt_str:
                                    post_time = dt_str.split('T')[1][:5]
                                    
                            if text:
                                if len(text) > 130:
                                    text = text[:127] + "..."
                                all_messages.append({
                                    "channel": f"@{channel}",
                                    "time": post_time,
                                    "text": text
                                })
                else:
                    print(f"Ошибка HTTP {response.status_code} для {channel}")
            except Exception as e:
                print(f"Ошибка при парсинге {channel}: {e}")
        
        if all_messages:
            # Свежие сверху
            latest_logs = all_messages[-10:][::-1]
        else:
            # Если не удалось спарсить, покажем статус в ленте
            latest_logs = [{
                "channel": "Менеджер связи",
                "time": "ERR",
                "text": "Не удалось получить посты. Проверяем соединение с Telegram..."
            }]
            
        time.sleep(15)

# Запускаем поток
threading.Thread(target=fetch_telegram_posts, daemon=True).start()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Мапа тривог</title>
    <link rel="stylesheet" href="
