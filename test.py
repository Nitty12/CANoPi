import time
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
def on_connect(client, obj, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("test/topic")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, obj, msg):
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
    
   
def get_msg_by_name(message_name, formatted_msg, db, msg):
    if re.match(rf"\n{re.escape(message_name)}\(\n", formatted_msg) is not None:
        decoded_signals = decode_message(db, msg)
        
        # Serializing the data to sned over network
        signal_values = list(decoded_signals.values())
        
        udp_msg = struct.pack('%sf' % len(signal_values), *signal_values)   
        return udp_msg
    else:
        # print('Else')
        return None
        
def send_via_udp(sock, udp_msg, name, port):
    #Send the message
    if udp_msg is not None:
        try:
            sock.sendto(udp_msg, (UDP_IP, port))
            print('Sending data: {0} to IP:{1} Port:{2}'.format(name, UDP_IP, port))
        # except:
            # pass
            #print('Cannot send UDP messages')
            return True
        except Exception as e:
            print('Exception --- ',str(e))
            return str(e)
    else:
        return False
        #print('Message not recieved')    
        
            
def format_and_send_CAN(msg_list, sock, db_list):
    # Both the CAN may contain messages with same name
    ICAN_msg = msg_list[0]
    ECAN_msg = msg_list[1]
    ICAN_db = db_list[0]
    ECAN_db = db_list[1]  
    
    formatted_ICAN_msg = format_message_by_frame_id(ICAN_db, ICAN_msg.arbitration_id, ICAN_msg.data, decode_choices=None,
                                            single_line=False)

    formatted_ECAN_msg = format_message_by_frame_id(ECAN_db, ECAN_msg.arbitration_id, ECAN_msg.data, decode_choices=None,
                                            single_line=False) 
                                            
    #Select the message to send
    ICAN_msg_names = ['LWI_01', 'SARA_11', 'Fahrwerk_01', 'ESP_05', 'Kombi_03', 'NavData_03', 'NavData_02', 'Kombi_02']
    ports = [6001, 6002, 6003, 6004, 6005, 6006, 6007, 6008]
    for name, port in zip(ICAN_msg_names, ports):
        udp_msg = get_msg_by_name(name, formatted_ICAN_msg, ICAN_db, ICAN_msg)
        sent = send_via_udp(sock, udp_msg, name, port)
        if sent:
            break
            
    ECAN_msg_names = ['ESP_03', 'DEV_RDK_Resp_03',  'DEV_RDK_Resp_04', 'DEV_RDK_Resp_05',  'DEV_RDK_Resp_06', 'DEV_RDK_Resp_07',  'DEV_RDK_Resp_08', 'DEV_RDK_Resp_09',  'DEV_RDK_Resp_0A', 'Klemmen_Status_01']
    ports = [7001, 7002, 7003, 7004, 7005, 7006, 7007, 7008, 7009, 7010]
    for name, port in zip(ECAN_msg_names, ports):
        udp_msg = get_msg_by_name(name, formatted_ECAN_msg, ECAN_db, ECAN_msg)
        sent = send_via_udp(sock, udp_msg, name, port)
        if sent:
            break    
    
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
				full_log.append([float(i) for i in row])
		
	data_unpacked = full_log[-1]
	return data_unpacked


def send_initial_value(start_value, sock):
    port = 8001   
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
  

def recieve_udp(sock, data_length):
    data, addr = sock.recvfrom(1024)
    data_unpacked_tuple = struct.unpack('%sf' % data_length, data)
    # print('Recieved message: ', data_unpacked_tuple)
    return data, data_unpacked_tuple
    

def publish_to_mqtt(data, client):
    client.publish('test/topic', data)


def save_to_memory(data, data_unpacked_tuple, first_time = []):
    if first_time == []:
        os.system('sudo rm /home/pi/DataFromModel/data_log.csv')
        print('Deleted old log file')
        first_time.append('Entered once')
        
    with open("/home/pi/DataFromModel/data_log.csv", "a") as csv_file:
        try:
            print('========================================================')
            print('>>>>>Saved message: ', data_unpacked_tuple)
            print('========================================================')
            writer = csv.writer(csv_file)
            writer.writerow(data_unpacked_tuple)
            # csv_file.write("{0}\n".format(data_unpacked_tuple[0]))
            csv_file.flush()
            
        # except:
            # pass
            #print('Cannot recieve UDP messages')
        except Exception as e:
            return str(e)
    return 0


def check_CAN_sleep(ICAN_bus, ECAN_bus):
    # Check CAN messages for 5 seconds
    sec = 0
    while sec <= 5:
        # Blocking read with timeout of 0.5 second
        ICAN_msg = ICAN_bus.recv(0.5)
        ECAN_msg = ECAN_bus.recv(0.5)
        
        # Check for 5 seconds whether the CAN bus is sleeping 
        if ICAN_msg is not None or ECAN_msg is not None:
            return False
        sec += 1
    return True
    
    
