import os
# Этот класс поможет нам сделать картинку из потока байт
import pygame
import requests
import spn_reformer
import math
# Пусть наше приложение предполагает запуск:
# python search.py Москва, ул. Ак. Королева, 12
# Тогда запрос к геокодеру формируется следующим образом:


def distance(coord_list):
    l = 111000
    len_of_way = int()
    for i in range(1, len(coord_list)):
        l_1 = math.radians((coord_list[i][1] + coord_list[i - 1][1]) / 2.)
        l_1 = math.cos(l_1)
        dx = (coord_list[i][0] - coord_list[i - 1][0]) * l * l_1
        dy = (coord_list[i][1] - coord_list[i - 1][1]) * l
        len_of_way += math.sqrt((dx ** 2) + (dy ** 2))
    return str(len_of_way).split('.')[0] + 'м'


toponym_to_find = input()

geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

geocoder_params = {
    "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
    "geocode": toponym_to_find,
    "format": "json"}

response = requests.get(geocoder_api_server, params=geocoder_params)

if not response:
    # обработка ошибочной ситуации
    pass

# Преобразуем ответ в json-объект
json_response = response.json()
# Получаем первый топоним из ответа геокодера.
toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
# Координаты центра топонима:
toponym_coodrinates = toponym["Point"]["pos"]
# Долгота и широта:
toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")

search_api_server = "https://search-maps.yandex.ru/v1/"
api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"

search_params = {
    "apikey": api_key,
    "text": "аптека",
    "lang": "ru_RU",
    "ll": ','.join(toponym_coodrinates.split()),
    "type": "biz"
}

response = requests.get(search_api_server, params=search_params)
if not response:
    #...
    pass
# Собираем параметры для запроса к StaticMapsAPI:

json_response = response.json()
lon_lat_dict = {'lon': [float(toponym_longitude)], 'lat': [float(toponym_lattitude)]}
chem_marks = list()
for i in range(10):
    # Получаем первую найденную организацию.
    organization = json_response["features"][i]
    # Получаем координаты ответа.
    point = organization["geometry"]["coordinates"]
    if 'TwentyFourHours' in list(organization['properties']['CompanyMetaData']['Hours']['Availabilities'][0].keys()):
        if organization['properties']['CompanyMetaData']['Hours']['Availabilities'][0]['TwentyFourHours'] is True:
            chem_marks.append(f'{str(point[0])},{str(point[1])},pm2gnm')
        elif organization['properties']['CompanyMetaData']['Hours']['Availabilities'][0]['TwentyFourHours'] is False:
            chem_marks.append(f'{str(point[0])},{str(point[1])},pm2blm')
    else:
        chem_marks.append(f'{str(point[0])},{str(point[1])},pm2grm')
    lon_lat_dict['lon'].append(point[0])
    lon_lat_dict['lat'].append(point[1])
toponym_spn = dict()
toponym_spn['lowerCorner'] = [min(lon_lat_dict['lon']), min(lon_lat_dict['lat'])]
toponym_spn['upperCorner'] = [max(lon_lat_dict['lon']), max(lon_lat_dict['lat'])]


lon_, lat_ = spn_reformer.reform(toponym_spn)
map_params = {
    "ll": ",".join([str(toponym_spn['lowerCorner'][0] + (lon_ / 2)), str(toponym_spn['lowerCorner'][1] + (lat_ / 2))]),
    "spn": ",".join([str(lon_), str(lat_)]),
    "l": "map",
    "pt": '~'.join([f'{toponym_longitude},{toponym_lattitude},pm2rdm', *chem_marks])
}
map_api_server = "http://static-maps.yandex.ru/1.x/"
# ... и выполняем запрос
response = requests.get(map_api_server, params=map_params)
map_file = "map.png"
with open(map_file, "wb") as file:
    file.write(response.content)

# Инициализируем pygame
pygame.init()
screen = pygame.display.set_mode((600, 450))
# Рисуем картинку, загружаемую из только что созданного файла.
screen.blit(pygame.image.load(map_file), (0, 0))
# Переключаем экран и ждем закрытия окна.
pygame.display.flip()
while pygame.event.wait().type != pygame.QUIT:
    pass
pygame.quit()

os.remove(map_file)