#!/usr/bin/env python2

import argparse
import os
import json # TODO: remove
from copy import deepcopy
from pprint import pprint

def parse_args():
	parser = argparse.ArgumentParser(description='Application Description')
#	parser.add_argument("-v", "--verbosity", default="INFO")

	args = parser.parse_args()

	return args

def main():
	args = parse_args()

	# load configs
	roots = os.getenv('YAC_ROOTS')
	if not roots:
		exit(1)
	roots = roots.split(':')
	config = load_configs(roots)
	
	pprint(config)

def load_configs(paths):
	all_configs = {}
	for path in paths:
		config = load_config(path)
		all_configs = merge_configs(all_configs, config)
	return all_configs

def load_config(path):
	with open(path) as f: # TODO: FILE_OPENER
		config = json.load(f) # TODO: CONFIG_READER
	if 'pyramid.include' in config:
		parent_config = load_configs(config['pyramid.include'])
		config = merge_configs(parent_config, config)
	return config

def merge_configs(parent_config, child_config, policy=None):
	if 'pyramid.merge_policy' in child_config:
		policy = child_config['pyramid.merge_policy']
		new_config = PolicyMerger(policy).merge(parent_config, child_config)
	else:
		new_config = DefaultMerger().merge(parent_config, child_config)
	return new_config

class DefaultMerger(object):
	def merge(self, parent_config, child_config):
#		print 'parent_config', parent_config
#		print 'child_config', child_config
		new_config = None
		if type(child_config) != type(parent_config):
#			print '!='
			new_config = deepcopy(child_config)
		elif type(child_config) is dict:
#			print 'dict'
			new_config = deepcopy(parent_config)
			for key in set(parent_config.viewkeys()) | set(child_config.viewkeys()):
#				print 'key=', key
				if key not in parent_config:
					new_config[key] = deepcopy(child_config[key])
				elif key not in child_config:
					pass
				else:
					new_config[key] = self.merge(parent_config[key], child_config[key])
		else:
#			print 'else'
			new_config = deepcopy(child_config)
#		print 'new_config', new_config
		return new_config

class PolicyMerger(object):
	def __init__(self, policy):
		self._policy = policy
	def merge(self, parent_config, child_config):
		return self._merge_inner(parent_config, child_config, self._policy)

	def _merge_inner(self, parent_config, child_config, policy):
#		print 'parent_config', parent_config
#		print 'child_config', child_config
#		print 'policy', policy
		type_ = type(child_config)
		if type(child_config) != type(parent_config) or policy == 'overwrite':
#			print 'type != or overwrite'
			new_config = deepcopy(child_config)
		elif policy == 'append':
			new_config = parent_config + child_config
#		elif policy == 'merge' and type_ is list:
#			# TODO: error for different size
#			# TODO: support list item merging
#			new_config = []
#			for i in xrange(len(child_config)):
#				new_config.append(self._merge_inner(parent_config[i], child_config[i], None))
		elif type_ is dict:
#			print 'dict'
			new_config = deepcopy(parent_config)
			for key in set(parent_config.viewkeys()) | set(child_config.viewkeys()):
#				print 'key=', key
				if key not in parent_config:
					new_config[key] = deepcopy(child_config[key])
				elif key not in child_config:
					pass
				else:
					if policy != None:
						next_policy = policy.get(key, None)
					else:
						next_policy = None
					new_config[key] = self._merge_inner(parent_config[key], child_config[key], next_policy)
		else:
#			print 'else'
			new_config = deepcopy(child_config)
#		print 'new_config', new_config
		return new_config

if __name__ == "__main__":
	main()

