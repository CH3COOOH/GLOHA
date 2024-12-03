# -*- coding: UTF-8 -*-
import os
import subprocess

import azlib.json as ajs
import plugin.c2j as c2j
from static import *

def ps():
	if os.path.exists(PATH_PID) == True:
		print('*** GLOHA managed ***')
		pid_map = ajs.gracefulLoadJSON(PATH_PID)
		pid_list = ['ps']
		for p in pid_map.keys():
			print('%s\t%s' % (p, pid_map[p]))
			pid_list.append(str(pid_map[p]))
		print('\n*** SYSTEM managed ***')
		# os.system('ps -u -p %s' % ','.join(pid_list))
		ps_ex = subprocess.run(pid_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		ps_out = ps_ex.stdout.decode("utf-8")
		print(ps_out)
	else:
		print('PID map is not found.')

	if os.path.exists(PATH_RED_RULE) == True:
		print('\n*** Rules added by GLOHA ***')
		rule_map = ajs.gracefulLoadJSON(PATH_RED_RULE)
		for label in rule_map.keys():
			cmd_pre = f"iptables -t nat -A PREROUTING {rule_map[label]['rule_pre']}"
			cmd_post = f"iptables -t nat -A POSTROUTING {rule_map[label]['rule_post']}"
			print(f"(.) {cmd_pre}")
			print(f"(.) {cmd_post}")
	else:
		print('Redirect rule is not found.')


def terminate():
	if os.path.exists(PATH_PID) == True:
		pid_map = ajs.gracefulLoadJSON(PATH_PID)
		for p in pid_map.keys():
			print(f"Kill PID [{pid_map[p]}] of process [{p}]...")
			os.system('kill -9 %d' % pid_map[p])
	else:
		print('PID map is not found.')

	if os.path.exists(PATH_RED_RULE) == True:
		rule_map = ajs.gracefulLoadJSON(PATH_RED_RULE)
		for label in rule_map.keys():
			cmd_remove_pre = f"iptables -t nat -D PREROUTING {rule_map[label]['rule_pre']}"
			cmd_remove_post = f"iptables -t nat -D POSTROUTING {rule_map[label]['rule_post']}"
			os.system(cmd_remove_pre)
			os.system(cmd_remove_post)
			print(f"(-) {cmd_remove_pre}")
			print(f"(-) {cmd_remove_post}")
		ajs.gracefulDumpJSON(PATH_RED_RULE, {})
	else:
		print('Redirect rule is not found.')

def loadConfig(fname_config):
	## Also used by gha.py
	if os.path.splitext(fname_config)[-1].lower() == '.json':
		return ajs.gracefulLoadJSON(fname_config)
	else:
		return c2j.conf2Json(fname_config)

def check_config(fname_config):
	print('Checking config...')
	conf = loadConfig(fname_config)
	# key4all = ['check_scheme']
	# key4ps = ['host', 'exec', 'timeout']
	# key4red = ['host', 'target', 'timeout']
	if 'GLOHA' in conf.keys():
		print('[!] GLOHA cannot be set as label. Exit...')
		return -1
	return 0

if __name__ == '__main__':
	print(check_config('config.json'))
	print(check_config('config_simple.conf'))