import socket
import json
import struct
import argparse
import csv

def send_udp(data_unpacked, UDP_IP, UDP_PORT):
	with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
		while True:
			try:
				data = struct.pack('%sf' % len(data_unpacked), *data_unpacked)   
				sock.sendto(data, (UDP_IP, UDP_PORT))
				print('Sending data: {0} to IP:{1} Port:{2}'.format(data, UDP_IP, UDP_PORT))
				
			except KeyboardInterrupt:
				break
				
			except:
				print('Cannot send UDP messages')

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Get the UDP Port and data to send')
	parser.add_argument('-port', default=6060, type=int, help='The UDP port to send data to')
	parser.add_argument('-ip', default="127.0.0.1", help='The IP address to send data to')
	args = parser.parse_args()
	
	UDP_IP = args.ip
	UDP_PORT = args.port
	
	with open("/home/pi/DataToModel/data_log.csv", "r") as csv_file:
		full_log = []
		row_index = 0
		csvReader = csv.reader(csv_file)
		for row in csvReader:
			if row:
				row_index +=1
				full_log.append([float(row[0])])
		
	data_unpacked = full_log[-1]
	send_udp(data_unpacked, UDP_IP, UDP_PORT)
