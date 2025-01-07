import os
import sys
import smtplib
import time
import datetime
from email.mime.text import MIMEText

class CryostatMonitor:
    def __init__(self):
        # Recipients for alerts
        self.recipients = ["9259996540@tmomail.net", "sophii.wang@gmail.com"]
        self.msg_to = ",".join(self.recipients)
        
        self.telemetry_dt = 600  # Maximum delay for telemetry data in seconds
        self.alert_dt = 300      # Frequency of alerts in seconds
        self.last_alert_time = None
        #self.last_update_time = datetime.datetime.now() ADD BACK AND DELETE BELOW IF FUNCTIONING
        self.last_update_time = datetime.datetime.now() - datetime.timedelta(seconds=self.telemetry_dt + 1)

    def send_alert(self, subject, message):
        msg = MIMEText(message)
        msg['From'] = "monitor@cryostat.com"
        msg['To'] = self.msg_to
        msg['Subject'] = subject

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login("sophii.wang@gmail.com", "yqbaucoiblaimzjq")
                smtp.sendmail("sophii.wang@gmail.com", self.recipients, msg.as_string())
            print("Alert sent successfully.")
        except Exception as e:
            print("Failed to send alert:", e)

    def check_status(self):
        """Check cryostat system status and alert if issues are detected."""
        current_time = datetime.datetime.now()
        time_since_last_update = (current_time - self.last_update_time).total_seconds()

        if time_since_last_update > self.telemetry_dt:
            subject = "Cryostat Alert: Data Outdated"
            message = f"Cryostat telemetry data is outdated by {time_since_last_update // 60} minutes."
            self.send_alert(subject, message)
            self.last_alert_time = current_time

    def monitor(self):
        print("Starting cryostat monitor...")
        while True:
            self.check_status()
            time.sleep(self.alert_dt)

if __name__ == "__main__":
    monitor = CryostatMonitor()
    monitor.monitor()


#MODULAR IMPORT APPROACH
'''import time
import datetime
from alert_system import alert_system  # Assuming this contains an `alert_system` class
from grips_mon_vitality import MonitorChecker

class CryostatMonitor:
    def __init__(self):
        # Initialize the external classes
        self.alert_system = alert_system()
        self.monitor_checker = MonitorChecker()
        
        # Set recipients and monitoring intervals
        self.recipients = self.monitor_checker.sendmail_to
        self.telemetry_dt = 600  # e.g., 10 minutes for telemetry delay threshold
        self.alert_dt = 300      # e.g., alert every 5 minutes on issues

    def check_system(self):
        """Check cryostat system status by leveraging functions from imported classes."""
        self.alert_system.check_alive()
        self.monitor_checker.run()  # Assuming `run()` triggers alerts if conditions are met

    def monitor(self):
        """Main monitoring loop that continuously checks the cryostat system."""
        print("Starting cryostat monitoring with imported modules...")
        while True:
            self.check_system()
            time.sleep(self.alert_dt)

if __name__ == "__main__":
    monitor = CryostatMonitor()
    monitor.monitor()
'''