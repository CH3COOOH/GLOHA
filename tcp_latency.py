import socket
from time import time, sleep

def getLatency(host_port, timeout=4.):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.settimeout(timeout)
	t1 = time()
	host_, port = host_port.split(':')
	if sock.connect_ex((host_, int(port))) != 0:
		sock.close()
		return -1
	la = time() - t1
	sock.close()
	return la

def getAveLatency(host_port, n=5, timeout=4.):
	timeAcc = 0
	n_failed = 0
	n_success = 0
	for i in range(n):
		la = getLatency(host_port, timeout)
		# print(la)
		if la == -1:
			n_failed += 1
			if n_failed > n / 2:
				return -1
			sleep(.1)
		else:
			n_success += 1
			timeAcc += la
	return timeAcc / n_success

if __name__ == '__main__':
	print('1: %.2f ms' % (getAveLatency('app.henchat.net:443') * 1000))
	print('2: %.2f ms' % (getAveLatency('cn.henchat.net:22') * 1000))
