# -*- coding: utf-8 -*-
# --------------------------------
# Copyright (c) 2017 "Capensis" [http://www.capensis.com]
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
from six import string_types

from datetime import timedelta
import json
from uuid import uuid4 as uuid


class AlarmFilters(object):
    """
        Access to a set of alarm filters.

        TODO: link to the global logger
    """

    def __init__(self, storage, alarm_storage):
        self.storage = storage  # A alarmfilter storage
        self.alarm_storage = alarm_storage  # An alarm storage

    def create_filter(self, element):
        """
        Create the selected alarm-filter.

        :param element: the filter informations
        :type element: dict
        :rtype: <AlarmFilter>
        """
        # Validating element minimal structure
        for key in [AlarmFilter.LIMIT, AlarmFilter.CONDITION,
                    AlarmFilter.TASKS, AlarmFilter.FILTER]:
            if key not in element:
                print('Missing key {} to create the filter'.foramt(key))
                return None

        af = AlarmFilter(element=element,
                         storage=self.storage,
                         alarm_storage=self.alarm_storage)

        return af

    def delete_filter(self, entity_id):
        """
        Delete the selected alarm filter.

        :param entity_id: the desired Entity ID
        :type entity_id: str
        :rtype: dict
        """
        return self.storage.remove_elements(ids=[entity_id])

    def update_filter(self, filter_id, key, value):
        """
        Update an alarm filter value.

        :param filter_id: the desired filter_id
        :type filter_id: str
        :param key: the key to update
        :type key: str
        :param value: the value to put
        :type value: str
        :rtype: <AlarmFilter>
        """
        query = {'_id': filter_id}
        element = list(self.storage.get_elements(query=query))
        if element is None or len(element) <= 0:
            return None

        lifter = self.create_filter(element.pop())
        lifter[key] = value
        lifter.save()

        return lifter

    def get_filter(self, alarmfilter_id):
        """
        Retreive the list of filters linked to a specific alarm.

        :param alarmfilter_id: the desired alarmfilter_id
        :type alarmfilter_id: str
        :rtype: list or None
        """
        query = {
            AlarmFilter.UID: alarmfilter_id
        }
        all_filters = list(self.storage.get_elements(query=query))

        return [AlarmFilter(fil) for fil in all_filters]

    def get_filters(self):
        """
        Retreive the list of all filters with their alarm.

        :rtype: [(AlarmFilter, Alarm)]
        """
        results = []

        all_filters = list(self.storage.get_elements())
        for yummy in all_filters:
            mfilter = yummy[AlarmFilter.FILTER]

            # Instanciate each AlarmFilter on this alarm
            new_filter = self.create_filter(yummy)
            try:
                query = json.loads(mfilter)
            except:
                print('Cannot parse mfilter: {}'.format(new_filter))
                continue

            # Associate a filter with his matching alarm
            for alarm in list(self.alarm_storage.get_elements(query=query)):
                if new_filter is not None:
                    results.append((new_filter, alarm))

        return results

    def __repr__(self):
        return "AlarmFilters of {}".format(self.storage)


class AlarmFilter(object):
    """
        An alarm filter.

        filter = {
            '_id': 'deadbeef',
            'entity_filter': '{"connector":{"$eq":"connector"}}'
            'limit': timedelta(seconds=30),
            'condition': '{"connector":{"$eq":"connector_value"}}'
            'tasks': ['alerts.systemaction.status_increase'],
            'output_format': '{old} -- message {foo}',
            'repeat': 1
        }
    """
    UID = '_id'
    LIMIT = 'limit'
    CONDITION = 'condition'
    FILTER = 'entity_filter'
    TASKS = 'tasks'
    FORMAT = 'output_format'
    REPEAT = 'repeat'

    def __init__(self, element, storage=None, alarm_storage=None):
        self.element = element  # has persisted in the db
        self.storage = storage
        self.alarm_storage = alarm_storage

        if not element.get(self.UID, False):
            element[self.UID] = str(uuid())

        # Map and converter element parts as attribute
        if self.REPEAT not in self.element:
            self[self.REPEAT] = 1  # default value
        for k, v in self.element.items():
            self[k] = v

    def __setitem__(self, key, item):
        value = item
        # Limit conversion
        if key == self.LIMIT and isinstance(item, (int, float)):
            value = timedelta(seconds=item)
        # Condition conversion
        elif key == self.CONDITION and isinstance(item, string_types):
            try:
                value = json.loads(item)
            except:
                print('Cannot parse condition item {}'.format(item))
                return

        # Dict serialization conversion
        if key in [self.CONDITION, self.FILTER] and isinstance(item, dict):
            item = json.dumps(item)

        setattr(self, key, value)
        self.element[key] = item

    def __getitem__(self, key):
        if hasattr(self, key):
            return getattr(self, key)

    def check_alarm(self, alarm):
        """
        Check if a filter is valide for a specified alarm.

        :param alarm: An alarm
        :type alarm: dict
        :rtype: bool
        """
        alarm_id = alarm[self.alarm_storage.DATA_ID]
        query = {
            '$and': [
                self[self.CONDITION],
                {self.alarm_storage.Key.DATA_ID: {'$eq': alarm_id}}
            ]
        }
        result = list(self.alarm_storage.find_elements(query))

        return len(result) > 0

    def output(self, old=''):
        """
        Modifiy an output message according to the filter parameters.

        :param old: the old output message, if needed in the format
        :type old': str
        :rtype: str
        """
        if self[self.FORMAT] is not None:
            return self[self.FORMAT].format(old=old)

        return old

    def save(self):
        """
        Save this filter into the db.

        :raises Exception: when storage is not avalaible
        """
        if self.storage is not None:
            return self.storage._backend.save(self.element)

        raise Exception("No storage available to save into !")

    def serialize(self):
        """
        Return a printable element (especially for json serialization)
        """
        return self.element

    def __repr__(self):
        return "AlarmFilter: {}".format(self.element)
