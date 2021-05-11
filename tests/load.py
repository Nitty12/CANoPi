import os
import time
import csv
from time import sleep
from datetime import datetime

with open("/home/pi/DataFromModel/data_log.csv", "r") as file:
	csvReader = csv.reader(file)
	for row in csvReader:
		print(row)
