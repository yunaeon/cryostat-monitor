
import smtplib
import os
import sys
from email.mime.text import MIMEText
import re
import datetime

class MonitorChecker:
  def __init__(self):
    #self.msg_to = "9254084246@vtext.com, 4155924332@vtext.com, 5103836840@tmomail.net"
    #self.sendmail_to = ["9254084246@vtext.com","4155924332@vtext.com","510383840@tmomail.net"]
    #self.msg_to = "9254084246@vtext.com"
    #self.sendmail_to = ["cosialert@outlook.com","5103836840@vtext.com","9254084246@vtext.com","9176930581@vtext.com","5102065319@txt.att.net"]
    #self.sendmail_to = ["9254084246@vtext.com","brentmochizuki@icloud.com","5107255591@vtext.com","5104074151@tmomail.net"]
    self.sendmail_to = ["9254084246@vtext.com","2016602798@tmomail.net","lazar.hadar@gmail.com","9165041847@txt.att.net","9149605210@vtext.com"]
    #self.sendmail_to = ["9254084246@vtext.com"]
    self.msg_to = ",".join(self.sendmail_to)
    self.path = os.path.expandvars("$PIPELINETOOLS") + "/grips_vitality/"
    self.errorFilename = self.path+"vitality.error"
    self.logFilename = self.path+"vitality.log"
    self.lastUpdateFilename = self.path+sys.argv[2]
    self.lastUpdateBackupFilename = self.path+sys.argv[2]+".old"
    self.updateFilename = self.path+"update.log"
    self.projectName = sys.argv[1]
    self.monitorLogURL = "http://cosi-mops.ssl.berkeley.edu/GRIPS/last_update.dat"
    self.secsBetweenTextMessages = 600
    self.secsBeforeAlarm = 310
    self.logFile = None
    self.lastUpdateFile = None
    self.errorFlagFile = None
    self.scriptFail = False

  def __del__(self):
    if self.logFile != None:
      self.logFile.close()
    if self.lastUpdateFile != None:
      self.lastUpdateFile.close()
    if self.errorFlagFile != None:
      self.errorFlagFile.close()

  def close(self):
    if not self.scriptFail:
      self.updateFileWrite()
    if self.logFile != None:
      self.logFile.close()
    if self.lastUpdateFile != None:
      self.lastUpdateFile.close()
    if self.errorFlagFile != None:
      self.errorFlagFile.close()
    exit(0)

  def getNowTimeString(self):
    return datetime.datetime.now().strftime("@%Y-%m-%d %H:%M:%S -- ")

  def logFileWrite(self, logString):
    self.logFile.write(self.getNowTimeString() + logString + "\n")

  def updateFileWrite(self):
    try:
      update_file = open (self.updateFilename, 'w')
      update_file.write(self.nowTime.strftime("%Y-%m-%d %H:%M:%S"))
      update_file.close()
    except:
      self.logFileWrite("Error: Couldn't write update file")

  def sendTextMessage(self, textString):
    self.logFileWrite(textString)
    textString = self.getNowTimeString() + textString

    msg = MIMEText(textString)
    msg['From'] = "brentm@berkeley.edu"
    msg['To'] = self.msg_to

    try:
      s = smtplib.SMTP_SSL("smtp.gmail.com", 465, 'localhost')
      s.login("brentm@berkeley.edu", "PTO$uck5!")
      s.sendmail("brentm@berkeley.edu", self.sendmail_to, msg.as_string())
      s.quit()
      self.logFileWrite("Sent text from bmail account")
      return
    except:
      self.logFileWrite("Can't send e-mail from bmail account, trying yahoo")

    try:
      msg['From'] = "brentmoch@yahoo.com"
      s = smtplib.SMTP("smtp.mail.yahoo.com", 587, 'localhost')
      s.starttls()
      s.login("brentmoch@yahoo.com", "Callyahoo!")
      s.sendmail("brentmoch@yahoo.com", self.sendmail_to, msg.as_string())
      s.quit()
      self.logFileWrite("Sent text from yahoo account")
      return
    except Exception as e:
      self.scriptFail = True
      self.logFileWrite("Can't send text message from any server: " + str(e))


  def getLastErrorTime(self):
    #get last error file update time
    try:
      self.errorFlagFile = open(self.errorFilename, 'r')
      try:
        errorTimeString = self.errorFlagFile.readline().rstrip()
        if errorTimeString == "":
          errorTime = None
        else:
          errorTimeString = re.sub(" -- .*","",errorTimeString)
          errorTime = datetime.datetime.strptime(errorTimeString, "@%Y-%m-%d %H:%M:%S")
      except ValueError:
        self.logFileWrite("Incorrectly formatted error time file")
        errorTime = None

      self.errorFlagFile.close()
      self.errorFlagFile = None
    except IOError:
      self.logFileWrite("Can't open error time file")
      errorTime = None
 
    return errorTime

  def error(self, errorString):
    errorTime = self.getLastErrorTime()
    if errorTime == None:
      errorTime = self.nowTime - datetime.timedelta(seconds = self.secsBetweenTextMessages + 1)
    #check if last error file update time was recent.  if not, send text, update error file
    if self.nowTime-errorTime > datetime.timedelta(seconds = self.secsBetweenTextMessages):
      self.sendTextMessage("Error: " + errorString)
      try:
        self.errorFlagFile = open(self.errorFilename, 'w')
        self.errorFlagFile.write(self.getNowTimeString() + "Error: Cannot access " + self.projectName + " Monitor update time")
      except IOError:
        self.logFileWrite("Can't open error time file for writing")
        
    else:
      self.logFileWrite("Error: " + errorString)
      self.logFileWrite("Note: not sending text message, as last one was sent " + str(self.nowTime-errorTime) + " ago")

  def openLastUpdateBackupFile(self):
    try:
      lastUpdateFile = open(self.lastUpdateBackupFilename, 'r')
    except IOError:
      self.error("Cannot access correctly formatted " + self.projectName + " Monitor update time at " + self.monitorLogURL)

      self.close()

    self.logFileWrite("Note: Found " + self.projectName + " Monitor log backup. Using that instead")
    self.lastUpdateFile = lastUpdateFile

    for line in self.lastUpdateFile:
      try:
        linearr = line.split("--")
        lastUpdateTime = datetime.datetime.strptime(linearr[0].rstrip(), "%B %d %Y %H:%M:%S")
      except ValueError:
        self.error("Monitor Log File incorrectly formatted. " + self.monitorLogURL)
        self.close()

      return lastUpdateTime

  def openLastUpdateFile(self):
    try:
      self.lastUpdateFile = open(self.lastUpdateFilename, 'r')
    except IOError:
      self.logFileWrite("Warning: Cannot access " + self.projectName + " Monitor last update time, looking for backup")
      self.lastUpdateFile = None
      return

    for line in self.lastUpdateFile:
      try:
        linearr = line.split("--")
        lastUpdateTime = datetime.datetime.strptime(linearr[0].rstrip(), "%B %d %Y %H:%M:%S")
      except ValueError:
        self.logFileWrite("Note: Monitor Log File incorrectly formatted.")
        self.lastUpdateFile.close()
        self.lastUpdateFile = None
        return

      return lastUpdateTime
    
  def getLastUpdateTime(self):
    lastUpdateTime = self.openLastUpdateFile()
    if self.lastUpdateFile == None:
      lastUpdateTime = self.openLastUpdateBackupFile()
    return lastUpdateTime

  def run(self):
    self.nowTime = datetime.datetime.now()
    self.logFile = open (self.logFilename, 'a')
    lastUpdateTime = self.getLastUpdateTime()

    timediff = self.nowTime-lastUpdateTime
    timediffSecs = int(timediff.total_seconds())
    if timediffSecs > self.secsBeforeAlarm:
      timediffMins = int(timediffSecs/60)
      timediffSecs -= 60*timediffMins 
      self.error(self.projectName + " Monitor last update " + str(timediffMins) + "min, " + str(timediffSecs) + "sec ago. " + self.monitorLogURL)
    else:
      timediffMins = int(timediffSecs/60)
      timediffSecs -= 60*timediffMins 
      errorTime = self.getLastErrorTime()
      if errorTime != None:
        self.sendTextMessage("Resolved: " + self.projectName + " Monitor last update " + str(timediffMins) + "min, " + str(timediffSecs) + "sec ago")
        try:
          self.errorFlagFile = open(self.errorFilename, 'w')
        except IOError:
          self.logFileWrite("Can't open error time file for writing")

      self.logFileWrite("Note: " + self.projectName + " Monitor last update " + str(timediffMins) + "min and " + str(timediffSecs) + "sec ago")
    self.close()

checker = MonitorChecker()
checker.run()
