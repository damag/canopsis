#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Healthcheck manager.
"""

from __future__ import unicode_literals
import os
import re
import requests
import subprocess

from pika.exceptions import ConnectionClosed
from requests.auth import HTTPBasicAuth
from urlparse import urlparse

from canopsis.common.amqp import AmqpConnection
from canopsis.common.collection import MongoCollection
from canopsis.common.influx import InfluxDBClient
from canopsis.common.mongo_store import MongoStore
from canopsis.common.redis_store import RedisStore
from canopsis.logger import Logger
from canopsis.models.healthcheck import Healthcheck, ServiceState


def check_engine_status(name):
    """
    Check if an engine is running

    :param string name: name of an engine
    :rtype: bool
    """
    return check_process_status('canopsis-engine@{}'.format(name))


def check_process_status(name):
    """
    Check if a service is running, through systemctl

    :param string name: name of a service
    :rtype: bool
    """
    status = os.system('systemctl status {}.service'.format(name))
    return status == 0


def check_checkable(name):
    """
    Check if there is any spawned service with systemctl with a particular
    parttern.

    :param string name: reg that match service names
    :rtype: bool
    """
    # Check is systemctl is available
    try:
        with open(os.devnull, 'w') as devnull:
            procs = subprocess.check_output(['systemctl'],
                                            stderr=devnull).splitlines()
    except (subprocess.CalledProcessError, OSError):
        return False

    # Check if any searched service exist
    reg = re.compile('{}'.format(name))
    engines = [p for p in procs if re.search(reg, p)]
    return len(engines) > 0


class HealthcheckManager(object):
    """
    Action managment.
    """
    LOG_PATH = 'var/log/healthcheck.log'

    CHECK_AMQP_LIMIT_SIZE = 100000
    CHECK_AMQP_QUEUES = [
        'Engine_alerts',
        'Engine_cleaner_events',
        'Engine_context-graph',
        'Engine_event_filter',
        'Engine_pbehavior',
        'task_importctx',
    ]
    # TODO: check Go queues too
    CHECK_COLLECTIONS = ['default_entities', 'periodical_alarm']
    CHECK_ENGINES = [
        'cleaner-cleaner_events',
        'dynamic-alerts',
        'dynamic-context-graph',
        'dynamic-pbehavior',
        'dynamic-watcher',
        'event_filter-event_filter',
        'task_importctx-task_importctx'
    ]
    # TODO: check Go engines too
    CHECK_TS_DB = 'canopsis'
    CHECK_WEBSERVER = 'canopsis-webserver'
    SYSTEMCTL_ENGINE_PREFIX = 'canopsis-engine@'

    def __init__(self, logger):
        self.logger = logger

        self.db_store = MongoStore.get_default()
        self.cache_store = RedisStore.get_default()
        self.amqp_url, self.amqp_exchange = AmqpConnection.parse_conf()
        self.ts_client = InfluxDBClient.from_configuration(self.logger)

    @classmethod
    def provide_default_basics(cls):
        """
        Provide logger, config, storages...

        ! Do not use in tests !

        :rtype: (logging.Logger)
        """
        logger = Logger.get('healthcheck', cls.LOG_PATH)

        return (logger,)

    def _check_rabbitmq_api(self, verb):
        """
        Retries informations from amqp API.
        See https://cdn.rawgit.com/rabbitmq/rabbitmq-management/v3.7.8/priv/www/api/index.html

        :param string verb: the needed path
        :rtype: Response
        """
        parse = urlparse(self.amqp_url)
        loc = parse.netloc.replace(':5672', ':15672', 1)

        url = 'http://{}/api/{}{}'.format(loc, verb, parse.path)
        auth = HTTPBasicAuth(parse.username, parse.password)

        return requests.get(url, auth=auth)

    def _check_rabbitmq_state(self):
        """
        Check amqp service state (consumers, queues).

        :rtype: ServiceState
        """
        # Check consumer presence on amqp queues
        r = self._check_rabbitmq_api('consumers')
        if r.status_code != requests.codes.ok:
            return ServiceState(message='Cannot read consumers on API')

        consumed_queues = [q['queue']['name'] for q in r.json()]
        for queue in self.CHECK_AMQP_QUEUES:
            if queue not in consumed_queues:
                msg = 'No consumer for queue {}'.format(queue)
                return ServiceState(message=msg)

        # Check queues state
        r = self._check_rabbitmq_api('queues')
        if r.status_code != requests.codes.ok:
            return ServiceState(message='Cannot read queues on API')

        queues = {q['name']: q for q in r.json()}
        for queue in self.CHECK_AMQP_QUEUES:
            if queue not in queues.keys():
                msg = 'Missing queue {}'.format(queue)
                return ServiceState(message=msg)

            if queues[queue]['state'] != 'running':
                msg = 'Queue {} is not running'.format(queue)
                return ServiceState(message=msg)

            length = queues[queue]['backing_queue_status']['len']
            if length > self.CHECK_AMQP_LIMIT_SIZE:
                msg = ('Queue {} is overloaded ({} ready messages)'
                       .format(queue, length))
                return ServiceState(message=msg)

        return ServiceState()

    def check_amqp(self):
        """
        Check if amqp service is available.

        :rtype: ServiceState
        """
        try:
            with AmqpConnection(self.amqp_url) as amqp_conn:
                channel = amqp_conn._channel
                try:
                    channel.basic_publish(self.amqp_exchange, '', 'test')
                except Exception as exc:
                    msg = 'Failed to publish: {}'.format(exc)
                    return ServiceState(message=msg)

                if not amqp_conn._connection.is_open:
                    return ServiceState(message='Connection is not opened')
                if not channel.is_open:
                    return ServiceState(message='Channel is not opened')

        except ConnectionClosed as exc:
            return ServiceState(message='Failed to connect: {}'.format(exc))

        return self._check_rabbitmq_state()

    def check_cache(self):
        """
        Check if cache service is available.

        :rtype: ServiceState
        """
        message = "import this"
        try:
            response = self.cache_store.echo(message)
        except Exception as exc:
            msg = 'Cache service crash on echo: {}'.format(exc)
            return ServiceState(message=msg)

        if response != message:
            return ServiceState(message='Failed to validate echo')

        return ServiceState()

    def check_db(self):
        """
        Check if database service is available.

        :rtype: ServiceState
        """
        existing_cols = self.db_store.client.collection_names()
        for collection_name in self.CHECK_COLLECTIONS:
            # Existence test
            if collection_name not in existing_cols:
                msg = 'Missing collection {}'.format(collection_name)
                return ServiceState(message=msg)

            # Read test
            collection = self.db_store.get_collection(name=collection_name)
            mongo_collection = MongoCollection(collection)
            try:
                mongo_collection.find({}, limit=1)
            except Exception as exc:
                return ServiceState(message='Find error: {}'.format(exc))

        return ServiceState()

    def check_engines(self):
        """
        Check if engines are available.

        :rtype: ServiceState
        """
        if not check_checkable(name=self.SYSTEMCTL_ENGINE_PREFIX):
            msg = 'Dockerised environment. Engines Not Checked.'
            ss = ServiceState(message=msg)
            ss.state = True
            return ss

        if not check_process_status(name=self.CHECK_WEBSERVER):
            return ServiceState(message='Webserver is not running')  # Derp

        for engine in self.CHECK_ENGINES:
            if not check_engine_status(name=engine):
                msg = 'Engine {} is not running'.format(engine)  # f-strings
                return ServiceState(message=msg)

        return ServiceState()

    def check_time_series(self):
        """
        Check if time_series service is available.

        :rtype: ServiceState
        """
        dbs = [d['name'] for d in self.ts_client.get_list_database()]
        if self.CHECK_TS_DB not in dbs:
            msg = 'Missing database {}'.format(self.CHECK_TS_DB)
            return ServiceState(message=msg)

        measurements = self.ts_client.get_list_measurements()
        if measurements is None:
            msg = 'Cannot read measurements'
            return ServiceState(message=msg)

        return ServiceState()

    def check(self, criticals=None):
        """
        Check all services.

        :param list criticals: service considered as critical (for overall)
        :rtype: dict
        """
        check = Healthcheck(
            amqp=self.check_amqp(),
            cache=self.check_cache(),
            database=self.check_db(),
            engines=self.check_engines(),
            time_series=self.check_time_series(),
            criticals=criticals
        )
        return check.to_dict()
