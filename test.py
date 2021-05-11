
import os
import subprocess
import can
import cantools
import socket
import struct
import pickle
import json
import re
import csv
import paho.mqtt.client as mqtt

from cantools.subparsers.utils import format_message_by_frame_id
from cantools.subparsers.utils import _format_message_multi_line
from cantools.subparsers.utils import _format_signals


UDP_IP = "127.0.0.1"

# The callback for when the MQTT client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    #client.subscribe("test/topic")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))


def decode_message(db, input_msg):  
    try:
        message = db.get_message_by_frame_id(input_msg.arbitration_id)
    except KeyError:
        return ' Unknown frame id {0} (0x{0:x})'.format(input_msg.arbitration_id)
    
    try:
        decoded_signals = message.decode(input_msg.data, decode_choices=None)
    except Exception as e:
        return ' ' + str(e)
    
    return decoded_signals
    

def send_SARA_11(formatted, db, msg):
    message_name = 'SARA_11'
    if re.match(rf"\n{re.escape(message_name)}\(\n", formatted) is not None:
        decoded_signals = decode_message(db, msg)
        
        # Serializing the data to sned over network
        signal_values = list(decoded_signals.values())
        
        udp_msg = struct.pack('%sf' % len(signal_values), *signal_values)   
        return udp_msg
    else:
        return None
   

def format_and_send_CAN(msg, sock, db):
    port = 6363
    
    timestamp = msg.timestamp
    formatted = format_message_by_frame_id(db, msg.arbitration_id, msg.data, decode_choices=None,
                                            single_line=False)
    #Select the message to send
    udp_msg = send_SARA_11(formatted, db, msg)
    
    #Send the message
    if udp_msg is not None:
        try:
            sock.sendto(udp_msg, (UDP_IP, port))
            #print('Sending data: {0} to IP:{1} Port:{2}'.format(udp_msg, UDP_IP, port))
        # except:
            # pass
            #print('Cannot send UDP messages')
        except Exception as e:
            return str(e)
    else:
        pass
        #print('Message not recieved')
    return 0
    
    
def MQTT_initialize():
    client = mqtt.Client()
    client.tls_set('/etc/mosquitto/ca_certificates/ca.crt')
    client.tls_insecure_set(True)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("127.0.0.1", 8883)
    client.subscribe("test/topic")
    return client
                
                    
def get_initial_values():
	with open("/home/pi/DataToModel/data_log.csv", "r") as csv_file:
		full_log = []
		row_index = 0
		csvReader = csv.reader(csv_file)
		for row in csvReader:
			if row:
				row_index +=1
				full_log.append([float(row[0])])
		
	data_unpacked = full_log[-1]
	return data_unpacked


def send_initial_value(start_value, sock):
    port = 6060    
    try:
        data = struct.pack('%sf' % len(start_value), *start_value)   
        sock.sendto(data, (UDP_IP, port))
        #print('Sending data: {0} to IP:{1} Port:{2}'.format(data, UDP_IP, port))      
    # except:
        # pass
        #print('Cannot send initial values')    
    except Exception as e:
        return str(e)
    return 0
  

def recieve_udp(sock, client, data_length):
    with open("/home/pi/DataFromModel/data_log.csv", "a") as csv_file:
        try:
            data, addr = sock.recvfrom(1024)
            data_tuple = struct.unpack('%sf' % data_length, data)
            print('Recieved message: ', data_tuple)
            csv_file.write("{0}\n".format(data_tuple[0]))
            csv_file.flush()
            
            client.publish('test/topic', data)
            
        # except:
            # pass
            #print('Cannot recieve UDP messages')
        except Exception as e:
            return str(e)
    return 0


def check_CAN_status():
    with can.interface.Bus(bustype="socketcan", channel='can0', bitrate=500000) as bus:
        status = False
        try:
            while True:
                #Recieve all the CAN messages
                msg = bus.recv(1)
                
                if msg is not None:
                    status = True
                    return status
                
        except:
            return status
                

def start_communication(db, start_value, client):
    """Receives all messages, select the needed message and send via UDP
        Send the initial values to the model and recieve the current outputs
        from the model and save it. Additionally send the output over 
        encrypted MQTT"""

    with can.interface.Bus(bustype="socketcan", channel='can0', bitrate=500000) as bus:
        
        # Generate a UDP socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock_send, socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock_recieve:
            
            # Port for recieving UDP message from the model
            port = 6161
            sock_recieve.bind((UDP_IP, port))
            sock_recieve.settimeout(0.05)
            
            err = 0
            while True:
                try:
                    #Recieve all the CAN messages
                    msg = bus.recv(1)
                    
                    #Format the message according to the CAN database file & send via UDP
                    if msg is not None:
                        err = format_and_send_CAN(msg, sock_send, db)
                            
                    # Send the Initial values to the model via UDP
                    err = send_initial_value(start_value, sock_send)
                    
                    # Recieve current values from the model via UDP and save and publish it
                    err = recieve_udp(sock_recieve, client, data_length=1)
                    
                except KeyboardInterrupt:
                    print('Interrupted')
                    break


if __name__ == "__main__":
    print('Reading the dbc file ...')
    path = os.path.dirname(os.path.abspath(__file__))
    db = cantools.database.load_file(os.path.join(path, 'MLBevo_Gen2_MLBevo_ICAN_KMatrix_V8.21.01F_20210129_EICR.dbc'))
    print('Completed reading the dbc file')

    try:
        print('main fn')
        # Check if recieving CAN messages
        CAN_available = check_CAN_status()
        
        if CAN_available:
            # Copy the previous log for input to model
            if os.path.isfile('/home/pi/DataFromModel/data_log.csv'):
                os.system('sudo cp /home/pi/DataFromModel/data_log.csv /home/pi/DataToModel/data_log.csv')
                os.system('sudo rm /home/pi/DataFromModel/data_log.csv')
                print('Completed copying files')
            
            start_value = get_initial_values()
            
            client = MQTT_initialize()

            # Start the simulink model
            model_start_command = 'sudo /home/pi/MATLAB_ws/R2020b/C/PM_Sandbox/Code/Matlab/Reifenverschleiss/Online_Modelle/Raspberry_-_Copy_Nitty/Test.elf'
            start_prog = subprocess.Popen(model_start_command, shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
            print('Starting model')
            
            start_communication(db, start_value, client)
            
            # Stop the simulink model
            model_stop_command = 'sudo killall /home/pi/MATLAB_ws/R2020b/C/PM_Sandbox/Code/Matlab/Reifenverschleiss/Online_Modelle/Raspberry_-_Copy_Nitty/Test.elf'
            stop_prog = subprocess.Popen(model_stop_command, shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
            print('Stopping model')  
            
    except:
        pass
        
