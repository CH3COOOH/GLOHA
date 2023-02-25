# -*- coding: UTF-8 -*-
import sys
import subprocess
import time
import multiprocessing
import json
from os import system

import azlib.ut as aut
import azlib.pr as apr
import azlib.json as ajs
import tcp_latency
import ping_latency

FNAME_CONFIG_UPDATED = './FLAG_CONFIG_UPDATED'
PATH_PID = '/tmp/gloha_pid.json'

## Global HA
class GHA_INSTANCE:
	def __init__(self, label, check_interval, check_scheme, select_scheme, server_list, log_level=0):
		self.log = apr.Log(log_level)
		self.log_level = log_level
		self.label = label
		self.check_interval = check_interval
		self.check_scheme = check_scheme
		self.select_scheme = select_scheme
		self.server_list = server_list
		self.status_list = {}
		self.pid = -99
		self._serverUnpack()

	def _serverUnpack(self):
		ids = self.server_list.keys()
		for i in ids:
			self.status_list[i] = 0

	def getLatency(self, host_port, scheme, timeout=3.):
		if scheme == 'tcp':
			return tcp_latency.getAveLatency(host_port, timeout=timeout)
		elif scheme == 'icmp':
			return ping_latency.getAveLatency(host_port, timeout=timeout)
		else:
			return -1

	def _statusUpdate(self):
		for i in self.status_list.keys():
			host = self.server_list[i]['host']
			self.status_list[i] = self.getLatency(host, self.check_scheme)

	def getLabel(self):
		return self.label

	def exec(self):
		nodeSelected = "0"
		isNodeSelected = False
		isNodeSwitching = True
		taskproc = None

		if self.select_scheme == 'priority':
			## Until 2023.02.25, it is the only scheme of GLOHA
			while True:
				self.log.print('Checking if node-0 available...')
				la_0 = self.getLatency(self.server_list['0']['host'], self.check_scheme, timeout=self.server_list['0']['timeout']/1000.)
				
				## If priority 0 failed, select an available one.
				if la_0 < 0:
					self.log.print('Node-0 seems not available. Check the next.')
					n_nodes = len(self.server_list.keys())
					if n_nodes > 1:
						for i in self.server_list.keys():
							if i == '0':
								continue
							la_n = self.getLatency(self.server_list[i]['host'], self.check_scheme, timeout=self.server_list[i]['timeout']/1000.)
							if la_n >= 0:
								self.log.print('Select node-%s, with latency of %.2f ms.' % (i, la_n * 1000.))
								if nodeSelected != i:
									self.log.print('Switch to node-%s from node-%s.' % (i, nodeSelected), False)
									isNodeSwitching = True
								else:
									self.log.print('Keep node-%s.' % i)
								nodeSelected = i
								isNodeSelected = True
								break
							else:
								self.log.print('Node-%s is also failed. Next...' % i)
						if isNodeSelected == False:
							self.log.print('Seems no node is available... What about node-0 now?')
							time.sleep(self.check_interval)
							continue
				else:
					self.log.print('Node-0 is available, with latency of %.2f ms.' % (la_0 * 1000.))
					isNodeSelected = True
					if nodeSelected != "0":
						self.log.print('Switch to node-0 from node-%s.' % (nodeSelected), 1)
						isNodeSwitching = True
					else:
						self.log.print('Keep node-0.')
					nodeSelected = "0"

				if isNodeSwitching:
					self.log.print('Executing task of node-%s...' % nodeSelected)
					if taskproc != None:
						self.log.print('Kill the old process.')
						taskproc.kill()
						self.log.print('Exec> %s' % ' '.join(self.server_list[nodeSelected]['exec']))
					taskproc = subprocess.Popen(self.server_list[nodeSelected]['exec'], shell=True)
					self.pid = taskproc.pid
					ajs.safelyEditJSON(PATH_PID, {self.label: self.pid})
					self.log.print('PID: %d' % self.pid)
					isNodeSwitching = False
				else:
					self.log.print('Node is not switched.')

				time.sleep(self.check_interval)

