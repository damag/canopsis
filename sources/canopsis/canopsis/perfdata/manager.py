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

"""
Perfdata manager.

Handle basic operations on series and metrics data.
"""

from __future__ import unicode_literals
from numbers import Number
from time import time

from canopsis.common.init import basestring
from canopsis.middleware.core import Middleware
from canopsis.monitoring.parser import PerfDataParser
from canopsis.timeserie.timewindow import get_offset_timewindow, TimeWindow
from canopsis.context_graph.manager import ContextGraph
from canopsis.logger import Logger

SLIDING_TIME = 'sliding_time'
SLIDING_TIME_UPPER_BOUND = 365 * 86400 * 3


class PerfData(object):
    """Dedicated to access to perfdata (via periodical and timed stores)."""

    DEFAULT_PERFDATA_STORAGE_URI = 'influxdb-timed-perfdata://'
    PERFDATA_STORAGE = 'perfdata_storage'
    CONTEXT_MANAGER = 'context'

    @property
    def context(self):
        """Return the context graph manager
        :rtype: an instance of the context graph manager"""

        return self.context_manager

    @classmethod
    def provide_default_basics(cls):
        """
        Provide logger, context manager and perfdata storage.

        Do not use in tests.

        :rtype: Union[logging.Logger, ContextGraph, canopsis.storage.core.Storage]
        """
        perfdata_storage = Middleware.get_middleware_by_uri(
            cls.DEFAULT_PERFDATA_STORAGE_URI)
        logger = Logger.get('perfdatamanager', 'var/log/perfdatamanager.log')
        context_manager = ContextGraph(logger)

        return logger, context_manager, perfdata_storage

    def __init__(
            self, logger, context_manager, perfdata_storage,
            *args, **kwargs
    ):

        super(PerfData, self).__init__(*args, **kwargs)
        self.perfdata_storage = perfdata_storage
        self.context_manager = context_manager
        self.logger = logger

    @staticmethod
    def _metric_id_tags(data_id):
        """
        Convert a metric id to a measurement name.

        :param str data_id: = /metric/connector/connector_name/component/resource/perf_metric
        :rtype: str
        """
        _, _, conn, conn_name, comp, res, perf_m = data_id.split('/')

        return '{}/{}'.format(res, comp)

    @staticmethod
    def _data_id_tags(metric_id, meta=None, event=None):
        """
        Return the metric and the associated tags.

        :param str metric_id: the metric id
        :param dict meta: ???
        :param event: event use to generate the eid
        :rtype : a tuple
        :return: the data id (the metric_id parameters untouched)
        and tags
        """

        if event is None:
            _, _, conn, conn_name, comp, res, perf_m = metric_id.split('/')
            event = {
                'connector': conn,
                'connector_name': conn_name,
                'component': comp,
                'resource': res,
                'perf_metric': perf_m
            }

        tags = {} if meta is None else meta.copy()

        entity = {}

        eid = '/metric/{0}/{1}/{2}/{3}/{4}'.format(
            event['connector'],
            event['connector_name'],
            event['component'],
            event['resource'],
            event['perf_metric']
        )

        entity = {
            'connector': event['connector'],
            'connector_name': event['connector_name'],
            'component': event['component'],
            'resource': event['resource'],
            'eid': eid,
            'type': 'metric',
            # 'retention': meta['retention'],
            # 'unit': meta['unit']
        }

        tags.update(entity)
        tags[eid] = metric_id

        data_id = tags.pop(eid)

        return data_id, tags

    def count(self, metric_id, timewindow=None, meta=None):
        """Get number of perfdata identified by metric_id in input timewindow

        :param timewindow: if None, get all perfdata values
        """

        data_id, tags = self._data_id_tags(metric_id, meta)

        result = self.perfdata_storage.count(
            data_id=data_id, timewindow=timewindow, tags=tags
        )

        return result

    def get_metrics(self, query=None):
        """Get registered metric ids.

        :return: list of registered metric ids.
        :rtype: list
        """

        return self.context_manager.find(
            _type='metric', _filter=query
        )

    def get(
            self, metric_id, meta=None, with_meta=True, timewindow=None,
            limit=0, skip=0, sort=None, timeserie=None, sliding_time=False
    ):
        """Get a set of data related to input data_id on the timewindow and
        input period.

        If with_meta, result is a couple of (points, list of tags by timestamp)
        """

        data_id, tags = self._data_id_tags(metric_id, meta)

        if sliding_time:  # apply sliding_time

            if timewindow is None:

                timewindow = TimeWindow()

            _timewindow = timewindow

            timewindow = TimeWindow(
                start=timewindow.start(),
                stop=timewindow.stop() + SLIDING_TIME_UPPER_BOUND
            )

        real_id = self._metric_id_tags(metric_id)
        result = self.perfdata_storage.get(
            data_id=real_id, timewindow=timewindow, limit=limit,
            tags=tags, with_tags=with_meta
        )

        if sliding_time:

            if with_meta:
                points = result[0]

            else:
                points = result

            points = [(min(ts, _timewindow.stop()), val) for (ts, val) in points]

            if with_meta:
                result = points, result[1]

            else:
                result = points

        return result

    def get_point(self, metric_id, with_meta=True, timestamp=None, meta=None):
        """Get the closest point before input timestamp. Add tags informations
        if with_tags.
        """

        data_id, tags = self._data_id_tags(metric_id, meta)

        if timestamp is None:
            timestamp = time()

        timewindow = get_offset_timewindow(timestamp)

        result = self.perfdata_storage.get(
            data_id=data_id, timewindow=timewindow,
            limit=1, tags=tags, with_tags=with_meta
        )

        return result

    def put(self, metric_id, points, meta=None, cache=False, event=None):
        """Put a (list of) couple (timestamp, value), a tags into
        rated_documents.

        kwargs will be added to all document in order to extend timed
        documents.

        :param iterable points: points to put. One point (timestamp, value) or
            points (timestamp, values)+.
        """

        if event is None:
            event = {}

        # do something only if there are points to put
        if len(points) > 0:
            first_point = points[0]
            # if first_point is a timestamp, points is one point
            if isinstance(first_point, (Number, basestring)):
                # transform points into a tuple
                points = (points,)

            data_id, tags = self._data_id_tags(metric_id, meta, event=event)

            # update data in a cache (a)synchronous way
            self.perfdata_storage.put(
                data_id=data_id, points=points, tags=tags, cache=cache
            )

    def remove(
            self, metric_id, timewindow=None, meta=None, cache=False
    ):
        """Remove values and tags of one metric."""

        data_id, tags = self._data_id_tags(metric_id, meta)

        self.perfdata_storage.remove(
            data_id=data_id,
            timewindow=timewindow,
            cache=cache,
            tags=tags
        )

    def parse_perfdata(self, perf_data_raw):
        """Try to get a perf data array from input perf_data_raw.

        :param str perf_data_raw: perf_data_raw to parse.
        :return: array of perfdata.
        :rtype: list
        :raises: parsing error if perf_data_raw is not in an understood format.
        """

        self.logger.debug("Parse: {0}".format(perf_data_raw))

        parser = PerfDataParser(perf_data_raw)
        result = parser.perf_data_array

        return result

    @staticmethod
    def is_internal(metric):
        """Check if the metrics is internal.
        :param metric: a metrics as dict.
        :rtype : a boolean
        """

        return metric['metric'].startswith('cps_')

    def get_metric_infos(self, limit, start, filter_=None):
        """
        Retreive metrics informations from influx.

        :param int limit: how many records to retreive
        :param int start: skip n first elements
        :param filter_: a string use to search specific metrics. If filter_ is
        set to None, every metrics will be returned.
        :rtype: list(dict)
        """

        query = None
        if filter_ is None:
            query = 'SHOW SERIES;'
        else:
            query = 'SHOW SERIES where "eid" =~ /.*{0}.*/;'.format(filter_)

        data = self.perfdata_storage._conn.query(query).raw

        if "series" not in data:
            return []

        metric_infos = []
        for serie in data['series']:
            try:
                index_ = serie['columns'].index('eid')
            except ValueError:
                self.logger.debug("Could not find eid in columns")
                continue

            for value in serie['values']:
                split = value[index_].split('/')
                dict_ = {
                    '_id': value[index_],
                    'type': 'metric',
                    'connector': split[2],
                    'connector_name': split[3],
                    'component': split[4],
                    'resource': split[5],
                    'name': split[6],
                    'internal': False  # TODO: calculate that
                }
                metric_infos.append(dict_)

        if limit is None:         # No limit
            end = len(metric_infos)
        else:
            end = start + limit

        return metric_infos[start:end]