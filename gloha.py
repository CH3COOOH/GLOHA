# -*- coding: UTF-8 -*-
import sys
import subprocess
import time
import os

import azlib.ut as aut
import azlib.pr as apr
import azlib.json as ajs
import tcp_latency
import ping_latency
import scheduler

VERSION = '0.2.1-230228'
FNAME_CONFIG_UPDATED = './FLAG_CONFIG_UPDATED'
PATH_PID = '/tmp/gloha_pid.json'
PERODIC_ACC = 5.
USAGE = '''Usage:
gloha <config.json> <0~3>
gloha -t
gloha -p
'''

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

		self.nodeSelected = '0'
		self.isNodeSelected = False
		self.isNodeSwitching = True
		self.taskproc = None

	def getInterval(self):
		return self.check_interval

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
		if self.select_scheme == 'priority':
			## Until 2023.02.25, "priority" is the only scheme of GLOHA

			self.log.print('[%s] Checking if node-0 available...' % self.label)
			la_0 = self.getLatency(self.server_list['0']['host'], self.check_scheme, timeout=self.server_list['0']['timeout']/1000.)
			
			## When node-0 failed, select an available one.
			## >>--- Node failover logic
			if la_0 < 0:
				self.log.print('[%s] Node-0 seems not available. Check the next.' % self.label)
				n_nodes = len(self.server_list.keys())
					## More than 1 nodes prepared
				if n_nodes > 1:
					## >>--- Node selection
					for i in self.server_list.keys():
						if i == '0':
							continue
						la_n = self.getLatency(self.server_list[i]['host'], self.check_scheme, timeout=self.server_list[i]['timeout']/1000.)
						if la_n >= 0:
							self.log.print('[%s] Select node-%s, with latency of %.2f ms.' % (self.label, i, la_n * 1000.))
							if self.nodeSelected != i:
								self.log.print('[%s] Switch to node-%s from node-%s.' % (self.label, i, self.nodeSelected), False)
								self.isNodeSwitching = True
							else:
								self.log.print('[%s] Keep node-%s.' % (self.label, i))
							self.nodeSelected = i
							self.isNodeSelected = True
							break
						else:
							self.log.print('[%s] Node-%s is also failed. Next...' % (self.label, i))
					## <<--- End node selection
					## All nodes died
					if self.isNodeSelected == False:
						self.log.print('[%s] Seems no node is available... What about node-0 now?' % self.label)
						return -1
			## <<--- End node failover logic
			## When node-0 is working / can work normally
			else:
				self.log.print('[%s] Node-0 is available, with latency of %.2f ms.' % (self.label, la_0 * 1000.))
				self.isNodeSelected = True
				if self.nodeSelected != "0":
					self.log.print('[%s] Switch to node-0 from node-%s.' % (self.label, self.nodeSelected), 1)
					self.isNodeSwitching = True
				else:
					self.log.print('[%s] Keep node-0.' % self.label)
				self.nodeSelected = "0"

			## When node switching is needed (or GLOHA is the 1st time launched)
			if self.isNodeSwitching:
				self.log.print('[%s] Executing task of node-%s...' % (self.label, self.nodeSelected))
				## When old process is running, kill it
				if self.taskproc != None:
					self.log.print('[%s] Kill the old process.' % self.label)
					os.system('kill -9 %d' % self.pid)
					self.taskproc.kill()
					self.log.print('[%s] Exec> %s' % (self.label, ' '.join(self.server_list[self.nodeSelected]['exec'])))
				## Run a new process
				self.taskproc = subprocess.Popen(self.server_list[self.nodeSelected]['exec'], shell=True)
				self.pid = self.taskproc.pid
				ajs.gracefulEditJSON(PATH_PID, {self.label: self.pid})
				self.log.print('[%s] PID: %d' % (self.label, self.pid))
				self.isNodeSwitching = False
			else:
				self.log.print('[%s] Node is not switched.' % self.label)


