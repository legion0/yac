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
	
	pprint(config)

	if args.command == 'run':
		workflow = config.get('mipmip.workflow.' + args.target, None)
		if workflow is not None:
			return run_workflow(workflow, config)
		task = config.get('mipmip.task.' + args.target, None)
		if task is not None:
			return run_task(task)

def run_workflow(workflow, config):
	for task_name in workflow.get('tasks', []):
		task = config.get('mipmip.task.' + task_name, None)
		returncode = run_task(task)
		if returncode != 0:
			return returncode
	return 0

def run_task(task):
	if task is None:
		return
	target = task['target']
	positional_args = task.get('args', {}).get('positional', [])
	returncode = subprocess.call([target] + positional_args)
	return returncode

if __name__ == "__main__":
	main()

