# netatmo_coreef - by Peter Sturm (peter@0x002a.me)
#
# Access all Netatmo stations data of a users periodically and save each poll result as an individual
# JSON-encoded file. Should survive service outages (but not yet tested enough). Returns a description
# of the error or exception as stations data (content) with the top-level entry "success"==False.
#
# Required arguments:
# --file <auth_file> = JSON-encoded token file (created by netatmo_oauth)
#
# Optional arguments:
# --poll <seconds> = Time interval between two polls (default is 600 seconds)
# --outdir <path> = Where to store all the JSON-encoded stations data; exists or will be created 

import argparse
import json
import time
import datetime
import os.path
import requests

import crMQTT

# Relevant URLs to access Netatmo REST API
netatmo_auth_ep = "https://api.netatmo.com/oauth2/token"
netatmo_getstationsdata_ep = "https://api.netatmo.com/api/getstationsdata"

# Address of the MQTT server
mqtt_address = '10.42.1.102'
mqtt_port = 1884
mqtt = crMQTT.crMQTT(mqtt_address,mqtt_port)

# Reading the content of the given JSON encoded file; returns a dictionary
def read_json_file(filename):
    with open(filename) as f:
        return json.load(f)

# generic REST request (f should be requests.get or requests.post)
def rest_request (f,url,headers,body):
    try:
        response=f(url,headers=headers,data=body)
    except Exception as e:
        return { "success" : False, "content" : repr(e) }
    if response.ok:
        return { "success" : True, "content" : json.loads(response.text) }
    else:
        # TODO maybe there is more in response that should be returned
        return { "success" : False, "content" : response.status_code }

def get_netatmo_access_token(auth_data):
    body = { 'grant_type':"password", 'scope':"read_station" }
    body = body | auth_data
    headers = { 'Content-Type':'application/x-www-form-urlencoded' }
    return rest_request(requests.post,netatmo_auth_ep,headers,body)

def refresh_netatmo_access_token(token):
    body = {
        'grant_type':'refresh_token',
        'refresh_token':token['refresh_token'],
        'client_id':token['client_id'],
        'client_secret':token['client_secret']
    }
    headers = { 'Content-Type':'application/x-www-form-urlencoded' }
    return rest_request(requests.post,netatmo_auth_ep,headers,body)

def get_netatmo_stationsdata(access_token):
    headers = { 'Authorization':f"Bearer {access_token}"}
    return rest_request(requests.get,netatmo_getstationsdata_ep,headers,{})

def write_stationsdata_to_file(dir,sd):
    dt = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    p = os.path.join(dir,f"{dt}_stationsdata.json")
    with open(p,'w') as fd:
        fd.write(json.dumps(sd,indent=4))

def send_moduledata_to_mqtt(home,module,dashboard):
    global mqtt
    tag = f'{module}/reading'.replace(" ", "")
    message = json.dumps(dashboard)
    mqtt.publish(tag,message)

def send_all_stationsdata_to_mqtt(sd):
    if not sd['success']:
        return
    devices = sd['content']['body']['devices']
    for device in devices:
        send_moduledata_to_mqtt(device['home_name'],device['module_name'],device['dashboard_data'])
        for module in device['modules']:
            send_moduledata_to_mqtt(device['home_name'],module['module_name'],module['dashboard_data'])

def main ():
    # Defining and parsing all the arguments used by this script
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, required=True, help="The file containing the access and refresh token (JSON encoded")
    parser.add_argument("--poll", type=int, required=False, help="The poll intervall between REST calls in seconds",default=600)
    parser.add_argument("--outdir", type=str, required=False, help="The directory to store stations data files",default=".")
    args = parser.parse_args()
    token_file = args.file
    poll_intervall_in_secs = args.poll

    # Check for the output directory and create it if not
    data_dir = os.path.abspath(args.outdir)
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)

    # Load authentication data as a dictionary
    token = read_json_file(token_file)
    token['expires_in'] = 0 # Force refresh

    # Start the loop, poll the stations data and refresh token if needed
    while True:
        next_poll = time.time() + poll_intervall_in_secs
        token['expires_in'] -= poll_intervall_in_secs
        if token['expires_in']<= 2*poll_intervall_in_secs:
            result = refresh_netatmo_access_token(token)
            print(json.dumps(result,indent=4))
            if not result['success']:
                write_stationsdata_to_file(data_dir,result)
                print('Token refresh failed')
                token = read_json_file(token_file)
            else:
                t = result['content']
                for k in t.keys():
                    token[k] = t[k]
        result = get_netatmo_stationsdata(token['access_token'])
        write_stationsdata_to_file(data_dir,result)
        send_all_stationsdata_to_mqtt(result)
        wait_time = next_poll-time.time()
        if int(wait_time)>0:
            time.sleep(wait_time)

if __name__ == '__main__':
    main()
