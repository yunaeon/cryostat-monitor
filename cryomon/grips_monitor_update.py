import urllib2
from datetime import datetime
import time

def CheckCryoMonitor():

	NumSeconds = 60

	while(True):

		#read monitor webpage
		response = urllib2.urlopen('http://sprg.ssl.berkeley.edu/~brentm/last_update.dat')
		html = response.read()
		updatestr = html.split(' -- ')

		#parse time of last update
		#lastupdate = datetime.strptime(updatestr[0], '%B %d %Y %H:%M:%S')
		lastupdate = datetime(2015, 8, 28, 0, 0, 0)

		#time now
		timenow = datetime.now()
		
		#time since last update
		d = timenow - lastupdate
		dmin = d.days * 1440 + d.seconds / 60

		#send texts if longer than 2 mins
		if dmin > 2:
			#print "Cryo monitor has not been updated in last %i minutes. http://sprg.ssl.berkeley.edu/~brentm/last_update.dat" % (dmin)
			SendTexts("Cryo monitor has not been updated in last %i minutes" %dmin )
			#SendTexts("From this point on alerts are real. Cheers, Hazel")


		time.sleep(NumSeconds)


def SendTexts(TxString):
      
      import smtplib
      
      TextList = []
      
      with open('phone_numbers','r') as f:
            for line in f:
        	  z = line.split(',')
        	  if len(z) == 3:
        		TextList.append(z)
        	  else:
        	  	pass
        		#LogText("Bad formatting: "+line)
        	  
      try:
            #connect to SMTP
            #print "here"
            server = smtplib.SMTP("smtp.gmail.com",587)
            server.starttls()
            server.login('gripsssl@gmail.com','grip$557')
            
            for Person in TextList:
        	  try:
        		server.sendmail('GRIPS-monitor',Person[1]+'@'+Person[2],TxString)
        	  except:			
        		raise Exception("Problem sending text to "+Person[0])
        		
            
      except:
            
            raise Exception("Error connecting to gmail SMTP server")
      
      server.close()
      return True #successful
      

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    #parser.add_argument('-t', action='store_true', default=False, dest='transit', help='Use this mode when in transit')

    args = parser.parse_args()

    result = CheckCryoMonitor()

   

      