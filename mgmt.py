# -*- coding: UTF-8 -*-
import os

import azlib.json as ajs
from static import *

def ps():
	pid_map = ajs.gracefulLoadJSON(PATH_PID)
	print('*** GLOHA managed ***')
	pid_list = []
	for p in pid_map.keys():
		print('%s\t%s' % (p, pid_map[p]))
		pid_list.append(str(pid_map[p]))
	print('\n*** SYSTEM managed ***')
	os.system('ps -u -p %s' % ','.join(pid_list))

def terminate():
	if os.path.exists(PATH_PID) == True:
		pid_map = ajs.gracefulLoadJSON(PATH_PID)
		for p in pid_map.keys():
			print('Kill PID %d...' % pid_map[p])
			os.system('kill -9 %d' % pid_map[p])
	else:
		print('PID map is not found.')

	if os.path.exists(PATH_RED_RULE) == True:
		rule_map = ajs.gracefulLoadJSON(PATH_RED_RULE)
		for label in rules.keys():
			cmd_remove_pre = f"iptables -t nat -D PREROUTING {rules[label]['rule_pre']}"
			cmd_remove_post = f"iptables -t nat -D POSTROUTING {rules[label]['rule_post']}"
			os.system(cmd_remove_pre)
			os.system(cmd_remove_post)
			print(f"(-) {cmd_remove_pre}")
			print(f"(-) {cmd_remove_post}")
	else:
		print('Redirect rule is not found.')