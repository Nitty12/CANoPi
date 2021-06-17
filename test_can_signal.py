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
    
   
def get_udp_msg_by_name(db, msg):
    decoded_signals = decode_message(db, msg)
    
    # Serializing the data to sned over network
    signal_values = list(decoded_signals.values())
    
    udp_msg = struct.pack('%sf' % len(signal_values), *signal_values)   
    return udp_msg
        
def format_and_send_CAN(msg_list, db_list):
    # Both the CAN may contain messages with same name
    ICAN_msg = msg_list[0]
    ECAN_msg = msg_list[1]
    ICAN_db = db_list[0]
    ECAN_db = db_list[1]  
    
    formatted_ICAN_msg, ICAN_msg_name = format_message_by_frame_id(ICAN_db, ICAN_msg.arbitration_id, ICAN_msg.data, decode_choices=None,
                                            single_line=False)

    formatted_ECAN_msg, ECAN_msg_name  = format_message_by_frame_id(ECAN_db, ECAN_msg.arbitration_id, ECAN_msg.data, decode_choices=None,
                                            single_line=False) 
    #Select the message to send
    Reqd_ICAN_msgs = ['LWI_01', 'SARA_11', 'Fahrwerk_01', 'ESP_05', 'Kombi_03', 'NavData_03', 'NavData_02', 'Kombi_02']
    ports = [6001, 6002, 6003, 6004, 6005, 6006, 6007, 6008]
    # ICAN_msg_names = ['LWI_01']
    # ports = [6001]
    if ICAN_msg_name in Reqd_ICAN_msgs:
        idx = Reqd_ICAN_msgs.index(ICAN_msg_name)
        udp_msg = get_udp_msg_by_name(ICAN_db, ICAN_msg)
        print('ICAN: ', ICAN_msg_name)
        # print(f'Sending {ICAN_msg_name} in port {ports[idx]}')
            
    Reqd_ECAN_msgs = ['ESP_03', 'DEV_RDK_Resp_03',  'DEV_RDK_Resp_04', 'DEV_RDK_Resp_05',  'DEV_RDK_Resp_06', 'DEV_RDK_Resp_07',  'DEV_RDK_Resp_08', 'DEV_RDK_Resp_09',  'DEV_RDK_Resp_0A', 'Klemmen_Status_01']
    ports = [7001, 7002, 7003, 7004, 7005, 7006, 7007, 7008, 7009, 7010]
    # ECAN_msg_names = ['DEV_RDK_Resp_03', 'DEV_RDK_Resp_05', 'DEV_RDK_Resp_09', 'DEV_RDK_Resp_0B']
    # ports = [7001, 7002, 7003, 7004]
    if ECAN_msg_name in Reqd_ECAN_msgs:
        idx = Reqd_ECAN_msgs.index(ECAN_msg_name)
        udp_msg = get_udp_msg_by_name(ECAN_db, ECAN_msg)
        print('ECAN: ', ECAN_msg_name)
        # print(f'Sending {ECAN_msg_name} in port {ports[idx]}')
    
    return 0
    
def start_communication(ICAN_db, ECAN_db):
    """Receives all messages, select the needed message and send via UDP
        Send the initial values to the model and recieve the current outputs
        from the model and save it. Additionally send the output over 
        encrypted MQTT"""

    with can.interface.Bus(bustype="socketcan", channel='can0', bitrate=500000) as ICAN_bus, can.interface.Bus(bustype="socketcan", channel='can1', bitrate=500000) as ECAN_bus:
        while True:
            try:
                ICAN_msg = ICAN_bus.recv(0.0)
                ECAN_msg = ECAN_bus.recv(0.0)
                err = format_and_send_CAN([ICAN_msg, ECAN_msg], [ICAN_db, ECAN_db])

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
        shutdown_trigger = start_communication(ICAN_db, ECAN_db)
        if shutdown_trigger:
            print('-------Shut down trigger here -------')
            
    except Exception as e:
        print('Error in main module')
        print(str(e))
