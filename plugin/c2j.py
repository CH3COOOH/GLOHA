def conf2Json(conf_txt):
	container = {}
	block_now = None
	block_signal = 0
	node_ctr = 0
	for line in conf_txt.split('\n'):
		if line == '' or line[0] == '#':
			continue
		if line[0] == '*':
		## New block
			ndoe_ctr = 0
			block_now = line[1:]
			block_signal = 1
			## Ready to find meta info
		else:
			if block_signal == 1:
				chk_interval, chk_scheme, run_mode = line.split(', ')
				container[block_now] = {'check_interval': chk_interval, 'check_scheme': chk_scheme, 'run_mode': run_mode, 'server_list': {}}
				block_signal = 2
			elif block_signal == 2:
				host, exec_, timeout = line.split(', ')
				timeout = int(timeout)
				if 'redirect:' in container[block_now]['run_mode']:
					container[block_now]['server_list'][str(ndoe_ctr)] = {'host': host, 'target': exec_, 'timeout': timeout}
				else:
					container[block_now]['server_list'][str(ndoe_ctr)] = {'host': host, 'exec': exec_, 'timeout': timeout}
				ndoe_ctr += 1
	return container

if __name__ == '__main__':
	import json
	with open('test_cfg.txt', 'r') as o:
		c2j = conf2Json(o.read())
	print(c2j)
	json.dump(c2j, open('test_js.json', 'w'))