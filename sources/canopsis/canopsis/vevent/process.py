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

"""Module in charge of defining main graph task execution.

When an event occured, the related entity is retrieved with its bound
graph nodes in order to execute theirs tasks.
"""

from canopsis.common.utils import singleton_per_scope
from canopsis.context_graph.manager import ContextGraph
from canopsis.task.core import register_task
from canopsis.vevent.manager import VEventManager
from canopsis.common.middleware import Middleware

@register_task('vevent.event_processing')
def event_processing(event, veventmanager=None, **params):
    """Add vevent information in VEventManager from input event.

    :param dict event: event to process.
    :param function get_info: function which takes in parameter the event and
        returns vevent info.
    """

    # initialiaze veventmanager
    if veventmanager is None:
        storage = Middleware.get_middleware_by_uri(VEventManager.VEVENT_COLL_URL)
        veventmanager = singleton_per_scope(VEventManager, kwargs={'vevent_storage': storage})
    context = singleton_per_scope(ContextGraph)
    # get source from the event
    source = context.get_id(event)
    # get vevent from the event
    vevent = event[VEventManager.VEVENT]
    # add event information into veventmanager
    veventmanager.put(source=source, vevents=[vevent], cache=True)
