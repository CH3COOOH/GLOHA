# -*- coding: UTF-8 -*-
import sys
import os

import azlib.json as ajs
import gha
from static import *

'''
2024.01.27: Add quick mode to tcp latency check
'''

VERSION = '0.2.3-240127'
USAGE = '''Usage:
gloha <config.json> <0~3>
gloha -t
gloha -p
'''

def ps():
	pid_map = ajs.gracefulLoadJSON(PATH_PID)
	print('*** GLOHA managed ***')
	pid_list = []
	for p in pid_map.keys():
		print('%s\t%s' % (p, pid_map[p]))
		pid_list.append(str(pid_map[p]))
	print('\n*** SYSTEM managed ***')
	os.system('ps -u -p %s' % ','.join(pid_list))


if __name__ == '__main__':
	print('GLOHA ver %s' % VERSION)
	print(USAGE)
	path_conf = sys.argv[1]
	if sys.argv[1] == '-t':
		pid_map = ajs.gracefulLoadJSON(PATH_PID)
		for p in pid_map.keys():
			print('Kill PID %d...' % pid_map[p])
			os.system('kill -9 %d' % pid_map[p])
	elif sys.argv[1] == '-p':
		ps()
	else:
		log_level = int(sys.argv[2])
		g = gha.GHA(path_conf, log_level)
		g.startDaemon()
