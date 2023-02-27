import time

class Scheduler:
	def __init__(self):
		self.task_pool = []  ## [period, func, args]
		self.stop_signal = False
	
	def addTask(self, task):
		self.task_pool.append(task)

	def terminate(self):
		self.stop_signal = True
	
	def periodicExecute(self, atStart=False, acc=1.):
		if atStart:
			for t in self.task_pool:
				if t[2] == None:
					t[1]()
				else:
					t[1](t[2])

		t0 = time.time()
		task_pool_with_clock = self.task_pool
		for t in task_pool_with_clock:
			t.append(t0)
		## task_pool_with_clock: [period, func, args, clock]

		while True:
			if self.stop_signal:
				break
			for t in task_pool_with_clock:
				t_now = time.time()
				if t_now - t[3] >= t[0]:
					t[3] = t_now
					if t[2] == None:
						flag_turbo = t[1]()
					else:
						flag_turbo = t[1](t[2])
			time.sleep(acc)
			
if __name__ == '__main__':
	def func(n):
		print('func-%d, t=%d' % (n, time.time()))
		time.sleep(2)
		
	mt = multiTimer()
	ta = [10, func, 1]
	tb = [15, func, 2]
	tc= [25, func, 3]
	mt.addTask(ta)
	mt.addTask(tb)
	mt.addTask(tc)
	mt.periodicExecute(1.)