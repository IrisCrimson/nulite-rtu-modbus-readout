import os
import sys
import struct
import logging
import argparse
from datetime import datetime

from pymodbus.client.sync import ModbusSerialClient as ModbusClient

# setup the logger
logger = logging.getLogger('Modbus')
logger.setLevel(logging.DEBUG)

# Formatter for log messages
formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Adding handlers to the logger
logger.addHandler(console_handler)

class debugDummy():
    def __init__(self):
        self.registers = [65529, 2, 3, 4, 5]
    @property
    def registers(self):
        return self.__registers
    @registers.setter
    def registers(self, value):
        self.__registers = value


class ReaderBase(object):
    def __init__(self, client, type):
        self.client = client
        self.type = type
        self.data = []
        self.data_filename = "base.csv"
    
    @property
    def type(self):
        return self.__type

    @type.setter
    def type(self, value):
        self.__type = value

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, value):
        self.__data = value

    @property
    def data_filename(self):
        return self.__data_filename

    @data_filename.setter
    def data_filename(self, value):
        self.__data_filename = value


    def addValueToDataList(self, value, name, description, register, raw=""):
        if type(value) is int:
            self.data.append(f"{name}, {value}, {description}, {register}, {raw}")
        else:
            self.data.append(f"{name}, {value:.2f}, {description}, {register}, {raw}")

    def writeDataToFile(self, file_path):
        if len(self.data) > 0 and os.path.isdir(file_path):
            # Get the current date and time
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
            # Split the filename into name and extension
            base, extension = os.path.splitext(self.data_filename)
            
            # Create a new filename with the timestamp
            new_filename = f"{base}_{timestamp}{extension}"
            
            file_path = os.path.join(file_path, new_filename)
            
            logger.info(f"write data to  {file_path}")
            
            fp = open(os.path.join(file_path), 'w')
            fp.write("name, value, description, register, raw_value \n")
            for line in self.data:
                fp.write(line + '\n')
            fp.close()

    def raw_value(self, register_value):
        return register_value

    def scale_value(self, register_value, scale, offset):
        signed_value = struct.unpack('h', struct.pack('H', register_value))[0]
        return (signed_value + offset) * scale
    
    def convert(self, register_value, scale, offset):
        if scale == 0:
            return int(self.raw_value(register_value))
        else:
            return float(self.scale_value(register_value, scale, offset))

    def read(self):
        logger.info(f"reading {self.type}")
        for block in self.readout_dict:
            start_address = block * 5
            logger.debug(f"read block {block}, start_address {start_address}, number of words {len(self.readout_dict[block])}")
#            read_vals  = self.client.read_holding_registers(start_address, 5, unit=1) # start_address, count, slave_id
            try:
                read_vals  = self.client.read_holding_registers(start_address, 5, unit=1) # start_address, count, slave_id
            except Exception as _e:
                logger.error(f"could not read the value via modbus client {_e}")
                sys.exit(1)
                #read_vals = debugDummy()
            
            for parameter in self.readout_dict[block]:
                block_offset = parameter[0] - start_address
                register_value = read_vals.registers[block_offset]
                value = self.convert(register_value, parameter[3], parameter[4])
                logger.debug(f"register {parameter[0]}, block offset {block_offset}, scaled value {value}")
                self.addValueToDataList(value, parameter[1], parameter[2], parameter[0], register_value )

