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

from canopsis.common.utils import singleton_per_scope
from canopsis.task.core import register_task

from canopsis.linklist.manager import LinklistManager
from canopsis.common.utils import encode_utf8

LINK_KEY = "event_link"

@register_task
def event_processing(engine, event, llmngr=None, logger=None, **kwargs):

    if llmngr is None:
        llmngr = singleton_per_scope(LinklistManager)

    encoded_event = encode_utf8(event)

    llmngr.enrich_from_event(encoded_event)


@register_task
def beat(engine, logger=None, **kwargs):
    # TODO reload configuration
    pass
