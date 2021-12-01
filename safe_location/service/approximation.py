import random
from schema import Location
from geopy.distance import geodesic
import geopy.distance


LOCATION_APPROXIMATION_RADIUS_KM = 1.0


def create_approximate_location(location: Location, radius: float = 1) -> Location:
    """
     Создание  фейковых координат с помощью библиотеки geopy с учетом элипсоидности Земли.

    :param location:  real location: Location
    :param radius: радиус круга, в котором указывается точка Float, километров
    :return: Новая фейковая локация Tuple[float, float]
    """




    # Получение фейковых координат. Чтобы "случайно" не получить нулевое смещение, берем за минимум расстояния 1/5
    # от указанного максимума.
    distance = random.uniform((radius / 5), radius)
    bearing = random.randint(-90, 270)
    new_lat, new_lon, height = geopy.distance.distance(kilometers=distance).destination((location.lat, location.lon),
                                                                                    bearing=bearing)
    return Location(new_lat, new_lon)



def get_distance(real_location: Location, fake_location: Location) -> int:
    """
    Функция расчета расстояния между координатами. Получив две локации, определяет расстояние между ними по поверхности Земли
    "Это определяет метод geopy.distance, который определяет расстояние на поверхности земли между двумя локациями
    :param real_location:  Широта и Долгота  №1
    :param fake_location:  Широта и Долгота  №2
    :return:   Расстояние в километрах
    """

    point_1 = real_location.lat, real_location.lon
    point_2 = fake_location.lat, fake_location.lon

    return geodesic(point_1, point_2).kilometers

