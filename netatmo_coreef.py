import argparse
import json
import time
import datetime
import requests

netatmo_auth_ep = "https://api.netatmo.com/oauth2/token"
netatmo_getstationsdata_ep = "https://api.netatmo.com/api/getstationsdata"

poll_intervall_in_secs = 600

# Reading the content of the given JSON encoded file; returns a dictionary
def read_json_file(filename):
    with open(filename) as f:
        return json.load(f)

def get_netatmo_access_token(auth_data):
    body = { 'grant_type':"password", 'scope':"read_station" }
    body = body | auth_data
    headers = { 'Content-Type':'application/x-www-form-urlencoded' }
    response = requests.post(netatmo_auth_ep, data=body, headers=headers)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return []

def refresh_netatmo_access_token(auth_data,tokens):
    body = {
        'grant_type':'refresh_token',
        'refresh_token':tokens['refresh_token'],
        'client_id':auth_data['client_id'],
        'client_secret':auth_data['client_secret']
    }
    headers = { 'Content-Type':'application/x-www-form-urlencoded' }
    response = requests.post(netatmo_auth_ep, data=body, headers=headers)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return []

def get_netatmo_stationsdata(access_token):
    headers = { 'Authorization':f"Bearer {access_token}"}
    response = requests.get(netatmo_getstationsdata_ep,headers=headers)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return []


def write_stationsdata_to_file(d):
    dt = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    with open(f"{dt}_stationsdata.json",'w') as fd:
        fd.write(json.dumps(d,indent=4))

def main ():
    # Defining and parsing all the arguments used by this script
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, required=True, help="The file containing all the authentication data (JSON encoded")
    args = parser.parse_args()
    auth_data_file = args.file

    # Load authentication data as a dictionary
    auth_data = read_json_file(auth_data_file)

    # Get access and renew token
    tokens = get_netatmo_access_token(auth_data)
    
    # Start the loop, poll the stations data and refresh token if needed
    while True:
        next_poll = time.time() + poll_intervall_in_secs
        stationsdata = get_netatmo_stationsdata(tokens['access_token'])
        write_stationsdata_to_file(stationsdata)
        tokens['expires_in'] -= poll_intervall_in_secs
        if tokens['expires_in']<= poll_intervall_in_secs:
            tokens = refresh_netatmo_access_token(auth_data,tokens)
        wait_time = next_poll-time.time()
        if int(wait_time)>0:
            time.sleep(wait_time)

if __name__ == '__main__':
    main()
