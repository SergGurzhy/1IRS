import unittest
from typing import Tuple

from client import *

USER_ID_1 = 'test_user_1'
USER_ID_2 = 'test_user_2'
HOST = '127.0.0.1:5000'


def __check_service_running() -> None:
    client = SafeLocationService(HOST, USER_ID_ADMIN)
    try:
        client.check_service_running()
    except Exception:
        print(f"Service at {HOST} is not running")


__check_service_running()


class SafeLocationServiceTests(unittest.TestCase):

    @staticmethod
    def delete_user(owner):
        client = SafeLocationService(HOST, USER_ID_ADMIN)
        ids = client.get_owner_ids(owner)
        if ids:
            for user_id in ids:
                client.delete_user(user_id)

    @staticmethod
    def create_user(user_name: str, lat: float, lon: float) -> Tuple[User, SafeLocationService, str]:
        user = User(f'{user_name}', Location(lat, lon))
        client = SafeLocationService(HOST, user_name)
        user_id = client.create_user(user)
        user = User(f'{user_name}', Location(lat, lon), user_id=user_id)
        return user, client, user_id

    def test_user_access(self):

        # Начинаем с удаления записи, которую  тест создает, если она есть
        self.delete_user(USER_ID_1)

        # Проверяем, что пользователь может создать запись на сервере и прочитать назад
        # эдентичную копию.
        user_1, client_1, user_1_id = self.create_user(USER_ID_1, 56.32, 65.23)
        user_1_copy = client_1.get_user(user_1_id)
        self.assertEqual(user_1, user_1_copy)

        # Второй пользователь, при обращении к id другого пользователя,
        # получает искаженные координаты
        client_2 = SafeLocationService(HOST, USER_ID_2)
        user_2_view = client_2.get_user(user_1_id)
        self.assertEqual(user_1.full_name, user_2_view.full_name)
        self.assertNotEqual(user_1.location, user_2_view.location)

    def test_admin_access(self):
        # Начинаем с удаления записи, которую  тест создает, если она есть
        self.delete_user(USER_ID_1)

        # Проверяем, что пользователь может создать запись на сервере и прочитать назад
        # эдентичную копию.
        user_1, client_1, user_1_id = self.create_user(USER_ID_1, 56.32, 65.23)
        user_1_copy = client_1.get_user(user_1_id)
        self.assertEqual(user_1, user_1_copy)

        # Проверяем, что Админ может прочитать у любого Пользователя реальные данные
        admin = SafeLocationService(HOST, USER_ID_ADMIN)
        user_1_admin_view = admin.get_user(user_1_id)
        self.assertEqual(user_1, user_1_admin_view)


if __name__ == '__main__':
    unittest.main()
