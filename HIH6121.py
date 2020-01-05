''' HIH6121 Driver
AditNW, May 2019
'''

import smbus
import time


class HIH6121sensor(object):
    def __init__(self):
        # Get I2C bus
        self.bus = smbus.SMBus(1)

    def returnTempRH(self):
        '''returns data from HIH6121
        '''
        self.bus.write_quick(0x27)
        time.sleep(0.1)

        # HIH6130 address, 0x27(39)
        # Read data back from 0x00(00), 4 bytes
        # humidity MSB, humidity LSB, temp MSB, temp LSB
        data = self.bus.read_i2c_block_data(0x27, 0x00, 4)

        # Convert the data to 14-bits
        humidity = ((((data[0] & 0x3F) * 256) + data[1]) * 100.0) / 16383.0
        temp = (((data[2] & 0xFF) * 256) + (data[3] & 0xFC)) / 4
        cTemp = (temp / 16384.0) * 165.0 - 40.0
        fTemp = cTemp * 1.8 + 32

        # added due to OSErrors
        time.sleep(0.1)

        return humidity, cTemp, fTemp


if __name__ == '__main__':
    print('test HIH6121')
    app = HIH6121sensor()
    i = 1
    while i < 5:
        humidity, cTemp, fTemp = app.returnTempRH()
        # Output data to screen
        print('Relative Humidity :', '{:.2f}'.format(humidity), '%')
        print('Temperature in Celsius :', '{:.2f}'.format(cTemp), 'C')
        print('Temperature in Fahrenheit :', '{:.2f}'.format(fTemp), 'F')
        time.sleep(1)