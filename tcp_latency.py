import socket
from time import time

def getLatency(host, port, timeout=3.):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.settimeout(timeout)
	t1 = time()
	if sock.connect_ex((host, port)) != 0:
		sock.close()
		return -1
	la = time() - t1
	sock.close()
	return la

def getAveLatency(host, port, n=3, timeout=3.):
	timeAcc = 0
	for i in range(n):
		la = getLatency(host, port, timeout)
		if la == -1:
			return la
		timeAcc += la
	return timeAcc / n

if __name__ == '__main__':
	print(getAveLatency('app.henchat.ml', 443))
	print(getAveLatency('cn.henchat.ml', 22))
	print(getAveLatency('www.baidu.com', 443))
