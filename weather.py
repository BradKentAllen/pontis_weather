#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# weather.py
# A.1.0

'''weather script for Pontis Weather Station
'''

# Rev A.1.0 - Field test release 10/10/19

import time
from datetime import datetime
import RPi.GPIO as GPIO
import math
import random

# files required in folder
import I2C_LCD_driver3
import tsl2591
import HIH6121
import RPiUtilities
import config
import EnglishSpanish


class stationData():
    '''class container for data used throughout system and recorded
    note: variables only used within timing, not recorded, are part of the weatherStation
        class not the stationData

    sensorError{TempError, RHError, LuxError}
    periodWeatherVariables{tempCurrent, RHCurrent, windAvrPeriod, windGust, windCurrent, windList, solarLux}
    '''
    def __init__(self):
        self.clearSensorError()

    def clearSensorError(self):
        self.sensorError = {
            'TempError': '',
            'RHError': '',
            'LuxError': ''
            }
        self.sensorOrder = ('TempError', 'RHError', 'LuxError')

    def resetPeriodVariables(self):
        ''' sets the period variables list
        note: period is time for recording weatherData and designated in timing
        note: although rainTotal is recorded every period, it is cleared daily so 
        is part of dayWeatherVariables[]
        '''
        tempCurrent = 0
        RHCurrent = 0
        windAvrPeriod = 0
        windGust = 0
        windCurrent = 0
        solarLux = 0
        
        self.periodWeatherVariables = {
            'tempCurrent': tempCurrent,
            'RHCurrent': RHCurrent,
            'windAvrPeriod': windAvrPeriod,
            'windGust': windGust, 
            'windCurrent': windCurrent,
            'solarLux': solarLux
            }

        self.periodOrder = ('tempCurrent', 'RHCurrent', 'rainTotalDay', 'windAvrPeriod', 'windGust', 'solarLux')
        self.periodLabels = ('Temp', 'RH', 'Rain total (mm)', 'Wind avr', 'Wind gust', 'Solar', 'Water loss (mm)', 'Cum loss (mm)')

    def printPeriodVariables(self):
        print('periodVariables: ', end='')
        for datum in self.periodOrder:
            if datum == 'rainTotalDay':
                print('{:.2f}'.format(self.dayWeatherVariables['rainTotalDay']), ' / ', end='')
            else:
                print('{:.2f}'.format(self.periodWeatherVariables[datum]), ' / ', end='')

        print('')


    def resetDayVariables(self, forceDefaults, ignoreSomeDefaults, ignoreSomeBackups):
        '''checks SD card for backup file, uses, or sets defaults
        - forceDefaults is used at midnight to clear variables, it precludes using the backup file values
        - ignoreSomeDefaults allows some variables to stay when others are cleared
        - ignoreSomeBackups is not currently used
        '''
        useDefaults = True

        # check SD for weatherDataBackup
        filePathName = config.SDFilePath + '/' + 'weatherDataBackup'
        try:
            with open(filePathName, newline='') as file:
                # read full file
                fileText = file.read()
                # split into lines
                lines = fileText.split('\n')
                # import backupData as a string
                backupData = lines[0]
                if len(backupData) < 12 or backupData.isspace() == True:
                    useDefaults = True
                else:
                    # check if backupData is from today
                    today = datetime.now().strftime('%Y-%m-%d')
                    backupDate = backupData[:10]
                    print(today, ' / ', backupDate)
                    if backupDate == today:
                        useDefaults = False
        except FileNotFoundError:
            useDefaults = True 

        if forceDefaults is True:
            useDefaults = True

        if useDefaults is True:
            print('useDefaults')
            # assign default values
            tempMax = 0
            tempMin = 100
            RHMax = 0
            RHMin = 100
            rainTotalDay = 0
            windAvrMax = 0
            windAvrMin = 100
            windGustMax = 0
            solarTotalDay = 0
            if ignoreSomeDefaults is False:
                self.waterLossCumulative = 0
            
        else:
            print('use backupData')
            # clip the date and time off backup data and convert to list of data
            backupDataList = backupData[17:].split(',')
            #use data from backup
            tempMax = int(backupDataList[0])
            if(tempMax > 100 or tempMax < -32): tempMax = 0

            tempMin = int(backupDataList[1])
            if(tempMin > 100 or tempMin < -32): tempMin = 100

            RHMax = int(backupDataList[2])
            if(RHMax > 100 or RHMax < 0): RHMax = 0

            RHMin = int(backupDataList[3])
            if(RHMin > 100 or RHMin < 0): RHMin = 100

            rainTotalDay = float(backupDataList[4])
            if(rainTotalDay > 100 or rainTotalDay < 0): rainTotalDay = 0

            windAvrMax = int(backupDataList[5])
            if(windAvrMax > 200 or windAvrMax < 0): windAvrMax = 0

            windAvrMin = int(backupDataList[6])
            if(windAvrMin > 200 or windAvrMin < 0): windAvrMin = 100

            windGustMax = int(backupDataList[7])
            if(windGustMax > 200 or windGustMax < 0): windGustMax = 0

            solarTotalDay = float(backupDataList[8])
            if(solarTotalDay > 100000 or solarTotalDay < 0): solarTotalDay = 0

            if ignoreSomeBackups is False:
                self.waterLossCumulative = float(backupDataList[9])
            if(self.waterLossCumulative > 1000 or self.waterLossCumulative < 0): self.waterLossCumulative = 0

        self.dayWeatherVariables = {
            'tempMax': tempMax,
            'tempMin': tempMin,
            'RHMax': RHMax,
            'RHMin': RHMin,
            'rainTotalDay': rainTotalDay,
            'windAvrMax': windAvrMax,
            'windAvrMin': windAvrMin, 
            'windGustMax': windGustMax, 
            'solarTotalDay': solarTotalDay
            }  

        self.dayOrder = ('tempMax', 'tempMin', 'RHMax', 'RHMin', 'rainTotalDay', 'windAvrMax', 'windAvrMin', 'windGustMax', 'solarTotalDay')
        self.dayLabels = ('Temp max', 'Temp min', 'RH max', 'RH min', 'Rain total', 'Wind max', 'Wind min', 'Wind gust', 'Solar total')

    def writeDataBackupSD(self):
        ''' write weather backup file (one line)
        '''
        filePathName = config.SDFilePath + '/' + 'weatherDataBackup'
        with open(filePathName, 'w') as file:
            dateTimeNow = '{:%Y-%m-%d:%_H:%M}'.format(datetime.now())
            file.write(dateTimeNow + ',')
            # write data from dayWeatherVariables
            for datum in self.dayOrder:
                file.write(str('{:.0f}'.format(self.dayWeatherVariables[datum])) + ',')
            file.write(str('{:.3f}'.format(self.waterLossCumulative)))
            file.write('\n')


