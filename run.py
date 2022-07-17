from sys import argv
import json
import gloha

if __name__ == '__main__':
	path_conf = argv[1]
	if len(argv) > 2:
		verbal = int(argv[2])
	else:
		verbal = 0
	g = gloha.GHA(path_conf, {0: False, 1: True}[verbal])
	g.startDaemon()