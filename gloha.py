# -*- coding: UTF-8 -*-

import subprocess
import time
import multiprocessing
import json
from os import system

import azlib.ut as aut
import azlib.pr as apr
import azlib.json as ajson
import tcp_latency

FNAME_CONFIG_UPDATED = './FLAG_CONFIG_UPDATED'
PATH_PID = '/tmp/gloha_pid.json'

## Global HA
class GHA_INSTANCE:
	def __init__(self, label, check_interval, check_scheme, select_scheme, server_list, verbal=False):
		self.verbal = verbal
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

	def _statusUpdate(self):
		for i in status_list.keys():
			host = self.server_list[i]['host']
			port = self.server_list[i]['port']
			status_list[i] = tcp_latency.getAveLatency(host, port)

	def _log(self, text, level=0):
		level_map = ['INFO', 'WARN', 'ERROR']
		localtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) 
		msg = '[%s][%s][%s] %s' % (localtime, level_map[level], self.label, text)
		if self.verbal:
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
				la_0 = tcp_latency.getAveLatency(self.server_list['0']['host'], self.server_list['0']['port'], timeout=self.server_list['0']['timeout']/1000.)
				
				## If priority 0 failed, select an available one.

				if la_0 < 0:
					self._log('Node-0 seems not available. Check the next.')
					n_nodes = len(self.server_list.keys())
					if n_nodes > 1:
						for i in self.server_list.keys():
							if i == '0':
								continue
							la_n = tcp_latency.getAveLatency(self.server_list[i]['host'], self.server_list[i]['port'], timeout=self.server_list[i]['timeout']/1000.)
							if la_n >= 0:
								self._log('Select node-%s, with latency of %.2f ms.' % (i, la_n * 1000.))
								if nodeSelected != i:
									self._log('Switch to node-%s from node-%s.' % (i, nodeSelected), False)
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
							time.sleep(self.check_interval)
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
						taskproc.kill()
						self._log('Exec> %s' % ' '.join(self.server_list[nodeSelected]['exec']))
					taskproc = subprocess.Popen(self.server_list[nodeSelected]['exec'], shell=True)
					self.pid = taskproc.pid
					ajson.safelyEditJSON(PATH_PID, {self.label: self.pid})
					self._log('PID: %d' % self.pid)
					isNodeSwitching = False
				else:
					self._log('Node is not switched.')

				time.sleep(self.check_interval)

class GHA:
	def __init__(self, config_fname, verbal=False):
		self.isLocked = False
		self.verbal = verbal
		self.config_fname = config_fname
		self.config = self._loadConfig(config_fname)
		self.taskQueen = []
		self.taskmap = {}
		self._configUnpack()

	def __del__(self):
		for t in self.taskQueen:
			self.taskmap[t.getLabel()].terminate()
			system('kill -9 %d' % pid_map[t.getLabel()])

	def _loadConfig(self, fname):
		with open(self.config_fname, 'r') as o:
			return json.load(o)

	def _isUpdatedConfigExist(self):
		try:
			config_now = self._loadConfig(self.config_fname)
			return config_now != self.config
		except:
			apr.log('<Update>Syntax error detected from the config file.', 1)
			return -1

	def _configUnpack(self):
		container = []
		try:
			for profile in self.config.keys():
				label = profile
				check_interval = self.config[profile]['check_interval']
				check_scheme = self.config[profile]['check_scheme']
				select_scheme = self.config[profile]['select_scheme']
				server_list = self.config[profile]['server_list']
				container.append(GHA_INSTANCE(label, check_interval, check_scheme, select_scheme, server_list, self.verbal))
		except:
			apr.log('<Unpack>Syntax error detected from the config file.', 1)
			return -1
		self.taskQueen = container.copy()
		return 0

	def _startConfigMonitor(self, interval=10):
		isConfigBackuped = False
		while True:
			time.sleep(interval)
			apr.log('<Monitor>Checking if there is update in config file.')

			## Error detected in loading config file
			if self._isUpdatedConfigExist() < 0:
				apr.log('<Monitor>Config error detected. Use previous config.')

				## Save the latest correct config
				if isConfigBackuped == False:
					with open(self.config_fname + '.bak', 'w') as o:
						json.dump(self.config, o)
					isConfigBackuped = True

			## Update detected in config file
			elif self._isUpdatedConfigExist() == True:
				apr.log('<Monitor>Update detected in config file.', write=False)

				## Error detected in apply config file
				if self._configUnpack == -1:
					apr.log('<Monitor>Config error detected. Use previous config.')

					## Save the latest correct config
					if isConfigBackuped == False:
						with open(self.config_fname + '.bak', 'w') as o:
							json.dump(self.config, o)
						isConfigBackuped = True
				
				## No problem in updated config file
				else:
					isConfigBackuped = False
					self.reloadConfig()

			## No update in config file
			else:
				apr.log('<Monitor>No update in config file.')
				isConfigBackuped = False

	def startDaemon(self):
		system('rm -rf %s.lck' % PATH_PID)
		aut.gracefulWrite(PATH_PID, '{}')
		for t in self.taskQueen:
			self.taskmap[t.getLabel()] = multiprocessing.Process(target=t.exec)
			self.taskmap[t.getLabel()].start()
		self._startConfigMonitor()

	def reloadConfig(self):
		pid_map = ajson.gracefulLoadJSON(PATH_PID)

		for t in self.taskQueen:
			apr.log('<Monitor>Kill PID %d' % pid_map[t.getLabel()])
			self.taskmap[t.getLabel()].terminate()
			system('kill -9 %d' % pid_map[t.getLabel()])

		apr.log('Reload config...')
		self.config = self._loadConfig(self.config_fname)
		self._configUnpack()
		for t in self.taskQueen:
			self.taskmap[t.getLabel()] = multiprocessing.Process(target=t.exec)
			self.taskmap[t.getLabel()].start()

if __name__ == '__main__':
	g = GHA('config.json', True)
	g.startDaemon()


