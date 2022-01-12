#!/usr/bin/env python3

import requests 
import json
import pprint
import argparse
import pandas as pd
import sys
from utils import *
from datetime import datetime
import time
# ==============================================================================
def main(parser):      
    """
    Provided:
    1. Mattermost server URL,
    2. Team ID,
    3. Authentication token,
    4. bot name,  
    5. File with message,
    6. Channel name
    Post the provided message in the provided channel as this bot
    """                                              
    args = parser.parse_args()
    pprint.pprint(args)
    message = ""
    results_per_page = 60 # Can up up to 200

    # Check if files exists

    # First the authenication file
    try:
        with open(args.authentication_info, "r") as authentication_info:
            pass
    except FileNotFoundError as e: 
        print(f"Can't find {args.authentication_info}")
        sys.exit(1)

    creds = parse_creds_from_file(args.authentication_info)
    url, team_id, token, bot_name = creds

    # Next the message file
    try:
        with open(args.message_file, "r") as message_file:
            message = message_file.read()
    except FileNotFoundError as e: 
        print(f"Can't find {args.message_file}")
        sys.exit(1)

    # Get channel by name
    headers = { 
                "is_or_search": "true",
                "time_zone_offset": "0",
                "include_deleted_channels": "false",
                "page": "0",
                "per_page": str(results_per_page),
                "Authorization" : f"Bearer {token}"
            }
    channel_by_name_url = f"{url}api/v4/teams/{team_id}/channels/name/{args.channel}"
    response = requests.get(channel_by_name_url, headers=headers)
    resp_dict = json.loads(response.text)

    if response.status_code < 300 and response.status_code >= 200:
        channel_id = resp_dict['id']
    else:
        print(f"Got response code: {response.status_code}")
        pprint.pprint(resp_dict)
        print("URL: " + channel_by_name_url)
        sys.exit(1)

    delay_seconds = return_computed_delay(args.delay)
    # Post to channel with provided message
    if args.live_run:
        print("Sleeping...")
        sys.stdout.flush()        
        time.sleep(delay.seconds)


        print(f"Posting to {args.channel}\nMessage: '{message}'")
        
        dm_info = requests.post(url+"api/v4/posts", 
                                headers=headers,
                                data=json.dumps({"channel_id": channel_id, 
                                                "message":message}))
        
    else:
        print("Dry run, not posting anything:")
        print(f"Would have posted to {args.channel}\nMessage: '{message}'")

    print("Done.")
# ==============================================================================
if __name__ == "__main__":
    valid_sort_criteria = ["nickname", "first_name", "last_name", "emoji", "username"]

    parser = argparse.ArgumentParser()

    parser.add_argument('--authentication-info', 
                        '-a',
                        required=True,
                        type=str,
                        help="File with (one per line): (1 server url, (2 team id, (3 auth token"
                        )

    parser.add_argument('--channel', 
                        '-c',
                        required=True,
                        type=str,
                        help="Channel name to post in"
                        )   
                        
    parser.add_argument('--message-file', 
                        '-m',
                        required=True,
                        type=str,
                        help="File with message (e.g. plain text or markdown)"
                        )  

    parser.add_argument('--live-run', 
                        '-l',
                        required=False,
                        default=False,
                        type=str2bool,
                        help="Live (True) or dry (False:default) run"
                        )      

    parser.add_argument('--delay', 
                        '-d',
                        required=False,
                        default="",
                        type=str,
                        help="Delay until date/time in format: MM/DD/YYYY: HH:MM"
                        )  
    parser.add_argument('--new-bot-name', 
                        '-b',
                        required=False,
                        default="",
                        type=str,
                        help="Temporary bot display name to use for this execution"
                        )   
    parser.add_argument('--new-bot-icon', 
                        '-i',
                        required=False,
                        default="",
                        type=str,
                        help="Temporary bot display avatar (SVG only)"
                        )  
    all_users = main(parser)        
