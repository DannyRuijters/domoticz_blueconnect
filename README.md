# domoticz_blueconnect

## Introduction

The goal of this code is to query the temperature, pH, and chlorine levels from the Blueriiot Blue Connect pool sensor, and to update Domoticz (https://domoticz.com/) with the queried data.

Marcel van der Veldt (@marcelveldt) already wrote a very elegant python library for communicating to the Blue Connect web server: https://github.com/marcelveldt/python-blueconnect. His library uses data classes to hold the sensor data and async calls, which is generally speaking a very nice design for many purposes. One pitfall with this design is that when the manufacturer of the sensor decides to change their JSON data model, which they may do at any given time as it is an internal api, the python code and the JSON model are out of sync, and the library does not work anymore. And exactly this seems to have happened at the time I checked out the library (August 2022). Of course it is possible to update the data models in the library, but this comes at some maintenance costs.

Therefore, I have decided to take a far simpler approach; A single file with procedural functions (no classes) that directly uses the JSON output of the REST calls to the blueconnect web server. Also, for a single threaded process that does nothing more than updating the sensor information, the asynchronous io calls are not necessary.

## Credits

The `__get_credentials` and `__get_data` functions where directly copied from https://github.com/marcelveldt/python-blueconnect and only slightly modified. Also, I figured out the correct REST calls to the Blue Connect web server from https://github.com/LordMike/MBW.Client.BlueRiiotApi.

## Usage

First make sure you have the aws-request-signer python package installed:
> pip3 install aws-request-signer

Then you will need to create dummy hardware in Domoticz: https://www.domoticz.com/wiki/Dummy_for_virtual_Switches.
Create the following virtual sensors:
- A temperature sensor
- A custom sensor for pH
- A custom sensor for chlorine

Note down the idx for these virtual sensors. Then put domoticz_blueconnect.py python script in /domoticz/scripts/python/ folder and update in the script the following global variables:
- _user = 'your@email.address' #login user name for blueconnect app
- _passwd = 'YourPassword' #login user password for blueconnect app
- _domoticz_idx_temp = 523 #Domoticz idx for pool temperature sensor
- _domoticz_idx_ph = 524 #Domoticz idx for pool pH sensor
- _domoticz_idx_chlorine = 525 #Domoticz idx for pool chlorine level sensor

Finally configure e.g. crontab to call the python script at regular (e.g. hourly) intervals:
> crontab -e

with an entry like:
> 0 * * * * /home/pi/domoticz/scripts/python/domoticz_blueconnect.py

