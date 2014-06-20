#!/usr/bin/env python
#--------------------------------
# Copyright (c) 2011 "Capensis" [http://www.capensis.com]
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

import unittest
import sys, os
import logging
import time

sys.path.append(os.path.expanduser('~/opt/amqp2engines/engines/'))
sys.path.append(os.path.expanduser('~/lib/canolibs/unittest/'))

import alertcounter
import camqpmock
import managermock

from crecord import crecord
from cstorage import get_storage
from caccount import caccount

class KnownValues(unittest.TestCase):
	def setUp(self):
		self.engine = alertcounter.engine(
			logging_level=logging.WARNING,
		)
		# mocking the manager
		self.engine.amqp = camqpmock.CamqpMock(self.engine)
		self.engine.manager = managermock.ManagerMock(self.engine)
		self.storage = get_storage(namespace='object', account=caccount(user="root", group="root"))


	"""
	Tests methods has engine method names
	"""

	def test_01_Work(self):

		event = {
			'connector': 'test',
			'connector_name': 'test',
			'event_type': 'not a checked type',
			'source_type': 'source',
			'component': 'component',
			'state': 1,
			'state_type': 1
		}
		routing_key = "%s.%s.%s.%s.%s" % (event['connector'], event['connector_name'], event['event_type'], event['source_type'], event['component'])
		event['rk'] = routing_key

		# asserts event was not validated
		self.engine.work(event)
		self.assertTrue(self.engine.amqp.events == [])

		# asserts event is being threaten thanks to it s type
		event['event_type'] = 'check'
		self.engine.work(event)
		self.assertTrue(self.engine.amqp.events != [])

	def test_02_load_macros(self):
		macro_name = 'TEST_MACRO'
		self.storage.get_backend('object').update(
			{'crecord_type': 'slamacros'},
			{'$set': {'macro': macro_name }},
			upsert=True
		)

		#effective test
		self.engine.load_macro()
		self.assertTrue(self.engine.MACRO == macro_name)
		self.reset_data()


	def test_04_load_crits(self):
		self.storage.get_backend('object').remove({'crecord_type': 'comment'})
		count = self.storage.get_backend('object').insert({
			'crecord_type': 'comment',
			'referer_event_rks': [{'rk': 'test_rk_1'}]
		})
		self.engine.reload_ack_comments()
		self.assertTrue(self.engine.comments['test_rk_1'] == 1)

	def test_05_perfdata_key(self):
		key = self.engine.perfdata_key({'co': 'co', 're': 're', 'me': 'me'})
		self.assertTrue(key == 'coreme')

		key = self.engine.perfdata_key({'co': 'co', 'me': 'me'})
		self.assertTrue(key == 'come')

		key = self.engine.perfdata_key({})
		self.assertTrue(key == 'missing component or metric key')
		self.reset_data()


	def test_06_increment_counter(self):
		meta = {'co': 'co', 're': 're', 'me': 'me'}
		self.engine.increment_counter(meta, 1)
		self.assertTrue(self.engine.manager.data.pop() == {'meta_data': 'meta_data', 'name':
			u'coreme', 'value': 1})
		self.engine.increment_counter({'co': 'co', 're': 're', 'me': 'me'}, 1)
		del meta['re']
		self.engine.increment_counter(meta, 2)
		self.assertTrue(self.engine.manager.data.pop() == {'meta_data': 'meta_data', 'name': u'come', 'value': 2})
		self.reset_data()

	def test_07_update_global_counter(self):
		#generated metrics names are listed below.
		truth_table = {
			"__canopsis__cps_statechange": [1,1,1,1],
			"__canopsis__cps_statechange_hard": [0,1,1,1],
			"__canopsis__cps_statechange_soft": [0,0,0,0],
			"__canopsis__cps_statechange_0": [1,0,0,0],
			"__canopsis__cps_statechange_1": [0,1,0,0],
			"__canopsis__cps_statechange_2": [0,0,1,0],
			"__canopsis__cps_statechange_3": [0,0,0,1],
			"__canopsis__cps_statechange_nok": [0,1,1,1]
		}
		self.reset_data()


		#data driven testing
		def ugc_each_status(state):

			self.engine.update_global_counter({'state': state, 'resource': 'resource'})
			event = self.engine.amqp.events.pop()

			self.assertEqual(event['state'], 0)
			self.assertEqual(event['connector'], 'cengine')
			self.assertEqual(event['connector_name'], self.engine.etype)
			self.assertEqual(event['source_type'], 'resource')
			self.assertEqual(event['component'], alertcounter.INTERNAL_COMPONENT)
			self.assertEqual(event['resource'], None)
			#Let test if they are all generated
			while self.engine.manager.data:
				metric = self.engine.manager.data.pop()
				self.assertTrue(metric['name'] in truth_table)
				#using state as postition in truth table
				self.assertEqual(truth_table[metric['name']][state], metric['value'])

		# all statuses : ok, warning, error, unknown
		for state in xrange(4):
			ugc_each_status(state)

		host_group = 'test_host_group'
		self.engine.update_global_counter({'state': state, 'resource': 'resource', 'hostgroups': [host_group]})

		#8 basic metrics + 8 for hostgroup
		self.assertEqual(len(self.engine.manager.data), 16)
		#reset data
		self.engine.manager.data = []

		while self.engine.amqp.events:
			event = self.engine.amqp.events.pop()
			self.assertTrue(event['resource'] == host_group)

		self.reset_data()


	def test_08_count_sla(self):
		truth_table = {
			"__canopsis__cps_sla_slatype_slaname_out": [1, 0, 0],
			"__canopsis__cps_sla_slatype_slaname_ok": [0, 0, 1],
			"__canopsis__cps_sla_slatype_slaname_nok": [0, 1, 0],
		}
		now = time.time()
		slatype = 'slatype'
		slaname = 'slaname'
		event = {'last_state_change': 1, 'state': 1}

		def test_sla(index,  delay=1):

			self.engine.count_sla(event,slatype, slaname, delay)
			while self.engine.manager.data:
				metric = self.engine.manager.data.pop()
				self.assertTrue(metric['name'] in truth_table)
				#using state as postition in truth table
				self.assertEqual(truth_table[metric['name']][index], metric['value'])

		#Test general cases
		self.storage.get_backend('entities').remove({'type': 'ack'})
		test_sla(0)
		self.storage.get_backend('entities').insert({'type': 'ack', 'timestamp': 2})
		test_sla(1)
		test_sla(2, delay=now + 1)


		#test other stuff like hostgroup care and event state == 0 that publish a new metric
		self.storage.get_backend('entities').remove({'type': 'ack'})

		event ['hostgroups'] = ['hostgroup_test']
		self.engine.count_sla(event,slatype, slaname, 1)
		self.assertEqual(len(self.engine.manager.data), 6)

		self.reset_data()

		event ['hostgroups'] = ['hostgroup_test']
		self.engine.count_sla(event,slatype, slaname, 1)
		self.assertEqual(len(self.engine.manager.data), 6)

		self.reset_data()



	def test_09_count_by_crits(self):
		self.engine.MACRO = 'MACRO'
		self.engine.crits = {'macro_value': 1}
		event = {
			'last_state_change':1,
			'previous_state':1,
			'state' : 0,
			'MACRO': 'macro_value'
		}

		#check metric name is properly built
		self.engine.count_by_crits(event)
		while self.engine.manager.data:
			metric = self.engine.manager.data.pop()
			self.assertTrue('warn' in metric['name'])

		event['previous_state'] = 2
		self.engine.count_by_crits(event)
		while self.engine.manager.data:
			metric = self.engine.manager.data.pop()
			self.assertTrue('crit' in metric['name'])

		#macro is a part of the metric name
		self.engine.crits['mock_test_macro'] = 1
		self.engine.count_by_crits(event)
		#test update other section
		for metric in self.engine.manager.data[3:]:
			metric = self.engine.manager.data.pop()
			self.assertTrue('mock_test_macro' in metric['name'])

		self.reset_data()

	def test_10_count_alert(self):
		self.engine.count_alert({'component': 1, 'state': 1}, 1)
		pass

	def reset_data(self):
		#init engine as needed

		self.engine.manager.clean()
		self.engine.amqp.clean()


	def show(self):
		print 'DATA'
		for d in self.engine.manager.data:
			print d
		print 'Events'
		for e in self.engine.amqp.events:
			print e

if __name__ == "__main__":
	unittest.main()
