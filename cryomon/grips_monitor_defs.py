import datetime
########################################################################################################################

def GetLakeshoreTemp(Guess=''):

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
			port = serial.Serial( port=Port,baudrate=9600, bytesize=7, parity='O', stopbits=1, timeout=1.0)
	    except OSError as e:
			#not sure what would throw this
			raise e
	    except IOError:
			pass
			
	    except serial.SerialException:
			pass							
	    else:
			PortOpened = True
			#port.setTimeout(0.1) #100 ms timeout
			port.write('*idn?\r\n')		
			RecvString = port.read(100)
			if RecvString.find('LSCI') != -1:
#			      #get the cryocooler temperature
			      port.write('krdg?\r\n')
			      RecvString = port.read(100)
			      port.close()
			      if len(RecvString) > 0:

				    m = re.findall('\d+.\d+',RecvString)
				    if len(m) > 0:
					return "CF " + m[0] + "K"
					

				  
			      else:
				
				    raise serial.SerialException("Read zero bytes from serial port")
				
				    
			      
			else:				
			      port.close()
	    
      raise serial.SerialException("Couldn't find Lakeshore CF on any ttyUSB*")	
	    


			
      

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
			port = serial.Serial( port=Port,baudrate=4800, bytesize=8, parity='N', stopbits=1, timeout=1.0)
	    except OSError as e:
			#not sure what would throw this
			raise e
	    except IOError:
			pass
			
	    except serial.SerialException:
			pass							
	    else:
			PortOpened = True
			#port.setTimeout(0.1) #100 ms timeout
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
			port = serial.Serial( port=Port,baudrate=4800, bytesize=8, parity='N', stopbits=1, timeout=1.0)
	    except OSError as e:
			#not sure what would throw this
			raise e
	    except IOError:
			pass
			
	    except serial.SerialException:
			pass							
	    else:
			PortOpened = True
			#port.setTimeout(0.1) #100 ms timeout
			port.write('SERIAL\r')		
			RecvString = port.read(100)
			
			if RecvString.find('REV4.1') != -1:
			      
			      #get the cryocooler power
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


##########################################################################################################################

def SetCryoPower(Power, Guess=''):

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
			port = serial.Serial( port=Port,baudrate=4800, bytesize=8, parity='N', stopbits=1, timeout=1.0)
	    except OSError as e:
			#not sure what would throw this
			raise e
	    except IOError:
			pass
			
	    except serial.SerialException:
			pass							
	    else:
			PortOpened = True
			#port.setTimeout(0.1) #100 ms timeout
			port.write('SERIAL\r')		
			RecvString = port.read(100)
			
			if RecvString.find('REV4.1') != -1:
			      
			      #set the cryocooler power
			      port.write("SET MAX=" + Power +"\r")
			      RecvString = port.read(100)
			      port.close()
			      if len(RecvString) > 0:

				    m = re.findall('\d+.\d+',RecvString)
				    if len(m) > 0:
					return "P " + m[0] + "W"
					

				  
			      else:
				
				    raise serial.SerialException("Read zero bytes from serial port")
				
				    
			      #get the cryocooler power
			      port.write("P\r")
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


##########################################################################################################################

def GetCryoTempPwrFile(fdir):
      
	import subprocess as sp
	import re
	import datetime
    

	output = sp.check_output(['tail', fdir+'cryolog.dat'])  
	lines = output.split('\n')
	
	#readout = lines[0].replace(':', '')
	Temp = lines[0].split('--  ')[1].split('P')[0]
	Pwr = lines[0].split('--  ')[1].split('K ')[1]
	updateTimeStr = lines[0].split(' --')[0]
	updateTime = datetime.datetime.strptime(updateTimeStr, "%B %d %Y %H:%M:%S")
	nowTime = datetime.datetime.now()
	timeDelta = nowTime - updateTime
	if (timeDelta > datetime.timedelta (minutes=2)):
	  LogText("stale timestamp on Cryocooler monitor")
	  raise Exception("stale timestamp on Cryocooler monitor")


	return Temp, Pwr
	
  
##########################################################################################################################

# def GetLakeshoreTempFile(fdir, npts):
      
# 	import subprocess as sp
# 	import re
# 	import numpy as np
# 	import scipy.signal as sig
# 	import re
    

# 	output = sp.check_output(['tail', fdir+'monitorboard.dat'])  
# 	print output
# 	#lines = filter(None, output.split('\n')[-npts-2:-1])  #get the last 5 outputs (also remove any empyt strin)
# 	lines = output.split('\n')[-npts-2:-1]

# 	print lines
	
# 	LkshTemp1 = []
# 	LkshTemp2 = []
# 	for l in lines:
# 	     #print l
# 	     l = re.sub("^ *", "", l)	    
# 	     l = re.sub("  *", " ", l)
# 	     #print l
# 	     LkshTemp1.append(float(l.split(' ')[0]))
# 	     LkshTemp2.append(float(l.split(' ')[1]))
# 	LkshTemp1 = np.asarray(LkshTemp1)
# 	LkshTemp2 = np.asarray(LkshTemp2)

