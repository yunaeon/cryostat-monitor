import zmq
from serial import Serial
import time

addr = 'ipc:///tmp/cryo'

def command(cmd, addr=addr):
  ctx = zmq.Context()
  req = ctx.socket(zmq.REQ)
  req.connect(addr)
  req.send(cmd)
  response = req.recv() #todo: timeout
  req.close()
  ctx.destroy()
  return response

def transact_serial(cmd,port):
  fd = Serial(port,baudrate=9600,timeout=0.5)
  fd.write(cmd)
  response = fd.read(4096)
  fd.close()
  return response

def rep_serial_server(port, addr=addr):
  ctx = zmq.Context()
  rep = ctx.socket(zmq.REP)
  rep.bind(addr)
  while 1:
    cmd = rep.recv()
    response = transact_serial(cmd,port)
    print(f'cmd: {cmd}   response: {response}')
    rep.send(response)

def parse_status(status):
  status = status.replace(b'\r\n',b' ')
  tokens = status.split()
  equals = False
  ret = []
  for token in tokens:
    if token == b'=':
      equals = True
    else:
      if equals:
        ret.append(token)
      equals = False
  return ret

def logger(addr=addr):
  from sqlite3 import connect
  con = connect('cryo.sqlite')
  con.execute('create table if not exists cryo(gcutime real, power_measured real, power_commanded real, target_temp real, reject_temp real, coldhead_temp real)')
  while 1:
    try:
      vals = parse_status(command(b'status\r'))
      vals = [float(val) for val in vals[1:]]
      con.execute('insert into cryo values (?,?,?,?,?,?)',[time.time()] + vals)
      con.commit()
    except Exception as e:
      print('exception: ',e)
    time.sleep(4.5)

if __name__ == '__main__':
  from argparse import ArgumentParser
  parser = ArgumentParser(description='run this script with only one flag set')
  parser.add_argument('--server',help='path/to/serial_port. setup a server that controls access to serial port.')
  parser.add_argument('--logger',help='no argument. start logging to sqlite file. --server instance must be running', action='store_true')
  parser.add_argument('--command',help='command to send to cryocooler controller, do not append carriage return. --server instance must be running')
  args = parser.parse_args()

  if args.server is not None:
    rep_serial_server(args.server)
  elif args.logger == True:
    logger()
  elif args.command is not None:
    response = command(args.command.encode('utf-8') + b'\r')
    print(f'response: {response}')
