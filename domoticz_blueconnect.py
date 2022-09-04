#!/usr/bin/env python3

#Copyright (c) 2022, Danny Ruijters
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions are met:
#
#1. Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
#2. Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
#FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import json
import requests
import time
import hashlib
from aws_request_signer import AwsRequestSigner


_user = 'your@email.address' #login user name for blueconnect app
_passwd = 'YourPassword' #login user password for blueconnect app
_verbose = True #set to True to see the content of the json data
_domoticz_host = 'http://127.0.0.1:80' #ip of the Domoticz server
_domoticz_idx_temp = 523 #Domoticz idx for pool temperature sensor
_domoticz_idx_ph = 524 #Domoticz idx for pool pH sensor
_domoticz_idx_chlorine = 525 #Domoticz idx for pool chlorine level sensor
_domoticz_last_updated = 'BlueConnectLastUpdated' #Domoticz user variable name
_token_info = None

AWS_REGION = 'eu-west-1'
BASE_HEADERS = {
    'User-Agent': 'BlueConnect/3.2.1',
    'Accept-Language': 'en;q=1.0, en-US;q=0.9, *;q=0.8',
    'Accept': '*/*',
}
BASE_URL = 'https://api.riiotlabs.com/prod/'


def __verbose(data: dict) -> dict:
    if _verbose: print(json.dumps(data, indent=4, sort_keys=True))
    return data

def __get_credentials() -> dict:
    """Retrieve auth credentials by logging in with username/password."""
    global _token_info
    if _token_info and _token_info['expires'] > time.time():
        # return cached credentials if still valid
        return _token_info['credentials']
    # perform log-in to get credentials
    url = BASE_URL + 'user/login'
    cmd = {'email': _user, 'password': _passwd}
    with requests.post(url, data=json.dumps(cmd)) as response:
        if response.status_code != 200:
            error_msg = response.text
            raise Exception(f'Error logging in user: {error_msg}')
        _token_info = response.json()
        _token_info['expires'] = time.time() + 3500
        return _token_info['credentials']

def __get_data(endpoint: str) -> dict:
    """Get data from blueriiot"""
    url = BASE_URL + endpoint
    creds = __get_credentials()
    rs = AwsRequestSigner( #sign the request
        AWS_REGION, creds['access_key'], creds['secret_key'], 'execute-api')
    headers = BASE_HEADERS.copy()
    headers['X-Amz-Security-Token'] = creds['session_token']
    headers.update(rs.sign_with_headers('GET', url, headers))
    with requests.get(url, headers=headers) as response:
        if response.status_code != 200:
            error_msg = response.text
            raise Exception(
                f'Error while retrieving data for endpoint {endpoint}: {error_msg}'
            )
    return __verbose(response.json())

def __post_data(endpoint: str, content: str) -> dict:
    url = BASE_URL + endpoint
    creds = __get_credentials()
    rs = AwsRequestSigner( #sign the request
        AWS_REGION, creds['access_key'], creds['secret_key'], 'execute-api')
    headers = BASE_HEADERS.copy()
    headers['X-Amz-Security-Token'] = creds['session_token']
    content_hash = hashlib.sha256(content).hexdigest()
    headers.update(rs.sign_with_headers('POST', url, headers, content_hash))
    with requests.post(url, headers=headers, data=content) as response:
        if response.status_code != 200:
            error_msg = response.text
            raise Exception(
                f'Error while retrieving data for endpoint {endpoint}: {error_msg}'
            )
    return __verbose(response.json())

def __find_entry(entries: dict, key: str, name: str) -> dict:
    if entries: #prevent trying to iterate when None is passed as entries
        for entry in entries:
            if entry[key] == name: return entry
    return None

def __domoticz(cmd: dict) -> str:
    url = _domoticz_host + "/json.htm"
    return __verbose(requests.get(url, params=cmd).json())

def main() -> None:
    #user = __get_data(f'user')
    pool = __get_data(f'swimming_pool')['data']
    pool_id = pool[0]['swimming_pool']['swimming_pool_id']
    blue = __get_data(f'swimming_pool/{pool_id}/blue')['data']
    blue_device_serial = blue[0]['blue_device_serial']
    #__get_data(f'blue/{blue_device_serial}')
    __post_data(f'blue/{blue_device_serial}/releaseLastUnprocessedEvent', b'') #assure that the measurement is the most recent reading
    time.sleep(3)  #wait for uploading most recent reading
    measurements = __get_data(f'swimming_pool/{pool_id}/blue/' + 
        f'{blue_device_serial}/lastMeasurements?mode=blue_and_strip')['data']

    timestamp = measurements[0]['timestamp']
    last_updated = __find_entry(__domoticz(
        {'type' : 'command', 'param' : 'getuservariables'}).get('result'),
         'Name', _domoticz_last_updated)

    if not last_updated or last_updated['Value'] != timestamp:
        __domoticz({
            'type' : 'command',
            'param' : 'udevice',
            'idx' : _domoticz_idx_temp, #temperature
            'svalue' : __find_entry(measurements, 'name', 'temperature')['value']})
        __domoticz({
            'type' : 'command',
            'param' : 'udevice',
            'idx' : _domoticz_idx_ph, #pH
            'svalue' : __find_entry(measurements, 'name', 'ph')['value']})
        __domoticz({
            'type' : 'command',
            'param' : 'udevice',
            'idx' : _domoticz_idx_chlorine, #chlorine
            'svalue' : __find_entry(measurements, 'name', 'orp')['value']})
        __domoticz({
            'type' : 'command',
            'param' : 'updateuservariable' if last_updated else 'adduservariable',
            'vname' : _domoticz_last_updated,
            'vtype' : 2, #vtype 2 = string
            'vvalue' : timestamp})

if __name__ == '__main__':
    main()
