from typing import Any

import flask
from flask import abort, g, request, url_for, Response, Request
import os
from db import create_db, connect_db, DataBase, Role
from schema import *


"""
В процессе разработки данного проекта были реализованы следующие добавления к исходному ТЗ, а именно:

1.  Было введено понятие - Пользователь API / Сервиса. Что бы сервис мог различать, кто к нему обращается.
    (Админ или нет). Аунтефикация пользователей не требовалось ТЗ. 
    Для простоты и читаемости  реализации аунтефкация не реализовывалась,
    но может быть добавлена в будущем любым требуемым способом.
    А пока ID пользователя сервиса передается в заголовке HTTP запроса. 

2.  Создатель профиля, при обращении, получает реальные данные. 
    Это часть не была конкретно указана в ТЗ, но кажется логичным, что пользователь профиля
    должен получать ориигинальные данные при запросе. 
    Соответственно, в дополнение к роли Админ, была реализована роль (Owner) "создатель профиля".
    
3.  Для реализации тестов добавлен метод удаления профиля. Его может выполнять либо Админ, либо создатель профиля.

4.  Так же Для реализации тестов  добавлен метод выбора всех записей по имени либо по создателю профиля.
    Для дальнейшего удаления из базы данных.
"""

DEBUG = True

app = flask.Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(DATABASE=os.path.join(app.root_path, 'users.db')))
db_path = app.config['DATABASE']

create_db()


def get_caller_id(request: Request) -> str:
    """
    Extracts service / API user id from request

    :param request: Received Request
    :return: API user id
    """
    caller_id = request.headers.get(HEADER_CALLER_ID)
    if caller_id is None:
        abort(400, f'Missing required header {HEADER_CALLER_ID}')
    return caller_id


def abort_on_db_error(result: Any) -> Any:
    """
    Транслирует ошибки,которые возвращаются с запросов к базе данных
    в исключение с HTTP status code and response message

    :param result: Result from DB class method
    :return: Input result unless it's a DB Error
    """
    if isinstance(result,  DataBase.Error):
        if result.code == DataBase.Error.Code.USER_ALREADY_EXISTS:
            abort(409, result.message)
        if result.code == DataBase.Error.Code.USER_NOT_FOUND:
            abort(404, result.message)
        abort(500, result.message)
    else:
        return result


@app.route('/')
def index():
    response = Response(json.dumps('Safe Location Service v1.0'))
    response.headers[HEADER_CONTENT_TYPE] = JSON_FORMAT
    return response


@app.route('/user/<user_id>', methods=['GET'])
def get_user(user_id) -> Response:
    caller_id = get_caller_id(request)
    dbase = DataBase(get_db())

    # Only admin or profile creator receive real location
    role = abort_on_db_error(dbase.get_caller_role(user_id, caller_id))
    real_location = role == Role.OWNER or role == Role.ADMIN

    # Read and return User profile
    user = abort_on_db_error(dbase.get_user(user_id, be_real=real_location))
    response = Response(user.serialize())
    response.headers[HEADER_CONTENT_TYPE] = JSON_FORMAT

    return response


@app.route('/user/', methods=['GET'])
def get_users():
    # Return list of user profile IDs matching query parameters filter (optional)
    dbase = DataBase(get_db())
    response = Response(json.dumps(dbase.get_users_id(request.args.get('owner'), request.args.get('name'))))
    response.headers[HEADER_CONTENT_TYPE] = JSON_FORMAT
    return response


@app.route('/user', methods=['POST'])
def add_user() -> Response:
    caller_id = get_caller_id(request)
    new_user = User(**json.loads(request.data.decode()))
    dbase = DataBase(get_db())
    user_id = abort_on_db_error(dbase.save_user(new_user, caller_id))

    # Per HTTP standard return Location header with newly created resource (profile) URL
    return Response(status=201, headers={'Location': url_for('get_user', user_id=user_id, _external=True)})


@app.route('/user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    caller_id = get_caller_id(request)
    dbase = DataBase(get_db())

    # Only admin or profile creator can delete profile
    role = abort_on_db_error(dbase.get_caller_role(user_id, caller_id))
    if role == Role.OTHER:
        abort(403)

    abort_on_db_error(dbase.delete_user(user_id))
    return 'ok'


def get_db():
    # Caching db instance between API calls
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'link_db'):
        g.link_db.close()


if __name__ == '__main__':
    app.run()
