# -*- coding: utf-8 -*-
# --------------------------------
# Copyright (c) 2015 "Capensis" [http://www.capensis.com]
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

from __future__ import unicode_literals

from canopsis.context_graph.manager import ContextGraph
from canopsis.logger import Logger
from canopsis.middleware.core import Middleware


class Entitylink(object):

    """
    Manage entity link information in Canopsis
    """

    LOG_PATH = 'var/log/linklist.log'
    ENTITYLINK_STORAGE_URI = 'mongodb-default-entitylink://'

    def __init__(self, logger, storage, context_graph):
        self.logger = logger
        self.entitylink_storage = storage
        self.context = context_graph

    @classmethod
    def provide_default_basics(cls):
        """
        Provide logger, config, storages...

        ! Do not use in tests !

        :rtype: Union[logging.Logger,
                      canopsis.storage.core.Storage,
                      canopsis.context_graph.manager.ContextGraph]
        """
        logger = Logger.get('linklist', cls.LOG_PATH)
        entitylink_storage = Middleware.get_middleware_by_uri(
            cls.ENTITYLINK_STORAGE_URI
        )
        context = ContextGraph(logger)

        return (logger, entitylink_storage, context)

    def get_or_create_from_event(self, event):
        """
        Find or create an entity link document.

        :param event: an event that may have an entity link stored
            if not, an entity link entry is created and is returned
        :type event:
        """
        entity_list = list(self.get_links_from_event(event))

        if len(entity_list) > 0:
            return entity_list[0]

        _id = self.get_id_from_event(event)
        self.put(_id, {
            'computed_links': [],
            'event_links': []
        })

        entity_list = list(self.get_links_from_event(event))

        if len(entity_list) > 0:
            return entity_list[0]

    def get_id_from_event(self, event):
        """
        Find a context id from an event.

        :param event: an event to search a context id from
        :type event:
        """
        entity_id = self.context.get_id(event)
        entity = self.context.get_entities_by_id(entity_id)
        if len(entity) <= 0:
            return None

        entity = entity[0]

        encoded_entity = {}
        for k, v in entity.items():
            try:
                k = k.encode('utf-8')
            except UnicodeError:
                pass
            try:
                v = v.encode('utf-8')
            except (UnicodeError, TypeError, AttributeError):
                pass
            encoded_entity[k] = v

        return encoded_entity["_id"]

    def get_links_from_event(self, event):
        """
        Try to find an entity link from a given event.

        :param event: a canopsis event
        """

        entity_id = self.get_id_from_event(event)
        return self.find(ids=[entity_id])

    def find(
        self,
        limit=None,
        skip=None,
        ids=None,
        sort=None,
        with_count=False,
        _filter={},
    ):
        """
        Retrieve information from data sources.

        :param ids: an id list for document to search
        :param limit: maximum record fetched at once
        :param skip: ordinal number where selection should start
        :param with_count: compute selection count when True
        """

        result = self.entitylink_storage.get_elements(
            ids=ids,
            skip=skip,
            sort=sort,
            limit=limit,
            query=_filter,
            with_count=with_count
        )
        return result

    def put(self, _id, document, cache=False):
        """
        Persistance layer for upsert operations.

        :param _id: entity id
        :param document: contains link information for entities
        """

        self.entitylink_storage.put_element(
            _id=_id, element=document, cache=cache
        )

    def remove(self, ids):
        """
        Remove fields persisted in a default storage.

        :param element_id: identifier for the document to remove
        """

        self.entitylink_storage.remove_elements(ids=ids)