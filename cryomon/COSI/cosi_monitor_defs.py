
########################################################################################################################

def GetCryoTemp(Guess=''):

#returns the temperature or raises an exception

      import serial
      import glob
      import re

      if Guess == '':
      	PortList = glob.glob("/dev/ttyUSB*")
      else:
	PortList = glob.glob("/dev/ttyUSB*")
	PortList.insert(0,Guess)

	

      for Port in PortList:			
	    
	    try:
			port = serial.Serial( port=Port,baudrate=4800, bytesize=8, parity='N', stopbits=1)
	    except OSError as e:
			#not sure what would throw this
			raise e
	    except IOError:
			pass
			
	    except serial.SerialException:
			pass							
	    else:
			PortOpened = True
			port.setTimeout(0.1) #100 ms timeout
			port.write('SERIAL\r')		
			RecvString = port.read(100)
			if RecvString.find('REV4.1') != -1:
			      
			      #get the cryocooler temperature
			      port.write('TC\r')
			      RecvString = port.read(100)
			      port.close()
			      if len(RecvString) > 0:

				    m = re.findall('\d+.\d+',RecvString)
				    if len(m) > 0:
					return "CT " + m[0] + "K"
					

				  
			      else:
				
				    raise serial.SerialException("Read zero bytes from serial port")
				
				    
			      
			else:				
			      port.close()
	    
      raise serial.SerialException("Couldn't find Cryotel CT on any ttyUSB*")	
	    


			
      
      
	    
#######################################################################################################################

def GetCryoPower(Guess=''):

#returns the temperature or raises an exception

      import serial
      import glob
      import re

      if Guess == '':
      	PortList = glob.glob("/dev/ttyUSB*")
      else:
	PortList = glob.glob("/dev/ttyUSB*")
	PortList.insert(0,Guess)

	

      for Port in PortList:			
	    
	    try:
			port = serial.Serial( port=Port,baudrate=4800, bytesize=8, parity='N', stopbits=1)
	    except OSError as e:
			#not sure what would throw this
			raise e
	    except IOError:
			pass
			
	    except serial.SerialException:
			pass							
	    else:
			PortOpened = True
			port.setTimeout(0.1) #100 ms timeout
			port.write('SERIAL\r')		
			RecvString = port.read(100)
			
			if RecvString.find('REV4.1') != -1:
			      
			      #get the cryocooler temperature
			      port.write('P\r')
			      RecvString = port.read(100)
			      port.close()
			      if len(RecvString) > 0:

				    m = re.findall('\d+.\d+',RecvString)
				    if len(m) > 0:
					return "P " + m[0] + "W"
					

				  
			      else:
				
				    raise serial.SerialException("Read zero bytes from serial port")
				
				    
			      
			else:				
			      port.close()
	    
      raise serial.SerialException("Couldn't find Cryotel CT on any ttyUSB*")

#######################################################################################################################

def SendTexts(TxString):
      
      import smtplib
      
      TextList = []
      
      with open('phone_numbers','r') as f:
	    for line in f:
		  z = line.split(',')
		  if len(z) == 3:
			TextList.append(z)
		  else:
			print "Bad formatting: "+line
		  
      try:
	    #connect to SMTP
	    server = smtplib.SMTP("smtp.gmail.com",587)
	    server.starttls()
	    server.login('cosi.monitor@gmail.com','nuclearcomptontelescope')
	    
	    for Person in TextList:
		  try:
			server.sendmail('COSI-monitor',Person[1]+'@'+Person[2],TxString)
		  except:			
			raise Exception("Problem sending text to "+Person[0])
			
	    
      except:
	    
	    raise Exception("Error connecting to gmail SMTP server")
      
      server.close()
      return True #successful
      
      
#######################################################################################################################


#def ManageConnection()

#pings outside world via USB, 


#######################################################################################################################

def Ping(URL):
      
      import subprocess as sp
      import re
	        
      try:       
	    output = sp.check_output(['ping','-c','3','-W','1',URL])
      except sp.CalledProcessError as e:
	    #rather than raise an error, probably just want to return false 
	    #raise Exception("call to check_output returned: " + str(e.returncode))
	    #might want to parse the output for more information?
	    return False
      
      except:
	    
	    return False
      
      else:
	    m = re.findall(',.*?\d+ received,',output)
	    if len(m) == 1:
		  n = re.findall('\d+',m[0])
		  for i in n:
			try:
			      z = int(i)
			except ValueError as e:
			      pass
			else:
			      if z > 0:
				    return True
			      elif z == 0:
				    return False

	    else:
		  return False
      
      
	    
      


#########################################################################################################################      

      
def LogText(String):
      
      import time            
      
      with open("/home/cosi/cosi-monitor/textlog.dat","a") as f:
	    
	    Timestamp = time.strftime("%B %d %Y %H:%M:%S -- ",time.localtime())
	    f.write(Timestamp+String+'\n')
	    
##########################################################################################################################

def GrabLastLakeshoreTemp():
      
      import subprocess as sp
      import re
      
      output = sp.check_output(['tail','/home/cosi/cosi-monitor/log.dat'])
      
      lines = output.split('\n')
      
      numlines = len(lines)
      
      for i in reversed(lines):
	#m = re.findall('\d:\+\d+\.\d+K',i)
	m = re.findall('\d+\.\d+K',i)
	if len(m) == 2:
		return 'CF '+m[0]+' '+m[1]
	
      raise ValueError("Couldn't find a string with two temperatures in it.")


##########################################################################################################################

def RsyncText(String):

	import time
	import subprocess as sp

	try:
		
		Timestamp = time.strftime("%B %d %Y %H:%M:%S -- ",time.localtime())
		f = open("/home/cosi/cosi-monitor/last_update.dat","w")
		f.write(Timestamp+String+'\n')
		f.close()

		sp.call(['rsync','/home/cosi/cosi-monitor/textlog.dat','alowell@apollo:/home/alowell/public_html'])
		sp.call(['rsync','/home/cosi/cosi-monitor/last_update.dat','alowell@apollo:/home/alowell/public_html'])

	except:
		raise Exception("Problem with Rsync")

      
	
      
      
      
      
      
      


	    
	    
	    
      
      