def check_CAN_status():
    with can.interface.Bus(bustype="socketcan", channel='can0', bitrate=500000) as ICAN_bus, can.interface.Bus(bustype="socketcan", channel='can1', bitrate=500000) as ECAN_bus:
        status = False
        try:
            # Check for 2 seconds
            t_end = time.time() + 60*2
            while time.time() < t_end:
                #Recieve all the CAN messages
                ICAN_msg = ICAN_bus.recv(0.5)
                ECAN_msg = ECAN_bus.recv(0.5)
                if ICAN_msg is not None or ECAN_msg is not None:
                    status = True
                    return status
                    
            return status   
        except:
            return status
                

def start_communication(ICAN_db, ECAN_db, start_value, client):
    """Receives all messages, select the needed message and send via UDP
        Send the initial values to the model and recieve the current outputs
        from the model and save it. Additionally send the output over 
        encrypted MQTT"""

    with can.interface.Bus(bustype="socketcan", channel='can0', bitrate=500000) as ICAN_bus, can.interface.Bus(bustype="socketcan", channel='can1', bitrate=500000) as ECAN_bus:
        
        # Generate a UDP socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock_send, socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock_recieve_to_save, socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock_recieve_to_mqtt:
            
            # Port for recieving UDP message from the model and save to sd card
            port = 6161
            sock_recieve_to_save.bind((UDP_IP, port))
            sock_recieve_to_save.settimeout(0.05)
            # Port for recieving UDP message from the model and send via mqtt
            port = 6262
            sock_recieve_to_mqtt.bind((UDP_IP, port))
            sock_recieve_to_mqtt.settimeout(0.05)
            
            err = 0
            
            # Save messages every 1 minute
            sampling_time = 0.05
            interval = 100
            counter = 0 
            
            while True:
                try:
                    counter += 1
                    
                    #Recieve all the CAN messages
                    ICAN_msg = ICAN_bus.recv(0.05)
                    ECAN_msg = ECAN_bus.recv(0.05)
                    
                    # Check for 5 seconds whether the CAN bus is sleeping 
                    if ICAN_msg is None and ECAN_msg is None:
                        CAN_sleeping = check_CAN_sleep(ICAN_bus, ECAN_bus)
                        if CAN_sleeping:
                            return 1
                    #Format the message according to the CAN database file & send via UDP
                    else:
                        err = format_and_send_CAN([ICAN_msg, ECAN_msg], sock_send, [ICAN_db, ECAN_db])
                            
                    # Send the Initial values to the model via UDP
                    err = send_initial_value(start_value, sock_send)
                    
                    # Recieve current values to save from the model via UDP
                    data_save, data_save_unpacked_tuple = recieve_udp(sock_recieve_to_save, data_length=34)
                    
                    # Recieve current values to send via mqtt from the model via UDP
                    data_to_mqtt, data_to_mqtt_unpacked_tuple = recieve_udp(sock_recieve_to_mqtt, data_length=1)                    
                    
                    if counter > interval/sampling_time:
                        # Save to a file and publish via MQTT 
                        save_to_memory(data_save, data_save_unpacked_tuple)
                        publish_to_mqtt(data_to_mqtt, client)
                        counter = 0
                    
                except KeyboardInterrupt:
                    print('Interrupted by user')
                    return 1
                    
                except Exception as e:
                    #print(str(e))
                    pass


if __name__ == "__main__":
    t_start = time.time()
    
    print('Reading the dbc file ...')
    path = os.path.dirname(os.path.abspath(__file__))
    ICAN_db = cantools.database.load_file(os.path.join(path, 'MLBevo_Gen2_MLBevo_ICAN_KMatrix_V8.19.05F_20200420_AM.dbc'))
    ECAN_db = cantools.database.load_file(os.path.join(path, 'MLBevo_Gen2_MLBevo_ECAN_KMatrix_V8.15.00F_20171109_SE_RDK_merged.dbc'))
    print('Completed reading the dbc file')

    try:
        # Check if recieving CAN messages
        CAN_available = check_CAN_status()
        
        if CAN_available:
            # Copy the previous log for input to model
            if os.path.isfile('/home/pi/DataFromModel/data_log.csv'):
                os.system('sudo cp /home/pi/DataFromModel/data_log.csv /home/pi/DataToModel/data_log.csv')
                print('Completed copying files')
            
            start_value = get_initial_values()
            
            client = MQTT_initialize()

            # Start the simulink model
            # model_start_command = 'sudo /home/pi/MATLAB_ws/R2020b/TWE_Raspberry.elf'
            # start_prog = subprocess.Popen(model_start_command, shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
            # print('Starting model')
            
            shutdown_trigger = start_communication(ICAN_db, ECAN_db, start_value, client)
            
            if shutdown_trigger:
                # subprocess.call("sudo shutdown -h now", shell=True)
                print('-------Shut down trigger here -------')
            
            # Stop the simulink model
            model_stop_command = 'sudo killall /home/pi/MATLAB_ws/R2020b/TWE_Raspberry.elf'
            stop_prog = subprocess.Popen(model_stop_command, shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
            print('Stopping model')  
            
    except Exception as e:
        print('Error in main module')
        print(str(e))
        
