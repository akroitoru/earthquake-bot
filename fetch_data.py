from datetime import datetime
import requests
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='earthquake_data.log',
    filemode='a'
)

def fetch_earthquake_data():
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude=43.25667&longitude=76.92861&maxradiuskm=400&orderby=time"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        events = []
        for feature in data.get("features", []):
            properties = feature.get("properties", {})
            event = {
                "id": feature.get("id"),
                "place": properties.get("place"),
                "mag": properties.get("mag"),
                "time": properties.get("time"),
                "url": properties.get("url")
            }
            events.append(event)

        logging.info("Получено %d событий", len(events))
        return events
    except requests.exceptions.RequestException as e:
        logging.error("Ошибка запроса: %s", e)
        return []
    except json.JSONDecodeError as e:
        logging.error("Ошибка JSON: %s", e)
        return []

