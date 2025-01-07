from cosi_monitor_defs import *
import time, sched
import re

NumSeconds = 60
NormalInterval = 60 #in minutes

UpdateInterval = NormalInterval
UpdateCounter = UpdateInterval
EmergencyInterval = 10
Emergency = False
EmergencyTemp = 90.0


CryotelGuess = '/dev/ttyUSB1'

while(True):

  try:
    Lakeshore = GrabLastLakeshoreTemp()
  except:
    Lakeshore = "CF-Err"
  
  try:
    Cryotel_T = GetCryoTemp(CryotelGuess)
  except:
    Cryotel_T = "CT-Err"

  try:
    Cryotel_P = GetCryoPower(CryotelGuess)
  except:
    Cryotel_P = "CT-Err"

  
  StatusString = Lakeshore+' '+Cryotel_T+' '+Cryotel_P
  LogText(StatusString)  

  try:
    RsyncText(StatusString)
  except:
    LogText("RsyncError")

  #parse LAkeshore string for detector temperature
  try:
    m = re.findall("\d+.\d+",Lakeshore)
    Temp1 = float(m[0])
    Temp2 = float(m[1])

  except:
    
    #problem parsing the lakeshore string, use an unrealistic value, say 500K
    Temp1 = 500.0
    Temp2 = 500.0
    Lakeshore = "CT "+"500.0 "+"500.0"
    StatusString = Lakeshore+' '+Cryotel_T+' '+Cryotel_P
    
  BoolEmergency = (Cryotel_T == "CT-Err") or (Temp1 > EmergencyTemp) or (Temp2 > EmergencyTemp)

  if BoolEmergency and (Emergency == False):
    #enter emergency mode
    Emergency = True
    SendTexts(StatusString)
    LogText("Emergency detected: "+StatusString)
    UpdateInterval = EmergencyInterval
    UpdateCounter = EmergencyInterval + 1

  if (not BoolEmergency) and (Emergency == True):
    #exit emergency mode, somehow things recovered
    Emergency = False
    SendTexts("Emergency probably resolved... stay tuned")
    SendTexts(StatusString)
    LogText("Emergency resolved: "+StatusString)
    UpdateInterval = NormalInterval
    UpdateCounter = NormalInterval + 1
    
  UpdateCounter = UpdateCounter - 1
  if UpdateCounter == 0:

    UpdateCounter = UpdateInterval #reset counter
    
    if Emergency == True:
      try:
        SendTexts(StatusString)            
      except:
        pass
  
  time.sleep(NumSeconds)


      
      
      
      
      













