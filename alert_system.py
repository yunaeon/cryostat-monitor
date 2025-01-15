# this is used for monitoring telemetry and instrument health
# relies on emergency_contact_list not packaged with bfsw, but should be installed in /home/gaps/config/alerts
# systemd runs script in /home/gaps/config/alerts/berkeley_server_alerts.py (on berkeley server) or
# /home/gaps/config/alerts/campaign_server_alerts.py (on campaign server)
# which are set up following the example in if name == main, but with the correct directory

# python alert_system.py -b -p "/Users/scott/Documents/GRIPS/ged-sttc/lakeshore.sqlite" --project grips2 -v

import time, smtplib,os
from datetime import datetime, timezone
from email.mime.text import MIMEText
from paramiko import SSHClient, AutoAddPolicy
#from pybfsw.gse.gsequery import GSEQuery
from pathlib import Path
from slack_sdk import WebClient
#from pybfsw.payloads.gaps.mppt_alarms import mppt_alarms_list
from scp import SCPClient
import json
import pathlib

emergency_list_path = Path("/Users/sophiaw/alerts/emergency_message_list")
if not emergency_list_path.exists():
    print("Warning: emergency_message_list file not found.")


cat_map = {'battery':3914,'v':3914,'network':3962,'power':3962,'d':3960,'o':4104,'trigger':4005}

