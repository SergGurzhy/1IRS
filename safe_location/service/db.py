
from enum import Enum
from sqlite3 import IntegrityError
from typing import Optional, List
import sqlite3
import os
from approximation import *
from schema import *

DATABASE = 'users.db'
DB_PATH = os.path.join(os.getcwd(), DATABASE)
GENERIC_ERROR_MESSAGE = "Database operation failed"
USER_NOT_FOUND_MESSAGE = 'User not found'


def connect_db():
    connect = sqlite3.connect(DB_PATH)
    return connect


def create_db():
    db = connect_db()
    cursor = db.cursor()
    sql_create_table = """ CREATE TABLE IF NOT EXISTS users (
                            id    INTEGER PRIMARY KEY AUTOINCREMENT,
                            owner  TEXT UNIQUE,
                            full_name  TEXT,
                            real_lat   REAL,
                            real_lon   REAL,
                            fake_lat   REAL,
                            fake_lon   REAL
                            )"""
    cursor.execute(sql_create_table)
    db.commit()
    db.close()


class Role(Enum):
    """
    Роли пользователей сервиса / API (администратор, создатель профиля, другой пользователь)
    """
    ADMIN = 'admin'
    OWNER = 'user'
    OTHER = 'other'


class DataBase:
    """
    Database access class
    """

    class Error:
        """
        Errors, specific to our service logic.
        """
        class Code(Enum):
            GENERIC = 1
            USER_NOT_FOUND = 2
            USER_ALREADY_EXISTS = 3

        code: Code
        message: str

        def __init__(self, code, message=None):
            self.code = code
            self.message = message

    def __init__(self, db: sqlite3):
        self.db = db
        self.cur = self.db.cursor()

    def get_caller_role(self, user_id: str, caller_id: str) -> Union[Error, Role]:
        """
        Определяем роль пользователя API (caller_id) в контексте профиля (user_id),
        к которому идет обращение.

        :param user_id: ID профиля, к которому будет делаться обращение
        :param caller_id: ID пользователя сервиса
        :return: Роль пользователя (администратор, создатель профиля, другой пользователь)
        """
        if caller_id == USER_ID_ADMIN:
            return Role.ADMIN

        sql = "SELECT owner FROM users WHERE id = ?"
        self.cur.execute(sql, (user_id,))
        result = self.cur.fetchall()
        if not result:
            return self.Error(self.Error.Code.USER_NOT_FOUND, USER_NOT_FOUND_MESSAGE)

        owner = result[0][0]
        return Role.OWNER if owner == caller_id else Role.OTHER

    def get_user(self, user_id: int, be_real: bool = True) -> Union[Error, Optional[User]]:
        """
        :param user_id: User profile ID
        :param be_real: Real or approximate location to return
        :return: User profile or error
        """
        try:
            self.cur.execute("SELECT * FROM users  WHERE id = ?", (user_id,))
            res = self.cur.fetchall()[0]
            if not res:
                return self.Error(self.Error.Code.USER_NOT_FOUND, USER_NOT_FOUND_MESSAGE)

            if be_real:
                lat = res[-4]
                lon = res[-3]
            else:
                lat = res[-2]
                lon = res[-1]

            location = Location(lat, lon)
            user_id = str(res[0])
            full_name = res[1]

            return User(user_id=user_id, full_name=full_name, location=location)

        except Exception:
            return self.Error(self.Error.Code.GENERIC, GENERIC_ERROR_MESSAGE)

    def get_users_id(self, owner=None, name=None) -> Union[Error, List]:
        """
        Finds all profiles created by specified owner or with the specified name

        :param owner: Optional API user ID
        :param name: Optional name fragment
        :return: List of found user profile IDs
        """
        try:
            if not owner and not name:
                self.cur.execute("SELECT id FROM users")
            elif owner and not name:
                self.cur.execute("SELECT id FROM users WHERE owner = ?", (owner,))
            elif not owner and name:
                self.cur.execute("SELECT id FROM users WHERE full_name LIKE ?", ('%' + name + '%',))
            else:
                self.cur.execute("SELECT id FROM users WHERE full_name LIKE ? AND owner = ?", ('%' + name + '%', owner))

            res = self.cur.fetchall()
            return [i[0] for i in res]

        except Exception as e:
            print(e)
            return self.Error(self.Error.Code.GENERIC, GENERIC_ERROR_MESSAGE)

    def save_user(self, user: User, caller_id: str) -> Union[Error, str]:
        """
        Сохранение профиля пользователя в базе данных

        :param user: User profile
        :param caller_id: Service user ID
        :return: User profile ID
        """
        try:
            fake_location = create_approximate_location(user.location, LOCATION_APPROXIMATION_RADIUS_KM)
            sql_insert_user = """ INSERT INTO users (owner, full_name, real_lat, real_lon, fake_lat, fake_lon)
                       VALUES (?,?,?,?,?,?);"""

            values = (caller_id,  user.full_name, user.location.lat, user.location.lon,
                      fake_location.lat, fake_location.lon)

            self.cur.execute(sql_insert_user, values)
            self.db.commit()
            user_id = self.cur.lastrowid
            return user_id

        except IntegrityError:
            return self.Error(self.Error.Code.USER_ALREADY_EXISTS, f"User with ID '{user.user_id}' already exists.")
        except Exception:
            return self.Error(self.Error.Code.GENERIC, GENERIC_ERROR_MESSAGE)

    def delete_user(self, user_id: str) -> Optional[Error]:
        """
        Удаляет пользовательский профиль, если он существует
        :param user_id: User profile ID
        :return: None
        """
        try:
            sql = "DELETE FROM users WHERE id = ?"
            self.cur.execute(sql, (user_id,))
            self.db.commit()

        except Exception as e:
            print(e)
            return self.Error(self.Error.Code.GENERIC, GENERIC_ERROR_MESSAGE)


