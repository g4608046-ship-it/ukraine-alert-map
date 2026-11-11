import os
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ukraine Alert Map - Monitoring</title>
    <style>
        body {
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #30363d;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }
        h1 { font-size: 22px; color: #58a6ff; margin: 0; }
        .status-badge {
            background-color: #238636;
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
        }
        .card {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
        }
        h2 { font-size: 18px; margin-top: 0; color: #8b949e; }
        .alert-none { color: #3fb950; font-weight: bold; }
        .log-box {
            background-color: #010409;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 12px;
            font-family: monospace;
            font-size: 13px;
            height: 150px;
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
            <h2>Статус мониторинга воздушной обстановки</h2>
            <p>Текущий статус системы: <span class="alert-none">Система активна, сбор телеметрии запущен</span></p>
        </div>

        <div class="card">
            <h2>Логи и поступающие данные</h2>
            <div class="log-box" id="logs">
                [19:00:01] Инициализация подключения к потокам данных...<br>
                [19:00:02] Мониторинг воздушного пространства активен.<br>
                [19:00:05] Ожидание телеметрических данных...
            </div>
        </div>
    </div>
</body>
</html>
"""


@app.route('/')
def index():
  return render_template_string(HTML_TEMPLATE)


@app.route('/api/status')
def status():
  return jsonify({'status': 'active', 'region': 'Ukraine', 'service': 'online'})


if __name__ == '__main__':
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port=port)
