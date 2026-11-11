import os
import time
import threading
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

latest_logs = [
    "[SYSTEM] Инициализация модулей...",
    "[SYSTEM] Подключение к каналам мониторинга...",
]

CHANNELS = ["raketa_trevoga", "timofii_kucher", "kiev_nebo"]

def fetch_telegram_posts():
    global latest_logs
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    while True:
        all_messages = []
        for channel in CHANNELS:
            url = f"https://t.me/s/{channel}"
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    messages = soup.find_all('div', class_='tgme_widget_message_text')
                    
                    for msg in messages[-3:]:
                        text = msg.get_text(strip=True)
                        if text:
                            if len(text) > 100:
                                text = text[:97] + "..."
                            all_messages.append(f"<b>[{channel}]</b> {text}")
            except Exception as e:
                print(f"Ошибка при парсинге {channel}: {e}")
        
        if all_messages:
            latest_logs = all_messages[-10:]
            
        time.sleep(20)

threading.Thread(target=fetch_telegram_posts, daemon=True).start()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ukraine Alert & Telemetry Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body {
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 15px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #30363d;
            padding-bottom: 12px;
            margin-bottom: 15px;
        }
        h1 { font-size: 20px; color: #58a6ff; margin: 0; }
        .status-badge {
            background-color: #238636;
            color: white;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: bold;
        }
        .card {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }
        h2 { font-size: 16px; margin-top: 0; color: #8b949e; }
        #map {
            height: 400px;
            border-radius: 6px;
            border: 1px solid #30363d;
            z-index: 1;
        }
        .feed-box {
            background-color: #010409;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 10px;
            font-family: monospace;
            font-size: 12px;
            max-height: 200px;
            overflow-y: auto;
            color: #7ee787;
            line-height: 1.4;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🇺🇦 Ukraine Alert & Telemetry Map</h1>
            <div class="status-badge">LIVE 24/7</div>
        </header>

        <div class="card">
            <h2>Интерактивная карта мониторинга</h2>
            <div id="map"></div>
        </div>

        <div class="card">
            <h2>Лента событий (Telegram-мониторинг)</h2>
            <div class="feed-box" id="feed">
                Подключение к потоку данных...
            </div>
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // Границы Украины для ограничения карты
        var ukraineBounds = [
            [44.0, 21.5], // Юго-Запад
            [53.0, 40.5]  // Северо-Восток
        ];

        // Инициализация карты с жесткой привязкой к границам Украины
        var map = L.map('map', {
            maxBounds: ukraineBounds,
            maxBoundsViscosity: 1.0, // Запрещает вытягивать карту за пределы границ
            minZoom: 6,
            maxZoom: 12
        }).setView([48.3794, 31.1656], 6);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);

        function fetchTelemetry() {
            fetch('/api/telemetry')
                .then(response => response.json())
                .then(data => {
                    const feed = document.getElementById('feed');
                    feed.innerHTML = data.logs.join('<br><br>');
                })
                .catch(err => {
                    console.log('Sync waiting...');
                });
        }

        setInterval(fetchTelemetry, 5000);
        fetchTelemetry();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/telemetry')
def telemetry():
    return jsonify({'status': 'ok', 'logs': latest_logs})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
