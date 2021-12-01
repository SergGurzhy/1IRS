
from typing import List
from service.schema import *
import http.client


class SafeLocationService:
    """
    Wrapper class for the Safe Location Service HTTP API
    """

    class APIException(Exception):
        """
         Исключение, которое генерируется если HTTP ответ не соответствует положительному / ожидаемому
        """

        def __init__(self, response: http.client.HTTPResponse):
            super().__init__(f"API call failed with status {response.status} {response.reason}")
            self.http_status = response.status
            self.http_reason = response.reason

    def __init__(self, base_url: str, caller_id: str):
        """
        Class initializer
        :param base_url:  Service API base URL.
        :param caller_id: API user ID (e.g. "admin")
        """
        self.base_url = base_url
        self.caller_id = caller_id
        self.client = http.client.HTTPConnection(self.base_url)

    def __check_response_status(self, response: http.client.HTTPResponse, expected_status=None) -> http.client.HTTPResponse:
        """
        Проверяет полученный ответ с сервера по статус-коду.
        в случае кодов ошибки, поднимает ошибку типа APIException (собственный класс ошибок)

        :param response: Response received from service
        :return: input Response object
        """

        if response.status >= 400:
            raise self.APIException(response)
        if expected_status:
            if response.status != expected_status:
                raise Exception(f"Unexpected HTTP response status {response.status}. Expected status: {expected_status}")

        return response

    def __get_response(self, expected_status=None) -> http.client.HTTPResponse:
        """
        Вспомогательная функция, которая получает Response от сервера и проверяет его на ошибочные
        статус-коды.

        :return: Response object
        """
        return self.__check_response_status(self.client.getresponse(), expected_status)

    def create_user(self, user: User) -> str:
        """
        Создание профиля пользователя.
        В настоящей реализации сервиса API пользователь может создать только один
        профиль на сервере. При попытке создать второй профиль, поднимается исключение.

        :param user: User profile to save on the server.
        :return: ID of user profile assigned by the service.
        """

        headers = {HEADER_CONTENT_TYPE: JSON_FORMAT, HEADER_CALLER_ID: self.caller_id}
        data = user.serialize()
        self.client.request('POST', '/user', data, headers)
        response = self.__get_response()
        if response.status == 201:
            url = response.getheader('Location')
            return url[url.rfind('/') + 1:]

        raise Exception("Unexpected server response. Response status:", response.status)

    def get_user(self, user_id: str) -> User:
        """
        Retrieves user profile from the service if exists, or raises exception.

        :param user_id: ID of user profile assigned by the service.
        :return: User profile returned by the service.
        """
        headers = {HEADER_ACCEPT: JSON_FORMAT, HEADER_CALLER_ID: self.caller_id}
        self.client.request('GET', f'/user/{user_id}', headers=headers)
        response = self.__get_response(200)

        return User(**json.loads(response.read().decode()))

    def delete_user(self, user_id: str) -> None:
        """
        Удадение профиля пользователя, если он существует на сервере.
        Удаление может выполнить только создатель профиля или администратор.
        В противном случае поднимается исключение.

        :param user_id: ID of user profile assigned by the service
        :return: None
        """
        headers = {HEADER_CALLER_ID: self.caller_id}
        self.client.request('DELETE', f'/user/{user_id}', headers=headers)
        self.__get_response()

    def get_owner_ids(self, owner) -> List[str]:
        """
        Возвращает список профилей созданных указанным API пользователем owner.

        :param owner: API user ID (e.g. "admin")
        :return: List of profile IDs created by specified API user.
                 Empty if user has no profiles on the server.
        """

        headers = {HEADER_ACCEPT: JSON_FORMAT, HEADER_CALLER_ID: self.caller_id}
        self.client.request('GET', f'/user/?owner={owner}', headers=headers)
        response = self.__get_response(200)

        return json.loads(response.read().decode())

    def check_service_running(self):
        headers = {HEADER_ACCEPT: JSON_FORMAT}
        self.client.request('GET', '/', headers=headers)
        self.__get_response(200)

