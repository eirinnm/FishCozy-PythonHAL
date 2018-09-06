''' 
Hardware Abstraction Layer for the FishCozy.
This module provides a wrapper/interface around the serial communication with the arduino.

Create a Mainboard instance, call connect(), and then regularly call refresh(). 
The Mainboard instance has a member, chambers, which is a list of Chamber objects.
Each Chamber object has temperature, power and setpoint variables. 
Changing a chamber's setpoint will send the appropriate serial string.
'''
import serial
import serial.tools.list_ports
import warnings
import sys
import os
import random
import time

class Chamber:
    def __init__(self, board, idx):
        self._board = board
        self._idx = idx
        self.temperature = 25
        self._setpoint = 28
        self.power = 0
        self.error = False

    def __repr__(self):
        return "%0.2f %0.2f %d" % (self.temperature, self.setpoint, self.power)
    
    @property
    def setpoint(self):
        return self._setpoint

    @setpoint.setter
    def setpoint(self, value):
        self._setpoint = value
        self._board._setchamber(self._idx, self._setpoint)  # Call the board function to send the command

    def update_from_string(self, text):
        temp, setpoint, power = text.split()
        self.temperature = float(temp)
        self._setpoint = float(setpoint)
        self.power = float(power)

    def mock(self):  # simulate some data
        # move a small fraction of the distance to the setpoint
        distance_to_setpoint = self.setpoint - self.temperature 
        self.temperature += distance_to_setpoint * 0.01
        if abs(distance_to_setpoint)>=1:
            self.power = distance_to_setpoint * 50
            self.power = min(max(self.power, -255),255)
        else:
            self.power = 0    
        # add some noise
        self.temperature += random.gauss(0, 0.05)


class ReadLine:  # found here https://github.com/pyserial/pyserial/issues/216
    def __init__(self, s):
        self.buf = bytearray()
        self.s = s

    def readline(self): 
        i = self.buf.find(b"\n")
        if i >= 0:
            r = self.buf[:i+1]
            self.buf = self.buf[i+1:]
            return r
        while True:
            i = max(1, min(2048, self.s.in_waiting))
            data = self.s.read(i)
            if not data:
                raise TimeoutError
            i = data.find(b"\n")
            if i >= 0:
                r = self.buf + data[:i+1]
                self.buf[0:] = data[i+1:]
                return r
            else:
                self.buf.extend(data)


class Mainboard:  ## Main class to be instantiated by the user
    def __init__(self, port=None, num_chambers=6):
        ''' If port is None, it will be auto selected as the highest-numbered port.
        If port is False, a simulation will run instead '''
        # Create the chamber objects
        self.chambers = [Chamber(self, i) for i in range(num_chambers)]
        if port is None:
            ports = [comport.device for comport in serial.tools.list_ports.comports()]
            if ports:
                port = ports[-1]
            else:
                port = False    
                warnings.warn('No serial port detected: entering hardware simulation')
        self.port = port

    def _setchamber(self, idx, value):
        ## Send the string to update a chamber's setpoint
        print("Setting chamber", idx, "to", value)
        if self.ser:
            self.ser.write(('S %s %0.2f\n' % (idx, value)).encode())

    def connect(self):
        if self.port:
            self.ser = serial.Serial(self.port, 115200, timeout=1)
        else:
            self.ser = None 


    def disconnect(self):
        if self.ser:
            self.ser.close()
   
    def refresh(self):
        if self.ser:
            reader = ReadLine(self.ser)
            errorcount = 0
            while errorcount < 3:
                try:
                    line = reader.readline().decode(encoding='ascii').strip()
                    if line.startswith("Command"):
                        print(line)
                    else:
                        chamber_parts = line.split('\t')
                        if len(chamber_parts) == len(self.chambers):
                            for chamber, text in zip(self.chambers, chamber_parts):
                                chamber.update_from_string(text)
                            break
                        else:
                            errorcount += 1
                            print("Unable to read line: '%s'" % line)
                except UnicodeDecodeError:
                    errorcount += 1
            else:
                print("Unable to read line: '%s'" % line)
        else: ## Mocking when there's no connection
            for chamber in self.chambers:
                chamber.mock()
            time.sleep(0.025)


if __name__ == '__main__':
    try:
        board = Mainboard(None, 6)
        board.connect()
        while True:
            board.refresh()
            print(board.chambers)
    except KeyboardInterrupt:
        print('Interrupted, closing connection')
        board.disconnect()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
