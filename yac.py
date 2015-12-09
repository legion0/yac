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

def merge_master_configs(parent_master, child_master):
	policy_view = deepcopy(parent_master)
	policy_view.update(child_master) # TODO: support advanced policy views
	for long_name in set(parent_master.viewkeys()) | set(child_master.viewkeys()):
		if long_name not in parent_master:
			parent_master[long_name] = deepcopy(child_master[long_name]) # TODO: deep copy required ?
		if long_name in child_master:
			parent_master[long_name] = merge_config(policy_view, parent_master[long_name], child_master[long_name])

def load_configs(paths):
	all_configs = {}
	for path in paths:
		master_config = load_config(path)
		merge_master_configs(all_configs, master_config)
	return all_configs

def load_config(path):
	with open(path) as f: # TODO: FILE_OPENER
		config = json.load(f) # TODO: CONFIG_READER

	if 'long_name' not in config:
		config['long_name'] = config['type'] + '.' + config['name']
	master_config = {}
	if 'include' in config:
		master_config = load_configs(config['include'].split(':'))
		del config['include']
	if config['long_name'] not in master_config:
		master_config[config['long_name']] = {}
	master_config[config['long_name']] = merge_config(master_config, master_config[config['long_name']], config)
	return master_config

def merge_config(policy_view,parent_config, child_config):
	new_config = deepcopy(parent_config)
	new_config.update(child_config) # TODO: CONFIG_MERGER
	return new_config

class PolicyMerger(object):
	def __init__(self, master_config):
		self._master_config = master_config

	def merge(parent_config, child_config):
		policy = self._select_policy(parent_config, child_config)
		return self._merge_inner(policy, parent_config, child_config)

	def _merge_inner(policy, parent_config, child_config):
		new_config = deepcopy(parent_config) # TODO: required deep ?
		for key in set(parent_config.viewkeys()) | set(child_config.viewkeys()):
			key_policy = policy.get(key, None) # TODO: CONTINUE_HERE
			if key not in parent_config:
				new_config[key] = deepcopy(child_config[key]) # TODO: required deep ?
			if key in child_config:
				
				if isinstance(x, dict):
					new_config[key] = self._merge_inner(policy.get(key, {}), parent_config[key], child_config[key])
				else:
					
		

	def _select_policy(parent_config, child_config):
		if 'merge_policy' in child_config:
			policy = child_config['merge_policy']
		elif 'merge_policy' in parent_config:
			policy = parent_config['merge_policy']
		else:
			policy = ''
		# TODO: handle non named policies (e.g. filepath / direct dict)
		policy_long_name = 'merge_policy.' + policy
		if policy_long_name in self._master_config:
			policy = self._master_config[policy_long_name]
		else:
			policy = {}
		return policy

if __name__ == "__main__":
	main()

