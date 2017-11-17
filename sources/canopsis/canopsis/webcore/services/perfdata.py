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

import json

from bottle import request

from canopsis.common.ws import route
from canopsis.common.utils import singleton_per_scope
from canopsis.confng import Configuration, Ini
from canopsis.perfdata.manager import PerfData
from canopsis.timeserie.timewindow import TimeWindow, Period
from canopsis.timeserie.core import TimeSerie
from canopsis.webcore.utils import gen_json, gen_json_error

NO_LIMIT = 0
DEFAULT_LIMIT = 100
DEFAULT_START = 0


def exports(ws):

    perfdata_manager_args = PerfData.provide_default_basics()
    manager = singleton_per_scope(PerfData, args=perfdata_manager_args)

    @route(ws.application.post, payload=['metric_id', 'timewindow', 'meta'])
    def perfdata_count(metric_id, timewindow=None, meta=None):
        if timewindow is not None:
            timewindow = TimeWindow(**timewindow)

        result = manager.count(
            metric_id=metric_id, timewindow=timewindow, meta=meta
        )

        return result

    @route(
        ws.application.post,
        payload=[
            'metric_id', 'with_meta',
            'limit', 'skip', 'period',
            'timewindow', 'period', 'timeserie', 'sliding_time'
        ]
    )
    def perfdata(
        metric_id, timewindow=None, period=None, with_meta=True,
        limit=0, skip=0, timeserie=None, meta=None, sliding_time=False
    ):
        if timewindow is not None:
            timewindow = TimeWindow(**timewindow)

        if timeserie is not None:
            if period is None:
                period = timeserie.pop('period', None)

            conf = Configuration.load(TimeSerie.CONF_PATH, Ini)
            timeserie = TimeSerie(config=conf, **timeserie)

            if period is not None:
                timeserie.period = Period(**period)

        if not isinstance(metric_id, list):
            metrics = [metric_id]

        else:
            metrics = metric_id

        result = []

        for metric_id in metrics:
            # meta -> _meta
            pts, _meta = manager.get(
                metric_id=metric_id, with_meta=True,
                timewindow=timewindow, limit=limit, skip=skip,
                meta=meta, sliding_time=sliding_time
            )

            _meta['data_id'] = metric_id

            if timeserie is not None:
                pts = timeserie.calculate(pts, timewindow, meta=_meta)

            if with_meta:
                result.append({
                    'points': pts,
                    'meta': _meta
                })

            else:
                result.append({
                    'points': pts
                })

        return (result, len(result))

    @route(ws.application.put, payload=['metric_id', 'points', 'meta'])
    def perfdata(metric_id, points, meta=None):
        manager.put(metric_id=metric_id, points=points, meta=meta)

        result = points

        return result

    @route(ws.application.delete, payload=['metric_id', 'timewindow', 'meta'])
    def perfdata(metric_id, timewindow=None, meta=None):
        if timewindow is not None:
            timewindow = TimeWindow(**timewindow)

        manager.remove(metric_id=metric_id, timewindow=timewindow, meta=meta)

        result = None

        return result

    @route(ws.application.get)
    def perfdata_period(metric_id):
        result = manager.get_period(metric_id)

        return result

    @route(ws.application.get)
    def perfdata_internal(metric):
        result = manager.is_internal(metric)

        return result

    @ws.application.get('/api/v2/perfdata/metric')
    def get_context_metric():
        """
        Fetch metric informations.
        """
        limit = request.query.limit or 10000
        start = request.query.start or 0
        try:
            limit = int(limit)
            start = int(start)
        except ValueError:
            gen_json_error({'description': 'cannot parse parameters'},
                           HTTP_ERROR)

        rep = manager.get_metric_infos(limit, start)

        return gen_json(rep)

    @ws.application.post('/api/context/metric')
    def context_metric():
        """Return every metrics matching a pattern. If they are not
        any pattern, every metrics will be returned.
        :rtype: a dict
        :return: a dict with every matching entities.
        """
        json_result = {"total": None,
                       "data": [],
                       "success": None}

        rep = None
        try:
            data_error = {}

            param = request.body.read()

            if param == "":
                param = {}
            else:
                param = json.loads(param)

            limit = int(param.get("limit", DEFAULT_LIMIT))
            start = int(param.get("start", DEFAULT_START))
            filter_ = param.get("_filter", {})

            # Pars the filter_ field to retrieve the pattern.
            if "name" in filter_:
                filter_ = filter_["name"].get("$regex", None)
            else:
                filter_ = None

            if limit == NO_LIMIT:
                limit = None
            # 0 because I need to retreive every metrics in order to create
            # the total field of the result
            rep = manager.get_metric_infos(limit=None, start=0, filter_=filter_)
        except Exception as err:
            data_error = {}
            data_error["msg"] = str(err.message)
            data_error["traceback"] = "TODO"
            data_error["type"] = str(type(err))
            json_result["data"] = data_error
            json_result["total"] = 0
            json_result["success"] = False
            return json_result

        if limit == None:
            end = len(rep)
        else:
            end = start+limit

        json_result["data"] = rep[start:end]
        json_result["total"] = len(rep)
        json_result["success"] = True
        return json_result