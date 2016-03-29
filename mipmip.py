#!/usr/bin/env python2

import argparse
import os
import sys
import json # TODO: remove
from copy import deepcopy
from pprint import pprint
from pyramid import pyramid_lib
import collections
import subprocess

def parse_args():
	Arguments = collections.namedtuple('Arguments', 'command target')
	argv = sys.argv[1:]
	command = argv[0]
	target = argv[1]
	args = Arguments(command, target)
	return args
		

def main():
	args = parse_args()

	roots = os.getenv('MIPMIP_ROOTS')
	if not roots:
		print 'no roots'
		exit(1)
	roots = roots.split(':')
	config = pyramid_lib.load_configs(roots)
	
#	pprint(config)

	if args.command == 'run':
		workflow = config.get('mipmip.workflow.' + args.target, None)
		if workflow is not None:
			return run_workflow(workflow, config)
		task = config.get('mipmip.task.' + args.target, None)
		if task is not None:
			return run_task(args.target, task, config)

def run_workflow(workflow, config):
	for task_name in workflow.get('tasks', []):
		task = config.get('mipmip.task.' + task_name, None)
		returncode = run_task(task_name, task, config)
		if returncode != 0:
			return returncode
	return 0

def run_task(task_name, task, config):
	if task is None:
		return
	target = task['target']
	positional_args = parse_list_arg(task.get('args', {}).get('positional', []), config, config.get('mipmip.arg_policy.' + task_name, {}).get('positional', {}), False)
	joined_named_args = parse_dict_arg(task.get('args', {}).get('named', {}), config, config.get('mipmip.arg_policy.' + task_name, {}).get('named', {}), False)
	stdout_pipe = None
	for artifact_name, artifact in task.get('artifacts', {}).viewitems():
		if artifact['type'] == 'stdout':
			stdout_pipe = subprocess.PIPE
	args = [target] + positional_args + joined_named_args
	print subprocess.list2cmdline(args)
	p = subprocess.Popen(args, stdout=stdout_pipe)
	returncode = p.wait()
	if returncode == 0:
		for artifact_name, artifact in task.get('artifacts', {}).viewitems():
			if artifact['type'] == 'stdout':
				config['mipmip.artifacts.' + task_name + '.' + artifact_name] = p.stdout.read()
	return p.returncode

def parse_dict_arg(arg, config, policy, use_glue=True):
	try:
		inner_glue = policy['inner_glue']
	except (TypeError, KeyError):
		inner_glue = '='
	try:
		wrap = policy['wrap']
	except (TypeError, KeyError):
		wrap = ''
	try:
		glue = policy['glue']
	except (TypeError, KeyError):
		glue = ','
	arg_list = []
	for key, val in arg.viewitems():
		try:
			inner_policy = policy[key]
		except (TypeError, KeyError):
			inner_policy = None
		arg_list += [key + inner_glue + parse_inner_value(val, config, inner_policy)]
	if use_glue:
		return wrap + glue.join(arg_list) + wrap
	return arg_list

def parse_list_arg(values, config, policy, use_glue=True):
	try:
		wrap = policy['wrap']
	except (TypeError, KeyError):
		wrap = ''
	try:
		glue = policy['glue']
	except (TypeError, KeyError):
		glue = ','
	for i in xrange(len(values)):
		try:
			inner_policy = policy[i]
		except (TypeError, KeyError):
			try:
				inner_policy = policy[unicode(i)]
			except (TypeError, KeyError):
				inner_policy = None
		values[i] = parse_inner_value(values[i], config, inner_policy)
	if use_glue:
		return wrap + glue.join(values) + wrap
	return values

def parse_inner_value(arg, config, policy):
	if type(arg) is unicode and arg.startswith('mipmip.artifacts.'):
		return config.get(arg, '')
	elif type(arg) is dict:
		return parse_dict_arg(arg, config, policy, ',')
	elif type(arg) is list:
		return parse_list_arg(arg, config, policy)
	return arg
	

if __name__ == "__main__":
	exit(main())

