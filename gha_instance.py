# -*- coding: UTF-8 -*-
import subprocess
from os import system, path

import azlib.pr as apr
import azlib.json as ajs
import azlib.tcp_latency as tcp_latency
import azlib.ping_latency as ping_latency
from static import *

## Global HA
class GHA_INSTANCE:
	def __init__(self, label, check_interval, check_scheme, run_mode, server_list, log_level=0):
		self.log = apr.Log(log_level)
		self.log_level = log_level
		self.label = label
		self.check_interval = check_interval
		self.check_scheme = check_scheme
		self.run_mode = run_mode
		self.server_list = server_list
		self.status_list = {}
		self.pid = -99
		self._serverUnpack()
		self.redirect_element = self._is_redirect_mode()

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

	def _is_redirect_mode(self):
		try:
			mode, protocol, host, port = self.run_mode.split(':')
			if (mode == 'redirect') and (protocol in ['tcp', 'udp']):
				return mode, protocol, host, port
			else:
				return False
		except:
			return False

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

	def suicide(self):
		## This "send-wait-poll" structure can prevent <defunct>.
		## It is known on 2023.02.28. As a historic moment, the day is worth to be memorized.
		if self.taskproc != None:
			'''
			On 2023.03.01, I noticed there is a bug / logic defection:
			 1. All nodes died
			 2. Config is modified and reloaded automatically
			 3. Destination does not re-launched, and all nodes keep death status
			 4. Config is modified and reloaded automatically again
			 5. Program crashes
			The reason is that self.taskproc was killed in 2, while it failed to be re-launched in 3.
			It means that before 4, type of self.taskproc was "NoneType".
			'''
			## Bug-20230306: signal 2 (=ctrl+c) has no effect in nohup mode!!
			# self.taskproc.send_signal(2)
			self.taskproc.kill()
			self.taskproc.wait()
			self.taskproc.poll()
			return 0
		else:
			self.log.print('[%s] Nothing to kill for a dead instance.' % self.label)
			return -1

	def _ps_switch(self):
			## When old process is running, kill it
			self.log.print('[%s] Kill the old process.' % self.label)
			self.suicide()
			## Run a new process
			self.taskproc = subprocess.Popen(self.server_list[self.nodeSelected]['exec'], shell=True)
			self.pid = self.taskproc.pid
			ajs.safelyEditJSON(PATH_PID, {self.label: self.pid})
			self.log.print('[%s] PID: %d' % (self.label, self.pid))

	def _red_rule_switch(self):
		_, protocol, host, port = self.redirect_element
		target = self.server_list[self.nodeSelected]['target']
		d, dport = target.split(':')
		rule_pre = f"-p {protocol} -d {host} --dport {port} -j DNAT --to-destination {target}"
		rule_post = f"-p {protocol} -d {d} --dport {dport} -j MASQUERADE"

		current_rule = ajs.gracefulLoadJSON(PATH_RED_RULE)
		if self.label in current_rule.keys():
			self.log.print('Remove old rules...')
			cmd_oldrule_pre = f"iptables -t nat -D PREROUTING {current_rule[self.label]['rule_pre']}"
			cmd_oldrule_post = f"iptables -t nat -D POSTROUTING {current_rule[self.label]['rule_post']}"
			self.log.print(f"[{self.label}] (-) {cmd_oldrule_pre}", 2)
			self.log.print(f"[{self.label}] (-) {cmd_oldrule_post}", 2)
			system(cmd_oldrule_pre)
			system(cmd_oldrule_post)
		
		cmd_rule_pre = f"iptables -t nat -A PREROUTING {rule_pre}"
		cmd_rule_post = f"iptables -t nat -A POSTROUTING {rule_post}"
		self.log.print(f"[{self.label}] (+) {cmd_rule_pre}", 2)
		self.log.print(f"[{self.label}] (+) {cmd_rule_post}", 2)
		system(cmd_rule_pre)
		system(cmd_rule_post)
		ajs.safelyEditJSON(PATH_RED_RULE, {self.label: {'rule_pre': rule_pre, 'rule_post': rule_post}})

	def exec(self):
		# if self.select_scheme == 'priority':
		## Until 2023.02.25, "priority" is the only scheme of GLOHA
		## And on 2024.01.27, this is completely deprecated

		self.log.print('[%s] Checking if node-0 available...' % self.label)
		la_0 = self.getLatency(self.server_list['0']['host'], self.check_scheme, timeout=self.server_list['0']['timeout']/1000.)
		
		## When node-0 failed, select an available one.
		if la_0 < 0:
			## Means that the node-0 died
			## >>--- Start node failover logic ---
			self.log.print('[%s] Node-0 seems not available. Check the next.' % self.label, 2)
			n_nodes = len(self.server_list.keys())
			
			if n_nodes > 1:
				## More than 1 nodes prepared
				## >>--- Node selection
				server_id = list(self.server_list.keys())
				server_id.sort()
				for i in server_id:
					if i == '0':
						continue
					la_n = self.getLatency(self.server_list[i]['host'], self.check_scheme, timeout=self.server_list[i]['timeout']/1000.)
					if la_n >= 0:
						## Means the node is available, and will be selected
						self.log.print('[%s] Select node-%s, with latency of %.2f ms.' % (self.label, i, la_n * 1000.))
						if self.nodeSelected != i:
							## Means that the previous node died, and this is a new one
							self.log.print('[%s] Switch to node-%s from node-%s.' % (self.label, i, self.nodeSelected), 2)
							self.isNodeSwitching = True
						else:
							self.log.print('[%s] Keep node-%s.' % (self.label, i))
						self.nodeSelected = i
						self.isNodeSelected = True
						break
					else:
						## Means this node is also died
						self.log.print('[%s] Node-%s is also failed. Next...' % (self.label, i))
				## <<--- End node selection

				## All nodes died
				if self.isNodeSelected == False:
					self.log.print('[%s] Seems no node is available... What about node-0 now?' % self.label)
					return -1
			## <<--- End node failover logic ---
		
		## When node-0 is working / can work normally
		else:
			self.log.print('[%s] Node-0 is available, with latency of %.2f ms.' % (self.label, la_0 * 1000.))
			self.isNodeSelected = True
			if self.nodeSelected != '0':
				self.log.print('[%s] Switch to node-0 from node-%s.' % (self.label, self.nodeSelected), 2)
				self.isNodeSwitching = True
			else:
				self.log.print('[%s] Keep node-0.' % self.label)
			self.nodeSelected = '0'

		## When node switching is needed (or GLOHA is the 1st time launched)
		if self.isNodeSwitching:
			self.log.print('[%s] Executing task of new node-%s...' % (self.label, self.nodeSelected))

			if self.redirect_element == False:
				self._ps_switch()
			else:
				self._red_rule_switch()
			self.isNodeSwitching = False
		else:
			self.log.print('[%s] Node is not switched.' % self.label)