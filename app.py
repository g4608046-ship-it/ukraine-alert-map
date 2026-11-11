import os
import time
import asyncio
import threading
from flask import Flask, jsonify, render_template_string
from telethon import TelegramClient

app = Flask(__name__)

# Твои учетные данные Telegram API
API_ID = 39038265  
API_HASH = '935a93cf6e5202bf91e80be5689710ff'  
PHONE_NUMBER = '380989486803'   # Укажи здесь свой номер телефона (нужен для авторизации Telethon)

# Каналы для мониторинга
CHANNELS = ["raketa_trevoga", "timofii_kucher", "kiev_nebo"]

latest_logs = [
    {"channel": "Система", "time": "LIVE", "text": "Инициализация Telethon клиента..."},
]

def run_telegram_client():
    global latest_logs
    
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
                        async for message in client.iter_messages(entity, limit=3):
                            if message.text:
                                msg_text = message.text
                                if len(msg_text) > 130:
                                    msg_text = msg_text[:127] + "..."
                                    
                                msg_time = "LIVE"
                                if message.date:
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
                    unique_logs = []
                    seen = set()
                    for msg in all_messages:
                        identifier = (msg["channel"], msg["text"])
                        if identifier not in seen:
                            seen.add(identifier)
                            unique_logs.append(msg)
                    
                    latest_logs = unique_logs[:10]

                await asyncio.sleep(20)
                
        except Exception as e:
            print(f"Ошибка авторизации/работы Telethon: {e}")
            latest_logs = [{
                "channel": "Ошибка",
                "time": "ERR",
                "text": f"Сбой Telethon: {str(e)}"
            }]

    loop.run_until_complete(main())

# Запускаем Telethon в фоновом потоке
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
