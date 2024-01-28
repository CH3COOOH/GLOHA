# -*- coding: UTF-8 -*-
import os

import azlib.pr as apr
import azlib.json as ajs
import scheduler
import gha_instance
from static import *

class GHA:
	def __init__(self, config_fname, log_level=0):
		self.log = apr.Log(log_level)
		self.log_level = log_level
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

	def _configUnpack(self, ext_conf=None, isCheckMode=False):
		container = []
		if ext_conf == None:
			config = self.config
		else:
			config = ext_conf
		try:
			for profile in config.keys():
				label = profile
				check_interval = config[profile]['check_interval']
				check_scheme = config[profile]['check_scheme']
				if 'run_mode' in config[profile].keys():
					run_mode = config[profile]['run_mode']
				else:
					run_mode = 'ps'
				server_list = config[profile]['server_list']
				if isCheckMode == False:
					container.append(gha_instance.GHA_INSTANCE(label, check_interval, check_scheme, run_mode, server_list, self.log_level))
		except:
			self.log.print('<Unpack>Syntax error detected from the config file.', 2)
			return -1
		return container

	def _startConfigMonitor(self):
		
		self.log.print('<Monitor>Checking if there is update in config file.')
		isUpdated = self._isUpdatedConfigExist()

		if isUpdated < 0:
			## Error detected in loading config file
			self.log.print('<Monitor>Config error detected. Use previous config.', 2)

			## Save the latest correct config
			if self.isConfigBackuped == False:
				ajs.gracefulDumpJSON(self.config_fname + '.bak', self.config)
				self.isConfigBackuped = True
			return -1
			## <Wait for the next period>

		elif isUpdated == True:
			## Update detected in config file
			self.log.print('<Monitor>Update detected in config file.')
			if self._configUnpack(ext_conf=ajs.gracefulLoadJSON(self.config_fname), isCheckMode=True) == -1:
				## Error detected in apply config file
				self.log.print('<Monitor>Config error detected. Use previous config.', 2)

				## Save the latest correct config
				if self.isConfigBackuped == False:
					## When the config is not backuped
					ajs.gracefulDumpJSON(self.config_fname + '.bak', self.config)
					self.isConfigBackuped = True
				return -1
				## <Wait for the next period>
			else:
				## No problem in updated config file
				self.isConfigBackuped = False
				self.reloadConfig(False)
				return 0
				## <Wait for the next period>
		else:
			## No update in config file
			self.log.print('<Monitor>No update in config file.')
			isConfigBackuped = False
			return 0
			## <Wait for the next period>

	def terminateRunning(self):
		self.log.print('GHA::terminateRunning > Terminate running task...', 0)
		pid_map = ajs.gracefulLoadJSON(PATH_PID)
		for t in self.taskQueen:
			t.suicide()
		self.timetable.terminate()

	def reloadConfig(self, isFirstTime):
		if isFirstTime == False:
			self.log.print('<Reload>Reload config...')
			self.terminateRunning()
			self.log.print('GHA::reloadConfig > Reload config...', 0)
			self.config = ajs.gracefulLoadJSON(self.config_fname)
		self.log.print('GHA::reloadConfig > Config unpack...', 0)
		self.taskQueen = self._configUnpack()
		if self.taskQueen == -1:
			return -1
		self.timetable = scheduler.Scheduler()
		self.log.print('GHA::reloadConfig > Adding task...', 0)
		for t in self.taskQueen:
			self.timetable.addTask([t.getInterval(), t.exec, None])
		self.timetable.addTask([10, self._startConfigMonitor, None])
		self.log.print('GHA::reloadConfig > Start periodic tasks.', 0)
		self.timetable.periodicExecute(atStart=True, acc=PERODIC_ACC)

	def initRedirectMode(self):
		if os.path.exists(PATH_RED_RULE) == True:
			rules = ajs.gracefulLoadJSON(PATH_RED_RULE)
			## Remove old rules
			for label in rules.keys():
				self.log.print(f"GHA::initRedirectMode > Remove old rules for [{label}]", 2)
				os.system(f"iptables -t nat -D PREROUTING {rules[label]['rule_pre']}")
				os.system(f"iptables -t nat -D POSTROUTING {rules[label]['rule_post']}")
		ajs.gracefulDumpJSON(PATH_RED_RULE, {})

	def startDaemon(self):
		os.system(f"rm -rf {PATH_PID}.lck")
		os.system(f"rm -rf {PATH_RED_RULE}.lck")
		ajs.gracefulDumpJSON(PATH_PID, {'GLOHA': os.getpid()})
		self.initRedirectMode()
		self.reloadConfig(True)