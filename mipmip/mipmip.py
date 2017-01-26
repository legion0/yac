#!/usr/bin/env python2

import argparse
import json
import os
import subprocess
import sys

from datetime import datetime
from pprint import pprint

import _jsonnet


def parse_args():
  parser = argparse.ArgumentParser(description='Process some integers.')
  parser.add_argument('config', help='A path to a config file to load.')
  parser.add_argument('action', choices={'run', 'dry_run', 'print'}, help='What to do.')
  parser.add_argument('target', help='On what target to perform the action.')
  args = parser.parse_args()
  return args


def main():
  args = parse_args()

  config = _jsonnet.evaluate_file(args.config)
  config = json.loads(config)

  if args.action == 'print':
    pprint(config, indent=2)
    exit(0)

  is_dry_run = (args.action == 'dry_run')
  workflow = config.get('mipmip.workflow.' + args.target, None)
  if workflow is not None:
    return run_workflow(workflow, config, is_dry_run)
  task = config.get('mipmip.task.' + args.target, None)
  if task is not None:
    return run_task(args.target, task, config, is_dry_run)

def run_workflow(workflow, config, is_dry_run):
  for task_name in workflow.get('tasks', []):
    task = config.get('mipmip.task.' + task_name, None)
    returncode = run_task(task_name, task, config, is_dry_run)
    if returncode != 0:
      return returncode
  return 0


def print_cmd(cmd):
  cmd_str = subprocess.list2cmdline(cmd)
  time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  print "[%s] %s" % (time_str, cmd_str)


def run_task(task_name, task, config, is_dry_run):
  if task is None:
    print "Cannot find task: %r" % task_name
    return 1
  target = task['target']
  args = task.get('args', {})
  arg_policy = config.get('mipmip.arg_policy.' + task_name, {})
  positional_args = parse_list_arg(args.get('positional', []), config, arg_policy.get('positional', {}), False)
  joined_named_args = parse_dict_arg(args.get('named', {}), config, arg_policy.get('named', {}), False)
  stdout_pipe = None
  for artifact_name, artifact in task.get('artifacts', {}).viewitems():
    if artifact['type'] == 'stdout':
      stdout_pipe = subprocess.PIPE
  args = [target] + positional_args + joined_named_args
  print_cmd(args)
  returncode = 0
  if not is_dry_run:
    p = subprocess.Popen(args, stdout=stdout_pipe)
    returncode = p.wait()
  if returncode == 0 and not is_dry_run:
    for artifact_name, artifact in task.get('artifacts', {}).viewitems():
      if artifact['type'] == 'stdout':
        stdout = p.stdout.read()
        print stdout
        config['mipmip.artifacts.' + task_name + '.' + artifact_name] = stdout
  return returncode


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

