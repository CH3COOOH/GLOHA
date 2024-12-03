import socket
from time import time

## 2024/1/25: Add quick mode

def getLatency(host_port, timeout=3.):
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

def getAveLatency(host_port, n=3, timeout=3., quick_mode=True):
	timeAcc = 0
	isStrong = True
	for i in range(n):
		la = getLatency(host_port, timeout)
		if la == -1:
			return la
		if quick_mode == True and isStrong == True:
			return la
		isStrong = False
		timeAcc += la
	return timeAcc / n

if __name__ == '__main__':
	print(getAveLatency('app.henchat.net:443'))
	print(getAveLatency('localhost:8008'))
