"""
Classes and constants shared by Safe Location Service implementation and clients.
"""

import json
from typing import Union


HEADER_CONTENT_TYPE = 'Content-type'
JSON_FORMAT = 'application/json'
HEADER_ACCEPT = 'Accept'
HEADER_CALLER_ID = 'X-self-caller-id'
USER_ID_ADMIN = 'admin'


MIN_LONGITUDE = -180.0
MAX_LONGITUDE = 180.0
MIN_LATITUDE = -90
MAX_LATITUDE = 90


def isequal(first, second) -> bool:
    """
    Compare objects equality in a way useful as __eq__ implementation
    :param first: First object to compare (usually "self")
    :param second: Object to compare the first object to (usually "other")
    :return: True is objects are equal
    """
    if first is second:
        return True

    if not isinstance(second, type(first)):
        return False

    return vars(first) == vars(second)


class Location:
    def __init__(self, lat: float, lon: float):
        self.lat = self.__enforce_lat(lat)
        self.lon = self.__enforce_lon(lon)

    def __eq__(self, o: object) -> bool:
        return isequal(self, o)

    def __str__(self):
        return f"lat: {self.lat}, lon: {self.lon}"

    @staticmethod
    def __enforce_lat(lat):
        if not isinstance(lat, float):
            lat = float(lat)

        if MIN_LATITUDE < lat < MAX_LATITUDE:
            return lat

        raise ValueError(f"Invalid latitude value {lat}. Valid range is {MIN_LATITUDE} - {MAX_LATITUDE}")

    @staticmethod
    def __enforce_lon(lon):
        if not isinstance(lon, float):
            lon = float(lon)

        if MIN_LONGITUDE < lon < MAX_LONGITUDE:
            return lon

        raise ValueError(f"Invalid longitude value {lon}. Valid range is {MIN_LONGITUDE} - {MAX_LONGITUDE}")


class User:
    def __init__(self, full_name: str, location: Union[Location, dict], user_id: str = None):
        self.user_id = user_id
        self.full_name = self.__enforce_full_name(full_name)
        self.location = location if isinstance(location, Location) else Location(**location)

    def __eq__(self, o: object) -> bool:
        return isequal(self, o)

    def __str__(self):
        return f"id: {self.user_id}, full name: {self.full_name}, " \
               f"location: {self.location}"

    @staticmethod
    def __enforce_full_name(full_name: str):
        if not full_name:
            raise ValueError("Name field is empty")
        return full_name

    def serialize(self):
        return json.dumps(self, default=lambda x: vars(x))