class GHA:
	def __init__(self, config_fname, log_level=0):
		self.log = apr.Log(log_level)
		self.log_level = log_level
		self.isLocked = False
		self.config_fname = config_fname
		self.config = ajs.gracefulLoadJSON(config_fname)
		self.taskQueen = []
		self.timetable = None

		self.isConfigBackuped = False

	def __del__(self):
		self.terminateRunning()

	def _isUpdatedConfigExist(self):
		try:
			config_now = ajs.gracefulLoadJSON(self.config_fname)
			return config_now != self.config
		except:
			self.log.print('<Update>Syntax error detected from the config file.', 2)
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

	def _startConfigMonitor(self):
		
		self.log.print('<Monitor>Checking if there is update in config file.')

		## Error detected in loading config file
		if self._isUpdatedConfigExist() < 0:
			self.log.print('<Monitor>Config error detected. Use previous config.', 2)

			## Save the latest correct config
			if self.isConfigBackuped == False:
				ajs.gracefulDumpJSON(self.config_fname + '.bak', self.config)
				self.isConfigBackuped = True
				## <Wait for the next period>

		## Update detected in config file
		elif self._isUpdatedConfigExist() == True:
			self.log.print('<Monitor>Update detected in config file.', 1)
			upacked_new_config = self._configUnpack()
			## Error detected in apply config file
			if upacked_new_config == -1:
				self.log.print('<Monitor>Config error detected. Use previous config.', 2)

				## Save the latest correct config
				if self.isConfigBackuped == False:
					ajs.gracefulDumpJSON(self.config_fname + '.bak', self.config)
					self.isConfigBackuped = True
					## <Wait for the next period>
				
			## No problem in updated config file
			else:
				self.isConfigBackuped = False
				self.reloadConfig()
				## <Wait for the next period>

		## No update in config file
		else:
			self.log.print('<Monitor>No update in config file.')
			isConfigBackuped = False
			## <Wait for the next period>

	def startDaemon(self):
		aut.gracefulWrite(PATH_PID, '{}')
		self.taskQueen = self._configUnpack()
		if self.taskQueen == -1:
			return -1
		self.timetable = scheduler.Scheduler()
		self.log.print('<Daemon>Adding task...', 0)
		for t in self.taskQueen:
			self.timetable.addTask([t.getInterval(), t.exec, None])
		self.timetable.addTask([10, self._startConfigMonitor, None])
		self.log.print('<Daemon>Start periodic tasks.', 0)
		self.timetable.periodicExecute(atStart=True, acc=PERODIC_ACC)

	def terminateRunning(self):
		pid_map = ajs.gracefulLoadJSON(PATH_PID)
		for t in pid_map.keys():
			self.log.print('<Monitor>Kill PID %d' % pid_map[t])
			os.system('kill -9 %d' % pid_map[t])
		self.timetable.terminate()

	def reloadConfig(self):
		self.log.print('Reload config...')
		self.terminateRunning()
		self.config = ajs.gracefulLoadJSON(self.config_fname)
		self.taskQueen = self._configUnpack()
		self.timetable = scheduler.Scheduler()
		for t in self.taskQueen:
			self.timetable.addTask([t.getInterval(), t.exec, None])
		self.timetable.addTask([10, self._startConfigMonitor, None])
		self.timetable.periodicExecute(atStart=True, acc=PERODIC_ACC)

def ps():
	pid_map = ajs.gracefulLoadJSON(PATH_PID)
	print('*** GLOHA managed ***')
	pid_list = []
	for p in pid_map.keys():
		print('%s\t%s' % (p, pid_map[p]))
		pid_list.append(str(pid_map[p]))
	print('\n*** SYSTEM managed ***')
	os.system('ps -u -p %s' % ','.join(pid_list))


if __name__ == '__main__':
	print('GLOHA ver %s' % VERSION)
	print(USAGE)
	path_conf = sys.argv[1]
	if sys.argv[1] == '-t':
		pid_map = ajs.gracefulLoadJSON(PATH_PID)
		for p in pid_map.keys():
			print('Kill PID %d...' % pid_map[p])
			os.system('kill -9 %d' % pid_map[p])
	elif sys.argv[1] == '-p':
		ps()
	else:
		log_level = int(sys.argv[2])
		g = GHA(path_conf, log_level)
		g.startDaemon()
	# except:
	# 	print('Usage: gloha <config_filename.json> <-t|0~2>')

