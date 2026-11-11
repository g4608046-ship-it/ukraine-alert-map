import os
import time
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

# Хранилище логов в памяти (последние 10 сообщений)
latest_logs = [
    {"channel": "Система", "time": "03:20", "text": "Мониторинг запущен. Ожидание данных..."},
]

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
            height: 340px;
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

        /* Форма добавления (скрытая/аккуратная панель) */
        .admin-panel {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 15px;
        }
        .admin-panel input, .admin-panel textarea {
            width: 100%;
            background: #0d1117;
            border: 1px solid #30363d;
            color: #fff;
            padding: 8px;
            border-radius: 6px;
            margin-bottom: 8px;
            box-sizing: border-box;
            font-size: 13px;
        }
        .admin-panel button {
            background: #238636;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            width: 100%;
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

        <!-- Карта -->
        <div class="map-card">
            <div id="map"></div>
        </div>

        <!-- Быстрая панель добавления поста (работает прямо с телефона) -->
        <div class="admin-panel">
            <form id="post-form" onsubmit="addPost(event)">
                <input type="text" id="channel-input" placeholder="Канал (например: @raketa_trevoga)" value="@raketa_trevoga" required>
                <textarea id="text-input" rows="2" placeholder="Текст сообщения о тревоге..." required></textarea>
                <button type="submit">Опубликовать в ленту</button>
            </form>
        </div>

        <div class="feed-header">Повідомлення з Telegram</div>
        <div id="feed-container">
            Загрузка ленты...
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

        function addPost(event) {
            event.preventDefault();
            const channel = document.getElementById('channel-input').value;
            const text = document.getElementById('text-input').value;

            fetch('/api/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ channel, text })
            })
            .then(res => res.json())
            .then(data => {
                if(data.status === 'ok') {
                    document.getElementById('text-input').value = '';
                    fetchTelemetry();
                }
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

@app.route('/api/add', methods=['POST'])
def add_message():
    global latest_logs
    data = request.get_json()
    if data and 'text' in data:
        t_now = time.strftime("%H:%M")
        new_entry = {
            "channel": data.get("channel", "@monitor"),
            "time": t_now,
            "text": data.get("text")
        }
        # Добавляем в начало списка
        latest_logs.insert(0, new_entry)
        if len(latest_logs) > 10:
            latest_logs.pop()
        return jsonify({'status': 'ok'})
    return jsonify({'status': 'error'}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