class alert_system():
    def __init__(self, project="gaps", verbose=False, path=None, telemetry_dt=60, alert_dt=20*60,
                 remote_ip= None, remote_user= None, remote_pw= None, remote_port=None,
                 alerts_dir="alerts", server_name = "default_server", test_connections = False):
        self.verbose = verbose
        self.telemetry_dt = telemetry_dt
        self.alert_dt = alert_dt
        self.remote_user = remote_user
        self.remote_pw = remote_pw
        self.remote_port = remote_port
        self.remote_ip = remote_ip
        self.server_name=server_name

        # directory for I'm alive
        if isinstance(alerts_dir, Path):
            self.alerts_dir = alerts_dir
        else:
            self.alerts_dir = pathlib.Path(__file__).parents[1] / "alerts" # only must run on same user on both servers; otherwise, change this line to hardcode directory
        self.emergency_list =  self.alerts_dir / "emergency_message_list"

        # GSEQuery instance
        # self.q = GSEQuery(project=project,path=path)

        # tracking success and errors
        self.telemetry = time.time() # time of most recent known good telemetry, or time program started
        self.campaign_network = time.time() # time of most recent known good campaign network, or time program started
        self.telemetry_alert = False # time of most recent telemetry alert, or none if not currently on alert
        self.campaign_network_alert = False # time of most recent campaign network alert, or none if not currently on alert
        self.inst_hkp_alert = {} # time of most recent alert for each hkp group
        self.inst_hkp = {} # time of most recent good known telemetry, or time program started
        self.remote_alive = time.time() # time of most recent remote alive, or time program started
        self.remote_alive_alert = False

        self.gse6_alert = False
        self.gse6_time = time.time()

        self.sunpower_alert = False
        self.sunpower_time = time.time()

        self.email_success = True
        self.emergency_list_updated = 0 # time of most recent alerts list update, or 0 if never updated
        self.gse_status_sent = time.gmtime(time.time()).tm_yday # displays day of the year gse email most recently sent

        for category in ['battery','v','trigger']:
            self.inst_hkp_alert[category] = False
            self.inst_hkp[category] = time.time()

        if test_connections:
            # send test email to alert to server restart
            if not self.SendPage(f"Restarting {self.server_name} Server Alert System",category='d'):
                print ("Test Pages Failed! See debug log!")
            if not self.SendEmails(f"Restarting {self.server_name} Server Alert System",category='d'):
                print ("Test emails failed! See debug log!")
            elif self.verbose: print ("successfully sent test emails upon startup")

            # test ssh connection to remote server
            if not self.TrySsh():
                print ("Ssh connection is not working; check code")
                self.SendPage(f"{self.server_name} ssh connection to {self.remote_ip}:{self.remote_port} is not working!", category='d')
            elif self.verbose: print (f'successfully tested ssh connection to {self.remote_ip}')

    def SendPage(self,TxString,send=True,category=None,subject="Cryostat Alert",continuing = False):

        message = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S ") + self.server_name + " Server\n"+TxString

        # send slack message
        try:
            if not continuing:
                slack_client = WebClient(token=os.environ.get("GSE_SLACK_TOKEN"))
                if slack_client:
                    slack_client.chat_postMessage(channel="gse-automatic-monitoring", text=message, username="GSE alerts")
        except Exception as e:
            self.LogText(f"Slack not working: {e}")

        try:
            #sn = os.environ.get("GSE_PAGEM_TOKEN")
            c = cat_map.get(category, 0)
            server = smtplib.SMTP("smtp.gmail.com", 587) #changed from 465 -> 587
            server.starttls()
            server.login('sophii.wang@gmail.com', "yqbaucoiblaimzjq")
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = 'monitor@cryostat.com'
            msg['To'] = self.msg_to
            server.sendmail('sophii.wang@gmail.com', self.recipients, msg.as_string())
            server.quit()
        except Exception as e:
            self.LogText(f"Email not working: {e}")

    def SendEmails(self,TxString,send=True,category=None,subject= 'Cryostat Alert', continuing = False):

        message = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S ") + self.server_name + " Server\n"+TxString

        # send texts and emails
        TextList = []
        with self.emergency_list.open("r") as f:
            content = f.read()
            for line in content.splitlines():
                if line.startswith("#"): continue
                z = line.split(",")
                if len(z) == 4:
                    if category == None:
                        TextList.append(z)
                    elif category in z[3]: TextList.append(z)
                else:
                    self.LogText("Bad formatting: " + line)
        if self.verbose and category == 'd': print (TextList)

        if len(TextList) == 0:
            self.LogText(f"no category {category} emails to alert"+ TxString + "\n")
            self.SendPage(f"No category {category} emails to alert!",category='d')
            return False

        try:
            server = smtplib.SMTP("smtp.gmail.com",587)
            server.starttls()
            server.login('sophii.wang@gmail.com',"yqbaucoiblaimzjq")

            for Person in TextList:
                try:
                    msg = MIMEText(message)
                    msg['Subject'] = subject
                    msg['From'] = "monitor@cryostat.com"
                    msg['To'] = Person[1] + "@" + Person[2]
                    if send: server.sendmail('GRIPS-monitor',Person[1]+'@'+Person[2],msg.as_string())

                except Exception as e:
                    print (e)
                    raise Exception("Could not send email to ",Person[0])

        except Exception as e:
            print (e)
            raise Exception("Error connecting to gmail SMTP server")

        server.close()
        return True

    def MakeSshClient(self,ip=None,user=None,port = None):

        ssh_list = []
        if not self.remote_pw:
            keys_dir = Path.home() / ".ssh"
            ssh_list = keys_dir.glob('id_*')
            ssh_list = [str(f) for f in ssh_list if f.is_file and not ".pub" in str(f)]

        if ip == None: ip = self.remote_ip
        if user == None: user = self.remote_user
        if port == None: port = self.remote_port

        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())

        if self.remote_pw:
            try:
                client.connect(ip,username=user,port=port,password=self.remote_pw)
                return client
            except:
                self.LogText(f"Cannot ssh into {ip} with port {port} and user {user} and remote pw")
                return False
        else:
            try:
                client.connect(ip,username=user,port=port,look_for_keys=True,key_filename=ssh_list)
                return client
            except:
                self.LogText(f"Cannot SSH into {ip} with port {port} and user {user} and ssh keys")
                return False

    def TrySsh(self,ip=None,user=None,port = None,cmd_str=False):

        output  = False
        client = self.MakeSshClient(ip=ip,user=user,port=port)

        if not client:
            return False
        if cmd_str:
            std_in,std_out,std_err = client.exec_command(cmd_str)
            output = std_out.read().decode('ascii').strip('\n')
            client.close()
            if not output: return True
            return output
        client.close()
        return True

    def copy_contact_list_remote(self,ip=None,user=None,port=None):

        # check if we need to update...
        time_m = os.path.getmtime(str(self.emergency_list))
        if time_m < self.emergency_list_updated:
            return True

        if self.verbose: print (f"Contact list updated on {self.server_name}; copying to remote")
        client = self.MakeSshClient(ip = ip, user=user,port=port)
        if not client:
            self.LogText("Could not establish ssh connection to remote to copy emergency contact list")
            return False

        with SCPClient(client.get_transport()) as scp:
            scp.put(str(self.emergency_list),str(self.emergency_list)) # fails if --remote_user is not the same as local user
            self.emergency_list_updated = time.time()

        client.close()
        return True

    def LogText(self,String):
        p = self.alerts_dir / "alerts_log"
        try:
            with p.open("a") as f:
                Timestamp = time.strftime("%B %d %Y %H:%M:%S -- ",time.localtime())
                f.write(Timestamp+String+'\n')
                if self.verbose: print (Timestamp + String + "\n")
        except Exception as e:
            print ("Can't write LogText:")
            print (String)

    def CheckTelemetryTime(self):
        latest_time = 0
        tables = self.q.get_table_names()
        for table in tables:
            _, res = self.q.get_latest_rows(table)
            if not res == None:
                latest_time = max(latest_time, res[0][1])
        return latest_time

    def IAmAlive(self):
        p = self.alerts_dir / "im_alive"
        with p.open("w") as f:
            f.write(str(time.time()))

    def CheckInstrumentHealth(self,parameter_list,alarm_ranges = {},dt=None):

        if dt == None: dt = self.telemetry_dt

        no_data = {}
        old_data = {}
        bad_value = {}

        pg = self.q.make_parameter_groups(parameter_list)
        res = self.q.get_median_value_groups(pg)
        for r in res.items():
            key = r[0]
            print (key)
            if r[1] == None:
                s = self.AlarmStringNoData(key)
                no_data[key] = s
                self.LogText(s)
                if self.verbose: print (key, " no data")

            else:
                val = r[1][1]
                gcu_time = r[1][0]
                ranges = [(r[1][2].low_alarm,r[1][2].high_alarm)]
                if key in alarm_ranges: ranges = alarm_ranges[key]
                if self.verbose: print (key,val, ranges)

                if time.time() - gcu_time > dt:
                    s = self.AlarmStringOldData(key,time.time() - gcu_time)
                    old_data[key] = s
                    self.LogText(s)

                goodValue = False
                for r in ranges:
                    if (r[0] is None or val >= r[0]) and (r[1] is None or val <= r[1]):
                        goodValue = True
                if not goodValue:
                    s = self.AlarmStringBadData(key,val,ranges)
                    self.LogText(s)
                    bad_value[key] = s
                    self.LogText(s)
        return bad_value | old_data | no_data

    def AlarmStringNoData(self,key):
        return f"No data for {key} in gsedb! Instrument health monitoring is compromised!"

    def AlarmStringOldData(self,key,time):
        time = round(time)
        return f"{key} data is {time} s out of date and instrument monitoring is not valid!"

    def AlarmStringBadData(self,key,val,ranges):
        val = round(val,3)
        rangestrs = [f'({v[0]},{v[1]})' for v in ranges]
        s = ', '.join(rangestrs)
        return f"{key} = {val}; good range is {s}"


    # check telemetry (if not getting data from campaign server, we get alerts about power outage on campaign site)
    def check_telemetry_campaign_network(self,dt = None, f = None):

        if dt == None: dt = self.telemetry_dt
        if f == None: f = self.alert_dt
        category = 'power'

        current_time = time.time()
        latest_db_time = self.CheckTelemetryTime()

        # if telemetry looks good, then the gsedb is good and also that means network and power are ok on campaign
        if current_time - latest_db_time < dt:

            # if telemetry and/or power/network was previously bad, then send an update that we're good now
            if self.campaign_network_alert:
                self.email_success = self.SendPage(f"Power or network is restored for GAPS Campaign site, and Telemetry is restored. Power outage time: {current_time - self.campaign_network} s",category=category) and self.email_success
            elif self.telemetry_alert:
                category='network'
                self.email_success = self.SendPage(f"Telemetry is restored. Telemetry outage time: {current_time - self.telemetry} s",category=category) and self.email_success

            # update latest time they are known to be good
            self.telemetry = current_time
            self.campaign_network = current_time
            self.campaign_network_alert = False
            self.telemetry_alert = False

            if self.verbose: print (current_time,"telemetry all good!")
            return True

        # if network is ok, then we just have a gsedb problem
        if self.TrySsh():

            # update that network is ok now
            if self.campaign_network_alert:
                self.email_success = self.SendPage(f"Power or network is restored on GAPS Campaign site. Outage time: {current_time - self.campaign_network} s",category=category) and self.email_success
            self.campaign_network = current_time
            self.campaign_network_alert = False

            # deal with the gsedb problem
            category = 'network'
            if not self.telemetry_alert: # if this is a new alert
                self.email_success = self.SendPage("Berkeley GSE not receiving Telemetry! Cannot monitor instrument safety.",category=category) and self.email_success
                self.telemetry_alert = current_time
            elif current_time - self.telemetry_alert > f: # if the email frequency time has elapsed...
                self.email_success = self.SendPage(f"Berkeley GSE telemetry outage ongoing.",category=category,continuing=True) and self.email_success
                self.telemetry_alert = current_time
            else:
                pass
            if self.verbose: print ("gsedb problem detected!")
            return False

        # the network is not ok
        if not self.campaign_network_alert:
            self.email_success = self.SendPage("Campaign network or power outage detected!",category=category) and self.email_success
            self.campaign_network_alert = current_time
        elif current_time - self.campaign_network_alert > f:
            self.email_success = self.SendPage(f'Campaign network or power outage is ongoing.',category=category, continuing=True) and self.email_success
            self.telemetry_alert = current_time
        else:
            pass
        if self.verbose: print ("network outage on campaign gse network")
        return False

    def test_gse6(self,dt=None,f=None):
        success = self.TrySsh(ip='192.168.36.6',user='gaps') # ,ip=None,user=None,port = None,cmd_str=False
        if dt == None: dt = self.telemetry_dt
        if f == None: f = self.alert_dt
        category = 'c'
        current_time = time.time()

        if success:
            self.gse6_time = current_time
            self.gse6_alert = False
            print ('gse6 is online!')
            return

        if current_time - self.gse6_time > dt and not self.gse6_alert:
            self.email_success = self.SendPage(f'temporary outage on gaps campaign site! GSE6 is offline. Outage time: {current_time - self.gse6_time} s',category=category) and self.email_success
            self.gse6_alert = current_time
            print ('gse6 is offline')
            return
        if current_time - self.gse6_time > dt and current_time -  self.gse6_alert > f:
            self.email_success = self.SendPage(f'ongoing outage on gaps campaign site! GSE6 is offline. Outage time: {current_time - self.gse6_time} s',category=category) and self.email_success
            self.gse6_alert = current_time
            print ('gse6 continues to be offline')



    def check_serial(self, port='/dev/ttyUSB0', baudrate=4800, bytesize=7, parity='O', stopbits=1, timeout=1.0, check_string='TC'):
        import serial
        try:
            serial_port = serial.serial(port=port, baudrate=baudrate, bytesize=bytesize, parity=parity, stopbits=stopbits, timeout=timeout)
        except IOError as e:
            raise e
        else:
            serial_port.write(check_string)
            recieved_string = serial_port.read(100)
            serial_port.close()
            if len(recieved_string) > 0:
                return recieved_string


    def test_sunpower_cryo(self, dt=None, f=None):
        too_low = 0
        too_high = 100
        try:
            recieved_string = self.check_serial(port='/dev/ttyUSB0', baudrate=4800, bytesize=7, parity='O', stopbits=1, timeout=1.0, check_string='TC')
        except IOError as e:
            pass # ignore IO errors, maybe should have an amount of time allowed to fail
        recieved_float = float(recieved_string)
        current_time = time.time()
        if recieved_float > too_low or recieved_float < too_high:
            # if good
            self.sunpower_time = current_time
            self.sunpower_alert = False
            print ('Sunpower cryo is good temp!')
            return
        else:
            if current_time - self.sunpower_time > dt and not self.sunpower_alert:
                # add information about current temperature
                self.email_success = self.SendPage(f'temporary bad temperature on sunpower cyrocooler controller. Outage time: {current_time - self.sunpower_time} s',category='c') and self.email_success
                self.sunpower_alert = current_time
                print ('sunpower is bad temp')
                return


    # check updated GSE5 hotspot IP - > also alert; this means we have a problem with the hotspot
    def check_hotspot_ip(self):
        pass

    def post_hotspot_ip(self):
        pass

    # check if data is out of bounds, we get alerts about data out of bounds
    def check_hkp(self,dt = None,f = None):

        if dt == None: dt = self.telemetry_dt
        if f == None: f = self.alert_dt

        #if not self.check_telemetry_campaign_network(dt = dt, f = f):
        #    return

        category = 'battery'
        checklist = ["@vbat_pdu0","@vbat_pdu2","@vbat_pdu3"]
        checklist = mppt_alarms_list + checklist
        self.check_hkp_list(checklist,alarm_ranges = {},category=category,dt=dt,f=f)

        category = 'trigger'
        #checklist = ['@tof_mtb_rate']
        # alarm_ranges is a dict, where key is the parameter name and the item is a list of (low,high) tuples specifying one or more allowed ranges
        # eg {'@vbat_pdu0':[(19,32)]
        alarm_ranges = json.load(open('/home/gaps/bfsw/pybfsw/payloads/gaps/mtb_alarms.txt'))#{'@tof_mtb_rate':(None,None)}
        checklist = []
        for key in alarm_ranges: checklist.append(key)
        self.check_hkp_list(checklist,alarm_ranges=alarm_ranges,category=category,dt=dt,f=f)

    def check_hkp_list(self,checklist,alarm_ranges={},dt=None,f=None,category=None):

        if dt == None: dt = self.telemetry_dt
        if f == None: f = self.alert_dt

        current_time = time.time()
        hkp_issues = self.CheckInstrumentHealth(checklist,alarm_ranges=alarm_ranges)

        # no current or previous problem
        if not hkp_issues and not self.inst_hkp_alert[category]:
            if self.verbose: print (f"category {category} checklist all good:",checklist)
            return

        # all old problem(s) resolved; no new problems
        if not hkp_issues:
            self.email_success = self.SendPage(f"Category {category} instrument Health Issues resolved! {category} hkp is OK!",category=category) and self.email_success
            self.inst_hkp_alert[category] = False
            self.inst_hkp[category] = time.time()
            return

        # new problem(s) detected
        first_key = next(iter(hkp_issues))
        n = len(hkp_issues.keys())
        msg = str(hkp_issues[first_key])
        if n > 1:
            msg = msg +  f"; {n} total instrument health issues\n"
            for key in hkp_issues:
                msg = msg + hkp_issues[key] + "\n"

        if not self.inst_hkp_alert[category]: # no old problems
            self.email_success = self.SendPage(msg,category=category) and self.email_success
            self.inst_hkp_alert[category] = current_time # time of most recent alert sent out
        elif current_time - self.inst_hkp_alert[category] > f:
            self.email_success = self.SendPage("Continuing " + msg,category=category,continuing =True) and self.email_success
            self.inst_hkp_alert[category] = current_time
        return

    def update_alive(self):
        if self.email_success:
            self.IAmAlive()
            if self.verbose: print ("updating i'm alive!\n")
        else:
            self.LogText("Note! Problem recorded with emailing. Not printing I'm alive")
            print ("Note! Problem with email sending! Not printing i'm alive")
            self.email_success = True

    def check_alive(self,dt=5*60,f=None,ssh_dt = .75*60):

        if f == None: f = self.alert_dt
        dt = max(dt,ssh_dt)

        current_time = time.time()
        p = str(self.alerts_dir / "im_alive")

        if (current_time - self.remote_alive  > ssh_dt):
            remote_alive_time = self.TrySsh(cmd_str=f"cat {p}")
            if self.verbose: print ('testing remote alive over ssh; returns', remote_alive_time)
            try: self.remote_alive = float(remote_alive_time)
            except:
                if self.verbose: print ("could not convert to a time ssh failed")
        elif self.verbose: print (f"last successful ssh was {current_time - self.remote_alive} s ago; skipping remote alive test")



        delta_remote = current_time - self.remote_alive

        # if remote is alive
        if delta_remote < dt:

            if self.remote_alive_alert:
                self.SendPage(f"alert system on {self.remote_ip} is back online!",category='network')
                self.remote_alive_alert = False

            if self.verbose: print (f"remote {self.remote_ip} reports alert system alive {round(delta_remote,1)} s ago!")
            return

        # remote alert server is down, or cannot access remote server
        if not self.remote_alive_alert:
            self.email_success = self.SendPage(f"alert system in {self.remote_ip} is down. Automatic monitoring is compromised!",category='network') and self.email_success
            self.remote_alive_alert = current_time
        elif current_time - self.remote_alive_alert > f:
            self.email_success = self.SendPage(f'alert system outage in {self.remote_ip} is ongoing.',category='network',continuing=True) and self.email_success
            self.remote_alive_alert = current_time
        else:
            pass # do nothing if we've already reported a problem within f seconds
        if self.verbose: print (f"{self.remote_ip} alert system is down.")
        return False

    def check_gses(self):

        yday = time.gmtime(time.time()).tm_yday
        if yday == self.gse_status_sent: return

        s = os.popen("df -Ph").read()#.splitlines()
        r = self.TrySsh(cmd_str='df -Ph')
        msg = self.server_name + " Server:\n" + s + "\n\n" + self.remote_ip + "\n" + r
        self.email_success = self.SendEmails(msg,category='g',subject = 'GAPS GSE Daily Health Check') and self.email_success
        self.gse_status_sent = yday