class ParameterReader(ReaderBase):
    def __init__(self, client):
        super().__init__(client, "Parameters")
        self.data_filename = "Parameters.csv"
        self.readout_dict = {0: [(0, "P00", "On-off", 0, 0), 
                                 (1, "P01", "Mode", 0, 0), 
                                 (2, "P02", "Heating target temperature", 1, 0), 
                                 (3, "P03", "Cooling target temperature", 1, 0), 
                                 (4, "P04", "Domestic hot water target temperature", 1, 0)],
                             1: [(5, "P05", "Indoor target temperature", 1, 0), 
                                 (6, "P06", "AC water temperature difference", 0.5, 0), 
                                 (7, "P07", "DHW water temperature difference", 0.5, 0),
                                 (8, "P08", "Domestic hot water AU option", 0, 0), 
                                 (9, "P09", "Hot water max frequency", 0, 0)],
                             2: [(10, "P10", "Sterilization interval days", 0, 0), 
                                 (11, "P11", "Sterilization start time", 0, 0), 
                                 (12, "P12", "Sterilization running time", 0, 0), 
                                 (13, "P13", "Sterilization temperature", 1, 0), 
                                 (14, "P14", "Force sterilization", 0, 0) ],
                             3: [(15, "P15", "Domestic hot water function selection", 0, 0), 
                                 (16, "P16", "Hot water circulation pump working mode", 0, 0), 
                                 (17, "P17", "Hot water circulating pump starting temperature difference", 1, 0), 
                                 (18, "P18", "Heating AU maximum temperature", 1, 0), 
                                 (19, "P19", "Heating AU offset temperature", 1, 0)],
                             4: [(20, "P20", "Air conditioner heating AU switch", 0, 0),
                                 (21, "P21", "Night run mode starting time", 0, 0),
                                 (22, "P22", "Night run mode stop time", 0, 0),
                                 (23, "P23", "Night run mode active option", 0, 0),
                                 (24, "P24", "Water pump working mode", 0, 0)],
                             5: [(25, "P25", "Water pump antifreeze time", 0, 0),
                                 (26, "P26", "Water pump speed regulation temperature difference", 1, 0),
                                 (27, "P27", "PWM water pump minimum speed", 0, 0),
                                 (28, "P28", "Ambient temperature of electric auxiliary heat start of air conditioner", 1, 0),
                                 (29, "P29", "Hot water and electric auxiliary heat start ambient temperature", 1, 0)],
                             6: [(30, "P30", "Electric heating stop offset temperature", 1, 0),
                                 (31, "P31", "E2 connection port function definition", 0, 0),
                                 (32, "P32", "Second heat source starting temperature", 1, 0),
                                 (33, "P33", "Air conditioner antifreeze temperature", 1, 0),
                                 (34, "P34", "defrosting method", 0, 0)],
                             7: [(35, "P35", "Defrost start temperature", 1, 0),
                                 (36, "P36", "Defrost Interval Multiplier", 0, 0),
                                 (37, "P37", "First defrost interval", 0, 0),
                                 (38, "P38", "Compressor defrost frequency", 0, 0),
                                 (39, "P39", "Defrost exit temperature", 1, 0)],
                             8: [(40, "P40", "Maximum defrost time", 0, 0),
                                 (41, "P41", "defrost mode 2 temp difference", 0, 0),
                                 (42, "P42", "defrost mode 2 pressure difference", 0.01, 0),
                                 (43, "P43", "EC fan maximum speed", 0, 0),
                                 (44, "P44", "Heating fan speed regulation temperature difference", 0, 0)],
                             9: [(45, "P45", "Cooling fan speed regulation temperature difference", 0, 0),
                                 (46, "P46", "EC fan speed control", 0, 0),
                                 (47, "P47", "EC fan manual speed", 0, 0),
                                 (48, "P48", "Inverter compressor model setting", 0, 0),
                                 (49, "P49", "Operating the set frequency function", 0, 0)],
                             10: [(50, "P50", "Debug fixed operating frequency", 0, 0),
                                  (51, "P51", "Compressor frequency limiting current", 0.1, 0),
                                  (52, "P52", "Compressor down frequency current", 0.1, 0),
                                  (53, "P53", "Compressor shutdown current", 0.1, 0),
                                  (54, "P54", "Compressor maximum frequency", 0, 0)],
                             11: [(55, "P55", "Compressor minimum frequency", 0, 0),
                                  (56, "P56", "Air conditioner water flow switch type selection", 0, 0),
                                  (57, "P57", "Air conditioner minimum water flow", 0, 0),
                                  (58, "P58", "Air conditioning function selection", 0, 0),
                                  (59, "P59", "Water source air cooling option", 0, 0)],
                             12: [(60, "P60", "Power-down recovery function bit", 0, 0),
                                  (61, "P61", "Main valve control mode", 0, 0),
                                  (62, "P62", "Main valve initial opening (manual opening adjustment) heating", 0, 0),
                                  (63, "P63", "Main valve initial opening (manual opening adjustment) cooling", 0, 0),
                                  (64, "P64", "Main valve superheat (heating)", 0, 0)],
                             13: [(65, "P65", "Main valve superheat (cooling)", 0, 0),
                                  (66, "P66", "Enthalpy injection valve control mode", 0, 0),
                                  (67, "P67", "Initial opening of enthalpy injection valve (manual opening adjustment) for heating", 0, 0),
                                  (68, "P68", "Enthalpy injection valve opening exhaust temperature (heating)", 1, 0),
                                  (69, "P69", "Enthalpy injection valve opening exhaust temperature (cooling)", 1, 0)],
                             14: [(70, "P70", "Enthalpy injection valve closing valve exhaust temperature hysteresis", 1, 0),
                                  (71, "P71", "Enthalpy injection valve closed valve ambient temperature hysteresis", 1, 0),
                                  (72, "P72", "Enthalpy injection valve opening ambient temperature (heating)", 1, 0),
                                  (73, "P73", "Enthalpy injection valve opening ambient temperature (cooling)", 1, 0),
                                  (74, "P74", "Pressure sensor enable bit", 0, 0)],
                             15: [(75, "P75", "Air conditioning mode frequency limit pressure", 0.1, 0),
                                  (76, "P76", "Air-conditioning mode cancels frequency limit pressure", 0.1, 0),
                                  (77, "P77", "Hot water mode frequency limiting pressure", 0.1, 0),
                                  (78, "P78", "Hot water mode cancels frequency limit pressure", 0.1, 0),
                                  (79, "P79", "High pressure protection setting value", 0.1, 0)],
                             16: [(80, "P80", "Low pressuree protection set point", 0.01, 0),
                                  (81, "P81", "High pressure protection release hysteresis", 0.01, 0),
                                  (82, "P82", "Low pressure protection release hysteresis", 0.01, 0),
                                  (83, "P83", "Electric heating control mode", 0, 0)],
                                  # 84 not used
                             17: [(85, "P84", "Reporting frequency", 0, 0),
                                  (86, "P85", "Reset", 0, 0),
#                                  (87, "P86", "User password setting", 0, 0),
#                                  (88, "P87", "Administrator password setting", 0, 0),
                                  (89, "P88", "Chassis heating start ambient temperature", 1, 0)],
                             18: [(90, "P89", "hot water coil", 0, 0)],
                                 }

