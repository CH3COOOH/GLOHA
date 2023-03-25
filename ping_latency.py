import ping3
import time

def getLatency(host, timeout=4.):
	dt = ping3.ping(host, timeout=timeout)
	if dt in [None, False] or dt > timeout:
		return -1
	return dt

def getAveLatency(host, n=5, timeout=4.):
	timeAcc = 0
	n_failed = 0
	n_success = 0
	for i in range(n):
		la = getLatency(host, timeout)
		# print(la)
		if la == -1:
			n_failed += 1
			if n_failed > n / 2:
				return -1
			time.sleep(.1)
		else:
			n_success += 1
			timeAcc += la
	return timeAcc / n_success

if __name__ == '__main__':
	print('1: %.2f ms' % (getAveLatency('app.henchat.net') * 1000))
	print('2: %.2f ms' % (getAveLatency('cn.henchat.net') * 1000))
