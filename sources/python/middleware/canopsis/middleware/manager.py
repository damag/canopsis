# -*- coding: utf-8 -*-
#--------------------------------
# Copyright (c) 2014 "Capensis" [http://www.capensis.com]
#
# This file is part of Canopsis.
#
# Canopsis is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Canopsis is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Canopsis.  If not, see <http://www.gnu.org/licenses/>.
# ---------------------------------

from urlparse import urlparse

from canopsis.configuration import Configurable, Parameter, Configuration
from .middleware import Middleware


class Manager(Configurable):
    """
    Manages middlewares.

    Attributes are related to middlewares where the data_scope corresponds to
    attribute names.

    Middleware instances can be shared globally in the same processus.
    """

    CONF_FILE = 'middleware/manager.conf'

    SHARED = 'shared'
    SCOPE_SHARING = 'scope_sharing'
    AUTO_CONNECT = 'auto_connect'

    CATEGORY = 'MANAGER'

    # middleware attribute suffix
    MIDDLEWARE_SUFFIX = '_middleware'

    # shared dictionary of {protocol, {Manager class, data_scope}}
    __MIDDLEWARES_BY_MANAGERS__ = {}

    class Error(Exception):
        """
        Handle Manager errors.
        """
        pass

    def __init__(
        self, shared=True, scope_sharing=False, auto_connect=True,
        *args, **kwargs
    ):

        super(Manager, self).__init__(*args, **kwargs)

        self.auto_connect = auto_connect
        self.shared = shared
        self.scope_sharing = scope_sharing

    @property
    def shared(self):
        return self._shared

    @shared.setter
    def shared(self, value):
        self._shared = value

    @property
    def scope_sharing(self):
        return self._scope_sharing

    @scope_sharing.setter
    def scope_sharing(self, value):
        self._scope_sharing = value

    @property
    def auto_connect(self):
        return self._auto_connect

    @auto_connect.setter
    def auto_connect(self, value):
        self._auto_connect = value

    def get_middleware(
        self,
        uri, data_scope=None, auto_connect=None,
        shared=None, scope_sharing=None,
        *args, **kwargs
    ):
        """
        Load a middleware related to input uri.

        If shared, the result instance is shared among same middleware type
        and self class type.

        :param uri: middleware ui
        :type uri: str

        :param auto_connect: middleware auto_connect parameter
        :type auto_connect: bool

        :param shared: if True, the result is a shared middleware instance
            among managers of the same class. If None, use self.shared.
        :type shared: bool

        :param scope_sharing: scope sharing
        :type scope_sharing: bool

        :return: middleware instance corresponding to input uri and data_scope.
        :rtype: Middleware
        """

        result = None

        if auto_connect is None:
            auto_connect = self.auto_connect

        if shared:
            parsed_uri = urlparse(uri)

            protocol = parsed_uri.scheme

            if not protocol:
                raise Manager.Error('uri %s must have a protocol' % uri)

            managers = Manager.__MIDDLEWARES_BY_MANAGERS__.setdefault(
                protocol, {})

            manager = managers.setdefault(scope_sharing, {})

            cls = manager.setdefault(
                data_scope, Middleware.resolve_middleware(uri))

        else:

            cls = Middleware.resolve_middleware(uri)

        result = cls(uri=uri, data_scope=data_scope, auto_connect=auto_connect)

        return result

    def _get_conf_files(self, *args, **kwargs):

        result = super(Manager, self)._get_conf_files(*args, **kwargs)

        result.append(Manager.CONF_FILE)

        return result

    def _conf(self, *args, **kwargs):

        result = super(Manager, self)._conf(*args, **kwargs)

        result.add_unified_category(
            name=Manager.CATEGORY,
            new_content=(
                Parameter(Manager.SHARED, self.shared, parser=Parameter.bool),
                Parameter(Manager.SCOPE_SHARING, self.scope_sharing),
                Parameter(Manager.AUTO_CONNECT, self.auto_connect)))

        return result

    def _configure(self, unified_conf, *args, **kwargs):

        super(Manager, self)._configure(
            unified_conf=unified_conf, *args, **kwargs)

        # set shared
        self._update_property(
            unified_conf=unified_conf, param_name=Manager.SHARED)
        self._update_property(
            unified_conf=unified_conf, param_name=Manager.SCOPE_SHARING)
        self._update_property(
            unified_conf=unified_conf, param_name=Manager.AUTO_CONNECT)

        values = unified_conf[Configuration.VALUES]

        # set all middlewares which ends with Manager.MIDDLEWARE_SUFFIX
        for parameter in values:
            if parameter.name.endswith(Manager.MIDDLEWARE_SUFFIX):
                data_scope = parameter.name[:Manager.MIDDLEWARE_SUFFIX]
                middleware = Middleware.resolve_middleware(
                    uri=parameter.value, data_scope=data_scope)
                parameter._value = middleware
                self._update_property(
                    unified_conf=unified_conf, param_name=parameter.name,
                    public=True)