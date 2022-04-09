# -*- coding: UTF-8 -*-

import subprocess
import time
import multiprocessing

import tcp_latency

# proc = subprocess.Popen(['ping','1.1.1.1'], shell=True)

## Global HA
class GHA_INSTANCE:
	def __init__(self, label, check_interval, check_scheme, select_scheme, server_list):
		self.label = label
		self.check_interval = check_interval
		self.check_scheme = check_scheme
		self.select_scheme = select_scheme
		self.server_list = server_list
		self.status_list = {}
		self._serverUnpack()

	def _serverUnpack(self):
		ids = self.server_list.keys()
		for i in ids:
			self.status_list[i] = 0

	def _statusUpdate(self):
		for i in status_list.keys():
			host = self.server_list[i]['host']
			port = self.server_list[i]['port']
			status_list[i] = tcp_latency.getAveLatency(host, port)

	def _log(self, text, level=0):
		level_map = ['INFO', 'WARN', 'ERROR']
		localtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) 
		msg = '[%s][%s][%s] %s' % (localtime, level_map[level], self.label, text)
		print(msg)
		if level > 0:
			with open('event.log', 'a') as o:
				o.write(msg + '\n')


	def getLabel(self):
		return self.label

	def exec(self):
		nodeSelected = "0"
		isNodeSelected = False
		isNodeSwitching = True
		taskproc = None

		if self.select_scheme == 'priority':

			while True:

				self._log('Checking if node-0 available...')
				la_0 = tcp_latency.getAveLatency(self.server_list['0']['host'], self.server_list['0']['port'])
				
				## If priority 0 failed, select an available one.

				if la_0 < 0:
					self._log('Node-0 seems not available. Check the next.')
					n_nodes = len(self.server_list.keys())
					if n_nodes > 1:
						for i in self.server_list.keys():
							if i == '0':
								continue
							la_n = tcp_latency.getAveLatency(self.server_list[i]['host'], self.server_list[i]['port'])
							if la_n >= 0:
								self._log('Select node-%s, with latency of %.2f ms.' % (i, la_n * 1000.))
								if nodeSelected != i:
									self._log('Switch to node-%s from node-%s.' % (i, nodeSelected), 1)
									isNodeSwitching = True
								else:
									self._log('Keep node-%s.' % i)
								nodeSelected = i
								isNodeSelected = True
								break
							else:
								self._log('Node-%s is also failed. Next...' % i)
						if isNodeSelected == False:
							self._log('Seems no node is available... What about node-0 now?')
							continue
				else:
					self._log('Node-0 is available, with latency of %.2f ms.' % (la_0 * 1000.))
					isNodeSelected = True
					if nodeSelected != "0":
						self._log('Switch to node-0 from node-%s.' % (nodeSelected), 1)
						isNodeSwitching = True
					else:
						self._log('Keep node-0.')
					nodeSelected = "0"

				if isNodeSwitching:
					self._log('Executing task of node-%s...' % nodeSelected)
					if taskproc != None:
						self._log('Kill the old process.')
						taskproc.terminate()
						self._log('Exec> %s' % ' '.join(self.server_list[nodeSelected]['exec']))
					taskproc = subprocess.Popen(self.server_list[nodeSelected]['exec'], shell=True)
					isNodeSwitching = False
				else:
					self._log('Node is not switched.')

				time.sleep(self.check_interval)


class GHA:
	def __init__(self, config):
		self.config = config
		self.taskQueen = []
		self._configUnpack()

	def _configUnpack(self):
		for profile in self.config.keys():
			label = profile
			check_interval = self.config[profile]['check_interval']
			check_scheme = self.config[profile]['check_scheme']
			select_scheme = self.config[profile]['select_scheme']
			server_list = self.config[profile]['server_list']
			self.taskQueen.append(GHA_INSTANCE(label, check_interval, check_scheme, select_scheme, server_list))


	def startDaemon(self):
		taskmap = {}
		for t in self.taskQueen:
			taskmap[t.getLabel()] = multiprocessing.Process(target=t.exec)
			taskmap[t.getLabel()].start()
			# t.exec()

if __name__ == '__main__':
	import json
	with open('config.json', 'r') as o:
		config = json.load(o)
	g = GHA(config)
	g.startDaemon()


