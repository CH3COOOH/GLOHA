import time

def log(text, level=0, write=False):
	level_map = ['INFO', 'WARN', 'ERROR']
	localtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) 
	msg = '[%s][%s] %s' % (localtime, level_map[level], text)
	print(msg)
	if write == True:
		with open('event.log', 'a') as o:
			o.write(msg + '\n')