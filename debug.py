# from db_manager import save_earthquakes_to_db
# from fetch_data import fetch_earthquake_data
#
# if __name__ == "__main__":
#     earthquakes = fetch_earthquake_data()
#     print(f"Полученные данные: {earthquakes}")
#     if earthquakes:
#         save_earthquakes_to_db(earthquakes)
#     else:
#         print("Нет данных для сохранения.")

# import requests
# import json
#
# base_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
# params = {
#     "format": "geojson",
#     "latitude": 43.25667,
#     "longitude": 76.92861,
#     "maxradiuskm": 1000,
#     "minmagnitude": 2,
#     "orderby": "time"
# }
#
# response = requests.get(base_url, params=params)
# data = response.json()
#
# print(json.dumps(data, indent=2)[:1000])

# from fetch_data import fetch_earthquake_data
#
# earthquakes = fetch_earthquake_data()
# print(f" Найдено {len(earthquakes)} землетрясений")
# for eq in earthquakes:
#     print(eq)
