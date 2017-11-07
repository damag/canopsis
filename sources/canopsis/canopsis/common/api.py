#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from requests.exceptions import HTTPError


class GenericAPI(object):
    """
    Generic wrapper to perform actions on an API (with authent).
    """

    def __init__(self, api_user, api_passw):
        """
        :param str api_user: the user to connect with
        :param str api_passw: the password to connect with
        """
        self._session = requests.Session()
        self._session.auth = (api_user, api_passw)
        self._session.headers = {
            'Content-Type': 'application/json'
        }

    def _action(self, req):
        try:
            j = req.json()
        except Exception:
            req.raise_for_status()
            j = {}

        if 'error' in j:
            error = j.get('error')
            raise HTTPError('{}: {}'.format(error['message'], error))

        try:
            req.raise_for_status()
        except Exception as e:
            raise HTTPError("{}: {}".format(e, j))

        return j

    def _build_url(self, service):
        """
        Build the final url from service name.

        :param str service: the desired service name
        """
        raise NotImplementedError()

    def _get(self, service, params={}):
        """
        Do a GET on the webservice.

        :param str service: the service name
        :param dict params: parameters to put with the request
        """
        req = self._session.get(self._build_url(service), params=params)
        return self._action(req)

    def _post(self, service, data={}):
        """
        Do a POST on the webservice.

        :param str service: the service name
        :param dict params: parameters to put with the request (body)
        """
        req = self._session.post(self._build_url(service), data=data)
        return self._action(req)

    def _put(self, service, data={}):
        """
        Do a PUT on the webservice.

        :param str service: the service name
        :param dict params: parameters to put with the request (body)
        """
        req = self._session.put(self._build_url(service), data=data)
        return self._action(req)

    def _delete(self, service):
        """
        Do a DELETE on the webservice.

        :param str service: the service name
        """
        req = self._session.delete(self._build_url(service))
        return self._action(req)
