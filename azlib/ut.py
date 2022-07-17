def sif(condition, value_true, value_false):
	if condition:
		return value_true
	else:
		return value_false

def gracefulRead(fname, method='r'):
	with open(fname, method) as o:
		buf = o.read()
	return buf

def gracefulWrite(fname, buff, method='w'):
	try:
		with open(fname, method) as o:
			o.write(buff)
		return 0
	except:
		return -1