import os
import time 
from time import sleep
from datetime import datetime

with open("/home/pi/data_log_toModel.csv", "w") as csv_file:
	i=0.0
	try:
		while True:
			i=i+0.25
			csv_file.write("{0}\n".format(i))
			csv_file.flush()
			sleep(1)
	except KeyboardInterrupt:
		pass 
