# domoticz_blueconnect

## Introduction

The goal of this code is to query the temperature, pH, and clorine levels from the Blueriiot Blue Connect pool sensor, and to update Domoticz (https://domoticz.com/) with the queried data.

Marcel van der Veldt (@marcelveldt) already wrote a very elegant python library for communicating to the Blue Connect: https://github.com/marcelveldt/python-blueconnect. This library uses data classes to hold the sensor data and async calls, which is generally speaking a very nice design for many purposes. One pittfall with this design is that when the manufacturer of the sensor decides to change their JSON data model, which they may do at any given time as it is an internal api, the python code and the JSON model are out of sync, and the library does not work anymore. And this seems to have happened at the time I checked out the library (August 2022). Of course it is possible to update the data models in the library, but this comes at some maintenance costs.

Therefore, I have decided to take a far simpler and more straightforward approach; A single file with procedural functions (no classes) that directly uses the JSON output of the REST calls to the blueconnect web server. Also, for a single threaded process that does nothing more than updating the sensor information, the asyncronous io calls are not necesarry (async calls are very nice when calling the python code directly from a framework that also does UI, as they will not block the UI thread).

## Credits

The __get_credentials and __get_data functions where directly copied from https://github.com/marcelveldt/python-blueconnect and only slightly modified. Also, I figured out the correct REST calls to the Blue Connect web server from https://github.com/LordMike/MBW.Client.BlueRiiotApi.

## Usage
