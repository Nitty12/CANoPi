import socket
import json
import struct
import argparse

def recieve_udp(data_length, UDP_IP, UDP_PORT):
	with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
		sock.bind((UDP_IP, UDP_PORT))
		with open("/home/pi/DataFromModel/data_log.csv", "w") as csv_file:
			while True:
				try:
					data, addr = sock.recvfrom(1024)
					data_tuple = struct.unpack('%sf' % data_length, data)
					print('Recieved message: ', data_tuple)
					csv_file.write("{0}\n".format(data_tuple[0]))
					csv_file.flush()
				except KeyboardInterrupt:
					break
					
				except:
					#print('Cannot recieve UDP messages')
					pass

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Get the UDP Port to recieve data')
	parser.add_argument('-port', default=6161, type=int, help='The UDP port to recieve data')
	parser.add_argument('-ip', default="127.0.0.1", help='The IP address to recieve data')
	parser.add_argument('length', type=int, help='Length of recieved data')
	args = parser.parse_args()
	
	UDP_IP = args.ip
	UDP_PORT = args.port
	data_length = args.length
	
	recieve_udp(data_length, UDP_IP, UDP_PORT)

