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

"""
Python utility library.
"""

from importlib import import_module

from inspect import ismodule

from collections import Iterable

from sys import version as PYVER


def resolve_element(path):
    """
    Get element reference from input full path element.

    :limitations: does not resolve class method.

    :param path: full path to a python element.
        Examples:
            - __builtin__.open
            - canopsis.common.utils.resolve_element
    :type path: str

    :return: python object which is accessible thourgh input path.
    :rtype: object
    """

    result = None

    if path:

        components = path.split('.')
        index = 0
        components_len = len(components)

        module_name = components[0]

        # try to import the first component name
        try:
            result = import_module(module_name)
        except ImportError:
            pass

        if result is not None:

            if components_len > 1:

                index = 1

                # try to import all sub-modules/packages
                try:  # check if name is defined from an external module
                    # find the right module

                    while index < components_len:
                        module_name = '%s.%s' % (
                            module_name, components[index])
                        result = import_module(module_name)
                        index += 1

                except ImportError:
                    # path sub-module content
                    try:

                        while index < components_len:
                            result = getattr(result, components[index])
                            index += 1

                    except AttributeError:
                        raise ImportError(
                            'Wrong path %s at %s' % (path, components[:index]))

        else:  # get relative object from current module
            raise ImportError('Does not handle relative path')

    return result


def path(element):
    """
    Get full path of a given element.

    Do the inverse of resolve_element

    :param element: must be directly defined into a module or a package
    :type element: object
    """

    if not hasattr(element, '__name__'):
        raise AttributeError(
            'element %s must have the attribute __name__' % element)

    result = element.__name__ if ismodule(element) else \
        '%s.%s' % (element.__module__, element.__name__)

    return result


def isiterable(element, is_str=True):
    """
    Check whatever or not if input element is an iterable.

    :param is_str: check if element is also a str
    :type is_str: bool
    """
    result = isinstance(element, Iterable) \
        and (is_str or not isinstance(element, basestring))

    return result


def isunicode(s):
    """
    Check if string is unicode.

    :param s: string to check
    :type s: basestring

    :return: True if unicode or Python3, False otherwise
    """

    if PYVER < '3':
        return isinstance(s, unicode)

    else:
        return True


def force_unicode(s):
    """
    Convert string to unicode.

    :param s: string to convert
    :type s: basestring

    :return: unicode (or the same string if Python3)
    """

    result = s

    if PYVER < '3':
        if isinstance(s, basestring):
            if not isinstance(s, unicode):
                result = s.decode()
        else:
            raise TypeError('Expecting a string as argument')

    return result


def force_iterable(value, iterable=list):
    """
    Convert a value into an iterable if it is not.

    :param value: value to convert
    :type value: object

    :param iterable: iterable type to apply (default: list)
    :type iterable: type
    """

    result = value

    if not isiterable(value, is_str=False):
        result = [value]
        result = iterable(result)

    else:
        result = iterable(value)

    return result
