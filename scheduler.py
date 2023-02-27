import time

class multiTimer:
	def __init__(self):
		self.task_pool = []  ## [period, func, args]
	
	def addTask(self, task):
		self.task_pool.append(task)
	
	def periodicExecute(self, acc=1.):
		t0 = time.time()
		task_pool_with_clock = self.task_pool
		for t in task_pool_with_clock:
			t.append(t0)
		print(task_pool_with_clock)
		## task_pool_with_clock: [period, func, args, clock]
		while True:
			time.sleep(acc)
			for t in task_pool_with_clock:
				t_now = time.time()
				if t_now - t[3] >= t[0]:
					t[3] = t_now
					t[1](t[2])
			
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