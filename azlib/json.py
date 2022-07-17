import json
import time
import os.path
import os.system

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
	while True:
		if os.path.exists(fname + '.lck') == False:
			break
		time.sleep(lock_interval)
	os.system('touch %s.lck' % fname)
	with open(fname, method_w) as o:
		json.dump(j, o)
	os.system('rm -rf %s.lck' % fname)

def gracefulLoadJSON(fname, method_r='r'):
	j = None
	with open(fname, method_r) as o:
		j = json.load(o)
	return j