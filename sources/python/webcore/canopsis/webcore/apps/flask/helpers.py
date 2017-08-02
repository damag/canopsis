import flask_restful
from flask import session, request
from flask_restful import Resource as FlaskResource

def authenticate(func):
    def wrapper(*args, **kwargs):
        if session.get('authenticated', False):
            return func(*args, **kwargs)

        flask_restful.abort(401)

    return wrapper

class Resource(FlaskResource):

    resource_routes = []
    method_decorators = [authenticate]

    @classmethod
    def init(cls, app, api):
        cls._app = app
        cls._api = api
        cls.add_resources()

    @classmethod
    def add_resources(cls):
        """
        Calls add_resource on api for every route defined in cls._routes.
        """
        cls._api.add_resource(cls, *cls.resource_routes)