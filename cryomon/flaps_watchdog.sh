#!/bin/bash

# Program name
WATCHED="flaps_cryo"
WATCHED_PATH="/home/grips/fsw/trunk/"
# Command line for starting the program
CMDLINE=""
# Distributor alive file
ALIVEFILE="/dev/shm/monitor_is_alive"
# Update tolerance for that file (i.e. how old it is allowed to be before restarting the program)
ALIVETOLERANCE=300

# Watchdog log file
datetime=$(date +"%Y_%m_%d_%H_%M_%S")
LOG=/home/grips/monitor_code/logs/${WATCHED}_$datetime
WLOG=/home/grips/monitor_code/logs/${WATCHED}Watchdog.log

# Check if we have exactly one process running
COUNT=`ps -ef | grep ${WATCHED} | grep -v grep | wc -l`

if [ ${COUNT} -eq 0 ]; then
  # No instance is running - we start it
  echo "ERROR: ${WATCHED} not running! Starting it!" | ts >> ${WLOG}
  echo "creating log: ${LOG}" | ts >> ${WLOG}
  ${WATCHED_PATH}${WATCHED} ${CMDLINE} &> ${LOG} &
  LASTPID=$!
  echo "INFO: Started instance of ${WATCHED} with PID ${LASTPID}" | ts >> ${WLOG}
elif [ ${COUNT} -gt 1 ]; then 
  # More than one instance is running - we kill all and start one
  echo "ERROR: More than one ${WATCHED} instance running! Killing all..." | ts >> ${WLOG}
  ps -ef | grep ${WATCHED} | grep -v grep | while read LINE; do
    DPID=`echo ${LINE} | awk -F" " '{ print $2 }'`
    kill -INT ${DPID}
    sleep 5
    kill -9 ${DPID}
  done
  sleep 1
  echo "       ... and restarting one" | ts >> ${WLOG}
  echo "creating log: ${LOG}" | ts >> ${WLOG}
  ${WATCHED_PATH}${WATCHED} ${CMDLINE} &>> ${LOG} &
  LASTPID=$!
  echo "INFO: Started instance of ${WATCHED} with PID ${LASTPID}" | ts >> ${WLOG}
else
  # Exactly one instance is rinnung 
  echo "OK: Exactly one ${WATCHED} instance running!" | ts >> ${WLOG}
  
  # Now check if it is still alive
  # If the file (ALIVEFILE) was updated more than ~1 minute (ALIVETOLERANCE) ago kill and restart the program
#TODO  NOWTIME=$(date +%s)
#  if [[ -f ${ALIVEFILE} ]]; then
#    FILEUPDATETIME=$(stat -c %Y ${ALIVEFILE} )
#    echo "Now: ${NOWTIME} vs file update time: ${FILEUPDATETIME}" | ts >> ${WLOG}
#  else
#    FILEUPDATETIME=1    
#  fi
#  
#  if [[ ! -f ${ALIVEFILE} ]] || [ $(( ${NOWTIME} - ${FILEUPDATETIME} )) -gt ${ALIVETOLERANCE} ]; then
#    echo "ERROR: ${WATCHED}'s alive file doesn't exit or has not been update for $(( ${NOWTIME} - ${FILEUPDATETIME} )) sec! Killing ${WATCHED}..." | ts >> ${WLOG}
#    ps -ef | grep ${WATCHED} | while read LINE; do
#      DPID=`echo ${LINE} | awk -F" " '{ print $2 }'`
#      echo "INFO: Killing PID ${DPID}" | ts >> ${WLOG}
#      kill -INT ${DPID}
#      sleep 5
#      kill -9 ${DPID}
#    done
#    sleep 1
#    echo "       ... and restarting one instance of ${WATCHED}" | ts >> ${WLOG}
#    echo "creating log: ${LOG}" | ts >> ${WLOG}
#    ${WATCHED_PATH}${WATCHED} ${CMDLINE} &>> ${LOG} &
#    LASTPID=$!
#    echo "INFO: Started instance of ${WATCHED} with PID ${LASTPID}" | ts >> ${WLOG}
#  else
#    echo "OK: ${WATCHED}'s alive file has been updated within $(( ${NOWTIME} - ${FILEUPDATETIME} )) seconds!" | ts >> ${WLOG} 
#  fi
fi

# Rotate logs:
if [ $RANDOM -gt 32700 ]; then  # do this only a few times a day
#  if [ $(cat ${LOG} | wc -l) -gt 200000 ]; then
#    tail -f 100000 ${LOG} > /tmp/${LOG}
#    mv /tmp/${LOG} ${LOG}
#  fi
  
  if [ $(cat ${WLOG} | wc -l) -gt 200000 ]; then
    tail -f 100000 ${WLOG} > /tmp/${WLOG}
    mv /tmp/${WLOG} ${WLOG}
  fi
fi

exit 0;
