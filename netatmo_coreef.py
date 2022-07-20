import argparse
import json
import time
import datetime
import os.path
import requests

# Relevant URLs to access Netatmo REST API
netatmo_auth_ep = "https://api.netatmo.com/oauth2/token"
netatmo_getstationsdata_ep = "https://api.netatmo.com/api/getstationsdata"

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

def refresh_netatmo_access_token(auth_data,tokens):
    body = {
        'grant_type':'refresh_token',
        'refresh_token':tokens['refresh_token'],
        'client_id':auth_data['client_id'],
        'client_secret':auth_data['client_secret']
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

def main ():
    # Defining and parsing all the arguments used by this script
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, required=True, help="The file containing all the authentication data (JSON encoded")
    parser.add_argument("--poll", type=int, required=False, help="The poll intervall between REST calls in seconds",default=600)
    parser.add_argument("--outdir", type=str, required=False, help="The directory to store stations data files",default=".")
    args = parser.parse_args()
    auth_data_file = args.file
    poll_intervall_in_secs = args.poll

    # Check for the output directory and create it if not
    data_dir = os.path.abspath(args.outdir)
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)

    # Load authentication data as a dictionary
    auth_data = read_json_file(auth_data_file)

    # Get access and renew token
    result = get_netatmo_access_token(auth_data)
    if not result['success']:
        print(f"Unable to get access token because of error <{result['content']}>\n")
        return
    tokens = result['content']
    
    # Start the loop, poll the stations data and refresh token if needed
    while True:
        next_poll = time.time() + poll_intervall_in_secs
        result = get_netatmo_stationsdata(tokens['access_token'])
        write_stationsdata_to_file(data_dir,result)
        tokens['expires_in'] -= poll_intervall_in_secs
        if tokens['expires_in']<= poll_intervall_in_secs:
            result = refresh_netatmo_access_token(auth_data,tokens)
            if not result['success']:
                write_stationsdata_to_file(data_dir,result)
            else:
                tokens = result['content']
        wait_time = next_poll-time.time()
        if int(wait_time)>0:
            time.sleep(wait_time)

if __name__ == '__main__':
    main()
