#!/usr/bin/env python
import sys, time, syslog, serial, urllib3, requests

################################################
# Send Message to VMware LogInsight via REST API
################################################
# ip - LogInsight IP address or Host name
# msg - log message
# fields - Log Insight fields in JSON array
#          Example:
#          [
#             {
#               "name":"id",
#               "content":"bbdd1dda8f"
#             },
#             {
#               "name":"container",
#               "content":"/vigilant_goldberg"
#             }
#          ]

def sendMsgToLogInsight(ip,msg,fields=[]):
  api_url = "https://" + ip + ":9543/api/v1/events/ingest/1"
  json_events = {
                  "events":
                    [
                      {
                        "text": msg,
                        "fields": fields
                      }
                    ]
                }
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
  response = requests.post(api_url, json=json_events, verify=False)
  return response



###########################################################
# Send command to serial device
# device [serial.Serial Object], command [string] - command
###########################################################
def sendCommand(device,command):
  command = str(command) + "\r"
  response = ""
  device.write(command.encode())
  time.sleep(0.5)  #give the serial port sometime to receive the data
  numOfLines = 0
  while True:
    response_c = device.readline()
    if (response_c != b''):
      response_d = response_c.decode()
      response = response_d[1:-2]
    numOfLines = numOfLines + 1
    if (numOfLines >= 5):
      break
  return response 

###########################################################
# Convert hex to string
###########################################################
def hex_to_string(hex):
    if hex[:2] == '0x':
        hex = hex[2:]
    string_value = hex.upper();
    return string_value

###################################################
# Main handler
###################################################
def main():
  # Initialize syslog 
  syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_LOCAL0);

  # Wattson
  ser = serial.Serial()
  ser.port = "/dev/ttyUSB0"
  ser.baudrate = 19200
  ser.bytesize = serial.EIGHTBITS #number of bits per bytes
  ser.parity = serial.PARITY_NONE #set parity check: no parity
  ser.stopbits = serial.STOPBITS_ONE #number of stop bits
  #ser.timeout = None          #block read
  #ser.timeout = 0             #non-block read
  ser.timeout = 0.1             # timeout X second for read
  ser.writeTimeout = 0.1     #timeout X second for write
  ser.xonxoff = False     #disable software flow control
  ser.rtscts = False     #disable hardware (RTS/CTS) flow control
  ser.dsrdtr = False       #disable hardware (DSR/DTR) flow control
  
  ser.open()
  ser.flushInput()  #flush input buffer, discarding all its contents
  ser.flushOutput() #flush output buffer, aborting current output

  if ser.isOpen():
    serial_number = sendCommand(ser,"nows")

    # CURRENT POWER USAGE
    #####################
    command = "nowp"

    power = []
    i=0
    time0 = time.time()

    while True:
      if i>50:
        break
      current_power_usage_hex_string = sendCommand(ser,command)
      try:
        current_power_usage_int = int(current_power_usage_hex_string, 16)
      except ValueError:
        current_power_usage_int = 65535
      power.append(current_power_usage_int)
      time_spent = time.time() - time0
      if time_spent<1:
        time.sleep(1-time_spent)
      time_sample = time.time() - time0
      print("Time spent:",time_spent)
      print("Time sample:",time_sample)
      print(i)
      print(power[i])
      i += 1
      time0 = time.time()

    power_sum = 0
    for p in power:
      power_sum += p
    power_avg = round(power_sum / len(power),0)

    # Send to LogInsight
    log_message = "Wattson Average Power Consumption for last ~1 min: " + str(power_avg) + " Watt"
    print("Log message:",log_message)
    response=sendMsgToLogInsight("syslog.home.uw.cz",log_message)
    print ("Response:", response)

  else:
    print("Cannot open serial port ")

main()