class GHA:
	def __init__(self, config_fname, log_level=0):
		self.log = apr.Log(log_level)
		self.log_level = log_level
		self.isLocked = False
		self.config_fname = config_fname
		self.config = ajs.gracefulLoadJSON(config_fname)
		self.taskQueen = []
		self.taskmap = {}

	def __del__(self):
		for t in self.taskQueen:
			self.taskmap[t.getLabel()].terminate()
			system('kill -9 %d' % pid_map[t.getLabel()])

	def _isUpdatedConfigExist(self):
		try:
			config_now = ajs.gracefulLoadJSON(self.config_fname)
			return config_now != self.config
		except:
			self.log.print('<Update>Syntax error detected from the config file.', 1)
			return -1

	def _configUnpack(self):
		container = []
		# for profile in self.config.keys():
		# 		label = profile
		# 		check_interval = self.config[profile]['check_interval']
		# 		check_scheme = self.config[profile]['check_scheme']
		# 		select_scheme = self.config[profile]['select_scheme']
		# 		server_list = self.config[profile]['server_list']
		# 		container.append(GHA_INSTANCE(label, check_interval, check_scheme, select_scheme, server_list, self.log_level))
		try:
			for profile in self.config.keys():
				label = profile
				check_interval = self.config[profile]['check_interval']
				check_scheme = self.config[profile]['check_scheme']
				select_scheme = self.config[profile]['select_scheme']
				server_list = self.config[profile]['server_list']
				container.append(GHA_INSTANCE(label, check_interval, check_scheme, select_scheme, server_list, self.log_level))
		except:
			self.log.print('<Unpack>Syntax error detected from the config file.', 2)
			return -1
		return container

	def _startConfigMonitor(self, interval=10):
		isConfigBackuped = False
		while True:
			time.sleep(interval)
			self.log.print('<Monitor>Checking if there is update in config file.')

			## Error detected in loading config file
			if self._isUpdatedConfigExist() < 0:
				self.log.print('<Monitor>Config error detected. Use previous config.')

				## Save the latest correct config
				if isConfigBackuped == False:
					# with open(self.config_fname + '.bak', 'w') as o:
					# 	json.dump(self.config, o)
					ajs.gracefulDumpJSON(self.config_fname + '.bak', self.config)
					isConfigBackuped = True

			## Update detected in config file
			elif self._isUpdatedConfigExist() == True:
				self.log.print('<Monitor>Update detected in config file.', write=False)
				upacked_new_config = self._configUnpack()
				## Error detected in apply config file
				if upacked_new_config == -1:
					self.log.print('<Monitor>Config error detected. Use previous config.')

					## Save the latest correct config
					if isConfigBackuped == False:
						# with open(self.config_fname + '.bak', 'w') as o:
						# 	json.dump(self.config, o)
						ajs.gracefulDumpJSON(self.config_fname + '.bak', self.config)
						isConfigBackuped = True
				
				## No problem in updated config file
				else:
					isConfigBackuped = False
					self.reloadConfig()

			## No update in config file
			else:
				self.log.print('<Monitor>No update in config file.')
				isConfigBackuped = False

	def startDaemon(self):
		system('touch %s.lck' % PATH_PID)
		aut.gracefulWrite(PATH_PID, '{}')
		system('rm -rf %s.lck' % PATH_PID)
		self.taskQueen = self._configUnpack()
		if self.taskQueen == -1:
			return -1
		for t in self.taskQueen:
			self.taskmap[t.getLabel()] = multiprocessing.Process(target=t.exec)
			self.taskmap[t.getLabel()].start()
		self._startConfigMonitor()

	def terminateRunning(self):
		pid_map = ajs.gracefulLoadJSON(PATH_PID)
		for t in self.taskQueen:
			self.log.print('<Monitor>Kill PID %d' % pid_map[t.getLabel()])
			self.taskmap[t.getLabel()].terminate()
			system('kill -9 %d' % pid_map[t.getLabel()])

	def reloadConfig(self):
		self.log.print('Reload config...')
		self.terminateRunning()
		self.config = ajs.gracefulLoadJSON(self.config_fname)
		self.taskQueen = self._configUnpack()
		for t in self.taskQueen:
			self.taskmap[t.getLabel()] = multiprocessing.Process(target=t.exec)
			self.taskmap[t.getLabel()].start()

if __name__ == '__main__':
	path_conf = sys.argv[1]
	if sys.argv[2] == '-t':
		pid_map = ajs.gracefulLoadJSON(PATH_PID)
		for p in pid_map.keys():
			print('Kill PID %d...' % pid_map[p])
			system('kill -9 %d' % pid_map[p])
	else:
		log_level = int(sys.argv[2])
		g = GHA(path_conf, log_level)
		g.startDaemon()
	# except:
	# 	print('Usage: gloha <config_filename.json> <-t|0~2>')

