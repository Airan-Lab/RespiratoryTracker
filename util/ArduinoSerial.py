import serial
import serial.tools.list_ports as list_ports
import numpy as np

class ArduinoSerial():
    def __init__(self,baud=9600,timeout=1):
        self.baud = baud
        self.timeout = timeout

        self.ports_avail = list_ports.comports()
        self.port = None

        self.streaming = False

    def update_ports(self):
        self.ports_avail = list_ports.comports()
        return self.ports_avail

    def connect(self,port_name):
        if self.port is not None and self.port.is_open:
            self.disconnect()
        self.port = serial.Serial(port_name,baudrate=self.baud,timeout=self.timeout)
        response = b'asdf'        
        while response[0:2] != b'Hi':
            self.port.write(b'h')
            response = self.port.readline()

    def disconnect(self):
        if self.port is not None and self.port.is_open:
            self.port.close()
            self.port = None

    def start(self):
        if self.port is not None and self.port.is_open:
            self.port.write(b'y')
            self.streaming = True

    def stop(self):
        if self.streaming:
            self.port.write(b'n')
            self.streaming = False
