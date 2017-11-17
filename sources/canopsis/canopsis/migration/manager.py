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
import os
import signal

from logging import StreamHandler

from canopsis.common.utils import lookup
from canopsis.confng import Configuration, Json
from canopsis.logger import Logger

DEFAULT_MODULES = ['canopsis.migration.purge.PurgeModule',
                   'canopsis.migration.indexes.IndexesModule',
                   'canopsis.migration.jsonloader.JSONLoaderModule',
                   'canopsis.migration.rights.RightsModule',
                   'canopsis.migration.views.ViewsModule',
                   'canopsis.migration.perfdata.PerfdataModule']
DEFAULT_ASK_TIMEOUT = 30
DEFAULT_VERSION_INFO = '~/var/lib/canopsis/migration.json'


class MigrationTool(object):
    """
    """

    CONF_PATH = 'etc/migration/manager.conf'
    LOG_PATH = 'var/log/migrationtool.log'
    CATEGORY = 'MIGRATION'

    def __init__(self, modules=None):

        self.logger = Logger.get('migrationtool', self.LOG_PATH)
        self.config = Configuration.load(MigrationTool.CONF_PATH, Json)
        conf = self.config.get(self.CATEGORY, {})

        if modules is None:
            self.modules = conf.get('modules', DEFAULT_MODULES)

        self.loghandler = StreamHandler()
        self.logger.addHandler(self.loghandler)

    def fill(self, init=True):
        tools = []

        for module in self.modules:
            try:
                migrationcls = lookup(module)

            except ImportError as err:
                self.logger.error(
                    'Impossible to load module "{0}": {1}'.format(
                        module,
                        err
                    )
                )

                continue

            migrationtool = migrationcls()
            migrationtool.logger.addHandler(self.loghandler)
            tools.append(migrationtool)

        for tool in tools:
            if init:
                tool.init()

            else:
                tool.update()


class MigrationModule(object):

    CONF_PATH = 'etc/migration/manager.conf'
    LOG_PATH = 'var/log/migrationtool.log'
    CATEGORY = 'MODULE'

    def __init__(self, ask_timeout=None, version_info=None):
        self.logger = Logger.get('migrationmodule', self.LOG_PATH)
        self.config = Configuration.load(MigrationModule.CONF_PATH, Json)
        conf = self.config.get(self.CATEGORY, {})

        self.ask_timeout = int(conf.get('ask_timeout', DEFAULT_ASK_TIMEOUT))
        if ask_timeout is not None:
            self.ask_timeout = ask_timeout

        self.version_info = os.path.expanduser(
            conf.get('version_info', DEFAULT_VERSION_INFO))
        if version_info is not None:
            self.version_info = os.path.expanduser(version_info)

    def get_version(self, item):
        try:
            with open(self.version_info) as f:
                version_info = json.load(f)

        except Exception as err:
            self.logger.error(
                'Impossible to parse version info: {0}'.format(err)
            )

            version_info = {}

        return version_info.get(item, 0)

    def set_version(self, item, version):
        try:
            with open(self.version_info) as f:
                version_info = json.load(f)

        except Exception as err:
            self.logger.error(
                'Impossible to parse version info: {0}'.format(err)
            )

            version_info = {}

        version_info[item] = version

        try:
            with open(self.version_info, 'w') as f:
                json.dump(version_info, f)

        except Exception as err:
            self.logger.error(
                'Impossible to save version info: {0}'.format(err)
            )

    def ask(self, prompt, default=True):
        answered = False
        user_input = 'N'
        default_val = 'Y' if default else 'N'

        def timeout(sig, frame):
            raise Exception('')

        signal.signal(signal.SIGALRM, timeout)

        while not answered:
            signal.alarm(self.ask_timeout)

            try:
                user_input = raw_input(
                    '{0} Y/N (default={1})'.format(
                        prompt,
                        default_val
                    )
                )

                if user_input in ['Y', 'y', 'N', 'n', '']:
                    answered = True

            except Exception:
                user_input = default_val
                answered = True

            signal.alarm(0)

        if user_input == '':
            user_input = default_val

        return (user_input in ['Y', 'y'])

    def init(self):
        raise NotImplementedError()

    def update(self):
        raise NotImplementedError()