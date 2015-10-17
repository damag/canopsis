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

from canopsis.middleware.registry import MiddlewareRegistry
from canopsis.configuration.configurable.decorator import add_category
from canopsis.configuration.configurable.decorator import conf_paths
from canopsis.configuration.parameters import Parameter

from canopsis.timeserie.core import TimeSerie
from canopsis.old.filter import check


CONF_PATH = 'stats/producer/metric.conf'
CATEGORY = 'METRICPRODUCER'
CONTENT = [
    Parameter('default_aggregation_interval', int),
    Parameter('round_time_interval', Parameter.bool)
]


@conf_paths(CONF_PATH)
@add_category(CATEGORY, content=CONTENT)
class MetricProducer(MiddlewareRegistry):

    FILTER_STORAGE = 'filter_storage'
    SERIE_MANAGER = 'serie'
    CONTEXT_MANAGER = 'context'
    PERFDATA_MANAGER = 'perfdata'

    @property
    def default_aggregation_interval(self):
        if not hasattr(self, '_default_aggregation_interval'):
            self.default_aggregation_interval = None

        return self._default_aggregation_interval

    @default_aggregation_interval.setter
    def default_aggregation_interval(self, value):
        if value is None:
            value = TimeSerie.VPERIOD.total_seconds()

        self._default_aggregation_interval = value

    @property
    def round_time_interval(self):
        if not hasattr(self, '_round_time_interval'):
            self.round_time_interval = None

        return self._round_time_interval

    @round_time_interval.setter
    def round_time_interval(self, value):
        if value is None:
            value = TimeSerie.VROUND_TIME.total_seconds()

        self._round_time_interval = value

    def __init__(
        self,
        default_aggregation_interval=None,
        round_time_interval=None,
        filter_storage=None,
        *args, **kwargs
    ):
        super(MetricProducer, self).__init__(*args, **kwargs)

        if default_aggregation_interval is not None:
            self.default_aggregation_interval = default_aggregation_interval

        if round_time_interval is not None:
            self.round_time_interval = round_time_interval

        if filter_storage is not None:
            self[MetricProducer.FILTER_STORAGE] = filter_storage

    def match(self, event):
        storage = self[MetricProducer.FILTER_STORAGE]
        matches = [
            evfilter['crecord_name']
            for evfilter in storage.find_elements()
            if check(evfilter['filter'], event)
        ]

        return matches

    def create_serie(self, metric, operator):
        serie = {
            'crecord_name': metric['name'],
            'component': metric['component'],
            'resource': metric['resource'],
            'metric_filter': 'co:{0} re:{1} me:{2}'.format(
                metric['component'],
                metric['resource'],
                metric['name']
            ),
            'aggregation_method': operator,
            'aggregation_interval': self.default_aggregation_interval,
            'round_time_interval': self.round_time_interval,
            # only one metric selected, so SUM is the identity
            'formula': 'SUM("me:.*")',
            'last_computation': 0
        }

        metric_id = self[MetricProducer.CONTEXT_MANAGER].get_entity_id(metric)
        meta = self[MetricProducer.PERFDATA_MANAGER].get_meta(metric_id)
        serie.update(meta)

        seriemgr = self[MetricProducer.SERIE_MANAGER]
        return seriemgr[seriemgr.SERIE_STORAGE].put_element(serie)
