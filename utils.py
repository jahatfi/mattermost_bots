#!/usr/bin/env python3

import argparse
import requests
import json
from datetime import datetime
import pprint
import sys
# ==============================================================================
# Reference: https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
def str2bool(v):
    """
    Validates that an argparse argument is a boolean value.
    """
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')
        
# ==============================================================================
def parse_creds_from_file(authentication_info):
    """
    Parse file with (one per line): 
    (1 server url, 
    (2 team id, 
    (3 auth token, 
    (4 bot name
    Return them all in a tuple
    """
    with open(authentication_info, 'r') as creds_file:
        # Split on '=' in case the format is 'URL: mymattermostserver.com'
        url =     creds_file.readline().split('=')[1].strip()
        team_id = creds_file.readline().split('=')[1].strip()
        token   = creds_file.readline().split('=')[1].strip()
        bot_name = creds_file.readline().split('=')[1].strip()

        return (url, team_id, token, bot_name)
# ==============================================================================
def rename_bot(base_url, old_bot_name, old_bot_id, new_bot_name, headers):
    """
    Rename bot to new name
    """
    payload = {}
    payload["username"] = new_bot_name   
    payload["display_name"] = new_bot_name
    resp = requests.put(base_url+"api/v4/bots/"+old_bot_id, 
                            headers=headers,
                            data=json.dumps(payload))

    
    if resp.status_code < 200 or resp.status_code > 299:
        print(f"Failed to rename {old_bot_name} bot to {new_bot_name}")
        print(resp)
        return False
    else:
        print(f"Renamed {old_bot_name} bot to {new_bot_name}")
    return True
# ==============================================================================
def update_bot_icon(base_url, bot_name, bot_id, new_image_file, headers):
    """
    Update image for bot
    """
    #if not new_image_file.endswith(".svg"):
    #    print(f"Cannot update bot icon with {new_image_file}, file must be .svg")
    #    return False

    files = {
        'image': (new_image_file, open(new_image_file, 'rb')),
    }


    new_headers = {}
    new_headers['Authorization'] = headers['Authorization']
    resp = requests.post(base_url+"api/v4/bots/"+bot_id+'/'+"icon", 
                        headers=new_headers,
                        files=files
            )
    
    if resp.status_code < 200 or resp.status_code > 299:
        print(f"Failed to update icon for {bot_name}")
        pprint.pprint(json.loads(resp.text))    
        return False
    else:
        # TODO This doesn't seem to work!
        print("Updating icon currently doesn't work even though server responded with 200/OK:")
        #print(f"Updated image for {bot_name} to {new_image_file}")
        pprint.pprint(json.loads(resp.text))    

    return True
# ==============================================================================
def return_computed_delay(target_time):
    """Compute delay between now and target time"""
    if not target_time:
        return 0
    try:
        target_time = datetime.strptime(target_time, "%m/%d/%Y %H:%M")
    except ValueError as e:
        print("Invalid time format, time format must be MM/DD/YYYY: HH:MM")
        sys.exit(1)
    if target_time < datetime.now():
        print(f"{target_time} in the past!")
        sys.exit(-1)
    delay = target_time - datetime.now()
    print(f"I need to sleep until {target_time}, that's {delay}, or {delay.seconds} seconds")
    return delay.seconds
# ==============================================================================
def create_dm_channel(base_url, bot_id, user_id, header):
    """
    Return dm channel info between bot and user
    """    
    header['Content-type'] = "application/json"
    channel_info = requests.post(base_url+"api/v4/channels/direct", 
                                headers=header,
                                data=json.dumps([bot_id, user_id]) )

    if channel_info.status_code < 200 or channel_info.status_code > 299:
        print(f"Failed to update icon for {bot_name}")
        pprint.pprint(json.loads(channel_info.text))    
        sys.exit(-1)

    channel_info = json.loads(channel_info.text)
    return channel_info['id']
# ==============================================================================
def log_failure_and_exit_if_failed(url, resp, message):
    if resp.status_code < 200 or resp.status_code > 299:
        resp = json.loads(resp.text)
        pprint.pprint(resp)
        print(message)
        print(f"URL was '{url}'.  See the problem?")
        sys.exit(-1)  

