from grips_monitor_defs import *
import time, sched
import re
import os
from time import localtime, strftime


def CryoMonitor(transit = False, highbay = False, gse = False, macbook = False):

  NumSeconds = 60
  NormalInterval = 60 #in minutes

  UpdateInterval = NormalInterval
  UpdateCounter = UpdateInterval
  EmergencyInterval = 10
  Emergency = False
  EmergencyTemp = 500.0
  EmergencyTempCT = 500.0
  EmergencyTempCol = 45.0
  CryoLowPower = "150" #This must be a STRING

  LakeshoreNpts = 20

  CryotelGuess = '/dev/ttyUSB0'
  LakeshoreGuess = '/dev/ttyUSB1'
  wdogFilename = "/dev/shm/monitor_is_alive"

  while(True):

    collar = ""
    
    if highbay:
      #In the highbay mode use Brents serial port monitoring

      try:
        Lakeshore = GetLakeshoreTemp(LakeshoreGuess)
      except:
        Lakeshore = "CF-Err"
      
      try:
        Cryotel_T = GetCryoTemp(CryotelGuess)
      except:
        Cryotel_T = "CT-Err"

      try:
        Cryotel_P = GetCryoPower(CryotelGuess)
      except:
        Cryotel_P = "CP-Err"

    elif transit:
      #In the transit mode use Brents serial port monitoring for CryoTemp and CryoPower
      #and use Alberts script to query Lakeshore
      
      try:
        Cryotel_T = GetCryoTemp(CryotelGuess)
      except Exception as e:
        LogText("Exception in temp serial:" + str(e))
        Cryotel_T = "CT-Err"
      try:
        Cryotel_P = GetCryoPower(CryotelGuess)
      except Exception as e:
        LogText("Exception in power serial:" + str(e))
        Cryotel_P = "CP-Err"

      fdir = '/home/grips/cryotherm/'
      try:
        (Lakeshore, collar, body, air) = GetLakeshoreTempFile(fdir, LakeshoreNpts)
      except Exception as e:
        print "Exception %s" % str(e)
        (Lakeshore, collar, body, air) = ("CF-Err"," CL-Err", "BD-Err", "AIR-Err")

    elif gse:
      ##read log files saved from the GSE
      #print 'MODE: GSE'

      fdir = '/home/grips/gse/trunk/'
      #fdir = '/home/grips/GRIPS/gse/trunk/'
      #fdir = '/Users/hazelbain/Dropbox/grips/gsesvn/trunk/'
      try:
        Cryotel_T , Cryotel_P = GetCryoTempPwrFile(fdir)
      except Exception as e:
        Cryotel_T = "CT-Err"
        Cryotel_P = "CP-Err"

      #fdir = '/home/grips/GRIPS/monitor_code/'
      #fdir = '/Users/hazelbain/Dropbox/grips/gsesvn/trunk/'
      fdir = '/home/grips/cryotherm/'
      try:
        (Lakeshore, collar, body, air) = GetLakeshoreTempFile(fdir, LakeshoreNpts)
      except Exception as e:
        (Lakeshore, collar, body, air) = ("CF-Err"," CL-Err", "BD-Err", "AIR-Err")

    elif macbook:

      fdir = '/Users/hazelbain/Dropbox/grips_misc/monitor_code/'

      try:
        Lakeshore, Cryotel_T , Cryotel_P = GetAllFile(fdir)
      except:
        Cryotel_T = "CT-Err"
        Cryotel_P = "CP-Err"
        Lakeshore = "CF-Err"

    StatusString = Lakeshore+' '+Cryotel_T+' '+Cryotel_P+collar+body+air
    print strftime("%Y-%m-%d %H:%M:%S", localtime() ) + ' ' +StatusString
    LogText(StatusString)  
    try:
      RsyncText(StatusString)
    except:
      LogText("RsyncError")

    #parse LAkeshore string for detector temperature
    try:
      m = re.findall("\d+.\d+",Lakeshore)
      Temp1 = float(m[0])
      #Temp2 = float(m[1])

      #print Temp1, Temp2
    
    except:
      
      #problem parsing the lakeshore string, use an unrealistic value, say 500K
      Temp1 = 500.0
      #Temp2 = 500.0
      Lakeshore = "CF 500.0K"
      
    #parse collar string for detector temperature
    try:
      m = re.findall("\d+.\d+",collar)
      Temp2 = float(m[0])
      
      #print Temp1, Temp2
    
    except:
      
      #problem parsing the collar string, use an unrealistic value, say 500K
      collar = "CL 500.0C"
      Temp2 = 500.0
      
    #parse Cryotel_T for cold tip temp
    try:
      #m = re.findall("\d+.",Cryotel_T)
      m = Cryotel_T.strip("CT ").strip("K")
      TempCT = float(m)
    
    except:
      #problem parsing the cold tip string, use an unrealistic value, say 500K
      TempCT = 500.0
      TempCTstr = "CT 500.0K"
            
    StatusString = Lakeshore+' '+Cryotel_T+' '+Cryotel_P+collar    
    BoolEmergency = (Cryotel_T == "CT-Err") or (TempCT > EmergencyTempCT) or (Temp1 > EmergencyTemp) or (Temp2 > EmergencyTempCol)
    
    # IF the collar temp exceeds a certain value, set the cryo power lower
    if Temp2 > EmergencyTempCol and Temp2 < 500:
      try:
        Cryotel_P = SetCryoPower(CryoLowPower)
        if Cryotel_P != "P " + CryoLowPower + "W":
          LogText("Cryo power set incorrectly.  Tried %s, read back %s" % (CryoLowPower, Cryotel_P))
          SendTexts("Cryo power set incorrectly.  Tried %s, read back %s" % (CryoLowPower, Cryotel_P))
        else:
          LogText("Cryo power lowered to %s" % (CryoLowPower))
          SendTexts("Cryo power lowered to %s" % (CryoLowPower))
      except Exception as e:
        LogText("Exception in power serial:" + str(e))
        Cryotel_P = "CP-Err"
     
    
    if BoolEmergency: #and (Emergency == False):
      #enter emergency mode
      Emergency = True
      SendTexts(StatusString)
      #for i in range(3):
      #    os.system('espeak -v en "Wake up. Wake up. Wake up. Cryo-cooler warning. Nicole, get your sorry ass out of bed"')
      #    #os.system('say "Wake up. Wake up. Wake up. Cryo-cooler warning. Nicole, get your sorry ass out of bed"')
      #    i=i+1
      LogText("Emergency detected: "+StatusString)
      UpdateInterval = EmergencyInterval
      UpdateCounter = EmergencyInterval + 1

    if (not BoolEmergency) and (Emergency == True):
      #exit emergency mode, somehow things recovered
      print 'Emergency resolved'
      Emergency = False
      SendTexts("Emergency probably resolved... stay tuned")
      SendTexts(StatusString)
      #for i in range(3):
      #  os.system('espeak -v en "Cryo-cooler emergency resolved. Go back to sleep."')
      #  #os.system('say "Cryo-cooler emergency resolved. Go back to sleep."')
      #  i=i+1
      #LogText("Emergency resolved: "+StatusString)
      UpdateInterval = NormalInterval
      UpdateCounter = NormalInterval + 1
      
    UpdateCounter = UpdateCounter - 1
    if UpdateCounter == 0:

      UpdateCounter = UpdateInterval #reset counter
      
      #if Emergency == True:
      #  try:
          #SendTexts(StatusString)            
      #  except:
      #    pass
    #tickle watchdog
    if not os.path.exists(wdogFilename):
      open(wdogFilename, 'a').close()
    os.utime(wdogFilename, None)
    time.sleep(NumSeconds)


  return None


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', action='store_true', default=False, dest='transit', help='Use this mode when in transit')
    parser.add_argument('-hb', action='store_true', default=False, dest='highbay', help='Use this mode when in the highbay')
    parser.add_argument('-g', action='store_true', default=False, dest='gse', help='Use this mode when in the highbay')
    parser.add_argument('-m', action='store_true', default=False, dest='macbook', help='Use this mode when using the macbook')



    args = parser.parse_args()

    result = CryoMonitor(transit = args.transit, highbay = args.highbay, gse = args.gse, macbook = args.macbook)

   








