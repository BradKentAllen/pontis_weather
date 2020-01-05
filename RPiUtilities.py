#! /usr/bin/env python
# -*- coding: utf-8 -*-
# RPiUtilities.py
# Rev 0
"""RPiUtilities is for use with all RPi programs
"""

import os

# Rev 0 - transferred from config tested with weather.py 3.5

#### RPI UTILITIES ####


def setRTC(year, month, date, hour, minute):
    # create and send time change to RTC
    timeEnter = 'sudo hwclock --set --date="' + str(year) + '-' + str(month)\
    + '-' + str(date) + ' ' + str(hour) + ':' + str(minute) + ':00"'
    #os.system('sudo hwclock --set --date="2011-08-14 16:45:05"')
    print('config input reset clock')
    print(timeEnter)
    os.system(timeEnter)

    # set RPI clock to RTC time (that was just set)
    os.system('sudo hwclock -s')
    print('set to: ', timeEnter)


def shutdownRPI():
    print('RPiUtilities shutdownRPI')
    os.system("sudo shutdown -h now")


def rebootRPI():
    os.system("sudo reboot")


def ejectUSB(usbPath):
    os.system('sudo umount ' + usbPath)
    print('usb ejected')


def copySW(usbPath):
    os.system('sudo cp -r ' + usbPath + '/weatherUPDATE/. /home/pi/WEATHER/')
    print('copy WEATHER directory: ')
    print('sudo cp -r ' + usbPath + '/weatherUPDATE/. /home/pi/WEATHER/')


def findUSB():
    '''searches rpi for usb mounted by application: usbmount
    '''
    driveFound = 0
    # search the 7 usb directories for the thumb drive
    for i in ('0', '1', '2', '3', '4', '5', '6', '7'):
        usbPath = '/media/usb' + i
        # get a list of files in that directory, empty if no usb
        fileList = os.listdir(path=usbPath)
        if fileList != []:
            print('found usb drive on usb', i)
            # umount if more than one directory has a drive mounted
            if driveFound == 1:
                print('eject drive on usb', i)
                ejectUSB(usbPath)
            else:
                driveFound = 1
                return usbPath
    print('dir used is ', usbPath)

