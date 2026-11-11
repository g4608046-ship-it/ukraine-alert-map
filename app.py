import os
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ukraine Alert & Telemetry Map</title>
    <!-- Стили Leaflet для карты -->
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
            max-height: 150px;
            overflow-y: auto;
            color: #7ee787;
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
            <h2>Лента событий и телеметрия</h2>
            <div class="feed-box" id="feed">
                Подключение к потоку данных...
            </div>
        </div>
    </div>

    <!-- Скрипт Leaflet -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // Инициализация карты с центром на Украине
        var map = L.map('map').setView([48.3794, 31.1656], 6);

        // Стабильный слой OpenStreetMap для надежного отображения тайлов
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 18,
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);

        // Функция обновления телеметрии с сервера без падений
        function fetchTelemetry() {
            fetch('/api/telemetry')
                .then(response => response.json())
                .then(data => {
                    const feed = document.getElementById('feed');
                    feed.innerHTML = data.logs.join('<br>');
                })
                .catch(err => {
                    console.log('Telemetry sync waiting...');
                });
        }

        // Обновляем каждые 5 секунд
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
  return jsonify({
      'status': 'ok',
      'logs': [
          '[20:00:01] Модуль картографии инициализирован.',
          '[20:00:03] Сбор телеметрических данных запущен в штатном режиме.',
          '[20:00:05] Ожидание новых сигналов с каналов...',
      ],
  })


if __name__ == '__main__':
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port=port)
