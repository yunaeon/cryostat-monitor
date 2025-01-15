from serial import Serial
import sqlite3
from argparse import ArgumentParser
import time
p = ArgumentParser()
p.add_argument('port')
p.add_argument('--period',type=float,default=5)
p.add_argument('--dbpath',default='lakeshore.sqlite')
p.add_argument('--table',default='lakeshore')
args = p.parse_args()

def to_float(s):
	try:
		fl = float(s)
	except:
		fl = -1
	return fl

port = Serial(args.port,baudrate=9600,parity='O',bytesize=7,timeout=0.2)

conn = sqlite3.connect(args.dbpath)
conn.execute(f'create table if not exists {args.table}(gcutime REAL, temperature REAL);')
f = open(f'{args.table}_211.txt','a')

while 1:
	try:
		port.write(b'KRDG?\r\n')
		data = port.read(128)
		tnow = time.time()
		conn.execute(f'insert into {args.table}(gcutime,temperature) values ({tnow},{to_float(data)})')
		conn.execute('commit')

		timestring = time.strftime('%y/%m/%d-%H:%M:%S',time.localtime(tnow))
		s = f'{timestring} {tnow}  {data}   {to_float(data)}'
		print(s)
		f.write(s)
		f.write('\n')
		f.flush()
		time.sleep(args.period)
	except Exception as E:
		print('got exception: ',E)
