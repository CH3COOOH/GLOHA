import json

def gracefulEditJSON(fname, content, method_r='r', method_w='w'):
	j = None
	with open(fname, method_r) as o:
		j = json.load(o)
	for k in content.keys():
		j[k] = content[k]
	with open(fname, method_w) as o:
		json.dump(j, o)

def gracefulLoadJSON(fname, method_r='r'):
	j = None
	with open(fname, method_r) as o:
		j = json.load(o)
	return j