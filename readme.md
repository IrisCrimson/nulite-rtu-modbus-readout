# Nulite Heatpump RTU modbus readout script #

__Note: python earlier than version 3.9 is not supported__

Python script to read out all the parameters (P) and measurement values (C) of the heatpump and store it to csv files.

Needed HW: RS485 usb dongle

## The script has following comand line options ##
-c: Serial Com port that should be used e.g COM2 (linux is untested but should work as well /dev/ttyx)

-o: Path to the output folder, within this folder the two output reports for the parameters and the meas values are stored

## Installation ##
install the req packages from the requirements.txi via pip
pip install -r /path/to/requirements.txt
