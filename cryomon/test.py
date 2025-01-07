from grips_monitor_defs import *
import time, sched
import re

NumSeconds = 60

#SendTexts("Sending grips texts")
#while(True):
#	StatusString = "status"
#	try:
#		RsyncText(StatusString)
#	except:
#		LogText("RsyncError")
#	time.sleep(NumSeconds)
#RsyncText("test rsync")
#GrabLastLakeshoreTemp()
#LogText("test log text")
#GetCryoPower()
#GetCryoTemp()

#print GetCryoPower()
#print GetCryoTemp()
print GetLakeshoreTemp()