class MeasValuesReader(ReaderBase):
    def __init__(self, client):
        super().__init__(client, "MeasValues")
        self.data_filename = "MeasValues.csv"
        self.readout_dict = {40: [(200, "C00", "External coil temperature", 0.5, 0), 
                                  (201, "C01", "Exhaust gas temperature", 0.5, 0), 
                                  (202, "C02", "Ambient temperature", 0.5, 0), 
                                  (203, "C03", "Return gas temperature", 0.5, 0), 
                                  (204, "C04", "EVI inlet temperature", 0.5, 0)],
                             41: [(205, "C05", "EVI outlet temperature", 0.5, 0), 
                                  (206, "C06", "Internal coil temperature", 0.5, 0), 
                                  (207, "C07", "Inlet temperature", 0.5, 0),
                                  (208, "C08", "water temperature", 0.5, 0), 
                                  (209, "C09", "domestic hot water temperature", 0.5, 0)],
                             42: [(210, "C10", "hot water pipe temperature", 0.5, 0), 
                                  (211, "C11", "Room temperature", 0.5, 0), 
                                  (212, "C12", "Solar temperature", 0.5, 0), 
                                  (213, "C13", "Outer water flow rate", 0, 0), 
                                  (214, "C14", "Inner water flow rate", 0, 0) ],
                             43: [(215, "C15", "Actual overheat degree of main expansion valve", 0.5, 0), 
                                  (216, "C16", "Actual overheat degree of injection enthalpy valve", 0.5, 0), 
                                  (217, "C17", "high pressure", 0,1, 0), 
                                  (218, "C18", "low pressure", 0.1, 0), 
                                  (219, "C19", "High pressure switch status", 0, 0)],
                             44: [(220, "C20", "Low pressure switch status", 0, 0),
                                  (221, "C21", "Temperature control switch status", 0, 0),
                                  (222, "C22", "Internal water flow switch status", 0, 0),
                                  (223, "C23", "Outer water flow switch status", 0, 0),
                                  (224, "C24", "Cooling switch status", 0, 0)],
                             45: [(225, "C25", "Heating switch status", 0, 0),
                                  (226, "C26", "Phase sequence state", 0, 0),
                                  (227, "C27", "defrost state", 0, 0),
                                  (228, "C28", "Sterilize state", 0, 0),
                                  (229, "C29", "Antifreeze state", 0, 0)],
                             46: [(230, "C30", "compressor", 0, 0),
                                  (231, "C31", "outdoor fan1", 0, 0),
                                  (232, "C32", "outdoor fan2", 0, 0),
                                  (233, "C33", "water pump1 state", 0, 0),
                                  (234, "C34", "water pump2 state", 0, 0)],
                             47: [(235, "C35", "water pump3 state", 0, 0),
                                  (236, "C36", "water pump4 state", 0, 0),
                                  (237, "C37", "water pump5 state", 0, 0),
                                  (238, "C38", "bypass valve", 0, 0),
                                  (239, "C39", "EVI electromagnetic valve", 0, 0)],
                             48: [(240, "C40", "Four-way valve status", 0, 0),
                                  (241, "C41", "Air conditioner electric heating status", 0, 0),
                                  (242, "C42", "Domestic hot water electric heating status", 0, 0),
                                  (243, "C43", "Crankshaft heater status", 0, 0),
                                  (244, "C44", "Three-way valve 1 state", 0, 0)],
                             49: [(245, "C45", "Three-way valve 2 state", 0, 0),
                                  (246, "C46", "Three-way valve 3 state", 0, 0),
                                  (247, "C47", "Main expansion valve opening", 0, 0),
                                  (248, "C48", "Enthalpy injection expansion valve opening", 0, 0),
                                  (249, "C49", "Compressor start and stop times", 0, 0)],
                             50: [(250, "C50", "Compressor running time", 0, 0),
                                  (251, "C51", "Current working mode", 0, 0),
                                  (252, "C52", "Total defrosting times", 0, 0),
                                  (253, "C53", "Compressor target frequency", 0, 0),
                                  (254, "C54", "Compressor input current", 0.1, 0)],
                             51: [(255, "C55", "Outdoor unit module temp.", 0.5, 0),
                                  (256, "C56", "Inverter running code1", 0, 0),
                                  (257, "C57", "Inverter running code2", 0, 0),
                                  (258, "C58", "Inverter running code3", 0, 0),
                                  (259, "C59", "Compressor Error Codes", 0, 0)],
                             52: [(260, "C60", "IPM fan", 0, 0),
                                  (261, "C61", "Tc", 0, 0),
                                  (262, "C62", "Ts", 0, 0),
                                  (263, "C63", "P", 0, 0),
                                  (264, "C64", "Main board program version", 0, 0)],
                             53: [(265, "C65", "Driver module program version", 0, 0),
                                  (266, "C66", "Chassis Electric Heating Status", 0, 0)]
                            }

class ReaderMain():
    def __init__(self, output_path=os.getcwd(), com_port="COM2"):
        self.output_path = output_path 
        try:
            logger.info(f"connect to NuLite heatpump via com port {com_port}")
            self.client = ModbusClient(method='rtu', port=com_port, baudrate=9600, parity='N', timeout=0.1)
            self.connection = self.client.connect()
        except Exception as _e:
            logger.error(f"{_e}")
        self.workers = [ParameterReader(self.client), MeasValuesReader(self.client)]

    def Process(self):
        logger.info("start reading data")
        for item in self.workers:
            item.read()
            #print(item.data)
            item.writeDataToFile(self.output_path)
        
        logger.info("reading finished")

def main():
    parser = argparse.ArgumentParser(
        description="Read out all the Parameters and meas values via modus RTU, of NuLite Flamingo HeatPump"
    )
    parser.add_argument("-o"
        "--output",
        dest="output",
        type=str,
        help="Path to the output folder"
    )
    parser.add_argument(
        "-c"
        "--com",
        dest="com",
        default="COM2",
        type=str,
        help="Serial Com port that should be used"
    )

    # Parse the command-line arguments
    args = parser.parse_args()
    
    if args.output is not None and os.path.isdir(args.output):
        if args.com is not None:
            MyReaderMain = ReaderMain(args.output, args.com)
            MyReaderMain.Process()
    else:
        logger.error(f"output folder {args.output} does not exist")

if __name__ == "__main__":
    main()
    sys.exit()