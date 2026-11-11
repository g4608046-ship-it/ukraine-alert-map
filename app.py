import os
import time
import threading
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

# Секретный пароль для доступа к добавлению (можешь изменить на любой свой)
ADMIN_SECRET_KEY = "my_super_secret_pass_123"

latest_logs = [
    {"channel": "Система", "time": "03:30", "text": "Защищенный мониторинг запущен..."},
]

CHANNELS = ["raketa_trevoga", "timofii_kucher", "kiev_nebo"]

def fetch_telegram_posts():
    global latest_logs
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    while True:
        all_messages = []
        for channel in CHANNELS:
            url = f"https://t.me/s/{channel}"
            try:
                response = requests.get(url, headers=headers, timeout=8)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    messages = soup.find_all('div', class_='tgme_widget_message')
                    
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
            except Exception as e:
                print(f"Ошибка фонового опроса {channel}: {e}")
        
        if all_messages:
            unique_logs = []
            seen = set()
            for msg in reversed(all_messages):
                identifier = (msg["channel"], msg["text"])
                if identifier not in seen:
                    seen.add(identifier)
                    unique_logs.append(msg)
            
            latest_logs = unique_logs[:10]
            
        time.sleep(20)

threading.Thread(target=fetch_telegram_posts, daemon=True).start()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Мапа тривог</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body {
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 10px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 5px;
            margin-bottom: 5px;
        }
        .header-title {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .app-icon {
            width: 32px;
            height: 32px;
            background: #ffcc00;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: #000;
            font-size: 16px;
        }
        h1 { font-size: 18px; margin: 0; color: #fff; }
        .sub-date { font-size: 11px; color: #8b949e; }
        
        .map-card {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 8px;
            margin-bottom: 15px;
        }
        #map {
            height: 360px;
            border-radius: 8px;
            border: 1px solid #30363d;
            background-color: #161b22;
            z-index: 1;
        }

        .feed-header {
            font-size: 12px;
            font-weight: bold;
            color: #8b949e;
            text-align: center;
            margin-bottom: 10px;
            text-transform:
