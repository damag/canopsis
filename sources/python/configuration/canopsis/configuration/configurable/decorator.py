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

from . import Configurable
from ..parameters import Category


def conf_paths(*conf_paths):
    """
    Configurable decorator which adds conf_path paths to a Configurable.

    :param paths: conf resource pathes to add to a Configurable
    :type paths: list of str

    Example:
    >>> conf_paths('test0', 'test1')(Configurable)().conf_paths[:-2]
    ['test0', 'test1']
    """

    def _get_conf_paths(self, *args, **kwargs):
        # get super result and append conf_paths
        result = super(type(self), self)._get_conf_paths()
        result += conf_paths

        return result

    def add_conf_paths(cls):
        # add _get_conf_paths method to configurable classes
        if issubclass(cls, Configurable):
            cls._get_conf_paths = _get_conf_paths

        else:
            raise Configurable.Error(
                "class {0} is not a Configurable class".format(cls))

        return cls

    return add_conf_paths


def add_category(name, unified=True, content=None):
    """
    Add a category to a configurable configuration.

    :param name: category name
    :type name: str

    :param unified: if True (by default), the new category is unified from
    previous conf
    :type unified: bool

    :param content: category or list of parameters to add to the new category
    :type content: Category or list(Parameter)
    """

    def _conf(self, *args, **kwargs):

        result = super(type(self), self)._conf(*args, **kwargs)

        if unified:
            result.add_unified_category(name=name, new_content=content)
        else:
            category = Category(name=name)
            if content is not None:
                category += content
            result += category

        return result

    def add_conf(cls):

        if issubclass(cls, Configurable):
            cls._conf = _conf

        else:
            raise Configurable.Error(
                "class {0} is not a Configurable class".format(cls))

        return cls

    return add_conf
