# -*- coding: UTF-8 -*-
import sys

import gha
import mgmt

'''
2024.01.27: Add quick mode to tcp latency check
2024.01.28:
 + Add redirect mode
 + Terminate GLOHA itself by -t
 + Simple config checker
'''

VERSION = '0.3.1-240128'
USAGE = '''Usage:
gloha <config.json> <0~3>
gloha -t
gloha -p
'''

if __name__ == '__main__':
	print('GLOHA ver %s' % VERSION)
	print(USAGE)
	path_conf = sys.argv[1]
	if sys.argv[1] == '-t':
		mgmt.terminate()
		
	elif sys.argv[1] == '-p':
		mgmt.ps()
	else:
		log_level = int(sys.argv[2])
		if mgmt.check_config(path_conf) == 0:
			g = gha.GHA(path_conf, log_level)
			g.startDaemon()
		else:
			exit(-1)