#if __name__ == '__main__':
    # alert_system = alert_system(verbose = True)
    # print("Alert system initialized successfully")

if __name__=="__main__":

    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("-p","--db_path",help="path to sqlite db", required = True)
    # /sqlRAIT/db/gsedb.sqlite on the gfp machine, or 127.0.0.1:44555 on your laptop",default=os.environ["GSE_DB_PATH"],)
    default_project = os.environ.get("GSE_PROJECT", "/Users/sophiaw/ssl grips/cryostat-monitor")
    p.add_argument("--project", help='bfsw project name, a directory name in /path/to/bfsw/pybfsw/payloads', default=default_project)
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("-b", "--berkeley", action="store_true",help="run berkeley server alert system")
    p.add_argument("-c","--campaign", action="store_true",help="run campaign server alert system")
    p.add_argument("-a","--alive", action="store_true",help="check alive only")
    p.add_argument("--sleep",help="sleep time [s] between running through the alert system check",default=10,type=int)
    p.add_argument("--remote_user", help='username login for remote port',default='gaps')#default=os.getlogin())
    p.add_argument("--remote_port",help='port for access remote server; default 55225 if we are berkeley server and campaign is remote; 55223 if we are campaign server and berkeley is remote', required=True)
    p.add_argument("--remote_pw",help='password for remote server access; default None assumes ssh keys are set up',default=False)
    p.add_argument("--remote_ip",help='ip for remote server; should be: gaps.astronevis.columbia.edu if we are berkeley server and campaign is remote; gamma1.ssl.berkeley.edu if we are campaign server and berkeley is remote',required=True)
    p.add_argument("--telemetry_dt",help='how out of date can telemetry data be before we raise an alarm',default=10*60)
    p.add_argument("--alert_dt",help='frequency of emails/texts for a given issue',default=5*60)

    args = p.parse_args()

    if args.verbose: print (args)

    alerts_dir = pathlib.Path(__file__).parents[1] / "alerts"

    if args.berkeley and args.campaign:
        print ("Error! Please select either the berkeley server or the campaign server mode")

    if args.berkeley:
        s = alert_system(telemetry_dt = args.telemetry_dt,alert_dt = args.alert_dt,path = args.db_path,project=args.project,verbose = args.verbose,alerts_dir=alerts_dir, remote_ip = args.remote_ip,remote_pw = args.remote_pw,remote_port=args.remote_port, remote_user = args.remote_user,server_name="Berkeley",test_connections = True)
        while True:
            s.copy_contact_list_remote() # look for changes in the contact list on the berkeley server, and copy them to the remote server if any changes exist
