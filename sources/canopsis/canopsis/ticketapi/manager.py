#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --------------------------------
# Copyright (c) 2016 "Capensis" [http://www.capensis.com]
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
Ticket Api Config manager.
"""

from __future__ import unicode_literals

from canopsis.common.collection import MongoCollection
from canopsis.common.mongo_store import MongoStore
from canopsis.logger import Logger
from canopsis.models.ticketapi import TicketApi


class TicketApiManager(object):
    """
    Action managment.
    """
    LOG_PATH = 'var/log/ticketapi.log'

    ACTION_COLLECTION = 'default_ticketapi'

    def __init__(self, logger, mongo_collection):
        self.logger = logger
        self.collection = mongo_collection

    @classmethod
    def provide_default_basics(cls):
        """
        Provide logger, config, storages...

        ! Do not use in tests !

        :rtype: Union[logging.Logger,
                      canopsis.common.collection.MongoCollection]
        """
        logger = Logger.get('ticketapi', cls.LOG_PATH)
        store = MongoStore.get_default()
        collection = store.get_collection(name=cls.ACTION_COLLECTION)
        mongo_collection = MongoCollection(collection)

        return (logger, mongo_collection)

    def get_id(self, id_):
        """
        Helper to find just an object from his _id.
        """
        return self.get(query={TicketApi._ID: id_})

    def get(self, query):
        """
        Read a ticketapi config.

        :param str query: a ticketapi config query string
        :rtype: TicektApi or None
        """
        record = self.collection.find_one(query=query)
        if not record:
            return

        ticket_api = TicketApi(**TicketApi.convert_keys(record))
        return ticket_api

    def create(self, ticketapi):
        """
        Create a ticketapi config.

        :param dict ticketapi: a ticketapi config as a dict
        :rtype: bool
        """
        id_ = self.collection.insert(document=ticketapi)

        return id_ is not None

    def update_id(self, id_, ticketapi):
        """
        Update a ticketapi config.

        :param str id_: a ticketapi config _id
        :param dict ticketapi: a ticketapi config as a dict
        :rtype: bool
        """
        query = {TicketApi._ID: id_}
        resp = self.collection.update(query=query, document=ticketapi)

        return self.collection.is_successfull(resp)

    def delete_id(self, id_):
        """
        Delete a ticketapi config.

        :param str id_: a ticketapi config _id
        :rtype: bool
        """
        query = {TicketApi._ID: id_}
        resp = self.collection.remove(query=query)

        return self.collection.is_successfull(resp)