class weatherStation():
    def __init__(self):
        '''set up initial parameters and sensors
        '''

        self.debugON = True
        self.debug2ON = config.debug2

        #### SET KEY OPERATING PARAMETERS ####
        self.historyFileName = config.historyFileName
        self.dataFileName = config.dataFileName

        self.comment = ''

        #### UI - Display, LED, BUTTONS  ####
        # initialize rpi gpio
        GPIO.setmode(GPIO.BOARD)
        self.powerLEDpin = 8
        self.powerOFFinputpin = 10
        self.powerOFFholdpin = 12

        # Green pulse LED on Jim Hawkins board
        GPIO.setup(self.powerLEDpin, GPIO.OUT, initial=GPIO.LOW)


        # buttonState: 0 is no button pressed, 99 is any button when backlight is off, (1-3) button pressed
        self.buttonState = 0

        # buttonAction indicates whether the requested action is complete (1) or yet to be completed (0)
        self.buttonAction = 0

        # buttons
        self.pinButton1 = 33
        self.pinButton2 = 31
        self.pinButton3 = 29
        GPIO.setup([self.pinButton1, self.pinButton2, self.pinButton3], GPIO.IN)

        # debounce time in milliseconds
        self.buttonDebounce = 300

        #### INTERRUPTS - BUTTONS ####
        GPIO.add_event_detect(self.pinButton1, GPIO.RISING, bouncetime=self.buttonDebounce, callback=self.reactToButton)
        GPIO.add_event_detect(self.pinButton2, GPIO.RISING, bouncetime=self.buttonDebounce, callback=self.reactToButton)
        GPIO.add_event_detect(self.pinButton3, GPIO.RISING, bouncetime=self.buttonDebounce, callback=self.reactToButton)


        # backlight timer (backlightOFFTime is also used for screen time outs)
        self.backlightTimer = 0
        self.backlightOffTime = config.backlightOffTime


        # LCD
        self.pollingDelay = .100  # this delays the polling of constant functions
        self.restartLCD()

        #### START ROUTINES ####
        self.usbPath = RPiUtilities.findUSB()
        # check for no USB then error
        if self.usbPath is None:
            self.comment = self.comment + 'USB/'
            self.mylcd.lcd_display_string('No USB Drive!', 1, 0)
            self.mylcd.lcd_display_string('replace USB', 2, 2)
            self.mylcd.lcd_display_string('and Reboot', 3, 0)
            time.sleep(5)
            self.MXscreenSelect(8)   # goes to MX screen then to reboot

        if self.debugON == True: print('usbPath: ', self.usbPath)

        # Display start screen to use initialization time
        self.startScreen(config.updateFilePath)

        #### WEATHER VARIABLES ####
        data.resetPeriodVariables()
        data.resetDayVariables(False, False, False)
        self.comment = '/'

        # windAvrCount used to calculate windAvr
        self.windAvrCount = 0


        #### START SENSORS
        data.clearSensorError()

        # TSL2561 light sensor
        try:
            self.lightSensor = tsl2591.Tsl2591()
        except OSError:
            if self.debugON == True: print('no light sensor detected')
            self.lightSensor = 0
            data.updateLuxError('no Solar/')

        # HIH6121 temp and humidity
        self.tempSensor = HIH6121.HIH6121sensor()
        self.readTempRH()

        if self.debugON == True: print('data.sensorError: ', data.sensorError.values())

        if data.sensorError['TempError'] == '' and\
                data.sensorError['RHError'] ==  '' and\
                data.sensorError['LuxError'] == '':
            if self.debugON == True: print('no errors at startup')
            self.mylcd.lcd_display_string(EnglishSpanish.getWord('no errors'), 3, 0)
        else:
            self.comment = self.comment + data.sensorError['TempError']\
                + data.sensorError['RHError'] + data.sensorError['LuxError']

        # Battery Low Power Monitor (Captain Smollett)
        self.lowBattery = 0
        GPIO.setup(self.powerOFFinputpin, GPIO.IN)
        GPIO.setup(self.powerOFFholdpin, GPIO.OUT)
        GPIO.output(self.powerOFFholdpin, GPIO.HIGH) #latch power on


        #### INTERRUPTS - SENSORS ####
        # anemometer
        self.windCounter = 0
        GPIO.setup(18, GPIO.IN)
        GPIO.add_event_detect(18, GPIO.RISING, bouncetime=self.buttonDebounce, callback=self.windCount)

        self.rainCounter = 0
        self.rainThisPeriod = 0
        GPIO.setup(16, GPIO.IN)
        GPIO.add_event_detect(16, GPIO.RISING, bouncetime=self.buttonDebounce, callback=self.rainCount)

        #### Set Up Data Files ####
        self.initializeDataFiles()

        #### START SCREEN ERROR DISPLAY ####
        if self.comment != '/':
            self.mylcd.lcd_display_string(self.comment, 3, 0)

        # Animation for 8 second delay
        self.runFunGrowAnimation(1, 8, 6, 4)
        time.sleep(4)
        

        # Clear comments, sensor errors will re-add during a read
        self.comment = 'power up/'

        if self.usbPath is None:
            self.systemError('NO USB or Ejected', 'Re-Insert USB')

        # LCD - first mainscreen
        self.readTempRH()
        self.mylcd.lcd_clear()
        self.mainScreen()
        
        self.mainScreenRefresh()

        # DEV reset anenometer just before timer
        self.windCounter = 0

        if self.debugON == True:
            data.printPeriodVariables()


    #### TIMER FUNCTIONS ####
    def runTimer(self):
        '''main operating loop for weather station
        '''
        # set timer variables
        lastSecond = 0
        lastFloatSecond = 0
        lastMinute = 0
        yesterday = datetime.now().strftime('%Y-%m-%d')

        self.readTempRH()
        self.readSolar()

        runWeather = True
        while runWeather is True:
            #### CONTINUOUS POLLING ####
            # too fast of polling causes LCD problems, so this sets the timing         
            thisSecond = float(datetime.now().strftime('%S.%f'))
            thisMinute = int(datetime.now().strftime('%M'))
            today = datetime.now().strftime('%Y-%m-%d')

            if lastFloatSecond + self.pollingDelay >= 60:
                lastFloatSecond = 0

            #### PACED POLLING ####
            if thisSecond > lastFloatSecond + self.pollingDelay:
                if self.debug2ON == True: print(datetime.now().strftime('%H:%M:%S.%f'))
                # index the timer
                lastFloatSecond = thisSecond

                # check and react to buttonState
                if self.buttonState != 0 and self.buttonAction == 0:
                    if self.buttonState == 1:
                        self.buttonAction = 1
                        # take action
                        self.rainScreen()
                        self.irrigation()
                        self.Iirrigated()

                        # refresh LCD
                        self.mylcd.lcd_clear()
                        self.mainScreen()
                        self.clockRefresh()
                        self.mainScreenRefresh()

                        # set for polling
                        lastFloatSecond = float(datetime.now().strftime('%S.%f'))

                    elif self.buttonState == 2:
                        self.buttonAction = 1
                        
                        # take action
                        self.MXscreenSelect(0)

                        # refresh LCD
                        self.mylcd.lcd_clear()
                        self.mainScreen()
                        self.clockRefresh()
                        self.mainScreenRefresh()

                        # set for polling
                        lastFloatSecond = float(datetime.now().strftime('%S.%f'))

                    elif self.buttonState == 3:
                        self.buttonAction = 1
                        pass

                    elif self.buttonState == 99:
                        self.backlightON()

                    else:
                        pass

                # Require buttons to be released before next press
                self.buttonCheckRelease()

                if self.debug2ON == True: print('before Every Second')

                #### EVERY SECOND ACTIONS ####
                thisSecond = int(thisSecond)
                if thisSecond != lastSecond:
                    # flash the pulse green LED on JH board, all of the time)
                    if thisSecond % 2 == 0:
                        GPIO.output(self.powerLEDpin, GPIO.LOW)
                    else:
                        GPIO.output(self.powerLEDpin, GPIO.HIGH)


                    if self.debug2ON == True: print('after pulse')

                    # turn backlight off (1 indicates ON)
                    if self.backlightTimer < self.backlightOffTime:
                        # Display actions
                        self.backlightTimer += 1
                        # flash the pulse (on LCD)
                        if thisSecond % 2 == 0:
                            # self.mylcd.lcd_display_string('*', 1, 19)
                            self.mylcd.lcd_display_string('', 1, 19)
                            self.mylcd.lcd_write_char(self.custom['flower'])
                        else:
                            self.mylcd.lcd_display_string(' ', 1, 19)
                        
                    elif self.backlightTimer == self.backlightOffTime:
                        self.mylcd.backlight(0)
                        self.backlightTimer += 1
                    else:
                        pass

                    if self.debug2ON == True: print('end every second')

                    #### EVERY 5 SECONDS ####
                    if thisSecond % 5 == 0 or thisSecond == 0:
                        self.readWind(5)
                        self.readSolar()

                        if self.debug2ON == True: print('every 5 second')

                        # rain total counts (resets rainCounter)
                        workingRainIncrement = (self.rainCounter * config.rainGageVolume)
                        data.dayWeatherVariables['rainTotalDay'] = data.dayWeatherVariables['rainTotalDay'] + workingRainIncrement
                        self.rainThisPeriod = self.rainThisPeriod + workingRainIncrement
                        self.rainCounter = 0

                        # Total solar for the day (kilojoules)
                        if data.sensorError['LuxError'] != 'no Solar/':
                            solarEnergyK = (config.luminousEff * data.periodWeatherVariables['solarLux'] * 5) / 1000
                            data.dayWeatherVariables['solarTotalDay'] = data.dayWeatherVariables['solarTotalDay'] + solarEnergyK

                        # Display actions
                        if self.backlightTimer < self.backlightOffTime:
                            self.mainScreen()
                            self.mainScreenRefresh()

                        # Low Battery check
                        if(GPIO.input(10) == False):
                            if self.debugON == True: print('low battery ',self.lowBattery)
                            self.lowBattery = self.lowBattery + 1
                            self.batteryCheck()

                        if self.debug2ON == True: print('end every 5 second')


                    #### EVERY 30 SECONDS ####
                    if thisSecond == 30 or thisSecond == 0:
                        if self.debug2ON == True: print('every 30 second')
                        self.readTempRH()

                    lastSecond = thisSecond
                    if self.debug2ON == True: print('end full every second')

                #### MINUTE ACTIONS ####
                if thisMinute != lastMinute:
                    #### 30 MINUTE ACTIONS ####
                    if self.debug2ON == True: print('every minute')
                    if thisMinute % 30 == 0 or thisMinute == 0:
                        ## reset lowBattery (this makes it have to go over 3 within 30 minutes)
                        self.lowBattery = 0
                    if self.debug2ON == True: print('end every minute')

                    #### ON THE HOUR ACTIONS ####
                    if thisMinute == 0:
                        if self.debug2ON == True: print('every hour')
                        if self.debugON == True: print('record weatherData at ', '{:%_H:%M}'.format(datetime.now()))
                        if self.debugON == True:
                            data.printPeriodVariables()
                            print('rainThisPeriod: ', self.rainThisPeriod)

                        #####################################################
                        #### PERFORM PERIOD ACTIONS #########################
                        #####################################################
                        if self.debug2ON == True: print('period actions')
                        # use Penman-Monteith to calculate water loss during this period
                        workingPrintFactor = False
                        if self.debugON == True:
                            workingPrintFactor = True      

                        waterLoss = self.penmanMonteith(
                            data.periodWeatherVariables['tempCurrent'],
                            data.periodWeatherVariables['RHCurrent'],
                            data.periodWeatherVariables['windAvrPeriod'],
                            data.periodWeatherVariables['solarLux'],
                            workingPrintFactor)
                        # add this waterloss to the cumulative water loss
                        data.waterLossCumulative = data.waterLossCumulative + waterLoss

                        # subtract rain during this period from waterLoss
                        data.waterLossCumulative = data.waterLossCumulative - self.rainThisPeriod
                        self.rainThisPeriod = 0

                        # limit water loss to when soil is fully dry
                        if data.waterLossCumulative > config.maximumDry:
                            data.waterLossCumulative = config.maximumDry

                        # water loss can't be negative (soil can only be saturated)
                        if data.waterLossCumulative < config.maximumAbsorption:
                            data.waterLossCumulative = config.maximumAbsorption

                        if self.debugON == True: print('waterLoss: ', waterLoss, ' / ', data.waterLossCumulative)
                        # Record weather variables to weatherData
                        self.writePeriodDataLine(waterLoss)

                        ## Clear averaging variables
                        data.periodWeatherVariables['windAvrPeriod'] = 0
                        self.windAvrCount = 0
                        data.periodWeatherVariables['windGust'] = 0

                        if self.debug2ON == True: print('end period actions')

                        #### END PERIOD ACTIONS ####

                    lastMinute = thisMinute

                    #### MIDNIGHT ACTIONS ####
                    if today != yesterday:
                        if self.debug2ON == True: print('midnight actions')
                        self.writeDailySummary(yesterday)

                        data.resetDayVariables(True, True, True)

                        self.rainCounter = 0

                        yesterday = today


    ##############################################################
    ##############################################################


    #### WATER LOSS and IRRIGATION ####
    def penmanMonteith(self, hourTemp, hourRH, hourWindAvr, hourLux, printFactor):
        ''' Calculates mm water lost in 1 hour
        ONLY WORKS FOR 1 HOUR PERIOD
        '''
        if printFactor is True: print(hourTemp, 'deg C, ', hourRH, '% ', hourWindAvr, 'km/hr, ', hourLux, 'Lux')

        # Solar Radiation
        solarRadiation = hourLux * config.luminousEff * (3600/1e6) # (MJ/m^2-hr)

        outgoingRadiation = 0 # equation 39 but am assuming this is small
        netRadiation = ((1 - .23) * solarRadiation) -  outgoingRadiation # equation 38 gives the .23 constant
        if printFactor is True: print('netRadiation: ', '{:3.6f}'.format(netRadiation))

        #Ground Heat Flux
        if hourLux > 3000:
            soilHeatFlux = .1 * netRadiation  # Daytime Gn MJ/m^-hr
        else:
            soilHeatFlux = .5 * netRadiation  # Night Gn MJ/m^-hr

        #psychometric constant is .067 at sea level and .060 at 3000 feet in kPa/deg C
        psychometricConstant = .0665 # (kPa/deg C)

        # e sub zero(T)  saturation vapor pressure at air temp T
        saturationVaporPressure = .6108 * (math.exp((17.27 * hourTemp)/(hourTemp + 273))) # (kPa/deg C)


        # saturation slope vapor pressure at air temperature
        saturationVaporSlope = (4098 * saturationVaporPressure) / ((hourTemp +237.3)**2) # KPa/deg C

        vaporPressure = saturationVaporPressure * (hourRH/100) # e sub a kPa
        windSpeed = hourWindAvr * .278  # wind speed converted to m/sec

        # Penman Monteith Equation in three parts then the whole
        solarComponent = ((.408 * saturationVaporSlope) * (netRadiation - soilHeatFlux))
        if printFactor is True: print('solar component: ', '{:4.3f}'.format(solarComponent))

        windComponent = (psychometricConstant * (37 / (hourTemp + 273))) * windSpeed * (saturationVaporPressure - vaporPressure)
        if printFactor is True: print('wind component: ', '{:4.3f}'.format(windComponent))

        workingDenominator = saturationVaporSlope + (psychometricConstant * (1 + (.34 * windSpeed)))
        if printFactor is True: print('denominator: ', '{:4.3f}'.format(workingDenominator))
        if printFactor is True: print('')

        # final Penman-Monteith
        evapoTranspiration = (solarComponent + windComponent) / workingDenominator

        return evapoTranspiration  # mm of water lost in that one hour

    #### POWER MANAGEMENT ####
    def batteryCheck(self):
        '''uses Capt Smollett power management board
        - latches power on then shuts off when below low battery
        - Capt Smollett incorporates delay in power off
        '''
        if(self.lowBattery > 3):
            if self.debugON == True: print('low battery shutdown')
            self.mylcd.lcd_clear()
            self.mylcd.lcd_display_string(EnglishSpanish.getWord('Low Battery Shutdown'), 1, 0)
            #### Write last line of data including lowBattery comment
            self.comment = self.comment + 'LOW BATTERY SHUTDOWN/'
            self.writePeriodDataLine(0)
            time.sleep(5)
            GPIO.output(self.powerOFFholdpin, GPIO.LOW) #turn power off
            GPIO.cleanup()
            RPiUtilities.shutdownRPI()

    #### DATA FUNCTIONS ####
    def initializeDataFiles(self):
        '''check for files on SD card and USB, add new file if required
        '''
        # check USB for weatherHistory, create if not there
        try:
            filePathName = self.usbPath + '/' + self.historyFileName
            open(filePathName)
        except FileNotFoundError:
            try:
                with open(filePathName, 'w') as file:
                    file.write('DateTime' + ',')
                    for label in data.dayLabels:
                        file.write(label + ',')
                    #file.write('DateTime,Temp max,Temp min,RH max,RH min,Rain total, Wind max, Wind min, Wind gust,solar')
                    file.write('\n')
            except OSError:
                self.systemError('wrong USB', 'format')


        # check USB for weatherData, create if not there
        try:
            filePathName = self.usbPath + '/' + self.dataFileName
            open(filePathName)
        except FileNotFoundError:
            try:
                with open(filePathName, 'w') as file:
                    file.write('DateTime' + ',')
                    for label in data.periodLabels:
                        file.write(label + ',')
                    #file.write('DateTime,Temp,RH,Wind avr,Wind gust,solar,Rain total')
                    file.write('\n')
            except OSError:
                self.systemError('wrong USB', 'format')

    def writePeriodDataLine(self, periodWaterLoss):
        '''writes one line of data to weatherData.CSV
        '''
        # update wind min and max
        if data.periodWeatherVariables['windAvrPeriod'] > data.dayWeatherVariables['windAvrMax']:
            data.dayWeatherVariables['windAvrMax'] = data.periodWeatherVariables['windAvrPeriod']
        if data.periodWeatherVariables['windAvrPeriod'] < data.dayWeatherVariables['windAvrMin']:
            data.dayWeatherVariables['windAvrMin'] = data.periodWeatherVariables['windAvrPeriod']

        # create comments for sensor errors
        self.comment = self.comment + data.sensorError['TempError'] + data.sensorError['RHError'] + data.sensorError['LuxError']
        
        data.writeDataBackupSD()

        filePathName = self.usbPath + '/' + self.dataFileName
        try:
            open(filePathName)
        except FileNotFoundError:
            self.systemError(self, 'No USB data file', 'Check USB and reboot')
        else:
            with open(filePathName, 'a') as file:
                dateTimeNow = '{:%Y-%m-%d:%_H:%M}'.format(datetime.now())
                file.write(dateTimeNow + ',')
                # write data from periodWeatherVariables
                for datum in data.periodOrder:
                    if datum == 'rainTotalDay':
                        file.write(str('{:.0f}'.format(data.dayWeatherVariables['rainTotalDay'])) + ',')
                    else:
                        file.write(str('{:.0f}'.format(data.periodWeatherVariables[datum])) + ',')

                # waterLoss and cumulative
                file.write(str('{:.3f}'.format(periodWaterLoss)) + ',')
                file.write(str('{:.3f}'.format(data.waterLossCumulative)) + ',')
                # comment
                file.write(str(self.comment) + ',')

                # clear comment
                self.comment = '/'

                file.write('\n')

    def writeDailySummary(self, yesterday):
        ''' writes one line to weather history files
        '''
        filePathName = self.usbPath + '/' + self.historyFileName
        try:
            open(filePathName)
        except FileNotFoundError:
            self.systemError(self, 'No USB history file', 'Check USB and reboot')
        else:
            with open(filePathName, 'a') as file:
                file.write(yesterday + ',')
                # write data from dayWeatherVariables
                for datum in data.dayOrder:
                    file.write(str('{:.0f}'.format(data.dayWeatherVariables[datum])) + ',')
                file.write('\n')

    def getFileSummary(self, fileName):
        '''get summary of file for MX screen
        '''
        filePathName = self.usbPath + '/' + fileName
        
        # count rows and get last line
        with open(filePathName,'r') as file:
            opened_file = file.readlines()
            rowsInFile = len(opened_file) - 1  # subtract 1 for header
            lastLine = opened_file[-1].split(',')[0]

        if fileName == self.dataFileName:
            dataFileMessage = str(rowsInFile) + 'L ' + lastLine[5:19]
        else:
            dataFileMessage = str(rowsInFile) + 'L ' + lastLine[:14]
        return dataFileMessage

    def getRainList(self, lengthRainList):
        filePathName = self.usbPath + '/weatherHistory.csv'
        rainList = []

        # count rows and get last line
        with open(filePathName,'r') as file:
            opened_file = file.readlines()
            rowsInFile = len(opened_file) - 1  # subtract 1 for header

        for i, row in enumerate(reversed(opened_file)):
            if i > (lengthRainList - 1):
                return rainList
            if i < rowsInFile:
                rainList.append(row.split(',')[5])
            else:
                rainList.append('ND')

        if i < lengthRainList:
            for j in range ((lengthRainList - 1) - i):
                rainList.append('ND')

        return rainList



    #### SENSOR CALLS AND WEATHER FUNCTIONS ####

    def readWind(self, timeUnit):
        '''calculate wind speed, update history, display on LCD
        '''
        # convert revelutions to distance (meters)
        windDist =  self.windCounter * 3.1415 * (2 * config.anemometerRadius) * .00001

        # convert distance to speed (km/hr)
        windCurrent = windDist / (timeUnit / 3600)

        # calculate running average
        data.periodWeatherVariables['windAvrPeriod'] = ((data.periodWeatherVariables['windAvrPeriod'] * self.windAvrCount) + windCurrent) / (self.windAvrCount + 1)
        self.windAvrCount +=1

        # check for gust
        if windCurrent > data.periodWeatherVariables['windGust']:
            data.periodWeatherVariables['windGust'] = windCurrent

        if data.periodWeatherVariables['windGust'] > data.dayWeatherVariables['windGustMax']:
            data.dayWeatherVariables['windGustMax'] = data.periodWeatherVariables['windGust']

        self.windCounter = 0

        data.periodWeatherVariables['windCurrent'] = windCurrent

    def readTempRH(self):
        '''reads tempurature, humidity, sets variables, determines min/max
        '''
        try:
            RHCurrent, tempCurrent, tempF = self.tempSensor.returnTempRH()
        except OSError:
            if self.debugON == True: print('tempSensor OSError')
            tempCurrent = 0
            if data.sensorError['TempError'] != 'no Temp/':
                self.comment = self.comment + 'temp or RH sensor fail/'
            data.sensorError['TempError'] = 'no Temp/'
            RHCurrent = 0
            data.sensorError['RHError'] = 'no RH/'

        # React to no sensor read (NoneType)
        if RHCurrent is None:
            RHCurrent = 0
            data.updateRHError('no RH/')
        else:
            if RHCurrent > data.dayWeatherVariables['RHMax']:
                data.dayWeatherVariables['RHMax'] = RHCurrent
            if RHCurrent < data.dayWeatherVariables['RHMin']:
                data.dayWeatherVariables['RHMin'] = RHCurrent

        if tempCurrent is None:
            tempCurrent = 0
            data.sensorError['TempError'] = 'no Temp/'
        else:
            if tempCurrent > data.dayWeatherVariables['tempMax']:
                data.dayWeatherVariables['tempMax'] = tempCurrent
            if tempCurrent < data.dayWeatherVariables['tempMin']:
                data.dayWeatherVariables['tempMin'] = tempCurrent

        data.periodWeatherVariables['tempCurrent'] = tempCurrent
        data.periodWeatherVariables['RHCurrent'] = RHCurrent
        
    def readSolar(self):
        '''reads solar sensor
        '''
        if self.lightSensor != 0:
            full, ir = self.lightSensor.get_full_luminosity()  # read raw values (full spectrum and ir spectrum)
            solarLux = self.lightSensor.calculate_lux(full, ir)  # convert raw values to lux
            data.sensorError['LuxError'] = ''
        else:
            solarLux = 0
            data.sensorError['LuxError'] = 'no Solar/'

        data.periodWeatherVariables['solarLux'] = solarLux

    #### SCREEN FUNCTIONS ####
    def restartLCD(self):
        '''re-initializes LCD, can be used at various times in case
        there was an ESD event at the LCD
        '''
        self.mylcd = I2C_LCD_driver3.lcd()
        
        # turn backlight on (1 indicates ON)
        if self.backlightTimer < self.backlightOffTime:
            self.mylcd.backlight(1)
        else:
            self.mylcd.backlight(0)

        customWeatherCharacters = [
            # Char 0 - flower
            [0x4, 0xa, 0x4, 0x0, 0x0, 0x1f, 0xe, 0xe],
            # Char 1 - water drop 
            [0x0, 0x4, 0x4, 0xa, 0x11, 0x11, 0x11, 0xe],
            # Char 2 - maiz 1
            [0x0,0x0,0x0,0x0,0x0,0x0, 0x4, 0x1f],
            # Char 3 - maiz 2
            [0x0,0x0, 0x0,0x4, 0xc, 0x6, 0x4, 0x1f],
            # Char 4 - maiz 3
            [0x0, 0x4, 0xc, 0x5, 0x16, 0xc, 0x4, 0x1f],
            # Char 5 - maiz 4
            [0x4, 0xc, 0x5, 0x16, 0xd, 0x6, 0x4, 0x1f],
            # Char 6 - up arrow
            [0x0, 0x4, 0xe, 0x1f, 0x0, 0x1f, 0x0, 0x0],
            # Char 7 - down arrow
            [0x0, 0x0, 0x1f, 0x0, 0x1f, 0xe, 0x4,  0x0]
            ]

        self.custom = {
            'flower': 0,
            'water drop': 1,
            'maiz1': 2,
            'maiz2': 3,
            'maiz3': 4,
            'maiz4': 5,
            'up arrow': 6,
            'down arrow': 7}

        # load custom characters
        self.mylcd.lcd_load_custom_chars(customWeatherCharacters)

    def startScreen(self, programFilePathName):
        '''screen during startup then goes away
        '''
        self.mylcd.lcd_clear()
        self.mylcd.lcd_display_string('Pontis', 1, 0)
        self.mylcd.lcd_display_string(EnglishSpanish.getWord('Weather Station'), 2, 0)

        # get software rev from weather.py file
        swNow, swNew = self.getSWrev(config.updateFilePath)

        message = 's/w ' + swNow
        self.mylcd.lcd_display_string(message, 4, 0)

    def runGrowAnimation(self, line, space, repeats, totalTime):
        '''animation of plants growing in unison
        '''
        for plant in ('maiz1', 'maiz2', 'maiz3', 'maiz4'):
            self.mylcd.lcd_display_string('          ', line, space)
            for spaceGap in range(0, repeats):
                thisSpace = space + (spaceGap * 2)
                self.mylcd.lcd_display_string('', line, thisSpace)
                self.mylcd.lcd_write_char(self.custom[plant])
            time.sleep(totalTime/4)

    def runFunGrowAnimation(self, line, space, repeats, totalTime):
        '''animation of plants growing randomly
        '''
        plant = [None] * 10

        for plantNumber in range (0, repeats):
            plant[plantNumber] = 1;
            thisSpace = space + (plantNumber * 2)
            self.mylcd.lcd_display_string('', line, thisSpace)
            self.mylcd.lcd_write_char(self.custom['maiz1'])

        grow = True

        while grow is True:
            whichPlant = random.randint(0, repeats - 1)

            if(plant[whichPlant] < 4):
                plant[whichPlant] +=1
                thisSpace = space + (whichPlant * 2)
                self.mylcd.lcd_display_string('', line, thisSpace)
                if(plant[whichPlant] == 2):
                    self.mylcd.lcd_write_char(self.custom['maiz2'])
                elif(plant[whichPlant] == 23):
                    self.mylcd.lcd_write_char(self.custom['maiz3'])
                else:
                    self.mylcd.lcd_write_char(self.custom['maiz4'])
                time.sleep(totalTime/12)
            else:
                workingTest = 0
                for plantNumber in range (0, repeats):
                    if(plant[plantNumber] < 4):
                        pass
                    else:
                        workingTest += 1
                if workingTest >= repeats:
                    grow = False


    def mainScreen(self):
        '''writes the main screen on LCD minus the variables
        '''
        # Line 1 date
        self.mylcd.lcd_display_string('{:%b %d}'.format(datetime.now()), 1, 0)

        # Line 4 navigation
        self.mylcd.lcd_display_string('', 4, 0)
        self.mylcd.lcd_write_char(127)
        self.mylcd.lcd_display_string(EnglishSpanish.getWord("page"), 4, 2)
        self.mylcd.lcd_display_string('MX ', 4, 16)
        self.mylcd.lcd_write_char(126)

    def clockRefresh(self):
        '''LCD prints clock display
        '''
        self.mylcd.lcd_display_string('{:%_I:%M %p}'.format(datetime.now()), 1, 10)

    def mainScreenRefresh(self):
        ''' writes the temp and RH lines with data
        '''
        # Time display
        self.mylcd.lcd_display_string('{:%_I:%M %p}'.format(datetime.now()), 1, 10)

        # Temp display
        if data.sensorError['TempError'] == 'no Temp/':
            self.mylcd.lcd_display_string('NT', 2, 0)
            self.mylcd.lcd_write_char(223)
            self.mylcd.lcd_display_string('C ', 2, 3)
        else:
            self.mylcd.lcd_display_string('{:2.0f}'.format(data.periodWeatherVariables['tempCurrent']), 2, 0)
            self.mylcd.lcd_write_char(223)
            self.mylcd.lcd_display_string('C ', 2, 3)

        # RH display
        if data.sensorError['RHError'] == 'no RH/':
            self.mylcd.lcd_display_string('NR', 2, 6)
            self.mylcd.lcd_display_string('% ', 2, 8)
        else:
            self.mylcd.lcd_display_string('{:2.0f}'.format(data.periodWeatherVariables['RHCurrent']), 2, 6)
            self.mylcd.lcd_display_string('% ', 2, 8)

        # Wind Display
        self.mylcd.lcd_display_string('{:3.0f}'.format(data.periodWeatherVariables['windCurrent']), 2, 11)
        self.mylcd.lcd_display_string(' km/h', 2, 14)

        # Rain Display
        self.mylcd.lcd_display_string('{:5.0f}'.format(data.dayWeatherVariables['rainTotalDay']), 3, 0)
        self.mylcd.lcd_display_string(' mm', 3, 5)

        # Solar Display
        if data.sensorError['LuxError'] != 'no Solar/':
            self.mylcd.lcd_display_string('{:5.0f}'.format(data.periodWeatherVariables['solarLux']), 3, 10)
        else:
            self.mylcd.lcd_display_string('   NS', 3, 10)
        self.mylcd.lcd_display_string('lux', 3, 16)

        # Irrigation water drops
        if data.waterLossCumulative >= 2:
            self.mylcd.lcd_display_string('', 4, 9)
            self.mylcd.lcd_write_char(self.custom['water drop'])

        if data.waterLossCumulative >= 4:
            self.mylcd.lcd_display_string('', 4, 10)
            self.mylcd.lcd_write_char(self.custom['water drop'])

        if data.waterLossCumulative >= 6:
            self.mylcd.lcd_display_string('', 4, 11)
            self.mylcd.lcd_write_char(self.custom['water drop'])

        if data.waterLossCumulative >= 8:
            self.mylcd.lcd_display_string('', 4, 12)
            self.mylcd.lcd_write_char(self.custom['water drop'])

        if data.waterLossCumulative >= 12:
            self.mylcd.lcd_display_string('', 4, 13)
            self.mylcd.lcd_write_char(self.custom['water drop'])


    def rainScreen(self):
        '''Rain screen displays previous week's rain
        '''
        sixDayRainList = self.getRainList(6)

        self.buttonState = 0
        self.mylcd.lcd_clear()
        self.mylcd.lcd_display_string(EnglishSpanish.getWord('Rain (mm)'), 1, 0)

        self.mylcd.lcd_display_string(EnglishSpanish.getWord('Today'), 2, 0)
        self.mylcd.lcd_display_string('{:4.0f}'.format(data.dayWeatherVariables['rainTotalDay']), 2, 4)
        self.mylcd.lcd_display_string(EnglishSpanish.getWord('Ystrdy'), 2, 10)
        self.mylcd.lcd_display_string(sixDayRainList[0], 2, 17)

        self.mylcd.lcd_display_string(sixDayRainList[1], 3, 0)
        self.mylcd.lcd_display_string(sixDayRainList[2], 3, 6)
        self.mylcd.lcd_display_string(sixDayRainList[3], 3, 12)
        self.mylcd.lcd_display_string(sixDayRainList[4], 3, 17)


        self.mylcd.lcd_display_string('', 4, 0)
        self.mylcd.lcd_write_char(127)
        self.mylcd.lcd_display_string(EnglishSpanish.getWord("page"), 4, 2)

        # XXXX DEV XXXX
        self.mylcd.lcd_display_string('{:2.3f}'.format(data.waterLossCumulative), 4, 12)

        lastSecond = 0
        lastFloatSecond = 0
        screenTimer = 0

        i = True
        while i  is True:
            #### CONTINUOUS POLLING ####
            # too fast of polling causes LCD problems, so this sets the timing
            
            thisSecond = float(datetime.now().strftime('%S.%f'))

            if lastFloatSecond + self.pollingDelay >= 60:
                lastFloatSecond = 0

            if thisSecond > lastFloatSecond + self.pollingDelay:
                # index the timer
                lastFloatSecond = thisSecond

                # check and react to buttonState
                if self.buttonState != 0 and self.buttonAction == 0:
                    if self.buttonState == 1:
                        self.buttonAction = 1
                        screenTimer = 0
                        if self.debugON == True: print('exit rain screen')
                        i = False
                        # set for polling
                        lastFloatSecond = float(datetime.now().strftime('%S.%f'))

                    elif self.buttonState == 2:
                        self.buttonAction = 1
                        screenTimer = 0
                        pass
                    elif self.buttonState == 3:
                        self.buttonAction = 1
                        screenTimer = 0
                        pass
                    else:
                        pass

            # Require buttons to be released before next press
            self.buttonCheckRelease()

            #### EVERY SECOND FUNCTIONS AND SCREEN TIMEOUT ####
            # use int of the float thisSecond
            if int(thisSecond) != lastSecond:
                # screen time out
                if screenTimer > self.backlightOffTime:
                    i = False

                lastSecond = int(thisSecond)
                screenTimer += 1

    def irrigation(self):
        '''Irrigation screen, runs through them sequentially
        '''
        self.buttonState = 0
        self.mylcd.lcd_clear()

        irrigationScreenNumber = 0
        irrigationScreenList = (
            'Beans (mm)',
            'Beans (l)',
            'Corn (mm)',
            'Corn (l)'
            )

        # line 1 is displayed below as it changes with crops

        self.mylcd.lcd_display_string('', 2, 0)
        self.mylcd.lcd_write_char(self.custom['maiz1'])

        self.mylcd.lcd_display_string('', 2, 8)
        self.mylcd.lcd_write_char(self.custom['maiz2'])

        self.mylcd.lcd_display_string('', 3, 0)
        self.mylcd.lcd_write_char(self.custom['maiz3'])

        self.mylcd.lcd_display_string('', 3, 8)
        self.mylcd.lcd_write_char(self.custom['maiz4'])

        self.mylcd.lcd_display_string('', 4, 0)
        self.mylcd.lcd_write_char(127)
        self.mylcd.lcd_display_string(EnglishSpanish.getWord("page"), 4, 2)

        # initialize with first screen
        self.irrigationCropRefresh(irrigationScreenList[irrigationScreenNumber])   

        lastSecond = 0
        lastFloatSecond = 0
        screenTimer = 0

        i = True
        while i is True:
            #### CONTINUOUS POLLING ####
            # too fast of polling causes LCD problems, so this sets the timing           
            thisSecond = float(datetime.now().strftime('%S.%f'))

            if lastFloatSecond + self.pollingDelay >= 60:
                lastFloatSecond = 0

            if thisSecond > lastFloatSecond + self.pollingDelay:
                # index the timer
                lastFloatSecond = thisSecond

                # check and react to buttonState
                if self.buttonState != 0 and self.buttonAction == 0:
                    if self.buttonState == 1:
                        self.buttonAction = 1
                        screenTimer = 0

                        irrigationScreenNumber +=1
                        if(irrigationScreenNumber >= len(irrigationScreenList)):
                            if self.debugON == True: print('exit irrigation screen')
                            i = False
                            # set for polling
                            lastFloatSecond = float(datetime.now().strftime('%S.%f'))
                        else:
                            self.irrigationCropRefresh(irrigationScreenList[irrigationScreenNumber])   

                    elif self.buttonState == 2:
                        self.buttonAction = 1
                        screenTimer = 0
                        pass
                    elif self.buttonState == 3:
                        self.buttonAction = 1
                        screenTimer = 0
                        pass
                    else:
                        pass

            # Require buttons to be released before next press
            self.buttonCheckRelease()

            #### EVERY SECOND FUNCTIONS AND SCREEN TIMEOUT ####
            # use int of the float thisSecond
            if int(thisSecond) != lastSecond:
                # screen time out
                if screenTimer > self.backlightOffTime:
                    i = False

                lastSecond = int(thisSecond)
                screenTimer += 1

    def Iirrigated(self):
        '''last irrigation screen, can indicate irrigation was completed
        '''
        self.buttonState = 0
        self.mylcd.lcd_clear()


        # line 1 is displayed below as it changes with crops

        self.mylcd.lcd_display_string('Irrigation Action', 1, 2)
        self.mylcd.lcd_display_string(EnglishSpanish.getWord('Irrigation Action'), 1, 0)

        self.mylcd.lcd_display_string(EnglishSpanish.getWord('partial'), 2, 10)
        self.mylcd.lcd_display_string('', 2, 19)
        self.mylcd.lcd_write_char(126)
        self.mylcd.lcd_display_string(EnglishSpanish.getWord('full'), 3, 10)
        self.mylcd.lcd_display_string('', 3, 19)
        self.mylcd.lcd_write_char(126)

        self.mylcd.lcd_display_string('', 4, 0)
        self.mylcd.lcd_write_char(127)
        self.mylcd.lcd_display_string(EnglishSpanish.getWord("page"), 4, 2)

        lastSecond = 0
        lastFloatSecond = 0
        screenTimer = 0

        i = True
        while i is True:
            #### CONTINUOUS POLLING ####
            # too fast of polling causes LCD problems, so this sets the timing           
            thisSecond = float(datetime.now().strftime('%S.%f'))

            if lastFloatSecond + self.pollingDelay >= 60:
                lastFloatSecond = 0

            if thisSecond > lastFloatSecond + self.pollingDelay:
                # index the timer
                lastFloatSecond = thisSecond

                # check and react to buttonState
                if self.buttonState != 0 and self.buttonAction == 0:
                    if self.buttonState == 1:
                        self.buttonAction = 1
                        screenTimer = 0
                        if self.debugON == True: print('exit irrigation screen')
                        i = False
                        # set for polling
                        lastFloatSecond = float(datetime.now().strftime('%S.%f'))
                    elif self.buttonState == 2:  # full irrigation
                        self.buttonAction = 1
                        screenTimer = 0
                        # full irrigation puts waterLoss at 0
                        data.waterLossCumulative = 0
                        if self.debugON == True: print('full irrigation')
                        self.mylcd.lcd_clear()
                        self.mylcd.lcd_display_string(EnglishSpanish.getWord('Full Irrigation'), 1, 0)
                        self.mylcd.lcd_display_string(EnglishSpanish.getWord('Complete'), 2, 5)
                        self.comment = self.comment + 'Full Irrigation/'
                        time.sleep(5)
                        i = False
                        # set for polling
                        lastFloatSecond = float(datetime.now().strftime('%S.%f'))
                    elif self.buttonState == 3:  # partial irrigation
                        self.buttonAction = 1
                        screenTimer = 0
                        data.waterLossCumulative  = data.waterLossCumulative  - config.partialIrrigation
                        if self.debugON == True: print('partial irrigation')
                        self.mylcd.lcd_clear()
                        self.mylcd.lcd_display_string(EnglishSpanish.getWord('Partial Irrigation'), 1, 0)
                        self.mylcd.lcd_display_string(EnglishSpanish.getWord('Complete'), 2, 5)
                        self.comment = self.comment + 'Partial Irrigation/'
                        time.sleep(5)
                        i = False
                        # set for polling
                        lastFloatSecond = float(datetime.now().strftime('%S.%f'))
                    else:
                        pass

            # Require buttons to be released before next press
            self.buttonCheckRelease()

            #### EVERY SECOND FUNCTIONS AND SCREEN TIMEOUT ####
            # use int of the float thisSecond
            if int(thisSecond) != lastSecond:
                # screen time out
                if screenTimer > self.backlightOffTime:
                    i = False

                lastSecond = int(thisSecond)
                screenTimer += 1




    def irrigationCropRefresh(self, crop):
        ''' refreshes crops in irrigation screen
        '''
        cropFactorLookup = {
            'Beans (mm)': (config.kBeans, 1),
            'Beans (l)': (config.kBeans, config.fManzana),
            'Corn (mm)': (config.kCorn, 1),
            'Corn (l)': (config.kCorn, config.fManzana)
            }

        
        if crop[-4:] == '(mm)':
            landFactor = 1
        elif config.landArea == 'acre':
            landFactor = config.fAcre
        elif config.landArea == 'hectare':
            landFactor = config.fHectare
        else:
            landFactor = config.fManzana

        self.mylcd.lcd_display_string('                    ', 1, 0)
        self.mylcd.lcd_display_string('      ', 2, 2)
        self.mylcd.lcd_display_string('      ', 2, 10)
        self.mylcd.lcd_display_string('      ', 3, 2)
        self.mylcd.lcd_display_string('      ', 3, 10)
        self.mylcd.lcd_display_string(EnglishSpanish.getWord(crop), 1)
        
        kList = cropFactorLookup[crop][0]

        if(data.waterLossCumulative >= config.minimumIrrigation):
            self.mylcd.lcd_display_string('{:3.0f}'.format(landFactor * kList[0] * data.waterLossCumulative), 2, 2)
            self.mylcd.lcd_display_string('{:3.0f}'.format(landFactor * kList[1] * data.waterLossCumulative), 2, 10)
            self.mylcd.lcd_display_string('{:3.0f}'.format(landFactor * kList[2] * data.waterLossCumulative), 3, 2)
            self.mylcd.lcd_display_string('{:3.0f}'.format(landFactor * kList[3] * data.waterLossCumulative), 3, 10)
        else:
            self.mylcd.lcd_display_string('0', 2, 2)
            self.mylcd.lcd_display_string('0', 2, 10)
            self.mylcd.lcd_display_string('0', 3, 2)
            self.mylcd.lcd_display_string('0', 3, 10)




    #### MX SCREENS ####

    def MXscreenSelect(self, mxFunction):
        '''first maintenance screen where others can be selected,
        generally the mxFunction is set at 0 but others can be sent
        '''
        self.buttonState = 0
        self.MXscreenRefresh()
        tempRainCounter = self.rainCounter  # used to reset if rain gage is tested

        lastSecond = 0
        lastFloatSecond = 0
        screenTimer = 0

        # mxFunction = 8 is referenced in s/w update to change to reboot
        mxFunctionList = [
                        'QUITE MX',
                        'USB eject',
                        'check Data File',
                        'check History',
                        'set clock',
                        'anemometer',
                        'rain gage',
                        's/w update',
                        'reboot',
                        'shutdown']
        lastmxFunction = 999

        i = 1
        while i < 10:
            #### CONTINUOUS POLLING ####
            # too fast of polling causes LCD problems, so this sets the timing
            
            thisSecond = float(datetime.now().strftime('%S.%f'))

            if lastFloatSecond + self.pollingDelay >= 60:
                lastFloatSecond = 0

            if thisSecond > lastFloatSecond + self.pollingDelay:
                # index the timer
                lastFloatSecond = thisSecond

                #### DISPLAYS DATA ON MAINTENANCE SCREEN ####
                if config.language == 'Spanish':
                    mxDisplayList = [
                        'SALIR MX',
                        'expulsar USB',
                        'mira datos',
                        'mira historia',
                        'configuar reloj',
                        'anemometro',
                        'pluviometro',
                        'actualizar update',
                        'reiniciar',
                        'apagar']
                else:
                    mxDisplayList = mxFunctionList

                if mxFunction != lastmxFunction:
                    self.MXscreenRefresh()
                    # update line
                    self.mylcd.lcd_display_string('                   ', 2, 0)
                    self.mylcd.lcd_display_string('                   ', 3, 0)
                    self.mylcd.lcd_display_string(mxDisplayList[mxFunction], 2, 1)

                    # some MX function require an init:
                    if mxFunctionList[mxFunction] == 'anemometer':
                        self.windCounter = 0
                        self.mylcd.lcd_display_string(EnglishSpanish.getWord('sensor count: '), 3, 0)

                    elif mxFunctionList[mxFunction] == 'rain gage':
                        self.rainCounter = 0
                        self.mylcd.lcd_display_string(EnglishSpanish.getWord('sensor count: '), 3, 0)

                    elif mxFunctionList[mxFunction] == 'set clock':
                        self.mylcd.lcd_display_string('{:%Y-%m-%d %_H:%M}'.format(datetime.now()), 3, 0)

                    elif mxFunctionList[mxFunction] == 'check Data File':
                        dataFileMessage = self.getFileSummary(self.dataFileName)
                        self.mylcd.lcd_display_string(dataFileMessage, 3, 0)

                    elif mxFunctionList[mxFunction] == 'check History':
                        dataFileMessage = self.getFileSummary(self.historyFileName)
                        self.mylcd.lcd_display_string(dataFileMessage, 3, 0)

                    elif mxFunctionList[mxFunction] == 's/w update':
                        swNow, swNew = self.getSWrev(config.updateFilePath)
                        message = swNow + ' to ' + swNew
                        self.mylcd.lcd_display_string(message, 3, 0)

                    lastmxFunction = mxFunction

                # Display values for sensor troubleshooting
                if mxFunctionList[mxFunction] == 'anemometer':
                    self.mylcd.lcd_display_string('{:.0f}'.format(self.windCounter), 3, 14)
                elif mxFunctionList[mxFunction] == 'rain gage':
                    self.mylcd.lcd_display_string('{:.0f}'.format(self.rainCounter), 3, 14)

                # check and react to buttonState
                if self.buttonState != 0 and self.buttonAction == 0:
                    if self.buttonState == 1:
                        self.buttonAction = 1
                        screenTimer = 0

                        if mxFunctionList[mxFunction] == 'QUITE MX':
                            # clear counters used in sensor troubleshooting to avoid
                            # inaccurate data
                            self.windCounter = 0
                            self.rainCounter = tempRainCounter

                            i = 999

                        elif mxFunctionList[mxFunction] == 'USB eject':
                            RPiUtilities.ejectUSB(self.usbPath)
                            self.mylcd.lcd_display_string(EnglishSpanish.getWord('Reboot Required!'), 1, 0)
                            self.mylcd.lcd_display_string(EnglishSpanish.getWord('replace USB'), 2, 2)
                            self.mylcd.lcd_display_string(EnglishSpanish.getWord('and Reboot'), 3, 0)
                            time.sleep(5)
                            mxFunction = 8

                        elif mxFunctionList[mxFunction] == 'set clock':
                            self.clockSet()

                            #self.mylcd.lcd_display_string(mxFunctionList[mxFunction], 2, 2)
                            # this forces display to refresh
                            lastmxFunction = 999

                        elif mxFunctionList[mxFunction] == 's/w update':
                            self.mylcd.lcd_clear()
                            self.mylcd.lcd_display_string(EnglishSpanish.getWord('Loading new s/w'), 1, 0)
                            self.mylcd.lcd_display_string(EnglishSpanish.getWord('please wait'), 2, 2)
                            self.mylcd.lcd_display_string(EnglishSpanish.getWord('will reboot'), 3, 0)
                            RPiUtilities.copySW(self.usbPath)
                            RPiUtilities.rebootRPI()

                        elif mxFunctionList[mxFunction] == 'reboot':
                            self.mylcd.lcd_clear()
                            self.mylcd.lcd_display_string(EnglishSpanish.getWord('Reboot System'), 1, 0)
                            self.mylcd.lcd_display_string(EnglishSpanish.getWord('please wait'), 2, 2)
                            GPIO.cleanup()
                            RPiUtilities.rebootRPI()

                        elif mxFunctionList[mxFunction] == 'shutdown':
                            self.mylcd.lcd_clear()
                            self.mylcd.lcd_display_string(EnglishSpanish.getWord('Shutdown System'), 1, 0)
                            self.mylcd.lcd_display_string(EnglishSpanish.getWord('must restart'), 2, 2)
                            GPIO.cleanup()
                            RPiUtilities.shutdownRPI()

                    elif self.buttonState == 2:
                        self.buttonAction = 1
                        screenTimer = 0

                        mxFunction = mxFunction - 1
                        if mxFunction < 0:
                            mxFunction = len(mxFunctionList) - 1

                    elif self.buttonState == 3:
                        self.buttonAction = 1
                        screenTimer = 0

                        mxFunction = mxFunction + 1
                        if mxFunction > len(mxFunctionList) - 1:
                            mxFunction = 0
                    else:
                        pass

                # Require buttons to be released before next press
                self.buttonCheckRelease()


                #### EVERY SECOND FUNCTIONS AND SCREEN TIMEOUT ####
                # use int of the float thisSecond
                if int(thisSecond) != lastSecond:
                    # screen time out
                    if screenTimer > self.backlightOffTime:
                        i = 999

                    lastSecond = int(thisSecond)
                    screenTimer += 1


    def MXscreenRefresh(self):
        '''LCD init and refresh for MX screen
        '''
        self.mylcd.lcd_clear()
        self.mylcd.lcd_display_string(EnglishSpanish.getWord('MX pages'), 1, 0)

        self.mylcd.lcd_display_string('', 2, 19)
        self.mylcd.lcd_write_char(self.custom['up arrow'])
        #self.mylcd.lcd_display_string('', 2, 19)
        #self.mylcd.lcd_write_char(94)
        self.mylcd.lcd_display_string('', 3, 19)
        self.mylcd.lcd_write_char(self.custom['down arrow'])
        #self.mylcd.lcd_display_string('', 3, 19)
        #self.mylcd.lcd_write_char(118)
        self.mylcd.lcd_display_string('', 4, 0)
        self.mylcd.lcd_write_char(127)
        self.mylcd.lcd_display_string(EnglishSpanish.getWord('do it'), 4, 2)

    def getSWrev(self, programFilePathName):
        '''get current and new s/w rev
        '''
        # grabs current rev from its own .py file
        try:
            with open(programFilePathName, newline='') as file:
                # read full file
                fileText = file.read()
                # split into lines
                lines = fileText.split('\n')
                line2 = lines[3]
                swNow = line2[2:]
                
        except FileNotFoundError as e:
            swNow = 'none'

        # count rows and get last line
        try:
            with open(self.usbPath + '/weatherUPDATE/readME') as file:
                swNew = file.readline()
                swNew = swNew[:-1]
        except FileNotFoundError:
            swNew = "none"

        if self.debugON == True: print('swNew: ', swNew)
        if self.debugON == True: print('getSWrev now/new: ',swNow, ' / ', swNew)

        return swNow, swNew

    def clockSet(self):
        '''Maintenance screen for setting real time clock
        '''
        # get timing variables from RTC (DS1307)
        year = int(datetime.now().strftime('%Y'))
        month = int(datetime.now().strftime('%m'))
        date = int(datetime.now().strftime('%d'))
        hour = int(datetime.now().strftime('%H'))
        minute = int(datetime.now().strftime('%M'))

        # set buttonState
        self.buttonState = 0

        # initialize LCD
        self.mylcd.lcd_clear()
        self.mylcd.lcd_display_string(EnglishSpanish.getWord('Clock set'), 1, 0)
        self.mylcd.lcd_display_string('', 2, 19)
        self.mylcd.lcd_write_char(self.custom['up arrow'])
        self.mylcd.lcd_display_string('', 3, 19)
        self.mylcd.lcd_write_char(self.custom['down arrow'])
        self.mylcd.lcd_display_string('', 4, 0)
        self.mylcd.lcd_write_char(127)
        self.mylcd.lcd_display_string(EnglishSpanish.getWord('next'), 4, 2)

        # set timing variables
        lastSecond = 0
        lastFloatSecond = 0
        screenTimer = 0

        # set lists for screen control
        screenList = ['YEAR', 'MONTH', 'DATE', 'HOUR', 'MINUTE', 'exit and set clock']
        if config.language == "Spanish":
            screenList = ['ANO', 'MES', 'FECHA', 'HORA', 'MINUTO', 'configurar el reloj']
        varList = [year, month, date, hour, minute, 999]
        setScreen = 0


        i = 1
        while i < 10:
            #### CONTINUOUS POLLING ####
            # too fast of polling causes LCD problems, so this sets the timing
            # pollingDelay is the timing and is set in init
            
            thisSecond = float(datetime.now().strftime('%S.%f'))

            # update set time on LCD
            if setScreen == 5:
                self.mylcd.lcd_display_string(EnglishSpanish.getWord('Set Clock and Exit  '), 1, 0)
            else:
                self.mylcd.lcd_display_string(screenList[setScreen] + '   ', 1, 10)
            year = varList[0]
            month = varList[1]
            date = varList[2]
            hour = varList[3]
            minute = varList[4]
            setDate = '{:}'.format(year) + '-' + '{:02d}'.format(month) + '-' + '{:02d}'.format(date)
            setTime = '{:02d}'.format(hour) + ':' + '{:02d}'.format(minute)
            self.mylcd.lcd_display_string(setDate, 2, 0)
            self.mylcd.lcd_display_string(setTime, 3, 0)

            if setScreen == 5:
                self.mylcd.lcd_display_string(EnglishSpanish.getWord('exit'), 2, 14)
                self.mylcd.lcd_display_string(EnglishSpanish.getWord('exit'), 3, 14)
                self.mylcd.lcd_display_string(EnglishSpanish.getWord('set clock'), 4, 2)  

            if lastFloatSecond + self.pollingDelay >= 60:
                lastFloatSecond = 0

            if thisSecond > lastFloatSecond + self.pollingDelay:
                # index the timer
                lastFloatSecond = thisSecond

                # check and react to buttonState
                if self.buttonState != 0 and self.buttonAction == 0:
                    if self.buttonState == 1:
                        self.buttonAction = 1
                        screenTimer = 0
                        setScreen = setScreen + 1
                        if setScreen > 5:
                            # this is to alert due to delay in clock setting
                            self.mylcd.lcd_clear()
                            self.mylcd.lcd_display_string(EnglishSpanish.getWord('WAIT'), 1, 0)
                            self.mylcd.lcd_display_string(EnglishSpanish.getWord('while clock sets'), 2, 2)

                            # this sets the RTC to the variables
                            RPiUtilities.setRTC(year, month, date, hour, minute)
                            i = 999

                        # set for polling
                        lastFloatSecond = float(datetime.now().strftime('%S.%f'))

                    elif self.buttonState == 2:
                        self.buttonAction = 1
                        screenTimer = 0
                        if setScreen == 5:
                            i = 999
                        else:
                            varList[setScreen] = varList[setScreen] - 1
                            if screenList[setScreen] == 'MONTH' and varList[setScreen] < 1:
                                varList[setScreen] = 12
                            elif screenList[setScreen] == 'DATE' and varList[setScreen] < 1:
                                varList[setScreen] = 31
                            elif screenList[setScreen] == 'HOUR' and varList[setScreen] < 0:
                                varList[setScreen] = 23
                            elif screenList[setScreen] == 'MINUTE' and varList[setScreen] < 0:
                                varList[setScreen] = 59
                            elif screenList[setScreen] == 'exit and set clock':
                                i = 999

                        screenTimer = 0
                        
                    elif self.buttonState == 3:
                        self.buttonAction = 1
                        screenTimer = 0
                        if setScreen == 5:
                            i = 999
                        else:
                            varList[setScreen] = varList[setScreen] + 1
                            if screenList[setScreen] == 'MONTH' and varList[setScreen] > 12:
                                varList[setScreen] = 1
                            elif screenList[setScreen] == 'DATE' and varList[setScreen] > 31:
                                varList[setScreen] = 1
                            elif screenList[setScreen] == 'HOUR' and varList[setScreen] > 23:
                                varList[setScreen] = 0
                            elif screenList[setScreen] == 'MINUTE' and varList[setScreen] > 59:
                                varList[setScreen] = 0
                            elif screenList[setScreen] == 'exit and set clock':
                                i = 999
                        screenTimer = 0
                        
                    else:
                        pass

                # Require buttons to be released before next press
                self.buttonCheckRelease()


                #### EVERY SECOND FUNCTIONS AND SCREEN TIMEOUT ####
                # use int of the float thisSecond
                if int(thisSecond) != lastSecond:
                    # screen time out (backlightOffTime is time out for screen)
                    if screenTimer > self.backlightOffTime:
                        i = 999

                    lastSecond = int(thisSecond)
                    screenTimer += 1

    def systemError(self, errorMessage2, errorMessage3):
        '''dead end screen requiring reboot with message for error
        '''
        self.mylcd.lcd_clear()
        self.mylcd.lcd_display_string('Act and Reboot', 1, 0)
        self.mylcd.lcd_display_string(errorMessage2, 2, 0)
        self.mylcd.lcd_display_string(errorMessage3, 3, 0)
        self.mylcd.lcd_display_string('reboot', 4, 13)
        self.mylcd.lcd_write_char(126)
        i = 1
        while i < 10:
            # check and react to buttonState
            if self.buttonState != 0:
                if self.buttonState == 1:
                    self.buttonAction = 1
                    pass

                elif self.buttonState == 2:
                    self.buttonAction = 1
                    self.mylcd.lcd_clear()
                    self.mylcd.lcd_display_string('Reboot System', 1, 0)
                    self.mylcd.lcd_display_string('please wait', 2, 2)
                    RPiUtilities.rebootRPI()

                elif self.buttonState == 3:
                    self.buttonAction = 1
                    pass

                else:
                    pass

                # return buttonState to no pressed state
                self.buttonState = 0




    #### INTERRUPT FUNCTIONS ####
    def windCount(self, pin):
        '''interrupt call from anemometer to increment the windCounter
        '''
        self.windCounter += 1

    def rainCount(self, pin):
        '''interrupt call from tipping bucket rain gage to increment the windCounter
        '''
        self.rainCounter += 1

    def backlightON(self):
        '''combined function for turning backlight on and refreshing screen
        '''
        # refresh LCD (in case of scramble) and turn backlight on
        self.backlightTimer = 0
        #self.restartLCD()    # restartLCD() includes backlight(1)
        self.mylcd.backlight(1)
        #self.mainScreen()
        self.mainScreenRefresh()
        time.sleep(.5)
        
        #self.buttonState = 0

    def reactToButton(self, buttonPin):
        '''function call from button 2 interrupt
        '''
        time.sleep(.01) # this is part of the debounce

        # if backlight is off, then turn on only for this press
        if self.backlightTimer > self.backlightOffTime:
            self.buttonState = 99
        else:
            if buttonPin == self.pinButton1:
                self.buttonState = 1
            elif buttonPin == self.pinButton2:
                self.buttonState = 2
            elif buttonPin == self.pinButton3:
                self.buttonState = 3
            else:
                self.buttonState = 0

        if self.debugON == True: print('button ', self.buttonState, ' pressed')

    def buttonCheckRelease(self):
        '''sets self.buttonState to 0 only if all buttons are not pressed
        - this is the only place self.buttonState can be set to 0
        - self.buttonState is the button pressed
        '''
        time.sleep(.01) # this is part of the debounce

        button1 = GPIO.input(self.pinButton1)
        button2 = GPIO.input(self.pinButton2)
        button3 = GPIO.input(self.pinButton3)

        if button1 == False and button2 == False and button3 == False:
            self.buttonState = 0
            self.buttonAction = 0



if __name__ == '__main__':
    print('start weather')
    data = stationData()
    app = weatherStation()
    app.runTimer()


print('end weather station script')