#            s.check_hkp() # checks housekeeing values are in range and up to date on campaign server
            # s.check_telemetry_campaign_network() # checks power on on campaign site, telemetry ok, gsedb building on berkeley server
 #           s.check_hkp() # checks housekeeing values are in range and up to date on campaign server
            #s.check_hotspot_ip() # checks hotspot ip so we have it in case of power outage; alerts us if hotspot is down
            # s.check_gses() # check gse diskspace and email once per day
            # s.check_alive() # checks tha tremote (campaign) server is alive
            s.test_sunpower_cryo()
            s.update_alive() # updates that berkeley server is alive and this check is working, including all emails
            time.sleep(args.sleep)

    elif args.campaign:
        s = alert_system(telemetry_dt = args.telemetry_dt,alert_dt = args.alert_dt,path=args.db_path,project=args.project,verbose=args.verbose,alerts_dir=alerts_dir, remote_ip = args.remote_ip, remote_pw = args.remote_pw, remote_port = args.remote_port, remote_user = args.remote_user,server_name="Campaign",test_connections = True)
        while True:
            s.check_hkp() # checks housekeeing values are in range and up to date on campaign server
#            s.post_hotspot_ip() # posts hotspot ip for campaign server to find
            s.test_gse6()
            s.check_alive() # checks that remote (berkeley) server is alive
            s.update_alive() # updates that campaign server is alive and this check is working, including all emails
            time.sleep(args.sleep)
    elif args.alive:
        s = alert_system(telemetry_dt = args.telemetry_dt,alert_dt = args.alert_dt,path=args.db_path,project=args.project,verbose=args.verbose,alerts_dir=alerts_dir, remote_ip = args.remote_ip, remote_pw = args.remote_pw, remote_port = args.remote_port, remote_user = args.remote_user,server_name=args.server_name,test_connections = True)
        while True:
            s.check_alive() # checks that remote (berkeley) server is alive
            s.update_alive() # checks that remote (berkeley) server is alive
            time.sleep(args.sleep)



    s = alert_system(telemetry_dt = args.telemetry_dt,alert_dt = args.alert_dt,path = args.db_path,project=args.project,verbose = args.verbose,alerts_dir=alerts_dir, remote_ip = args.remote_ip,remote_pw = args.remote_pw,remote_port=args.remote_port, remote_user = args.remote_user,server_name="Berkeley",test_connections = True)
    s.check_gses()



#to run: python alert_system.py --db_path "$DB_PATH" --remote_ip "127.0.0.1:44555" --remote_port 22222
#current problem: <- because not connected to server?
#Test Pages Failed! See debug log!
#Test emails failed! See debug log!
#Ssh connection is not working; check code