# 	LkshMedTemp1 = np.median(LkshTemp1)
# 	LkshMedTemp2 = np.median(LkshTemp2)

# 	LakeshoreTemp = "CF " + str(LkshMedTemp1) +' K ' + str(LkshMedTemp2)+ ' K'

# 	return LakeshoreTemp

def GetLakeshoreTempFile(fdir, npts):
      
	import subprocess as sp
	import re
	import datetime
    

	output = sp.check_output(['tail', fdir+'monitorboard-oneline.dat']) 
	lines = output.split('\n')
	
	#print lines[0].split(' ')

	#readout = lines[0].replace(':', '')
	lines[0] = re.sub("^ *", "", lines[0])
	lines[0] = re.sub(" +", " ", lines[0])
	CF = lines[0].split(' ')[0]
	CL = lines[0].split(' ')[5]
	BD = lines[0].split(' ')[4]
	AIR = lines[0].split(' ')[6]
	updateTimeStr =lines[0].split(' ')[10] + " " + lines[0].split(' ')[11] 
	updateTime = datetime.datetime.strptime(updateTimeStr, "%Y-%m-%d %H:%M:%S")
	nowTime = datetime.datetime.now()
	timeDelta = nowTime - updateTime
	if (timeDelta > datetime.timedelta (minutes=2)):
	  #print "here"
	  LogText("stale timestamp on Lakeshore monitor")
	  #print "here0"
	  raise Exception("stale timestamp on Lakeshore monitor")

	#LakeshoreTemp = "CF " + str(CF) +'K CL ' + str(CL)+ 'C'

	#return LakeshoreTemp
	return ("CF " + str(CF) + "K", " CL " + str(CL) + "C", " BD " + str(BD) + "C", " AIR " + str(AIR) + "C")
	
   
##########################################################################################################################

def GetAllFile(fdir):
      
	import subprocess as sp
	import re
    

	output = sp.check_output(['tail', fdir+'textlog_db.dat'])  
	lines = output.split('\n')
	LakeshoreTemp = "CF " + lines[0].split('CF ')[1].split(' K')[0] + ' K ' + lines[0].split('CF ')[1].split(' K')[1] + ' K'
	ColdtipTemp = "CT " + lines[0].split('CT ')[1].split('K')[0] + 'K'
	Pwr = "P " + lines[0].split('P ')[1].split('W')[0] + 'W'


	return LakeshoreTemp, ColdtipTemp, Pwr
	
  


#######################################################################################################################

def SendTexts(TxString):
      
      import smtplib
      from email.mime.text import MIMEText
      
      TextList = []
      
      with open('/home/grips/cryomon/phone_numbers','r') as f:
            for line in f:
        	  z = line.split(',')
        	  if len(z) == 3:
        		TextList.append(z)
        	  else:
        		LogText("Bad formatting: "+line)
        	  
      try:
            #connect to SMTP
            #print "here"
            server = smtplib.SMTP("smtp.gmail.com",587)
            server.starttls()
            server.login('brentm@berkeley.edu','PTO$uck5!')
            
            for Person in TextList:
        	  try:
        		msg = MIMEText(datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S -- ") + TxString)
        		msg['Subject'] = "GRIPS Alert"
        		msg['From'] = "brent.m@berkeley.edu"
        		msg['To'] = Person[1]+'@'+Person[2]
        		server.sendmail('GRIPS-monitor',Person[1]+'@'+Person[2],msg.as_string())
        	  except Exception as e:			
        		print str(e)
        		raise Exception("Problem sending text to "+Person[0])
        		
            
      except Exception as e:
            
            print str(e)
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
      
      #with open("/Users/hazelbain/Dropbox/grips_misc/cryomon/textlog.dat","a") as f:
      try:
        with open("/home/grips/cryomon/textlog.dat","a") as f:
          Timestamp = time.strftime("%B %d %Y %H:%M:%S -- ",time.localtime())
          f.write(Timestamp+String+'\n')
      except Exception as e:
        print "Can't write LogText:"
        print String

      


      
##########################################################################################################################

def GrabLastLakeshoreTemp():
      
      import subprocess as sp
      import re
      
      output = sp.check_output(['tail','/home/grips/GRIPS/cryomon/log.dat'])
      
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
		f = open("/home/grips/cryomon/last_update.dat","w")
		f.write(Timestamp+String+'\n')
		f.close()

		#sp.call(['scp','-P36867','/home/grips/cryomon/textlog.dat','brentm@apollo.ssl.berkeley.edu:/home/brentm/public_html'])
		#sp.call(['scp','-P36867','/home/grips/cryomon/last_update.dat','brentm@apollo.ssl.berkeley.edu:/home/brentm/public_html'])
                sp.call(['scp','/home/grips/cryomon/textlog.dat','mops@cosi-mops.ssl.berkeley.edu:/raid/logs/GRIPS'])
                sp.call(['scp','/home/grips/cryomon/last_update.dat','mops@cosi-mops.ssl.berkeley.edu:/raid/logs/GRIPS'])

	except Exception as e:
		#print "Rsync execption" + str(e)
		raise Exception("Problem with Rsync")

