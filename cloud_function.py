
import base64
import json
import logging
import time

import traceback
import sys

from apiclient import errors
from docopt import docopt
from googleapiclient import discovery
from google.cloud import pubsub_v1

logger = logging.getLogger('resurrect.prere')

PROJECT_ID = ' YOUR PROJECTID '

class GoogleCloud:
	"""Helper class for interacting with Google Cloud compute API."""

	def __init__(self, project_id):
		# disable cache discovery
		# https://github.com/google/google-api-python-client/issues/299#issuecomment-268915510
		compute = discovery.build('compute', 'v1', cache_discovery=False)
		self.inst_api = compute.instances()
		self.project_id = project_id

	def get_instance(self, zone, inst_name):
		"""Return a dictionary describing a GCE instance, if it exists."""
		return self.inst_api.get(project=self.project_id, zone=zone,
								 instance=inst_name).execute()

	def start_instance(self, zone, inst_name):
		"""Call the start GCE instance API, returning the operation response."""
		return self.inst_api.start(project=self.project_id, zone=zone,
									 instance=inst_name).execute()


def resurrect_instance(project_id, instance_desc):
	"""Try resurrecting a terminated (preempted) GCE instance.
	Input `instance_desc`: dictionary with the instance 'name' and 'zone'.
	Ignores instance if: it doesn't exist; it's already running.
	Retry if: instance not yet terminated.
	"""
	try:
		inst_name, zone = instance_desc['name'], instance_desc['zone']
	except KeyError:
		logger.error('Parsed message missing mandatory fields: %r', instance_desc)
		return
	except TypeError:
		logger.error('Parsed message not valid dictionary: %r', instance_desc)
		return

	logger.info('Got resurrection request for instance "%s" in zone "%s"',
				inst_name, zone)

	gcloud = GoogleCloud(project_id)
	still_running_count = 0

	while True:
		try:
			gce_inst = gcloud.get_instance(zone, inst_name)
		except (errors.HttpError, TypeError):
			logger.warning('No instance named "%s" in zone "%s"', inst_name, zone)
			return
		if gce_inst['status'] == 'TERMINATED':
			logger.info('Attempting to start terminated instance "%s" in zone "%s"',
						inst_name, zone)
			response = gcloud.start_instance(zone, inst_name)
			logger.debug('Started GCE operation: %r', response)
			return
		elif gce_inst['status'] == 'STOPPING':
			logger.info('Instance "%s/%s" is stopping - waiting for termination',
						zone, inst_name)
			time.sleep(10.0)
		elif gce_inst['status'] == 'RUNNING':
			still_running_count += 1
			if still_running_count > 6:
				logger.warning('Instance "%s/%s" has been running for the last 3 '
								 'minutes - assuming it\'s not about to terminate',
								 zone, inst_name)
				return
			logger.info('Instance "%s/%s" still running - waiting for termination',
						zone, inst_name)
			time.sleep(30.0)
		else:
			logger.warning('Not sure how to handle instance "%s/%s" status: "%s" '
						 '-- ignoring', zone, inst_name, gce_inst['status'])


def configure_logging():
	"""Configure DEBUG-level logging with console output."""
	logger.setLevel(logging.DEBUG)
	ch = logging.StreamHandler()
	ch.setLevel(logging.DEBUG)
	formatter = logging.Formatter(
		'%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	ch.setFormatter(formatter)
	logger.addHandler(ch)



def cloudfunc_entry(event, context):
	"""Triggered from a message on a Cloud Pub/Sub topic.
	Args:
		 event (dict): Event payload.
		 context (google.cloud.functions.Context): Metadata for the event.
	"""

	try:
		print(event)
		if 'data' in event:
			pubsub_message = base64.b64decode(event['data']).decode('utf-8')
		else:
			pubsub_message = event

		#for key in event.keys():
		#	print(key)
		#pubsub_message = base64.b64decode(event).decode('utf-8')
		#print(pubsub_message)
		
		#configure_logging()

		## resurrect instance based on message data
		try:
			if 'data' in event:
				instance_desc = json.loads(pubsub_message)
			else:
				instance_desc = pubsub_message
		except:
			logger.exception('Failed parsing JSON message - ignoring it\n%s', pubsub_message)
		else:
			resurrect_instance(PROJECT_ID, instance_desc)

	except Exception as err:
		print(f'There was an error {err}')

		

