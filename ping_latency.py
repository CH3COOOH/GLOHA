import ping3
from time import time

def getLatency(host, timeout=3.):
	dt = ping3.ping(host)
	if dt == None or dt == False or dt > timeout:
		return -1
	return dt

def getAveLatency(host, n=3, timeout=3.):
	timeAcc = 0
	for i in range(n):
		la = getLatency(host, timeout)
		if la == -1:
			return la
		timeAcc += la
	return timeAcc / n

if __name__ == '__main__':
	print(getAveLatency('app.henchat.net'))
	print(getAveLatency('cn.henchat.net'))
