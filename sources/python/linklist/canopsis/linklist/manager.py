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

#from functools import wraps
import json
from six import string_types

from canopsis.configuration.configurable.decorator import (
    conf_paths, add_category)
from canopsis.context_graph.manager import ContextGraph
from canopsis.event.manager import Event
from canopsis.middleware.registry import MiddlewareRegistry

CONF_PATH = 'linklist/linklist.conf'
CATEGORY = 'LINKLIST'

"""
def update_linklist(f):
    ""Recalculate all linklist filter, after an entity update for example""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        retval = f(*args, **kwargs)

        # Find the processed entity
        if 'entity' in kwargs:
            new_entity = kwargs['entity']
        elif len(args) == 1:
            new_entity = args[0]
        else:
            return retval

        return LinklistManager.apply_all_filters(new_entity)

    return decorated_function
"""


@conf_paths(CONF_PATH)
@add_category(CATEGORY)
class LinklistManager(MiddlewareRegistry):
    """
    Manage linklist information in Canopsis.
    """

    LINKLIST_STORAGE = 'linklist_storage'  #: linklist storage name
    CG_LINKS = 'filterlink'  # field name for linklist in entities

    def __init__(self, linklist_storage=None, *args, **kwargs):
        super(LinklistManager, self).__init__(*args, **kwargs)

        self.context_graph = ContextGraph()
        self.event = Event()

        if linklist_storage is not None:
            self[LinklistManager.CONFIG_STORAGE] = linklist_storage

    def find(self, limit=None, skip=None, ids=None, sort=None,
             with_count=False, _filter={}):
        """
        Find linklist documents in db.

        :param ids: id(s) for document to search. All documents by default.
        :type ids: str or list
        :param int limit: maximum record fetched at once.
        :param int skip: ordinal number where selection should start.
        :param bool with_count: compute selection count when True.
        :rtype: list
        """

        result = self[LinklistManager.LINKLIST_STORAGE].get_elements(
            ids=ids,
            skip=skip,
            sort=sort,
            limit=limit,
            query=_filter,
            with_count=with_count
        )

        return list(result)

    def put(self, document):
        """
        Put a linklist documents in db.

        :param document: document to put
        :type document: dict
        :return: put result
        :rtype: dict
        """

        # If its a string, converting mfilter to dict
        mfilter = document['mfilter']
        if isinstance(mfilter, string_types):
            try:
                document['mfilter'] = json.loads(mfilter)
            except:
                raise ValueError('Cannot parse mfilter item "{}"'.format(mfilter))

        return (self[LinklistManager.LINKLIST_STORAGE]
                .put_element(element=document))

    def remove(self, ids):
        """
        Remove a linklist documents in db.

        :param ids: identifier for documents to remove
        :type ids: list
        """

        self[LinklistManager.LINKLIST_STORAGE].remove_elements(ids=ids)

    """
    def get_entity_from_filter(self, filter_):
        ""
        Return all entities linked matched by an event filter.

        :rtype: list
        ""
        try:
            l_filter = json.loads(filter_)
        except Exception as e:
            self.logger.error(
                'Unable to parse mfilter, query aborted {}'.format(e)
            )
            return []

        result = []
        for event in self.event.find(query=l_filter):
            result.append(self.context_graph.get_id(event))

        return result
    """

    def apply_all_filters(self, entity):
        """
        Find and apply linklist filters on an entity.

        :param entity: the entity to enrich
        :type entity: dict
        :return: nothing
        """
        # TODO : Decorate create/update/delete entity action with this function
        for linklist in self.find():
            print(linklist)
            name = linklist.get('name', None)
            l_filter = linklist.get('mfilter', None)
            if name is None or l_filter is None:
                self.logger.info('Cannot proceed linklist {}'.format(linklist))
                continue

            self.logger.debug('Proceeding linklist {}'.format(name))

            # Enrich the entity if it match the filter
            #if self.event.check_entity(entity=entity, filter_=l_filter):
            #    l_list = linklist.get(self.CG_LINKS, [])
            #    print(l_list)
            #    self.enrich_from_entity(entity=entity, links=l_list)

            l_list = linklist.get(self.CG_LINKS, [])
            # Get events from this filter
            print(l_filter)
            print(type(l_filter))
            for event in self.event.find(query=l_filter):
                print(event)
                ev_entity = ContextGraph.get_id(event=event)
                print(ev_entity)
                if entity['_id'] == ev_entity['_id']:
                    self.enrich_from_entity(entity=entity, links=l_list)

    def enrich_from_entity(self, entity, links, forced=False):
        """
        Enrich an entity with a list of links.

        :param entity: the entity to enrich [sic]
        :type entity: dict
        :param links: a list of link dict
        :type links: list(dict)
        :param forced: is links will NOT be purged on the next enrichment ?
        :type forced: bool
        :rtype: bool
        """
        purged_links = []
        # Remove not forced links from actual linklist
        for links_ in entity[ContextGraph.INFOS].get(self.CG_LINKS, []):
            if links_.get('forced', False):
                purged_links.append(links_)

        # Add a flag for forced links
        if forced:
            for link in links:
                link['forced'] = forced

        # Merge purged linklist with the desired one
        merge = purged_links + [x for x in links if x not in purged_links]
        # TODO: duplication if a link is forced and not forced at the same time ?

        entity[ContextGraph.INFOS][self.CG_LINKS] = merge
        self.logger.debug('enrich entity "{}" with links: {}'
                          .format(entity['name'], merge))
        self.context_graph.update_entity(entity)

    def enrich_from_event(self, event):
        """
        Enrich the context of an event with an url, if desired.
        Specifically called from process.eventprocessing()

        :param event: the arrived event
        :type event: dict
        """
        entity_id = self.context_graph.get_id(event)
        entities = self.context_graph.get_entities_by_id(entity_id)
        links = [{
            'name': 'action url',
            'url': event['action_url'],
            'category': 'procedure'
        }]  # TODO : get real datas !!
        for entity in entities:
            self.logger.debug('enrich from event entity "{}"'.format(entity))
            self.enrich_from_entity(entity=entity, links=links, forced=True)

    def get_links_from_event(self, event):
        """
        Return all links of an event.
        TEMPORARY! AND DEPRECATED!
        linklists should be returned with the context (see infos field)

        :param event: the targeted event
        :return: a list of links (as dict)
        :rtype: list
        """
        entity_id = self.context_graph.get_id(event)
        entity = self.context_graph.get_entities_by_id(entity_id).pop()

        return entity[ContextGraph.INFOS].get(self.CG_LINKS, None)

