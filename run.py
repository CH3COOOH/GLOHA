from sys import argv
import json
import gloha

if __name__ == '__main__':
	path_conf = argv[1]
	with open(path_conf, 'r') as o:
		config = json.load(o)
	g = gloha.GHA(config)
	g.startDaemon()