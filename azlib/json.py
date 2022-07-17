import json
import time
from os import system, path

def gracefulEditJSON(fname, content, method_r='r', method_w='w'):
	j = None
	with open(fname, method_r) as o:
		j = json.load(o)
	for k in content.keys():
		j[k] = content[k]
	with open(fname, method_w) as o:
		json.dump(j, o)

def safelyEditJSON(fname, content, method_r='r', method_w='w', lock_interval=.5):
	j = None
	with open(fname, method_r) as o:
		j = json.load(o)
	for k in content.keys():
		j[k] = content[k]
	flag_print = 0
	while True:
		if path.exists(fname + '.lck') == False:
			break
		if flag_print == 0:
			print('Waiting for unlock on file %s...' % fname)
			flag_print = 1
		time.sleep(lock_interval)
	system('touch %s.lck' % fname)
	with open(fname, method_w) as o:
		json.dump(j, o)
	system('rm -rf %s.lck' % fname)

def gracefulLoadJSON(fname, method_r='r'):
	j = None
	with open(fname, method_r) as o:
		j = json.load(o)
	return j