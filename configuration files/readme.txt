Install python-can & cantools
	pip3 install python-can
	pip3 install cantools

If using mosquitto broker inside pi, install by:
	sudo apt-get install mosquitto
	sudo apt-get install mosquitto-clients

Paste the contents of config.txt into boot/config.txt in the raspberry pi

Type crontab -e and add the following lines:
	@reboot sudo ip link set can0 up type can bitrate 500000
	@reboot sudo ip link set can1 up type can bitrate 500000
