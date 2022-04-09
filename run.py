from sys import argv
import json
import gloha

if __name__ == '__main__':
	path_conf = argv[1]
	if len(argv) > 2:
		verbal = int(argv[2])
	else:
		verbal = 0
	with open(path_conf, 'r') as o:
		config = json.load(o)
	g = gloha.GHA(config, {0: False, 1: True}[verbal])
	g.startDaemon()