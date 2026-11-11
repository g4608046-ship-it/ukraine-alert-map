import os
import time
import asyncio
import threading
from flask import Flask, jsonify, render_template_string
from telethon import TelegramClient

app = Flask(__name__)

# Твои учетные данные Telegram API
API_ID = 1234567  # Замени на свой integer API_ID
API_HASH = 'your_api_hash_here'  # Замени на свой string API_HASH
PHONE_NUMBER = '+380XXXXXXXXX'   # Твой номер телефона

# Каналы для мониторинга
CHANNELS = ["raketa_trevoga", "timofii_kucher", "kiev_nebo"]

latest_logs = [
    {"channel": "Система", "time": "LIVE", "text": "Инициализация Telethon клиента..."},
]

def run_telegram_client():
    global latest_logs
    
    # Создаем асинхронный цикл для Telethon в фоновом потоке
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    client = TelegramClient('session_name', API_ID, API_HASH)

    async def main():
        global latest_logs
        try:
            await client.start(phone=PHONE_NUMBER)
            print("Telethon клиент успешно запущен как читатель!")
            
            while True:
                all_messages = []
                for channel in CHANNELS:
                    try:
                        entity = await client.get_entity(channel)
                        # Читаем последние 3 сообщения из каждого канала
                        async for message in client.iter_messages(entity, limit=3):
                            if message.text:
                                msg_text = message.text
                                if len(msg_text) > 130:
                                    msg_text = msg_text[:127] + "..."
                                    
                                # Форматируем время сообщения
                                msg_time = "LIVE"
                                if message.date:
                                    # Конвертируем в локальное время (UTC+2/+3) или просто берем часы:минуты
                                    local_time = message.date.strftime('%H:%M')
                                    msg_time = local_time

                                all_messages.append({
                                    "channel": f"@{channel}",
                                    "time": msg_time,
                                    "text": msg_text
                                })
                    except Exception as e:
                        print(f"Ошибка чтения канала {channel}: {e}")

                if all_messages:
                    # Сортируем и убираем дубликаты, свежие сверху
                    unique_logs = []
                    seen = set()
                    for msg in all_messages:
                        identifier = (msg["channel"], msg["text"])
                        if identifier not in seen:
                            seen.add(identifier)
                            unique_logs.append(msg)
                    
                    # Ограничиваем до 10 последних штук
                    latest_logs = unique_logs[:10]

                # Пауза перед следующим опросом каналов через API
                await asyncio.sleep(20)
                
        except Exception as e:
            print(f"Ошибка авторизации/работы Telethon: {e}")
            latest_logs = [{
                "channel": "Ошибка",
                "time": "ERR",
                "text": f"Сбой Telethon: {str(e)}"
            }]

    loop.run_until_complete(main())

# Запускаем Telethon в фоновом потоке, чтобы он не вешал Flask
threading.Thread(target=run_telegram_client, daemon=True).start()

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
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .post-card {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 12px 15px;
            margin-bottom: 10px;
        }
        .post-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            font-size: 13px;
        }
        .channel-info {
            display: flex;
            align-items: center;
            gap: 6px;
            color: #58a6ff;
            font-weight: 500;
        }
        .post-time {
            color: #8b949e;
            font-size: 12px;
        }
        .post-text {
            font-size: 14px;
            color: #e6edf3;
            line-height: 1.4;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-title">
                <div class="app-icon">🇺🇦</div>
                <div>
                    <h1>Мапа тривог</h1>
                    <div class="sub-date" id="live-date">Станом на --.--.---- --:--</div>
                </div>
            </div>
        </header>

        <div class="map-card">
            <div id="map"></div>
        </div>

        <div class="feed-header">Повідомлення з Telegram</div>
        <div id="feed-container">
            Загрузка данных через Telethon API...
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const now = new Date();
        const day = String(now.getDate()).padStart(2, '0');
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const year = now.getFullYear();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        document.getElementById('live-date').innerText = `Станом на ${day}.${month}.${year} ${hours}:${minutes}`;

        var ukraineBounds = [
            [44.3, 21.8],
            [52.4, 40.2]
        ];

        var map = L.map('map', {
            maxBounds: ukraineBounds,
            maxBoundsViscosity: 1.0,
            minZoom: 6,
            maxZoom: 10
        }).setView([48.3794, 31.1656], 6);

        L.tileLayer('https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png', {
            maxZoom: 20,
            attribution: '&copy; Stadia Maps, OpenMapTiles, OpenStreetMap'
        }).addTo(map);

        function fetchTelemetry() {
            fetch('/api/telemetry')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('feed-container');
                    let html = '';
                    data.logs.forEach(post => {
                        html += `
                            <div class="post-card">
                                <div class="post-header">
                                    <div class="channel-info">
                                        <span>🔵</span> ${post.channel}
                                    </div>
                                    <div class="post-time">${post.time}</div>
                                </div>
                                <div class="post-text">${post.text}</div>
                            </div>
                        `;
                    });
                    container.innerHTML = html;
                })
                .catch(err => console.log('Sync error'));
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
