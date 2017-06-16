#!/usr/bin/env python
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

from unittest import TestCase, main
from uuid import uuid4

from canopsis.middleware.core import Middleware
from canopsis.context_graph.manager import ContextGraph
from canopsis.event.manager import Event
from canopsis.linklist.manager import LinklistManager


class CheckManagerTest(TestCase):
    """
    Base class for all check manager tests.
    """

    def setUp(self):
        # Linklist testing storage
        self.manager = LinklistManager()
        self.linklist_storage = Middleware.get_middleware_by_uri(
            'storage-default-testlinklist://'
        )
        self.manager[LinklistManager.LINKLIST_STORAGE] = self.linklist_storage

        # Event testing storage
        self.event = Event()
        self.event_storage = Middleware.get_middleware_by_uri(
            'storage-default-testevent://'
        )
        self.manager.event[Event.EVENT_STORAGE] = self.event_storage

        # ContextGraph testing storage
        self.context_graph = ContextGraph()
        self.entities_storage = Middleware.get_middleware_by_uri(
            'storage-default-testentities://'
        )
        self.manager.context_graph[ContextGraph.ENTITIES_STORAGE] = self.entities_storage

        # Insert default filter
        self.filter_name = 'testlinklist'
        self.filter_id = str(uuid4())
        self.default_filter = {
            '_id': self.filter_id,
            'name': self.filter_name,
            'linklist': ['http://canopsis.org'],
            'mfilter': '{"$and": [{"connector": "fake_connector"}]}'
        }
        self.manager.put(self.default_filter)

        # Insert default entity
        self.entity_id = 'fake_connector/fake_connector_name'
        self.entity = {
            '_id': self.entity_id,
            'type': 'connector',
            'name': 'fake entity',
            'depends': [],
            'impact': [],
            'measurements': [],
            'infos': {}
        }
        try:
            self.manager.context_graph.create_entity(entity=self.entity)  # TODO:upsert
        except:
            pass

        # Default event
        self.event = {
            'source_type': 'connector',
            'connector': 'fake_connector',
            'connector_name': 'fake_connector_name',
            'component': 'c',
            'output': '...',
            'action_url': 'http://gnu.org/',
        }
        # storage.put_element

        # Default links
        self.links = [
            {
                "url": "http://fr.wikipedia.org",
                "category": "procedure",
                "label": "wikipedia"
            }
        ]

    def tearDown(self):
        self.linklist_storage.remove_elements()
        self.entities_storage.remove_elements()

    def linklist_count_equals(self, count):
        result = list(self.manager.find(ids=[self.filter_id]))
        self.assertEqual(len(result), count)


class LinkListTest(CheckManagerTest):
    """
    def test_put(self):

        self.linklist_count_equals(1)

    def test_find(self):
        self.manager.put({
            'name': self.filter_name + '1',
            'linklist': ['http://canopsis.org'],
            'mfilter': '{"$and": [{"connector": "connectorX"}]}'
        })

        self.linklist_count_equals(1)

        result = self.manager.find()
        self.assertGreaterEqual(len(list(result)), 2)

        result = self.manager.find(limit=1)
        self.assertEqual(len(list(result)), 1)

    def test_remove(self):
        self.linklist_count_equals(1)

        self.manager.remove([self.filter_id])

        self.linklist_count_equals(0)
    """
    def test_apply_all_filters(self):
        self.manager.apply_all_filters(entity=self.entity)

        res = self.manager.context_graph.get_entities_by_id(self.entity_id)[0]
        print(res)
        self.assertTrue(LinklistManager.CG_LINKS in res['infos'])

    """
    def test_enrich_from_entity(self):
        self.manager.enrich_from_entity(entity=self.entity, links=self.links)

        res = self.manager.context_graph.get_entities_by_id(self.entity_id)[0]
        self.assertTrue(LinklistManager.CG_LINKS in res['infos'])
        self.assertEqual(res['infos'][LinklistManager.CG_LINKS][0]["label"],
                         "wikipedia")

    def test_enrich_from_event(self):
        self.manager.enrich_from_event(event=self.event)

        res = self.manager.context_graph.get_entities_by_id(self.entity_id)[0]
        self.assertTrue(LinklistManager.CG_LINKS in res['infos'])
        self.assertEqual(res['infos'][LinklistManager.CG_LINKS][0]["url"],
                         "http://gnu.org/")

    def test_get_links_from_event(self):
        # DEPRECATED !
        self.manager.enrich_from_entity(entity=self.entity, links=self.links)

        res = self.manager.get_links_from_event(event=self.event)

        self.assertEqual(res, self.links)
    """

if __name__ == '__main__':
    main()
