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
	positional_args = parse_list_arg(task.get('args', {}).get('positional', []), config, None)
	joined_named_args = parse_dict_arg(task.get('args', {}).get('named', {}), config, None)
	stdout_pipe = None
	for artifact_name, artifact in task.get('artifacts', {}).viewitems():
		if artifact['type'] == 'stdout':
			stdout_pipe = subprocess.PIPE
	print repr([target] + positional_args + joined_named_args)
	p = subprocess.Popen([target] + positional_args + joined_named_args, stdout=stdout_pipe)
	returncode = p.wait()
	if returncode == 0:
		for artifact_name, artifact in task.get('artifacts', {}).viewitems():
			if artifact['type'] == 'stdout':
				config['mipmip.artifacts.' + task_name + '.' + artifact_name] = p.stdout.read()
	return p.returncode

def parse_dict_arg(arg, config, glue=' ', inner_glue='=', wrap=''):
	if 'mipmip.glue' in arg:
		glue = arg['mipmip.glue']
	if 'mipmip.inner_glue' in arg:
		inner_glue = arg['mipmip.inner_glue']
	if 'mipmip.wrap' in arg:
		wrap = arg['mipmip.wrap']
	if 'mipmip.values' in arg:
		return parse_list_arg(arg['mipmip.values'], config, glue)
	arg_list = []
	for key, val in arg.viewitems():
		if key == 'mipmip.glue':
			continue
		if key == 'mipmip.inner_glue':
			continue
		if key == 'mipmip.wrap':
			continue
		arg_list += [key + inner_glue + parse_inner_value(val, config)]
	if glue is not None:
		return wrap + glue.join(arg_list) + wrap
	return arg_list

def parse_list_arg(values, config, glue=','):
	for i in xrange(len(values)):
		values[i] = parse_inner_value(values[i], config)
	if glue is not None:
		return glue.join(values)
	return values

def parse_inner_value(arg, config):
	if type(arg) is unicode and arg.startswith('mipmip.artifacts.'):
		return config.get(arg, '')
	elif type(arg) is dict:
		return parse_dict_arg(arg, config, ',')
	elif type(arg) is list:
		return parse_list_arg(arg, config)
	return arg
	

if __name__ == "__main__":
	main()

