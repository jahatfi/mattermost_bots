#!/usr/bin/env python3
"""
Utility functions shared across modules
"""
# Standard libs
import argparse
import json
from datetime import datetime
import pprint
import sys

# Non standard libs
import pandas as pd
import requests

pd.set_option('display.width', 1000)
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
    except ValueError:
        print("Invalid time format, time format must be MM/DD/YYYY: HH:MM")
        sys.exit(1)
    if target_time < datetime.now():
        print(f"{target_time} in the past!")
        sys.exit(-1)
    delay = target_time - datetime.now()
    print(f"I need to sleep until {target_time}, that's {delay}, or {delay.seconds} seconds")
    return delay.seconds
# ==============================================================================
def create_dm_channel(base_url, bot_id, bot_name, user_id, header):
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
        return -1
# ==============================================================================
def get_channels(base_url, headers):
    """
    Returns a Pandas DataFrame of all channels on this server, but with only
    a subset of the columns that are useful for identifying the channels.
    """
    cols_to_keep = ['id', 'name', 'display_name']
    page = 0
    all_channels = []
    channel_url = base_url+"api/v4/channels"
    
    print(f"Retrieving info for channels, starting with all channels")
    while True:
        headers["page"] = page
        resp = requests.get(channel_url, headers=headers)
        #print(resp.text)
        new_dict = json.loads(resp.text)
        
        all_channels += new_dict
        all_channels = pd.DataFrame(all_channels)
        cols_to_drop = all_channels.columns
        cols_to_drop = list(set(cols_to_drop) - set(cols_to_keep))
        all_channels.drop(cols_to_drop, axis=1, inplace=True)
        #rows_to_keep = all_channels['username'].isin(usernames)
        #all_channels = all_channels[rows_to_keep]
        #pprint.pprint(all_channels)
        if all_channels.empty:
            print("Failed")
        pprint.pprint(all_channels)
        return all_channels    
# ==============================================================================
def get_users(users_url, headers, usernames, channels, results_per_page):
    """
    Returns a Pandas DataFrame of all users on this server, but with only
    a subset of the columns that are useful for identifying the users.

    If both usernames and channels_ids provided, return the intersection of the 
    users in both those channels AND the username list.
    Otherwise, if only a list of usernames OR channels is provided,
    return those users.
    """
    cols_to_keep = ['id', 'username', 'email', 'first_name', 'nickname', 'last_name', 'status']
    page = 0
    all_users = []
    
    if any(channels):
        for _, channel in channels.iterrows():
            channel_name = channel['name']
            channel_id = channel['id']
            while True:
              
                print(f"Retrieving info for users in channel {channel_name}, page {page} ({results_per_page} entries per page)")
                resp = requests.get(users_url+f"?page={page}&in_channel={channel_id}", headers=headers)
                new_dict = json.loads(resp.text)
                all_users += new_dict
                if len(new_dict) < results_per_page:
                    break
                page += 1

    else:
        while True:
            
            print(f"Retrieving info for users, page {page} ({results_per_page} entries per page)")
            resp = requests.get(users_url+f"?page={page}", headers=headers)
            new_dict = json.loads(resp.text)
            
            all_users += new_dict
            if len(new_dict) < results_per_page:
                break
            page += 1        


    all_users = pd.DataFrame(all_users)
    cols_to_drop = all_users.columns
    cols_to_drop = list(set(cols_to_drop) - set(cols_to_keep))
    all_users.drop(cols_to_drop, axis=1, inplace=True)
    if usernames:
        rows_to_keep = all_users['username'].isin(usernames)
        all_users = all_users[rows_to_keep]
    #pprint.pprint(all_users)
    all_users.drop_duplicates(inplace=True)

    return all_users

# ==============================================================================
def get_bot_info(base_url, bot_id, headers):
    """
    Return bot info for this bot, None if it doesn't exist
    """
    all_bots = requests.get(base_url+"api/v4/bots", headers=headers)
    all_bots = json.loads(all_bots.text)
    all_bots = pd.DataFrame(all_bots)
    #pprint.pprint(all_bots)

    return all_bots[all_bots['user_id'] == bot_id]

#==============================================================================
def send_dm(base_url, channel_id, header, message):
    """
    Send dm to the provided channel
    """    
    header['Content-type'] = "application/json"
    dm_info = requests.post(base_url+"api/v4/posts", 
                                headers=header,
                                data=json.dumps({"channel_id": channel_id, "message":message}))
    dm_info = json.loads(dm_info.text)
    return dm_info

#==============================================================================    
def search_keyword(args, url, headers, team_id, channels):
    reaction_url = f"{url}api/v4/teams/{team_id}/posts/search"
    results = pd.DataFrame()
    data = {
        #"is_or_search": False,
        #"time_zone_offset": 0,
        #"include_deleted_channels": True,
        "per_page": 60
    }
    for channel_index, channel_id in enumerate(channels['id'].values):
        get_posts_url = f"{url}api/v4/channels/{channel_id}/posts"
        for page in range(6):
            print(f"Getting Page {page} of {channels.iloc[channel_index]['name']} posts")
            #headers['page'] = page
            resp = requests.get(   get_posts_url+f"?page={page}", 
                                    headers=headers,
                                    data=json.dumps(data)
                                )
            if resp.status_code < 200 or resp.status_code > 299:
                print("Error")
                print(f"URL was '{reaction_url}'.  See the problem?")  
                print(resp.text)          

            elif resp.text:
                posts = json.loads(resp.text)
                messages = pd.DataFrame(posts['posts'], index=None).T
                #print(messages.columns)
                if 'message' not in messages:
                    break
                desired_messages = messages[messages['message'].str.contains(args.keyword)]
                print(f"Found {len(desired_messages)} results")
                if results.empty:
                    results = desired_messages[["id", "create_at", "user_id", "message", "hashtags"]]
                else:
                    #print(desired_messages.columns)
                    results = results.append(desired_messages[["id", "create_at", "user_id", "message", "hashtags"]])
                #headers["before"] = posts["prev_post_id"]
                #print(posts["prev_post_id"])
    results = results.reset_index(drop=True)
    #pprint.pprint(results)    
    return results
#==============================================================================    
def read_usernames(username_file):

    if username_file:
        with open(username_file, 'r') as callsign_file:
            usernames = callsign_file.readlines()
            usernames = [c.lower().strip() for c in usernames]
    else:
        usernames = []

    return usernames