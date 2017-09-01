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

from canopsis.middleware.core import Middleware

from canopsis.confng import Configuration, Ini

class Event(object):
    """
    Manage events in Canopsis
    """

    CONF_PATH = 'etc/event/event.conf'
    CONF_CATEGORY = 'EVENT'
    DEFAULT_EVENT_STORAGE_URI = 'mongodb-default-event://'

    default_state = 0
    EVENT_STORAGE = 'event_storage'

    states_str = {
        0: 'info',
        1: 'minor',
        2: 'major',
        3: 'critical'
    }

    def __init__(self, config=None, event_storage=None):
        super(Event, self).__init__()
        if config is None:
            self.config = Configuration.load(self.CONF_PATH, Ini)
        else:
            self.config = config

        self.config_event = self.config.get(self.CONF_CATEGORY, {})

        if event_storage is None:
            event_storage_uri = self.config_event.get(
                'event_storage_uri', self.DEFAULT_EVENT_STORAGE_URI)
            self.event_storage = Middleware.get_middleware_by_uri(event_storage_uri)
        else:
            self.event_storage = event_storage

    @staticmethod
    def get_rk(event):
        rk = '{0}.{1}.{2}.{3}.{4}'.format(
            event['connector'],
            event['connector_name'],
            event['event_type'],
            event['source_type'],
            event['component']
        )

        if event['source_type'] == 'resource':
            rk = '{0}.{1}'.format(rk, event['resource'])

        return rk

    def is_ack(self, event):
        """
        Define if an event is in ack state
        :param: event is the event to test
        """
        return event.get('ack', {}).get('isAck', False)

    def is_alert(self, state):
        """
            Define if a state is in alert
            allow progressive alert definition migration
        """
        result = None
        if state == 0:
            result = False
        if state in (1, 2, 3):
            result = True
        return result

    def get_last_state(self, event):
        """
            Retrieve last event state from database
            This is a subset information of a find query focused on state
        """

        existing_event = self.get(Event.get_rk(event), {})
        return existing_event.get('state', self.default_state)

    def get(self, rk, projection=None, default=None):
        result = self.find(query={'rk': rk}, limit=1, projection=projection)

        return result[0] if len(result) else default

    def find(
        self,
        limit=None,
        skip=None,
        ids=None,
        sort=None,
        with_count=False,
        query={},
        projection=None
    ):

        """
        Retrieve information from data sources

        :param ids: an id list for document to search
        :param limit: maximum record fetched at once
        :param skip: ordinal number where selection should start
        :param with_count: compute selection count when True
        """

        result = self.event_storage.get_elements(
            ids=ids,
            skip=skip,
            sort=sort,
            limit=limit,
            query=query,
            with_count=with_count,
            projection=projection
        )
        return result
