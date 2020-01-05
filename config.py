#! /usr/bin/env python
# -*- coding: utf-8 -*-
# weatherConfig.py
# Rev A.0
"""Config - for weather.py version A.0.1
"""

# Rev A.0 - field test release

debug2 = False  #for finding hang ups using syslog, lots of prints

#### PREFERENCES ####

# uncomment 1 language
#language = "English"
language = "Spanish"

# uncomment 1 land area measure
landArea = 'manzana'
#landArea = 'hectare'
#landArea = 'acre'

# file pathes (note the usb path is found with function findUSB)
updateFilePath = '/home/pi/WEATHER/weather.py'
SDFilePath = '/home/pi'

#### DATA ACQUISITION PARAMETERS ####
# data files on usb drive
historyFileName = 'weatherHistory.csv'
dataFileName = 'weatherData.csv'

#### WEATHER STATION PARAMETERS ####
# radius of the anemometer vanes in centimeters
anemometerRadius = 5.7

# rain gage factor (measured at .04 cm/tip, .4 millimeters of rain per tip)
rainGageVolume = .4

#### LCD ####
# Configured I2C address (default is 0x27)
LCDaddress = 0x23

# LCD backlight off time in SECONDS
backlightOffTime = 180

# luminouse efficiency is an experimentally determined factor based on sunlight
# and frequency. 
luminousEff = .0079

#### FACTORS USED IN PENMON-MONTEITH ####
# soil factors
maximumAbsorption = -25  # mm of rain that will absorb beyond waterLoss of 0 (must be negative)
maximumDry = 100  # maximum mm of waterLoss (must be positive)
partialIrrigation = 4 # mm of waterLoss removed for a partial irrigation
minimumIrrigation = 2 # irrigation required shows 0 until these mm


# crop constants for Penman-Monteith
kGeneral = 1.1
kCitrus = .7
kCoffee = 1.1
kBeans = (.4, .75, 1.15, .7)
kCorn = (.75, 1.0, 1.2, 1)
kGrain = (.75, 1, 1.15, .5)

fHectare = 1000
fManzana = 700
fAcre = 400

